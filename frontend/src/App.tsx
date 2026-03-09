import { useCallback, useEffect, useState } from "react";
import ControlPanel from "./components/ControlPanel";
import StatsPanel from "./components/StatsPanel";
import WarehouseCanvas from "./components/WarehouseCanvas";
import { useSimulation } from "./hooks/useSimulation";
import "./App.css";

function App() {
  const {
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
  } = useSimulation();

  const [selectedScenario, setSelectedScenario] = useState("simple");
  const [selectedAlgorithm, setSelectedAlgorithm] = useState("cbs");

  useEffect(() => {
    fetchScenarios();
  }, [fetchScenarios]);

  const handleSolve = useCallback(() => {
    solve(selectedScenario, selectedAlgorithm);
  }, [solve, selectedScenario, selectedAlgorithm]);

  return (
    <div className="app">
      <header className="app-header">
        <h1>Multi-Agent Warehouse Robot Planner</h1>
        <p className="subtitle">
          AI Planning & Scheduling Demo — CBS / Prioritized MAPF
        </p>
      </header>

      <main className="app-main">
        <StatsPanel
          stats={stats}
          robots={robots}
          currentFrame={currentFrame}
          plan={plan}
        />

        <div className="main-row">
          <aside className="sidebar">
            <ControlPanel
              scenarios={scenarios}
              selectedScenario={selectedScenario}
              selectedAlgorithm={selectedAlgorithm}
              isPlaying={isPlaying}
              speed={speed}
              loading={loading}
              finished={finished}
              onScenarioChange={setSelectedScenario}
              onAlgorithmChange={setSelectedAlgorithm}
              onSolve={handleSolve}
              onPlay={play}
              onPause={pause}
              onStep={stepForward}
              onReset={reset}
              onSpeedChange={updateSpeed}
            />
          </aside>

          <div className="canvas-area">
            {grid ? (
              <WarehouseCanvas
                grid={grid}
                plan={plan}
                robotsRef={robotsRef}
                progressRef={progressRef}
                frameRef={frameRef}
              />
            ) : (
              <div className="placeholder">
                <p>
                  Select a scenario and click <strong>Solve & Load</strong> to
                  begin
                </p>
              </div>
            )}
          </div>
        </div>
      </main>
    </div>
  );
}

export default App;
