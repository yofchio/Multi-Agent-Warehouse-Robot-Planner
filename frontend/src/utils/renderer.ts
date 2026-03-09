import { CellType, GridData } from "../types";

const CELL_COLORS: Record<number, string> = {
  [CellType.EMPTY]: "#1a1a2e",
  [CellType.SHELF]: "#e2a84b",
  [CellType.PICKUP]: "#4caf50",
  [CellType.DELIVERY]: "#42a5f5",
  [CellType.OBSTACLE]: "#37474f",
};

export function getCellSize(
  canvas: HTMLCanvasElement,
  grid: GridData
): number {
  const maxW = canvas.width / grid.width;
  const maxH = canvas.height / grid.height;
  return Math.floor(Math.min(maxW, maxH));
}

export function drawGrid(
  ctx: CanvasRenderingContext2D,
  grid: GridData,
  cellSize: number
) {
  for (let y = 0; y < grid.height; y++) {
    for (let x = 0; x < grid.width; x++) {
      const type = grid.cells[y][x];
      ctx.fillStyle = CELL_COLORS[type] ?? CELL_COLORS[CellType.EMPTY];
      ctx.fillRect(x * cellSize, y * cellSize, cellSize, cellSize);

      ctx.strokeStyle = "#0d0d1a";
      ctx.lineWidth = 1;
      ctx.strokeRect(x * cellSize, y * cellSize, cellSize, cellSize);

      if (type === CellType.SHELF) {
        ctx.fillStyle = "#c8922f";
        const inset = cellSize * 0.15;
        ctx.fillRect(
          x * cellSize + inset,
          y * cellSize + inset,
          cellSize - 2 * inset,
          cellSize - 2 * inset
        );
      }

      if (type === CellType.PICKUP) {
        ctx.fillStyle = "#ffffff33";
        ctx.beginPath();
        ctx.arc(
          x * cellSize + cellSize / 2,
          y * cellSize + cellSize / 2,
          cellSize * 0.3,
          0,
          Math.PI * 2
        );
        ctx.fill();
        ctx.fillStyle = "#fff";
        ctx.font = `${cellSize * 0.35}px sans-serif`;
        ctx.textAlign = "center";
        ctx.textBaseline = "middle";
        ctx.fillText("P", x * cellSize + cellSize / 2, y * cellSize + cellSize / 2);
      }

      if (type === CellType.DELIVERY) {
        ctx.fillStyle = "#ffffff33";
        ctx.beginPath();
        ctx.arc(
          x * cellSize + cellSize / 2,
          y * cellSize + cellSize / 2,
          cellSize * 0.3,
          0,
          Math.PI * 2
        );
        ctx.fill();
        ctx.fillStyle = "#fff";
        ctx.font = `${cellSize * 0.35}px sans-serif`;
        ctx.textAlign = "center";
        ctx.textBaseline = "middle";
        ctx.fillText("D", x * cellSize + cellSize / 2, y * cellSize + cellSize / 2);
      }
    }
  }
}

export interface AnimatedRobot {
  id: number;
  x: number;
  y: number;
  prevX: number;
  prevY: number;
  color: string;
  state: string;
  trail: { x: number; y: number; age: number }[];
}

export function drawRobots(
  ctx: CanvasRenderingContext2D,
  robots: AnimatedRobot[],
  cellSize: number,
  progress: number // 0-1 interpolation within timestep
) {
  for (const robot of robots) {
    // draw trail
    for (let i = 0; i < robot.trail.length; i++) {
      const t = robot.trail[i];
      const alpha = Math.max(0, 0.4 - t.age * 0.04);
      if (alpha <= 0) continue;
      ctx.fillStyle = robot.color + Math.round(alpha * 255).toString(16).padStart(2, "0");
      ctx.beginPath();
      ctx.arc(
        t.x * cellSize + cellSize / 2,
        t.y * cellSize + cellSize / 2,
        cellSize * 0.15,
        0,
        Math.PI * 2
      );
      ctx.fill();
    }

    // interpolated position
    const ix = robot.prevX + (robot.x - robot.prevX) * easeInOut(progress);
    const iy = robot.prevY + (robot.y - robot.prevY) * easeInOut(progress);

    const cx = ix * cellSize + cellSize / 2;
    const cy = iy * cellSize + cellSize / 2;
    const radius = cellSize * 0.35;

    // glow
    const glow = ctx.createRadialGradient(cx, cy, radius * 0.5, cx, cy, radius * 2);
    glow.addColorStop(0, robot.color + "40");
    glow.addColorStop(1, robot.color + "00");
    ctx.fillStyle = glow;
    ctx.beginPath();
    ctx.arc(cx, cy, radius * 2, 0, Math.PI * 2);
    ctx.fill();

    // body
    ctx.fillStyle = robot.color;
    ctx.beginPath();
    ctx.arc(cx, cy, radius, 0, Math.PI * 2);
    ctx.fill();

    // border
    ctx.strokeStyle = "#fff";
    ctx.lineWidth = 2;
    ctx.beginPath();
    ctx.arc(cx, cy, radius, 0, Math.PI * 2);
    ctx.stroke();

    // id label
    ctx.fillStyle = "#000";
    ctx.font = `bold ${cellSize * 0.3}px sans-serif`;
    ctx.textAlign = "center";
    ctx.textBaseline = "middle";
    ctx.fillText(String(robot.id), cx, cy);

    // carrying indicator
    if (robot.state === "moving_to_delivery") {
      ctx.fillStyle = "#ffeb3b";
      ctx.beginPath();
      ctx.arc(cx + radius * 0.6, cy - radius * 0.6, cellSize * 0.1, 0, Math.PI * 2);
      ctx.fill();
    }
  }
}

export function drawPaths(
  ctx: CanvasRenderingContext2D,
  paths: Record<string, [number, number][]>,
  robots: AnimatedRobot[],
  cellSize: number,
  currentFrame: number
) {
  const robotMap = new Map(robots.map((r) => [String(r.id), r]));
  for (const [rid, path] of Object.entries(paths)) {
    const robot = robotMap.get(rid);
    if (!robot) continue;
    const color = robot.color;

    ctx.strokeStyle = color + "60";
    ctx.lineWidth = 2;
    ctx.setLineDash([4, 4]);
    ctx.beginPath();
    for (let i = Math.max(0, currentFrame); i < path.length; i++) {
      const [px, py] = path[i];
      const sx = px * cellSize + cellSize / 2;
      const sy = py * cellSize + cellSize / 2;
      if (i === Math.max(0, currentFrame)) {
        ctx.moveTo(sx, sy);
      } else {
        ctx.lineTo(sx, sy);
      }
    }
    ctx.stroke();
    ctx.setLineDash([]);
  }
}

function easeInOut(t: number): number {
  return t < 0.5 ? 2 * t * t : -1 + (4 - 2 * t) * t;
}
