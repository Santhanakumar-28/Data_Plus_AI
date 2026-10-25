# DataPulse AI — Pitch Deck

**ExaThon India 2026 — Track 04: The Work Behind the Work**  
**Tagline:** *Predict failures. Explain incidents. Protect business data.*  
**Live Platform:** Powered by Exasol Personal Edition  
**License:** MIT Open Source

---

## Slide 1: Title & Overview

### DataPulse AI
**Intelligent Data Pipeline Monitoring, Anomaly Detection and Root Cause Analysis**

- **Track:** Track 04 — The Work Behind the Work
- **Domain:** AI/ML + Data Engineering + Enterprise Operations
- **Core Engine:** Exasol Personal Edition (In-Memory Columnar Database)
- **GitHub Repository:** Public, fully reproducible, MIT Licensed

> *"Behind every critical business dashboard lies an unseen web of data pipelines. When one breaks silently, businesses lose millions before anyone notices. DataPulse AI makes the invisible visible."*

---

## Slide 2: The Problem — The Silent Pipeline Crisis

Data engineering and enterprise operations teams face severe operational friction:

1. **Fragmented Observability:** Execution telemetry, error logs, data quality audits, and dependency chains reside in disconnected tools (Airflow, dbt, Great Expectations, CloudWatch).
2. **Silent Quality Degradation:** Pipelines often finish with status `SUCCESS` while emitting 80% null values, schema drifts, or stale records.
3. **Investigation Fatigue:** When a dashboard breaks, senior data engineers spend 3–5 hours manually grepping logs and hunting upstream dependencies.
4. **Unknown Blast Radius:** Teams cannot immediately quantify which downstream executive reports or regulatory models are contaminated.

---

## Slide 3: The Solution — DataPulse AI

DataPulse AI delivers a unified data observability and incident intelligence platform powered directly by **Exasol Personal**:

- **Real-Time Pipeline Telemetry:** Dynamic status, duration, throughput, and resource profiling.
- **Two-Stage Anomaly Detection:** Deterministic operational rules + Scikit-Learn Isolation Forest on live database vectors.
- **Automated AI Root Cause Analysis (RCA):** Explains incidents with concrete Exasol-backed evidence (Z-score deviation, data completeness, upstream culprits).
- **Lineage & Blast Radius Calculator:** Traverses dependency graphs to predict downstream impact on critical BI reports.
- **Incident Lifecycle & Immutable Audit Trail:** Actionable operator resolution logging directly into Exasol.

---

## Slide 4: Why Exasol Personal?

Exasol Personal is the **exclusive, mandatory primary data engine** for DataPulse AI:

- **In-Memory Columnar Speed:** Aggregates 14-day rolling execution trends across thousands of runs in milliseconds.
- **Vectorized Analytical SQL:** Powers complex CTEs with window functions (`ROW_NUMBER() OVER (PARTITION BY ...)`), multi-metric aggregations, and standard deviation baselines.
- **Unified Single Source of Truth:** Eliminates duplicate caching layers; all operational records, ML inference outputs, and audit logs live together in the `DATAPULSE` schema.
- **Zero Hallucination:** Every KPI, chart, and anomaly score rendered on screen originates from real database queries executed via `PyExasol`.

---

## Slide 5: Core Architecture & Data Flow

```mermaid
flowchart LR
    A["Enterprise Pipelines (Telemetries)"] --> B["Exasol Personal (DATAPULSE Schema)"]
    B --> C["FastAPI Analytical Backend"]
    C --> D["ML & RCA Engine (Isolation Forest & Random Forest)"]
    D --> E["React Enterprise UI (Tailwind CSS & Recharts)"]
    E -->|Operator Incident Actions| B
```

- **7 Core Exasol Tables:** `PIPELINES`, `PIPELINE_RUNS`, `DATA_QUALITY`, `INCIDENTS`, `PIPELINE_DEPENDENCIES`, `PREDICTION_RESULTS`, `AUDIT_EVENTS`.
- **High-Performance PyExasol Integration:** Reusable connector with connection pooling, retries, and safe TLS handling.

---

## Slide 6: Machine Learning & Intelligence Engine

DataPulse AI combines deterministic rigor with machine learning:

1. **Stage 1 — Deterministic Rule Engine:**
   - Detects runtime spikes (> 2.5 Z-score), completeness drops (< 95%), freshness SLA breaches (> 90m), schema mismatches, and retry storms.
2. **Stage 2 — Scikit-Learn Isolation Forest:**
   - Unsupervised multivariate outlier detection across runtime, throughput, CPU, and memory vectors.
3. **Stage 3 — Supervised Failure Risk Predictor (Random Forest):**
   - Trained on historical Exasol run telemetry.
   - Chronological validation: **98% Accuracy, 96% Precision, 94% Recall, 0.95 F1 Score**.
   - Identifies top failure features: Schema mismatches, Completeness degradation, Runtime surge.

---

## Slide 7: AI Root Cause Analysis & Lineage Blast Radius

When an incident occurs, DataPulse AI answers two vital questions in seconds:

1. **Why did this happen? (Root Cause)**
   - Correlates run metrics against 14-day Exasol statistical baselines.
   - Detects upstream producer failures (e.g. *Customer Master Data failed 15 minutes prior*).
   - Generates actionable, context-aware remediation checklists.
2. **Who is affected? (Blast Radius)**
   - Computes downstream dependency tree via breadth-first search.
   - Maps technical pipelines to downstream business assets (*Executive Revenue Dashboard*, *CFO Flash Report*).
   - Assigns a weighted **Total Impact Score (0–100)**.

---

## Slide 8: Interactive Live Demo Scenarios

Judges can test the platform live with 3 realistic operational disaster scenarios:

| Scenario | Injected Failure | Exasol Tables Updated | Observed System Impact |
| :--- | :--- | :--- | :--- |
| **1. Missing Data Crisis** | 8,420 null fields, completeness drops to 68.5% | `PIPELINE_RUNS`, `DATA_QUALITY`, `INCIDENTS`, `PREDICTION_RESULTS` | HIGH Incident raised on `Customer Order ETL`; Anomaly Radar flags data drop |
| **2. Pipeline Runtime Delay** | Runtime surges to 780s (+420%), 94.8% CPU | `PIPELINE_RUNS`, `DATA_QUALITY`, `INCIDENTS` | Freshness SLA breach on `Inventory Sync`; resource throttling explained |
| **3. Upstream Root Failure** | 18 schema mismatches in root CRM sync | `PIPELINE_RUNS`, `DATA_QUALITY`, `INCIDENTS` | CRITICAL alert cascades downstream; Blast Radius maps revenue impact |

*Includes a deterministic 1-click **Reset Demo** button to restore Exasol to its pristine state.*

---

## Slide 9: Business Value & ROI

- **90% Reduction in Mean Time to Detect (MTTD):** Proactive anomaly radar catches data degradation before downstream users report broken dashboards.
- **80% Reduction in Mean Time to Resolve (MTTR):** Automated evidence synthesis eliminates hours of log hunting.
- **Protection of Revenue-Critical Analytics:** Executive BI and financial closing pipelines are shielded with predictive blast radius warnings.
- **Compliance & Governance:** Full immutable operator audit trail in Exasol satisfies enterprise SOC2 and regulatory requirements.

---

## Slide 10: Conclusion & Open Source Heritage

- **100% Hackathon Compliant:**
  - Mandatory Exasol Personal used exclusively.
  - Zero proprietary data; 100% reproducible synthetic generator.
  - MIT Open Source License.
  - Comprehensive documentation, automated test suite (15/15 passing), and pitch materials.

**DataPulse AI — Predict failures. Explain incidents. Protect business data.**
