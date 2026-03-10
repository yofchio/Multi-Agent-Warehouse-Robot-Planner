from __future__ import annotations

import logging
import time
from typing import Dict, Tuple

from fastapi import APIRouter
from pydantic import BaseModel

from backend.simulation.engine import SimulationEngine
from backend.simulation.scenarios import SCENARIOS

logger = logging.getLogger(__name__)

router = APIRouter()

# Pre-computed cache: (scenario, algorithm) -> response dict
_cache: Dict[Tuple[str, str], dict] = {}


def _precompute_all():
    """Run all scenario × algorithm combinations at startup."""
    algorithms = ["cbs", "prioritized"]
    total = len(SCENARIOS) * len(algorithms)
    logger.info(f"Pre-computing {total} scenario/algorithm combinations...")
    t0 = time.time()

    for scenario_key, builder in SCENARIOS.items():
        for algo in algorithms:
            scenario = builder()
            engine = SimulationEngine(
                grid=scenario["grid"],
                robots=scenario["robots"],
                tasks=scenario["tasks"],
                algorithm=algo,
            )
            snapshot = engine.solve_all()
            plan = engine.get_full_plan()
            _cache[(scenario_key, algo)] = {**snapshot, "plan": plan}
            logger.info(f"  {scenario_key}/{algo}: {plan['totalFrames']} frames")

    elapsed = time.time() - t0
    logger.info(f"Pre-computation done in {elapsed:.2f}s")


_precompute_all()


class SolveRequest(BaseModel):
    scenario: str = "simple"
    algorithm: str = "cbs"


@router.get("/scenarios")
def list_scenarios():
    result = []
    for key, builder in SCENARIOS.items():
        s = builder()
        result.append({
            "id": key,
            "name": s["name"],
            "robotCount": len(s["robots"]),
            "taskCount": len(s["tasks"]),
            "gridWidth": s["grid"].width,
            "gridHeight": s["grid"].height,
        })
    return result


@router.post("/solve")
def solve(req: SolveRequest):
    cache_key = (req.scenario, req.algorithm)
    if cache_key in _cache:
        return _cache[cache_key]
    return {"error": f"Unknown scenario/algorithm: {req.scenario}/{req.algorithm}"}
