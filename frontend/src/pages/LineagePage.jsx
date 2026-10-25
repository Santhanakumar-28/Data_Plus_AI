import React, { useState, useEffect } from 'react';
import { useSearchParams, useNavigate } from 'react-router-dom';
import {
  GitFork,
  AlertTriangle,
  Layers,
  ArrowRight,
  ShieldAlert,
  FileSpreadsheet,
  Activity,
  CheckCircle2,
  RefreshCw
} from 'lucide-react';
import { apiService } from '../api/client';

export default function LineagePage() {
  const [searchParams] = useSearchParams();
  const navigate = useNavigate();

  const [graph, setGraph] = useState({ nodes: [], edges: [] });
  const [selectedPipelineId, setSelectedPipelineId] = useState('');
  const [blastReport, setBlastReport] = useState(null);
  const [loading, setLoading] = useState(true);
  const [calculating, setCalculating] = useState(false);

  const loadGraph = async () => {
    try {
      setLoading(true);
      const data = await apiService.getDependencyGraph();
      setGraph(data || { nodes: [], edges: [] });

      const urlPipeline = searchParams.get('pipeline_id');
      const initialId = urlPipeline || (data?.nodes?.length > 0 ? data.nodes[0].id : 'PIPE_CUST_MASTER');
      setSelectedPipelineId(initialId);
      calculateBlast(initialId);
    } catch (err) {
      console.error('Failed to load dependency graph:', err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadGraph();
  }, [searchParams]);

  const calculateBlast = async (id) => {
    if (!id) return;
    try {
      setCalculating(true);
      const report = await apiService.getBlastRadius(id);
      setBlastReport(report);
    } catch (err) {
      console.error('Blast radius calculation failed:', err);
    } finally {
      setCalculating(false);
    }
  };

  return (
    <div className="space-y-6">
      {/* Header and Pipeline Picker */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 p-5 bg-gradient-to-r from-slate-900 via-[#0d1424] to-indigo-950/40 border border-slate-800 rounded-xl">
        <div>
          <div className="flex items-center space-x-2">
            <h2 className="text-xl font-bold text-white tracking-tight">Lineage & Blast Radius Calculator</h2>
            <span className="px-2 py-0.5 rounded text-[11px] font-mono bg-cyan-950/60 text-cyan-400 border border-cyan-800/40">
              DAG Lineage Traversal
            </span>
          </div>
          <p className="text-xs text-slate-400 mt-1">
            Traverses Exasol <code className="text-cyan-400 font-mono">PIPELINE_DEPENDENCIES</code> graph to predict downstream business impact.
          </p>
        </div>

        {/* Pipeline Selector */}
        <div className="flex items-center space-x-3">
          <label className="text-xs text-slate-400">Simulate Failure In:</label>
          <select
            value={selectedPipelineId}
            onChange={(e) => {
              setSelectedPipelineId(e.target.value);
              calculateBlast(e.target.value);
            }}
            className="px-3 py-1.5 bg-slate-900 border border-slate-700 rounded-lg text-xs text-white focus:outline-none focus:border-cyan-500 font-mono"
          >
            {graph.nodes.map((node) => (
              <option key={node.id} value={node.id}>
                [{node.criticality}] {node.name} ({node.id})
              </option>
            ))}
          </select>
        </div>
      </div>

      {/* Blast Radius Report Grid */}
      {blastReport && (
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          {/* Blast Score Metric Card */}
          <div className="p-5 bg-[#0d1424] border border-slate-800 rounded-xl flex flex-col justify-between">
            <div>
              <div className="flex items-center justify-between mb-2">
                <span className="text-xs font-semibold uppercase tracking-wider text-slate-400">
                  Total Impact Score
                </span>
                <ShieldAlert
                  className={`w-4 h-4 ${
                    blastReport.total_impact_score > 60
                      ? 'text-rose-400'
                      : blastReport.total_impact_score > 30
                      ? 'text-amber-400'
                      : 'text-cyan-400'
                  }`}
                />
              </div>

              <div className="flex items-baseline space-x-2 mt-2">
                <div
                  className={`text-4xl font-extrabold ${
                    blastReport.total_impact_score > 60
                      ? 'text-rose-400'
                      : blastReport.total_impact_score > 30
                      ? 'text-amber-400'
                      : 'text-cyan-400'
                  }`}
                >
                  {blastReport.total_impact_score.toFixed(1)}
                </div>
                <span className="text-xs text-slate-500">/ 100.0</span>
              </div>

              <p className="text-xs text-slate-400 mt-2">
                Severity Rating: <strong className="text-white">{blastReport.severity}</strong>. Weighted across
                cascading hops, system criticality, and downstream consumers.
              </p>
            </div>

            <div className="pt-4 border-t border-slate-800 mt-4 space-y-2 text-xs">
              <div className="flex justify-between text-slate-400">
                <span>Direct Upstream Culprit:</span>
                <span className="font-semibold text-white">{blastReport.incident_pipeline_name}</span>
              </div>
              <div className="flex justify-between text-slate-400">
                <span>Downstream Pipelines Affected:</span>
                <span className="font-semibold text-rose-400">
                  {blastReport.affected_downstream_pipelines.length} pipelines
                </span>
              </div>
              <div className="flex justify-between text-slate-400">
                <span>Business BI Reports Affected:</span>
                <span className="font-semibold text-amber-400">
                  {blastReport.affected_business_reports.length} reports
                </span>
              </div>
            </div>
          </div>

          {/* Affected Downstream Pipelines */}
          <div className="p-5 bg-[#0d1424] border border-slate-800 rounded-xl flex flex-col">
            <h3 className="text-sm font-semibold text-white mb-2">Affected Downstream Pipelines</h3>
            <p className="text-xs text-slate-400 mb-4">
              Pipelines directly or transitively blocked if {blastReport.incident_pipeline_name} fails
            </p>

            <div className="flex-1 overflow-y-auto space-y-2.5 max-h-64 pr-1">
              {blastReport.affected_downstream_pipelines.length === 0 ? (
                <div className="text-xs text-slate-500 text-center py-10">
                  No downstream pipeline dependencies. Terminal node in DAG.
                </div>
              ) : (
                blastReport.affected_downstream_pipelines.map((dep, idx) => (
                  <div
                    key={idx}
                    className="p-3 bg-slate-900/80 border border-slate-800 rounded-lg flex items-center justify-between text-xs"
                  >
                    <div>
                      <div className="font-semibold text-white">{dep.pipeline_name}</div>
                      <div className="text-[10px] text-slate-400 flex items-center space-x-2 mt-0.5">
                        <span className="font-mono text-cyan-400">{dep.pipeline_id}</span>
                        <span>•</span>
                        <span>{dep.owner_team}</span>
                      </div>
                    </div>
                    <div className="text-right flex flex-col items-end">
                      <span className="text-[10px] font-mono px-2 py-0.5 rounded bg-rose-950/60 text-rose-300 border border-rose-800">
                        Hop: +{dep.hop_distance}
                      </span>
                      <span className="text-[10px] text-slate-500 mt-1">{dep.dependency_type}</span>
                    </div>
                  </div>
                ))
              )}
            </div>
          </div>

          {/* Affected Business Reports & Executive Dashboards */}
          <div className="p-5 bg-[#0d1424] border border-slate-800 rounded-xl flex flex-col">
            <div className="flex items-center space-x-2 mb-2">
              <FileSpreadsheet className="w-4 h-4 text-cyan-400" />
              <h3 className="text-sm font-semibold text-white">Impacted Business Systems</h3>
            </div>
            <p className="text-xs text-slate-400 mb-4">
              High-value organizational assets, BI portals, and regulatory models degraded
            </p>

            <div className="flex-1 overflow-y-auto space-y-2 max-h-64 pr-1">
              {blastReport.affected_business_reports.length === 0 ? (
                <div className="text-xs text-slate-500 text-center py-10">
                  No public business reports mapped to this pipeline.
                </div>
              ) : (
                blastReport.affected_business_reports.map((report, idx) => (
                  <div
                    key={idx}
                    className="p-2.5 bg-slate-900/60 border border-slate-800 rounded-lg flex items-center space-x-2.5 text-xs text-slate-200"
                  >
                    <span className="w-1.5 h-1.5 rounded-full bg-rose-400 flex-shrink-0" />
                    <span className="font-medium truncate">{report}</span>
                  </div>
                ))
              )}
            </div>
          </div>
        </div>
      )}

      {/* Full Enterprise Dependency Matrix */}
      <div className="p-5 bg-[#0d1424] border border-slate-800 rounded-xl space-y-4">
        <div className="flex items-center justify-between">
          <div>
            <h3 className="text-sm font-semibold text-white">Enterprise Pipeline Lineage Graph</h3>
            <p className="text-xs text-slate-400">
              Interactive structural map of all 12 pipelines and 9 directed dependencies from Exasol
            </p>
          </div>
          <button
            onClick={loadGraph}
            className="p-1.5 bg-slate-800 hover:bg-slate-700 text-slate-300 rounded border border-slate-700 text-xs flex items-center space-x-1"
          >
            <RefreshCw className="w-3 h-3" />
            <span>Reload DAG</span>
          </button>
        </div>

        {/* Visual Node Grid */}
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-4 pt-2">
          {graph.nodes.map((node) => {
            const isSelected = node.id === selectedPipelineId;
            const isDownstream = blastReport?.affected_downstream_pipelines?.some(
              (p) => p.pipeline_id === node.id
            );

            return (
              <div
                key={node.id}
                onClick={() => {
                  setSelectedPipelineId(node.id);
                  calculateBlast(node.id);
                }}
                className={`p-4 rounded-xl border transition-all cursor-pointer ${
                  isSelected
                    ? 'bg-cyan-950/40 border-cyan-500 shadow-md shadow-cyan-500/20'
                    : isDownstream
                    ? 'bg-rose-950/20 border-rose-800/80'
                    : 'bg-slate-900/80 border-slate-800 hover:border-slate-700'
                }`}
              >
                <div className="flex items-center justify-between mb-2">
                  <span
                    className={`w-2 h-2 rounded-full ${
                      node.status === 'HEALTHY'
                        ? 'bg-emerald-400'
                        : node.status === 'WARNING'
                        ? 'bg-amber-400'
                        : 'bg-rose-500 animate-pulse'
                    }`}
                  />
                  <span
                    className={`text-[10px] font-mono px-1.5 py-0.5 rounded border ${
                      node.criticality === 'CRITICAL'
                        ? 'bg-rose-950/60 text-rose-300 border-rose-800'
                        : node.criticality === 'HIGH'
                        ? 'bg-amber-950/60 text-amber-300 border-amber-800'
                        : 'bg-slate-800 text-slate-400 border-slate-700'
                    }`}
                  >
                    {node.criticality}
                  </span>
                </div>

                <div className="font-semibold text-xs text-white truncate">{node.name}</div>
                <div className="text-[10px] font-mono text-slate-400 truncate mt-0.5">{node.id}</div>

                <div className="mt-3 pt-2 border-t border-slate-800/80 flex items-center justify-between text-[11px] text-slate-400">
                  <span>{node.type}</span>
                  <span className="font-mono text-slate-500">{node.owner}</span>
                </div>
              </div>
            );
          })}
        </div>
      </div>
    </div>
  );
}
