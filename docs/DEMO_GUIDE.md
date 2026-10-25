# DataPulse AI — Evaluation & Run Guide

**ExaThon India 2026 — Track 04: The Work Behind the Work**  
**Judge Walkthrough & Verification Manual**

---

## 1. Quick Verification Checklist for Judges

Judges can verify the entire application in under 3 minutes following this guide:

```bash
# 1. Verify Exasol connectivity & analytical SQL
python backend/scripts/test_exasol.py

# 2. Run automated backend integration test suite
python -m pytest backend/tests/test_api.py -v
```

All 15 tests will execute against live Exasol Personal on port `8563` with 100% pass rate.

---

## 2. Running the Full Stack Locally

### Terminal 1: Backend API Server
```powershell
python -m uvicorn backend.app.main:app --host 127.0.0.1 --port 8000 --reload
```
- Swagger API Docs: [http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs)
- Exasol Status Probe: [http://127.0.0.1:8000/api/system/exasol-status](http://127.0.0.1:8000/api/system/exasol-status)

### Terminal 2: React Dashboard
```powershell
cd frontend
npm run dev
```
- Interactive Dashboard: **[http://localhost:5173](http://localhost:5173)**

---

## 3. Interactive Walkthrough Flow (Step-by-Step)

### Step 1: Confirm Database Proof (`/system`)
1. In the sidebar, click **"Exasol Health"**.
2. Notice the top pill: `● Exasol Connected (2026.2.0-nano.3) | 1.8 ms`.
3. Click the **"Execute Database Ping"** button.
4. Review the **5/5 Hackathon Verification Checklist** and the **7 verified schema tables**.
5. Inspect the **Machine Learning Failure Predictor** panel showing 98% accuracy and feature importance weights.

### Step 2: Review Operations Overview (`/`)
1. Click **"Overview"** in the sidebar.
2. Review real-time KPIs: Monitored Pipelines, Active Incidents, Avg Data Quality %, Avg Runtime.
3. Hover over the **14-Day Pipeline Run History** stacked bar chart (Success, Degraded, Failed runs aggregated directly from Exasol fact tables).
4. Review the **Health Distribution Donut** and **Platform Data Quality Index** area chart.

### Step 3: Inspect Pipeline Catalog (`/pipelines`)
1. Click **"Pipelines"** in the sidebar.
2. Use the filter dropdowns to filter by Status (`FAILED`, `WARNING`, `HEALTHY`) or Criticality.
3. Click any pipeline row (e.g. `Customer Order ETL`) to open the **Slide-Over Inspection Drawer**.
4. Switch between the 3 tabs:
   - **Execution Runs:** 50 most recent execution telemetry records with runtime, CPU, and RAM metrics.
   - **Data Quality Audits:** Completeness scores, null counts, freshness latency, and schema errors.
   - **Lineage:** Upstream dependencies and downstream consumers.

### Step 4: Inject Live Failure in Demo Simulator (`/simulator`)
1. Click **"Simulator"** in the sidebar.
2. Under **Scenario 1 ("Missing Data & Quality Drop")**, click **"Trigger Missing Data"**.
3. Watch the live console output write records directly into Exasol tables `PIPELINE_RUNS`, `DATA_QUALITY`, `INCIDENTS`, and `PREDICTION_RESULTS`.
4. Click the button **"Investigate Injected Incident"**.

### Step 5: Perform AI Root Cause Analysis (`/investigation`)
1. Inspect the generated diagnostic report.
2. Notice the **Database Evidence Points** box comparing the incident's run metrics against Exasol's 14-day historical baselines (Z-score deviation).
3. Review the **Diagnostic Narrative** and **Suggested Remediation Protocol**.
4. In the **Incident Lifecycle Action** panel, select `INVESTIGATING` or `RESOLVED`, add notes, and click **"Resolve"**.
5. This writes an immutable audit record to Exasol's `AUDIT_EVENTS` table with full operator attribution.

### Step 6: Map Lineage & Blast Radius (`/lineage`)
1. Click **"Blast Radius"** in the sidebar.
2. Select `PIPE_CUST_MASTER` or `PIPE_CUST_ORDER` from the dropdown.
3. Observe the **Total Impact Score (0–100)** calculated using breadth-first DAG traversal.
4. Review the list of **Affected Downstream Pipelines** and **Impacted Business Systems** (e.g. *Executive Revenue Dashboard*, *CFO Flash Report*).

### Step 7: Idempotent Demo Reset (`/simulator`)
1. Click **"Simulator"** in the sidebar.
2. Click **"Reset Demo Database"** at top right.
3. Confirm in the modal. Exasol is restored back to clean baseline state for the next evaluation.
