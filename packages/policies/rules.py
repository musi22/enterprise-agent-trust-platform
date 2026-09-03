import re
from typing import Optional
from packages.policies.models import PolicyContext, PolicyEvaluationResult, PolicyDecisionEnum
from apps.api.app.core.config import settings

# Tool Allowlist per role
ROLE_ALLOWED_TOOLS = {
    "customer": {
        "search_catalog",
        "get_product",
        "check_inventory",
        "add_to_cart",
        "create_order",
        "get_order",
        "update_delivery_address",
        "cancel_order",
        "request_refund",
        "get_refund_status",
        "escalate_to_human"
    },
    "support_agent": {
        "search_catalog",
        "get_product",
        "check_inventory",
        "add_to_cart",
        "create_order",
        "get_order",
        "update_delivery_address",
        "cancel_order",
        "request_refund",
        "get_refund_status",
        "escalate_to_human"
    },
    "admin": {
        "search_catalog",
        "get_product",
        "check_inventory",
        "add_to_cart",
        "create_order",
        "get_order",
        "update_delivery_address",
        "cancel_order",
        "request_refund",
        "get_refund_status",
        "escalate_to_human",
        "admin_adjust_inventory",
        "admin_override_refund",
        "admin_delete_order"
    }
}

WRITE_TOOLS = {
    "create_order",
    "update_delivery_address",
    "cancel_order",
    "request_refund",
    "admin_adjust_inventory",
    "admin_override_refund"
}

PROMPT_INJECTION_PATTERNS = [
    re.compile(r"(?i)\bignore\s+(?:all\s+)?(?:previous\s+)?instructions\b"),
    re.compile(r"(?i)\byou\s+are\s+now\s+(?:an?\s+)?(?:admin|root|system|superuser)\b"),
    re.compile(r"(?i)\bgrant\s+(?:me\s+)?admin\s+access\b"),
    re.compile(r"(?i)\bbypass\s+all\s+(?:security|policy|permission|guardrails?)\b"),
    re.compile(r"(?i)\bdisregard\s+(?:the\s+)?rules\b"),
    re.compile(r"(?i)\boverride\s+(?:authorization|authentication|rbac)\b")
]

class BasePolicyRule:
    rule_name: str = "base_rule"

    def evaluate(self, ctx: PolicyContext) -> Optional[PolicyEvaluationResult]:
        raise NotImplementedError


class PromptInjectionDefenseRule(BasePolicyRule):
    rule_name = "prompt_injection_defense"

    def evaluate(self, ctx: PolicyContext) -> Optional[PolicyEvaluationResult]:
        if not ctx.prompt_text:
            return None
        
        for pattern in PROMPT_INJECTION_PATTERNS:
            if pattern.search(ctx.prompt_text):
                return PolicyEvaluationResult(
                    decision=PolicyDecisionEnum.DENY,
                    rule_name=self.rule_name,
                    reason="Prompt text contains unauthorized privilege escalation or instruction override pattern.",
                    suggested_action="Reject query and log security incident."
                )
        return None


class ToolScopeAuthorizationRule(BasePolicyRule):
    rule_name = "tool_scope_authorization"

    def evaluate(self, ctx: PolicyContext) -> Optional[PolicyEvaluationResult]:
        allowed = ROLE_ALLOWED_TOOLS.get(ctx.user_role, set())
        if ctx.tool_name not in allowed:
            return PolicyEvaluationResult(
                decision=PolicyDecisionEnum.DENY,
                rule_name=self.rule_name,
                reason=f"Role '{ctx.user_role}' is not authorized to execute tool '{ctx.tool_name}'.",
                suggested_action="Escalate to administrator or block action."
            )
        return None


class ResourceOwnershipRule(BasePolicyRule):
    rule_name = "resource_ownership_check"

    def evaluate(self, ctx: PolicyContext) -> Optional[PolicyEvaluationResult]:
        # Admins and support agents may have wider access; customers strictly limited to their own resources
        if ctx.user_role == "customer":
            if ctx.order_owner_id and ctx.order_owner_id != ctx.user_id:
                return PolicyEvaluationResult(
                    decision=PolicyDecisionEnum.DENY,
                    rule_name=self.rule_name,
                    reason=f"Cross-account violation: Customer '{ctx.user_id}' cannot access order owned by '{ctx.order_owner_id}'.",
                    suggested_action="Deny action and return HTTP 403 Forbidden."
                )
            
            # Check target argument user_id if passed explicitly
            arg_user_id = ctx.tool_arguments.get("user_id")
            if arg_user_id and arg_user_id != ctx.user_id:
                return PolicyEvaluationResult(
                    decision=PolicyDecisionEnum.DENY,
                    rule_name=self.rule_name,
                    reason=f"Cross-account violation: Tool argument user_id '{arg_user_id}' does not match authenticated user '{ctx.user_id}'.",
                    suggested_action="Deny action."
                )
        return None


class OrderStateTransitionRule(BasePolicyRule):
    rule_name = "order_state_transition"

    def evaluate(self, ctx: PolicyContext) -> Optional[PolicyEvaluationResult]:
        if ctx.tool_name == "update_delivery_address":
            if ctx.order_status in ["shipped", "delivered", "cancelled"]:
                return PolicyEvaluationResult(
                    decision=PolicyDecisionEnum.DENY,
                    rule_name=self.rule_name,
                    reason=f"Cannot update delivery address: Order is already '{ctx.order_status}'.",
                    suggested_action="Inform customer address changes are unavailable once order has shipped."
                )
        
        if ctx.tool_name == "cancel_order":
            if ctx.order_status in ["shipped", "delivered"]:
                return PolicyEvaluationResult(
                    decision=PolicyDecisionEnum.DENY,
                    rule_name=self.rule_name,
                    reason=f"Cannot cancel order: Order has already been '{ctx.order_status}'. Must request a refund or return.",
                    suggested_action="Offer product return or refund flow."
                )
            if ctx.order_status == "cancelled":
                return PolicyEvaluationResult(
                    decision=PolicyDecisionEnum.DENY,
                    rule_name=self.rule_name,
                    reason="Cannot cancel order: Order is already in 'cancelled' state.",
                    suggested_action="No-op."
                )
        return None


class RefundThresholdApprovalRule(BasePolicyRule):
    rule_name = "refund_threshold_approval"

    def evaluate(self, ctx: PolicyContext) -> Optional[PolicyEvaluationResult]:
        if ctx.tool_name == "request_refund":
            amount_cents = ctx.tool_arguments.get("amount_cents", 0)
            threshold = settings.REFUND_APPROVAL_THRESHOLD_CENTS
            if amount_cents > threshold:
                return PolicyEvaluationResult(
                    decision=PolicyDecisionEnum.REQUIRE_APPROVAL,
                    rule_name=self.rule_name,
                    reason=f"Refund request of ${amount_cents / 100:.2f} exceeds automatic approval threshold (${threshold / 100:.2f}). Requires supervisor authorization.",
                    suggested_action="Enqueue action into Approval Inbox for human sign-off.",
                    escalation_required=True
                )
        return None


class IdempotencyKeyPresenceRule(BasePolicyRule):
    rule_name = "idempotency_key_presence"

    def evaluate(self, ctx: PolicyContext) -> Optional[PolicyEvaluationResult]:
        if ctx.tool_name in WRITE_TOOLS:
            idemp_key = ctx.tool_arguments.get("idempotency_key")
            if not idemp_key:
                return PolicyEvaluationResult(
                    decision=PolicyDecisionEnum.DENY,
                    rule_name=self.rule_name,
                    reason=f"Write tool '{ctx.tool_name}' rejected: Missing required 'idempotency_key'.",
                    suggested_action="Supply a unique UUID v4 idempotency key before submitting write operations."
                )
        return None
