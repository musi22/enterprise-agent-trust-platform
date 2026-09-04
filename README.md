# Agentic Commerce Reliability & Recovery Lab

> **Enterprise Agent Trust & Evaluation Platform**  
> An independently built, Amazon-inspired retail operations agent reliability sandbox and evaluation harness.
>
> 🌐 **Live Web Console:** [https://enterprise-ai-web-production.up.railway.app](https://enterprise-ai-web-production.up.railway.app)  
> ⚡ **Live API Documentation:** [https://enterprise-ai-api-production.up.railway.app/docs](https://enterprise-ai-api-production.up.railway.app/docs)  
> 📖 **Recruiter Quickstart:** [QUICK_START.md](QUICK_START.md)

[![Live Demo](https://img.shields.io/badge/Live%20Demo-Active%20(Railway)-success?style=for-the-badge&logo=railway)](https://enterprise-ai-web-production.up.railway.app)
[![API Docs](https://img.shields.io/badge/Swagger%20API-v1.0.0-blue?style=for-the-badge&logo=fastapi)](https://enterprise-ai-api-production.up.railway.app/docs)
[![Release Gate](https://img.shields.io/badge/Release%20Gate-PASSED-emerald?style=for-the-badge)](results/amazon_inspired_result_card.md)
[![Python](https://img.shields.io/badge/Python-3.11%20%7C%203.12-blue?style=for-the-badge&logo=python)](apps/api)
[![LangGraph](https://img.shields.io/badge/LangGraph-9--Node%20State%20Machine-cyan?style=for-the-badge)](packages/agent)
[![Next.js](https://img.shields.io/badge/Next.js-14%20Console-black?style=for-the-badge&logo=next.js)](apps/web)

---

## ⚡ 60-Second Live Tour for Recruiters & Hiring Managers

Click **[Live Web Console](https://enterprise-ai-web-production.up.railway.app)** (no login required, 24/7 online):

1. **Overview Tab:** Review the executive reliability dashboard with real-time release gates (`PASSED`), failure taxonomy, and KPI cards (+40% lift in task success).
2. **Scenario Lab:** Select any of the **20 enterprise scenarios** (e.g., `04_price_changed`, `06_cross_tenant_access_attempt`) and run live comparisons between **Baseline** (unprotected) and **Guarded** (LangGraph state machine).
3. **Trace Explorer:** Drill down into microsecond-level tool execution traces, policy validations, and state transitions.
4. **Approval Inbox:** Observe human-in-the-loop governance where high-value refunds (> $50) or risk events pause for supervisor sign-off.
5. **Benchmark & Gates:** Inspect statistical evaluation across all 20 scenarios under seeded network faults (429 rate limits, 500 errors, cache drift).
6. **Evidence Ledger:** Audit the cryptographically signed **SHA-256 hash chain** and test the real-time tamper-detection engine.

---

## 🎥 End-to-End Feature Demonstration Video

> A full automated Playwright walkthrough executing all 6 features with live UI verification, graph trace exploration, HITL approval handling, and cryptographic tamper detection.

- 📹 **Watch Video Walkthrough:** [`docs/videos/enterprise_features_demo.webm`](docs/videos/enterprise_features_demo.webm)
- 📚 **Comprehensive Feature-by-Feature Guide:** [`docs/FEATURES.md`](docs/FEATURES.md)

---

> [!IMPORTANT]
> **Independent Project Notice**: This is an independent open-source research and platform reliability project inspired by enterprise retail operations. It does not use Amazon logos, trademarks, or proprietary customer data, and makes no claim of affiliation, production access, or internal Amazon knowledge. All commerce fixtures, entities, and transactions are 100% synthetic and simulated locally.

---

## 📌 For Technical Recruiters & Hiring Managers

**Target Roles**: AI Platform Engineer &bull; Agent Infrastructure Engineer &bull; Backend Software Engineer (Amazon / AWS / Enterprise AI)

### Core Architecture Competencies Demonstrated:
* **Autonomous Agent State Machines**: Built a 9-node LangGraph state machine separating intent classification, planning, authorization, tool dispatch, result validation, and audit logging.
* **Deterministic Policy Enforcement**: Pre-execution security engine enforcing RBAC, multi-tenant resource ownership, order lifecycle state machines, and prompt injection defense.
* **Distributed Systems Resilience**: Idempotency key deduplication (0.0% duplicate writes), transactional outbox pattern, and bounded exponential backoff ($2^{N-1} \times 0.1\text{s}$) healing transient 429/500 faults.
* **Cryptographic Auditing**: Append-only SHA-256 hash-chain evidence ledger with $O(N)$ tamper detection pinpointing exact corrupted block indices.
* **Release Gate Evaluation**: 20 ground-truth scenarios achieving **100% Task Success** (+40% lift over Baseline) and **0.0% Unauthorized Actions**.

### Verified Resume Bullets:
* *Architected a 9-node LangGraph autonomous agent state machine for retail operations, decoupling probabilistic LLM planning from deterministic RBAC policy evaluation, order-state precondition checks, and output validation.*
* *Engineered an append-only SHA-256 cryptographic evidence ledger, linking model decisions and tool executions into a tamper-evident hash chain with mathematical integrity verification and PII/secret redaction.*
* *Built a deterministic fault-injection engine simulating 15 real-world distributed failure modes (HTTP 429 rate limits, 500 errors, stale inventory caches, price drift) with bounded exponential backoff recovery.*
* *Developed a full-stack Next.js 14 and FastAPI engineering console featuring live scenario replays, multi-tenant trace timelines, human-in-the-loop approval workflows, and interactive ledger verification.*
* *Designed an automated CI release gate evaluating 20 ground-truth scenarios across baseline and guarded agents, achieving 100% critical gates pass, 0.0% unauthorized actions, and 0.0% duplicate committed writes.*

---

## 1. Problem Statement & Motivation

Existing LLM agent demonstrations typically feature unchecked model-to-tool loops, naive question-answering wrappers, or fragile recruitment workflows. When autonomous agents are exposed to mission-critical commerce operations (order fulfillment, address modifications, financial refunds, catalog updates), probabilistic planning introduces catastrophic risks:

1. **Cross-Tenant Data Leaks**: Agents query orders without ownership verification.
2. **Uncontrolled Payouts**: Automated refunds execute without financial caps or supervisor authorization.
3. **Cascading Failures**: Downstream rate limits (HTTP 429) or transient 500 errors cause crashes or duplicate write submissions.
4. **Audit Deficits**: Transient model logs lack cryptographic non-repudiation required for regulatory compliance (SOX/PCI-DSS).

The **Agentic Commerce Reliability & Recovery Lab** solves this by decoupling raw model planning from **deterministic policy enforcement, state machine validation, bounded exponential backoff recovery, and tamper-evident cryptographic auditing**.

---

## 2. Architecture & LangGraph 9-Node State Machine

The platform implements a dual-agent comparative architecture:
- **Baseline Agent**: A fair, standard model-to-tool loop with schema validation.
- **Guarded Agent**: A 9-node state machine built with **LangGraph**, **FastAPI**, **Async SQLAlchemy**, and a **Tamper-Evident SHA-256 Evidence Ledger**.

```mermaid
flowchart TB
    subgraph UI ["Engineering Console (Next.js 14 + Tailwind)"]
        Console["1. Overview & Health\n2. Scenario Lab & Replay\n3. Trace Explorer\n4. Approval Inbox\n5. Benchmark & Release Gate\n6. Cryptographic Evidence Ledger"]
    end

    subgraph API ["FastAPI Platform Core (/api/v1)"]
        RouterRuns["/runs & /replay"]
        RouterEvals["/evaluations & /benchmarks"]
        RouterGate["/release-gate"]
        RouterApprovals["/approvals"]
        RouterEvidence["/evidence & /verify"]
        RouterPolicies["/policies"]
    end

    subgraph GuardedStateGraph ["LangGraph 9-Node Guarded State Machine"]
        N1["1. classify_intent"] --> N2["2. create_plan"]
        N2 --> N3{"3. authorize_plan"}
        N3 -->|ALLOW| N5["5. execute_tool"]
        N3 -->|REQUIRE_APPROVAL| N4["4. request_approval (HITL)"]
        N3 -->|DENY| N8["8. emit_evidence_receipt"]
        N4 -->|Approved| N5
        N4 -->|Pending / Rejected| N8
        N5 --> N6{"6. validate_result"}
        N6 -->|Clean & Next Tool| N3
        N6 -->|Clean & Complete| N8
        N6 -->|Fault / Anomaly| N7{"7. recover_or_escalate"}
        N7 -->|Retryable (429/500/Timeout)| N5
        N7 -->|Fatal / Max Retries| N8
        N8 --> N9["9. complete_run"]
    end

    subgraph ResilienceBoundary ["Deterministic Policy & Storage Boundary"]
        PolicyEngine["Policy Engine\n- Tool allowlists (RBAC)\n- Resource ownership checks\n- Order state transitions\n- Refund limits ($50 threshold)"]
        FaultProxy["Fault Injection Proxy\n(15 deterministic fault rules)"]
        IdempotencyStore[("Transactional Idempotency & Outbox")]
        EvidenceLedger[("Tamper-Evident Ledger\nSHA-256 Hash Chain")]
    end

    Console <--> API
    API --> GuardedStateGraph
    N3 -.-> PolicyEngine
    N5 -.-> FaultProxy
    N5 -.-> IdempotencyStore
    N8 -.-> EvidenceLedger
```

---

## 3. Visual Tour: Engineering Console UI

| Overview & Automated Release Gate | Scenario Lab Execution & Ground-Truth Diff |
|---|---|
| ![Overview Dashboard](results/screenshots/01_overview.png) | ![Scenario Lab](results/screenshots/02_scenario_lab.png) |

| LangGraph 9-Node Execution Timeline | Dual-Agent Comparative Benchmark |
|---|---|
| ![Trace Explorer](results/screenshots/03_trace_explorer.png) | ![Benchmark Comparison](results/screenshots/05_benchmark_comparison.png) |

| Cryptographic Hash-Chain Verification (Pristine) | Cryptographic Tamper Detection (Corrupted Payload Alert) |
|---|---|
| ![Evidence Ledger Valid](results/screenshots/06_evidence_ledger_verified.png) | ![Evidence Ledger Tampered](results/screenshots/07_evidence_ledger_tampered.png) |

---

## 4. Actual Benchmark Results (Verified Local Run)

*Evaluated across all 20 labelled scenarios under identical seeds ($s=42$) and injected faults:*

| Metric Dimension | Baseline Agent | Guarded Agent | Variance / Delta | Impact Rationale |
|---|---|---|---|---|
| **Task Success Rate** | 60.0% | **100.0%** | **+40.0%** | Unhandled faults & policy breaches fail baseline |
| **Unauthorized Action Rate** | 5.0% | **0.0%** | **-5.0%** | Zero cross-tenant leaks or admin privilege bypass |
| **Policy Violation Rate** | 0.0% | **0.0%** | **0.0%** | Order state machine & refund thresholds enforced |
| **Fault Recovery Rate** | 33.3% | **66.7%** | **+33.3%** | Bounded backoff retry & circuit breaker healing |
| **Escalation Precision** | 25.0% | **100.0%** | **+75.0%** | Sensitive/hazardous disputes routed to HITL inbox |
| **Audit Receipt Completeness**| 0.0% | **100.0%** | **+100.0%**| Every write chained to SHA-256 evidence ledger |
| **p50 Execution Latency** | 8.0 ms | 30.6 ms | +22.5 ms | Negligible overhead for full policy evaluation |
| **p95 Execution Latency** | 1012.2 ms | 1140.3 ms | +128.1 ms | Includes bounded exponential backoff sleep |
| **Release Gate Decision** | 🛑 **FAIL** | 🚀 **PASSED** | **100% Critical Gates** | Ready for production candidacy |

*Raw data available in [`results/raw_benchmark.json`](results/raw_benchmark.json) and [`results/benchmark_summary.csv`](results/benchmark_summary.csv).*

---

## 4. Quickstart & Local Reproduction Commands

### Prerequisites
- Python 3.11 or 3.12
- Node.js 18+ or 20+

### Option A: Local Execution (Zero-API Key Required)

```bash
# 1. Create and activate virtual environment
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate

# 2. Install backend & frontend dependencies
make setup

# 3. Seed synthetic database (52 products, 11 users, orders)
make seed

# 4. Run test suite (19 unit & integration tests)
make test

# 5. Execute release gate benchmark
make eval

# 6. Verify cryptographic hash chain integrity
make ledger-verify

# 7. Run 90-second interactive terminal walkthrough
make demo
```

### Option B: Running the Engineering Console UI

```bash
# Terminal 1: Start FastAPI backend (port 8000)
make dev

# Terminal 2: Start Next.js frontend (port 3000)
cd apps/web
npm run dev
```
Open **`http://localhost:3000`** to access the Engineering Console.

### Option C: Full Containerized Stack via Docker Compose

```bash
docker compose -f infra/docker-compose.yml up --build
```
Spins up PostgreSQL, Redis, Redpanda, Jaeger, FastAPI, and Next.js console.

---

## 5. Repository Structure

```
├── apps/
│   ├── api/                     # FastAPI backend application
│   │   ├── app/
│   │   │   ├── api/v1/          # REST routers (runs, trace, evaluations, approvals, evidence)
│   │   │   ├── core/            # Config, security, JWT, redaction engine
│   │   │   ├── db/              # Async SQLAlchemy models, database setup, seed fixtures
│   │   │   └── main.py          # FastAPI application entrypoint
│   │   └── Dockerfile
│   └── web/                     # Next.js 14 Engineering Console
│       ├── src/
│       │   ├── app/             # App router (layout, globals, page)
│       │   ├── components/      # ConsoleHeader, Overview, ScenarioLab, Trace, Approvals, Benchmark, Evidence
│       │   └── lib/             # Typed API client
│       └── Dockerfile
├── packages/
│   ├── agent/                   # Baseline Agent & LangGraph 9-Node Guarded Agent
│   │   ├── baseline.py          # Standard model-to-tool agent
│   │   ├── guarded_graph.py     # 9-node LangGraph state machine
│   │   └── providers/           # Deterministic mock (default), optional Gemini, OpenAI, Ollama
│   ├── policies/                # Security policies (RBAC, ownership, order transitions, refund thresholds)
│   ├── sandbox_tools/           # 11 synthetic retail tools with idempotency
│   ├── fault_injection/         # Proxy supporting 15 deterministic fault types
│   ├── evaluators/              # Metrics calculator, state checker, benchmark runner
│   └── telemetry/               # Cryptographic SHA-256 evidence ledger
├── scenarios/                   # 20 ground-truth YAML scenario fixtures
├── scripts/                     # release_gate.py, verify_ledger.py, demo_walkthrough.py
├── results/                     # raw_benchmark.json, benchmark_summary.csv, result card
├── tests/                       # Unit & integration tests (19 passing tests)
├── docs/                        # 10 comprehensive architecture & portfolio documents
├── infra/                       # docker-compose.yml, prometheus.yml
├── Makefile                     # Developer automation commands
└── README.md
```

---

## 6. Security, Privacy & Compliance Statement

- **Strict Multi-Tenant Isolation**: The `ResourceOwnershipRule` prevents cross-tenant data leakage by verifying customer ownership before any order or refund lookup.
- **PII / Secret Redaction**: All audit logs pass through a regex sanitization pipeline before persistence, replacing credit cards, credentials, and tokens with `[REDACTED]`.
- **Tamper-Evident Audit Ledger**: Every write operation is linked via SHA-256 hash chaining. If any record is altered in the database, `make ledger-verify` pinpoints the exact corrupted block index.
- **Prompt Injection Defense**: Adversarial tokens ("ignore instructions", "you are admin") are neutralized by linguistic filtering and code-level tool allowlists.

---

## 7. Portfolio Documentation Suite

- [`docs/problem-memo.md`](docs/problem-memo.md): Strategic memo on autonomous agent reliability in enterprise commerce.
- [`docs/architecture.md`](docs/architecture.md): In-depth 9-node LangGraph state machine specification.
- [`docs/threat-model.md`](docs/threat-model.md): STRIDE threat analysis for commerce agents.
- [`docs/evaluation-methodology.md`](docs/evaluation-methodology.md): Mathematical formulations and statistical rigor.
- [`docs/failure-taxonomy.md`](docs/failure-taxonomy.md): Taxonomy of agent failure modes.
- [`docs/limitations.md`](docs/limitations.md): Explicit assumptions, synthetic scope, and production scaling.
- [`docs/amazon-inspired-result-card.md`](docs/amazon-inspired-result-card.md): Formal research result card.
- [`docs/interview-talking-points.md`](docs/interview-talking-points.md): High-yield interview questions for Amazon/AWS roles.
- [`docs/90-second-demo-script.md`](docs/90-second-demo-script.md): Turn-by-turn executive demonstration script.
