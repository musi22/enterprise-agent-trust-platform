import pytest
from httpx import AsyncClient, ASGITransport
from apps.api.app.main import app

@pytest.mark.asyncio
async def test_api_health():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        res = await client.get("/health/live")
        assert res.status_code == 200
        assert res.json()["live"] is True

        res_ready = await client.get("/health/ready")
        assert res_ready.status_code == 200
        assert res_ready.json()["ready"] is True

@pytest.mark.asyncio
async def test_api_policies_list():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        res = await client.get("/api/v1/policies")
        assert res.status_code == 200
        data = res.json()
        assert data["active_rules_count"] > 0
        assert "customer" in data["role_tool_allowlists"]

@pytest.mark.asyncio
async def test_api_scenarios_list():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        res = await client.get("/api/v1/scenarios")
        assert res.status_code == 200
        scenarios = res.json()
        assert len(scenarios) == 20
        scenario_ids = [s["id"] for s in scenarios]
        assert "01_catalog_search" in scenario_ids
        assert "20_ambiguous_escalation" in scenario_ids

@pytest.mark.asyncio
async def test_api_run_and_trace():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        # Create run
        res = await client.post("/api/v1/runs", json={
            "scenario_id": "01_catalog_search",
            "agent_mode": "guarded",
            "seed": 42
        })
        assert res.status_code == 200
        data = res.json()
        assert data["status"] == "SUCCESS"
        run_id = data["run_id"]

        # Fetch trace
        trace_res = await client.get(f"/api/v1/runs/{run_id}/trace")
        assert trace_res.status_code == 200
        trace = trace_res.json()
        assert len(trace["events"]) > 0
        assert len(trace["tool_calls"]) > 0
        assert trace["evidence_receipt"] is not None

@pytest.mark.asyncio
async def test_api_evidence_verification():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        res = await client.post("/api/v1/evidence/verify")
        assert res.status_code == 200
        data = res.json()
        assert data["valid"] is True
        assert data["tamper_detected"] is False

@pytest.mark.asyncio
async def test_api_benchmarks_and_gate():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        bench_res = await client.get("/api/v1/benchmarks/latest")
        assert bench_res.status_code == 200
        bench = bench_res.json()
        assert "baseline_metrics" in bench
        assert "guarded_metrics" in bench

        gate_res = await client.get("/api/v1/release-gate")
        assert gate_res.status_code == 200
        gate = gate_res.json()
        assert "release_gate_passed" in gate
        assert "critical_gates" in gate
