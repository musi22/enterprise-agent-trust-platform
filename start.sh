#!/usr/bin/env bash
# ============================================================
# start.sh -- One-command startup for Mac/Linux
# Usage: bash start.sh
#        GEMINI_API_KEY=your_key bash start.sh   (for live mode)
# ============================================================
set -e

if [ ! -f .env ]; then
  cp .env.example .env
  echo "[setup] Created .env from .env.example"
fi

if [ -n "$GEMINI_API_KEY" ]; then
  sed -i.bak "s|^# GEMINI_API_KEY=.*|GEMINI_API_KEY=$GEMINI_API_KEY|" .env
  sed -i.bak "s|^DEFAULT_MODEL_PROVIDER=.*|DEFAULT_MODEL_PROVIDER=gemini|" .env
  echo "[mode] LIVE mode -- Using Gemini API"
else
  echo "[mode] DEMO mode -- Using deterministic mock provider (no API key needed)"
fi

echo "NEXT_PUBLIC_API_URL=http://localhost:8000" > apps/web/.env.local

if [ ! -d ".venv" ]; then
  python3 -m venv .venv
  source .venv/bin/activate
  pip install -r requirements.txt
else
  source .venv/bin/activate
fi

if [ ! -d "apps/web/node_modules" ]; then
  cd apps/web && npm install && cd ../..
fi

python -m apps.api.app.db.seed_data

python -m uvicorn apps.api.app.main:app --host 0.0.0.0 --port 8000 &
API_PID=$!

for i in 1 2 3 4 5 6 7 8 9 10 11 12 13 14 15 16 17 18 19 20; do
  curl -sf http://localhost:8000/health/live > /dev/null 2>&1 && break
  sleep 1
done

cd apps/web && npm run dev &
WEB_PID=$!
cd ../..

sleep 4

echo ""
echo "===================================================="
echo "  ENTERPRISE AI PLATFORM IS RUNNING"
echo "===================================================="
echo "  Dashboard:  http://localhost:3000"
echo "  API Docs:   http://localhost:8000/docs"
echo "  Mode:       $([ -n "$GEMINI_API_KEY" ] && echo "LIVE (Gemini)" || echo "DEMO (Mock)")"
echo "===================================================="
echo "  Press Ctrl+C to stop."

trap "kill $API_PID $WEB_PID 2>/dev/null; echo Stopped." INT TERM
wait