# Technical Architecture Specification: Agentic Commerce Reliability & Recovery Lab

## 1. Architectural Blueprint

The platform implements a resilient, multi-tiered enterprise architecture that separates probabilistic planning from deterministic security, policy enforcement, tool execution, and cryptographic auditability.

```mermaid
flowchart TD
    UserQuery(["User Task / Query"]) --> N1["1. classify_intent\n(Extract intent & risk)"]
    N1 --> N2["2. create_plan\n(Formulate tool sequence)"]
    N2 --> N3{"3. authorize_plan\n(PolicyEngine RBAC & Ownership)"}
    
    N3 -->|ALLOW| N5["5. execute_tool\n(Via Fault Proxy & Circuit Breaker)"]
    N3 -->|REQUIRE_APPROVAL| N4["4. request_approval\n(Enqueue to Human Inbox)"]
    N3 -->|DENY| N8["8. emit_evidence_receipt\n(Record Rejection)"]
    
    N4 -->|Supervisor Approved| N5
    N4 -->|Pending / Rejected| N8
    
    N5 --> N6{"6. validate_result\n(Schema, Semantic & State Check)"}
    
    N6 -->|Clean Result & More Tools| N3
    N6 -->|Clean Result & Done| N8
    N6 -->|Fault / Anomaly Detected| N7{"7. recover_or_escalate\n(Retryable?)"}
    
    N7 -->|Retryable (429/500/Timeout)| N5
    N7 -->|Unrecoverable / Max Retries| N8
    
    N8 --> N9["9. complete_run\n(Persist Events, Latency & Metrics)"]
    N9 --> FinalState(["Final Outcome State"])

    subgraph Resilience_Boundary ["Resilience & Storage Boundary"]
        PolicyEngine["Policy Engine\n- Tool allowlist\n- Ownership checks\n- State transition rules\n- Refund threshold ($50)"]
        FaultProxy["Fault Injection Proxy\n(15 deterministic fault types)"]
        EvidenceLedger[("Tamper-Evident Ledger\nSHA-256 Hash Chain")]
        OutboxTable[("Transactional Outbox")]
    end

    N3 -.-> PolicyEngine
    N5 -.-> FaultProxy
    N8 -.-> EvidenceLedger
    N5 -.-> OutboxTable
```

---

## 2. LangGraph 9-Node State Machine Specification

| Node Index | Node Identifier | Responsibilities & Invariants | Transitions & Routing |
|---|---|---|---|
| 1 | `classify_intent` | Analyzes user natural language query, extracts target entities, and assigns initial risk classification (`LOW`, `MEDIUM`, `HIGH`, `CRITICAL`). | Unconditionally routes to `create_plan`. |
| 2 | `create_plan` | Generates a structured sequence of `PlannedToolCall` items with explicit typed argument payloads. | Unconditionally routes to `authorize_plan`. |
| 3 | `authorize_plan` | Evaluates all active policy rules (`ToolScopeAuthorizationRule`, `ResourceOwnershipRule`, `OrderStateTransitionRule`, `RefundThresholdApprovalRule`, `PromptInjectionDefenseRule`). | If `DENY` $\to$ `emit_evidence_receipt`. If `REQUIRE_APPROVAL` $\to$ `request_approval`. If `ALLOW` $\to$ `execute_tool`. |
| 4 | `request_approval` | Enqueues action into the persistent `approvals` table. In live execution, pauses until supervisor approval. In automated testing, inspects pre-approval flag. | If approved $\to$ `execute_tool`. If pending/rejected $\to$ `emit_evidence_receipt`. |
| 5 | `execute_tool` | Dispatches the tool invocation through the `FaultInjectionProxy` with strict idempotency key tracking and timeout guards. | Routes to `validate_result`. |
| 6 | `validate_result` | Validates raw tool return payload against output schema, detects semantic silent drifts (e.g. wrong SKU returned), and verifies price consistency. | If valid & more tools $\to$ `authorize_plan`. If valid & done $\to$ `emit_evidence_receipt`. If invalid $\to$ `recover_or_escalate`. |
| 7 | `recover_or_escalate` | Evaluates whether error is transient (HTTP 429 rate limit, HTTP 500 transient server error, socket timeout). Computes exponential backoff $2^{\text{retries}-1} \times 0.1\text{s}$. If unrecoverable, triggers `escalate_to_human`. | If retryable $\to$ `execute_tool`. If fatal $\to$ `emit_evidence_receipt`. |
| 8 | `emit_evidence_receipt` | Computes canonical payload JSON, redacts secrets/PII, and links the execution receipt to the cryptographic SHA-256 hash chain. | Unconditionally routes to `complete_run`. |
| 9 | `complete_run` | Persists execution records into `agent_runs`, `agent_events`, and `tool_calls` tables, computes latency metrics, and finalizes run state. | Routes to `END`. |

---

## 3. Cryptographic Hash-Chain Evidence Ledger

Every state mutation and terminal run decision produces an immutable audit receipt linked via mathematical hashing:

$$\text{payload\_canonical} = \text{sort\_keys\_canonical\_json}(\text{redact}(\text{event\_data}))$$
$$\text{payload\_hash} = \text{SHA-256}(\text{payload\_canonical})$$
$$\text{event\_hash} = \text{SHA-256}(\text{previous\_event\_hash} \parallel \text{payload\_canonical})$$

The genesis block utilizes a fixed 64-character null hash (`0000000000000000000000000000000000000000000000000000000000000000`). If any database row is altered, inserted, or omitted retroactively, `TamperEvidentEvidenceLedger.verify_chain()` pinpoints the exact corrupted block index in $O(N)$ verification time.
