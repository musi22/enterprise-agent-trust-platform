# Interview Talking Points: Amazon / AWS Backend & Agent Platform Roles

This guide prepares the candidate to discuss the **Agentic Commerce Reliability & Recovery Lab** during technical deep dives and behavioral interviews at Amazon / AWS (Agent Platforms, Bedrock, Retail Systems, DynamoDB/S3 teams).

---

## 1. Core Technical Answers (High-Yield Architecture Questions)

### Q1: "Why build a 9-node LangGraph state machine instead of letting the LLM loop autonomously with tool calling?"
> *"Autonomous tool loops are fundamentally non-deterministic and unsafe for commerce. If you allow an LLM to directly call tools in an unrestricted loop, there is no deterministic boundary between reasoning and execution. In this project, I decoupled planning from policy enforcement. The `authorize_plan` node evaluates RBAC, resource ownership, and order state preconditions *before* any tool can touch downstream services. Furthermore, stateful nodes like `validate_result` and `recover_or_escalate` allow us to handle transient 429 and 500 errors deterministically with bounded backoff rather than burning model tokens in blind loops."*

### Q2: "How did you implement idempotency and prevent duplicate order/refund creation?"
> *"I implemented a transactional idempotency layer combined with the transactional outbox pattern. Every write tool (`create_order`, `request_refund`, `cancel_order`) requires an `idempotency_key`. Before modifying state, the system checks the `idempotency_keys` table within an atomic database transaction. If the key already exists in a completed state, the system returns the cached result payload without re-executing inventory deductions or charges. If an event stream drops or delivers a duplicate webhook, exactly one order or refund record is committed. I verified this with automated unit tests that simulate duplicate retransmissions."*

### Q3: "How does your cryptographic evidence ledger detect tampering?"
> *"Every state mutation and terminal run decision emits a structured receipt block containing canonicalized JSON data, previous event hash, and a SHA-256 digest: $\text{hash}_n = \text{SHA256}(\text{hash}_{n-1} \parallel \text{canonical}(E_n))$. The genesis block uses a fixed null hash. If an attacker or compromised database administrator mutates a row in PostgreSQL or SQLite, the mathematical chain breaks. My verification script traverses the chain in $O(N)$ time and pinpoints the exact corrupted block index. In the engineering console, I built a 'Simulate Tampering' button that mutates a DB field and visually proves immediate detection."*

### Q4: "How do you handle prompt injection attempting to execute admin functions?"
> *"I used defense-in-depth: prompt text cannot override software policy. First, a linguistic pre-filter detects instruction override patterns like 'ignore previous instructions'. Second—and more importantly—even if an LLM is persuaded by an injection attack to propose an admin tool (e.g. `admin_adjust_inventory`), the `authorize_plan` node intercepts the call and checks the customer persona's allowlist. Since the customer role does not have permission, the PolicyEngine issues a strict `DENY` decision, halts execution, and emits a security incident receipt."*

---

## 2. Amazon Leadership Principles Alignment

- **Customer Obsession**: Preventing cross-customer order leaks (`ord_1003`) and duplicate credit card charges protects customer trust at scale.
- **Ownership**: Rather than stopping at a generic UI mockup, I implemented all 20 scenarios, async SQLAlchemy database migrations, cryptographic audit ledgers, automated release gates, and verified tests.
- **Insist on the Highest Standards**: Enforced zero unauthorized actions (0.0%), zero duplicate writes (0.0%), and 100% cryptographic receipts as mandatory release gates before code can ship.
- **Frugality**: Designed the evaluation platform to run 100% offline using deterministic rule-informed models, enabling exhaustive benchmarking with zero cloud API costs.
