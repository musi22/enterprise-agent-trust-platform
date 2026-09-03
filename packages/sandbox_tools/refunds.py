from typing import Dict, Any, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from apps.api.app.db.models import RefundRequest, Order, IdempotencyKey, OutboxEvent, generate_uuid
from packages.sandbox_tools.context import ToolContext
from apps.api.app.core.config import settings

async def request_refund(
    session: AsyncSession,
    ctx: ToolContext,
    order_id: str,
    user_id: str,
    amount_cents: int,
    reason: str,
    idempotency_key: str
) -> Dict[str, Any]:
    """Request a refund for an order with strict idempotency and approval thresholds."""
    # 1. Idempotency Check
    idemp_stmt = select(IdempotencyKey).where(IdempotencyKey.key == idempotency_key)
    idemp_res = await session.execute(idemp_stmt)
    existing_idemp = idemp_res.scalar_one_or_none()

    if existing_idemp and existing_idemp.status == "completed" and existing_idemp.result_payload:
        return {
            "status": "success",
            "is_duplicate_replay": True,
            "message": "Refund request already processed under this idempotency key.",
            **existing_idemp.result_payload
        }

    if not existing_idemp:
        existing_idemp = IdempotencyKey(
            key=idempotency_key,
            scope="request_refund",
            status="started"
        )
        session.add(existing_idemp)
        await session.flush()

    # 2. Verify Order
    ord_stmt = select(Order).where(Order.id == order_id)
    ord_res = await session.execute(ord_stmt)
    order = ord_res.scalar_one_or_none()

    if not order:
        return {"status": "error", "error_code": "ORDER_NOT_FOUND", "message": f"Order '{order_id}' was not found."}

    if amount_cents > order.total_cents:
        return {
            "status": "error",
            "error_code": "INVALID_REFUND_AMOUNT",
            "message": f"Refund amount ${amount_cents / 100:.2f} cannot exceed order total ${order.total_cents / 100:.2f}."
        }

    # 3. Determine status based on threshold
    threshold = settings.REFUND_APPROVAL_THRESHOLD_CENTS
    requires_approval = amount_cents > threshold
    refund_status = "pending_approval" if requires_approval else "approved"

    refund_id = generate_uuid()
    refund = RefundRequest(
        id=refund_id,
        order_id=order_id,
        user_id=user_id,
        amount_cents=amount_cents,
        reason=reason,
        status=refund_status,
        idempotency_key=idempotency_key
    )
    session.add(refund)

    outbox = OutboxEvent(
        event_type="REFUND_REQUESTED",
        aggregate_type="refund",
        aggregate_id=refund_id,
        payload={
            "refund_id": refund_id,
            "order_id": order_id,
            "user_id": user_id,
            "amount_cents": amount_cents,
            "requires_approval": requires_approval,
            "status": refund_status
        }
    )
    session.add(outbox)

    result_payload = {
        "refund_id": refund_id,
        "order_id": order_id,
        "amount_cents": amount_cents,
        "amount_formatted": f"${amount_cents / 100:.2f}",
        "refund_status": refund_status,
        "requires_human_approval": requires_approval,
        "reason": reason
    }

    existing_idemp.status = "completed"
    existing_idemp.result_payload = result_payload

    await session.commit()
    return {"status": "success", "is_duplicate_replay": False, **result_payload}


async def get_refund_status(
    session: AsyncSession,
    ctx: ToolContext,
    refund_id: str,
    user_id: Optional[str] = None
) -> Dict[str, Any]:
    """Check current status and decision details of a refund request."""
    stmt = select(RefundRequest).where(RefundRequest.id == refund_id)
    res = await session.execute(stmt)
    refund = res.scalar_one_or_none()

    if not refund:
        return {"status": "error", "error_code": "REFUND_NOT_FOUND", "message": f"Refund '{refund_id}' was not found."}

    return {
        "status": "success",
        "refund": {
            "refund_id": refund.id,
            "order_id": refund.order_id,
            "user_id": refund.user_id,
            "amount_cents": refund.amount_cents,
            "amount_formatted": f"${refund.amount_cents / 100:.2f}",
            "status": refund.status,
            "reason": refund.reason,
            "created_at": refund.created_at.isoformat() if refund.created_at else None
        }
    }
