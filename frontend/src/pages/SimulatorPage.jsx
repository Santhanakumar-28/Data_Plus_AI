import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import {
  PlaySquare,
  AlertTriangle,
  RotateCcw,
  Zap,
  CheckCircle,
  Database,
  ArrowRight,
  Flame,
  Clock,
  Layers,
  ShieldAlert,
  Terminal
} from 'lucide-react';
import { apiService } from '../api/client';

export default function SimulatorPage() {
  const [loadingScenario, setLoadingScenario] = useState(null);
  const [resetting, setResetting] = useState(false);
  const [logs, setLogs] = useState([]);
  const [lastIncidentId, setLastIncidentId] = useState(null);
  const [showResetConfirm, setShowResetConfirm] = useState(false);

  const navigate = useNavigate();

  const addLog = (message, type = 'info') => {
    const time = new Date().toLocaleTimeString();
    setLogs((prev) => [{ time, message, type }, ...prev]);
  };

  const handleTrigger = async (scenario) => {
    try {
      setLoadingScenario(scenario);
      addLog(`Injecting failure scenario '${scenario}' directly into Exasol...`, 'info');
      
      const res = await apiService.triggerSimulation({ scenario });
      
      setLastIncidentId(res.generated_incident_id);
      addLog(`[OK] Scenario executed successfully! Generated Incident: ${res.generated_incident_id}`, 'success');
      addLog(`Affected pipeline: ${res.affected_pipeline}`, 'info');
      addLog(`Downstream blast radius: ${res.impacted_downstream_count} dependent systems affected`, 'warning');
      addLog(`Exasol tables updated: PIPELINE_RUNS, DATA_QUALITY, INCIDENTS, PREDICTION_RESULTS`, 'success');
    } catch (err) {
      addLog(`[ERROR] Failed to inject scenario: ${err.message}`, 'error');
    } finally {
      setLoadingScenario(null);
    }
  };

  const handleReset = async () => {
    try {
      setResetting(true);
      setShowResetConfirm(false);
      addLog('Resetting Exasol Personal database and executing deterministic reseed...', 'info');
      
      const res = await apiService.resetSimulation();
      
      addLog(`[OK] Exasol database reset complete! ${res.message}`, 'success');
      setLastIncidentId(null);
    } catch (err) {
      addLog(`[ERROR] Database reset failed: ${err.message}`, 'error');
    } finally {
      setResetting(false);
    }
  };

  return (
    <div className="space-y-6">
      {/* Header and Reset Action */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 p-5 bg-gradient-to-r from-slate-900 via-[#0d1424] to-cyan-950/40 border border-slate-800 rounded-xl">
        <div>
          <div className="flex items-center space-x-2">
            <h2 className="text-xl font-bold text-white tracking-tight">Interactive Demo Simulator</h2>
            <span className="px-2 py-0.5 rounded text-[11px] font-mono bg-cyan-950/60 text-cyan-400 border border-cyan-800/40">
              Live Exasol Injection
            </span>
          </div>
          <p className="text-xs text-slate-400 mt-1">
            Simulate realistic production failures and cascading pipeline disasters to demonstrate DataPulse AI to judges.
          </p>
        </div>

        <button
          onClick={() => setShowResetConfirm(true)}
          disabled={resetting}
          className="px-4 py-2 bg-slate-800 hover:bg-slate-700 text-slate-200 border border-slate-700 rounded-lg text-xs font-semibold transition flex items-center space-x-2 disabled:opacity-50"
        >
          <RotateCcw className={`w-3.5 h-3.5 ${resetting ? 'animate-spin text-cyan-400' : ''}`} />
          <span>{resetting ? 'Resetting Database...' : 'Reset Demo Database'}</span>
        </button>
      </div>

      {/* 3 Scenario Cards */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        {/* Scenario 1: Missing Data */}
        <div className="p-5 bg-[#0d1424] border border-slate-800 rounded-xl flex flex-col justify-between hover:border-slate-700 transition space-y-4">
          <div className="space-y-3">
            <div className="flex items-center justify-between">
              <span className="px-2 py-0.5 rounded text-[10px] font-bold bg-amber-950/60 text-amber-300 border border-amber-800">
                SCENARIO 1
              </span>
              <AlertTriangle className="w-4 h-4 text-amber-400" />
            </div>

            <h3 className="text-base font-bold text-white">Missing Data & Quality Drop</h3>
            <p className="text-xs text-slate-400 leading-relaxed">
              Injects sudden upstream source data corruption on <strong className="text-slate-200">Customer Order ETL</strong>. Data completeness drops to 68.5% with 8,420 unexpected null values in mandatory fields.
            </p>

            <div className="p-3 bg-slate-900/80 rounded-lg border border-slate-800 text-[11px] space-y-1 font-mono text-slate-400">
              <div>Target: <span className="text-cyan-400">PIPE_CUST_ORDER</span></div>
              <div>Severity: <span className="text-amber-400">HIGH</span></div>
              <div>Type: DATA_QUALITY_DEGRADATION</div>
            </div>
          </div>

          <button
            onClick={() => handleTrigger('MISSING_DATA')}
            disabled={loadingScenario !== null}
            className="w-full py-2.5 bg-gradient-to-r from-amber-600 to-amber-700 hover:from-amber-500 hover:to-amber-600 disabled:opacity-50 text-white font-semibold rounded-lg text-xs transition flex items-center justify-center space-x-2"
          >
            <Flame className="w-3.5 h-3.5" />
            <span>{loadingScenario === 'MISSING_DATA' ? 'Injecting...' : 'Trigger Missing Data'}</span>
          </button>
        </div>

        {/* Scenario 2: Pipeline Delay */}
        <div className="p-5 bg-[#0d1424] border border-slate-800 rounded-xl flex flex-col justify-between hover:border-slate-700 transition space-y-4">
          <div className="space-y-3">
            <div className="flex items-center justify-between">
              <span className="px-2 py-0.5 rounded text-[10px] font-bold bg-indigo-950/60 text-indigo-300 border border-indigo-800">
                SCENARIO 2
              </span>
              <Clock className="w-4 h-4 text-indigo-400" />
            </div>

            <h3 className="text-base font-bold text-white">Pipeline Execution Delay</h3>
            <p className="text-xs text-slate-400 leading-relaxed">
              Simulates severe database lock contention and CPU throttling (94.8%) on <strong className="text-slate-200">Inventory Synchronization</strong>. Runtime surges to 780s causing SLA breach.
            </p>

            <div className="p-3 bg-slate-900/80 rounded-lg border border-slate-800 text-[11px] space-y-1 font-mono text-slate-400">
              <div>Target: <span className="text-cyan-400">PIPE_INV_SYNC</span></div>
              <div>Severity: <span className="text-indigo-400">MEDIUM</span></div>
              <div>Type: EXECUTION_DELAY</div>
            </div>
          </div>

          <button
            onClick={() => handleTrigger('PIPELINE_DELAY')}
            disabled={loadingScenario !== null}
            className="w-full py-2.5 bg-gradient-to-r from-indigo-600 to-indigo-700 hover:from-indigo-500 hover:to-indigo-600 disabled:opacity-50 text-white font-semibold rounded-lg text-xs transition flex items-center justify-center space-x-2"
          >
            <Zap className="w-3.5 h-3.5" />
            <span>{loadingScenario === 'PIPELINE_DELAY' ? 'Injecting...' : 'Trigger Runtime Surge'}</span>
          </button>
        </div>

        {/* Scenario 3: Upstream Failure */}
        <div className="p-5 bg-[#0d1424] border border-slate-800 rounded-xl flex flex-col justify-between hover:border-slate-700 transition space-y-4">
          <div className="space-y-3">
            <div className="flex items-center justify-between">
              <span className="px-2 py-0.5 rounded text-[10px] font-bold bg-rose-950/60 text-rose-300 border border-rose-800">
                SCENARIO 3
              </span>
              <ShieldAlert className="w-4 h-4 text-rose-400" />
            </div>

            <h3 className="text-base font-bold text-white">Cascading Upstream Failure</h3>
            <p className="text-xs text-slate-400 leading-relaxed">
              Injects 18 fatal schema conversion mismatches in the root producer <strong className="text-slate-200">Customer Master Data</strong>. Triggers cascading blockage across downstream pipelines and BI portals.
            </p>

            <div className="p-3 bg-slate-900/80 rounded-lg border border-slate-800 text-[11px] space-y-1 font-mono text-slate-400">
              <div>Target: <span className="text-cyan-400">PIPE_CUST_MASTER</span></div>
              <div>Severity: <span className="text-rose-400">CRITICAL</span></div>
              <div>Type: SCHEMA_MISMATCH</div>
            </div>
          </div>

          <button
            onClick={() => handleTrigger('UPSTREAM_FAILURE')}
            disabled={loadingScenario !== null}
            className="w-full py-2.5 bg-gradient-to-r from-rose-600 to-rose-700 hover:from-rose-500 hover:to-rose-600 disabled:opacity-50 text-white font-semibold rounded-lg text-xs transition flex items-center justify-center space-x-2"
          >
            <ShieldAlert className="w-3.5 h-3.5" />
            <span>{loadingScenario === 'UPSTREAM_FAILURE' ? 'Injecting...' : 'Trigger Cascading Crash'}</span>
          </button>
        </div>
      </div>

      {/* Live Simulation Execution Console */}
      <div className="p-5 bg-[#0d1424] border border-slate-800 rounded-xl space-y-3">
        <div className="flex items-center justify-between">
          <div className="flex items-center space-x-2 text-cyan-400 text-xs font-semibold">
            <Terminal className="w-4 h-4" />
            <h3 className="text-white">Live Exasol Simulation Event Log</h3>
          </div>
          {lastIncidentId && (
            <button
              onClick={() => navigate(`/investigation?incident_id=${lastIncidentId}`)}
              className="px-3 py-1 bg-cyan-950 hover:bg-cyan-900 text-cyan-300 border border-cyan-800 rounded text-xs font-medium transition flex items-center space-x-1"
            >
              <span>Investigate Injected Incident ({lastIncidentId})</span>
              <ArrowRight className="w-3 h-3" />
            </button>
          )}
        </div>

        <div className="bg-slate-950 p-4 rounded-lg border border-slate-800 font-mono text-xs max-h-56 overflow-y-auto space-y-1.5">
          {logs.length === 0 ? (
            <div className="text-slate-600 italic">
              Ready. Click any simulation card above to inject an operational event into Exasol.
            </div>
          ) : (
            logs.map((log, idx) => (
              <div
                key={idx}
                className={`flex items-start space-x-2 ${
                  log.type === 'error'
                    ? 'text-rose-400'
                    : log.type === 'success'
                    ? 'text-emerald-400'
                    : log.type === 'warning'
                    ? 'text-amber-300'
                    : 'text-slate-300'
                }`}
              >
                <span className="text-slate-600 text-[10px] flex-shrink-0">[{log.time}]</span>
                <span>{log.message}</span>
              </div>
            ))
          )}
        </div>
      </div>

      {/* Confirmation Modal for Reset Demo */}
      {showResetConfirm && (
        <div className="fixed inset-0 z-50 bg-black/60 backdrop-blur-sm flex items-center justify-center p-4">
          <div className="bg-[#0d1424] border border-slate-800 rounded-xl max-w-sm w-full p-6 shadow-2xl space-y-4">
            <div className="flex items-center space-x-3 text-amber-400">
              <AlertTriangle className="w-6 h-6" />
              <h3 className="text-base font-bold text-white">Reset Demo Database?</h3>
            </div>
            <p className="text-xs text-slate-300 leading-relaxed">
              This will re-run the database initialization and deterministic synthetic data generator, restoring all 7 Exasol tables in schema <code className="text-cyan-400 font-mono">DATAPULSE</code> back to clean baseline state.
            </p>
            <div className="pt-2 flex justify-end space-x-2">
              <button
                onClick={() => setShowResetConfirm(false)}
                className="px-3 py-1.5 bg-slate-800 text-slate-300 rounded-lg text-xs hover:bg-slate-700 transition"
              >
                Cancel
              </button>
              <button
                onClick={handleReset}
                className="px-4 py-1.5 bg-rose-600 hover:bg-rose-500 text-white font-medium rounded-lg text-xs transition"
              >
                Confirm Reset & Reseed
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
