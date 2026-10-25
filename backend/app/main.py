"""
DataPulse AI - Main FastAPI Application
ExaThon India 2026 - Track 04: The Work Behind the Work
"""

from contextlib import asynccontextmanager
import logging
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from backend.app.api.endpoints import router as api_router
from backend.app.core.config import settings
from backend.app.database.exasol_client import exasol_client

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(name)s: %(message)s")
logger = logging.getLogger("datapulse")


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup validation
    logger.info("Initializing DataPulse AI backend...")
    logger.info(f"Connecting to Exasol Personal at {settings.EXASOL_DSN} (schema: {settings.EXASOL_SCHEMA})...")
    status = exasol_client.check_connection()
    if status["connected"]:
        logger.info(f"[OK] Connected to Exasol Personal ({status.get('db_version')}) in {status.get('latency_ms')} ms")
    else:
        logger.warning(f"[WARNING] Exasol connection failed: {status.get('error')}")
    yield
    # Shutdown logic
    logger.info("DataPulse AI backend shutting down...")
    exasol_client.close()


app = FastAPI(
    title=settings.PROJECT_NAME,
    version=settings.VERSION,
    description="DataPulse AI — Intelligent Data Pipeline Monitoring, Anomaly Detection and Root Cause Analysis powered by Exasol Personal.",
    lifespan=lifespan
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount API router
app.include_router(api_router, prefix="/api")


@app.get("/", tags=["Root"])
def root():
    return {
        "project": "DataPulse AI",
        "tagline": "Predict failures. Explain incidents. Protect business data.",
        "hackathon": "ExaThon India 2026 - Track 04: The Work Behind the Work",
        "documentation": "/docs",
        "openapi": "/openapi.json",
        "system_status": "/api/system/exasol-status"
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("backend.app.main:app", host=settings.API_HOST, port=settings.API_PORT, reload=True)
