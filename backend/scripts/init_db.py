"""
DataPulse AI - Database Initialization Script
Executes database/schema.sql on Exasol Personal to establish DATAPULSE schema and tables.
"""

import sys
import re
from pathlib import Path

# Add project root to sys.path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))

from backend.app.core.config import settings
from backend.app.database.exasol_client import exasol_client


def init_database():
    print("=" * 70)
    print("   DataPulse AI — Initializing Exasol Personal Database")
    print("=" * 70)

    schema_file = Path(__file__).resolve().parent.parent.parent / "database" / "schema.sql"
    if not schema_file.exists():
        print(f"[ERROR] Schema file not found at: {schema_file}")
        return False

    print(f"Reading SQL schema from: {schema_file}")
    with open(schema_file, "r", encoding="utf-8") as f:
        sql_content = f.read()

    # Split SQL into individual statements safely
    # Remove SQL single-line comments
    cleaned_sql = re.sub(r"--.*", "", sql_content)
    # Split by semicolon
    statements = [stmt.strip() for stmt in cleaned_sql.split(";") if stmt.strip()]

    print(f"Found {len(statements)} SQL statements to execute.")

    try:
        conn = exasol_client.connect()
        print(f"Connected to Exasol at {settings.EXASOL_DSN}")

        for i, stmt in enumerate(statements, 1):
            # Print brief summary of the statement
            first_line = stmt.strip().split("\n")[0]
            print(f"[{i}/{len(statements)}] Executing: {first_line[:60]}...")
            conn.execute(stmt)

        print("-" * 70)
        print("Verifying created schema and tables...")
        tables_stmt = conn.execute(f"""
            SELECT TABLE_NAME 
            FROM SYS.EXA_ALL_TABLES 
            WHERE TABLE_SCHEMA = '{settings.EXASOL_SCHEMA}'
            ORDER BY TABLE_NAME
        """)
        created_tables = [r["TABLE_NAME"] if isinstance(r, dict) else r[0] for r in tables_stmt.fetchall()]

        print(f"[SUCCESS] Tables in '{settings.EXASOL_SCHEMA}':")
        for table in created_tables:
            print(f"  [OK] {table}")

        print("=" * 70)
        print("Database schema successfully initialized!")
        return True
    except Exception as e:
        print(f"[FAIL] Error initializing database: {e}")
        return False


if __name__ == "__main__":
    success = init_database()
    sys.exit(0 if success else 1)
