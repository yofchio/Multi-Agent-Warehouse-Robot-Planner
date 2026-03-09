import { useEffect, useRef } from "react";
import type { GridData, PlanData } from "../types";
import type { AnimatedRobot } from "../utils/renderer";
import { drawGrid, drawPaths, drawRobots, getCellSize } from "../utils/renderer";

interface Props {
  grid: GridData | null;
  plan: PlanData | null;
  robotsRef: React.RefObject<AnimatedRobot[]>;
  progressRef: React.RefObject<number>;
  frameRef: React.RefObject<number>;
}

export default function WarehouseCanvas({
  grid,
  plan,
  robotsRef,
  progressRef,
  frameRef,
}: Props) {
  const canvasRef = useRef<HTMLCanvasElement>(null);
  const rafRef = useRef<number>(0);
  const gridRef = useRef(grid);
  const planRef = useRef(plan);
  gridRef.current = grid;
  planRef.current = plan;

  useEffect(() => {
    const canvas = canvasRef.current;
    const g = gridRef.current;
    if (!canvas || !g) return;

    const ctx = canvas.getContext("2d");
    if (!ctx) return;

    const dpr = window.devicePixelRatio || 1;
    const cellSize = getCellSize(canvas, g);
    const drawW = g.width * cellSize;
    const drawH = g.height * cellSize;

    canvas.width = drawW * dpr;
    canvas.height = drawH * dpr;
    canvas.style.width = `${drawW}px`;
    canvas.style.height = `${drawH}px`;
    ctx.scale(dpr, dpr);

    function render() {
      const currentGrid = gridRef.current;
      const currentRobots = robotsRef.current ?? [];
      const currentPlan = planRef.current;
      const progress = progressRef.current ?? 0;
      const frame = frameRef.current ?? 0;

      if (!ctx || !currentGrid) return;
      ctx.clearRect(0, 0, drawW, drawH);

      drawGrid(ctx, currentGrid, cellSize);

      if (currentPlan?.paths) {
        drawPaths(ctx, currentPlan.paths, currentRobots, cellSize, frame);
      }

      drawRobots(ctx, currentRobots, cellSize, progress);

      rafRef.current = requestAnimationFrame(render);
    }

    rafRef.current = requestAnimationFrame(render);
    return () => cancelAnimationFrame(rafRef.current);
  }, [grid, plan, robotsRef, progressRef, frameRef]);

  return (
    <canvas
      ref={canvasRef}
      style={{
        background: "#0d0d1a",
        borderRadius: 12,
        boxShadow: "0 0 40px rgba(79, 195, 247, 0.15)",
        maxWidth: "100%",
      }}
      width={900}
      height={650}
    />
  );
}
