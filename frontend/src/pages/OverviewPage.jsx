import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import {
  Activity,
  CheckCircle,
  AlertTriangle,
  XCircle,
  Clock,
  ShieldCheck,
  TrendingUp,
  AlertCircle,
  ArrowRight,
  Database,
  ExternalLink
} from 'lucide-react';
import {
  ResponsiveContainer,
  AreaChart,
  Area,
  BarChart,
  Bar,
  XAxis,
  YAxis,
  Tooltip,
  CartesianGrid,
  Legend,
  PieChart,
  Pie,
  Cell
} from 'recharts';
import { apiService } from '../api/client';

export default function OverviewPage() {
  const [overview, setOverview] = useState(null);
  const [trends, setTrends] = useState([]);
  const [incidents, setIncidents] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const navigate = useNavigate();

  const loadData = async () => {
    try {
      setLoading(true);
      setError(null);
      const [overviewData, trendsData, incidentList] = await Promise.all([
        apiService.getOverview(),
        apiService.getTrends(14),
        apiService.getIncidents({ limit: 5 })
      ]);
      setOverview(overviewData);
      setTrends(trendsData.trends || []);
      setIncidents(incidentList || []);
    } catch (err) {
      console.error('Failed to load overview:', err);
      setError(err.message || 'Error connecting to backend / Exasol Personal');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadData();
    const interval = setInterval(loadData, 30000);
    return () => clearInterval(interval);
  }, []);

  if (loading && !overview) {
    return (
      <div className="flex h-96 items-center justify-center">
        <div className="flex flex-col items-center space-y-3">
          <div className="w-10 h-10 border-4 border-cyan-500/30 border-t-cyan-500 rounded-full animate-spin" />
          <p className="text-slate-400 text-sm font-mono">Executing analytical SQL in Exasol...</p>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="p-6 bg-rose-950/30 border border-rose-800 rounded-xl text-rose-200">
        <div className="flex items-center space-x-3 mb-2">
          <AlertCircle className="w-6 h-6 text-rose-400" />
          <h2 className="text-lg font-bold">Failed to load Exasol Overview Analytics</h2>
        </div>
        <p className="text-sm text-rose-300 font-mono mb-4">{error}</p>
        <button
          onClick={loadData}
          className="px-4 py-2 bg-rose-700 hover:bg-rose-600 text-white rounded-lg text-sm font-medium transition"
        >
          Retry Database Query
        </button>
      </div>
    );
  }

  const pieData = [
    { name: 'Healthy', value: overview?.healthy_pipelines || 0, color: '#10B981' },
    { name: 'Warning', value: overview?.warning_pipelines || 0, color: '#F59E0B' },
    { name: 'Failed', value: overview?.failed_pipelines || 0, color: '#EF4444' }
  ];

  return (
    <div className="space-y-6">
      {/* Top Banner Notice */}
      <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between p-4 bg-gradient-to-r from-slate-900 via-[#0f172a] to-cyan-950/30 border border-slate-800 rounded-xl">
        <div className="flex items-center space-x-3 mb-3 sm:mb-0">
          <div className="p-2.5 bg-cyan-500/10 border border-cyan-500/20 rounded-lg text-cyan-400">
            <Database className="w-5 h-5" />
          </div>
          <div>
            <h3 className="text-sm font-semibold text-slate-200">
              Live Observability Powered by Exasol Personal
            </h3>
            <p className="text-xs text-slate-400">
              Aggregated across {overview?.total_runs_evaluated?.toLocaleString() || 0} historical pipeline runs in schema <code className="text-cyan-400 font-mono">DATAPULSE</code>
            </p>
          </div>
        </div>
        <div className="flex items-center space-x-3">
          <button
            onClick={() => navigate('/simulator')}
            className="px-3.5 py-1.5 bg-gradient-to-r from-cyan-600 to-indigo-600 hover:from-cyan-500 hover:to-indigo-500 text-white text-xs font-medium rounded-lg shadow-sm transition flex items-center space-x-1.5"
          >
            <span>Demo Disaster Simulator</span>
            <ArrowRight className="w-3.5 h-3.5" />
          </button>
        </div>
      </div>

      {/* KPI Cards Grid */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        {/* Total Pipelines */}
        <div className="p-5 bg-[#0d1424] border border-slate-800 rounded-xl">
          <div className="flex items-center justify-between text-slate-400 mb-2">
            <span className="text-xs font-semibold uppercase tracking-wider">Monitored Pipelines</span>
            <Activity className="w-4 h-4 text-cyan-400" />
          </div>
          <div className="text-3xl font-bold text-white tracking-tight">{overview?.total_pipelines || 0}</div>
          <div className="flex items-center space-x-2 mt-2 text-xs">
            <span className="text-emerald-400 flex items-center">
              <CheckCircle className="w-3 h-3 mr-1" />
              {overview?.healthy_pipelines || 0} Healthy
            </span>
            <span className="text-slate-600">•</span>
            <span className="text-amber-400 flex items-center">
              <AlertTriangle className="w-3 h-3 mr-1" />
              {overview?.warning_pipelines || 0} Degraded
            </span>
            <span className="text-slate-600">•</span>
            <span className="text-rose-400 flex items-center">
              <XCircle className="w-3 h-3 mr-1" />
              {overview?.failed_pipelines || 0} Failed
            </span>
          </div>
        </div>

        {/* Open Incidents */}
        <div className="p-5 bg-[#0d1424] border border-slate-800 rounded-xl">
          <div className="flex items-center justify-between text-slate-400 mb-2">
            <span className="text-xs font-semibold uppercase tracking-wider">Active Incidents</span>
            <AlertCircle className="w-4 h-4 text-rose-400" />
          </div>
          <div className="text-3xl font-bold text-white tracking-tight">{overview?.open_incidents || 0}</div>
          <div className="mt-2 text-xs text-rose-400 flex items-center space-x-1.5 font-medium">
            <span className="w-1.5 h-1.5 rounded-full bg-rose-500 animate-pulse" />
            <span>{overview?.critical_incidents || 0} Critical Impact SLA</span>
          </div>
        </div>

        {/* Data Quality Score */}
        <div className="p-5 bg-[#0d1424] border border-slate-800 rounded-xl">
          <div className="flex items-center justify-between text-slate-400 mb-2">
            <span className="text-xs font-semibold uppercase tracking-wider">Avg Data Quality</span>
            <ShieldCheck className="w-4 h-4 text-emerald-400" />
          </div>
          <div className="text-3xl font-bold text-white tracking-tight">
            {overview?.avg_data_quality_score?.toFixed(1) || '0.0'}%
          </div>
          <div className="mt-2 text-xs text-slate-400 flex items-center">
            <span>Completeness, schema & freshness score</span>
          </div>
        </div>

        {/* Avg Duration */}
        <div className="p-5 bg-[#0d1424] border border-slate-800 rounded-xl">
          <div className="flex items-center justify-between text-slate-400 mb-2">
            <span className="text-xs font-semibold uppercase tracking-wider">Avg Pipeline Runtime</span>
            <Clock className="w-4 h-4 text-indigo-400" />
          </div>
          <div className="text-3xl font-bold text-white tracking-tight">
            {overview?.avg_duration_seconds ? `${Math.round(overview.avg_duration_seconds)}s` : '0s'}
          </div>
          <div className="mt-2 text-xs text-slate-400 truncate">
            Last success: {overview?.last_successful_run ? overview.last_successful_run.substring(0, 19) : 'N/A'}
          </div>
        </div>
      </div>

      {/* Main Charts Section */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* 14-Day Execution Volume & Status Trend */}
        <div className="lg:col-span-2 p-5 bg-[#0d1424] border border-slate-800 rounded-xl flex flex-col">
          <div className="flex items-center justify-between mb-4">
            <div>
              <h3 className="text-sm font-semibold text-white">14-Day Pipeline Run History</h3>
              <p className="text-xs text-slate-400">Daily execution breakdown aggregated from Exasol fact tables</p>
            </div>
            <span className="text-xs font-mono text-cyan-400 bg-cyan-950/40 border border-cyan-800/40 px-2.5 py-1 rounded">
              Window: 14 Days
            </span>
          </div>
          <div className="h-72 w-full">
            <ResponsiveContainer width="100%" height="100%">
              <BarChart data={trends} margin={{ top: 10, right: 10, left: -20, bottom: 0 }}>
                <CartesianGrid strokeDasharray="3 3" stroke="#1e293b" />
                <XAxis dataKey="date" stroke="#64748b" tick={{ fontSize: 11 }} />
                <YAxis stroke="#64748b" tick={{ fontSize: 11 }} />
                <Tooltip
                  contentStyle={{ backgroundColor: '#0f172a', borderColor: '#334155', borderRadius: '8px' }}
                  labelStyle={{ color: '#94a3b8' }}
                />
                <Legend wrapperStyle={{ fontSize: '12px' }} />
                <Bar dataKey="success_runs" name="Success" fill="#10B981" stackId="a" />
                <Bar dataKey="degraded_runs" name="Degraded" fill="#F59E0B" stackId="a" />
                <Bar dataKey="failed_runs" name="Failed" fill="#EF4444" stackId="a" />
              </BarChart>
            </ResponsiveContainer>
          </div>
        </div>

        {/* Health Distribution Donut */}
        <div className="p-5 bg-[#0d1424] border border-slate-800 rounded-xl flex flex-col justify-between">
          <div className="mb-2">
            <h3 className="text-sm font-semibold text-white">Pipeline Health Distribution</h3>
            <p className="text-xs text-slate-400">Current state across all registered pipelines</p>
          </div>
          <div className="h-56 w-full flex items-center justify-center">
            <ResponsiveContainer width="100%" height="100%">
              <PieChart>
                <Pie
                  data={pieData}
                  cx="50%"
                  cy="50%"
                  innerRadius={55}
                  outerRadius={80}
                  paddingAngle={4}
                  dataKey="value"
                >
                  {pieData.map((entry, index) => (
                    <Cell key={`cell-${index}`} fill={entry.color} />
                  ))}
                </Pie>
                <Tooltip
                  contentStyle={{ backgroundColor: '#0f172a', borderColor: '#334155', borderRadius: '8px' }}
                />
              </PieChart>
            </ResponsiveContainer>
          </div>
          <div className="grid grid-cols-3 gap-2 pt-3 border-t border-slate-800 text-center text-xs">
            <div>
              <div className="font-bold text-emerald-400">{overview?.healthy_pipelines || 0}</div>
              <div className="text-slate-400 text-[11px]">Healthy</div>
            </div>
            <div>
              <div className="font-bold text-amber-400">{overview?.warning_pipelines || 0}</div>
              <div className="text-slate-400 text-[11px]">Warning</div>
            </div>
            <div>
              <div className="font-bold text-rose-400">{overview?.failed_pipelines || 0}</div>
              <div className="text-slate-400 text-[11px]">Failed</div>
            </div>
          </div>
        </div>
      </div>

      {/* Quality Trend & Recent Incidents Row */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Data Quality Historical Index */}
        <div className="p-5 bg-[#0d1424] border border-slate-800 rounded-xl">
          <div className="flex items-center justify-between mb-4">
            <div>
              <h3 className="text-sm font-semibold text-white">Platform Data Quality Index</h3>
              <p className="text-xs text-slate-400">Average completeness score trajectory over time</p>
            </div>
            <TrendingUp className="w-4 h-4 text-cyan-400" />
          </div>
          <div className="h-56 w-full">
            <ResponsiveContainer width="100%" height="100%">
              <AreaChart data={trends} margin={{ top: 10, right: 10, left: -20, bottom: 0 }}>
                <defs>
                  <linearGradient id="colorQuality" x1="0" y1="0" x2="0" y2="1">
                    <stop offset="5%" stopColor="#06b6d4" stopOpacity={0.4} />
                    <stop offset="95%" stopColor="#06b6d4" stopOpacity={0} />
                  </linearGradient>
                </defs>
                <CartesianGrid strokeDasharray="3 3" stroke="#1e293b" />
                <XAxis dataKey="date" stroke="#64748b" tick={{ fontSize: 11 }} />
                <YAxis domain={[50, 100]} stroke="#64748b" tick={{ fontSize: 11 }} />
                <Tooltip
                  contentStyle={{ backgroundColor: '#0f172a', borderColor: '#334155', borderRadius: '8px' }}
                />
                <Area type="monotone" dataKey="avg_quality" name="Avg Quality (%)" stroke="#06b6d4" fillOpacity={1} fill="url(#colorQuality)" />
              </AreaChart>
            </ResponsiveContainer>
          </div>
        </div>

        {/* Recent Active Incidents Table */}
        <div className="p-5 bg-[#0d1424] border border-slate-800 rounded-xl flex flex-col justify-between">
          <div>
            <div className="flex items-center justify-between mb-4">
              <div>
                <h3 className="text-sm font-semibold text-white">Recent Incident Stream</h3>
                <p className="text-xs text-slate-400">Active alerts requiring engineering intervention</p>
              </div>
              <button
                onClick={() => navigate('/incidents')}
                className="text-xs text-cyan-400 hover:text-cyan-300 font-medium flex items-center space-x-1"
              >
                <span>View all</span>
                <ArrowRight className="w-3 h-3" />
              </button>
            </div>

            <div className="space-y-2.5">
              {incidents.length === 0 ? (
                <div className="text-center py-8 text-slate-500 text-xs">
                  No active incidents. All data pipelines running nominally.
                </div>
              ) : (
                incidents.slice(0, 4).map((inc) => (
                  <div
                    key={inc.incident_id}
                    onClick={() => navigate(`/investigation?incident_id=${inc.incident_id}`)}
                    className="p-3 bg-slate-900/80 hover:bg-slate-800/80 border border-slate-800 rounded-lg cursor-pointer transition flex items-center justify-between"
                  >
                    <div className="flex items-center space-x-3 min-w-0">
                      <span
                        className={`w-2 h-2 rounded-full flex-shrink-0 ${
                          inc.severity === 'CRITICAL'
                            ? 'bg-rose-500'
                            : inc.severity === 'HIGH'
                            ? 'bg-amber-500'
                            : 'bg-blue-500'
                        }`}
                      />
                      <div className="min-w-0">
                        <div className="text-xs font-semibold text-slate-200 truncate">
                          {inc.pipeline_name || inc.pipeline_id}
                        </div>
                        <div className="text-[11px] text-slate-400 truncate max-w-xs">
                          {inc.description}
                        </div>
                      </div>
                    </div>
                    <div className="flex items-center space-x-2 flex-shrink-0 ml-2">
                      <span
                        className={`text-[10px] font-semibold px-2 py-0.5 rounded border ${
                          inc.severity === 'CRITICAL'
                            ? 'bg-rose-950/60 text-rose-300 border-rose-800'
                            : 'bg-amber-950/60 text-amber-300 border-amber-800'
                        }`}
                      >
                        {inc.severity}
                      </span>
                      <ArrowRight className="w-3 h-3 text-slate-500" />
                    </div>
                  </div>
                ))
              )}
            </div>
          </div>

          <div className="pt-3 border-t border-slate-800 text-right">
            <button
              onClick={() => navigate('/investigation')}
              className="text-xs text-cyan-400 hover:text-cyan-300 font-medium inline-flex items-center space-x-1"
            >
              <span>Launch AI Root Cause Investigator</span>
              <ArrowRight className="w-3 h-3" />
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}
