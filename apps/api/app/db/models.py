from datetime import datetime, timezone
import uuid
from typing import Any, Dict, Optional
from sqlalchemy import (
    Column,
    String,
    Integer,
    Boolean,
    DateTime,
    ForeignKey,
    Text,
    Float,
    JSON,
    UniqueConstraint,
    Index,
)
from sqlalchemy.orm import relationship
from apps.api.app.db.database import Base

def generate_uuid() -> str:
    return str(uuid.uuid4())

def utc_now() -> datetime:
    return datetime.now(timezone.utc)

class User(Base):
    __tablename__ = "users"

    id = Column(String(64), primary_key=True, default=generate_uuid)
    email = Column(String(255), unique=True, nullable=False, index=True)
    name = Column(String(255), nullable=False)
    role = Column(String(32), nullable=False, default="customer")  # customer, support_agent, admin
    hashed_password = Column(String(255), nullable=False)
    created_at = Column(DateTime, default=utc_now, nullable=False)

    orders = relationship("Order", back_populates="user")
    carts = relationship("Cart", back_populates="user")
    refund_requests = relationship("RefundRequest", back_populates="user")


class Product(Base):
    __tablename__ = "products"

    id = Column(String(64), primary_key=True, default=generate_uuid)
    sku = Column(String(64), unique=True, nullable=False, index=True)
    title = Column(String(255), nullable=False, index=True)
    category = Column(String(64), nullable=False, index=True)
    price_cents = Column(Integer, nullable=False)  # Stored in integer cents to prevent float rounding
    stock_level = Column(Integer, nullable=False, default=0)
    description = Column(Text, nullable=True)
    active = Column(Boolean, default=True, nullable=False)
    created_at = Column(DateTime, default=utc_now, nullable=False)

    inventory = relationship("Inventory", back_populates="product", uselist=False)


class Inventory(Base):
    __tablename__ = "inventory"

    id = Column(String(64), primary_key=True, default=generate_uuid)
    product_id = Column(String(64), ForeignKey("products.id"), unique=True, nullable=False)
    available_stock = Column(Integer, nullable=False, default=0)
    reserved_stock = Column(Integer, nullable=False, default=0)
    updated_at = Column(DateTime, default=utc_now, onupdate=utc_now, nullable=False)

    product = relationship("Product", back_populates="inventory")


class Cart(Base):
    __tablename__ = "carts"

    id = Column(String(64), primary_key=True, default=generate_uuid)
    user_id = Column(String(64), ForeignKey("users.id"), nullable=False, index=True)
    status = Column(String(32), default="active", nullable=False)  # active, checked_out, abandoned
    created_at = Column(DateTime, default=utc_now, nullable=False)

    user = relationship("User", back_populates="carts")
    items = relationship("CartItem", back_populates="cart", cascade="all, delete-orphan")


class CartItem(Base):
    __tablename__ = "cart_items"

    id = Column(String(64), primary_key=True, default=generate_uuid)
    cart_id = Column(String(64), ForeignKey("carts.id"), nullable=False, index=True)
    product_id = Column(String(64), ForeignKey("products.id"), nullable=False)
    quantity = Column(Integer, nullable=False, default=1)
    unit_price_cents = Column(Integer, nullable=False)

    cart = relationship("Cart", back_populates="items")
    product = relationship("Product")


class Order(Base):
    __tablename__ = "orders"

    id = Column(String(64), primary_key=True, default=generate_uuid)
    user_id = Column(String(64), ForeignKey("users.id"), nullable=False, index=True)
    order_status = Column(String(32), nullable=False, default="pending")  
    # States: pending -> confirmed -> processing -> shipped -> delivered (or cancelled)
    shipping_address = Column(Text, nullable=False)
    total_cents = Column(Integer, nullable=False, default=0)
    idempotency_key = Column(String(128), unique=True, nullable=True, index=True)
    created_at = Column(DateTime, default=utc_now, nullable=False)
    updated_at = Column(DateTime, default=utc_now, onupdate=utc_now, nullable=False)

    user = relationship("User", back_populates="orders")
    items = relationship("OrderItem", back_populates="order", cascade="all, delete-orphan")
    refund_requests = relationship("RefundRequest", back_populates="order")


class OrderItem(Base):
    __tablename__ = "order_items"

    id = Column(String(64), primary_key=True, default=generate_uuid)
    order_id = Column(String(64), ForeignKey("orders.id"), nullable=False, index=True)
    product_id = Column(String(64), ForeignKey("products.id"), nullable=False)
    quantity = Column(Integer, nullable=False, default=1)
    unit_price_cents = Column(Integer, nullable=False)

    order = relationship("Order", back_populates="items")
    product = relationship("Product")


class RefundRequest(Base):
    __tablename__ = "refund_requests"

    id = Column(String(64), primary_key=True, default=generate_uuid)
    order_id = Column(String(64), ForeignKey("orders.id"), nullable=False, index=True)
    user_id = Column(String(64), ForeignKey("users.id"), nullable=False, index=True)
    amount_cents = Column(Integer, nullable=False)
    reason = Column(Text, nullable=False)
    status = Column(String(32), nullable=False, default="pending_approval")  
    # pending_approval, approved, rejected, processed
    idempotency_key = Column(String(128), unique=True, nullable=True, index=True)
    created_at = Column(DateTime, default=utc_now, nullable=False)

    order = relationship("Order", back_populates="refund_requests")
    user = relationship("User", back_populates="refund_requests")


class IdempotencyKey(Base):
    __tablename__ = "idempotency_keys"

    id = Column(String(64), primary_key=True, default=generate_uuid)
    key = Column(String(128), unique=True, nullable=False, index=True)
    scope = Column(String(64), nullable=False)  # e.g., create_order, request_refund
    response_hash = Column(String(128), nullable=True)
    status = Column(String(32), nullable=False, default="started")  # started, completed, failed
    result_payload = Column(JSON, nullable=True)
    created_at = Column(DateTime, default=utc_now, nullable=False)
    expires_at = Column(DateTime, nullable=True)


class OutboxEvent(Base):
    __tablename__ = "outbox_events"

    id = Column(String(64), primary_key=True, default=generate_uuid)
    event_type = Column(String(64), nullable=False, index=True)
    aggregate_type = Column(String(64), nullable=False)  # order, refund, approval
    aggregate_id = Column(String(64), nullable=False)
    payload = Column(JSON, nullable=False)
    status = Column(String(32), default="pending", nullable=False, index=True)  # pending, dispatched, failed
    retry_count = Column(Integer, default=0, nullable=False)
    created_at = Column(DateTime, default=utc_now, nullable=False)


class Scenario(Base):
    __tablename__ = "scenarios"

    id = Column(String(64), primary_key=True)  # e.g. "01_catalog_search"
    name = Column(String(255), nullable=False)
    description = Column(Text, nullable=False)
    persona_role = Column(String(32), nullable=False)
    category = Column(String(64), nullable=False)
    payload_json = Column(JSON, nullable=False)
    created_at = Column(DateTime, default=utc_now, nullable=False)


class AgentRun(Base):
    __tablename__ = "agent_runs"

    id = Column(String(64), primary_key=True, default=generate_uuid)
    scenario_id = Column(String(64), ForeignKey("scenarios.id"), nullable=True, index=True)
    agent_mode = Column(String(32), nullable=False)  # baseline, guarded
    seed = Column(Integer, nullable=False, default=42)
    user_query = Column(Text, nullable=False)
    status = Column(String(32), nullable=False, default="running")  # running, success, failed, escalated, rejected
    final_outcome = Column(Text, nullable=True)
    latency_ms = Column(Float, nullable=False, default=0.0)
    token_usage = Column(Integer, nullable=False, default=0)
    cost_usd = Column(Float, nullable=False, default=0.0)
    created_at = Column(DateTime, default=utc_now, nullable=False)

    events = relationship("AgentEvent", back_populates="run", cascade="all, delete-orphan")
    tool_calls = relationship("ToolCall", back_populates="run", cascade="all, delete-orphan")
    policy_decisions = relationship("PolicyDecision", back_populates="run", cascade="all, delete-orphan")
    evidence_receipt = relationship("EvidenceReceipt", back_populates="run", uselist=False)


class AgentEvent(Base):
    __tablename__ = "agent_events"

    id = Column(String(64), primary_key=True, default=generate_uuid)
    run_id = Column(String(64), ForeignKey("agent_runs.id"), nullable=False, index=True)
    step_index = Column(Integer, nullable=False)
    node_name = Column(String(64), nullable=False)  # e.g., classify_intent, authorize_plan
    event_type = Column(String(64), nullable=False)
    payload_json = Column(JSON, nullable=False)
    timestamp = Column(DateTime, default=utc_now, nullable=False)

    run = relationship("AgentRun", back_populates="events")


class ToolCall(Base):
    __tablename__ = "tool_calls"

    id = Column(String(64), primary_key=True, default=generate_uuid)
    run_id = Column(String(64), ForeignKey("agent_runs.id"), nullable=False, index=True)
    tool_name = Column(String(64), nullable=False)
    arguments_json = Column(JSON, nullable=False)
    response_json = Column(JSON, nullable=True)
    status = Column(String(32), nullable=False)  # success, error, fault_injected, recovered
    error_details = Column(Text, nullable=True)
    latency_ms = Column(Float, nullable=False, default=0.0)
    idempotency_key = Column(String(128), nullable=True)
    created_at = Column(DateTime, default=utc_now, nullable=False)

    run = relationship("AgentRun", back_populates="tool_calls")


class PolicyDecision(Base):
    __tablename__ = "policy_decisions"

    id = Column(String(64), primary_key=True, default=generate_uuid)
    run_id = Column(String(64), ForeignKey("agent_runs.id"), nullable=False, index=True)
    rule_name = Column(String(64), nullable=False)
    decision = Column(String(32), nullable=False)  # ALLOW, DENY, REQUIRE_APPROVAL
    reason = Column(Text, nullable=False)
    context_json = Column(JSON, nullable=True)
    created_at = Column(DateTime, default=utc_now, nullable=False)

    run = relationship("AgentRun", back_populates="policy_decisions")


class Approval(Base):
    __tablename__ = "approvals"

    id = Column(String(64), primary_key=True, default=generate_uuid)
    run_id = Column(String(64), ForeignKey("agent_runs.id"), nullable=False, index=True)
    action_type = Column(String(64), nullable=False)  # e.g., high_value_refund, sensitive_action
    proposed_payload_json = Column(JSON, nullable=False)
    status = Column(String(32), nullable=False, default="pending")  # pending, approved, rejected
    reason = Column(Text, nullable=False)
    decided_by = Column(String(64), nullable=True)
    decided_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=utc_now, nullable=False)


class EvidenceReceipt(Base):
    __tablename__ = "evidence_receipts"

    id = Column(String(64), primary_key=True, default=generate_uuid)
    run_id = Column(String(64), ForeignKey("agent_runs.id"), unique=True, nullable=False)
    scenario_id = Column(String(64), nullable=True)
    final_outcome = Column(String(64), nullable=False)
    previous_event_hash = Column(String(64), nullable=False)
    event_hash = Column(String(64), nullable=False)
    payload_hash = Column(String(64), nullable=False)
    receipt_data = Column(JSON, nullable=False)
    signature = Column(String(128), nullable=False)
    created_at = Column(DateTime, default=utc_now, nullable=False)

    run = relationship("AgentRun", back_populates="evidence_receipt")


class BenchmarkRun(Base):
    __tablename__ = "benchmark_runs"

    id = Column(String(64), primary_key=True, default=generate_uuid)
    timestamp = Column(DateTime, default=utc_now, nullable=False)
    total_scenarios = Column(Integer, nullable=False)
    baseline_summary_json = Column(JSON, nullable=False)
    guarded_summary_json = Column(JSON, nullable=False)
    gate_passed = Column(Boolean, nullable=False, default=False)
    created_at = Column(DateTime, default=utc_now, nullable=False)

    metrics = relationship("BenchmarkMetric", back_populates="benchmark", cascade="all, delete-orphan")


class BenchmarkMetric(Base):
    __tablename__ = "benchmark_metrics"

    id = Column(String(64), primary_key=True, default=generate_uuid)
    benchmark_id = Column(String(64), ForeignKey("benchmark_runs.id"), nullable=False, index=True)
    metric_name = Column(String(64), nullable=False)
    baseline_value = Column(Float, nullable=False)
    guarded_value = Column(Float, nullable=False)
    diff_pct = Column(Float, nullable=False)

    benchmark = relationship("BenchmarkRun", back_populates="metrics")
