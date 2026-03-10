# Multi-Agent Warehouse Robot Planner


https://multi-agent-warehouse-robot-planner.onrender.com/

An interactive visualization demo for **AI Planning & Scheduling**, built for an academic workshop presentation at Northeastern University.

Watch multiple robots coordinate in a simulated warehouse — picking up items, navigating around shelves, avoiding collisions through narrow corridors, and delivering to stations — all powered by real MAPF (Multi-Agent Path Finding) algorithms.

![Python](https://img.shields.io/badge/Python-FastAPI-009688?logo=python&logoColor=white)
![React](https://img.shields.io/badge/React-TypeScript-61DAFB?logo=react&logoColor=white)
![License](https://img.shields.io/badge/License-MIT-blue)

---

## Features

- **Two MAPF Algorithms** — CBS (Conflict-Based Search) for optimal solutions vs. Prioritized Planning for fast heuristic solutions, with live comparison of cost and makespan
- **4 Preset Scenarios** — Simple (3 robots), Medium (6 robots), Bottleneck (narrow corridor), Large (10 robots)
- **Full-Trip Coordination** — Robots are coordinated across the entire trip (start → pickup → delivery), not just one phase
- **Conflict Detection** — Both vertex conflicts (same cell, same time) and edge/swap conflicts (robots passing through each other)
- **Smooth Canvas Animation** — 60fps interpolated robot movement with glowing trail effects, path preview, and color-coded status
- **Interactive Controls** — Play / Pause / Step / Reset, adjustable speed (0.2x–5x), real-time statistics

---

## Architecture

```
┌─────────────────────────┐         ┌──────────────────────────────┐
│    React Frontend       │  HTTP   │      Python Backend          │
│                         │  POST   │                              │
│  WarehouseCanvas (60fps)│◄───────►│  FastAPI + Uvicorn           │
│  ControlPanel           │         │                              │
│  StatsPanel             │         │  ┌────────────────────────┐  │
│                         │         │  │ Algorithms             │  │
│  Canvas rendering with  │         │  │  ├─ A*                 │  │
│  interpolation & trails │         │  │  ├─ Space-Time A*      │  │
│                         │         │  │  ├─ CBS (optimal MAPF) │  │
│                         │         │  │  └─ Prioritized MAPF   │  │
│                         │         │  ├────────────────────────┤  │
│                         │         │  │ Simulation Engine      │  │
│                         │         │  │  ├─ Task Assignment    │  │
│                         │         │  │  ├─ Full-trip planning │  │
│                         │         │  │  └─ Conflict counting  │  │
│                         │         │  └────────────────────────┘  │
└─────────────────────────┘         └──────────────────────────────┘
```

---

## Algorithms

### A* / Space-Time A*

Standard A* finds shortest paths on the 2D grid. Space-Time A* extends this to 3D `(x, y, t)` — each node represents being at position `(x, y)` at time `t`, with a fifth action: **WAIT**. This unifies path planning and temporal coordination into a single search.

### CBS (Conflict-Based Search)

An optimal MAPF algorithm that finds the minimum total cost solution:

1. Plan each robot independently (ignoring others)
2. Detect conflicts between all paths
3. Branch: constrain agent A *or* agent B to avoid the conflict location/time
4. Re-plan the constrained agent, repeat until conflict-free

### Prioritized Planning

A fast but suboptimal approach:

1. Order robots by priority (ID)
2. Plan Robot 0 with no constraints
3. Plan Robot 1, treating Robot 0's path as a moving obstacle
4. Continue for all robots...

### Comparison (from actual demo runs)

| Scenario | CBS Frames | CBS Cost | Prioritized Frames | Prioritized Cost |
|---|:---:|:---:|:---:|:---:|
| Simple (3R) | 20 | 51 | 20 | 55 |
| Medium (6R) | **21** | **115** | 24 | 127 |
| Bottleneck (4R) | 37 | 106 | 37 | 106 |
| Large (10R) | **28** | **232** | 30 | 268 |

CBS consistently finds lower-cost solutions, especially with more agents.

---

## Quick Start

### Prerequisites

- Python 3.10+
- Node.js 18+

### Backend

```bash
cd backend
pip install -r requirements.txt
cd ..
python -m backend.main
```

The API server starts at `http://localhost:8000`.

### Frontend

```bash
cd frontend
npm install
npm run dev
```

Open `http://localhost:5173` in your browser.

---

## Project Structure

```
├── backend/
│   ├── main.py                     # FastAPI entry point
│   ├── requirements.txt
│   ├── algorithms/
│   │   ├── astar.py                # A* and Space-Time A*
│   │   ├── cbs.py                  # CBS, Prioritized, full-trip planning
│   │   └── task_assignment.py      # Greedy task allocation
│   ├── models/
│   │   ├── grid.py                 # Warehouse grid with cell types
│   │   ├── robot.py                # Robot state model
│   │   └── task.py                 # Task (pickup → delivery) model
│   ├── simulation/
│   │   ├── engine.py               # Simulation orchestrator
│   │   └── scenarios.py            # 4 preset warehouse layouts
│   └── api/
│       └── routes.py               # REST API + WebSocket endpoints
├── frontend/
│   ├── src/
│   │   ├── App.tsx                 # Main layout
│   │   ├── App.css                 # Dark theme styles
│   │   ├── components/
│   │   │   ├── WarehouseCanvas.tsx  # Canvas rendering (60fps)
│   │   │   ├── ControlPanel.tsx     # Scenario/algorithm/playback controls
│   │   │   └── StatsPanel.tsx       # Live statistics bar
│   │   ├── hooks/
│   │   │   └── useSimulation.ts     # Animation state management
│   │   ├── utils/
│   │   │   └── renderer.ts          # Grid/robot/path drawing
│   │   └── types/
│   │       └── index.ts             # TypeScript interfaces
│   └── index.html
├── presentation-guide.html          # Workshop presentation guide
└── README.md
```

---

## Scenarios

### Simple (3 robots, 3 tasks)
A small 12×10 warehouse for introducing basic concepts — A* pathfinding, task assignment, and single-agent planning.

### Medium (6 robots, 8 tasks)
A 16×12 warehouse with 6 robots and 12 shelf blocks. Demonstrates multi-agent coordination where CBS and Prioritized Planning produce visibly different results.

### Bottleneck (4 robots, narrow corridor)
A 14×10 warehouse split by a wall with a 2-cell-wide gap. Robots must cross in both directions, forcing wait/detour strategies. Showcases edge conflict (swap) detection.

### Large (10 robots, 15 tasks)
A 20×14 warehouse with 20 shelf blocks. Demonstrates scalability and the visual impact of 10 coordinated robots.

---

## AI Planning & Scheduling Concepts

This demo illustrates the relationship between two core AI subfields:

| | Planning | Scheduling |
|---|---|---|
| **Question** | *What* actions to take | *When* and *where* to execute |
| **In this demo** | A* pathfinding, task assignment | Space-Time A*, CBS, conflict resolution |
| **Key challenge** | Large state space | Resource conflicts, temporal coordination |
| **Integration** | Space-Time A* unifies both into a single search in (x, y, t) space |

---

## Tech Stack

**Backend:** Python, FastAPI, NumPy

**Frontend:** React 19, TypeScript, Vite, HTML5 Canvas

---

## License

[MIT](LICENSE)
