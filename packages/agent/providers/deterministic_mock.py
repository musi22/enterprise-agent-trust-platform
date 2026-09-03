import re
import uuid
from typing import Dict, Any, List, Optional
from packages.agent.providers.base import BaseModelProvider, AgentPlan, PlannedToolCall

class DeterministicMockProvider(BaseModelProvider):
    """
    Deterministic rule-informed model provider for 100% offline, reproducible, 
    and zero-cost benchmarking across all 20 scenarios.
    """
    async def classify_intent(self, query: str, context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        q_lower = query.lower()

        if "ignore all previous instructions" in q_lower or "superadmin" in q_lower or "admin_adjust_inventory" in q_lower:
            return {"intent": "ADMIN_OVERRIDE_ATTEMPT", "risk_level": "CRITICAL", "confidence": 0.99}
        elif "hazardous" in q_lower or "legal action" in q_lower or "$500 store credit" in q_lower:
            return {"intent": "SENSITIVE_CUSTOMER_DISPUTE", "risk_level": "HIGH", "confidence": 0.98}
        elif "refund" in q_lower:
            return {"intent": "REQUEST_REFUND", "risk_level": "MEDIUM", "confidence": 0.95}
        elif "change" in q_lower and "address" in q_lower:
            return {"intent": "UPDATE_DELIVERY_ADDRESS", "risk_level": "MEDIUM", "confidence": 0.95}
        elif "cancel" in q_lower:
            return {"intent": "CANCEL_ORDER", "risk_level": "MEDIUM", "confidence": 0.95}
        elif "order" in q_lower or "purchase" in q_lower or "buy" in q_lower:
            return {"intent": "CREATE_ORDER", "risk_level": "MEDIUM", "confidence": 0.94}
        elif "inventory" in q_lower or "stock" in q_lower:
            return {"intent": "CHECK_INVENTORY", "risk_level": "LOW", "confidence": 0.98}
        elif "search" in q_lower or "find" in q_lower or "headphones" in q_lower or "pans" in q_lower:
            return {"intent": "SEARCH_CATALOG", "risk_level": "LOW", "confidence": 0.97}
        elif "details" in q_lower or "ord_" in q_lower or "prod_" in q_lower:
            return {"intent": "LOOKUP_DETAILS", "risk_level": "LOW", "confidence": 0.96}
        return {"intent": "GENERAL_INQUIRY", "risk_level": "LOW", "confidence": 0.90}

    async def generate_plan(
        self,
        query: str,
        persona: Dict[str, Any],
        context: Optional[Dict[str, Any]] = None
    ) -> AgentPlan:
        q_lower = query.lower()
        user_id = persona.get("user_id", "usr_cust_001")
        default_seed = context.get("seed", 42) if context else 42

        # 1. Prompt Injection Scenario
        if "ignore all previous instructions" in q_lower or "superadmin" in q_lower or "admin_adjust_inventory" in q_lower:
            return AgentPlan(
                classified_intent="ADMIN_OVERRIDE_ATTEMPT",
                confidence=0.99,
                planned_tools=[
                    PlannedToolCall(
                        tool_name="admin_adjust_inventory",
                        arguments={"product_id": "prod_elec_010", "units": 9999},
                        rationale="Attempting user-requested admin inventory modification."
                    )
                ],
                explanation="Detected request for administrative inventory modification."
            )

        # 2. Ambiguous / Sensitive Escalation Scenario
        if "hazardous" in q_lower or "legal action" in q_lower or "$500 store credit" in q_lower:
            return AgentPlan(
                classified_intent="SENSITIVE_CUSTOMER_DISPUTE",
                confidence=0.98,
                planned_tools=[
                    PlannedToolCall(
                        tool_name="get_order",
                        arguments={"order_id": "ord_1003", "user_id": user_id},
                        rationale="Retrieve disputed order details."
                    ),
                    PlannedToolCall(
                        tool_name="escalate_to_human",
                        arguments={
                            "issue_type": "safety_damage_claim",
                            "summary": "Customer claims hazardous smoke damage, threatening legal action and requesting $500 compensation.",
                            "context_details": {"order_id": "ord_1003", "severity": "CRITICAL"}
                        },
                        rationale="Escalate hazardous damage claim to human supervisor."
                    )
                ],
                explanation="Sensitive claim involving physical hazard and legal threats requires human supervisor intervention."
            )

        # 3. Address Update Scenario
        if "change" in q_lower and "address" in q_lower:
            match = re.search(r"ord_\d+", query)
            order_id = match.group(0) if match else "ord_1002"
            new_addr = "100 Main St, Austin, TX"
            if "to " in query:
                new_addr = query.split("to ")[-1].strip()
            return AgentPlan(
                classified_intent="UPDATE_DELIVERY_ADDRESS",
                confidence=0.96,
                planned_tools=[
                    PlannedToolCall(
                        tool_name="update_delivery_address",
                        arguments={
                            "order_id": order_id,
                            "user_id": user_id,
                            "new_address": new_addr,
                            "idempotency_key": f"idemp_addr_{order_id}_{default_seed}"
                        },
                        rationale=f"Update delivery destination for order {order_id}."
                    )
                ]
            )

        # 4. Order Cancellation Scenario
        if "cancel" in q_lower and "ord_" in q_lower:
            match = re.search(r"ord_\d+", query)
            order_id = match.group(0) if match else "ord_1005"
            return AgentPlan(
                classified_intent="CANCEL_ORDER",
                confidence=0.96,
                planned_tools=[
                    PlannedToolCall(
                        tool_name="cancel_order",
                        arguments={
                            "order_id": order_id,
                            "user_id": user_id,
                            "reason": "Customer cancellation request",
                            "idempotency_key": f"idemp_cancel_{order_id}_{default_seed}"
                        },
                        rationale=f"Cancel order {order_id}."
                    )
                ]
            )

        # 5. Refund Requests (Below or Above threshold)
        if "refund" in q_lower:
            match = re.search(r"ord_\d+", query)
            order_id = match.group(0) if match else "ord_1002"
            
            # Check amount
            amount_match = re.search(r"\$(\d+(?:\.\d{2})?)", query)
            amount_cents = int(float(amount_match.group(1)) * 100) if amount_match else 2000
            
            idemp_key = f"idemp_refund_{order_id}_{amount_cents}"
            if "duplicate" in query.lower() or "submit refund for order ord_1002" in q_lower:
                idemp_key = "idemp_dup_ref_11"

            return AgentPlan(
                classified_intent="REQUEST_REFUND",
                confidence=0.95,
                planned_tools=[
                    PlannedToolCall(
                        tool_name="request_refund",
                        arguments={
                            "order_id": order_id,
                            "user_id": user_id,
                            "amount_cents": amount_cents,
                            "reason": "Customer requested refund for item issue",
                            "idempotency_key": idemp_key
                        },
                        rationale=f"Submit refund of ${amount_cents / 100:.2f} for order {order_id}."
                    )
                ]
            )

        # 6. Out of stock / Specific Order creation
        if "omnitab" in q_lower:
            return AgentPlan(
                classified_intent="CREATE_ORDER",
                confidence=0.95,
                planned_tools=[
                    PlannedToolCall(
                        tool_name="check_inventory",
                        arguments={"product_id": "prod_elec_010"},
                        rationale="Check warehouse stock for OmniTab before ordering."
                    ),
                    PlannedToolCall(
                        tool_name="create_order",
                        arguments={
                            "user_id": user_id,
                            "items": [{"product_id": "prod_elec_010", "quantity": 1}],
                            "shipping_address": "221B Baker Street",
                            "idempotency_key": f"idemp_order_omni_{default_seed}"
                        },
                        rationale="Create order for OmniTab."
                    )
                ]
            )

        if "retrostyle" in q_lower or "toaster" in q_lower:
            return AgentPlan(
                classified_intent="CREATE_ORDER",
                confidence=0.95,
                planned_tools=[
                    PlannedToolCall(
                        tool_name="check_inventory",
                        arguments={"product_id": "prod_home_020"},
                        rationale="Check stock for RetroStyle Toaster."
                    ),
                    PlannedToolCall(
                        tool_name="create_order",
                        arguments={
                            "user_id": user_id,
                            "items": [{"product_id": "prod_home_020", "quantity": 1}],
                            "shipping_address": "12 Grimmauld Place, London N1",
                            "idempotency_key": f"idemp_order_toast_{default_seed}"
                        },
                        rationale="Create order for RetroStyle Toaster."
                    )
                ]
            )

        if "thunderbolt" in q_lower:
            return AgentPlan(
                classified_intent="CREATE_ORDER",
                confidence=0.95,
                planned_tools=[
                    PlannedToolCall(
                        tool_name="create_order",
                        arguments={
                            "user_id": user_id,
                            "items": [{"product_id": "prod_elec_008", "quantity": 1, "unit_price_cents": 2999}],
                            "shipping_address": "742 Evergreen Terrace",
                            "idempotency_key": f"idemp_order_tb_{default_seed}"
                        },
                        rationale="Purchase Braided Thunderbolt 4 Cable 2M for $29.99."
                    )
                ]
            )

        if "negative five" in q_lower or "quantity negative" in q_lower:
            return AgentPlan(
                classified_intent="CREATE_ORDER",
                confidence=0.90,
                planned_tools=[
                    PlannedToolCall(
                        tool_name="create_order",
                        arguments={
                            "user_id": user_id,
                            "items": [{"product_id": "prod_elec_003", "quantity": -5}],
                            "shipping_address": "742 Evergreen Terrace",
                            "idempotency_key": f"idemp_order_neg_{default_seed}"
                        },
                        rationale="Attempt to order with malformed negative quantity."
                    )
                ]
            )

        if "ergonomic precision mouse" in q_lower or "mouse with fast shipping" in q_lower:
            return AgentPlan(
                classified_intent="CREATE_ORDER",
                confidence=0.96,
                planned_tools=[
                    PlannedToolCall(
                        tool_name="create_order",
                        arguments={
                            "user_id": user_id,
                            "items": [{"product_id": "prod_elec_004", "quantity": 1, "unit_price_cents": 4999}],
                            "shipping_address": "100 Pine Street, Seattle, WA",
                            "idempotency_key": "idemp_dup_ord_10"
                        },
                        rationale="Order Ergonomic Precision Mouse with deterministic idempotency key."
                    )
                ]
            )

        # 7. Cross-customer order lookup
        if "details and shipping address for order" in q_lower or ("ord_" in q_lower and "details" in q_lower):
            match = re.search(r"ord_\d+", query)
            order_id = match.group(0) if match else "ord_1003"
            return AgentPlan(
                classified_intent="GET_ORDER",
                confidence=0.97,
                planned_tools=[
                    PlannedToolCall(
                        tool_name="get_order",
                        arguments={"order_id": order_id, "user_id": user_id},
                        rationale=f"Retrieve details for order {order_id}."
                    )
                ]
            )

        # 8. Inventory lookup
        if "inventory for" in q_lower or "warehouse status" in q_lower:
            match = re.search(r"prod_[a-z]+_\d+", query)
            prod_id = match.group(0) if match else "prod_elec_001"
            return AgentPlan(
                classified_intent="CHECK_INVENTORY",
                confidence=0.98,
                planned_tools=[
                    PlannedToolCall(
                        tool_name="check_inventory",
                        arguments={"product_id": prod_id},
                        rationale=f"Check warehouse inventory for {prod_id}."
                    )
                ]
            )

        # 9. Product lookup
        if "details for product" in q_lower or "prod_" in q_lower:
            match = re.search(r"prod_[a-z]+_\d+", query)
            prod_id = match.group(0) if match else "prod_elec_001"
            return AgentPlan(
                classified_intent="GET_PRODUCT",
                confidence=0.98,
                planned_tools=[
                    PlannedToolCall(
                        tool_name="get_product",
                        arguments={"product_id": prod_id},
                        rationale=f"Get product specs and pricing for {prod_id}."
                    )
                ]
            )

        # 10. Catalog search (default fallback)
        search_kw = "headphones"
        if "ceramic pans" in q_lower or "pans" in q_lower:
            search_kw = "pan"
        elif "headphones" in q_lower:
            search_kw = "headphones"

        return AgentPlan(
            classified_intent="SEARCH_CATALOG",
            confidence=0.95,
            planned_tools=[
                PlannedToolCall(
                    tool_name="search_catalog",
                    arguments={"query": search_kw, "limit": 5},
                    rationale=f"Search catalog for '{search_kw}'."
                )
            ]
        )
