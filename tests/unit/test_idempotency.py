import pytest
from sqlalchemy import select, func
from packages.sandbox_tools.orders import create_order
from packages.sandbox_tools.refunds import request_refund
from packages.sandbox_tools.context import ToolContext
from apps.api.app.db.models import Order, RefundRequest

@pytest.mark.asyncio
async def test_duplicate_create_order_idempotency(db_session):
    ctx = ToolContext(user_id="usr_cust_001")
    key = "idemp_test_duplicate_ord_999"

    items = [{"product_id": "prod_elec_002", "quantity": 1, "unit_price_cents": 3499}]
    addr = "742 Evergreen Terrace"

    # Call 1: Original creation
    res1 = await create_order(db_session, ctx, user_id="usr_cust_001", items=items, shipping_address=addr, idempotency_key=key)
    assert res1["status"] == "success"
    assert res1["is_duplicate_replay"] is False
    order_id = res1["order_id"]

    # Call 2: Duplicate delivery with exact same idempotency key
    res2 = await create_order(db_session, ctx, user_id="usr_cust_001", items=items, shipping_address=addr, idempotency_key=key)
    assert res2["status"] == "success"
    assert res2["is_duplicate_replay"] is True
    assert res2["order_id"] == order_id  # Returns original order ID

    # Verify exactly ONE order was created in DB
    stmt = select(func.count(Order.id)).where(Order.idempotency_key == key)
    count = (await db_session.execute(stmt)).scalar()
    assert count == 1

@pytest.mark.asyncio
async def test_duplicate_refund_idempotency(db_session):
    ctx = ToolContext(user_id="usr_cust_001")
    key = "idemp_test_duplicate_ref_888"

    # Call 1: Original refund request for ord_1001
    res1 = await request_refund(db_session, ctx, order_id="ord_1001", user_id="usr_cust_001", amount_cents=1500, reason="test", idempotency_key=key)
    assert res1["status"] == "success"
    assert res1["is_duplicate_replay"] is False
    refund_id = res1["refund_id"]

    # Call 2: Duplicate refund request
    res2 = await request_refund(db_session, ctx, order_id="ord_1001", user_id="usr_cust_001", amount_cents=1500, reason="test", idempotency_key=key)
    assert res2["status"] == "success"
    assert res2["is_duplicate_replay"] is True
    assert res2["refund_id"] == refund_id

    # Verify exactly ONE refund record created in DB
    stmt = select(func.count(RefundRequest.id)).where(RefundRequest.idempotency_key == key)
    count = (await db_session.execute(stmt)).scalar()
    assert count == 1
