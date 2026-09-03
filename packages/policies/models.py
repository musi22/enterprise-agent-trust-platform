from enum import Enum
from typing import Any, Dict, Optional, List
from pydantic import BaseModel, Field

class PolicyDecisionEnum(str, Enum):
    ALLOW = "ALLOW"
    DENY = "DENY"
    REQUIRE_APPROVAL = "REQUIRE_APPROVAL"

class PolicyContext(BaseModel):
    user_id: str
    user_role: str  # customer, support_agent, admin
    tool_name: str
    tool_arguments: Dict[str, Any] = Field(default_factory=dict)
    target_resource_id: Optional[str] = None
    target_resource_type: Optional[str] = None  # order, cart, refund, product
    order_status: Optional[str] = None
    order_owner_id: Optional[str] = None
    prompt_text: Optional[str] = None
    is_idempotent: bool = True
    session_metadata: Dict[str, Any] = Field(default_factory=dict)

class PolicyEvaluationResult(BaseModel):
    decision: PolicyDecisionEnum
    rule_name: str
    reason: str
    suggested_action: Optional[str] = None
    escalation_required: bool = False
    context_snapshot: Dict[str, Any] = Field(default_factory=dict)
