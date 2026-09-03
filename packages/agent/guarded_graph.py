import asyncio
import time
import uuid
from typing import Dict, Any, List, Optional, TypedDict, Annotated
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from langgraph.graph import StateGraph, END

from packages.agent.providers.base import BaseModelProvider, AgentPlan, PlannedToolCall
from packages.agent.providers import get_model_provider
from packages.policies.models import PolicyContext, PolicyEvaluationResult, PolicyDecisionEnum
from packages.policies.engine import policy_engine
from packages.sandbox_tools.context import ToolContext
from packages.fault_injection.proxy import FaultInjectionProxy
from packages.telemetry.ledger import TamperEvidentEvidenceLedger
from apps.api.app.db.models import AgentRun, AgentEvent, ToolCall, PolicyDecision, Approval, Order, generate_uuid
from apps.api.app.core.config import settings

class GuardedState(TypedDict, total=False):
    run_id: str
    scenario_id: Optional[str]
    user_query: str
    persona: Dict[str, Any]
    seed: int
    session: Any  # AsyncSession
    proxy: Optional[Any]  # FaultInjectionProxy
    context: Dict[str, Any]
    step_index: int
    events: List[Dict[str, Any]]
    classified_intent: str
    intent_confidence: float
    plan: Optional[AgentPlan]
    current_tool_index: int
    current_tool: Optional[PlannedToolCall]
    policy_decision: Optional[PolicyEvaluationResult]
    approval_status: Optional[str]
    approval_id: Optional[str]
    tool_results: List[Dict[str, Any]]
    current_tool_result: Optional[Dict[str, Any]]
    retry_count: int
    max_retries: int
    validation_passed: bool
    escalated: bool
    escalation_reason: Optional[str]
    evidence_receipt: Optional[Dict[str, Any]]
    final_status: str
    final_outcome: str
    start_time: float
    latency_ms: float
    token_usage: int
    cost_usd: float

class GuardedAgent:
    """
    9-node LangGraph Guarded Agent state machine.
    Enforces tool allowlists, resource ownership, order-state preconditions,
    human approvals, bounded retry/backoff, output validation, and cryptographic audit receipts.
    """
    def __init__(self, provider: Optional[BaseModelProvider] = None):
        self.provider = provider or get_model_provider("deterministic_mock")
        self.graph = self._build_graph()

    def _build_graph(self) -> StateGraph:
        builder = StateGraph(GuardedState)

        # 1. Register 9 required LangGraph nodes
        builder.add_node("classify_intent", self._node_classify_intent)
        builder.add_node("create_plan", self._node_create_plan)
        builder.add_node("authorize_plan", self._node_authorize_plan)
        builder.add_node("request_approval", self._node_request_approval)
        builder.add_node("execute_tool", self._node_execute_tool)
        builder.add_node("validate_result", self._node_validate_result)
        builder.add_node("recover_or_escalate", self._node_recover_or_escalate)
        builder.add_node("emit_evidence_receipt", self._node_emit_evidence_receipt)
        builder.add_node("complete_run", self._node_complete_run)

        # 2. Add control flow edges
        builder.set_entry_point("classify_intent")
        builder.add_edge("classify_intent", "create_plan")
        builder.add_edge("create_plan", "authorize_plan")

        # Routing from authorize_plan
        builder.add_conditional_edges(
            "authorize_plan",
            self._route_after_authorize,
            {
                "execute_tool": "execute_tool",
                "request_approval": "request_approval",
                "emit_evidence_receipt": "emit_evidence_receipt"
            }
        )

        # Routing from request_approval
        builder.add_conditional_edges(
            "request_approval",
            self._route_after_approval,
            {
                "execute_tool": "execute_tool",
                "emit_evidence_receipt": "emit_evidence_receipt"
            }
        )

        builder.add_edge("execute_tool", "validate_result")

        # Routing from validate_result
        builder.add_conditional_edges(
            "validate_result",
            self._route_after_validate,
            {
                "authorize_plan": "authorize_plan",
                "recover_or_escalate": "recover_or_escalate",
                "emit_evidence_receipt": "emit_evidence_receipt"
            }
        )

        # Routing from recover_or_escalate
        builder.add_conditional_edges(
            "recover_or_escalate",
            self._route_after_recover,
            {
                "execute_tool": "execute_tool",
                "emit_evidence_receipt": "emit_evidence_receipt"
            }
        )

        builder.add_edge("emit_evidence_receipt", "complete_run")
        builder.add_edge("complete_run", END)

        return builder.compile()

    # --- Node 1: classify_intent ---
    async def _node_classify_intent(self, state: GuardedState) -> Dict[str, Any]:
        query = state["user_query"]
        intent_info = await self.provider.classify_intent(query, state.get("context"))
        
        events = list(state.get("events", []))
        events.append({
            "step_index": len(events) + 1,
            "node_name": "classify_intent",
            "event_type": "INTENT_CLASSIFIED",
            "payload": intent_info,
            "timestamp": time.time()
        })

        return {
            "classified_intent": intent_info.get("intent", "UNKNOWN"),
            "intent_confidence": intent_info.get("confidence", 1.0),
            "events": events
        }

    # --- Node 2: create_plan ---
    async def _node_create_plan(self, state: GuardedState) -> Dict[str, Any]:
        query = state["user_query"]
        persona = state["persona"]
        plan = await self.provider.generate_plan(query, persona, state.get("context"))

        events = list(state.get("events", []))
        events.append({
            "step_index": len(events) + 1,
            "node_name": "create_plan",
            "event_type": "PLAN_GENERATED",
            "payload": plan.model_dump(),
            "timestamp": time.time()
        })

        return {
            "plan": plan,
            "current_tool_index": 0,
            "retry_count": 0,
            "events": events
        }

    # --- Node 3: authorize_plan ---
    async def _node_authorize_plan(self, state: GuardedState) -> Dict[str, Any]:
        plan = state["plan"]
        idx = state.get("current_tool_index", 0)
        
        if not plan or idx >= len(plan.planned_tools):
            return {"policy_decision": None}

        tool_call = plan.planned_tools[idx]
        persona = state["persona"]
        session: AsyncSession = state["session"]

        # Gather context for order ownership and state checks
        order_owner_id = None
        order_status = None
        order_id = tool_call.arguments.get("order_id")
        
        if order_id:
            stmt = select(Order).where(Order.id == order_id)
            res = await session.execute(stmt)
            ord_obj = res.scalar_one_or_none()
            if ord_obj:
                order_owner_id = ord_obj.user_id
                order_status = ord_obj.order_status

        policy_ctx = PolicyContext(
            user_id=persona.get("user_id", "usr_cust_001"),
            user_role=persona.get("role", "customer"),
            tool_name=tool_call.tool_name,
            tool_arguments=tool_call.arguments,
            order_owner_id=order_owner_id,
            order_status=order_status,
            prompt_text=state["user_query"]
        )

        decision_result = policy_engine.evaluate(policy_ctx)

        events = list(state.get("events", []))
        events.append({
            "step_index": len(events) + 1,
            "node_name": "authorize_plan",
            "event_type": f"POLICY_{decision_result.decision.value}",
            "payload": decision_result.model_dump(),
            "timestamp": time.time()
        })

        updates: Dict[str, Any] = {
            "current_tool": tool_call,
            "policy_decision": decision_result,
            "events": events
        }

        if decision_result.decision == PolicyDecisionEnum.DENY:
            updates["final_status"] = "REJECTED_POLICY"
            updates["final_outcome"] = f"Action blocked by policy '{decision_result.rule_name}': {decision_result.reason}"

        return updates

    def _route_after_authorize(self, state: GuardedState) -> str:
        dec = state.get("policy_decision")
        if not dec:
            return "emit_evidence_receipt"
        if dec.decision == PolicyDecisionEnum.DENY:
            return "emit_evidence_receipt"
        elif dec.decision == PolicyDecisionEnum.REQUIRE_APPROVAL:
            return "request_approval"
        return "execute_tool"

    # --- Node 4: request_approval ---
    async def _node_request_approval(self, state: GuardedState) -> Dict[str, Any]:
        tool_call = state["current_tool"]
        session: AsyncSession = state["session"]
        approval_id = generate_uuid()
        run_id = state["run_id"]
        reason = state["policy_decision"].reason if state.get("policy_decision") else "Approval required by policy"

        # Check if caller already granted pre-approval in context
        approval_override = state.get("context", {}).get("pre_approved_action")
        is_pre_approved = approval_override is True

        approval = Approval(
            id=approval_id,
            run_id=run_id,
            action_type=tool_call.tool_name if tool_call else "sensitive_action",
            proposed_payload_json=tool_call.arguments if tool_call else {},
            status="approved" if is_pre_approved else "pending",
            reason=reason
        )
        session.add(approval)
        await session.flush()

        events = list(state.get("events", []))
        events.append({
            "step_index": len(events) + 1,
            "node_name": "request_approval",
            "event_type": "APPROVAL_SUBMITTED",
            "payload": {"approval_id": approval_id, "status": approval.status, "reason": reason},
            "timestamp": time.time()
        })

        if is_pre_approved:
            return {
                "approval_id": approval_id,
                "approval_status": "approved",
                "events": events
            }
        else:
            return {
                "approval_id": approval_id,
                "approval_status": "pending",
                "final_status": "APPROVAL_PENDING",
                "final_outcome": f"Action paused. Requires human approval: {reason}",
                "events": events
            }

    def _route_after_approval(self, state: GuardedState) -> str:
        if state.get("approval_status") == "approved":
            return "execute_tool"
        return "emit_evidence_receipt"

    # --- Node 5: execute_tool ---
    async def _node_execute_tool(self, state: GuardedState) -> Dict[str, Any]:
        tool_call = state["current_tool"]
        session: AsyncSession = state["session"]
        proxy: Optional[FaultInjectionProxy] = state.get("proxy")
        persona = state["persona"]
        run_id = state["run_id"]

        tool_ctx = ToolContext(
            user_id=persona.get("user_id", "usr_cust_001"),
            user_role=persona.get("role", "customer"),
            run_id=run_id,
            idempotency_key=tool_call.arguments.get("idempotency_key"),
            session_metadata=state.get("context", {})
        )

        t_start = time.time()
        if proxy:
            res = await proxy.execute(tool_call.tool_name, tool_call.arguments, session, tool_ctx)
        else:
            from packages.sandbox_tools.registry import execute_sandbox_tool
            res = await execute_sandbox_tool(tool_call.tool_name, tool_call.arguments, session, tool_ctx)
        tool_lat = (time.time() - t_start) * 1000.0

        tool_entry = {
            "tool_name": tool_call.tool_name,
            "arguments": tool_call.arguments,
            "response": res,
            "latency_ms": tool_lat,
            "status": res.get("status", "unknown")
        }

        tool_results = list(state.get("tool_results", []))
        tool_results.append(tool_entry)

        events = list(state.get("events", []))
        events.append({
            "step_index": len(events) + 1,
            "node_name": "execute_tool",
            "event_type": "TOOL_EXECUTED",
            "payload": tool_entry,
            "timestamp": time.time()
        })

        return {
            "current_tool_result": res,
            "tool_results": tool_results,
            "events": events
        }

    # --- Node 6: validate_result ---
    async def _node_validate_result(self, state: GuardedState) -> Dict[str, Any]:
        res = state.get("current_tool_result", {})
        tool_call = state.get("current_tool")
        tool_name = tool_call.tool_name if tool_call else ""

        validation_passed = True
        failure_reason = None

        # 1. Check status
        if res.get("status") in ("error", "fault_injected", "malformed_json_corrupted"):
            validation_passed = False
            failure_reason = res.get("message") or res.get("error_code") or "Tool returned error"

        # 2. Check silent product ID drift
        if tool_name == "get_product" and "product" in res:
            requested_id = tool_call.arguments.get("product_id")
            returned_id = res["product"].get("product_id")
            if requested_id and returned_id and requested_id != returned_id:
                validation_passed = False
                failure_reason = f"Silent semantic drift: requested product '{requested_id}' but received '{returned_id}'."

        # 3. Check price drift
        if res.get("price_drift_injected"):
            validation_passed = False
            failure_reason = "Price drift anomaly detected prior to order execution."

        events = list(state.get("events", []))
        events.append({
            "step_index": len(events) + 1,
            "node_name": "validate_result",
            "event_type": "RESULT_VALIDATED" if validation_passed else "RESULT_VALIDATION_FAILED",
            "payload": {"validation_passed": validation_passed, "failure_reason": failure_reason},
            "timestamp": time.time()
        })

        updates: Dict[str, Any] = {
            "validation_passed": validation_passed,
            "escalation_reason": failure_reason,
            "events": events
        }

        if validation_passed:
            plan = state.get("plan")
            next_idx = state.get("current_tool_index", 0) + 1
            updates["current_tool_index"] = next_idx
            updates["retry_count"] = 0  # reset retries for next tool
            
            if res.get("status") == "escalated" or tool_name == "escalate_to_human":
                updates["final_status"] = "ESCALATED"
                updates["approval_id"] = res.get("approval_id")
                updates["approval_status"] = "pending"
                updates["final_outcome"] = res.get("summary") or res.get("message") or "Action escalated to human supervisor."
            elif not plan or next_idx >= len(plan.planned_tools):
                updates["final_status"] = "SUCCESS"
                updates["final_outcome"] = f"Successfully completed all {len(plan.planned_tools) if plan else 1} planned actions."

        return updates

    def _route_after_validate(self, state: GuardedState) -> str:
        if not state.get("validation_passed"):
            return "recover_or_escalate"
        
        plan = state.get("plan")
        idx = state.get("current_tool_index", 0)
        if plan and idx < len(plan.planned_tools):
            return "authorize_plan"
        
        return "emit_evidence_receipt"

    # --- Node 7: recover_or_escalate ---
    async def _node_recover_or_escalate(self, state: GuardedState) -> Dict[str, Any]:
        res = state.get("current_tool_result", {})
        err_code = res.get("error_code", "")
        retries = state.get("retry_count", 0)
        max_retries = state.get("max_retries", settings.MAX_RECOVERY_RETRIES)

        is_retryable = err_code in (
            "HTTP_429_TOO_MANY_REQUESTS",
            "HTTP_500_INTERNAL_ERROR",
            "TOOL_TIMEOUT",
            "HTTP_503_SERVICE_UNAVAILABLE"
        )

        events = list(state.get("events", []))

        # Check if we can retry with bounded backoff
        if is_retryable and retries < max_retries:
            backoff_sec = (2 ** retries) * 0.1
            await asyncio.sleep(backoff_sec)
            
            events.append({
                "step_index": len(events) + 1,
                "node_name": "recover_or_escalate",
                "event_type": "RETRY_WITH_BACKOFF",
                "payload": {"retry_index": retries + 1, "backoff_seconds": backoff_sec, "reason": err_code},
                "timestamp": time.time()
            })

            return {
                "retry_count": retries + 1,
                "events": events
            }

        if err_code == "INSUFFICIENT_STOCK":
            return {
                "escalated": False,
                "final_status": "REJECTED_OUT_OF_STOCK",
                "final_outcome": res.get("message", "Order rejected: Requested product is currently out of stock."),
                "events": events
            }

        # Otherwise escalate or safe abort
        session: AsyncSession = state["session"]
        tool_ctx = ToolContext(
            user_id=state["persona"].get("user_id", "usr_cust_001"),
            run_id=state["run_id"]
        )
        from packages.sandbox_tools.escalation import escalate_to_human
        esc_res = await escalate_to_human(
            session=session,
            ctx=tool_ctx,
            issue_type="unrecoverable_fault",
            summary=f"Automated recovery failed or fatal condition: {state.get('escalation_reason') or err_code}",
            context_details={"last_tool_result": res}
        )

        events.append({
            "step_index": len(events) + 1,
            "node_name": "recover_or_escalate",
            "event_type": "ESCALATED_TO_HUMAN",
            "payload": esc_res,
            "timestamp": time.time()
        })

        return {
            "escalated": True,
            "final_status": "ESCALATED",
            "final_outcome": f"Execution halted safely. Escalated to human operator: {esc_res.get('summary')}",
            "events": events
        }

    def _route_after_recover(self, state: GuardedState) -> str:
        if not state.get("escalated") and state.get("retry_count", 0) > 0:
            # If retry was scheduled, re-execute the tool
            return "execute_tool"
        return "emit_evidence_receipt"

    # --- Node 8: emit_evidence_receipt ---
    async def _node_emit_evidence_receipt(self, state: GuardedState) -> Dict[str, Any]:
        session: AsyncSession = state["session"]
        run_id = state["run_id"]
        scenario_id = state.get("scenario_id")
        final_outcome = state.get("final_status", "UNKNOWN")

        event_data = {
            "run_id": run_id,
            "scenario_id": scenario_id,
            "user_query": state["user_query"],
            "persona": state["persona"],
            "final_status": state.get("final_status"),
            "final_outcome": state.get("final_outcome"),
            "tool_calls_count": len(state.get("tool_results", [])),
            "events_count": len(state.get("events", [])),
            "timestamp": time.time()
        }

        receipt = await TamperEvidentEvidenceLedger.append_receipt(
            session=session,
            run_id=run_id,
            scenario_id=scenario_id,
            final_outcome=final_outcome,
            event_data=event_data
        )

        events = list(state.get("events", []))
        events.append({
            "step_index": len(events) + 1,
            "node_name": "emit_evidence_receipt",
            "event_type": "RECEIPT_CHAINED",
            "payload": {
                "receipt_id": receipt.id,
                "event_hash": receipt.event_hash,
                "previous_event_hash": receipt.previous_event_hash
            },
            "timestamp": time.time()
        })

        return {
            "evidence_receipt": {
                "receipt_id": receipt.id,
                "event_hash": receipt.event_hash,
                "previous_event_hash": receipt.previous_event_hash,
                "payload_hash": receipt.payload_hash,
                "signature": receipt.signature
            },
            "events": events
        }

    # --- Node 9: complete_run ---
    async def _node_complete_run(self, state: GuardedState) -> Dict[str, Any]:
        start_time = state.get("start_time", time.time())
        total_latency = (time.time() - start_time) * 1000.0
        session: AsyncSession = state["session"]
        run_id = state["run_id"]

        # Persist AgentRun record in database
        run_record = AgentRun(
            id=run_id,
            scenario_id=state.get("scenario_id"),
            agent_mode="guarded",
            seed=state.get("seed", 42),
            user_query=state["user_query"],
            status=state.get("final_status", "UNKNOWN").lower(),
            final_outcome=state.get("final_outcome"),
            latency_ms=total_latency,
            token_usage=250,
            cost_usd=0.0005
        )
        session.add(run_record)

        # Persist all AgentEvents
        for ev in state.get("events", []):
            agent_ev = AgentEvent(
                run_id=run_id,
                step_index=ev["step_index"],
                node_name=ev["node_name"],
                event_type=ev["event_type"],
                payload_json=ev["payload"]
            )
            session.add(agent_ev)

        # Persist all ToolCalls
        for tc in state.get("tool_results", []):
            tool_rec = ToolCall(
                run_id=run_id,
                tool_name=tc["tool_name"],
                arguments_json=tc["arguments"],
                response_json=tc["response"],
                status=tc["status"],
                latency_ms=tc["latency_ms"],
                idempotency_key=tc["arguments"].get("idempotency_key")
            )
            session.add(tool_rec)

        # Persist PolicyDecision if any
        if state.get("policy_decision"):
            pd = state["policy_decision"]
            pol_rec = PolicyDecision(
                run_id=run_id,
                rule_name=pd.rule_name,
                decision=pd.decision.value,
                reason=pd.reason,
                context_json=pd.context_snapshot
            )
            session.add(pol_rec)

        await session.commit()

        return {
            "latency_ms": total_latency,
            "token_usage": 250,
            "cost_usd": 0.0005
        }

    async def run(
        self,
        user_query: str,
        persona: Dict[str, Any],
        session: AsyncSession,
        proxy: Optional[FaultInjectionProxy] = None,
        context: Optional[Dict[str, Any]] = None,
        scenario_id: Optional[str] = None,
        seed: int = 42
    ) -> Dict[str, Any]:
        """Executes the complete 9-node LangGraph state machine."""
        run_id = str(uuid.uuid4())
        initial_state: GuardedState = {
            "run_id": run_id,
            "scenario_id": scenario_id,
            "user_query": user_query,
            "persona": persona,
            "seed": seed,
            "session": session,
            "proxy": proxy,
            "context": context or {},
            "step_index": 0,
            "events": [],
            "tool_results": [],
            "retry_count": 0,
            "max_retries": settings.MAX_RECOVERY_RETRIES,
            "start_time": time.time(),
            "final_status": "RUNNING"
        }

        final_state = await self.graph.ainvoke(initial_state)
        
        # Prepare clean return dict
        return {
            "run_id": run_id,
            "agent_mode": "guarded",
            "scenario_id": scenario_id,
            "status": final_state.get("final_status", "SUCCESS"),
            "final_outcome": final_state.get("final_outcome"),
            "classified_intent": final_state.get("classified_intent"),
            "plan_explanation": final_state.get("plan").explanation if final_state.get("plan") else "",
            "policy_decision": final_state.get("policy_decision").model_dump() if final_state.get("policy_decision") else None,
            "approval_id": final_state.get("approval_id"),
            "approval_status": final_state.get("approval_status"),
            "tool_calls": final_state.get("tool_results", []),
            "events": final_state.get("events", []),
            "evidence_receipt": final_state.get("evidence_receipt"),
            "latency_ms": final_state.get("latency_ms", 0.0),
            "token_usage": final_state.get("token_usage", 0),
            "cost_usd": final_state.get("cost_usd", 0.0)
        }
