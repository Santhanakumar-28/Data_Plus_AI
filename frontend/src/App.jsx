import React from 'react';
import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import Layout from './components/Layout';
import OverviewPage from './pages/OverviewPage';
import PipelinesPage from './pages/PipelinesPage';
import AnomaliesPage from './pages/AnomaliesPage';
import InvestigationPage from './pages/InvestigationPage';
import LineagePage from './pages/LineagePage';
import IncidentsPage from './pages/IncidentsPage';
import SimulatorPage from './pages/SimulatorPage';
import SystemPage from './pages/SystemPage';

export default function App() {
  return (
    <BrowserRouter>
      <Routes>
        <Route path="/" element={<Layout />}>
          <Route index element={<OverviewPage />} />
          <Route path="pipelines" element={<PipelinesPage />} />
          <Route path="anomalies" element={<AnomaliesPage />} />
          <Route path="investigation" element={<InvestigationPage />} />
          <Route path="lineage" element={<LineagePage />} />
          <Route path="incidents" element={<IncidentsPage />} />
          <Route path="simulator" element={<SimulatorPage />} />
          <Route path="system" element={<SystemPage />} />
          <Route path="*" element={<Navigate to="/" replace />} />
        </Route>
      </Routes>
    </BrowserRouter>
  );
}
