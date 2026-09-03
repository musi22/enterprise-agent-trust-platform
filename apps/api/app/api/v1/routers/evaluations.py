import json
from pathlib import Path
from typing import Dict, Any, Optional
from fastapi import APIRouter, BackgroundTasks, HTTPException
from packages.evaluators.runner import BenchmarkRunner

router = APIRouter(tags=["Evaluations & Benchmarks"])

@router.post("/evaluations")
async def trigger_evaluation_batch(background_tasks: BackgroundTasks, reps: int = 1):
    """Trigger an asynchronous benchmark evaluation across all 20 scenarios."""
    runner = BenchmarkRunner()
    # Run synchronously or dispatch to background task
    summary = await runner.run_benchmark(repetitions_per_scenario=reps)
    return {
        "status": "completed",
        "total_scenarios": summary["total_scenarios"],
        "total_runs": summary["total_runs"],
        "release_gate_passed": summary["release_gate_passed"],
        "timestamp": summary["timestamp"]
    }

@router.get("/benchmarks/latest")
async def get_latest_benchmark():
    """Retrieve the most recent benchmark comparison results."""
    raw_path = Path("results/raw_benchmark.json")
    if not raw_path.exists():
        # Run one quick iteration if not present
        runner = BenchmarkRunner()
        return await runner.run_benchmark(repetitions_per_scenario=1)

    with open(raw_path, "r", encoding="utf-8") as fp:
        data = json.load(fp)

    return {
        "timestamp": data.get("timestamp"),
        "total_scenarios": data.get("total_scenarios"),
        "total_runs": data.get("total_runs"),
        "release_gate_passed": data.get("release_gate_passed"),
        "critical_gates": data.get("critical_gates"),
        "baseline_metrics": data.get("baseline_metrics"),
        "guarded_metrics": data.get("guarded_metrics")
    }

@router.get("/release-gate")
async def get_release_gate_status():
    """Retrieve current release-gate criteria status and markdown result card."""
    raw_path = Path("results/raw_benchmark.json")
    card_path = Path("results/amazon_inspired_result_card.md")

    if not raw_path.exists():
        runner = BenchmarkRunner()
        await runner.run_benchmark(repetitions_per_scenario=1)

    with open(raw_path, "r", encoding="utf-8") as fp:
        data = json.load(fp)

    result_card_md = ""
    if card_path.exists():
        with open(card_path, "r", encoding="utf-8") as fp:
            result_card_md = fp.read()

    return {
        "release_gate_passed": data.get("release_gate_passed", False),
        "critical_gates": data.get("critical_gates", {}),
        "timestamp": data.get("timestamp"),
        "baseline_metrics": data.get("baseline_metrics"),
        "guarded_metrics": data.get("guarded_metrics"),
        "result_card_markdown": result_card_md
    }
