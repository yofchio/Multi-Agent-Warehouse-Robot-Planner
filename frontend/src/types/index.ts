export enum CellType {
  EMPTY = 0,
  SHELF = 1,
  PICKUP = 2,
  DELIVERY = 3,
  OBSTACLE = 4,
}

export interface GridData {
  width: number;
  height: number;
  cells: number[][];
}

export interface RobotData {
  id: number;
  x: number;
  y: number;
  color: string;
  state: string;
  currentTaskId: number | null;
  path: [number, number][];
  pathIndex: number;
  tasksCompleted: number;
}

export interface TaskData {
  id: number;
  pickup: [number, number];
  delivery: [number, number];
  status: string;
  assignedRobotId: number | null;
}

export interface Stats {
  totalTasks: number;
  completedTasks: number;
  totalMoves: number;
  conflictsResolved: number;
  makespan: number;
  totalCost: number;
  algorithm: string;
}

export interface FrameRobot {
  x: number;
  y: number;
  color: string;
  state: string;
}

export interface PlanData {
  frames: Record<string, FrameRobot>[];
  paths: Record<string, [number, number][]>;
  totalFrames: number;
}

export interface ScenarioInfo {
  id: string;
  name: string;
  robotCount: number;
  taskCount: number;
  gridWidth: number;
  gridHeight: number;
}

export interface SimulationState {
  grid: GridData | null;
  robots: Record<string, RobotData>;
  tasks: Record<string, TaskData>;
  stats: Stats;
  plan: PlanData | null;
  finished: boolean;
}
