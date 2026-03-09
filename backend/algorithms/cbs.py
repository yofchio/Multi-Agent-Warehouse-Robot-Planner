"""Conflict-Based Search (CBS) for Multi-Agent Path Finding."""

from __future__ import annotations

import heapq
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Set, Tuple

from backend.algorithms.astar import spacetime_astar, _build_occupied_map, Constraint, EdgeConstraint
from backend.models.grid import Grid


@dataclass
class Conflict:
    agent_i: int
    agent_j: int
    position: Tuple[int, int]
    timestep: int
    is_edge: bool = False
    pos_i: Tuple[int, int] = (0, 0)
    pos_j: Tuple[int, int] = (0, 0)


@dataclass(order=True)
class CTNode:
    cost: int
    id: int = field(compare=True)
    constraints: Dict[int, Set[Constraint]] = field(default_factory=dict, compare=False)
    edge_constraints: Dict[int, Set[EdgeConstraint]] = field(default_factory=dict, compare=False)
    paths: Dict[int, List[Tuple[int, int]]] = field(default_factory=dict, compare=False)
    conflicts_resolved: int = field(default=0, compare=False)


def detect_first_conflict(
    paths: Dict[int, List[Tuple[int, int]]],
) -> Optional[Conflict]:
    agents = sorted(paths.keys())
    max_t = max(len(p) for p in paths.values())

    def pos_at(agent: int, t: int) -> Tuple[int, int]:
        p = paths[agent]
        return p[t] if t < len(p) else p[-1]

    for t in range(max_t):
        for i_idx in range(len(agents)):
            for j_idx in range(i_idx + 1, len(agents)):
                ai, aj = agents[i_idx], agents[j_idx]
                pi, pj = pos_at(ai, t), pos_at(aj, t)
                # vertex conflict
                if pi == pj:
                    return Conflict(ai, aj, pi, t)
                # edge conflict (swap)
                if t + 1 < max_t:
                    pi_next, pj_next = pos_at(ai, t + 1), pos_at(aj, t + 1)
                    if pi == pj_next and pj == pi_next:
                        return Conflict(ai, aj, pi, t, is_edge=True, pos_i=pi, pos_j=pj)
    return None


def _total_cost(paths: Dict[int, List[Tuple[int, int]]]) -> int:
    return sum(len(p) for p in paths.values())


_node_counter = 0


def cbs_solve(
    grid: Grid,
    starts: Dict[int, Tuple[int, int]],
    goals: Dict[int, Tuple[int, int]],
    max_time: int = 200,
) -> Optional[Dict[int, List[Tuple[int, int]]]]:
    """Run CBS and return dict of agent_id -> path, or None."""
    global _node_counter
    _node_counter = 0

    root_paths: Dict[int, List[Tuple[int, int]]] = {}
    for agent_id in starts:
        path = spacetime_astar(grid, starts[agent_id], goals[agent_id], max_time=max_time)
        if path is None:
            return None
        root_paths[agent_id] = path

    root = CTNode(
        cost=_total_cost(root_paths),
        id=_node_counter,
        constraints={a: set() for a in starts},
        edge_constraints={a: set() for a in starts},
        paths=root_paths,
    )

    open_set: list[CTNode] = []
    heapq.heappush(open_set, root)

    iterations = 0
    max_iterations = min(2000 * len(starts), 20000)

    while open_set and iterations < max_iterations:
        iterations += 1
        node = heapq.heappop(open_set)

        conflict = detect_first_conflict(node.paths)
        if conflict is None:
            return node.paths

        for agent in (conflict.agent_i, conflict.agent_j):
            _node_counter += 1
            new_constraints = {a: set(c) for a, c in node.constraints.items()}
            new_edge_constraints = {a: set(c) for a, c in node.edge_constraints.items()}

            if conflict.is_edge:
                if agent == conflict.agent_i:
                    new_edge_constraints[agent].add(
                        (*conflict.pos_i, *conflict.pos_j, conflict.timestep, conflict.timestep + 1)
                    )
                else:
                    new_edge_constraints[agent].add(
                        (*conflict.pos_j, *conflict.pos_i, conflict.timestep, conflict.timestep + 1)
                    )
            else:
                new_constraints[agent].add(
                    (conflict.position[0], conflict.position[1], conflict.timestep)
                )

            new_path = spacetime_astar(
                grid,
                starts[agent],
                goals[agent],
                constraints=new_constraints[agent],
                edge_constraints=new_edge_constraints[agent],
                max_time=max_time,
            )
            if new_path is None:
                continue

            new_paths = dict(node.paths)
            new_paths[agent] = new_path

            child = CTNode(
                cost=_total_cost(new_paths),
                id=_node_counter,
                constraints=new_constraints,
                edge_constraints=new_edge_constraints,
                paths=new_paths,
                conflicts_resolved=node.conflicts_resolved + 1,
            )
            heapq.heappush(open_set, child)

    return None


def prioritized_planning(
    grid: Grid,
    starts: Dict[int, Tuple[int, int]],
    goals: Dict[int, Tuple[int, int]],
    max_time: int = 200,
) -> Optional[Dict[int, List[Tuple[int, int]]]]:
    """Simple prioritized planning: plan agents one-by-one, treating
    earlier agents' paths as moving obstacles."""
    planned: Dict[int, List[Tuple[int, int]]] = {}
    for agent_id in sorted(starts.keys()):
        path = spacetime_astar(
            grid,
            starts[agent_id],
            goals[agent_id],
            max_time=max_time,
            other_paths=planned,
        )
        if path is None:
            return None
        planned[agent_id] = path
    return planned


def _plan_single_full_trip(
    grid: Grid,
    start: Tuple[int, int],
    pickup: Tuple[int, int],
    delivery: Tuple[int, int],
    constraints: Set[Constraint],
    edge_constraints: Set[EdgeConstraint],
    max_time: int,
) -> Optional[List[Tuple[int, int]]]:
    """Plan one agent's full trip (start->pickup->delivery) with CBS constraints."""
    pickup_path = spacetime_astar(
        grid, start, pickup,
        constraints=constraints,
        edge_constraints=edge_constraints,
        max_time=max_time,
    )
    if pickup_path is None:
        return None

    pickup_time = len(pickup_path) - 1

    delivery_path = spacetime_astar(
        grid, pickup, delivery,
        constraints=constraints,
        edge_constraints=edge_constraints,
        max_time=max_time,
        start_time=pickup_time,
    )
    if delivery_path is None:
        return None

    return pickup_path + delivery_path[1:]


def cbs_full_trip(
    grid: Grid,
    starts: Dict[int, Tuple[int, int]],
    pickups: Dict[int, Tuple[int, int]],
    deliveries: Dict[int, Tuple[int, int]],
    max_time: int = 300,
) -> Optional[Dict[int, List[Tuple[int, int]]]]:
    """CBS for full trips (start -> pickup -> delivery).

    Finds the optimal (minimum total cost) set of conflict-free full paths.
    Falls back to None if CBS exceeds iteration budget.
    """
    root_paths: Dict[int, List[Tuple[int, int]]] = {}
    for aid in starts:
        path = _plan_single_full_trip(
            grid, starts[aid], pickups[aid], deliveries[aid],
            set(), set(), max_time,
        )
        if path is None:
            return None
        root_paths[aid] = path

    root = CTNode(
        cost=_total_cost(root_paths),
        id=0,
        constraints={a: set() for a in starts},
        edge_constraints={a: set() for a in starts},
        paths=root_paths,
    )

    open_set: list[CTNode] = []
    heapq.heappush(open_set, root)

    iterations = 0
    max_iterations = min(3000 * len(starts), 30000)
    node_counter = 0

    while open_set and iterations < max_iterations:
        iterations += 1
        node = heapq.heappop(open_set)

        conflict = detect_first_conflict(node.paths)
        if conflict is None:
            node.conflicts_resolved = node.conflicts_resolved
            return node.paths

        for agent in (conflict.agent_i, conflict.agent_j):
            node_counter += 1
            new_constraints = {a: set(c) for a, c in node.constraints.items()}
            new_edge_constraints = {a: set(c) for a, c in node.edge_constraints.items()}

            if conflict.is_edge:
                if agent == conflict.agent_i:
                    new_edge_constraints[agent].add(
                        (*conflict.pos_i, *conflict.pos_j, conflict.timestep, conflict.timestep + 1)
                    )
                else:
                    new_edge_constraints[agent].add(
                        (*conflict.pos_j, *conflict.pos_i, conflict.timestep, conflict.timestep + 1)
                    )
            else:
                new_constraints[agent].add(
                    (conflict.position[0], conflict.position[1], conflict.timestep)
                )

            new_path = _plan_single_full_trip(
                grid, starts[agent], pickups[agent], deliveries[agent],
                new_constraints[agent], new_edge_constraints[agent], max_time,
            )
            if new_path is None:
                continue

            new_paths = dict(node.paths)
            new_paths[agent] = new_path

            child = CTNode(
                cost=_total_cost(new_paths),
                id=node_counter,
                constraints=new_constraints,
                edge_constraints=new_edge_constraints,
                paths=new_paths,
                conflicts_resolved=node.conflicts_resolved + 1,
            )
            heapq.heappush(open_set, child)

    return None


def prioritized_full_trip(
    grid: Grid,
    starts: Dict[int, Tuple[int, int]],
    pickups: Dict[int, Tuple[int, int]],
    deliveries: Dict[int, Tuple[int, int]],
    max_time: int = 300,
) -> Optional[Dict[int, List[Tuple[int, int]]]]:
    """Prioritized planning for the full trip: start -> pickup -> delivery.

    Plans each agent's complete path while avoiding all previously planned
    agents' full paths, ensuring no vertex or swap collisions.
    """
    planned: Dict[int, List[Tuple[int, int]]] = {}
    for agent_id in sorted(starts.keys()):
        occupied_at, edges_at, max_other_time = _build_occupied_map(planned, max_time)

        # Phase 1: start -> pickup
        pickup_path = spacetime_astar(
            grid,
            starts[agent_id],
            pickups[agent_id],
            max_time=max_time,
            occupied_at=occupied_at,
            edges_at=edges_at,
            max_other_time=max_other_time,
        )
        if pickup_path is None:
            return None

        pickup_arrival_time = len(pickup_path) - 1

        # Add pickup path edges+vertices to maps for phase 2
        for t, pos in enumerate(pickup_path):
            occupied_at.setdefault(t, set()).add(pos)
            if t + 1 < len(pickup_path):
                nxt = pickup_path[t + 1]
                if pos != nxt:
                    edges_at.setdefault(t, set()).add((pos[0], pos[1], nxt[0], nxt[1]))

        # Phase 2: pickup -> delivery (starting at pickup_arrival_time)
        delivery_path = spacetime_astar(
            grid,
            pickups[agent_id],
            deliveries[agent_id],
            max_time=max_time,
            start_time=pickup_arrival_time,
            occupied_at=occupied_at,
            edges_at=edges_at,
            max_other_time=max_other_time,
        )
        if delivery_path is None:
            return None

        full_path = pickup_path + delivery_path[1:]
        planned[agent_id] = full_path

    return planned
