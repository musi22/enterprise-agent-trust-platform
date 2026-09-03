.PHONY: setup dev seed test eval lint ledger-verify demo docker-up docker-down help

PYTHON := .venv/bin/python
ifeq ($(OS),Windows_NT)
    PYTHON := .venv\Scripts\python.exe
endif

help:
	@echo "Agentic Commerce Reliability & Recovery Lab - Commands:"
	@echo "  make setup          - Install Python and Node dependencies"
	@echo "  make seed           - Seed synthetic database with 50+ products, 10+ users, orders"
	@echo "  make test           - Run full test suite (unit and integration)"
	@echo "  make eval           - Execute release gate benchmark across all 20 scenarios"
	@echo "  make ledger-verify  - Cryptographically verify tamper-evident evidence ledger"
	@echo "  make dev            - Start FastAPI backend server"
	@echo "  make demo           - Run interactive terminal walkthrough demo"
	@echo "  make docker-up      - Launch full stack in Docker Compose"

setup:
	$(PYTHON) -m pip install -r requirements.txt
	cd apps/web && npm install

seed:
	$(PYTHON) -m apps.api.app.db.seed_data

test:
	$(PYTHON) -m pytest tests/ -v

eval:
	$(PYTHON) -m scripts.release_gate --reps 1

ledger-verify:
	$(PYTHON) -m scripts.verify_ledger

dev:
	$(PYTHON) -m apps.api.app.main

demo:
	$(PYTHON) -m scripts.demo_walkthrough

docker-up:
	docker compose -f infra/docker-compose.yml up --build

docker-down:
	docker compose -f infra/docker-compose.yml down
