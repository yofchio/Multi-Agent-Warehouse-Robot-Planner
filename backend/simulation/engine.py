"""Simulation engine: orchestrates task assignment, path planning, and
time-step execution for the warehouse demo."""

from __future__ import annotations

from typing import Any, Dict, List, Optional, Tuple

from backend.algorithms.astar import astar
from backend.algorithms.cbs import cbs_solve, cbs_full_trip, detect_first_conflict, prioritized_planning, prioritized_full_trip
from backend.algorithms.task_assignment import greedy_assign
from backend.models.grid import Grid
from backend.models.robot import Robot, RobotState
from backend.models.task import Task, TaskStatus


class SimulationEngine:
    def __init__(
        self,
        grid: Grid,
        robots: List[Robot],
        tasks: List[Task],
        algorithm: str = "cbs",
    ):
        self.grid = grid
        self.robots = {r.id: r for r in robots}
        self.tasks = {t.id: t for t in tasks}
        self.algorithm = algorithm
        self.timestep = 0
        self.finished = False
        self.conflicts_resolved = 0
        self.total_moves = 0
        self._plan_cache: Dict[int, List[Tuple[int, int]]] = {}

    # ------------------------------------------------------------------
    def solve_all(self) -> Dict[str, Any]:
        """One-shot solve: assign tasks, plan all paths, return full result."""
        assignments = greedy_assign(list(self.robots.values()), list(self.tasks.values()))
        for rid, tid in assignments.items():
            self.robots[rid].current_task_id = tid
            self.robots[rid].state = RobotState.MOVING_TO_PICKUP
            self.tasks[tid].status = TaskStatus.ASSIGNED
            self.tasks[tid].assigned_robot_id = rid

        starts: Dict[int, Tuple[int, int]] = {}
        pickups: Dict[int, Tuple[int, int]] = {}
        deliveries: Dict[int, Tuple[int, int]] = {}
        for rid, tid in assignments.items():
            r = self.robots[rid]
            t = self.tasks[tid]
            starts[rid] = (r.x, r.y)
            pickups[rid] = t.pickup
            deliveries[rid] = t.delivery

        if not starts:
            self.finished = True
            return self._snapshot()

        # Count conflicts that would exist without coordination
        self._count_naive_conflicts(starts, pickups, deliveries)

        # Plan full coordinated trips: start -> pickup -> delivery
        if self.algorithm == "cbs":
            full_paths = cbs_full_trip(self.grid, starts, pickups, deliveries)
            if full_paths is None:
                full_paths = prioritized_full_trip(self.grid, starts, pickups, deliveries)
        else:
            full_paths = prioritized_full_trip(self.grid, starts, pickups, deliveries)

        if full_paths is None:
            return self._snapshot()

        for rid, path in full_paths.items():
            self.robots[rid].path = path
            self.robots[rid].path_index = 0
            self._plan_cache[rid] = path

        return self._snapshot()

    # ------------------------------------------------------------------
    def step(self) -> Dict[str, Any]:
        """Advance one timestep; return updated snapshot."""
        if self.finished:
            return self._snapshot()

        any_active = False
        for rid, robot in self.robots.items():
            if robot.state == RobotState.IDLE and robot.path_index >= len(robot.path):
                continue
            if robot.path_index < len(robot.path) - 1:
                robot.path_index += 1
                pos = robot.path[robot.path_index]
                robot.x, robot.y = pos
                self.total_moves += 1
                any_active = True

                if robot.current_task_id is not None:
                    task = self.tasks[robot.current_task_id]
                    if (robot.x, robot.y) == task.pickup and robot.state == RobotState.MOVING_TO_PICKUP:
                        robot.state = RobotState.MOVING_TO_DELIVERY
                    elif (robot.x, robot.y) == task.delivery and robot.state == RobotState.MOVING_TO_DELIVERY:
                        robot.state = RobotState.IDLE
                        task.status = TaskStatus.COMPLETED
                        robot.tasks_completed += 1
                        robot.current_task_id = None
            else:
                if robot.state != RobotState.IDLE:
                    robot.state = RobotState.IDLE

        self.timestep += 1

        pending_tasks = [t for t in self.tasks.values() if t.status == TaskStatus.PENDING]
        idle_robots = [r for r in self.robots.values() if r.state == RobotState.IDLE]
        if pending_tasks and idle_robots:
            self._assign_and_plan()
            any_active = True

        if not any_active:
            all_done = all(t.status == TaskStatus.COMPLETED for t in self.tasks.values())
            if all_done or not any(
                r.state != RobotState.IDLE for r in self.robots.values()
            ):
                self.finished = True

        return self._snapshot()

    # ------------------------------------------------------------------
    def get_full_plan(self) -> Dict[str, Any]:
        """Return the pre-computed full paths for animation on the frontend."""
        max_t = max((len(p) for p in self._plan_cache.values()), default=0)
        frames: list[Dict] = []
        for t in range(max_t):
            frame: Dict[int, Dict] = {}
            for rid, path in self._plan_cache.items():
                idx = min(t, len(path) - 1)
                pos = path[idx]
                robot = self.robots[rid]
                task_id = None
                for tid, task in self.tasks.items():
                    if task.assigned_robot_id == rid:
                        task_id = tid
                        break
                # determine state at this timestep
                state = RobotState.IDLE.value
                if task_id is not None:
                    task = self.tasks[task_id]
                    if idx < len(path) - 1:
                        pickup_reached = False
                        for pi in range(idx + 1):
                            p = path[pi]
                            if p == task.pickup:
                                pickup_reached = True
                                break
                        state = (
                            RobotState.MOVING_TO_DELIVERY.value
                            if pickup_reached
                            else RobotState.MOVING_TO_PICKUP.value
                        )
                    else:
                        state = RobotState.IDLE.value

                frame[rid] = {
                    "x": pos[0],
                    "y": pos[1],
                    "color": robot.color,
                    "state": state,
                }
            frames.append(frame)
        return {
            "frames": frames,
            "paths": {rid: path for rid, path in self._plan_cache.items()},
            "totalFrames": max_t,
        }

    # ------------------------------------------------------------------
    def _assign_and_plan(self):
        assignments = greedy_assign(list(self.robots.values()), list(self.tasks.values()))
        if not assignments:
            return
        for rid, tid in assignments.items():
            self.robots[rid].current_task_id = tid
            self.robots[rid].state = RobotState.MOVING_TO_PICKUP
            self.tasks[tid].status = TaskStatus.ASSIGNED
            self.tasks[tid].assigned_robot_id = rid

        starts = {rid: (self.robots[rid].x, self.robots[rid].y) for rid in assignments}
        pickups = {rid: self.tasks[assignments[rid]].pickup for rid in assignments}
        deliveries_map = {rid: self.tasks[assignments[rid]].delivery for rid in assignments}

        self._count_naive_conflicts(starts, pickups, deliveries_map)

        if self.algorithm == "cbs":
            full_paths = cbs_full_trip(self.grid, starts, pickups, deliveries_map)
            if full_paths is None:
                full_paths = prioritized_full_trip(self.grid, starts, pickups, deliveries_map)
        else:
            full_paths = prioritized_full_trip(self.grid, starts, pickups, deliveries_map)

        if full_paths is None:
            return
        for rid, path in full_paths.items():
            self.robots[rid].path = path
            self.robots[rid].path_index = 0
            self._plan_cache[rid] = path

    def _count_naive_conflicts(
        self,
        starts: Dict[int, Tuple[int, int]],
        pickups: Dict[int, Tuple[int, int]],
        deliveries_map: Dict[int, Tuple[int, int]],
    ):
        """Count how many conflicts exist in uncoordinated (naive) paths."""
        naive: Dict[int, List[Tuple[int, int]]] = {}
        for aid in starts:
            p1 = astar(self.grid, starts[aid], pickups[aid])
            p2 = astar(self.grid, pickups[aid], deliveries_map[aid])
            if p1 and p2:
                naive[aid] = p1 + p2[1:]
        if naive and len(naive) == len(starts):
            conflict = detect_first_conflict(naive)
            if conflict:
                self.conflicts_resolved += 1

    def _snapshot(self) -> Dict[str, Any]:
        completed = sum(1 for t in self.tasks.values() if t.status == TaskStatus.COMPLETED)
        return {
            "timestep": self.timestep,
            "finished": self.finished,
            "robots": {rid: r.to_dict() for rid, r in self.robots.items()},
            "tasks": {tid: t.to_dict() for tid, t in self.tasks.items()},
            "stats": {
                "totalTasks": len(self.tasks),
                "completedTasks": completed,
                "totalMoves": self.total_moves,
                "conflictsResolved": self.conflicts_resolved,
                "makespan": self.timestep,
                "totalCost": sum(len(p) for p in self._plan_cache.values()),
                "algorithm": self.algorithm,
            },
            "grid": self.grid.to_dict(),
        }
