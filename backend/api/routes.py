from __future__ import annotations

from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from pydantic import BaseModel
from typing import Optional
import asyncio
import json

from backend.simulation.engine import SimulationEngine
from backend.simulation.scenarios import SCENARIOS

router = APIRouter()

_engine: Optional[SimulationEngine] = None


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
    global _engine
    if req.scenario not in SCENARIOS:
        return {"error": f"Unknown scenario: {req.scenario}"}
    scenario = SCENARIOS[req.scenario]()
    _engine = SimulationEngine(
        grid=scenario["grid"],
        robots=scenario["robots"],
        tasks=scenario["tasks"],
        algorithm=req.algorithm,
    )
    snapshot = _engine.solve_all()
    plan = _engine.get_full_plan()
    return {**snapshot, "plan": plan}


@router.post("/step")
def step():
    global _engine
    if _engine is None:
        return {"error": "No active simulation. Call /solve first."}
    return _engine.step()


@router.websocket("/ws/simulation")
async def simulation_ws(websocket: WebSocket):
    global _engine
    await websocket.accept()
    try:
        while True:
            data = await websocket.receive_text()
            msg = json.loads(data)

            if msg.get("type") == "solve":
                scenario_key = msg.get("scenario", "simple")
                algorithm = msg.get("algorithm", "cbs")
                if scenario_key not in SCENARIOS:
                    await websocket.send_json({"error": f"Unknown scenario: {scenario_key}"})
                    continue
                scenario = SCENARIOS[scenario_key]()
                _engine = SimulationEngine(
                    grid=scenario["grid"],
                    robots=scenario["robots"],
                    tasks=scenario["tasks"],
                    algorithm=algorithm,
                )
                snapshot = _engine.solve_all()
                plan = _engine.get_full_plan()
                await websocket.send_json({
                    "type": "solved",
                    **snapshot,
                    "plan": plan,
                })

            elif msg.get("type") == "step":
                if _engine is None:
                    await websocket.send_json({"error": "No simulation active"})
                else:
                    snapshot = _engine.step()
                    await websocket.send_json({"type": "step", **snapshot})

    except WebSocketDisconnect:
        pass
