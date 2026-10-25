# Exasol Personal Setup & Verification Guide

**Project:** DataPulse AI  
**Hackathon:** ExaThon India 2026 — Track 04: The Work Behind the Work  
**Database:** Exasol Personal Edition (`docker.io/exasol/nano:2026.2.0-nano.3`)

---

## Prerequisites

- **OS:** Windows 10/11 (with WSL2), Linux, or macOS.
- **Runtime:** Python 3.10+ (tested on Python 3.14).
- **Container Engine:** Podman or Docker.

---

## 1. Starting Exasol Personal

If using WSL2 / Linux with Podman:

```bash
# Check if container is already running
podman ps -a

# Start existing Exasol Personal container
podman start exasol-db-b11b26af

# Or run fresh Exasol nano container on port 8563:
podman run -d --name exasol-datapulse -p 8563:8563 docker.io/exasol/nano:2026.2.0-nano.3
```

On Windows, WSL2 automatically forwards port `8563` to `127.0.0.1:8563` on the Windows host.

---

## 2. Environment Configuration

Copy the example configuration:

```bash
cp .env.example .env
```

Ensure `.env` contains:

```ini
EXASOL_DSN=127.0.0.1:8563
EXASOL_USER=sys
EXASOL_PASSWORD=exasol
EXASOL_SCHEMA=DATAPULSE
EXASOL_VERIFY_TLS=False
EXASOL_ENABLED=True
```

---

## 3. Database Initialization & Schema Creation

Initialize the required database schema `DATAPULSE` and create all 7 core tables:

```bash
python backend/scripts/init_db.py
```

Expected output:
```
Connected to Exasol Personal.
Executing schema creation DDL...
Schema 'DATAPULSE' created or verified.
[OK] Table PIPELINES created or verified.
[OK] Table PIPELINE_RUNS created or verified.
[OK] Table DATA_QUALITY created or verified.
[OK] Table INCIDENTS created or verified.
[OK] Table PIPELINE_DEPENDENCIES created or verified.
[OK] Table PREDICTION_RESULTS created or verified.
[OK] Table AUDIT_EVENTS created or verified.
```

---

## 4. Synthetic Telemetry Seeding

Populate the database with realistic business pipelines, execution telemetry, and quality indicators:

```bash
python backend/scripts/generate_synthetic_data.py
```

This seeds:
- 12 realistic enterprise pipelines
- 9 directed upstream/downstream dependencies
- 784 pipeline execution runs
- 784 data quality checks
- 3 active operational incidents
- 784 ML prediction results
- Initial audit event

---

## 5. Connectivity & Analytical SQL Verification

Run the automated diagnostic suite:

```bash
python backend/scripts/test_exasol.py
```

Expected result:
```
[1/5] Testing physical connection to Exasol... [OK]
[2/5] Executing 'SELECT 1' ping test... [OK]
[3/5] Querying Exasol metadata... [OK] (Version: 2026.2.0-nano.3)
[4/5] Verifying schema 'DATAPULSE' and required tables... [OK] (7/7 tables verified)
[5/5] Executing sample analytical SQL query... [OK]
[SUCCESS] Exasol Personal connectivity and database verification passed!
```

---

## 6. Running the Application Test Suite

Validate all 15 API endpoints against live Exasol Personal:

```bash
python -m pytest backend/tests/test_api.py -v
```

All 15 tests will pass against the live database instance.
