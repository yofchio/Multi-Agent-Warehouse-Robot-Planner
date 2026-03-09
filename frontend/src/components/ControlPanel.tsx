import type { ScenarioInfo } from "../types";

interface Props {
  scenarios: ScenarioInfo[];
  selectedScenario: string;
  selectedAlgorithm: string;
  isPlaying: boolean;
  speed: number;
  loading: boolean;
  finished: boolean;
  onScenarioChange: (s: string) => void;
  onAlgorithmChange: (a: string) => void;
  onSolve: () => void;
  onPlay: () => void;
  onPause: () => void;
  onStep: () => void;
  onReset: () => void;
  onSpeedChange: (s: number) => void;
}

export default function ControlPanel({
  scenarios,
  selectedScenario,
  selectedAlgorithm,
  isPlaying,
  speed,
  loading,
  finished,
  onScenarioChange,
  onAlgorithmChange,
  onSolve,
  onPlay,
  onPause,
  onStep,
  onReset,
  onSpeedChange,
}: Props) {
  return (
    <div className="control-panel">
      <h2>Control Panel</h2>

      <div className="control-group">
        <label>Scenario</label>
        <select
          value={selectedScenario}
          onChange={(e) => onScenarioChange(e.target.value)}
        >
          {scenarios.map((s) => (
            <option key={s.id} value={s.id}>
              {s.name} ({s.robotCount}R / {s.taskCount}T)
            </option>
          ))}
        </select>
      </div>

      <div className="control-group">
        <label>Algorithm</label>
        <select
          value={selectedAlgorithm}
          onChange={(e) => onAlgorithmChange(e.target.value)}
        >
          <option value="cbs">CBS (Conflict-Based Search)</option>
          <option value="prioritized">Prioritized Planning</option>
        </select>
      </div>

      <button className="btn btn-primary" onClick={onSolve} disabled={loading}>
        {loading ? "Solving..." : "Solve & Load"}
      </button>

      <div className="control-group playback">
        <button className="btn" onClick={onReset} title="Reset">
          ⏮
        </button>
        <button className="btn" onClick={onStep} title="Step">
          ⏭
        </button>
        {isPlaying ? (
          <button className="btn btn-warn" onClick={onPause} title="Pause">
            ⏸
          </button>
        ) : (
          <button
            className="btn btn-success"
            onClick={onPlay}
            disabled={finished}
            title="Play"
          >
            ▶
          </button>
        )}
      </div>

      <div className="control-group">
        <label>Speed: {speed.toFixed(1)}x</label>
        <input
          type="range"
          min="0.2"
          max="5"
          step="0.2"
          value={speed}
          onChange={(e) => onSpeedChange(parseFloat(e.target.value))}
        />
      </div>

      {finished && <div className="badge badge-done">All tasks completed!</div>}
    </div>
  );
}
