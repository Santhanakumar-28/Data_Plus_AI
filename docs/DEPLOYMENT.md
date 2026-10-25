# DataPulse AI — Deployment Instructions

**ExaThon India 2026 — Track 04: The Work Behind the Work**  
**Target Environments:** Windows 10/11 (WSL2), Linux (Ubuntu/Debian/RHEL), macOS (Docker Desktop)

---

## 1. System Architecture Deployment Model

DataPulse AI consists of three production components:
1. **Database Layer:** Exasol Personal Edition (`docker.io/exasol/nano:2026.2.0-nano.3`) listening on port `8563`.
2. **API Backend:** FastAPI ASGI server listening on port `8000`.
3. **Frontend Dashboard:** React 19 + Vite 8 static application listening on port `5173`.

---

## 2. Containerized Exasol Personal Deployment

Exasol Personal runs as an in-memory single-node container.

### Option A: Using Podman (Recommended on WSL2 / Linux)
```bash
# Pull official Exasol nano image
podman pull docker.io/exasol/nano:2026.2.0-nano.3

# Run container with persistent host port mapping
podman run -d \
  --name exasol-datapulse \
  -p 8563:8563 \
  docker.io/exasol/nano:2026.2.0-nano.3

# Verify container is running
podman ps
```

### Option B: Using Docker Desktop (Windows / macOS)
```bash
docker run -d \
  --name exasol-datapulse \
  -p 8563:8563 \
  docker.io/exasol/nano:2026.2.0-nano.3
```

---

## 3. Environment & Secrets Hardening

Create your production configuration from `.env.example`:
```bash
cp .env.example .env
```

Production `.env` configuration:
```ini
# Exasol Personal Connectivity
EXASOL_DSN=127.0.0.1:8563
EXASOL_USER=sys
EXASOL_PASSWORD=exasol
EXASOL_SCHEMA=DATAPULSE
EXASOL_VERIFY_TLS=False
EXASOL_ENABLED=True

# Server Bindings
HOST=0.0.0.0
PORT=8000
ENVIRONMENT=production
CORS_ORIGINS=http://localhost:5173,http://127.0.0.1:5173

# Optional LLM Integration (OpenAI API key for diagnostic enhancements)
OPENAI_API_KEY=
LLM_MODEL=gpt-4o-mini
```

---

## 4. Automated Database Provisioning

Run schema creation DDL and seed synthetic telemetry:

```bash
# Step 1: Create DATAPULSE schema and 7 relational tables
python backend/scripts/init_db.py

# Step 2: Seed deterministic pipeline catalog, historical runs, and quality indicators
python backend/scripts/generate_synthetic_data.py

# Step 3: Execute diagnostic verification (5/5 checks)
python backend/scripts/test_exasol.py
```

---

## 5. Production Service Execution

### Backend API Server (Uvicorn / Gunicorn)
For production workloads with multiple workers:
```bash
# Using uvicorn with multi-worker concurrency:
python -m uvicorn backend.app.main:app --host 0.0.0.0 --port 8000 --workers 4
```

### Frontend Production Build & Hosting
```bash
cd frontend

# Build optimized static distribution
npm run build

# Preview production build or serve with static server (Nginx, Caddy, or serve):
npm run preview -- --port 5173 --host 0.0.0.0
```

---

## 6. Health Check Endpoints for Monitoring & Orchestration

| Endpoint | Method | Expected Output | Purpose |
| :--- | :---: | :--- | :--- |
| `/api/system/health` | `GET` | `{"status": "UP", ...}` | Liveness & Readiness probe |
| `/api/system/exasol-status` | `GET` | `{"connected": true, "latency_ms": 1.8}` | Exasol socket & table verification |
