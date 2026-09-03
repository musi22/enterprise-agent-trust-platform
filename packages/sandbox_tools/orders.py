from typing import List, Dict, Any, Optional
import json
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.orm import selectinload
from apps.api.app.db.models import (
    Order, OrderItem, Cart, CartItem, Product, Inventory, IdempotencyKey, OutboxEvent, generate_uuid
)
from packages.sandbox_tools.context import ToolContext

async def add_to_cart(
    session: AsyncSession,
    ctx: ToolContext,
    product_id: str,
    quantity: int = 1
) -> Dict[str, Any]:
    """Add product items to the authenticated user's active cart."""
    # Find or create active cart
    stmt = select(Cart).where(Cart.user_id == ctx.user_id, Cart.status == "active")
    res = await session.execute(stmt)
    cart = res.scalar_one_or_none()

    if not cart:
        cart = Cart(user_id=ctx.user_id, status="active")
        session.add(cart)
        await session.flush()

    # Fetch product for pricing
    prod_stmt = select(Product).where(Product.id == product_id)
    prod_res = await session.execute(prod_stmt)
    product = prod_res.scalar_one_or_none()
    if not product:
        return {"status": "error", "error_code": "PRODUCT_NOT_FOUND", "message": f"Product '{product_id}' not found."}

    # Check if item already exists in cart
    item_stmt = select(CartItem).where(CartItem.cart_id == cart.id, CartItem.product_id == product_id)
    item_res = await session.execute(item_stmt)
    item = item_res.scalar_one_or_none()

    if item:
        item.quantity += quantity
    else:
        item = CartItem(
            cart_id=cart.id,
            product_id=product_id,
            quantity=quantity,
            unit_price_cents=product.price_cents
        )
        session.add(item)

    await session.commit()
    return {
        "status": "success",
        "cart_id": cart.id,
        "product_id": product_id,
        "quantity_added": quantity,
        "product_title": product.title
    }


async def create_order(
    session: AsyncSession,
    ctx: ToolContext,
    user_id: str,
    items: List[Dict[str, Any]],
    shipping_address: str,
    idempotency_key: str
) -> Dict[str, Any]:
    """
    Create a new order with atomic inventory deduction, outbox event generation, 
    and strict idempotency enforcement.
    """
    # 1. Check Idempotency Key
    idemp_stmt = select(IdempotencyKey).where(IdempotencyKey.key == idempotency_key)
    idemp_res = await session.execute(idemp_stmt)
    existing_idemp = idemp_res.scalar_one_or_none()

    if existing_idemp and existing_idemp.status == "completed" and existing_idemp.result_payload:
        return {
            "status": "success",
            "is_duplicate_replay": True,
            "message": "Order already processed under this idempotency key.",
            **existing_idemp.result_payload
        }

    if not existing_idemp:
        existing_idemp = IdempotencyKey(
            key=idempotency_key,
            scope="create_order",
            status="started"
        )
        session.add(existing_idemp)
        await session.flush()

    # 2. Check and reserve inventory for all items
    total_cents = 0
    order_id = generate_uuid()
    created_items = []

    for it in items:
        p_id = it["product_id"]
        qty = it.get("quantity", 1)

        # Inventory check
        inv_stmt = select(Inventory).where(Inventory.product_id == p_id)
        inv_res = await session.execute(inv_stmt)
        inv = inv_res.scalar_one_or_none()

        if not inv or inv.available_stock < qty:
            available = inv.available_stock if inv else 0
            await session.rollback()
            return {
                "status": "error",
                "error_code": "INSUFFICIENT_STOCK",
                "message": f"Insufficient stock for product '{p_id}'. Requested: {qty}, Available: {available}"
            }

        # Product details
        prod_stmt = select(Product).where(Product.id == p_id)
        prod_res = await session.execute(prod_stmt)
        product = prod_res.scalar_one_or_none()
        price = product.price_cents if product else it.get("unit_price_cents", 0)

        # Deduct stock
        inv.available_stock -= qty
        inv.reserved_stock += qty

        total_cents += price * qty
        created_items.append(OrderItem(
            order_id=order_id,
            product_id=p_id,
            quantity=qty,
            unit_price_cents=price
        ))

    # 3. Create Order
    order = Order(
        id=order_id,
        user_id=user_id,
        order_status="confirmed",
        shipping_address=shipping_address,
        total_cents=total_cents,
        idempotency_key=idempotency_key
    )
    session.add(order)
    for oi in created_items:
        session.add(oi)

    # 4. Create Transactional Outbox Event
    outbox_event = OutboxEvent(
        event_type="ORDER_CREATED",
        aggregate_type="order",
        aggregate_id=order_id,
        payload={
            "order_id": order_id,
            "user_id": user_id,
            "total_cents": total_cents,
            "items_count": len(created_items),
            "idempotency_key": idempotency_key
        }
    )
    session.add(outbox_event)

    result_payload = {
        "order_id": order_id,
        "user_id": user_id,
        "order_status": "confirmed",
        "total_cents": total_cents,
        "total_formatted": f"${total_cents / 100:.2f}",
        "shipping_address": shipping_address,
        "items_count": len(created_items)
    }

    # Update idempotency key status
    existing_idemp.status = "completed"
    existing_idemp.result_payload = result_payload

    await session.commit()
    return {"status": "success", "is_duplicate_replay": False, **result_payload}


async def get_order(
    session: AsyncSession,
    ctx: ToolContext,
    order_id: str,
    user_id: Optional[str] = None
) -> Dict[str, Any]:
    """Retrieve full details of an order, including status and line items."""
    stmt = (
        select(Order)
        .options(selectinload(Order.items).selectinload(OrderItem.product))
        .where(Order.id == order_id)
    )
    res = await session.execute(stmt)
    order = res.scalar_one_or_none()

    if not order:
        return {
            "status": "error",
            "error_code": "ORDER_NOT_FOUND",
            "message": f"Order '{order_id}' was not found."
        }

    items_list = []
    for it in order.items:
        items_list.append({
            "product_id": it.product_id,
            "title": it.product.title if it.product else "Unknown Product",
            "quantity": it.quantity,
            "unit_price_cents": it.unit_price_cents,
            "unit_price_formatted": f"${it.unit_price_cents / 100:.2f}",
            "total_price_formatted": f"${(it.unit_price_cents * it.quantity) / 100:.2f}"
        })

    return {
        "status": "success",
        "order": {
            "order_id": order.id,
            "user_id": order.user_id,
            "order_status": order.order_status,
            "shipping_address": order.shipping_address,
            "total_cents": order.total_cents,
            "total_formatted": f"${order.total_cents / 100:.2f}",
            "created_at": order.created_at.isoformat() if order.created_at else None,
            "items": items_list
        }
    }


async def update_delivery_address(
    session: AsyncSession,
    ctx: ToolContext,
    order_id: str,
    user_id: str,
    new_address: str,
    idempotency_key: str
) -> Dict[str, Any]:
    """Update delivery address if order has not yet shipped."""
    stmt = select(Order).where(Order.id == order_id)
    res = await session.execute(stmt)
    order = res.scalar_one_or_none()

    if not order:
        return {"status": "error", "error_code": "ORDER_NOT_FOUND", "message": f"Order '{order_id}' not found."}

    if order.order_status in ["shipped", "delivered", "cancelled"]:
        return {
            "status": "error",
            "error_code": "INVALID_STATE_FOR_UPDATE",
            "message": f"Cannot update address: Order status is '{order.order_status}'."
        }

    old_address = order.shipping_address
    order.shipping_address = new_address

    outbox = OutboxEvent(
        event_type="ORDER_ADDRESS_UPDATED",
        aggregate_type="order",
        aggregate_id=order_id,
        payload={"order_id": order_id, "old_address": old_address, "new_address": new_address}
    )
    session.add(outbox)
    await session.commit()

    return {
        "status": "success",
        "order_id": order_id,
        "new_address": new_address,
        "previous_address": old_address,
        "order_status": order.order_status
    }


async def cancel_order(
    session: AsyncSession,
    ctx: ToolContext,
    order_id: str,
    user_id: str,
    reason: str,
    idempotency_key: str
) -> Dict[str, Any]:
    """Cancel order and restore stock if order has not shipped."""
    stmt = select(Order).options(selectinload(Order.items)).where(Order.id == order_id)
    res = await session.execute(stmt)
    order = res.scalar_one_or_none()

    if not order:
        return {"status": "error", "error_code": "ORDER_NOT_FOUND", "message": f"Order '{order_id}' not found."}

    if order.order_status in ["shipped", "delivered"]:
        return {
            "status": "error",
            "error_code": "CANNOT_CANCEL_SHIPPED_ORDER",
            "message": f"Order '{order_id}' cannot be cancelled because it has already been {order.order_status}."
        }

    if order.order_status == "cancelled":
        return {
            "status": "error",
            "error_code": "ALREADY_CANCELLED",
            "message": f"Order '{order_id}' is already cancelled."
        }

    # Restock inventory
    for it in order.items:
        inv_stmt = select(Inventory).where(Inventory.product_id == it.product_id)
        inv_res = await session.execute(inv_stmt)
        inv = inv_res.scalar_one_or_none()
        if inv:
            inv.available_stock += it.quantity
            if inv.reserved_stock >= it.quantity:
                inv.reserved_stock -= it.quantity

    order.order_status = "cancelled"

    outbox = OutboxEvent(
        event_type="ORDER_CANCELLED",
        aggregate_type="order",
        aggregate_id=order_id,
        payload={"order_id": order_id, "reason": reason}
    )
    session.add(outbox)
    await session.commit()

    return {
        "status": "success",
        "order_id": order_id,
        "order_status": "cancelled",
        "reason": reason
    }
