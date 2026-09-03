from typing import List, Dict, Any, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, or_
from apps.api.app.db.models import Product, Inventory
from packages.sandbox_tools.context import ToolContext

async def search_catalog(
    session: AsyncSession,
    ctx: ToolContext,
    query: str,
    category: Optional[str] = None,
    max_price_cents: Optional[int] = None,
    limit: int = 10
) -> Dict[str, Any]:
    """Search synthetic product catalog by keyword, optional category, and max price."""
    stmt = select(Product).where(Product.active == True)

    if query:
        search_filter = or_(
            Product.title.ilike(f"%{query}%"),
            Product.description.ilike(f"%{query}%"),
            Product.sku.ilike(f"%{query}%")
        )
        stmt = stmt.where(search_filter)

    if category:
        stmt = stmt.where(Product.category.ilike(f"%{category}%"))

    if max_price_cents is not None:
        stmt = stmt.where(Product.price_cents <= max_price_cents)

    stmt = stmt.limit(limit)
    res = await session.execute(stmt)
    products = res.scalars().all()

    items = []
    for p in products:
        items.append({
            "product_id": p.id,
            "sku": p.sku,
            "title": p.title,
            "category": p.category,
            "price_cents": p.price_cents,
            "price_formatted": f"${p.price_cents / 100:.2f}",
            "stock_level": p.stock_level,
            "in_stock": p.stock_level > 0,
            "description": p.description
        })

    return {
        "status": "success",
        "query": query,
        "total_found": len(items),
        "products": items
    }


async def get_product(
    session: AsyncSession,
    ctx: ToolContext,
    product_id: str
) -> Dict[str, Any]:
    """Retrieve full details and inventory for a specific product ID."""
    stmt = select(Product).where(Product.id == product_id)
    res = await session.execute(stmt)
    p = res.scalar_one_or_none()

    if not p:
        return {
            "status": "error",
            "error_code": "PRODUCT_NOT_FOUND",
            "message": f"Product with ID '{product_id}' was not found in catalog."
        }

    return {
        "status": "success",
        "product": {
            "product_id": p.id,
            "sku": p.sku,
            "title": p.title,
            "category": p.category,
            "price_cents": p.price_cents,
            "price_formatted": f"${p.price_cents / 100:.2f}",
            "stock_level": p.stock_level,
            "in_stock": p.stock_level > 0,
            "description": p.description,
            "active": p.active
        }
    }


async def check_inventory(
    session: AsyncSession,
    ctx: ToolContext,
    product_id: str
) -> Dict[str, Any]:
    """Check verified real-time warehouse inventory for a product."""
    stmt = select(Inventory).where(Inventory.product_id == product_id)
    res = await session.execute(stmt)
    inv = res.scalar_one_or_none()

    if not inv:
        return {
            "status": "error",
            "error_code": "INVENTORY_RECORD_NOT_FOUND",
            "message": f"No inventory record found for product ID '{product_id}'."
        }

    return {
        "status": "success",
        "product_id": product_id,
        "available_stock": inv.available_stock,
        "reserved_stock": inv.reserved_stock,
        "in_stock": inv.available_stock > 0
    }
