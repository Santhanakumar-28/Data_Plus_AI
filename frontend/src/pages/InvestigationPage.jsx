import React, { useState, useEffect } from 'react';
import { useSearchParams, useNavigate } from 'react-router-dom';
import {
  Search,
  AlertOctagon,
  CheckCircle2,
  Clock,
  ArrowRight,
  ShieldAlert,
  GitFork,
  FileText,
  Activity,
  Layers,
  Sparkles,
  Check,
  RotateCcw,
  RefreshCw,
  AlertTriangle
} from 'lucide-react';
import { apiService } from '../api/client';

export default function InvestigationPage() {
  const [searchParams] = useSearchParams();
  const navigate = useNavigate();

  const [incidents, setIncidents] = useState([]);
  const [selectedIncidentId, setSelectedIncidentId] = useState('');
  const [report, setReport] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [updatingStatus, setUpdatingStatus] = useState(false);
  const [resolutionNotes, setResolutionNotes] = useState('');

  const loadIncidents = async () => {
    try {
      setError(null);
      const list = await apiService.getIncidents({ limit: 50 });
      setIncidents(list || []);

      const urlIncidentId = searchParams.get('incident_id');
      const urlPipelineId = searchParams.get('pipeline_id');

      let targetId = null;
      if (urlIncidentId) {
        targetId = urlIncidentId;
      } else if (urlPipelineId && list && list.length > 0) {
        const match = list.find((i) => i.pipeline_id === urlPipelineId);
        targetId = match ? match.incident_id : list[0].incident_id;
      } else if (list && list.length > 0) {
        targetId = list[0].incident_id;
      }

      if (targetId) {
        setSelectedIncidentId(targetId);
        fetchInvestigation(targetId);
      }
    } catch (err) {
      console.error('Failed to load incidents list:', err);
      setError('Failed to retrieve incidents from Exasol database. Please verify backend status.');
    }
  };

  useEffect(() => {
    loadIncidents();
  }, [searchParams]);

  const fetchInvestigation = async (id) => {
    if (!id) return;
    try {
      setLoading(true);
      setError(null);
      const data = await apiService.investigateIncident(id);
      setReport(data);
    } catch (err) {
      console.error('Investigation failed:', err);
      setError(`Failed to load investigation report for incident ${id}: ${err.message || 'Server error'}`);
    } finally {
      setLoading(false);
    }
  };

  const handleStatusUpdate = async (newStatus) => {
    if (!selectedIncidentId) return;
    try {
      setUpdatingStatus(true);
      await apiService.updateIncidentStatus(selectedIncidentId, {
        resolution_status: newStatus,
        actor: 'LeadDataEngineer',
        notes: resolutionNotes || `Updated incident status to ${newStatus} via AI Console`
      });
      // Refresh investigation
      await fetchInvestigation(selectedIncidentId);
      // Refresh list
      const updatedList = await apiService.getIncidents({ limit: 50 });
      setIncidents(updatedList || []);
      setResolutionNotes('');
    } catch (err) {
      console.error('Failed to update incident:', err);
    } finally {
      setUpdatingStatus(false);
    }
  };

  return (
    <div className="space-y-6">
      {/* Header and Incident Selector */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 p-5 bg-gradient-to-r from-slate-900 via-[#0d1424] to-cyan-950/40 border border-slate-800 rounded-xl">
        <div>
          <div className="flex items-center space-x-2">
            <h2 className="text-xl font-bold text-white tracking-tight">AI Root Cause Analysis (RCA)</h2>
            <span className="px-2 py-0.5 rounded text-[11px] font-mono bg-indigo-950/60 text-indigo-300 border border-indigo-800/40 flex items-center space-x-1">
              <Sparkles className="w-3 h-3 text-cyan-400" />
              <span>Evidence Synthesizer</span>
            </span>
          </div>
          <p className="text-xs text-slate-400 mt-1">
            Correlates live Exasol execution telemetry with historical 14-day baselines and upstream dependencies.
          </p>
        </div>

        {/* Incident Dropdown & Actions */}
        <div className="flex items-center space-x-3">
          <label className="text-xs text-slate-400">Target Incident:</label>
          <select
            value={selectedIncidentId}
            onChange={(e) => {
              setSelectedIncidentId(e.target.value);
              fetchInvestigation(e.target.value);
            }}
            disabled={incidents.length === 0}
            className="px-3 py-1.5 bg-slate-900 border border-slate-700 rounded-lg text-xs text-white focus:outline-none focus:border-cyan-500 font-mono max-w-[280px] sm:max-w-[360px] truncate"
          >
            {incidents.length === 0 ? (
              <option value="">No incidents found in Exasol</option>
            ) : (
              incidents.map((inc) => (
                <option key={inc.incident_id} value={inc.incident_id}>
                  [{inc.severity}] {inc.pipeline_name || inc.pipeline_id} — {inc.incident_type}
                </option>
              ))
            )}
          </select>
          <button
            onClick={() => {
              if (selectedIncidentId) {
                fetchInvestigation(selectedIncidentId);
              } else {
                loadIncidents();
              }
            }}
            title="Refresh Incident RCA"
            className="p-1.5 bg-slate-800 hover:bg-slate-700 text-slate-300 hover:text-white rounded-lg border border-slate-700 transition"
          >
            <RefreshCw className={`w-4 h-4 ${loading ? 'animate-spin' : ''}`} />
          </button>
        </div>
      </div>

      {/* Error Alert */}
      {error && (
        <div className="p-4 bg-rose-950/40 border border-rose-800/80 rounded-xl flex items-center justify-between text-xs text-rose-300">
          <div className="flex items-center space-x-2">
            <AlertTriangle className="w-4 h-4 text-rose-400 flex-shrink-0" />
            <span>{error}</span>
          </div>
          <button
            onClick={loadIncidents}
            className="px-3 py-1 bg-rose-900/60 hover:bg-rose-800 text-white rounded font-medium transition"
          >
            Retry
          </button>
        </div>
      )}

      {loading ? (
        <div className="py-24 flex flex-col items-center justify-center">
          <div className="w-10 h-10 border-4 border-cyan-500/30 border-t-cyan-500 rounded-full animate-spin mb-3" />
          <p className="text-sm text-slate-400 font-mono">Aggregating multi-table evidence from Exasol...</p>
        </div>
      ) : !report ? (
        <div className="p-12 text-center text-slate-400 bg-[#0d1424] border border-slate-800 rounded-xl space-y-4">
          <AlertOctagon className="w-10 h-10 text-cyan-400 mx-auto opacity-70" />
          <div>
            <h3 className="text-base font-semibold text-slate-200">No Incident Selected</h3>
            <p className="text-xs text-slate-500 max-w-md mx-auto mt-1">
              Select an incident from the dropdown above or inspect recent anomalies to load root cause diagnostics backed by Exasol telemetry.
            </p>
          </div>
          <button
            onClick={() => navigate('/simulator')}
            className="px-4 py-2 bg-cyan-600 hover:bg-cyan-500 text-white rounded-lg text-xs font-semibold transition"
          >
            Simulate New Incident Scenario
          </button>
        </div>
      ) : (
        <div className="space-y-6">
          {/* Incident Overview Card */}
          <div className="p-5 bg-[#0d1424] border border-slate-800 rounded-xl space-y-4">
            <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 border-b border-slate-800/80 pb-4">
              <div>
                <div className="flex items-center space-x-3">
                  <span
                    className={`px-2.5 py-1 rounded text-xs font-bold border ${
                      report.severity === 'CRITICAL'
                        ? 'bg-rose-950/60 text-rose-300 border-rose-800'
                        : report.severity === 'HIGH'
                        ? 'bg-amber-950/60 text-amber-300 border-amber-800'
                        : 'bg-blue-950/60 text-blue-300 border-blue-800'
                    }`}
                  >
                    {report.severity}
                  </span>
                  <h3 className="text-lg font-bold text-white">{report.pipeline_name}</h3>
                  <span className="text-xs font-mono text-slate-500">{report.pipeline_id}</span>
                </div>
                <div className="text-xs text-slate-400 mt-1 flex items-center space-x-3">
                  <span>Incident Type: <strong className="text-slate-200">{report.incident_type}</strong></span>
                  <span>•</span>
                  <span>Detected: <strong className="text-slate-200">{report.detected_at.substring(0, 19)}</strong></span>
                  <span>•</span>
                  <span>Incident ID: <code className="text-cyan-400 font-mono">{report.incident_id}</code></span>
                </div>
              </div>

              {/* Status Badge */}
              <div className="flex items-center space-x-2">
                <span className="text-xs text-slate-400">Current Status:</span>
                <span
                  className={`px-2.5 py-1 rounded-full text-xs font-bold border ${
                    report.status === 'RESOLVED'
                      ? 'bg-emerald-950/60 text-emerald-300 border-emerald-800'
                      : report.status === 'INVESTIGATING'
                      ? 'bg-indigo-950/60 text-indigo-300 border-indigo-800'
                      : 'bg-rose-950/60 text-rose-300 border-rose-800 animate-pulse'
                  }`}
                >
                  {report.status}
                </span>
              </div>
            </div>

            {/* Probable Cause Box */}
            <div className="p-4 bg-slate-900/90 border-l-4 border-cyan-500 rounded-r-xl">
              <div className="text-xs uppercase tracking-wider text-cyan-400 font-semibold mb-1 flex items-center space-x-1.5">
                <Sparkles className="w-3.5 h-3.5" />
                <span>Primary Probable Cause</span>
                <span className="ml-auto text-[11px] font-mono text-slate-400">
                  Confidence: {(report.confidence_score * 100).toFixed(0)}%
                </span>
              </div>
              <p className="text-sm font-semibold text-slate-100">{report.probable_cause}</p>
            </div>
          </div>

          {/* Upstream Culprit Alert (if exists) */}
          {report.upstream_culprit && (
            <div className="p-4 bg-amber-950/20 border border-amber-800/60 rounded-xl flex items-center justify-between">
              <div className="flex items-center space-x-3">
                <div className="p-2 bg-amber-500/20 rounded-lg text-amber-400">
                  <ShieldAlert className="w-5 h-5" />
                </div>
                <div>
                  <div className="text-xs font-bold text-amber-300 uppercase tracking-wider">
                    Upstream Root Cause Detected
                  </div>
                  <div className="text-sm text-slate-200 mt-0.5">
                    Failure cascaded from direct producer pipeline{' '}
                    <strong className="text-white underline">{report.upstream_culprit.pipeline_name}</strong>{' '}
                    (Status: {report.upstream_culprit.status}, Errors: {report.upstream_culprit.error_count}).
                  </div>
                </div>
              </div>
              <button
                onClick={() => navigate(`/lineage?pipeline_id=${report.upstream_culprit.pipeline_id}`)}
                className="px-3 py-1.5 bg-amber-900/60 hover:bg-amber-800 text-amber-200 border border-amber-700 rounded-lg text-xs font-medium transition flex items-center space-x-1"
              >
                <span>View Lineage</span>
                <ArrowRight className="w-3.5 h-3.5" />
              </button>
            </div>
          )}

          {/* Evidence Points & AI Synthesis Grid */}
          <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
            {/* Quantitative Evidence Points */}
            <div className="lg:col-span-2 space-y-4">
              <div className="p-5 bg-[#0d1424] border border-slate-800 rounded-xl">
                <div className="flex items-center justify-between mb-4">
                  <h4 className="text-sm font-semibold text-white">Database Evidence Points</h4>
                  <span className="text-xs font-mono text-cyan-400">
                    {report.evidence_points ? report.evidence_points.length : 0} Statistical Indicators Verified
                  </span>
                </div>

                <div className="space-y-3">
                  {report.evidence_points && report.evidence_points.length > 0 ? (
                    report.evidence_points.map((ev, idx) => (
                      <div
                        key={idx}
                        className="p-3 bg-slate-900/80 border border-slate-800 rounded-lg flex items-center justify-between text-xs"
                      >
                        <div className="space-y-1 max-w-lg">
                          <div className="flex items-center space-x-2">
                            <span
                              className={`px-1.5 py-0.5 rounded text-[10px] font-mono font-bold ${
                                ev.severity === 'CRITICAL'
                                  ? 'bg-rose-950 text-rose-400 border border-rose-800'
                                  : ev.severity === 'HIGH'
                                  ? 'bg-amber-950 text-amber-400 border border-amber-800'
                                  : 'bg-blue-950 text-blue-400 border border-blue-800'
                              }`}
                            >
                              {ev.category}
                            </span>
                          </div>
                          <p className="text-slate-200 font-medium">{ev.finding}</p>
                        </div>

                        <div className="text-right font-mono text-[11px] flex-shrink-0 ml-4">
                          <div className="text-rose-400 font-bold">{ev.metric_value}</div>
                          <div className="text-slate-500">Base: {ev.baseline_value}</div>
                        </div>
                      </div>
                    ))
                  ) : (
                    <div className="p-4 text-center text-xs text-slate-500">
                      Standard operating baseline maintained across telemetry indicators.
                    </div>
                  )}
                </div>
              </div>

              {/* Actionable Remediation Checklist */}
              <div className="p-5 bg-[#0d1424] border border-slate-800 rounded-xl">
                <h4 className="text-sm font-semibold text-white mb-3">Suggested Remediation Protocol</h4>
                <ul className="space-y-2">
                  {report.suggested_actions && report.suggested_actions.length > 0 ? (
                    report.suggested_actions.map((act, idx) => (
                      <li
                        key={idx}
                        className="flex items-start space-x-2.5 text-xs text-slate-300 p-2.5 bg-slate-900/60 border border-slate-800/80 rounded-lg"
                      >
                        <CheckCircle2 className="w-4 h-4 text-emerald-400 flex-shrink-0 mt-0.5" />
                        <span>{act}</span>
                      </li>
                    ))
                  ) : (
                    <li className="text-xs text-slate-500">No immediate remediation action required.</li>
                  )}
                </ul>
              </div>
            </div>

            {/* AI Diagnostic Synthesis & Status Transition */}
            <div className="space-y-6">
              {/* AI Diagnostic Synthesis */}
              <div className="p-5 bg-[#0d1424] border border-slate-800 rounded-xl space-y-3">
                <div className="flex items-center space-x-2 text-cyan-400">
                  <Sparkles className="w-4 h-4" />
                  <h4 className="text-sm font-semibold text-white">Diagnostic Narrative</h4>
                </div>
                <div className="text-xs text-slate-300 leading-relaxed font-sans bg-slate-900/60 p-3.5 rounded-lg border border-slate-800">
                  {report.llm_analysis}
                </div>
              </div>

              {/* Status Action Panel */}
              <div className="p-5 bg-[#0d1424] border border-slate-800 rounded-xl space-y-4">
                <h4 className="text-sm font-semibold text-white">Incident Lifecycle Action</h4>
                <div className="space-y-2">
                  <label className="text-xs text-slate-400">Resolution Notes (Logged to Audit Table):</label>
                  <textarea
                    rows={2}
                    placeholder="Enter diagnostic finding or engineering resolution summary..."
                    value={resolutionNotes}
                    onChange={(e) => setResolutionNotes(e.target.value)}
                    className="w-full p-2.5 bg-slate-900 border border-slate-700 rounded-lg text-xs text-white focus:outline-none focus:border-cyan-500 placeholder-slate-500"
                  />
                </div>

                <div className="grid grid-cols-3 gap-2">
                  <button
                    onClick={() => handleStatusUpdate('ACKNOWLEDGED')}
                    disabled={updatingStatus || report.status === 'ACKNOWLEDGED'}
                    className="px-3 py-2 bg-slate-800 hover:bg-slate-700 disabled:opacity-50 text-slate-200 rounded-lg text-xs font-semibold transition"
                  >
                    Acknowledge
                  </button>
                  <button
                    onClick={() => handleStatusUpdate('INVESTIGATING')}
                    disabled={updatingStatus || report.status === 'INVESTIGATING'}
                    className="px-3 py-2 bg-indigo-900/60 hover:bg-indigo-800 disabled:opacity-50 text-indigo-200 border border-indigo-700 rounded-lg text-xs font-semibold transition"
                  >
                    Investigating
                  </button>
                  <button
                    onClick={() => handleStatusUpdate('RESOLVED')}
                    disabled={updatingStatus || report.status === 'RESOLVED'}
                    className="px-3 py-2 bg-emerald-900/60 hover:bg-emerald-800 disabled:opacity-50 text-emerald-200 border border-emerald-700 rounded-lg text-xs font-semibold transition flex items-center justify-center space-x-1"
                  >
                    <Check className="w-3.5 h-3.5" />
                    <span>Resolve</span>
                  </button>
                </div>
              </div>

              {/* Downstream Blast Radius Shortcut */}
              <div className="p-4 bg-slate-900/60 border border-slate-800 rounded-xl flex items-center justify-between text-xs">
                <div>
                  <div className="font-semibold text-slate-200">Downstream Blast Radius</div>
                  <div className="text-[11px] text-slate-400">
                    {report.downstream_impact ? report.downstream_impact.length : 0} downstream pipelines exposed
                  </div>
                </div>
                <button
                  onClick={() => navigate(`/lineage?pipeline_id=${report.pipeline_id}`)}
                  className="px-3 py-1.5 bg-cyan-950 hover:bg-cyan-900 text-cyan-300 border border-cyan-800 rounded-lg text-xs font-medium transition"
                >
                  Map Impact
                </button>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
