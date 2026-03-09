from __future__ import annotations
from enum import Enum
from typing import List, Optional, Tuple


class RobotState(str, Enum):
    IDLE = "idle"
    MOVING_TO_PICKUP = "moving_to_pickup"
    PICKING = "picking"
    MOVING_TO_DELIVERY = "moving_to_delivery"
    DELIVERING = "delivering"


class Robot:
    def __init__(self, robot_id: int, x: int, y: int, color: str = "#4fc3f7"):
        self.id = robot_id
        self.x = x
        self.y = y
        self.color = color
        self.state = RobotState.IDLE
        self.current_task_id: Optional[int] = None
        self.path: List[Tuple[int, int]] = []
        self.path_index: int = 0
        self.tasks_completed: int = 0

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "x": self.x,
            "y": self.y,
            "color": self.color,
            "state": self.state.value,
            "currentTaskId": self.current_task_id,
            "path": self.path,
            "pathIndex": self.path_index,
            "tasksCompleted": self.tasks_completed,
        }
