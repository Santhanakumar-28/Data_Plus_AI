import axios from 'axios';

const api = axios.create({
  baseURL: import.meta.env.VITE_API_URL || '/api',
  timeout: 30000,
  headers: {
    'Content-Type': 'application/json',
  },
});

export const apiService = {
  // System & Exasol Status
  getHealth: () => api.get('/system/health').then(res => res.data),
  getExasolStatus: () => api.get('/system/exasol-status').then(res => res.data),

  // Dashboard
  getOverview: () => api.get('/dashboard/overview').then(res => res.data),
  getTrends: (days = 14) => api.get(`/dashboard/trends?days=${days}`).then(res => res.data),

  // Pipelines
  getPipelines: (params = {}) => {
    const search = new URLSearchParams();
    if (params.status && params.status !== 'ALL') search.append('status', params.status);
    if (params.criticality && params.criticality !== 'ALL') search.append('criticality', params.criticality);
    const qs = search.toString();
    return api.get(`/pipelines${qs ? `?${qs}` : ''}`).then(res => res.data);
  },
  getPipelineDetail: (pipelineId) => api.get(`/pipelines/${pipelineId}`).then(res => res.data),

  // Anomalies & ML
  getAnomalies: (limit = 50) => api.get(`/anomalies?limit=${limit}`).then(res => res.data),
  detectAnomalies: (data = {}) => api.post('/anomalies/detect', data).then(res => res.data),
  getModelEvaluation: () => api.get('/models/evaluation').then(res => res.data),

  // Incidents
  getIncidents: (params = {}) => {
    const search = new URLSearchParams();
    if (params.severity && params.severity !== 'ALL') search.append('severity', params.severity);
    if (params.status && params.status !== 'ALL') search.append('status', params.status);
    if (params.pipelineId) search.append('pipeline_id', params.pipelineId);
    const qs = search.toString();
    return api.get(`/incidents${qs ? `?${qs}` : ''}`).then(res => res.data);
  },
  getIncident: (incidentId) => api.get(`/incidents/${incidentId}`).then(res => res.data),
  updateIncidentStatus: (incidentId, data) => api.patch(`/incidents/${incidentId}/status`, data).then(res => res.data),

  // RCA Investigation
  investigateIncident: (incidentId) => api.get(`/investigation/${incidentId}`).then(res => res.data),

  // Dependencies & Blast Radius
  getDependencyGraph: () => api.get('/dependencies/graph').then(res => res.data),
  getBlastRadius: (pipelineId) => api.get(`/dependencies/blast-radius/${pipelineId}`).then(res => res.data),

  // Demo Simulation
  triggerSimulation: (data) => api.post('/simulation/trigger', data).then(res => res.data),
  resetSimulation: () => api.post('/simulation/reset').then(res => res.data),
};

export default api;
