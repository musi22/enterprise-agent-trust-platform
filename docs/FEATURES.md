# Enterprise Agent Trust Platform — Feature Guide & Deep Dive

> A comprehensive technical breakdown of the 6 core enterprise reliability and security systems implemented in the platform.

📹 **Video Walkthrough:** [`docs/videos/enterprise_features_demo.mp4`](videos/enterprise_features_demo.mp4)  
🌐 **Live Interactive Console:** [https://enterprise-ai-web-production.up.railway.app](https://enterprise-ai-web-production.up.railway.app)

---

## 1. Executive Reliability Scorecard & Release Gate (Feature 1)

### The Problem
When deploying autonomous LLM agents in production retail operations, engineering teams lack quantifiable, release-blocking quality gates. Standard unit tests fail to catch emergent multi-step agent vulnerabilities such as cross-account data leaks, price drift, or cascade failures under network pressure.

### The Solution
The **Overview & Release Gate** module aggregates real-time evaluation metrics across all 20 ground-truth enterprise scenarios:
- **Task Success Rate:** Measures overall scenario completion (Guarded: **100.0%** vs. Baseline: **60.0%**, representing a **+40.0% lift**).
- **Unauthorized Actions:** Strict zero-tolerance gate for cross-tenant access attempts (**0.0%** on Guarded vs. **5.0%** vulnerability on Baseline).
- **Fault Recovery Rate:** Percentage of transient HTTP 429 rate limits and 500 crashes healed via bounded exponential backoff (**66.7%** vs. **33.3%** baseline).
- **Evidence Completeness:** Verifies that **100.0%** of agent actions produce cryptographically signed receipts.

### Code Implementation
- Evaluation logic: [`scripts/release_gate.py`](../scripts/release_gate.py)
- Web UI component: [`apps/web/src/components/tabs/OverviewTab.tsx`](../apps/web/src/components/tabs/OverviewTab.tsx)
- Health probe with dynamic mode badge: [`apps/api/app/api/v1/routers/health.py`](../apps/api/app/api/v1/routers/health.py)

---

## 2. Scenario Lab & Dual-Agent Comparative Execution (Feature 2)

### The Problem
Evaluating an agent requires running reproducible commerce workflows against complex preconditions (e.g. order in `SHIPPED` state cannot be canceled, out-of-stock items require catalog substitution, price mismatches require user re-confirmation).

### The Solution
The **Scenario Lab** provides an interactive side-by-side testbed of **20 labelled retail scenarios**:
1. **Catalog Search & Inquiries** (`01_catalog_search`, `02_out_of_stock`, `03_stale_inventory`)
2. **Price & Argument Verification** (`04_price_changed`, `05_malformed_arguments`)
3. **Multi-Tenant Security** (`06_cross_customer_access`, `07_prompt_injection_admin`)
4. **Order State Lifecycle** (`08_cancel_delivered_order`, `09_address_change_in_transit`)
5. **Human-in-the-Loop Thresholds** (`10_large_refund_threshold`, `11_disputed_charge`)
6. **Network & Chaos Faults** (`12_rate_limit_429`, `13_server_error_500`, `14_slow_network_timeout`)
7. **Complex Multi-Step Returns** (`15_multi_item_partial_return` through `20_end_to_end_exchange`)

Users can toggle between **Baseline Mode** (unprotected model-to-tool loop) and **Guarded Mode** (LangGraph state machine) to observe how guardrails intercept unauthorized queries before any database mutation occurs.

### Code Implementation
- Scenario definitions: [`scenarios/*.yaml`](../scenarios)
- Execution router: [`apps/api/app/api/v1/routers/runs.py`](../apps/api/app/api/v1/routers/runs.py)
- Web UI component: [`apps/web/src/components/tabs/ScenarioLabTab.tsx`](../apps/web/src/components/tabs/ScenarioLabTab.tsx)

---

## 3. 9-Node LangGraph State Machine & Trace Explorer (Feature 3)

### The Problem
Black-box agent frameworks like standard ReAct combine planning, authorization, and execution into a single prompt. If the model hallucinates or is jailbroken, unauthorized tool calls execute directly against production databases.

### The Solution
The platform decouples execution into a **9-node LangGraph directed state graph**:
1. `classify_intent` — Classifies user intent and assigns initial risk level (`LOW`, `MEDIUM`, `HIGH`, `CRITICAL`).
2. `create_plan` — Synthesizes ordered tool sequence using schema constraints.
3. `authorize_plan` — Deterministic RBAC, resource ownership, and order state validation.
4. `request_approval` — Intercepts actions requiring human sign-off (e.g., refund > $50).
5. `execute_tool` — Sandboxed tool execution with idempotency key deduplication.
6. `validate_result` — Post-execution anomaly detection (validates returned SKUs, prices, quantities).
7. `recover_or_escalate` — Bounded exponential backoff ($2^{N-1} \times 0.1\text{s}$) or graceful fallback.
8. `emit_evidence_receipt` — Redacts secrets/PII and generates cryptographically signed receipt.
9. `complete_run` — Final state transition and client event emission.

The **Trace Explorer** visualizes every node transition, tool input/output, execution duration, and cryptographic receipt block in chronological order.

### Code Implementation
- LangGraph graph definition: [`packages/agent/guarded_graph.py`](../packages/agent/guarded_graph.py)
- State schema: [`packages/agent/state.py`](../packages/agent/state.py)
- Web UI component: [`apps/web/src/components/tabs/TraceExplorerTab.tsx`](../apps/web/src/components/tabs/TraceExplorerTab.tsx)

---

## 4. Human-in-the-Loop (HITL) Approval Inbox (Feature 4)

### The Problem
Full agent autonomy on financial transactions creates severe business risk. An unconstrained agent might issue unwarranted refunds, accept fraudulent returns, or modify high-value shipping orders without managerial oversight.

### The Solution
The platform enforces a configurable financial threshold (`REFUND_APPROVAL_THRESHOLD_CENTS = 5000` / $50.00) and sensitivity policies:
- When an agent proposes a refund exceeding $50 or flags a sensitive dispute, the execution state is safely suspended in node `4 (request_approval)`.
- An approval ticket is enqueued in the **Approval Inbox** with full context: requested amount, customer tier, item condition, and risk score.
- Supervisors can review, inspect the trace, and click **Approve** (resumes state machine execution) or **Reject** (emits a policy denial receipt and safely informs the customer).

### Code Implementation
- Policy rule model: [`packages/policies/rules.py`](../packages/policies/rules.py)
- Approval API router: [`apps/api/app/api/v1/routers/approvals.py`](../apps/api/app/api/v1/routers/approvals.py)
- Web UI component: [`apps/web/src/components/tabs/ApprovalsTab.tsx`](../apps/web/src/components/tabs/ApprovalsTab.tsx)

---

## 5. Dual-Agent Benchmark Matrix & Chaos Resilience (Feature 5)

### The Problem
Distributed commerce environments experience unpredictable network turbulence: payment gateway rate limits (HTTP 429), inventory microservice 500 errors, and stale read replica caches. Without resilience testing, agents crash or cause double billing.

### The Solution
The platform includes an in-memory **Chaos & Fault Injection Proxy**:
- Intercepts tool calls deterministically based on scenario configs.
- Injects 15 distinct fault types (rate limits, network latency, malformed JSON, price drift).
- Evaluates agent resilience: The Guarded Agent automatically executes retry policies with jittered exponential backoff, recovering gracefully where the Baseline agent fails.
- The **Benchmark Matrix** renders comparative radar/bar visualizations and provides single-click **Export as CSV** and **Download Raw JSON** for auditing.

### Code Implementation
- Fault injection proxy: [`packages/fault_injection/proxy.py`](../packages/fault_injection/proxy.py)
- Benchmark API: [`apps/api/app/api/v1/routers/evaluations.py`](../apps/api/app/api/v1/routers/evaluations.py)
- Web UI component: [`apps/web/src/components/tabs/BenchmarkTab.tsx`](../apps/web/src/components/tabs/BenchmarkTab.tsx)

---

## 6. Tamper-Evident Cryptographic Evidence Ledger (Feature 6)

### The Problem
Enterprise AI deployments subject to SOX, PCI-DSS, or GDPR compliance require non-repudiation: proof that an audit log has not been modified after the fact to hide agent errors or policy breaches.

### The Solution
The platform features an append-only **Cryptographic Evidence Ledger**:
- Every intent classification, policy decision, and tool execution is serialized and hashed with **SHA-256**.
- Each block links to the previous block's hash:
  $$\text{Current Hash} = \text{SHA256}(\text{Block Index} + \text{Prev Hash} + \text{Payload} + \text{Timestamp})$$
- Automated PII and secret redaction filters out credit cards, access tokens, and passwords before hashing.
- **Real-Time Verification Engine:** Computes ledger integrity across all blocks in $O(N)$ time.
- **Interactive Tampering Simulation:** The console includes a "Simulate DB Tampering" button that silently modifies a historical payload in the database; clicking "Verify Ledger Integrity" immediately flags `SECURITY ALERT: AUDIT TAMPERING DETECTED!` and isolates the exact corrupted block index.

### Code Implementation
- Cryptographic hash-chain engine: [`packages/telemetry/ledger.py`](../packages/telemetry/ledger.py)
- Evidence API router: [`apps/api/app/api/v1/routers/evidence.py`](../apps/api/app/api/v1/routers/evidence.py)
- Web UI component: [`apps/web/src/components/tabs/EvidenceLedgerTab.tsx`](../apps/web/src/components/tabs/EvidenceLedgerTab.tsx)
