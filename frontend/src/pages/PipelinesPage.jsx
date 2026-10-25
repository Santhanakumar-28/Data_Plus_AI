import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import {
  Layers,
  Search,
  Filter,
  CheckCircle,
  AlertTriangle,
  XCircle,
  Clock,
  ArrowRight,
  X,
  Activity,
  ShieldAlert,
  GitFork,
  Cpu,
  HardDrive,
  RefreshCw
} from 'lucide-react';
import { apiService } from '../api/client';

export default function PipelinesPage() {
  const [pipelines, setPipelines] = useState([]);
  const [loading, setLoading] = useState(true);
  const [statusFilter, setStatusFilter] = useState('ALL');
  const [criticalityFilter, setCriticalityFilter] = useState('ALL');
  const [searchQuery, setSearchQuery] = useState('');
  
  // Slide-over drawer state for pipeline inspection
  const [selectedPipelineId, setSelectedPipelineId] = useState(null);
  const [pipelineDetail, setPipelineDetail] = useState(null);
  const [detailLoading, setDetailLoading] = useState(false);
  const [detailTab, setDetailTab] = useState('runs'); // runs, quality, dependencies

  const navigate = useNavigate();

  const loadPipelines = async () => {
    try {
      setLoading(true);
      const data = await apiService.getPipelines({
        status: statusFilter,
        criticality: criticalityFilter
      });
      setPipelines(data || []);
    } catch (err) {
      console.error('Error fetching pipelines:', err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadPipelines();
  }, [statusFilter, criticalityFilter]);

  const inspectPipeline = async (id) => {
    setSelectedPipelineId(id);
    try {
      setDetailLoading(true);
      const data = await apiService.getPipelineDetail(id);
      setPipelineDetail(data);
    } catch (err) {
      console.error('Error fetching pipeline detail:', err);
    } finally {
      setDetailLoading(false);
    }
  };

  const filteredPipelines = pipelines.filter((p) => {
    const q = searchQuery.toLowerCase();
    return (
      p.pipeline_name.toLowerCase().includes(q) ||
      p.pipeline_id.toLowerCase().includes(q) ||
      p.source_system.toLowerCase().includes(q) ||
      p.destination_system.toLowerCase().includes(q) ||
      p.owner_team.toLowerCase().includes(q)
    );
  });

  return (
    <div className="space-y-6">
      {/* Header and Controls */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
        <div>
          <h2 className="text-xl font-bold text-white tracking-tight">Pipeline Catalog</h2>
          <p className="text-xs text-slate-400">
            Monitored data pipelines registered in Exasol schema <code className="text-cyan-400 font-mono">DATAPULSE</code>
          </p>
        </div>

        {/* Filters */}
        <div className="flex flex-wrap items-center gap-3">
          {/* Search */}
          <div className="relative">
            <Search className="w-4 h-4 absolute left-3 top-2.5 text-slate-400" />
            <input
              type="text"
              placeholder="Filter by name, source, team..."
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              className="pl-9 pr-4 py-1.5 bg-slate-900 border border-slate-700 rounded-lg text-xs text-white focus:outline-none focus:border-cyan-500 w-56 placeholder-slate-500"
            />
          </div>

          {/* Status Filter */}
          <select
            value={statusFilter}
            onChange={(e) => setStatusFilter(e.target.value)}
            className="px-3 py-1.5 bg-slate-900 border border-slate-700 rounded-lg text-xs text-white focus:outline-none focus:border-cyan-500"
          >
            <option value="ALL">All Statuses</option>
            <option value="HEALTHY">Healthy</option>
            <option value="WARNING">Warning</option>
            <option value="FAILED">Failed</option>
          </select>

          {/* Criticality Filter */}
          <select
            value={criticalityFilter}
            onChange={(e) => setCriticalityFilter(e.target.value)}
            className="px-3 py-1.5 bg-slate-900 border border-slate-700 rounded-lg text-xs text-white focus:outline-none focus:border-cyan-500"
          >
            <option value="ALL">All Criticalities</option>
            <option value="CRITICAL">Critical</option>
            <option value="HIGH">High</option>
            <option value="MEDIUM">Medium</option>
            <option value="LOW">Low</option>
          </select>

          <button
            onClick={loadPipelines}
            className="p-2 rounded-lg bg-slate-800 hover:bg-slate-700 border border-slate-700 text-slate-300"
            title="Reload pipelines from Exasol"
          >
            <RefreshCw className={`w-3.5 h-3.5 ${loading ? 'animate-spin text-cyan-400' : ''}`} />
          </button>
        </div>
      </div>

      {/* Pipelines Data Grid */}
      <div className="bg-[#0d1424] border border-slate-800 rounded-xl overflow-hidden shadow-lg">
        <div className="overflow-x-auto">
          <table className="w-full text-left text-xs border-collapse">
            <thead>
              <tr className="bg-slate-900/90 text-slate-400 border-b border-slate-800 font-semibold uppercase tracking-wider text-[11px]">
                <th className="py-3 px-4">Pipeline</th>
                <th className="py-3 px-4">Source &rarr; Destination</th>
                <th className="py-3 px-4">Type / Schedule</th>
                <th className="py-3 px-4">Criticality</th>
                <th className="py-3 px-4">Status</th>
                <th className="py-3 px-4 text-right">Avg Runtime</th>
                <th className="py-3 px-4 text-right">Fail Rate</th>
                <th className="py-3 px-4 text-right">Quality</th>
                <th className="py-3 px-4 text-center">Incidents</th>
                <th className="py-3 px-4 text-right">Action</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-800/60 text-slate-200">
              {filteredPipelines.length === 0 ? (
                <tr>
                  <td colSpan={10} className="py-12 text-center text-slate-500">
                    No pipelines matched the selected filter.
                  </td>
                </tr>
              ) : (
                filteredPipelines.map((p) => (
                  <tr
                    key={p.pipeline_id}
                    onClick={() => inspectPipeline(p.pipeline_id)}
                    className="hover:bg-slate-800/40 cursor-pointer transition-colors"
                  >
                    <td className="py-3 px-4">
                      <div className="font-semibold text-white">{p.pipeline_name}</div>
                      <div className="text-[10px] text-slate-500 font-mono">{p.pipeline_id}</div>
                    </td>
                    <td className="py-3 px-4">
                      <span className="text-slate-300">{p.source_system}</span>
                      <span className="text-slate-500 mx-1.5">&rarr;</span>
                      <span className="text-slate-300">{p.destination_system}</span>
                    </td>
                    <td className="py-3 px-4 text-slate-400">
                      <div>{p.pipeline_type}</div>
                      <div className="text-[10px] text-slate-500">{p.schedule_type}</div>
                    </td>
                    <td className="py-3 px-4">
                      <span
                        className={`inline-block px-2 py-0.5 rounded text-[10px] font-semibold border ${
                          p.criticality === 'CRITICAL'
                            ? 'bg-rose-950/60 text-rose-300 border-rose-800'
                            : p.criticality === 'HIGH'
                            ? 'bg-amber-950/60 text-amber-300 border-amber-800'
                            : 'bg-slate-800 text-slate-300 border-slate-700'
                        }`}
                      >
                        {p.criticality}
                      </span>
                    </td>
                    <td className="py-3 px-4">
                      <span
                        className={`inline-flex items-center space-x-1.5 px-2 py-0.5 rounded text-[10px] font-semibold border ${
                          p.status === 'HEALTHY'
                            ? 'bg-emerald-950/50 text-emerald-300 border-emerald-800/60'
                            : p.status === 'WARNING'
                            ? 'bg-amber-950/50 text-amber-300 border-amber-800/60'
                            : 'bg-rose-950/50 text-rose-300 border-rose-800/60'
                        }`}
                      >
                        <span
                          className={`w-1.5 h-1.5 rounded-full ${
                            p.status === 'HEALTHY'
                              ? 'bg-emerald-400'
                              : p.status === 'WARNING'
                              ? 'bg-amber-400'
                              : 'bg-rose-500 animate-pulse'
                          }`}
                        />
                        <span>{p.status}</span>
                      </span>
                    </td>
                    <td className="py-3 px-4 text-right font-mono text-slate-300">
                      {Math.round(p.avg_duration_seconds)}s
                    </td>
                    <td className="py-3 px-4 text-right font-mono">
                      <span
                        className={
                          p.failure_rate_pct > 0
                            ? 'text-rose-400 font-semibold'
                            : 'text-slate-400'
                        }
                      >
                        {p.failure_rate_pct.toFixed(1)}%
                      </span>
                    </td>
                    <td className="py-3 px-4 text-right font-mono text-slate-300">
                      {p.avg_completeness_score.toFixed(1)}%
                    </td>
                    <td className="py-3 px-4 text-center">
                      {p.open_incidents_count > 0 ? (
                        <span className="px-2 py-0.5 rounded-full bg-rose-500/20 text-rose-400 font-bold border border-rose-500/30 text-[10px]">
                          {p.open_incidents_count}
                        </span>
                      ) : (
                        <span className="text-slate-600 font-mono">0</span>
                      )}
                    </td>
                    <td className="py-3 px-4 text-right">
                      <button
                        onClick={(e) => {
                          e.stopPropagation();
                          inspectPipeline(p.pipeline_id);
                        }}
                        className="px-2.5 py-1 bg-slate-800 hover:bg-cyan-600 hover:text-white text-slate-300 rounded text-[11px] font-medium transition"
                      >
                        Inspect
                      </button>
                    </td>
                  </tr>
                ))
              )}
            </tbody>
          </table>
        </div>
      </div>

      {/* Slide-over Detailed Inspector Drawer */}
      {selectedPipelineId && (
        <div className="fixed inset-0 z-50 bg-black/60 backdrop-blur-sm flex justify-end">
          <div className="w-full max-w-2xl bg-[#0d1424] border-l border-slate-800 h-full flex flex-col shadow-2xl animate-in slide-in-from-right duration-200">
            {/* Drawer Header */}
            <div className="p-5 border-b border-slate-800 flex items-center justify-between">
              <div>
                <div className="flex items-center space-x-2">
                  <h3 className="text-base font-bold text-white">
                    {pipelineDetail?.pipeline.pipeline_name || selectedPipelineId}
                  </h3>
                  <span className="text-xs px-2 py-0.5 rounded bg-slate-800 font-mono text-cyan-400">
                    {selectedPipelineId}
                  </span>
                </div>
                <p className="text-xs text-slate-400 mt-1">
                  Owner: {pipelineDetail?.pipeline.owner_team || 'Data Platform'} • Criticality:{' '}
                  <span className="font-semibold text-slate-300">
                    {pipelineDetail?.pipeline.criticality || 'MEDIUM'}
                  </span>
                </p>
              </div>
              <button
                onClick={() => setSelectedPipelineId(null)}
                className="p-2 text-slate-400 hover:text-white rounded-lg hover:bg-slate-800"
              >
                <X className="w-5 h-5" />
              </button>
            </div>

            {/* Action Bar inside Drawer */}
            <div className="px-5 py-3 bg-slate-900/60 border-b border-slate-800 flex items-center justify-between text-xs">
              <div className="flex items-center space-x-2">
                <button
                  onClick={() => setDetailTab('runs')}
                  className={`px-3 py-1.5 rounded-lg font-medium transition ${
                    detailTab === 'runs'
                      ? 'bg-cyan-500/20 text-cyan-400 border border-cyan-500/40'
                      : 'text-slate-400 hover:text-slate-200'
                  }`}
                >
                  Execution Runs ({pipelineDetail?.recent_runs?.length || 0})
                </button>
                <button
                  onClick={() => setDetailTab('quality')}
                  className={`px-3 py-1.5 rounded-lg font-medium transition ${
                    detailTab === 'quality'
                      ? 'bg-cyan-500/20 text-cyan-400 border border-cyan-500/40'
                      : 'text-slate-400 hover:text-slate-200'
                  }`}
                >
                  Data Quality Audits ({pipelineDetail?.recent_quality?.length || 0})
                </button>
                <button
                  onClick={() => setDetailTab('dependencies')}
                  className={`px-3 py-1.5 rounded-lg font-medium transition ${
                    detailTab === 'dependencies'
                      ? 'bg-cyan-500/20 text-cyan-400 border border-cyan-500/40'
                      : 'text-slate-400 hover:text-slate-200'
                  }`}
                >
                  Lineage ({ (pipelineDetail?.upstream_dependencies?.length || 0) + (pipelineDetail?.downstream_dependencies?.length || 0) })
                </button>
              </div>

              <button
                onClick={() => navigate(`/lineage?pipeline_id=${selectedPipelineId}`)}
                className="text-xs text-indigo-400 hover:text-indigo-300 flex items-center space-x-1"
              >
                <GitFork className="w-3.5 h-3.5" />
                <span>Blast Radius</span>
              </button>
            </div>

            {/* Drawer Body */}
            <div className="flex-1 overflow-y-auto p-5">
              {detailLoading ? (
                <div className="py-16 flex flex-col items-center justify-center">
                  <div className="w-8 h-8 border-4 border-cyan-500/30 border-t-cyan-500 rounded-full animate-spin mb-3" />
                  <p className="text-xs text-slate-400 font-mono">Querying Exasol runs telemetry...</p>
                </div>
              ) : detailTab === 'runs' ? (
                <div className="space-y-3">
                  {pipelineDetail?.recent_runs?.map((r) => (
                    <div
                      key={r.run_id}
                      className="p-3 bg-slate-900/80 border border-slate-800 rounded-lg flex items-center justify-between text-xs"
                    >
                      <div>
                        <div className="flex items-center space-x-2">
                          <span
                            className={`w-2 h-2 rounded-full ${
                              r.status === 'SUCCESS'
                                ? 'bg-emerald-400'
                                : r.status === 'DEGRADED'
                                ? 'bg-amber-400'
                                : 'bg-rose-500'
                            }`}
                          />
                          <span className="font-mono font-semibold text-white">{r.run_id}</span>
                          <span className="text-slate-500 font-mono text-[11px]">{r.start_time.substring(0, 19)}</span>
                        </div>
                        <div className="flex items-center space-x-4 mt-1 text-[11px] text-slate-400">
                          <span>Processed: {r.records_processed.toLocaleString()} records</span>
                          <span>Errors: {r.error_count}</span>
                          <span>Retries: {r.retry_count}</span>
                        </div>
                      </div>
                      <div className="text-right">
                        <div className="font-mono font-semibold text-slate-200">
                          {r.duration_seconds ? `${Math.round(r.duration_seconds)}s` : '--'}
                        </div>
                        <div className="text-[10px] text-slate-400 flex items-center space-x-1 justify-end">
                          <Cpu className="w-3 h-3 text-cyan-400" />
                          <span>{Math.round(r.cpu_usage)}%</span>
                          <HardDrive className="w-3 h-3 ml-1 text-indigo-400" />
                          <span>{Math.round(r.memory_usage)}%</span>
                        </div>
                      </div>
                    </div>
                  ))}
                </div>
              ) : detailTab === 'quality' ? (
                <div className="space-y-3">
                  {pipelineDetail?.recent_quality?.map((q) => (
                    <div
                      key={q.check_id}
                      className="p-3 bg-slate-900/80 border border-slate-800 rounded-lg text-xs space-y-1.5"
                    >
                      <div className="flex items-center justify-between">
                        <span className="font-mono text-slate-400 text-[11px]">{q.checked_at.substring(0, 19)}</span>
                        <span
                          className={`font-semibold ${
                            q.completeness_score >= 98
                              ? 'text-emerald-400'
                              : q.completeness_score >= 90
                              ? 'text-amber-400'
                              : 'text-rose-400'
                          }`}
                        >
                          Completeness: {q.completeness_score.toFixed(1)}%
                        </span>
                      </div>
                      <div className="grid grid-cols-4 gap-2 pt-1 text-[11px] text-slate-400 font-mono">
                        <div>Freshness: {Math.round(q.freshness_minutes)}m</div>
                        <div>Nulls: {q.null_count.toLocaleString()}</div>
                        <div>Duplicates: {q.duplicate_count}</div>
                        <div>Schema Errs: {q.schema_error_count}</div>
                      </div>
                    </div>
                  ))}
                </div>
              ) : (
                <div className="space-y-6">
                  {/* Upstream */}
                  <div>
                    <h4 className="text-xs font-semibold text-slate-400 uppercase tracking-wider mb-2">
                      Upstream Producers (Dependencies)
                    </h4>
                    {pipelineDetail?.upstream_dependencies?.length === 0 ? (
                      <p className="text-xs text-slate-500 italic">No upstream dependencies. Root pipeline.</p>
                    ) : (
                      <div className="space-y-2">
                        {pipelineDetail?.upstream_dependencies?.map((dep, idx) => (
                          <div
                            key={idx}
                            className="p-3 bg-slate-900/70 border border-slate-800 rounded-lg text-xs flex items-center justify-between"
                          >
                            <div>
                              <div className="font-semibold text-white">{dep.upstream_name || dep.upstream_pipeline_id}</div>
                              <div className="text-[10px] text-slate-500 font-mono">{dep.upstream_pipeline_id}</div>
                            </div>
                            <span className="text-[10px] font-mono px-2 py-0.5 rounded bg-slate-800 text-slate-400 border border-slate-700">
                              {dep.dependency_type}
                            </span>
                          </div>
                        ))}
                      </div>
                    )}
                  </div>

                  {/* Downstream */}
                  <div>
                    <h4 className="text-xs font-semibold text-slate-400 uppercase tracking-wider mb-2">
                      Downstream Consumers
                    </h4>
                    {pipelineDetail?.downstream_dependencies?.length === 0 ? (
                      <p className="text-xs text-slate-500 italic">No downstream consumers registered.</p>
                    ) : (
                      <div className="space-y-2">
                        {pipelineDetail?.downstream_dependencies?.map((dep, idx) => (
                          <div
                            key={idx}
                            className="p-3 bg-slate-900/70 border border-slate-800 rounded-lg text-xs flex items-center justify-between"
                          >
                            <div>
                              <div className="font-semibold text-white">{dep.downstream_name || dep.downstream_pipeline_id}</div>
                              <div className="text-[10px] text-slate-500 font-mono">{dep.downstream_pipeline_id}</div>
                            </div>
                            <span className="text-[10px] font-mono px-2 py-0.5 rounded bg-slate-800 text-slate-400 border border-slate-700">
                              {dep.dependency_type}
                            </span>
                          </div>
                        ))}
                      </div>
                    )}
                  </div>
                </div>
              )}
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
