import React, { useState, useEffect } from 'react';
import { NavLink, Outlet, useLocation } from 'react-router-dom';
import {
  Activity,
  Layers,
  AlertTriangle,
  Search,
  GitFork,
  CheckCircle2,
  PlaySquare,
  Database,
  RefreshCw,
  Server,
  Zap,
  ExternalLink
} from 'lucide-react';
import { apiService } from '../api/client';

export default function Layout() {
  const [exasolStatus, setExasolStatus] = useState(null);
  const [loading, setLoading] = useState(false);
  const [lastUpdated, setLastUpdated] = useState(new Date().toLocaleTimeString());
  const location = useLocation();

  const fetchStatus = async () => {
    try {
      setLoading(true);
      const data = await apiService.getExasolStatus();
      setExasolStatus(data);
      setLastUpdated(new Date().toLocaleTimeString());
    } catch (err) {
      setExasolStatus({
        connected: false,
        error: err.message || 'Connection refused to Exasol Personal',
      });
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchStatus();
    const interval = setInterval(fetchStatus, 15000);
    return () => clearInterval(interval);
  }, []);

  const navItems = [
    { to: '/', label: 'Overview', icon: Activity },
    { to: '/pipelines', label: 'Pipelines', icon: Layers },
    { to: '/anomalies', label: 'Anomaly Radar', icon: AlertTriangle },
    { to: '/investigation', label: 'AI Root Cause', icon: Search },
    { to: '/lineage', label: 'Blast Radius', icon: GitFork },
    { to: '/incidents', label: 'Incidents', icon: CheckCircle2 },
    { to: '/simulator', label: 'Simulator', icon: PlaySquare },
    { to: '/system', label: 'Exasol Health', icon: Database },
  ];

  return (
    <div className="flex h-screen bg-[#070b14] text-slate-100 overflow-hidden font-sans">
      {/* Sidebar */}
      <aside className="w-64 bg-[#0d1424] border-r border-slate-800 flex flex-col flex-shrink-0">
        {/* Brand */}
        <div className="p-5 border-b border-slate-800 flex items-center justify-between">
          <div className="flex items-center space-x-3">
            <div className="w-9 h-9 rounded-lg bg-gradient-to-tr from-cyan-500 to-indigo-600 flex items-center justify-center shadow-lg shadow-cyan-500/20">
              <Zap className="w-5 h-5 text-white" />
            </div>
            <div>
              <div className="font-bold text-lg tracking-tight bg-gradient-to-r from-cyan-400 via-indigo-300 to-white bg-clip-text text-transparent">
                DataPulse AI
              </div>
              <div className="text-[10px] text-cyan-400 font-mono tracking-wider uppercase">
                Exasol Personal Engine
              </div>
            </div>
          </div>
        </div>

        {/* Navigation Links */}
        <nav className="flex-1 px-3 py-4 space-y-1 overflow-y-auto">
          {navItems.map((item) => {
            const Icon = item.icon;
            return (
              <NavLink
                key={item.to}
                to={item.to}
                className={({ isActive }) =>
                  `flex items-center space-x-3 px-3 py-2.5 rounded-lg text-sm font-medium transition-all ${
                    isActive
                      ? 'bg-cyan-500/15 text-cyan-400 border border-cyan-500/30 shadow-sm shadow-cyan-500/10'
                      : 'text-slate-400 hover:text-slate-200 hover:bg-slate-800/60'
                  }`
                }
              >
                <Icon className="w-4 h-4 flex-shrink-0" />
                <span>{item.label}</span>
              </NavLink>
            );
          })}
        </nav>

        {/* Database Sidebar Footer */}
        <div className="p-3 border-t border-slate-800 bg-[#090e1a]/80">
          <div className="bg-slate-900/90 rounded-lg p-2.5 border border-slate-800 text-xs">
            <div className="flex items-center justify-between mb-1.5">
              <span className="text-slate-400 flex items-center space-x-1.5">
                <Server className="w-3.5 h-3.5 text-slate-400" />
                <span className="font-semibold text-slate-300">Exasol Personal</span>
              </span>
              <span
                className={`inline-flex items-center px-1.5 py-0.5 rounded text-[10px] font-semibold ${
                  exasolStatus?.connected
                    ? 'bg-emerald-500/20 text-emerald-400 border border-emerald-500/40'
                    : 'bg-rose-500/20 text-rose-400 border border-rose-500/40'
                }`}
              >
                <span
                  className={`w-1.5 h-1.5 rounded-full mr-1 ${
                    exasolStatus?.connected ? 'bg-emerald-400 animate-pulse' : 'bg-rose-400'
                  }`}
                />
                {exasolStatus?.connected ? 'ONLINE' : 'OFFLINE'}
              </span>
            </div>
            <div className="text-[11px] text-slate-400 font-mono truncate">
              DSN: {exasolStatus?.dsn || '127.0.0.1:8563'}
            </div>
            <div className="text-[11px] text-slate-500 flex justify-between mt-1">
              <span>Schema: {exasolStatus?.schema_name || 'DATAPULSE'}</span>
              <span>{exasolStatus?.latency_ms ? `${exasolStatus.latency_ms}ms` : '--'}</span>
            </div>
          </div>
        </div>
      </aside>

      {/* Main Content Area */}
      <div className="flex-1 flex flex-col min-w-0 overflow-hidden">
        {/* Top Header */}
        <header className="h-16 bg-[#0d1424]/80 backdrop-blur border-b border-slate-800 px-6 flex items-center justify-between z-10">
          <div className="flex items-center space-x-3">
            <h1 className="text-lg font-semibold text-white tracking-tight">
              {navItems.find((n) => n.to === location.pathname)?.label || 'Dashboard'}
            </h1>
            <span className="text-xs px-2 py-0.5 rounded-full bg-slate-800 text-slate-400 border border-slate-700">
              ExaThon Track 04
            </span>
          </div>

          {/* Action Bar */}
          <div className="flex items-center space-x-4">
            {/* Live Exasol Pill */}
            <div
              className={`flex items-center space-x-2 px-3 py-1.5 rounded-full text-xs font-mono border ${
                exasolStatus?.connected
                  ? 'bg-emerald-950/40 border-emerald-800/60 text-emerald-300'
                  : 'bg-rose-950/40 border-rose-800/60 text-rose-300'
              }`}
            >
              <div
                className={`w-2 h-2 rounded-full ${
                  exasolStatus?.connected ? 'bg-emerald-400 animate-ping' : 'bg-rose-500'
                }`}
              />
              <span className="font-medium">
                {exasolStatus?.connected
                  ? `Exasol Connected (${exasolStatus.db_version || '2026.2.0'})`
                  : 'Exasol Disconnected'}
              </span>
              <span className="text-slate-500">|</span>
              <span className="text-slate-400">
                {exasolStatus?.latency_ms ? `${exasolStatus.latency_ms} ms` : 'N/A'}
              </span>
            </div>

            {/* Refresh Button */}
            <button
              onClick={fetchStatus}
              disabled={loading}
              title="Refresh database connection telemetry"
              className="p-2 rounded-lg bg-slate-800 hover:bg-slate-700 text-slate-300 transition-colors border border-slate-700 flex items-center space-x-1.5 text-xs"
            >
              <RefreshCw className={`w-3.5 h-3.5 ${loading ? 'animate-spin text-cyan-400' : ''}`} />
              <span className="hidden sm:inline">Refresh</span>
            </button>
          </div>
        </header>

        {/* Scrollable Page Outlet */}
        <main className="flex-1 overflow-y-auto p-6 bg-[#070b14]">
          <Outlet context={{ exasolStatus, refreshStatus: fetchStatus }} />
        </main>
      </div>
    </div>
  );
}
