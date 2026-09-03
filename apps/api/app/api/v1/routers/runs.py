import yaml
from pathlib import Path
from typing import Dict, Any, Optional, List
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.orm import selectinload

from apps.api.app.db.database import get_db
from apps.api.app.db.models import AgentRun, AgentEvent, ToolCall, PolicyDecision, EvidenceReceipt
from packages.agent.baseline import BaselineAgent
from packages.agent.guarded_graph import GuardedAgent
from packages.fault_injection.proxy import FaultInjectionProxy
from packages.fault_injection.rules import FaultConfig, FaultType

router = APIRouter(prefix="/runs", tags=["Agent Runs & Replay"])

class CreateRunRequest(BaseModel):
    query: Optional[str] = None
    scenario_id: Optional[str] = None
    agent_mode: str = "guarded"  # baseline or guarded
    persona: Dict[str, Any] = Field(default_factory=lambda: {"user_id": "usr_cust_001", "role": "customer", "name": "Alice Johnson"})
    seed: int = 42
    fault_configs: Optional[List[Dict[str, Any]]] = None

class ReplayRunRequest(BaseModel):
    override_seed: Optional[int] = None

@router.post("")
async def create_agent_run(req: CreateRunRequest, session: AsyncSession = Depends(get_db)):
    """Launch a baseline or guarded agent run on a scenario or custom query."""
    user_query = req.query
    scenario_data = None

    if req.scenario_id:
        scenario_file = Path(f"scenarios/{req.scenario_id}.yaml")
        if scenario_file.exists():
            with open(scenario_file, "r", encoding="utf-8") as fp:
                scenario_data = yaml.safe_load(fp)
                if not user_query:
                    user_query = scenario_data.get("user_request")
                if "persona" in scenario_data and not req.query:
                    req.persona = scenario_data["persona"]

    if not user_query:
        raise HTTPException(status_code=400, detail="Must provide either 'query' or valid 'scenario_id'.")

    # Build fault proxy if faults are specified
    proxy = FaultInjectionProxy()
    faults_to_inject = req.fault_configs or (scenario_data.get("injected_faults") if scenario_data else [])
    for fd in faults_to_inject:
        proxy.register_fault(FaultConfig(
            fault_type=FaultType(fd["fault_type"]),
            target_tool=fd.get("target_tool", "*"),
            probability=fd.get("probability", 1.0),
            invocation_count=fd.get("invocation_count", 1),
            delay_seconds=fd.get("delay_seconds", 0.2),
            seed=req.seed
        ))

    if req.agent_mode == "baseline":
        agent = BaselineAgent()
        result = await agent.run(
            user_query=user_query,
            persona=req.persona,
            session=session,
            proxy=proxy,
            context={"seed": req.seed, "scenario_id": req.scenario_id}
        )
        # Store in DB
        run_record = AgentRun(
            id=result["run_id"],
            scenario_id=req.scenario_id,
            agent_mode="baseline",
            seed=req.seed,
            user_query=user_query,
            status=result["status"].lower(),
            final_outcome=result["final_outcome"],
            latency_ms=result["latency_ms"],
            token_usage=result["token_usage"],
            cost_usd=result["cost_usd"]
        )
        session.add(run_record)
        for tc in result.get("tool_calls", []):
            session.add(ToolCall(
                run_id=result["run_id"],
                tool_name=tc["tool_name"],
                arguments_json=tc["arguments"],
                response_json=tc["response"],
                status=tc["status"],
                latency_ms=tc["latency_ms"]
            ))
        await session.commit()
    else:
        agent = GuardedAgent()
        result = await agent.run(
            user_query=user_query,
            persona=req.persona,
            session=session,
            proxy=proxy,
            context={"seed": req.seed, "scenario_id": req.scenario_id},
            scenario_id=req.scenario_id,
            seed=req.seed
        )

    return result

@router.get("/{run_id}")
async def get_run_details(run_id: str, session: AsyncSession = Depends(get_db)):
    """Retrieve summary details for an executed agent run."""
    stmt = select(AgentRun).where(AgentRun.id == run_id)
    res = await session.execute(stmt)
    run = res.scalar_one_or_none()
    if not run:
        raise HTTPException(status_code=404, detail=f"Run '{run_id}' not found.")

    return {
        "run_id": run.id,
        "scenario_id": run.scenario_id,
        "agent_mode": run.agent_mode,
        "seed": run.seed,
        "user_query": run.user_query,
        "status": run.status,
        "final_outcome": run.final_outcome,
        "latency_ms": run.latency_ms,
        "token_usage": run.token_usage,
        "cost_usd": run.cost_usd,
        "created_at": run.created_at.isoformat() if run.created_at else None
    }

@router.get("/{run_id}/trace")
async def get_run_trace(run_id: str, session: AsyncSession = Depends(get_db)):
    """Retrieve full execution trace: LangGraph nodes, policy decisions, and tool calls."""
    run_stmt = select(AgentRun).where(AgentRun.id == run_id)
    run = (await session.execute(run_stmt)).scalar_one_or_none()
    if not run:
        raise HTTPException(status_code=404, detail=f"Run '{run_id}' not found.")

    # Events
    ev_stmt = select(AgentEvent).where(AgentEvent.run_id == run_id).order_by(AgentEvent.step_index.asc())
    events = (await session.execute(ev_stmt)).scalars().all()

    # Tool calls
    tc_stmt = select(ToolCall).where(ToolCall.run_id == run_id).order_by(ToolCall.created_at.asc())
    tool_calls = (await session.execute(tc_stmt)).scalars().all()

    # Policy decisions
    pd_stmt = select(PolicyDecision).where(PolicyDecision.run_id == run_id)
    policies = (await session.execute(pd_stmt)).scalars().all()

    # Evidence receipt
    er_stmt = select(EvidenceReceipt).where(EvidenceReceipt.run_id == run_id)
    receipt = (await session.execute(er_stmt)).scalar_one_or_none()

    return {
        "run_id": run.id,
        "scenario_id": run.scenario_id,
        "agent_mode": run.agent_mode,
        "user_query": run.user_query,
        "status": run.status,
        "final_outcome": run.final_outcome,
        "latency_ms": run.latency_ms,
        "events": [
            {
                "step_index": e.step_index,
                "node_name": e.node_name,
                "event_type": e.event_type,
                "payload": e.payload_json,
                "timestamp": e.timestamp.isoformat() if e.timestamp else None
            }
            for e in events
        ],
        "tool_calls": [
            {
                "tool_name": tc.tool_name,
                "arguments": tc.arguments_json,
                "response": tc.response_json,
                "status": tc.status,
                "latency_ms": tc.latency_ms,
                "idempotency_key": tc.idempotency_key
            }
            for tc in tool_calls
        ],
        "policy_decisions": [
            {
                "rule_name": pd.rule_name,
                "decision": pd.decision,
                "reason": pd.reason,
                "context": pd.context_json
            }
            for pd in policies
        ],
        "evidence_receipt": {
            "receipt_id": receipt.id,
            "event_hash": receipt.event_hash,
            "previous_event_hash": receipt.previous_event_hash,
            "payload_hash": receipt.payload_hash,
            "signature": receipt.signature
        } if receipt else None
    }

@router.post("/{run_id}/replay")
async def replay_run(run_id: str, req: ReplayRunRequest, session: AsyncSession = Depends(get_db)):
    """Deterministically replay a past run with identical seed, mode, and faults."""
    run_stmt = select(AgentRun).where(AgentRun.id == run_id)
    orig_run = (await session.execute(run_stmt)).scalar_one_or_none()
    if not orig_run:
        raise HTTPException(status_code=404, detail=f"Original run '{run_id}' not found.")

    seed = req.override_seed if req.override_seed is not None else orig_run.seed
    create_req = CreateRunRequest(
        query=orig_run.user_query,
        scenario_id=orig_run.scenario_id,
        agent_mode=orig_run.agent_mode,
        seed=seed
    )
    return await create_agent_run(create_req, session)
