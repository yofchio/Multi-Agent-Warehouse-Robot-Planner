"""Standard A* and Space-Time A* for single-agent path-finding."""

from __future__ import annotations

import heapq
from typing import Dict, List, Optional, Set, Tuple

from backend.models.grid import Grid


def heuristic(a: Tuple[int, int], b: Tuple[int, int]) -> int:
    return abs(a[0] - b[0]) + abs(a[1] - b[1])


# ---------- plain A* ----------

def astar(
    grid: Grid,
    start: Tuple[int, int],
    goal: Tuple[int, int],
) -> Optional[List[Tuple[int, int]]]:
    """Return shortest path from *start* to *goal* on *grid*, or None."""
    if start == goal:
        return [start]

    open_set: list[Tuple[int, Tuple[int, int]]] = []
    heapq.heappush(open_set, (0, start))
    came_from: Dict[Tuple[int, int], Tuple[int, int]] = {}
    g_score: Dict[Tuple[int, int], int] = {start: 0}

    while open_set:
        _, current = heapq.heappop(open_set)
        if current == goal:
            path = [current]
            while current in came_from:
                current = came_from[current]
                path.append(current)
            return path[::-1]

        for nx, ny in grid.neighbors(*current):
            nb = (nx, ny)
            tentative = g_score[current] + 1
            if tentative < g_score.get(nb, float("inf")):
                came_from[nb] = current
                g_score[nb] = tentative
                f = tentative + heuristic(nb, goal)
                heapq.heappush(open_set, (f, nb))

    return None


# ---------- Space-Time A* ----------

STNode = Tuple[int, int, int]  # (x, y, t)

Constraint = Tuple[int, int, int]          # vertex: (x, y, t)
EdgeConstraint = Tuple[int, int, int, int, int, int]  # (x1,y1,x2,y2,t_from,t_to)


def _goal_safe_after(
    goal: Tuple[int, int],
    arrival_time: int,
    occupied_at: Dict[int, Set[Tuple[int, int]]],
    max_time: int,
) -> bool:
    """Check that no other agent occupies *goal* at any time >= arrival_time."""
    for t in range(arrival_time, max_time + 1):
        if goal in occupied_at.get(t, set()):
            return False
    return True


SwapEdge = Tuple[int, int, int, int]  # (from_x, from_y, to_x, to_y)


def _build_occupied_map(
    other_paths: Optional[Dict[int, List[Tuple[int, int]]]],
    max_time: int,
) -> Tuple[Dict[int, Set[Tuple[int, int]]], Dict[int, Set[SwapEdge]], int]:
    """Build time->positions and time->edges maps from other agents' paths."""
    occupied_at: Dict[int, Set[Tuple[int, int]]] = {}
    edges_at: Dict[int, Set[SwapEdge]] = {}
    max_other_time = 0
    if other_paths:
        for path in other_paths.values():
            for t, pos in enumerate(path):
                occupied_at.setdefault(t, set()).add(pos)
                if t + 1 < len(path):
                    nxt = path[t + 1]
                    if pos != nxt:
                        edges_at.setdefault(t, set()).add((pos[0], pos[1], nxt[0], nxt[1]))
            if path:
                last = path[-1]
                end_t = len(path) - 1
                if end_t > max_other_time:
                    max_other_time = end_t
                for t in range(len(path), max_time + 1):
                    occupied_at.setdefault(t, set()).add(last)
    return occupied_at, edges_at, max_other_time


def spacetime_astar(
    grid: Grid,
    start: Tuple[int, int],
    goal: Tuple[int, int],
    constraints: Optional[Set[Constraint]] = None,
    edge_constraints: Optional[Set[EdgeConstraint]] = None,
    max_time: int = 200,
    other_paths: Optional[Dict[int, List[Tuple[int, int]]]] = None,
    start_time: int = 0,
    occupied_at: Optional[Dict[int, Set[Tuple[int, int]]]] = None,
    edges_at: Optional[Dict[int, Set[SwapEdge]]] = None,
    max_other_time: int = 0,
) -> Optional[List[Tuple[int, int]]]:
    """A* in (x, y, t) space respecting vertex and edge constraints.

    *other_paths* maps agent_id -> path; used by prioritized planning to avoid
    agents that have already been planned.
    *start_time* allows starting from a non-zero timestep (for multi-phase planning).
    *occupied_at* pre-built occupation map (avoids rebuilding for chained calls).
    *edges_at* pre-built edge map for swap conflict detection.
    """
    if constraints is None:
        constraints = set()
    if edge_constraints is None:
        edge_constraints = set()

    if occupied_at is None:
        occupied_at, edges_at_built, max_other_time = _build_occupied_map(other_paths, max_time)
        if edges_at is None:
            edges_at = edges_at_built
    if edges_at is None:
        edges_at = {}

    check_goal_safety = bool(other_paths) or len(occupied_at) > 0

    start_node: STNode = (start[0], start[1], start_time)
    open_set: list[Tuple[int, int, STNode]] = []
    counter = 0
    heapq.heappush(open_set, (heuristic(start, goal), counter, start_node))
    came_from: Dict[STNode, STNode] = {}
    g_score: Dict[STNode, int] = {start_node: 0}

    while open_set:
        _, _, current = heapq.heappop(open_set)
        cx, cy, ct = current

        if (cx, cy) == goal:
            if check_goal_safety and not _goal_safe_after(goal, ct, occupied_at, max(ct + 20, max_other_time + 5)):
                pass
            else:
                path: list[Tuple[int, int]] = [(cx, cy)]
                node = current
                while node in came_from:
                    node = came_from[node]
                    path.append((node[0], node[1]))
                return path[::-1]

        if ct >= max_time:
            continue

        nt = ct + 1
        moves = grid.neighbors(cx, cy) + [(cx, cy)]  # include wait
        for nx, ny in moves:
            if (nx, ny, nt) in constraints:
                continue
            if (cx, cy, nx, ny, ct, nt) in edge_constraints:
                continue
            if (nx, ny) in occupied_at.get(nt, set()):
                continue
            # Swap conflict: another agent moving (nx,ny)->(cx,cy) at time ct
            if (nx, ny) != (cx, cy) and (nx, ny, cx, cy) in edges_at.get(ct, set()):
                continue

            nb: STNode = (nx, ny, nt)
            tentative = g_score[current] + 1
            if tentative < g_score.get(nb, float("inf")):
                came_from[nb] = current
                g_score[nb] = tentative
                f = tentative + heuristic((nx, ny), goal)
                counter += 1
                heapq.heappush(open_set, (f, counter, nb))

    return None
