from typing import Dict, Any, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from apps.api.app.db.models import Approval, OutboxEvent, generate_uuid
from packages.sandbox_tools.context import ToolContext

async def escalate_to_human(
    session: AsyncSession,
    ctx: ToolContext,
    issue_type: str,
    summary: str,
    context_details: Optional[Dict[str, Any]] = None
) -> Dict[str, Any]:
    """Escalate ambiguous, high-risk, or policy-restricted actions to a human operator."""
    approval_id = generate_uuid()
    run_id = ctx.run_id or generate_uuid()

    approval = Approval(
        id=approval_id,
        run_id=run_id,
        action_type=issue_type,
        proposed_payload_json={
            "summary": summary,
            "user_id": ctx.user_id,
            "user_role": ctx.user_role,
            "context": context_details or {}
        },
        status="pending",
        reason=summary
    )
    session.add(approval)

    outbox = OutboxEvent(
        event_type="HUMAN_ESCALATION_TRIGGERED",
        aggregate_type="approval",
        aggregate_id=approval_id,
        payload={
            "approval_id": approval_id,
            "run_id": run_id,
            "issue_type": issue_type,
            "summary": summary
        }
    )
    session.add(outbox)
    await session.commit()

    return {
        "status": "escalated",
        "approval_id": approval_id,
        "issue_type": issue_type,
        "summary": summary,
        "message": "Action paused and dispatched to human supervisor for review."
    }
