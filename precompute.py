"""Pre-compute all scenario/algorithm results and save to a JSON file."""

import sys
import os
import json
import time

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from backend.simulation.engine import SimulationEngine
from backend.simulation.scenarios import SCENARIOS

OUTPUT_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "backend", "precomputed.json")
ALGORITHMS = ["cbs", "prioritized"]


def main():
    results = {}
    total = len(SCENARIOS) * len(ALGORITHMS)
    print(f"Pre-computing {total} combinations...")
    t0 = time.time()

    for scenario_key, builder in SCENARIOS.items():
        for algo in ALGORITHMS:
            key = f"{scenario_key}_{algo}"
            print(f"  [{key}] computing...", end=" ", flush=True)

            t1 = time.time()
            scenario = builder()
            engine = SimulationEngine(
                grid=scenario["grid"],
                robots=scenario["robots"],
                tasks=scenario["tasks"],
                algorithm=algo,
            )
            snapshot = engine.solve_all()
            plan = engine.get_full_plan()
            elapsed = time.time() - t1

            results[key] = {**snapshot, "plan": plan}
            print(f"done in {elapsed:.2f}s  "
                  f"(frames={plan['totalFrames']}, cost={snapshot['stats']['totalCost']})")

    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        json.dump(results, f, separators=(",", ":"))

    size_mb = os.path.getsize(OUTPUT_FILE) / 1024 / 1024
    total_time = time.time() - t0
    print(f"\nSaved to {OUTPUT_FILE} ({size_mb:.2f} MB)")
    print(f"Total time: {total_time:.2f}s")


if __name__ == "__main__":
    main()
