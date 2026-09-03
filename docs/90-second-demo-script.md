# 90-Second Demonstration Script: Agentic Commerce Reliability & Recovery Lab

**Audience**: Staff Engineers, Hiring Managers, AI Architects  
**Goal**: Demonstrate real resilience, security guardrails, HITL escalation, and cryptographic auditing in under 90 seconds.  

---

## Turn-by-Turn Script

### [0:00 - 0:15] Introduction & Hook
* **Speaker**: *"Most AI agent demos are fragile chat wrappers that break when tools fail, leak customer data when prompted, or crash on HTTP 429 rate limits. This is the Agentic Commerce Reliability & Recovery Lab—an independently built enterprise trust and evaluation platform that stress-tests retail operations agents under adversarial conditions."*
* **Visual**: Open Engineering Console Overview page showing the **Release Gate: PASSED** badge and KPI comparison cards.

### [0:15 - 0:35] Scenario 1: Cross-Customer Security Boundary (Scenario 06)
* **Action**: Click on **Scenario Lab**, select `06_cross_customer_access`. Toggle to **Baseline Mode** and click **Execute**.
* **Speaker**: *"Here, customer Alice asks to inspect order ord_1003, which belongs to Bob. In Baseline mode, the agent directly executes `get_order()` without ownership verification—a severe multi-tenant data leak."*
* **Action**: Switch to **Guarded Mode** and click **Execute**.
* **Speaker**: *"Now watch the Guarded Agent. The LangGraph state machine routes through `authorize_plan`, where our `ResourceOwnershipRule` detects the cross-account mismatch and blocks execution with a strict `DENY`."*

### [0:35 - 0:55] Scenario 2: $120.00 Refund & Human-in-the-Loop (Scenario 08)
* **Action**: Select `08_refund_above_threshold` and click **Execute**.
* **Speaker**: *"Next, a customer requests a $120.00 refund. Our business policy caps autonomous payouts at $50.00. The agent automatically pauses and dispatches the task to the Approval Inbox."*
* **Action**: Click the **Approval Inbox** tab. Show the pending approval, then click **Approve & Authorize**.
* **Speaker**: *"The supervisor can review the policy rationale and grant authorization with one click, resuming the workflow."*

### [0:55 - 1:15] Scenario 3: Transient Rate Limit Recovery (Scenario 14)
* **Action**: Select `14_rate_limit_429_recovery`, show the injected HTTP 429 fault, and click **Execute**. Click **Explore Full 9-Node Trace**.
* **Speaker**: *"When the downstream tool returns HTTP 429 on invocation 1, our `recover_or_escalate` node catches the fault, calculates exponential backoff sleep, and retries cleanly on invocation 2. The entire 9-node trajectory is visible in the Trace Explorer."*

### [1:15 - 1:30] Cryptographic Evidence Ledger & Conclusion
* **Action**: Click **Evidence Ledger** tab. Click **Verify Ledger Integrity** (shows green 100% Valid). Click **Simulate DB Tampering** (shows immediate red alert).
* **Speaker**: *"Finally, every state mutation emits an append-only SHA-256 hash-chain receipt. If a malicious database admin alters even one byte of history, our verification mathematically pinpoints the exact corrupted block. The entire release gate runs locally with `make eval`. Thank you!"*
