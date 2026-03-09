from __future__ import annotations
from enum import Enum
from typing import Tuple


class TaskStatus(str, Enum):
    PENDING = "pending"
    ASSIGNED = "assigned"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"


class Task:
    def __init__(
        self,
        task_id: int,
        pickup: Tuple[int, int],
        delivery: Tuple[int, int],
    ):
        self.id = task_id
        self.pickup = pickup
        self.delivery = delivery
        self.status = TaskStatus.PENDING
        self.assigned_robot_id: int | None = None

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "pickup": self.pickup,
            "delivery": self.delivery,
            "status": self.status.value,
            "assignedRobotId": self.assigned_robot_id,
        }
