from pathlib import Path
from typing import List, Dict, Any
import yaml
from fastapi import APIRouter, HTTPException

router = APIRouter(prefix="/scenarios", tags=["Scenarios"])

@router.get("")
async def list_scenarios() -> List[Dict[str, Any]]:
    """List all 20 labelled reliability and recovery benchmark scenarios."""
    scenarios_dir = Path("scenarios")
    if not scenarios_dir.exists():
        from scripts.generate_scenarios import generate_all_scenarios
        generate_all_scenarios()

    scenarios = []
    files = sorted(list(scenarios_dir.glob("*.yaml")))
    for f in files:
        with open(f, "r", encoding="utf-8") as fp:
            sc = yaml.safe_load(fp)
            scenarios.append(sc)

    return scenarios

@router.get("/{scenario_id}")
async def get_scenario(scenario_id: str) -> Dict[str, Any]:
    """Retrieve full configuration and metadata for a specific scenario."""
    file_path = Path(f"scenarios/{scenario_id}.yaml")
    if not file_path.exists():
        raise HTTPException(status_code=404, detail=f"Scenario '{scenario_id}' not found.")

    with open(file_path, "r", encoding="utf-8") as fp:
        return yaml.safe_load(fp)
