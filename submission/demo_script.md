# DataPulse AI — 3-Minute Hackathon Video Demo Script

**ExaThon India 2026 — Track 04: The Work Behind the Work**  
**Tagline:** *Predict failures. Explain incidents. Protect business data.*  
**Presenter:** DataPulse AI Engineering Team  
**Live Target:** Exasol Personal Edition (`docker.io/exasol/nano:2026.2.0-nano.3`)

---

## Video Walkthrough Overview

| Timestamp | Segment Title | Core Visual / UI Action | Spoken Narrative Focus |
| :---: | :--- | :--- | :--- |
| **0:00 – 0:30** | The Problem | Operations Overview Dashboard | The unseen crisis in modern data pipelines; silent data degradation. |
| **0:30 – 1:00** | Exasol Personal Proof | Exasol Verification Cockpit (`/system`) | Live DSN connection, 7 tables, sub-2ms latency, analytical window queries. |
| **1:00 – 1:45** | Live Disaster Simulation | Demo Simulator (`/simulator`) | Ingesting real-time failure into Exasol; Anomaly Radar alert trigger. |
| **1:45 – 2:30** | AI Root Cause & Blast Radius | AI RCA (`/investigation`) & Lineage (`/lineage`) | Multi-table evidence points, Z-score deviation, downstream report impact. |
| **2:30 – 3:00** | Resolution & Audit Trail | Incident Management (`/incidents`) | Resolving incident with audit logging into Exasol `AUDIT_EVENTS`. |

---

## Segment-by-Segment Script & UI Click Directives

### [0:00 – 0:30] — The Problem: "The Work Behind the Work"
**Screen:** Operations Overview Dashboard (`http://localhost:5173/`)  
**UI Action:** Move cursor across the KPI cards (Monitored Pipelines, Active Incidents, Data Quality Index) and hover over the 14-Day Execution History stacked bar chart.

**Spoken Script:**
> *"Behind every critical business dashboard and executive decision lies an invisible web of data pipelines. But when a pipeline silently degrades—producing millions of null values or breaching freshness SLAs—data teams often find out hours too late, after corrupt figures reach the CFO.*  
> *Welcome to **DataPulse AI**, our submission for ExaThon Track 04: 'The Work Behind the Work'. DataPulse AI is an intelligent data observability, anomaly detection, and root-cause intelligence platform powered entirely by **Exasol Personal**."*

---

### [0:30 – 1:00] — Mandatory Exasol Personal Integration
**Screen:** Exasol System Health Page (`/system`)  
**UI Action:** Click **"Exasol Health"** in the sidebar. Point out the top pill showing `Exasol Connected (v2026.2.0-nano.3) | 1.8 ms`. Click the **"Execute Database Ping"** button. Point to the 5-point verification checklist (All 5 verified) and the 7 verified tables in schema `DATAPULSE`.

**Spoken Script:**
> *"First and foremost: Exasol Personal is our mandatory, exclusive data platform. No SQLite or Postgres substitutes.  
> As you can see in our live Exasol Verification Cockpit, we are connected directly to Exasol Personal running on port 8563.  
> Every single metric you see is computed on the fly in Exasol across 7 core relational tables. When I trigger a database ping, Exasol responds in just 1.8 milliseconds. Our queries execute high-performance Common Table Expressions and window functions like `ROW_NUMBER() OVER (PARTITION BY ...)` to analyze thousands of pipeline runs in real time."*

---

### [1:00 – 1:45] — Live Disaster Simulation & Anomaly Detection
**Screen:** Demo Simulator (`/simulator`) & Anomaly Radar (`/anomalies`)  
**UI Action:** Click **"Simulator"** in the sidebar. Show the 3 realistic disaster scenarios. Click **"Trigger Missing Data"** under Scenario 1. Point to the live event log showing Exasol tables `PIPELINE_RUNS`, `DATA_QUALITY`, `INCIDENTS`, and `PREDICTION_RESULTS` being updated. Click the button **"Investigate Injected Incident"**.

**Spoken Script:**
> *"To prove this isn't static dummy data, let's inject a real operational disaster. In our Demo Simulator, I'll trigger Scenario 1: 'Missing Data & Quality Drop' on our Customer Order ETL pipeline.  
> Instantly, DataPulse AI writes new telemetry records into Exasol. Our two-stage anomaly detection engine—combining deterministic SLA rules with Scikit-Learn Isolation Forest—flags the incident with an anomaly score of 0.88 and 92% failure risk."*

---

### [1:45 – 2:30] — AI Root Cause Analysis & Lineage Blast Radius
**Screen:** AI Root Cause Analysis (`/investigation`) & Blast Radius (`/lineage`)  
**UI Action:** In the Investigation page, scroll through the **Database Evidence Points** box. Point out the runtime deviation Z-score, the completeness drop to 68.5%, and the 8,420 null values compared to the 14-day Exasol baseline. Then click **"Map Impact"** to switch to the Lineage page. Point to the **Total Impact Score (82.5/100)** and the list of impacted business systems.

**Spoken Script:**
> *"Now let's examine the AI Root Cause Investigation report. Instead of forcing engineers to hunt through raw log files, DataPulse AI synthesizes concrete quantitative evidence directly from Exasol:  
> Notice Evidence Point 1: Data completeness plunged to 68.5% with 8,420 null values compared to our 14-day historical baseline of 99.8%.  
> Next, our Lineage Engine computes the downstream Blast Radius: Because Customer Order ETL failed, we see a Total Impact Score of 82.5 out of 100, directly threatening the Executive Revenue Dashboard and Customer Invoicing Portal."*

---

### [2:30 – 3:00] — Resolution, Immutable Audit Trail & Conclusion
**Screen:** Incidents Console (`/incidents`)  
**UI Action:** On the Incident Management page, click **"Update Status"** on the open incident. Change status to `RESOLVED`, type notes: *"Patch deployed for upstream schema migration"*, and click **"Commit Status Update"**. Show the green RESOLVED badge and point out the entry in Exasol's `AUDIT_EVENTS` table.

**Spoken Script:**
> *"Once the data engineer deploys the remediation script, they transition the incident to `RESOLVED` directly in the UI. This update immediately writes an immutable audit record to Exasol's `AUDIT_EVENTS` table with full operator attribution for enterprise compliance.  
> With a single click, judges can also use our 'Reset Demo Database' button to re-seed Exasol back to its pristine state.  
> DataPulse AI predicts failures, explains incidents, and protects business data—powered by the unmatched analytical speed of Exasol Personal. Thank you!"*
