import time
import uuid
from typing import Dict, Any, List, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from packages.agent.providers.base import BaseModelProvider, AgentPlan
from packages.agent.providers import get_model_provider
from packages.sandbox_tools.context import ToolContext
from packages.fault_injection.proxy import FaultInjectionProxy

class BaselineAgent:
    """
    Fair, standard model-to-tool execution agent with schema validation.
    Executes planned tools directly without advanced policy gates, HITL approvals,
    exponential backoff recovery, or tamper-evident audit evidence receipts.
    """
    def __init__(self, provider: Optional[BaseModelProvider] = None):
        self.provider = provider or get_model_provider("deterministic_mock")

    async def run(
        self,
        user_query: str,
        persona: Dict[str, Any],
        session: AsyncSession,
        proxy: Optional[FaultInjectionProxy] = None,
        context: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        start_time = time.time()
        run_id = str(uuid.uuid4())
        tool_ctx = ToolContext(
            user_id=persona.get("user_id", "usr_cust_001"),
            user_role=persona.get("role", "customer"),
            run_id=run_id,
            session_metadata=context or {}
        )

        # 1. Classify intent
        intent_info = await self.provider.classify_intent(user_query, context)

        # 2. Generate tool plan
        plan: AgentPlan = await self.provider.generate_plan(user_query, persona, context)

        tool_results = []
        overall_success = True
        error_details = None

        # 3. Execute planned tools sequentially (direct execution, no policy guard or retry)
        for pt in plan.planned_tools:
            tool_start = time.time()
            if proxy:
                res = await proxy.execute(pt.tool_name, pt.arguments, session, tool_ctx)
            else:
                from packages.sandbox_tools.registry import execute_sandbox_tool
                res = await execute_sandbox_tool(pt.tool_name, pt.arguments, session, tool_ctx)

            tool_latency = (time.time() - tool_start) * 1000.0
            tool_results.append({
                "tool_name": pt.tool_name,
                "arguments": pt.arguments,
                "response": res,
                "latency_ms": tool_latency,
                "status": res.get("status", "unknown")
            })

            # Check if execution failed
            if res.get("status") in ("error", "fault_injected"):
                overall_success = False
                error_details = res.get("message", "Tool execution failed")
                # Baseline does not retry; terminates or moves on
                break

        total_latency = (time.time() - start_time) * 1000.0

        # Determine outcome
        final_status = "SUCCESS" if overall_success else "FAILED"
        final_outcome = f"Executed {len(tool_results)} tools. Status: {final_status}"
        if error_details:
            final_outcome += f" (Error: {error_details})"

        return {
            "run_id": run_id,
            "agent_mode": "baseline",
            "status": final_status,
            "classified_intent": plan.classified_intent,
            "plan_explanation": plan.explanation,
            "tool_calls": tool_results,
            "final_outcome": final_outcome,
            "latency_ms": total_latency,
            "token_usage": 150,  # Synthetic token count
            "cost_usd": 0.0003
        }
