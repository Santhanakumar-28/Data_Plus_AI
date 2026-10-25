# DataPulse AI — System Architecture & Design

**ExaThon India 2026 — Track 04: The Work Behind the Work**  
**Project:** DataPulse AI — Intelligent Data Pipeline Monitoring, Anomaly Detection and Root Cause Analysis

---

## 1. System Overview

DataPulse AI is a modern data observability and incident intelligence platform designed to eliminate pipeline blindspots in complex enterprise data architectures.

```mermaid
flowchart TD
    subgraph UI["Frontend (React 19 + Vite + Tailwind CSS)"]
        A1[Operations Dashboard]
        A2[Pipeline Explorer]
        A3[Anomaly Radar]
        A4[AI RCA Investigator]
        A5[Lineage & Blast Radius]
        A6[Incident Console]
        A7[Demo Simulator]
    end

    subgraph API["Backend API (FastAPI + Pydantic v2)"]
        B1["/api/dashboard/*"]
        B2["/api/pipelines/*"]
        B3["/api/anomalies/*"]
        B4["/api/investigation/*"]
        B5["/api/dependencies/*"]
        B6["/api/incidents/*"]
        B7["/api/simulation/*"]
        B8["/api/system/*"]
    end

    subgraph ML["Intelligence & Analysis Engine"]
        C1[Deterministic Rule Engine]
        C2[Scikit-Learn Isolation Forest]
        C3[Random Forest Failure Predictor]
        C4[Graph Blast Radius Calculator]
        C5[AI Root Cause Synthesizer]
    end

    subgraph DB["Primary Storage & Analytics: Exasol Personal"]
        D1[(PIPELINES)]
        D2[(PIPELINE_RUNS)]
        D3[(DATA_QUALITY)]
        D4[(INCIDENTS)]
        D5[(PIPELINE_DEPENDENCIES)]
        D6[(PREDICTION_RESULTS)]
        D7[(AUDIT_EVENTS)]
    end

    UI <-->|RESTful JSON / CORS| API
    API <--> ML
    API <-->|PyExasol / In-Memory Columnar SQL| DB
    ML <-->|Live Feature Vectors & Baselines| DB
```

---

## 2. Component Architecture

### A. Frontend Layer
- **Framework:** React 19 with Vite 8.
- **Styling:** Tailwind CSS (Dark Enterprise Palette — `#0B1120`, `#1E293B`, `#38BDF8`, `#818CF8`).
- **Data Visualization:** Recharts (time-series multi-line graphs, area charts, bar charts, custom gauges).
- **Icons:** Lucide React.
- **Routing:** React Router v7.
- **State & Communication:** Axios with live Exasol ping monitor.

### B. Backend API Layer
- **Framework:** FastAPI with Uvicorn async server.
- **Data Validation:** Pydantic v2 strict models (`schemas.py`).
- **Connection Management:** `exasol_client.py` with exponential backoff, persistent pooling, TLS configuration, and health ping telemetry.
- **Service Modularization:**
  - `dashboard_service.py`: High-performance windowed metrics and historical trend aggregations.
  - `pipeline_service.py`: Pipeline catalog, run histories, and data quality indicators.
  - `anomaly_service.py`: Two-stage deterministic + unsupervised anomaly detection.
  - `prediction_service.py`: Supervised failure risk scoring and model validation metrics.
  - `investigation_service.py`: Multi-source evidence compilation and AI root-cause diagnosis.
  - `dependency_service.py`: DAG traversal, BFS blast radius computation, and affected business reports mapping.
  - `incident_service.py`: Incident lifecycle transitions and immutable audit event logging.
  - `simulator_service.py`: Live failure scenario injection into Exasol.

### C. Primary Database Engine: Exasol Personal
- **Engine Version:** Exasol Personal `2026.2.0-nano.3`.
- **Port:** `8563`.
- **Schema:** `DATAPULSE`.
- **Role:** Mandatory primary database powering all persistence, time-series aggregation, and analytical SQL. No in-memory cache or relational substitutes are used for application data.

---

## 3. Data Flow

### Anomaly Detection & Investigation Flow
```mermaid
sequenceDiagram
    autonumber
    actor Operator as Data Engineer
    participant UI as React Dashboard
    participant API as FastAPI Backend
    participant Engine as ML / RCA Engine
    participant Exa as Exasol Personal

    Operator->>UI: Selects Degraded Pipeline or Incident
    UI->>API: GET /api/investigation/{incident_id}
    API->>Exa: Query Incident details & Run telemetry
    API->>Exa: Execute Analytical SQL for 14-day baseline (AVG, STDDEV)
    API->>Exa: Traverse PIPELINE_DEPENDENCIES for upstream failures
    Exa-->>API: Return baseline metrics and upstream run states
    API->>Engine: Synthesize evidence (Z-score, quality drop, upstream culprit)
    Engine-->>API: Formulate diagnostic explanation & remediation steps
    API-->>UI: Return complete InvestigationReport
    Operator->>UI: Clicks "Acknowledge" or "Resolve"
    UI->>API: PATCH /api/incidents/{incident_id}/status
    API->>Exa: UPDATE INCIDENTS & INSERT INTO AUDIT_EVENTS
    Exa-->>API: Commit transaction
    API-->>UI: Return updated Incident with audit record
```

---

## 4. Security & Compliance
- **Zero Hardcoded Secrets:** Credentials loaded exclusively via `.env` with fallback validation in `backend/app/core/config.py`.
- **Public GitHub Readiness:** Gitignore excludes `.env`, logs, local scratch files, node_modules, and cache files.
- **Immutable Audit Trail:** All operator interventions, status transitions, and notes are appended to `DATAPULSE.AUDIT_EVENTS` with operator attribution and ISO timestamps.
