from fastapi import APIRouter
from packages.policies.engine import policy_engine
from packages.policies.rules import ROLE_ALLOWED_TOOLS
from apps.api.app.core.config import settings

router = APIRouter(prefix="/policies", tags=["Policies & Guardrails"])

@router.get("")
async def list_policies():
    """List all registered policy rules, tool allowlists, and safety thresholds."""
    rules_info = [
        {
            "rule_name": r.rule_name,
            "description": r.__doc__ or r.rule_name.replace("_", " ").title(),
            "status": "active"
        }
        for r in policy_engine.rules
    ]

    return {
        "active_rules_count": len(rules_info),
        "rules": rules_info,
        "role_tool_allowlists": {role: sorted(list(tools)) for role, tools in ROLE_ALLOWED_TOOLS.items()},
        "thresholds": {
            "refund_approval_threshold_cents": settings.REFUND_APPROVAL_THRESHOLD_CENTS,
            "refund_approval_threshold_formatted": f"${settings.REFUND_APPROVAL_THRESHOLD_CENTS / 100:.2f}",
            "max_recovery_retries": settings.MAX_RECOVERY_RETRIES,
            "circuit_breaker_threshold": settings.CIRCUIT_BREAKER_FAILURE_THRESHOLD
        }
    }
