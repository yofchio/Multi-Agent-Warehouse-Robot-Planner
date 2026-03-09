import { useCallback, useRef, useState } from "react";
import type {
  GridData,
  PlanData,
  RobotData,
  ScenarioInfo,
  Stats,
  TaskData,
} from "../types";
import type { AnimatedRobot } from "../utils/renderer";

const API_BASE = "http://localhost:8000/api";

export function useSimulation() {
  const [grid, setGrid] = useState<GridData | null>(null);
  const [robots, setRobots] = useState<AnimatedRobot[]>([]);
  const [tasks, setTasks] = useState<Record<string, TaskData>>({});
  const [stats, setStats] = useState<Stats>({
    totalTasks: 0,
    completedTasks: 0,
    totalMoves: 0,
    conflictsResolved: 0,
    makespan: 0,
    totalCost: 0,
    algorithm: "",
  });
  const [plan, setPlan] = useState<PlanData | null>(null);
  const [scenarios, setScenarios] = useState<ScenarioInfo[]>([]);
  const [isPlaying, setIsPlaying] = useState(false);
  const [currentFrame, setCurrentFrame] = useState(0);
  const [speed, setSpeed] = useState(1);
  const [finished, setFinished] = useState(false);
  const [loading, setLoading] = useState(false);

  const animFrameRef = useRef<number>(0);
  const lastTimeRef = useRef<number>(0);
  const progressRef = useRef<number>(0);
  const frameRef = useRef<number>(0);
  const robotsRef = useRef<AnimatedRobot[]>([]);
  const planRef = useRef<PlanData | null>(null);
  const isPlayingRef = useRef(false);
  const speedRef = useRef(1);

  const fetchScenarios = useCallback(async () => {
    const res = await fetch(`${API_BASE}/scenarios`);
    const data = await res.json();
    setScenarios(data);
  }, []);

  const solve = useCallback(
    async (scenario: string, algorithm: string) => {
      setLoading(true);
      setFinished(false);
      setCurrentFrame(0);
      frameRef.current = 0;
      progressRef.current = 0;

      try {
        const res = await fetch(`${API_BASE}/solve`, {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ scenario, algorithm }),
        });
        const data = await res.json();

        console.log("Solve response:", data);
        console.log("Grid data:", data.grid);

        setGrid(data.grid);
        setTasks(data.tasks);
        setStats(data.stats);
        setPlan(data.plan);
        planRef.current = data.plan;

        const initialRobots: AnimatedRobot[] = Object.values(
          data.robots as Record<string, RobotData>
        ).map((r) => ({
          id: r.id,
          x: r.x,
          y: r.y,
          prevX: r.x,
          prevY: r.y,
          color: r.color,
          state: r.state,
          trail: [],
        }));
        setRobots(initialRobots);
        robotsRef.current = initialRobots;
        setLoading(false);
      } catch (error) {
        console.error("Error solving:", error);
        setLoading(false);
      }
    },
    []
  );

  const animate = useCallback((timestamp: number) => {
    if (!isPlayingRef.current) return;

    const plan = planRef.current;
    if (!plan || plan.totalFrames === 0) return;

    if (lastTimeRef.current === 0) lastTimeRef.current = timestamp;
    const delta = timestamp - lastTimeRef.current;
    lastTimeRef.current = timestamp;

    const stepDurationMs = 400 / speedRef.current;
    progressRef.current += delta / stepDurationMs;

    if (progressRef.current >= 1) {
      progressRef.current = 0;
      frameRef.current++;

      if (frameRef.current >= plan.totalFrames) {
        // Finalize robots at their last-frame positions so interpolation
        // doesn't snap them back when progress resets to 0.
        const finalRobots = robotsRef.current.map((r) => ({
          ...r,
          prevX: r.x,
          prevY: r.y,
        }));
        robotsRef.current = finalRobots;
        setRobots(finalRobots);
        progressRef.current = 1;
        setFinished(true);
        setIsPlaying(false);
        isPlayingRef.current = false;
        return;
      }

      setCurrentFrame(frameRef.current);

      const frame = plan.frames[frameRef.current];
      if (frame) {
        const updated = robotsRef.current.map((r) => {
          const fd = frame[String(r.id)];
          if (!fd) return r;
          const newTrail = [
            { x: r.x, y: r.y, age: 0 },
            ...r.trail.map((t) => ({ ...t, age: t.age + 1 })),
          ].slice(0, 12);
          return {
            ...r,
            prevX: r.x,
            prevY: r.y,
            x: fd.x,
            y: fd.y,
            state: fd.state,
            trail: newTrail,
          };
        });
        robotsRef.current = updated;
        setRobots(updated);
        setStats((prev) => ({
          ...prev,
          makespan: frameRef.current,
          completedTasks: Object.values(plan.frames[frameRef.current] || {}).filter(
            (r) => r.state === "idle"
          ).length,
        }));
      }
    }

    animFrameRef.current = requestAnimationFrame(animate);
  }, []);

  const play = useCallback(() => {
    if (finished) return;
    setIsPlaying(true);
    isPlayingRef.current = true;
    lastTimeRef.current = 0;
    animFrameRef.current = requestAnimationFrame(animate);
  }, [animate, finished]);

  const pause = useCallback(() => {
    setIsPlaying(false);
    isPlayingRef.current = false;
    cancelAnimationFrame(animFrameRef.current);
  }, []);

  const stepForward = useCallback(() => {
    const plan = planRef.current;
    if (!plan || frameRef.current >= plan.totalFrames - 1) return;

    frameRef.current++;
    setCurrentFrame(frameRef.current);
    progressRef.current = 1;

    const frame = plan.frames[frameRef.current];
    if (frame) {
      const updated = robotsRef.current.map((r) => {
        const fd = frame[String(r.id)];
        if (!fd) return r;
        return {
          ...r,
          prevX: fd.x,
          prevY: fd.y,
          x: fd.x,
          y: fd.y,
          state: fd.state,
          trail: [
            { x: r.x, y: r.y, age: 0 },
            ...r.trail.map((t) => ({ ...t, age: t.age + 1 })),
          ].slice(0, 12),
        };
      });
      robotsRef.current = updated;
      setRobots(updated);
    }
  }, []);

  const reset = useCallback(() => {
    pause();
    frameRef.current = 0;
    progressRef.current = 0;
    setCurrentFrame(0);
    setFinished(false);

    const plan = planRef.current;
    if (plan && plan.frames.length > 0) {
      const frame = plan.frames[0];
      const updated = robotsRef.current.map((r) => {
        const fd = frame[String(r.id)];
        if (!fd) return r;
        return {
          ...r,
          prevX: fd.x,
          prevY: fd.y,
          x: fd.x,
          y: fd.y,
          state: fd.state,
          trail: [],
        };
      });
      robotsRef.current = updated;
      setRobots(updated);
    }
  }, [pause]);

  const updateSpeed = useCallback((s: number) => {
    setSpeed(s);
    speedRef.current = s;
  }, []);

  return {
    grid,
    robots,
    tasks,
    stats,
    plan,
    scenarios,
    isPlaying,
    currentFrame,
    speed,
    finished,
    loading,
    progressRef,
    robotsRef,
    frameRef,
    fetchScenarios,
    solve,
    play,
    pause,
    stepForward,
    reset,
    updateSpeed,
  };
}
