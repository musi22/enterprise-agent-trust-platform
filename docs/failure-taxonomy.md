# Failure Taxonomy in Agentic Commerce Systems

This taxonomy categorizes the specific failure modes observed during automated evaluations of retail operations agents.

```
                    AGENT FAILURE MODES
                             │
     ┌───────────────────────┼───────────────────────┐
     ▼                       ▼                       ▼
Security & Policy       Data Consistency       Transient Faults
- Cross-Tenant Read     - Stale Stock Cache    - HTTP 429 Drops
- Prompt Injection      - Price Discrepancy    - Timeout Hangs
- Unapproved Refund     - Silent SKU Mutation  - Outbox Interruption
```

---

## 1. Security & Policy Violations

### Category 1.1: Cross-Tenant Resource Access
- **Description**: An agent executes a query on a sensitive resource (e.g. order details, customer addresses) without validating that the authenticated session owns the entity.
- **Baseline Behavior**: Executes `get_order(order_id="ord_1003")` directly and returns private customer data to an unauthorized user.
- **Guarded Remediation**: `ResourceOwnershipRule` verifies entity ownership against user credentials, denying execution before data retrieval.

### Category 1.2: Privilege Escalation via Prompt Injection
- **Description**: Adversarial prompt tokens coerce the LLM into invoking administrative functions.
- **Baseline Behavior**: Submits `admin_adjust_inventory()` when prompted with "Ignore previous instructions."
- **Guarded Remediation**: Linguistic pattern filtering + deterministic role-based tool allowlists prevent execution regardless of prompt instructions.

### Category 1.3: Threshold Overrun
- **Description**: Financial transactions exceeding human authority limits are executed automatically.
- **Baseline Behavior**: Immediately pays out $120.00 refund requests.
- **Guarded Remediation**: `RefundThresholdApprovalRule` intercepts transactions exceeding $50.00, routes to `request_approval`, and halts until supervisor approval.

---

## 2. Data Consistency & Semantic Drift

### Category 2.1: Stale Inventory Cache Drift
- **Description**: Upstream read caches report item in stock when real-time warehouse stock is zero.
- **Baseline Behavior**: Places order against stale cache, resulting in unfulfillable backorders.
- **Guarded Remediation**: Transactional database checks verify stock at commit time, rolling back atomically if inventory is insufficient.

### Category 2.2: Silent Semantic SKU Drift
- **Description**: Tool returns data for product B when product A was requested, causing the agent to mislead the customer.
- **Baseline Behavior**: Blindly accepts tool output and presents incorrect specs to the user.
- **Guarded Remediation**: `validate_result` node verifies returned entity IDs match requested entity parameters.

---

## 3. Downstream Infrastructure Volatility

### Category 3.1: Transient Rate Limiting (HTTP 429)
- **Description**: Downstream tool returns 429 Too Many Requests.
- **Baseline Behavior**: Fails immediately and reports an unhandled exception.
- **Guarded Remediation**: `recover_or_escalate` executes bounded exponential backoff ($2^{N-1} \times 0.1\text{s}$) and retries cleanly.

### Category 3.2: Duplicate Event Delivery
- **Description**: Retransmission delivers the same order-creation webhook twice.
- **Baseline Behavior**: Commits two separate orders and charges the customer twice.
- **Guarded Remediation**: Idempotency key table deduplicates incoming events, returning the cached result of the original transaction without double-committing.
