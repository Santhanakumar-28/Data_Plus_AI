import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import {
  CheckCircle2,
  AlertTriangle,
  Filter,
  Search,
  ArrowRight,
  ShieldAlert,
  Clock,
  RefreshCw,
  Check,
  X,
  FileText
} from 'lucide-react';
import { apiService } from '../api/client';

export default function IncidentsPage() {
  const [incidents, setIncidents] = useState([]);
  const [loading, setLoading] = useState(true);
  const [severityFilter, setSeverityFilter] = useState('ALL');
  const [statusFilter, setStatusFilter] = useState('ALL');
  const [selectedIncident, setSelectedIncident] = useState(null);
  const [newStatus, setNewStatus] = useState('RESOLVED');
  const [actor, setActor] = useState('DataEngineer');
  const [notes, setNotes] = useState('');
  const [updating, setUpdating] = useState(false);

  const navigate = useNavigate();

  const loadIncidents = async () => {
    try {
      setLoading(true);
      const data = await apiService.getIncidents({
        severity: severityFilter,
        status: statusFilter,
        limit: 100
      });
      setIncidents(data || []);
    } catch (err) {
      console.error('Failed to load incidents:', err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadIncidents();
  }, [severityFilter, statusFilter]);

  const handleUpdate = async (e) => {
    e.preventDefault();
    if (!selectedIncident) return;
    try {
      setUpdating(true);
      await apiService.updateIncidentStatus(selectedIncident.incident_id, {
        resolution_status: newStatus,
        actor,
        notes: notes || `Operator set status to ${newStatus}`
      });
      setSelectedIncident(null);
      setNotes('');
      await loadIncidents();
    } catch (err) {
      console.error('Update failed:', err);
    } finally {
      setUpdating(false);
    }
  };

  return (
    <div className="space-y-6">
      {/* Header and Filter Controls */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
        <div>
          <h2 className="text-xl font-bold text-white tracking-tight">Incident Management</h2>
          <p className="text-xs text-slate-400">
            Pipeline failures and data anomalies persisted in Exasol table <code className="text-cyan-400 font-mono">INCIDENTS</code>
          </p>
        </div>

        {/* Filters */}
        <div className="flex flex-wrap items-center gap-3">
          {/* Status Filter */}
          <select
            value={statusFilter}
            onChange={(e) => setStatusFilter(e.target.value)}
            className="px-3 py-1.5 bg-slate-900 border border-slate-700 rounded-lg text-xs text-white focus:outline-none focus:border-cyan-500"
          >
            <option value="ALL">All Statuses</option>
            <option value="OPEN">Open</option>
            <option value="ACKNOWLEDGED">Acknowledged</option>
            <option value="INVESTIGATING">Investigating</option>
            <option value="RESOLVED">Resolved</option>
          </select>

          {/* Severity Filter */}
          <select
            value={severityFilter}
            onChange={(e) => setSeverityFilter(e.target.value)}
            className="px-3 py-1.5 bg-slate-900 border border-slate-700 rounded-lg text-xs text-white focus:outline-none focus:border-cyan-500"
          >
            <option value="ALL">All Severities</option>
            <option value="CRITICAL">Critical</option>
            <option value="HIGH">High</option>
            <option value="MEDIUM">Medium</option>
            <option value="LOW">Low</option>
          </select>

          <button
            onClick={loadIncidents}
            className="p-2 rounded-lg bg-slate-800 hover:bg-slate-700 border border-slate-700 text-slate-300"
            title="Reload from Exasol"
          >
            <RefreshCw className={`w-3.5 h-3.5 ${loading ? 'animate-spin text-cyan-400' : ''}`} />
          </button>
        </div>
      </div>

      {/* Incidents Table */}
      <div className="bg-[#0d1424] border border-slate-800 rounded-xl overflow-hidden shadow-lg">
        <div className="overflow-x-auto">
          <table className="w-full text-left text-xs border-collapse">
            <thead>
              <tr className="bg-slate-900/90 text-slate-400 border-b border-slate-800 font-semibold uppercase tracking-wider text-[11px]">
                <th className="py-3 px-4">Severity</th>
                <th className="py-3 px-4">Incident ID</th>
                <th className="py-3 px-4">Pipeline</th>
                <th className="py-3 px-4">Incident Type</th>
                <th className="py-3 px-4">Detected At</th>
                <th className="py-3 px-4">Description</th>
                <th className="py-3 px-4">Status</th>
                <th className="py-3 px-4 text-right">Actions</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-800/60 text-slate-200">
              {incidents.length === 0 ? (
                <tr>
                  <td colSpan={8} className="py-12 text-center text-slate-500">
                    No incidents found matching the filter criteria.
                  </td>
                </tr>
              ) : (
                incidents.map((inc) => (
                  <tr key={inc.incident_id} className="hover:bg-slate-800/40 transition-colors">
                    <td className="py-3 px-4">
                      <span
                        className={`inline-block px-2 py-0.5 rounded text-[10px] font-bold border ${
                          inc.severity === 'CRITICAL'
                            ? 'bg-rose-950/60 text-rose-300 border-rose-800'
                            : inc.severity === 'HIGH'
                            ? 'bg-amber-950/60 text-amber-300 border-amber-800'
                            : 'bg-blue-950/60 text-blue-300 border-blue-800'
                        }`}
                      >
                        {inc.severity}
                      </span>
                    </td>
                    <td className="py-3 px-4 font-mono text-cyan-400 font-semibold">{inc.incident_id}</td>
                    <td className="py-3 px-4">
                      <div className="font-semibold text-white">{inc.pipeline_name || inc.pipeline_id}</div>
                      <div className="text-[10px] text-slate-500 font-mono">{inc.pipeline_id}</div>
                    </td>
                    <td className="py-3 px-4 text-slate-300">{inc.incident_type}</td>
                    <td className="py-3 px-4 font-mono text-slate-400">{inc.detected_at.substring(0, 19)}</td>
                    <td className="py-3 px-4 max-w-sm truncate text-slate-300">{inc.description}</td>
                    <td className="py-3 px-4">
                      <span
                        className={`inline-flex items-center space-x-1 px-2 py-0.5 rounded text-[10px] font-semibold border ${
                          inc.resolution_status === 'RESOLVED'
                            ? 'bg-emerald-950/50 text-emerald-300 border-emerald-800/60'
                            : inc.resolution_status === 'INVESTIGATING'
                            ? 'bg-indigo-950/50 text-indigo-300 border-indigo-800/60'
                            : 'bg-rose-950/50 text-rose-300 border-rose-800/60'
                        }`}
                      >
                        <span
                          className={`w-1.5 h-1.5 rounded-full ${
                            inc.resolution_status === 'RESOLVED'
                              ? 'bg-emerald-400'
                              : inc.resolution_status === 'INVESTIGATING'
                              ? 'bg-indigo-400'
                              : 'bg-rose-500 animate-pulse'
                          }`}
                        />
                        <span>{inc.resolution_status}</span>
                      </span>
                    </td>
                    <td className="py-3 px-4 text-right">
                      <div className="flex items-center justify-end space-x-2">
                        <button
                          onClick={() => {
                            setSelectedIncident(inc);
                            setNewStatus(inc.resolution_status === 'OPEN' ? 'INVESTIGATING' : 'RESOLVED');
                          }}
                          className="px-2 py-1 bg-slate-800 hover:bg-slate-700 text-slate-200 rounded text-[11px] font-medium transition"
                        >
                          Update Status
                        </button>
                        <button
                          onClick={() => navigate(`/investigation?incident_id=${inc.incident_id}`)}
                          className="px-2 py-1 bg-cyan-950 hover:bg-cyan-900 text-cyan-300 border border-cyan-800 rounded text-[11px] font-medium transition inline-flex items-center space-x-1"
                        >
                          <span>RCA</span>
                          <ArrowRight className="w-3 h-3" />
                        </button>
                      </div>
                    </td>
                  </tr>
                ))
              )}
            </tbody>
          </table>
        </div>
      </div>

      {/* Status Update Modal */}
      {selectedIncident && (
        <div className="fixed inset-0 z-50 bg-black/60 backdrop-blur-sm flex items-center justify-center p-4">
          <div className="bg-[#0d1424] border border-slate-800 rounded-xl max-w-md w-full p-6 shadow-2xl space-y-4">
            <div className="flex items-center justify-between pb-3 border-b border-slate-800">
              <h3 className="text-sm font-bold text-white">Update Incident Status in Exasol</h3>
              <button
                onClick={() => setSelectedIncident(null)}
                className="text-slate-400 hover:text-white"
              >
                <X className="w-4 h-4" />
              </button>
            </div>

            <div className="text-xs text-slate-300 bg-slate-900 p-3 rounded-lg border border-slate-800">
              <div>Incident: <strong className="text-white">{selectedIncident.incident_id}</strong></div>
              <div>Pipeline: <strong className="text-cyan-400">{selectedIncident.pipeline_name || selectedIncident.pipeline_id}</strong></div>
            </div>

            <form onSubmit={handleUpdate} className="space-y-3 text-xs">
              <div>
                <label className="text-slate-400 block mb-1">New Resolution Status:</label>
                <select
                  value={newStatus}
                  onChange={(e) => setNewStatus(e.target.value)}
                  className="w-full p-2 bg-slate-900 border border-slate-700 rounded-lg text-white focus:outline-none focus:border-cyan-500"
                >
                  <option value="OPEN">OPEN</option>
                  <option value="ACKNOWLEDGED">ACKNOWLEDGED</option>
                  <option value="INVESTIGATING">INVESTIGATING</option>
                  <option value="RESOLVED">RESOLVED</option>
                </select>
              </div>

              <div>
                <label className="text-slate-400 block mb-1">Actor (Operator Identity):</label>
                <input
                  type="text"
                  value={actor}
                  onChange={(e) => setActor(e.target.value)}
                  className="w-full p-2 bg-slate-900 border border-slate-700 rounded-lg text-white focus:outline-none focus:border-cyan-500 font-mono"
                  required
                />
              </div>

              <div>
                <label className="text-slate-400 block mb-1">Audit Notes:</label>
                <textarea
                  rows={3}
                  value={notes}
                  onChange={(e) => setNotes(e.target.value)}
                  placeholder="Reason for state transition or resolution steps applied..."
                  className="w-full p-2 bg-slate-900 border border-slate-700 rounded-lg text-white focus:outline-none focus:border-cyan-500 placeholder-slate-500"
                />
              </div>

              <div className="pt-2 flex justify-end space-x-2">
                <button
                  type="button"
                  onClick={() => setSelectedIncident(null)}
                  className="px-3 py-1.5 bg-slate-800 text-slate-300 rounded-lg hover:bg-slate-700 transition"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  disabled={updating}
                  className="px-4 py-1.5 bg-cyan-600 hover:bg-cyan-500 text-white font-medium rounded-lg transition disabled:opacity-50"
                >
                  {updating ? 'Committing to Exasol...' : 'Commit Status Update'}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
}
