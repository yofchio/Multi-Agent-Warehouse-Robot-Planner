"""Pre-defined warehouse scenarios for the demo."""

from __future__ import annotations

from typing import Dict, List, Tuple

from backend.models.grid import CellType, Grid
from backend.models.robot import Robot
from backend.models.task import Task

ROBOT_COLORS = [
    "#4fc3f7",  # light blue
    "#ff8a65",  # orange
    "#81c784",  # green
    "#ba68c8",  # purple
    "#fff176",  # yellow
    "#f06292",  # pink
    "#4db6ac",  # teal
    "#e57373",  # red
    "#64b5f6",  # blue
    "#aed581",  # light green
    "#9575cd",  # deep purple
    "#4dd0e1",  # cyan
]


def _place_shelves(grid: Grid, shelf_rows: List[Tuple[int, int, int, int]]):
    """shelf_rows: list of (y_start, y_end, x_start, x_end) inclusive."""
    for ys, ye, xs, xe in shelf_rows:
        for y in range(ys, ye + 1):
            for x in range(xs, xe + 1):
                grid.cells[y, x] = CellType.SHELF


def _place_stations(
    grid: Grid,
    pickups: List[Tuple[int, int]],
    deliveries: List[Tuple[int, int]],
):
    for x, y in pickups:
        grid.cells[y, x] = CellType.PICKUP
    for x, y in deliveries:
        grid.cells[y, x] = CellType.DELIVERY


def build_simple_scenario() -> Dict:
    """3 robots, 3 tasks, small 12x10 warehouse."""
    grid = Grid(12, 10)
    _place_shelves(grid, [
        (2, 3, 2, 3), (2, 3, 5, 6), (2, 3, 8, 9),
        (6, 7, 2, 3), (6, 7, 5, 6), (6, 7, 8, 9),
    ])
    pickups = [(1, 4), (4, 4), (7, 4)]
    deliveries = [(10, 1), (10, 5), (10, 8)]
    _place_stations(grid, pickups, deliveries)

    robots = [
        Robot(0, 0, 0, ROBOT_COLORS[0]),
        Robot(1, 0, 5, ROBOT_COLORS[1]),
        Robot(2, 0, 9, ROBOT_COLORS[2]),
    ]
    tasks = [
        Task(0, pickups[0], deliveries[0]),
        Task(1, pickups[1], deliveries[1]),
        Task(2, pickups[2], deliveries[2]),
    ]
    return {"grid": grid, "robots": robots, "tasks": tasks, "name": "Simple (3 robots)"}


def build_medium_scenario() -> Dict:
    """6 robots, 8 tasks, 16x12 warehouse."""
    grid = Grid(16, 12)
    _place_shelves(grid, [
        (2, 3, 2, 3), (2, 3, 5, 6), (2, 3, 8, 9), (2, 3, 11, 12),
        (5, 6, 2, 3), (5, 6, 5, 6), (5, 6, 8, 9), (5, 6, 11, 12),
        (8, 9, 2, 3), (8, 9, 5, 6), (8, 9, 8, 9), (8, 9, 11, 12),
    ])
    pickups = [(1, 4), (4, 4), (7, 4), (10, 4), (1, 7), (4, 7), (7, 7), (10, 7)]
    deliveries = [(14, 0), (14, 2), (14, 4), (14, 6), (14, 8), (14, 10), (14, 11), (14, 1)]
    _place_stations(grid, pickups, deliveries)

    robots = [Robot(i, 0, i * 2, ROBOT_COLORS[i]) for i in range(6)]
    tasks = [Task(i, pickups[i], deliveries[i]) for i in range(8)]
    return {"grid": grid, "robots": robots, "tasks": tasks, "name": "Medium (6 robots)"}


def build_bottleneck_scenario() -> Dict:
    """4 robots that must pass through a narrow corridor."""
    grid = Grid(14, 10)
    # walls forming a narrow corridor in the middle
    for y in range(10):
        if y != 4 and y != 5:
            grid.cells[y, 6] = CellType.OBSTACLE
            grid.cells[y, 7] = CellType.OBSTACLE
    # shelves on left side
    _place_shelves(grid, [
        (1, 2, 1, 2), (1, 2, 4, 5),
        (7, 8, 1, 2), (7, 8, 4, 5),
    ])
    # shelves on right side
    _place_shelves(grid, [
        (1, 2, 9, 10), (1, 2, 12, 13),
        (7, 8, 9, 10), (7, 8, 12, 13),
    ])
    pickups = [(3, 4), (3, 5), (0, 4), (0, 5)]
    deliveries = [(11, 4), (11, 5), (13, 4), (13, 5)]
    _place_stations(grid, pickups, deliveries)

    robots = [
        Robot(0, 0, 0, ROBOT_COLORS[0]),
        Robot(1, 0, 9, ROBOT_COLORS[1]),
        Robot(2, 13, 0, ROBOT_COLORS[2]),
        Robot(3, 13, 9, ROBOT_COLORS[3]),
    ]
    tasks = [
        Task(0, pickups[0], deliveries[0]),
        Task(1, pickups[1], deliveries[1]),
        Task(2, pickups[2], deliveries[2]),
        Task(3, pickups[3], deliveries[3]),
    ]
    return {"grid": grid, "robots": robots, "tasks": tasks, "name": "Bottleneck (narrow corridor)"}


def build_large_scenario() -> Dict:
    """10 robots, 15 tasks, 20x14 warehouse."""
    grid = Grid(20, 14)
    _place_shelves(grid, [
        (2, 3, 2, 3), (2, 3, 5, 6), (2, 3, 8, 9), (2, 3, 11, 12), (2, 3, 14, 15),
        (5, 6, 2, 3), (5, 6, 5, 6), (5, 6, 8, 9), (5, 6, 11, 12), (5, 6, 14, 15),
        (8, 9, 2, 3), (8, 9, 5, 6), (8, 9, 8, 9), (8, 9, 11, 12), (8, 9, 14, 15),
        (11, 12, 2, 3), (11, 12, 5, 6), (11, 12, 8, 9), (11, 12, 11, 12), (11, 12, 14, 15),
    ])
    pickups = [
        (1, 4), (4, 4), (7, 4), (10, 4), (13, 4),
        (1, 7), (4, 7), (7, 7), (10, 7), (13, 7),
        (1, 10), (4, 10), (7, 10), (10, 10), (13, 10),
    ]
    deliveries = [
        (18, 0), (18, 1), (18, 2), (18, 3), (18, 4),
        (18, 5), (18, 6), (18, 7), (18, 8), (18, 9),
        (18, 10), (18, 11), (18, 12), (18, 13), (18, 0),
    ]
    _place_stations(grid, pickups, deliveries)

    robots = [Robot(i, 0, i if i < 14 else 13, ROBOT_COLORS[i]) for i in range(10)]
    tasks = [Task(i, pickups[i], deliveries[i]) for i in range(15)]
    return {"grid": grid, "robots": robots, "tasks": tasks, "name": "Large (10 robots)"}


SCENARIOS = {
    "simple": build_simple_scenario,
    "medium": build_medium_scenario,
    "bottleneck": build_bottleneck_scenario,
    "large": build_large_scenario,
}
