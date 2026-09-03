from typing import Dict, Any, Callable, Awaitable
from sqlalchemy.ext.asyncio import AsyncSession
from packages.sandbox_tools.context import ToolContext
from packages.sandbox_tools.catalog import search_catalog, get_product, check_inventory
from packages.sandbox_tools.orders import add_to_cart, create_order, get_order, update_delivery_address, cancel_order
from packages.sandbox_tools.refunds import request_refund, get_refund_status
from packages.sandbox_tools.escalation import escalate_to_human

TOOL_REGISTRY: Dict[str, Callable[..., Awaitable[Dict[str, Any]]]] = {
    "search_catalog": search_catalog,
    "get_product": get_product,
    "check_inventory": check_inventory,
    "add_to_cart": add_to_cart,
    "create_order": create_order,
    "get_order": get_order,
    "update_delivery_address": update_delivery_address,
    "cancel_order": cancel_order,
    "request_refund": request_refund,
    "get_refund_status": get_refund_status,
    "escalate_to_human": escalate_to_human,
}

TOOL_SCHEMAS = {
    "search_catalog": {
        "description": "Search product catalog by keyword, optional category and price limit.",
        "parameters": {
            "query": {"type": "string", "required": True},
            "category": {"type": "string", "required": False},
            "max_price_cents": {"type": "integer", "required": False},
            "limit": {"type": "integer", "required": False, "default": 10}
        }
    },
    "get_product": {
        "description": "Get detailed specs and pricing for a product ID.",
        "parameters": {
            "product_id": {"type": "string", "required": True}
        }
    },
    "check_inventory": {
        "description": "Check current available warehouse stock level for a product ID.",
        "parameters": {
            "product_id": {"type": "string", "required": True}
        }
    },
    "add_to_cart": {
        "description": "Add product items into active cart.",
        "parameters": {
            "product_id": {"type": "string", "required": True},
            "quantity": {"type": "integer", "required": False, "default": 1}
        }
    },
    "create_order": {
        "description": "Submit a confirmed order with line items, shipping address, and idempotency key.",
        "parameters": {
            "user_id": {"type": "string", "required": True},
            "items": {"type": "array", "required": True},
            "shipping_address": {"type": "string", "required": True},
            "idempotency_key": {"type": "string", "required": True}
        }
    },
    "get_order": {
        "description": "Look up order status and items.",
        "parameters": {
            "order_id": {"type": "string", "required": True},
            "user_id": {"type": "string", "required": False}
        }
    },
    "update_delivery_address": {
        "description": "Modify the delivery destination of an order prior to shipping.",
        "parameters": {
            "order_id": {"type": "string", "required": True},
            "user_id": {"type": "string", "required": True},
            "new_address": {"type": "string", "required": True},
            "idempotency_key": {"type": "string", "required": True}
        }
    },
    "cancel_order": {
        "description": "Cancel an order prior to shipment and restock items.",
        "parameters": {
            "order_id": {"type": "string", "required": True},
            "user_id": {"type": "string", "required": True},
            "reason": {"type": "string", "required": True},
            "idempotency_key": {"type": "string", "required": True}
        }
    },
    "request_refund": {
        "description": "Submit a refund request for an existing order.",
        "parameters": {
            "order_id": {"type": "string", "required": True},
            "user_id": {"type": "string", "required": True},
            "amount_cents": {"type": "integer", "required": True},
            "reason": {"type": "string", "required": True},
            "idempotency_key": {"type": "string", "required": True}
        }
    },
    "get_refund_status": {
        "description": "Retrieve status of an existing refund request.",
        "parameters": {
            "refund_id": {"type": "string", "required": True},
            "user_id": {"type": "string", "required": False}
        }
    },
    "escalate_to_human": {
        "description": "Escalate ambiguous, risky, or blocked actions to human supervisors.",
        "parameters": {
            "issue_type": {"type": "string", "required": True},
            "summary": {"type": "string", "required": True},
            "context_details": {"type": "object", "required": False}
        }
    }
}

async def execute_sandbox_tool(
    tool_name: str,
    arguments: Dict[str, Any],
    session: AsyncSession,
    ctx: ToolContext
) -> Dict[str, Any]:
    """Dispatches tool call to corresponding registered handler."""
    if tool_name not in TOOL_REGISTRY:
        return {
            "status": "error",
            "error_code": "UNKNOWN_TOOL",
            "message": f"Tool '{tool_name}' is not registered in the commerce sandbox."
        }

    handler = TOOL_REGISTRY[tool_name]
    try:
        return await handler(session, ctx, **arguments)
    except TypeError as e:
        return {
            "status": "error",
            "error_code": "INVALID_TOOL_ARGUMENTS",
            "message": f"Argument signature mismatch for tool '{tool_name}': {str(e)}"
        }
    except Exception as e:
        return {
            "status": "error",
            "error_code": "TOOL_EXECUTION_EXCEPTION",
            "message": f"Tool '{tool_name}' failed with unexpected exception: {str(e)}"
        }
