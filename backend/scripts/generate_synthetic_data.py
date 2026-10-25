"""
DataPulse AI - Synthetic Dataset Generator
Generates realistic enterprise pipeline topologies, execution telemetry,
data-quality checks, dependency graphs, and labeled anomaly incidents.
"""

import sys
import argparse
import random
import uuid
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Tuple

import pandas as pd
import numpy as np

# Add project root to sys.path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))

from backend.app.core.config import settings
from backend.app.database.exasol_client import exasol_client

PIPELINE_CATALOG = [
    {
        "pipeline_id": "PIPE_CUST_MASTER",
        "pipeline_name": "Customer Master Data",
        "pipeline_type": "BATCH_CDC",
        "source_system": "Salesforce CRM",
        "destination_system": "Enterprise Data Lake",
        "schedule_type": "HOURLY",
        "owner_team": "Data Platform",
        "criticality": "HIGH",
        "base_duration": 180,  # seconds
        "base_records": 45000,
    },
    {
        "pipeline_id": "PIPE_CUST_ORDER",
        "pipeline_name": "Customer Order ETL",
        "pipeline_type": "STREAM_BATCH",
        "source_system": "Kafka Orders Topic",
        "destination_system": "Exasol Personal Store",
        "schedule_type": "HOURLY",
        "owner_team": "E-Commerce Engineering",
        "criticality": "CRITICAL",
        "base_duration": 420,
        "base_records": 125000,
    },
    {
        "pipeline_id": "PIPE_BILLING_TXN",
        "pipeline_name": "Billing Transactions",
        "pipeline_type": "BATCH_ETL",
        "source_system": "Stripe & Internal Ledger",
        "destination_system": "Financial Data Warehouse",
        "schedule_type": "HOURLY",
        "owner_team": "Finance Platform",
        "criticality": "CRITICAL",
        "base_duration": 360,
        "base_records": 82000,
    },
    {
        "pipeline_id": "PIPE_PAY_RECON",
        "pipeline_name": "Payment Reconciliation",
        "pipeline_type": "BATCH_ETL",
        "source_system": "Banking Clearinghouse",
        "destination_system": "Audit Vault",
        "schedule_type": "DAILY",
        "owner_team": "Risk & Finance",
        "criticality": "CRITICAL",
        "base_duration": 900,
        "base_records": 210000,
    },
    {
        "pipeline_id": "PIPE_FIN_DAILY",
        "pipeline_name": "Finance Daily Reporting",
        "pipeline_type": "ANALYTICAL_AGG",
        "source_system": "Financial Data Warehouse",
        "destination_system": "Tableau & Executive Dashboard",
        "schedule_type": "DAILY",
        "owner_team": "Corporate Finance",
        "criticality": "CRITICAL",
        "base_duration": 720,
        "base_records": 60000,
    },
    {
        "pipeline_id": "PIPE_SUPPLIER_IMP",
        "pipeline_name": "Supplier Data Import",
        "pipeline_type": "FILE_TRANSFER",
        "source_system": "Vendor SFTP Portal",
        "destination_system": "Supply Chain S3",
        "schedule_type": "HOURLY",
        "owner_team": "Procurement Tech",
        "criticality": "MEDIUM",
        "base_duration": 240,
        "base_records": 35000,
    },
    {
        "pipeline_id": "PIPE_LOGISTICS_TRK",
        "pipeline_name": "Logistics Tracking",
        "pipeline_type": "IOT_INGESTION",
        "source_system": "Fleet GPS Telemetry",
        "destination_system": "Operations Kafka",
        "schedule_type": "REALTIME",
        "owner_team": "Logistics Operations",
        "criticality": "HIGH",
        "base_duration": 150,
        "base_records": 350000,
    },
    {
        "pipeline_id": "PIPE_INV_SYNC",
        "pipeline_name": "Inventory Synchronization",
        "pipeline_type": "BATCH_ETL",
        "source_system": "Warehouse ERP",
        "destination_system": "Global Inventory Store",
        "schedule_type": "HOURLY",
        "owner_team": "Supply Chain Engineering",
        "criticality": "HIGH",
        "base_duration": 510,
        "base_records": 160000,
    },
    {
        "pipeline_id": "PIPE_SALES_ANLYT",
        "pipeline_name": "Sales Analytics",
        "pipeline_type": "ANALYTICAL_AGG",
        "source_system": "Exasol Personal Store",
        "destination_system": "Looker Data Hub",
        "schedule_type": "DAILY",
        "owner_team": "Revenue Operations",
        "criticality": "HIGH",
        "base_duration": 480,
        "base_records": 95000,
    },
    {
        "pipeline_id": "PIPE_BI_REFRESH",
        "pipeline_name": "Business Intelligence Refresh",
        "pipeline_type": "SEMANTIC_LAYER",
        "source_system": "Looker Data Hub",
        "destination_system": "PowerBI Reports",
        "schedule_type": "DAILY",
        "owner_team": "Business Intelligence",
        "criticality": "MEDIUM",
        "base_duration": 300,
        "base_records": 40000,
    },
    {
        "pipeline_id": "PIPE_USER_ACT",
        "pipeline_name": "User Activity Ingestion",
        "pipeline_type": "STREAM_CDC",
        "source_system": "Clickstream Kinesis",
        "destination_system": "Behavior Data Lake",
        "schedule_type": "HOURLY",
        "owner_team": "Growth Engineering",
        "criticality": "MEDIUM",
        "base_duration": 210,
        "base_records": 500000,
    },
    {
        "pipeline_id": "PIPE_MKT_ATTR",
        "pipeline_name": "Marketing Campaign Attribution",
        "pipeline_type": "ML_INFERENCE",
        "source_system": "Behavior Data Lake",
        "destination_system": "Ad Platform Connectors",
        "schedule_type": "DAILY",
        "owner_team": "Growth Marketing",
        "criticality": "LOW",
        "base_duration": 650,
        "base_records": 75000,
    },
]

DEPENDENCIES = [
    # upstream -> downstream, type
    ("PIPE_CUST_MASTER", "PIPE_CUST_ORDER", "HARD_BLOCKING"),
    ("PIPE_CUST_ORDER", "PIPE_BILLING_TXN", "HARD_BLOCKING"),
    ("PIPE_BILLING_TXN", "PIPE_PAY_RECON", "HARD_BLOCKING"),
    ("PIPE_PAY_RECON", "PIPE_FIN_DAILY", "HARD_BLOCKING"),
    ("PIPE_CUST_ORDER", "PIPE_SALES_ANLYT", "DATA_FEED"),
    ("PIPE_SALES_ANLYT", "PIPE_BI_REFRESH", "SOFT_TRIGGER"),
    ("PIPE_SUPPLIER_IMP", "PIPE_INV_SYNC", "HARD_BLOCKING"),
    ("PIPE_LOGISTICS_TRK", "PIPE_INV_SYNC", "DATA_FEED"),
    ("PIPE_USER_ACT", "PIPE_MKT_ATTR", "DATA_FEED"),
]


def generate_dataset(days: int = 14, seed: int = 42) -> Tuple[
    pd.DataFrame, pd.DataFrame, pd.DataFrame, pd.DataFrame, pd.DataFrame, pd.DataFrame, pd.DataFrame
]:
    """
    Deterministic generation of synthetic pipeline runs and telemetry.
    """
    np.random.seed(seed)
    random.seed(seed)

    now = datetime.utcnow()
    start_time = now - timedelta(days=days)

    pipelines_rows = []
    runs_rows = []
    dq_rows = []
    incident_rows = []
    dep_rows = []
    pred_rows = []
    audit_rows = []

    # 1. Pipelines
    for p in PIPELINE_CATALOG:
        pipelines_rows.append({
            "pipeline_id": p["pipeline_id"],
            "pipeline_name": p["pipeline_name"],
            "pipeline_type": p["pipeline_type"],
            "source_system": p["source_system"],
            "destination_system": p["destination_system"],
            "schedule_type": p["schedule_type"],
            "owner_team": p["owner_team"],
            "criticality": p["criticality"],
            "created_at": start_time.strftime("%Y-%m-%d %H:%M:%S"),
        })

    # 2. Dependencies
    for up, down, dtype in DEPENDENCIES:
        dep_rows.append({
            "upstream_pipeline_id": up,
            "downstream_pipeline_id": down,
            "dependency_type": dtype
        })

    # 3. Runs & Quality & Incidents
    # Hourly pipelines execute 24 times/day; daily pipelines execute 1 time/day
    intervals = []
    current_ts = start_time
    while current_ts < now:
        intervals.append(current_ts)
        current_ts += timedelta(hours=3)  # Sample every 3 hours for high-fidelity 112 runs per pipeline

    # Deliberate anomaly schedule for reproducible demonstrations
    # 1. Duration Spike in Customer Order ETL (Day -4)
    # 2. Quality Degradation in Billing Transactions (Day -2)
    # 3. Missing Data & Freshness violation in Inventory Sync (Day -1)
    # 4. Critical Upstream Failure in Customer Master Data (Recent hours)

    for p in PIPELINE_CATALOG:
        p_id = p["pipeline_id"]
        base_dur = p["base_duration"]
        base_rec = p["base_records"]
        is_daily = p["schedule_type"] == "DAILY"

        for idx, ts in enumerate(intervals):
            if is_daily and ts.hour not in [3, 4]:
                continue

            run_id = f"RUN_{p_id}_{ts.strftime('%Y%m%d%H%M')}"
            run_start = ts + timedelta(minutes=random.randint(0, 5))

            # Default healthy telemetry
            status = "SUCCESS"
            duration = max(30.0, round(float(np.random.normal(base_dur, base_dur * 0.08)), 2))
            records = max(100, int(np.random.normal(base_rec, base_rec * 0.05)))
            error_count = 0
            cpu_usage = round(float(np.random.uniform(25.0, 65.0)), 2)
            memory_usage = round(float(np.random.uniform(30.0, 70.0)), 2)
            retry_count = 0

            completeness = round(float(np.random.uniform(99.0, 100.0)), 2)
            freshness = round(float(np.random.uniform(5.0, 30.0)), 2)
            duplicates = int(np.random.poisson(3))
            nulls = int(np.random.poisson(12))
            schema_errors = 0

            # Inject targeted anomalies
            # Scenario A: Duration Spike (Customer Order ETL 4 days ago)
            if p_id == "PIPE_CUST_ORDER" and (now - ts).days == 4 and ts.hour in [9, 12]:
                status = "DEGRADED"
                duration = round(base_dur * 3.8, 2)  # 380% baseline
                cpu_usage = 98.40
                memory_usage = 94.20
                retry_count = 2
                inc_id = f"INC_{uuid.uuid4().hex[:8].upper()}"
                incident_rows.append({
                    "incident_id": inc_id,
                    "pipeline_id": p_id,
                    "run_id": run_id,
                    "detected_at": run_start.strftime("%Y-%m-%d %H:%M:%S"),
                    "incident_type": "DURATION_SPIKE",
                    "severity": "HIGH",
                    "description": f"Pipeline execution duration {duration}s exceeded 300% historical baseline.",
                    "probable_cause": "High volume ingestion concurrency and CPU throttling on Kafka consumer.",
                    "confidence_score": 92.50,
                    "resolution_status": "RESOLVED",
                    "resolved_at": (run_start + timedelta(hours=2)).strftime("%Y-%m-%d %H:%M:%S"),
                })

            # Scenario B: Quality Degradation & Schema mismatch (Billing Transactions 2 days ago)
            elif p_id == "PIPE_BILLING_TXN" and (now - ts).days == 2 and ts.hour in [15, 18]:
                status = "DEGRADED"
                completeness = 81.40
                duplicates = 1420
                nulls = 3890
                schema_errors = 18
                error_count = 18
                inc_id = f"INC_{uuid.uuid4().hex[:8].upper()}"
                incident_rows.append({
                    "incident_id": inc_id,
                    "pipeline_id": p_id,
                    "run_id": run_id,
                    "detected_at": run_start.strftime("%Y-%m-%d %H:%M:%S"),
                    "incident_type": "QUALITY_DEGRADATION",
                    "severity": "CRITICAL",
                    "description": "Critical completeness drop to 81.4% with 18 unmapped ledger schema fields.",
                    "probable_cause": "Unannounced upstream Stripe payload schema modification omitting customer tax identifiers.",
                    "confidence_score": 96.00,
                    "resolution_status": "RESOLVED",
                    "resolved_at": (run_start + timedelta(hours=3, minutes=30)).strftime("%Y-%m-%d %H:%M:%S"),
                })

            # Scenario C: Upstream Ingestion Failure (Customer Master Data - Recent hours)
            elif p_id == "PIPE_CUST_MASTER" and (now - ts) < timedelta(hours=10):
                status = "FAILED"
                duration = 45.0
                records = 0
                error_count = 14
                retry_count = 3
                freshness = 240.0
                completeness = 0.0
                inc_id = f"INC_{uuid.uuid4().hex[:8].upper()}"
                incident_rows.append({
                    "incident_id": inc_id,
                    "pipeline_id": p_id,
                    "run_id": run_id,
                    "detected_at": run_start.strftime("%Y-%m-%d %H:%M:%S"),
                    "incident_type": "UPSTREAM_FAILURE",
                    "severity": "CRITICAL",
                    "description": "Salesforce CRM CDC extract failed with HTTP 503 Service Unavailable.",
                    "probable_cause": "Third-party CRM API authentication timeout and gateway rate limiting.",
                    "confidence_score": 98.20,
                    "resolution_status": "OPEN",
                    "resolved_at": None,
                })

            # Scenario D: Missing data & freshness breach (Inventory Sync - 1 day ago)
            elif p_id == "PIPE_INV_SYNC" and (now - ts).days == 1 and ts.hour == 6:
                status = "DEGRADED"
                freshness = 360.0
                records = int(base_rec * 0.12)
                nulls = 1200
                inc_id = f"INC_{uuid.uuid4().hex[:8].upper()}"
                incident_rows.append({
                    "incident_id": inc_id,
                    "pipeline_id": p_id,
                    "run_id": run_id,
                    "detected_at": run_start.strftime("%Y-%m-%d %H:%M:%S"),
                    "incident_type": "FRESHNESS_BREACH",
                    "severity": "HIGH",
                    "description": "Data freshness delay of 360 minutes breached 120-minute SLA threshold.",
                    "probable_cause": "Supplier SFTP batch delivery delay caused downstream inventory sync starvation.",
                    "confidence_score": 94.00,
                    "resolution_status": "INVESTIGATING",
                    "resolved_at": None,
                })

            run_end = run_start + timedelta(seconds=duration)

            runs_rows.append({
                "run_id": run_id,
                "pipeline_id": p_id,
                "start_time": run_start.strftime("%Y-%m-%d %H:%M:%S"),
                "end_time": run_end.strftime("%Y-%m-%d %H:%M:%S"),
                "duration_seconds": duration,
                "status": status,
                "records_processed": records,
                "error_count": error_count,
                "cpu_usage": cpu_usage,
                "memory_usage": memory_usage,
                "retry_count": retry_count
            })

            dq_rows.append({
                "check_id": f"DQ_{run_id}",
                "run_id": run_id,
                "pipeline_id": p_id,
                "checked_at": run_end.strftime("%Y-%m-%d %H:%M:%S"),
                "completeness_score": completeness,
                "freshness_minutes": freshness,
                "duplicate_count": duplicates,
                "null_count": nulls,
                "schema_error_count": schema_errors
            })

            # Prediction score
            # Higher failure risk if degraded or failed
            risk_score = 0.05
            anomaly_score = 0.04
            if status == "FAILED":
                risk_score = 0.95
                anomaly_score = 0.92
            elif status == "DEGRADED":
                risk_score = 0.78
                anomaly_score = 0.81
            elif duration > base_dur * 1.5 or completeness < 95.0:
                risk_score = 0.45
                anomaly_score = 0.52

            pred_rows.append({
                "prediction_id": f"PRD_{run_id}",
                "pipeline_id": p_id,
                "run_id": run_id,
                "prediction_time": run_end.strftime("%Y-%m-%d %H:%M:%S"),
                "anomaly_score": round(anomaly_score, 4),
                "failure_risk_score": round(risk_score, 4),
                "model_version": "v1.2.0-isolation-forest",
                "explanation": f"Telemetry evaluated against {p['pipeline_name']} baseline."
            })

    # Initial audit events
    audit_rows.append({
        "event_id": f"EVT_{uuid.uuid4().hex[:8].upper()}",
        "event_time": (now - timedelta(days=days)).strftime("%Y-%m-%d %H:%M:%S"),
        "actor": "SystemAdmin",
        "action": "SEED_DATASET",
        "entity_type": "CATALOG",
        "entity_id": "DATAPULSE_ALL",
        "event_details": f"Initialized {len(PIPELINE_CATALOG)} monitored pipelines and synthetic baseline history."
    })

    df_pipelines = pd.DataFrame(pipelines_rows)
    df_deps = pd.DataFrame(dep_rows)
    df_runs = pd.DataFrame(runs_rows)
    df_dq = pd.DataFrame(dq_rows)
    df_incidents = pd.DataFrame(incident_rows)
    df_pred = pd.DataFrame(pred_rows)
    df_audit = pd.DataFrame(audit_rows)

    return df_pipelines, df_deps, df_runs, df_dq, df_incidents, df_pred, df_audit


def seed_to_exasol(reset: bool = True, days: int = 14, seed: int = 42):
    print("=" * 70)
    print("   DataPulse AI — Seeding Synthetic Pipeline Data into Exasol")
    print("=" * 70)
    print(f"History window:     {days} days")
    print(f"Random seed:        {seed}")
    print(f"Reset existing:     {reset}")
    print("-" * 70)

    print("Generating deterministic telemetry and causal incident records...")
    df_p, df_deps, df_runs, df_dq, df_inc, df_pred, df_audit = generate_dataset(days=days, seed=seed)

    print(f"  Generated Pipelines:    {len(df_p)}")
    print(f"  Generated Dependencies: {len(df_deps)}")
    print(f"  Generated Runs:         {len(df_runs)}")
    print(f"  Generated DQ Checks:    {len(df_dq)}")
    print(f"  Generated Incidents:    {len(df_inc)}")
    print(f"  Generated Predictions:  {len(df_pred)}")
    print(f"  Generated Audit Events: {len(df_audit)}")
    print("-" * 70)

    conn = exasol_client.connect()
    schema = settings.EXASOL_SCHEMA

    if reset:
        print(f"Resetting existing records in '{schema}' tables...")
        # Order matters due to logical foreign key relationships
        tables_to_clear = [
            "AUDIT_EVENTS",
            "PREDICTION_RESULTS",
            "INCIDENTS",
            "DATA_QUALITY",
            "PIPELINE_RUNS",
            "PIPELINE_DEPENDENCIES",
            "PIPELINES"
        ]
        for tbl in tables_to_clear:
            try:
                conn.execute(f"TRUNCATE TABLE {schema}.{tbl}")
                print(f"  [OK] Truncated {tbl}")
            except Exception as e:
                print(f"  (i) Could not truncate {tbl}: {e}")

    print("Loading data into Exasol tables via PyExasol...")
    # Import in correct dependency order
    conn.import_from_pandas(df_p, (schema, "PIPELINES"))
    print(f"  [OK] Loaded {len(df_p)} PIPELINES")

    conn.import_from_pandas(df_deps, (schema, "PIPELINE_DEPENDENCIES"))
    print(f"  [OK] Loaded {len(df_deps)} PIPELINE_DEPENDENCIES")

    conn.import_from_pandas(df_runs, (schema, "PIPELINE_RUNS"))
    print(f"  [OK] Loaded {len(df_runs)} PIPELINE_RUNS")

    conn.import_from_pandas(df_dq, (schema, "DATA_QUALITY"))
    print(f"  [OK] Loaded {len(df_dq)} DATA_QUALITY records")

    if not df_inc.empty:
        conn.import_from_pandas(df_inc, (schema, "INCIDENTS"))
        print(f"  [OK] Loaded {len(df_inc)} INCIDENTS")

    conn.import_from_pandas(df_pred, (schema, "PREDICTION_RESULTS"))
    print(f"  [OK] Loaded {len(df_pred)} PREDICTION_RESULTS")

    # Rename action column if needed
    df_audit_exasol = df_audit.rename(columns={"action": "ACTION"})
    conn.import_from_pandas(df_audit_exasol, (schema, "AUDIT_EVENTS"))
    print(f"  [OK] Loaded {len(df_audit)} AUDIT_EVENTS")

    print("-" * 70)
    print("Verification count query:")
    count_stmt = conn.execute(f"""
        SELECT 
            (SELECT COUNT(*) FROM {schema}.PIPELINES) AS PIPELINE_COUNT,
            (SELECT COUNT(*) FROM {schema}.PIPELINE_RUNS) AS RUN_COUNT,
            (SELECT COUNT(*) FROM {schema}.DATA_QUALITY) AS DQ_COUNT,
            (SELECT COUNT(*) FROM {schema}.INCIDENTS) AS INCIDENT_COUNT
        FROM DUAL
    """)
    row = count_stmt.fetchone()
    print(f"  Confirmed in Exasol: Pipelines={row['PIPELINE_COUNT']}, Runs={row['RUN_COUNT']}, DQ={row['DQ_COUNT']}, Incidents={row['INCIDENT_COUNT']}")
    print("=" * 70)
    print("Synthetic dataset successfully seeded into Exasol Personal!")
    return True


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Seed synthetic data into Exasol Personal.")
    parser.add_argument("--days", type=int, default=14, help="Historical days of data")
    parser.add_argument("--seed", type=int, default=42, help="Random seed")
    parser.add_argument("--no-reset", action="store_true", help="Do not truncate before inserting")
    args = parser.parse_args()

    seed_to_exasol(reset=not args.no_reset, days=args.days, seed=args.seed)
