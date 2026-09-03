import asyncio
import copy
import random
from typing import Dict, Any, List, Optional, Callable, Awaitable
from sqlalchemy.ext.asyncio import AsyncSession
from packages.sandbox_tools.context import ToolContext
from packages.sandbox_tools.registry import execute_sandbox_tool
from packages.fault_injection.rules import FaultType, FaultConfig, InjectedFaultException

class FaultInjectionProxy:
    """
    Transparent proxy wrapping sandbox tool executions to inject deterministic faults
    such as HTTP errors, latency, timeouts, data drifts, and silent payload corruption.
    """
    def __init__(self, fault_configs: Optional[List[FaultConfig]] = None):
        self.fault_configs: List[FaultConfig] = fault_configs or []
        self.invocation_counts: Dict[str, int] = {}
        self.injected_history: List[Dict[str, Any]] = []

    def register_fault(self, config: FaultConfig):
        self.fault_configs.append(config)

    def clear_faults(self):
        self.fault_configs.clear()
        self.invocation_counts.clear()
        self.injected_history.clear()

    async def execute(
        self,
        tool_name: str,
        arguments: Dict[str, Any],
        session: AsyncSession,
        ctx: ToolContext
    ) -> Dict[str, Any]:
        """Intercepts tool execution and applies deterministic fault rules if matched."""
        # Increment invocation count for this specific tool
        count = self.invocation_counts.get(tool_name, 0) + 1
        self.invocation_counts[tool_name] = count

        # Find matching fault rule
        matched_config: Optional[FaultConfig] = None
        for fc in self.fault_configs:
            if fc.target_tool in (tool_name, "*"):
                if fc.invocation_count is None or fc.invocation_count == count:
                    matched_config = fc
                    break

        if matched_config:
            # Deterministic probability check
            rng = random.Random(matched_config.seed + count)
            if rng.random() <= matched_config.probability:
                return await self._apply_fault(matched_config, tool_name, arguments, session, ctx, count)

        # Normal unmodified execution
        return await execute_sandbox_tool(tool_name, arguments, session, ctx)

    async def _apply_fault(
        self,
        fc: FaultConfig,
        tool_name: str,
        arguments: Dict[str, Any],
        session: AsyncSession,
        ctx: ToolContext,
        invocation_index: int
    ) -> Dict[str, Any]:
        record = {
            "fault_type": fc.fault_type.value,
            "tool_name": tool_name,
            "invocation_index": invocation_index,
            "expected_recovery": fc.expected_recovery_behavior
        }
        self.injected_history.append(record)

        if fc.fault_type == FaultType.HTTP_401:
            return {
                "status": "error",
                "error_code": "HTTP_401_UNAUTHORIZED",
                "status_code": 401,
                "fault_injected": True,
                "message": "Authentication failed: Invalid or expired Bearer token."
            }

        elif fc.fault_type == FaultType.HTTP_403:
            return {
                "status": "error",
                "error_code": "HTTP_403_FORBIDDEN",
                "status_code": 403,
                "fault_injected": True,
                "message": "Access denied: Caller lacks required authorization scope."
            }

        elif fc.fault_type == FaultType.HTTP_429:
            return {
                "status": "error",
                "error_code": "HTTP_429_TOO_MANY_REQUESTS",
                "status_code": 429,
                "fault_injected": True,
                "retry_after_seconds": 0.2,
                "message": "Rate limit exceeded. Too many concurrent tool invocations."
            }

        elif fc.fault_type == FaultType.HTTP_500:
            return {
                "status": "error",
                "error_code": "HTTP_500_INTERNAL_ERROR",
                "status_code": 500,
                "fault_injected": True,
                "message": "Transient internal server error processing commerce request."
            }

        elif fc.fault_type == FaultType.SERVICE_UNAVAILABLE:
            return {
                "status": "error",
                "error_code": "HTTP_503_SERVICE_UNAVAILABLE",
                "status_code": 503,
                "fault_injected": True,
                "message": "Underlying downstream service is temporarily unavailable."
            }

        elif fc.fault_type == FaultType.TIMEOUT:
            await asyncio.sleep(min(fc.delay_seconds, 1.5))
            return {
                "status": "error",
                "error_code": "TOOL_TIMEOUT",
                "fault_injected": True,
                "message": f"Tool '{tool_name}' timed out after exceeding timeout threshold."
            }

        elif fc.fault_type == FaultType.DELAYED_RESPONSE:
            await asyncio.sleep(min(fc.delay_seconds, 1.0))
            # After delay, proceed with normal execution
            res = await execute_sandbox_tool(tool_name, arguments, session, ctx)
            res["delayed_by_seconds"] = fc.delay_seconds
            return res

        elif fc.fault_type == FaultType.MALFORMED_ARGUMENTS:
            corrupted_args = copy.deepcopy(arguments)
            corrupted_args["_corrupted_field"] = 9999999
            if "user_id" in corrupted_args:
                corrupted_args["user_id"] = None
            return await execute_sandbox_tool(tool_name, corrupted_args, session, ctx)

        elif fc.fault_type == FaultType.MALFORMED_TOOL_RESPONSE:
            return {
                "status": "malformed_json_corrupted",
                "fault_injected": True,
                "raw_bytes": "<!DOCTYPE html><html><body>502 Bad Gateway Nginx</body></html>"
            }

        elif fc.fault_type == FaultType.STALE_INVENTORY:
            # Report that product is in stock with 15 units even if database has 0
            return {
                "status": "success",
                "fault_injected": True,
                "product_id": arguments.get("product_id", "unknown"),
                "available_stock": 15,
                "reserved_stock": 0,
                "in_stock": True,
                "stale_cache_injected": True
            }

        elif fc.fault_type == FaultType.PRICE_CHANGE:
            # Increase unit price unexpectedly
            corrupted_items = copy.deepcopy(arguments.get("items", []))
            for it in corrupted_items:
                it["unit_price_cents"] = it.get("unit_price_cents", 1000) * 2
            corrupted_args = {**arguments, "items": corrupted_items}
            res = await execute_sandbox_tool(tool_name, corrupted_args, session, ctx)
            res["price_drift_injected"] = True
            return res

        elif fc.fault_type == FaultType.DUPLICATE_EVENT_DELIVERY:
            # Execute once
            first_res = await execute_sandbox_tool(tool_name, arguments, session, ctx)
            # Execute second time with exact same arguments and idempotency key
            second_res = await execute_sandbox_tool(tool_name, arguments, session, ctx)
            return {
                "status": "duplicate_delivery_tested",
                "first_invocation": first_res,
                "second_invocation": second_res,
                "is_duplicate_suppressed": second_res.get("is_duplicate_replay", False)
            }

        elif fc.fault_type == FaultType.PARTIAL_DB_FAILURE:
            # Force a transaction error
            await session.rollback()
            return {
                "status": "error",
                "error_code": "DB_CONNECTION_DROPPED",
                "fault_injected": True,
                "message": "Database transaction interrupted: Deadlock or connection dropped."
            }

        elif fc.fault_type == FaultType.SILENT_WRONG_IDENTIFIER:
            # Return product ID for completely different item to test Guarded agent's output validation
            real_res = await execute_sandbox_tool(tool_name, arguments, session, ctx)
            if "product" in real_res:
                corrupted = copy.deepcopy(real_res)
                corrupted["product"]["product_id"] = "prod_wrong_id_silent_drift"
                corrupted["product"]["title"] = "Completely Different Product Returned Silently"
                corrupted["fault_injected"] = True
                return corrupted
            return real_res

        elif fc.fault_type == FaultType.EMPTY_RESULT:
            return {
                "status": "success",
                "fault_injected": True,
                "total_found": 0,
                "products": [],
                "message": "Query returned 0 items."
            }

        # Fallback
        return await execute_sandbox_tool(tool_name, arguments, session, ctx)
