"""Greedy task assignment: assign each pending task to the nearest idle robot."""

from __future__ import annotations

from typing import Dict, List, Tuple

from backend.models.robot import Robot, RobotState
from backend.models.task import Task, TaskStatus


def _manhattan(a: Tuple[int, int], b: Tuple[int, int]) -> int:
    return abs(a[0] - b[0]) + abs(a[1] - b[1])


def greedy_assign(
    robots: List[Robot],
    tasks: List[Task],
) -> Dict[int, int]:
    """Return mapping of robot_id -> task_id for new assignments."""
    idle_robots = [r for r in robots if r.state == RobotState.IDLE]
    pending_tasks = [t for t in tasks if t.status == TaskStatus.PENDING]

    assignments: Dict[int, int] = {}
    used_robots: set[int] = set()
    used_tasks: set[int] = set()

    for task in pending_tasks:
        best_robot = None
        best_dist = float("inf")
        for robot in idle_robots:
            if robot.id in used_robots:
                continue
            d = _manhattan((robot.x, robot.y), task.pickup)
            if d < best_dist:
                best_dist = d
                best_robot = robot
        if best_robot is not None:
            assignments[best_robot.id] = task.id
            used_robots.add(best_robot.id)
            used_tasks.add(task.id)

    return assignments
