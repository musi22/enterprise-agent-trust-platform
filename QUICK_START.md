# Quick Start Guide — Enterprise Agent Trust & Evaluation Platform

> An end-to-end AI reliability & safety lab for agentic retail commerce.
> Works fully offline with realistic mock data, or connect a Gemini API key for live LLM calls.

---

## 🚀 Live Cloud Demo (Instant — No Installation Required)

Open the live cloud console directly in your browser:
- **Live Web Console:** [https://enterprise-ai-web-production.up.railway.app](https://enterprise-ai-web-production.up.railway.app)
- **Live API Documentation:** [https://enterprise-ai-api-production.up.railway.app/docs](https://enterprise-ai-api-production.up.railway.app/docs)

---

## Option 1: Run Locally (2 minutes)

### Prerequisites
- Python 3.10+ ([python.org](https://python.org))
- Node.js 18+ ([nodejs.org](https://nodejs.org))

### Windows
```powershell
git clone https://github.com/musi22/enterprise-agent-trust-platform
cd enterprise-agent-trust-platform
.\start.ps1
```

### Mac / Linux
```bash
git clone https://github.com/musi22/enterprise-agent-trust-platform
cd enterprise-agent-trust-platform
bash start.sh
```

The browser opens automatically at **http://localhost:3000**.

---

## Option 2: Docker Compose (No Python/Node install needed)

### Prerequisites
- Docker Desktop ([docker.com](https://www.docker.com/products/docker-desktop))

```bash
git clone https://github.com/musi22/enterprise-agent-trust-platform
cd enterprise-agent-trust-platform
docker compose -f infra/docker-compose.yml up --build
```

Then open **http://localhost:3000**.

---

## Live Mode vs Demo Mode

| Mode | What it does | How to enable |
|------|---|---|
| 🔵 **DEMO (Mock)** | Fully offline, deterministic AI responses, no API key needed | Default — just run the app |
| 🟢 **LIVE (Gemini)** | Real Google Gemini LLM for intent classification & planning | Set `GEMINI_API_KEY=your_key` |

### Enabling Live Mode
```bash
# Mac/Linux
GEMINI_API_KEY=your_key bash start.sh

# Windows PowerShell
$env:GEMINI_API_KEY="your_key"; .\start.ps1

# Docker
GEMINI_API_KEY=your_key docker compose -f infra/docker-compose.yml up --build
```

Get a free Gemini API key at: https://aistudio.google.com/app/apikey

---

## What You Can Do

| Feature | What to explore |
|---|---|
| **Overview** | Release gate dashboard, KPI cards, failure taxonomy |
| **Scenario Lab** | Run any of 20 labelled scenarios — baseline vs guarded agent |
| **Trace Explorer** | 9-node LangGraph execution timeline with full event trace |
| **Approval Inbox** | Human-in-the-loop (HITL) approval queue for high-risk actions |
| **Benchmark & Gates** | Side-by-side agent comparison with download CSV/JSON |
| **Evidence Ledger** | Cryptographic SHA-256 hash-chain integrity + tamper detection |

---

## API Documentation

Interactive Swagger UI available at: **http://localhost:8000/docs**

---

## Architecture

```
┌─────────────────────────────────────────────────────┐
│  Next.js 14 Engineering Console  (port 3000)        │
│  6 Feature Tabs + Real-time API integration         │
└───────────────────┬─────────────────────────────────┘
                    │ REST API
┌───────────────────▼─────────────────────────────────┐
│  FastAPI Backend  (port 8000)                       │
│  LangGraph 9-Node Guarded Agent                     │
│  Policy Engine · Evidence Ledger · HITL Approvals   │
│  SQLite (local) or PostgreSQL (Docker)              │
└─────────────────────────────────────────────────────┘
         │                         │
   Gemini API (optional)    Deterministic Mock
   (LIVE mode)              (DEMO mode - default)
```

---

## Running Tests

```bash
# All unit + integration tests
python -m pytest tests/ -v

# E2E Playwright tests (requires both servers running)
python -m pytest tests/e2e/ -v -s

# E2E with video recording
python tests/e2e/run_with_video.py
```

---

*Built with FastAPI · LangGraph · Next.js 14 · SQLite · Playwright*