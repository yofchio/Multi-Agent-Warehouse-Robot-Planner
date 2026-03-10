from __future__ import annotations

import json
import os
from typing import Dict, Tuple

from fastapi import APIRouter
from pydantic import BaseModel

from backend.simulation.scenarios import SCENARIOS

router = APIRouter()

PRECOMPUTED_FILE = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "precomputed.json")

_cache: Dict[str, dict] = {}

if os.path.isfile(PRECOMPUTED_FILE):
    with open(PRECOMPUTED_FILE, "r", encoding="utf-8") as f:
        _cache = json.load(f)


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
    cache_key = f"{req.scenario}_{req.algorithm}"
    if cache_key in _cache:
        return _cache[cache_key]
    return {"error": f"Unknown scenario/algorithm: {req.scenario}/{req.algorithm}"}
