from typing import List, Optional
from packages.policies.models import PolicyContext, PolicyEvaluationResult, PolicyDecisionEnum
from packages.policies.rules import (
    BasePolicyRule,
    PromptInjectionDefenseRule,
    ToolScopeAuthorizationRule,
    ResourceOwnershipRule,
    OrderStateTransitionRule,
    RefundThresholdApprovalRule,
    IdempotencyKeyPresenceRule
)

class PolicyEngine:
    def __init__(self, custom_rules: Optional[List[BasePolicyRule]] = None):
        self.rules: List[BasePolicyRule] = custom_rules or [
            PromptInjectionDefenseRule(),
            ToolScopeAuthorizationRule(),
            ResourceOwnershipRule(),
            OrderStateTransitionRule(),
            RefundThresholdApprovalRule(),
            IdempotencyKeyPresenceRule(),
        ]

    def evaluate(self, ctx: PolicyContext) -> PolicyEvaluationResult:
        """
        Evaluates registered policy rules against the given execution context.
        Priority:
          1. Any DENY immediately rejects execution.
          2. Any REQUIRE_APPROVAL pauses execution for human authorization.
          3. Default to ALLOW if no rules trigger.
        """
        pending_approval_result: Optional[PolicyEvaluationResult] = None

        for rule in self.rules:
            result = rule.evaluate(ctx)
            if not result:
                continue

            if result.decision == PolicyDecisionEnum.DENY:
                result.context_snapshot = ctx.model_dump()
                return result

            if result.decision == PolicyDecisionEnum.REQUIRE_APPROVAL:
                pending_approval_result = result

        if pending_approval_result:
            pending_approval_result.context_snapshot = ctx.model_dump()
            return pending_approval_result

        return PolicyEvaluationResult(
            decision=PolicyDecisionEnum.ALLOW,
            rule_name="default_allow",
            reason="All security, ownership, and domain policy constraints passed successfully.",
            context_snapshot=ctx.model_dump()
        )

# Global singleton policy engine
policy_engine = PolicyEngine()
