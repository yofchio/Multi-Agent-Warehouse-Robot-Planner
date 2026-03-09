from __future__ import annotations
from enum import IntEnum
from typing import List, Tuple

import numpy as np


class CellType(IntEnum):
    EMPTY = 0
    SHELF = 1
    PICKUP = 2
    DELIVERY = 3
    OBSTACLE = 4


class Grid:
    """2-D warehouse grid."""

    def __init__(self, width: int, height: int):
        self.width = width
        self.height = height
        self.cells: np.ndarray = np.zeros((height, width), dtype=int)

    # ---- helpers ----
    def in_bounds(self, x: int, y: int) -> bool:
        return 0 <= x < self.width and 0 <= y < self.height

    def passable(self, x: int, y: int) -> bool:
        if not self.in_bounds(x, y):
            return False
        return self.cells[y, x] not in (CellType.SHELF, CellType.OBSTACLE)

    def neighbors(self, x: int, y: int) -> List[Tuple[int, int]]:
        result: list[Tuple[int, int]] = []
        for dx, dy in [(0, 1), (0, -1), (1, 0), (-1, 0)]:
            nx, ny = x + dx, y + dy
            if self.passable(nx, ny):
                result.append((nx, ny))
        return result

    def to_dict(self) -> dict:
        return {
            "width": self.width,
            "height": self.height,
            "cells": self.cells.tolist(),
        }
