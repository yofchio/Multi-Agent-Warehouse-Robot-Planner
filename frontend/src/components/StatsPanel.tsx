import type { PlanData, Stats } from "../types";
import type { AnimatedRobot } from "../utils/renderer";

interface Props {
  stats: Stats;
  robots: AnimatedRobot[];
  currentFrame: number;
  plan: PlanData | null;
}

export default function StatsPanel({ stats, robots, currentFrame, plan }: Props) {
  return (
    <div className="stats-panel">
      <div className="stats-top">
        <div className="stat-card">
          <span className="stat-label">Time Step</span>
          <span className="stat-value">
            {plan ? currentFrame + 1 : 0} / {plan?.totalFrames ?? 0}
          </span>
        </div>

        <div className="stat-card">
          <span className="stat-label">Tasks</span>
          <span className="stat-value">
            {stats.completedTasks} / {stats.totalTasks}
          </span>
        </div>

        <div className="stat-card">
          <span className="stat-label">Total Cost</span>
          <span className="stat-value">{stats.totalCost || 0}</span>
        </div>

        <div className="stat-card">
          <span className="stat-label">Conflicts Resolved</span>
          <span className="stat-value">{stats.conflictsResolved}</span>
        </div>

        {stats.algorithm && (
          <div className="stat-card">
            <span className="stat-label">Algorithm</span>
            <span className="stat-value stat-algo">
              {stats.algorithm === "cbs" ? "CBS" : "Prioritized"}
            </span>
          </div>
        )}

        <div className="stat-divider" />

        <div className="robot-list">
          {robots.map((r) => (
            <div key={r.id} className="robot-status">
              <span
                className="robot-dot"
                style={{ backgroundColor: r.color }}
              />
              <span className="robot-label">{r.id}</span>
              <span className={`robot-state state-${r.state}`}>
                {formatState(r.state)}
              </span>
            </div>
          ))}
        </div>

        <div className="stat-divider" />

        <div className="legend">
          <div className="legend-item">
            <span className="legend-color" style={{ backgroundColor: "#e2a84b" }} />
            Shelf
          </div>
          <div className="legend-item">
            <span className="legend-color" style={{ backgroundColor: "#4caf50" }} />
            Pickup (P)
          </div>
          <div className="legend-item">
            <span className="legend-color" style={{ backgroundColor: "#42a5f5" }} />
            Delivery (D)
          </div>
          <div className="legend-item">
            <span className="legend-color" style={{ backgroundColor: "#37474f" }} />
            Obstacle
          </div>
        </div>
      </div>
    </div>
  );
}

function formatState(state: string): string {
  switch (state) {
    case "idle":
      return "Idle";
    case "moving_to_pickup":
      return "To Pickup";
    case "moving_to_delivery":
      return "Carrying";
    case "picking":
      return "Picking";
    case "delivering":
      return "Delivering";
    default:
      return state;
  }
}
