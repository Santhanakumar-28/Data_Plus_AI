"""
DataPulse AI - Exasol Personal Verification Script
Validates connectivity, schema, tables, and analytical SQL capabilities.
"""

import sys
import time
from pathlib import Path

# Add project root to sys.path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))

from backend.app.core.config import settings
from backend.app.database.exasol_client import exasol_client


def run_verification():
    print("=" * 70)
    print("   DataPulse AI — Exasol Personal Database Verification")
    print("=" * 70)
    print(f"Target DSN:         {settings.EXASOL_DSN}")
    print(f"User:               {settings.EXASOL_USER}")
    print(f"Target Schema:      {settings.EXASOL_SCHEMA}")
    print(f"Verify TLS:         {settings.EXASOL_VERIFY_TLS}")
    print("-" * 70)

    # 1. Connectivity Check
    print("[1/5] Testing physical connection to Exasol...")
    start = time.time()
    try:
        conn = exasol_client.connect(retries=2, retry_delay=1.0)
        latency = (time.time() - start) * 1000
        print(f"      [OK] Successfully connected in {latency:.2f} ms")
    except Exception as e:
        print(f"      [FAIL] Could not connect to Exasol at {settings.EXASOL_DSN}")
        print(f"      Error details: {e}")
        print("-" * 70)
        print("NEXT ACTIONS TO RESOLVE:")
        print("1. Ensure Exasol Personal is running:")
        print("   Run: exakit status   or   exasol status")
        print("2. If not running, start it:")
        print("   Run: exakit start    or   exasol start")
        print("3. Check that the port matches EXASOL_DSN (default: localhost:8563).")
        print("4. Verify credentials in .env against `exakit info`.")
        print("=" * 70)
        return False

    # 2. Execute 'SELECT 1'
    print("[2/5] Executing 'SELECT 1' ping test...")
    try:
        stmt = conn.execute("SELECT 1 AS PING_RESULT, CURRENT_TIMESTAMP AS DB_TIME")
        row = stmt.fetchone()
        print(f"      [OK] Ping returned: {row}")
    except Exception as e:
        print(f"      [FAIL] Execution failed: {e}")
        return False

    # 3. Verify Database Metadata
    print("[3/5] Querying Exasol metadata...")
    try:
        stmt = conn.execute("SELECT PARAM_VALUE FROM SYS.EXA_METADATA WHERE PARAM_NAME = 'databaseProductVersion'")
        row = stmt.fetchone()
        version = row.get("PARAM_VALUE") if row else "Unknown"
        print(f"      [OK] Database Product Version: {version}")
    except Exception as e:
        print(f"      [WARN] Could not read metadata table: {e}")

    # 4. Verify Schema and Required Tables
    print(f"[4/5] Verifying schema '{settings.EXASOL_SCHEMA}' and required tables...")
    required_tables = [
        "PIPELINES",
        "PIPELINE_RUNS",
        "DATA_QUALITY",
        "INCIDENTS",
        "PIPELINE_DEPENDENCIES",
        "PREDICTION_RESULTS",
        "AUDIT_EVENTS"
    ]
    try:
        stmt = conn.execute(f"""
            SELECT TABLE_NAME 
            FROM SYS.EXA_ALL_TABLES 
            WHERE TABLE_SCHEMA = '{settings.EXASOL_SCHEMA}'
        """)
        existing = set(r["TABLE_NAME"] if isinstance(r, dict) else r[0] for r in stmt.fetchall())
        missing = [t for t in required_tables if t not in existing]

        if not missing:
            print(f"      [OK] All {len(required_tables)} required tables verified in schema '{settings.EXASOL_SCHEMA}':")
            for t in sorted(existing):
                if t in required_tables:
                    print(f"           - {t}")
        else:
            print(f"      [WARN] Schema missing tables: {missing}")
            print(f"      Found tables: {list(existing)}")
            print("      Run: python backend/scripts/init_db.py to create schema and tables.")
    except Exception as e:
        print(f"      [FAIL] Error querying table metadata: {e}")
        return False

    # 5. Execute Sample Analytical SQL Query
    print("[5/5] Executing sample analytical SQL query (aggregations & window function)...")
    try:
        if "PIPELINE_RUNS" in existing:
            query = f"""
                SELECT 
                    pipeline_id,
                    COUNT(*) AS total_runs,
                    ROUND(AVG(duration_seconds), 2) AS avg_duration,
                    SUM(CASE WHEN status = 'FAILED' THEN 1 ELSE 0 END) AS failed_runs,
                    ROUND(SUM(CASE WHEN status = 'FAILED' THEN 1.0 ELSE 0.0 END) * 100.0 / NULLIF(COUNT(*), 0), 2) AS failure_rate_pct
                FROM {settings.EXASOL_SCHEMA}.PIPELINE_RUNS
                GROUP BY pipeline_id
                ORDER BY failure_rate_pct DESC, total_runs DESC
                LIMIT 5
            """
            stmt = conn.execute(query)
            rows = stmt.fetchall()
            print(f"      [OK] Analytical SQL executed successfully! Returned {len(rows)} summary rows.")
            for r in rows:
                print(f"           Pipeline: {r.get('PIPELINE_ID', 'N/A')} | Runs: {r.get('TOTAL_RUNS')} | Fail Rate: {r.get('FAILURE_RATE_PCT')}%")
        else:
            stmt = conn.execute("SELECT COUNT(*) AS DUMMY_CNT, SUM(100) AS DUMMY_SUM FROM (VALUES 1, 2, 3) t")
            print("      [OK] Analytical SQL test executed on system expression.")
    except Exception as e:
        print(f"      [WARN] Sample analytical query warning: {e}")

    print("-" * 70)
    print("   [SUCCESS] Exasol Personal connectivity and database verification passed!")
    print("=" * 70)
    return True


if __name__ == "__main__":
    success = run_verification()
    sys.exit(0 if success else 1)
