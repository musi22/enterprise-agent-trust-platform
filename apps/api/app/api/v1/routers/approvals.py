from datetime import datetime, timezone
from typing import List, Dict, Any, Optional
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from apps.api.app.db.database import get_db
from apps.api.app.db.models import Approval, AgentRun

router = APIRouter(prefix="/approvals", tags=["Human Approval Inbox"])

class ApprovalDecisionRequest(BaseModel):
    decision: str  # "approved" or "rejected"
    decided_by: str = "supervisor_admin"
    reason: Optional[str] = "Decision rendered via engineering console approval inbox."

@router.get("")
async def list_approvals(status: Optional[str] = None, session: AsyncSession = Depends(get_db)):
    """List pending and historical human-in-the-loop approval requests."""
    stmt = select(Approval).order_by(Approval.created_at.desc())
    if status:
        stmt = stmt.where(Approval.status == status)

    res = await session.execute(stmt)
    approvals = res.scalars().all()

    return [
        {
            "approval_id": a.id,
            "run_id": a.run_id,
            "action_type": a.action_type,
            "status": a.status,
            "reason": a.reason,
            "proposed_payload": a.proposed_payload_json,
            "decided_by": a.decided_by,
            "decided_at": a.decided_at.isoformat() if a.decided_at else None,
            "created_at": a.created_at.isoformat() if a.created_at else None
        }
        for a in approvals
    ]

@router.post("/{approval_id}/decision")
async def decide_approval(
    approval_id: str,
    req: ApprovalDecisionRequest,
    session: AsyncSession = Depends(get_db)
):
    """Approve or reject a pending action requiring supervisor authorization."""
    stmt = select(Approval).where(Approval.id == approval_id)
    res = await session.execute(stmt)
    approval = res.scalar_one_or_none()

    if not approval:
        raise HTTPException(status_code=404, detail=f"Approval '{approval_id}' not found.")

    if approval.status != "pending":
        raise HTTPException(status_code=400, detail=f"Approval is already '{approval.status}'.")

    decision_norm = req.decision.lower()
    if decision_norm not in ("approved", "rejected"):
        raise HTTPException(status_code=400, detail="Decision must be 'approved' or 'rejected'.")

    approval.status = decision_norm
    approval.decided_by = req.decided_by
    approval.decided_at = datetime.now(timezone.utc)
    if req.reason:
        approval.reason = f"{approval.reason} | Decision Note: {req.reason}"

    # Update associated AgentRun record
    run_stmt = select(AgentRun).where(AgentRun.id == approval.run_id)
    run = (await session.execute(run_stmt)).scalar_one_or_none()
    if run:
        run.status = "approved" if decision_norm == "approved" else "rejected"
        run.final_outcome = f"Human supervisor {decision_norm} action. ({req.reason})"

    await session.commit()

    return {
        "status": "success",
        "approval_id": approval.id,
        "decision": approval.status,
        "decided_by": approval.decided_by,
        "decided_at": approval.decided_at.isoformat()
    }
