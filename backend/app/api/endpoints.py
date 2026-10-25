"""
DataPulse AI - API Endpoints Definition
Exposes RESTful endpoints for dashboard analytics, pipeline telemetry,
anomaly detection, root-cause investigation, blast radius, and demo simulations.
"""

from datetime import datetime, timezone
from typing import Any, Dict, List, Optional
from fastapi import APIRouter, HTTPException, Query, status as http_status

from backend.app.core.config import settings
from backend.app.database.exasol_client import exasol_client
from backend.app.models.schemas import (
    AnomalyDetectionRequest,
    AnomalyDetectionResult,
    BlastRadiusReport,
    DashboardOverview,
    DashboardTrendsResponse,
    DependencyGraphResponse,
    ExasolStatusResponse,
    HealthResponse,
    Incident,
    IncidentUpdateRequest,
    InvestigationReport,
    MLModelEvaluation,
    PipelineDetail,
    PipelineSummary,
    SimulationResponse,
    SimulationTriggerRequest,
)
from backend.app.services.anomaly_service import anomaly_service
from backend.app.services.dashboard_service import dashboard_service
from backend.app.services.dependency_service import dependency_service
from backend.app.services.incident_service import incident_service
from backend.app.services.investigation_service import investigation_service
from backend.app.services.pipeline_service import pipeline_service
from backend.app.services.prediction_service import prediction_service
from backend.app.services.simulator_service import simulator_service

router = APIRouter()


# ---------------------------------------------------------------------
# System & Exasol Verification Endpoints
# ---------------------------------------------------------------------
@router.get("/system/health", response_model=HealthResponse, tags=["System"])
def get_system_health():
    db_status = exasol_client.check_connection()
    return HealthResponse(
        status="UP" if db_status["connected"] else "DEGRADED",
        version="1.0.0",
        timestamp=datetime.now(timezone.utc).isoformat(),
        database=db_status
    )


@router.get("/system/exasol-status", response_model=ExasolStatusResponse, tags=["System"])
def get_exasol_status():
    status_info = exasol_client.check_connection()
    return ExasolStatusResponse(**status_info)


# ---------------------------------------------------------------------
# Dashboard & Analytics Endpoints
# ---------------------------------------------------------------------
@router.get("/dashboard/overview", response_model=DashboardOverview, tags=["Dashboard"])
def get_dashboard_overview():
    try:
        return dashboard_service.get_overview()
    except Exception as e:
        raise HTTPException(
            status_code=http_status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to fetch dashboard overview from Exasol: {str(e)}"
        )


@router.get("/dashboard/trends", response_model=DashboardTrendsResponse, tags=["Dashboard"])
def get_dashboard_trends(days: int = Query(default=14, ge=1, le=90)):
    try:
        return dashboard_service.get_trends(days=days)
    except Exception as e:
        raise HTTPException(
            status_code=http_status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to fetch execution trends from Exasol: {str(e)}"
        )


# ---------------------------------------------------------------------
# Pipeline Explorer Endpoints
# ---------------------------------------------------------------------
@router.get("/pipelines", response_model=List[PipelineSummary], tags=["Pipelines"])
def list_pipelines(
    status_filter: Optional[str] = Query(default=None, alias="status"),
    criticality: Optional[str] = Query(default=None)
):
    try:
        summaries = pipeline_service.list_pipelines()
        if status_filter and status_filter.upper() != "ALL":
            summaries = [p for p in summaries if p.status.upper() == status_filter.upper()]
        if criticality and criticality.upper() != "ALL":
            summaries = [p for p in summaries if p.criticality.upper() == criticality.upper()]
        return summaries
    except Exception as e:
        raise HTTPException(
            status_code=http_status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to query pipelines from Exasol: {str(e)}"
        )


@router.get("/pipelines/{pipeline_id}", response_model=PipelineDetail, tags=["Pipelines"])
def get_pipeline_detail(pipeline_id: str):
    detail = pipeline_service.get_pipeline(pipeline_id)
    if not detail:
        raise HTTPException(
            status_code=http_status.HTTP_404_NOT_FOUND,
            detail=f"Pipeline with ID '{pipeline_id}' not found in Exasol"
        )
    return detail


# ---------------------------------------------------------------------
# Anomaly Detection & ML Endpoints
# ---------------------------------------------------------------------
@router.get("/anomalies", response_model=List[Dict[str, Any]], tags=["Anomalies"])
def get_recent_anomalies(limit: int = Query(default=50, ge=1, le=200)):
    try:
        return anomaly_service.get_recent_anomalies(limit=limit)
    except Exception as e:
        raise HTTPException(
            status_code=http_status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to fetch anomalies from Exasol: {str(e)}"
        )


@router.post("/anomalies/detect", response_model=AnomalyDetectionResult, tags=["Anomalies"])
def trigger_anomaly_detection(req: AnomalyDetectionRequest):
    try:
        return anomaly_service.run_detection(
            pipeline_id=req.pipeline_id,
            lookback_runs=req.lookback_runs
        )
    except Exception as e:
        raise HTTPException(
            status_code=http_status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Anomaly detection execution error: {str(e)}"
        )


@router.get("/models/evaluation", response_model=MLModelEvaluation, tags=["Machine Learning"])
def get_model_evaluation():
    try:
        return prediction_service.get_evaluation()
    except Exception as e:
        raise HTTPException(
            status_code=http_status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to compute model evaluation: {str(e)}"
        )


# ---------------------------------------------------------------------
# Incident & RCA Investigation Endpoints
# ---------------------------------------------------------------------
@router.get("/incidents", response_model=List[Incident], tags=["Incidents"])
def list_incidents(
    severity: Optional[str] = Query(default=None),
    incident_status: Optional[str] = Query(default=None, alias="status"),
    pipeline_id: Optional[str] = Query(default=None),
    limit: int = Query(default=50, ge=1, le=200)
):
    try:
        return incident_service.get_incidents(
            severity=severity,
            status=incident_status,
            pipeline_id=pipeline_id,
            limit=limit
        )
    except Exception as e:
        raise HTTPException(
            status_code=http_status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve incidents from Exasol: {str(e)}"
        )


@router.get("/incidents/{incident_id}", response_model=Incident, tags=["Incidents"])
def get_incident(incident_id: str):
    inc = incident_service.get_incident_by_id(incident_id)
    if not inc:
        raise HTTPException(
            status_code=http_status.HTTP_404_NOT_FOUND,
            detail=f"Incident '{incident_id}' not found"
        )
    return inc


@router.patch("/incidents/{incident_id}/status", response_model=Incident, tags=["Incidents"])
def update_incident_status(incident_id: str, req: IncidentUpdateRequest):
    try:
        return incident_service.update_incident_status(
            incident_id=incident_id,
            new_status=req.resolution_status,
            actor=req.actor,
            notes=req.notes
        )
    except ValueError as ve:
        raise HTTPException(status_code=http_status.HTTP_404_NOT_FOUND, detail=str(ve))
    except Exception as e:
        raise HTTPException(
            status_code=http_status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to update incident in Exasol: {str(e)}"
        )


@router.get("/investigation/{incident_id}", response_model=InvestigationReport, tags=["Investigation"])
def investigate_incident(incident_id: str):
    try:
        return investigation_service.investigate_incident(incident_id)
    except ValueError as ve:
        raise HTTPException(status_code=http_status.HTTP_404_NOT_FOUND, detail=str(ve))
    except Exception as e:
        raise HTTPException(
            status_code=http_status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Investigation failed: {str(e)}"
        )


# ---------------------------------------------------------------------
# Dependency & Blast Radius Endpoints
# ---------------------------------------------------------------------
@router.get("/dependencies/graph", response_model=DependencyGraphResponse, tags=["Dependencies"])
def get_dependency_graph():
    try:
        return dependency_service.get_dependency_graph()
    except Exception as e:
        raise HTTPException(
            status_code=http_status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to fetch dependency graph from Exasol: {str(e)}"
        )


@router.get("/dependencies/blast-radius/{pipeline_id}", response_model=BlastRadiusReport, tags=["Dependencies"])
def calculate_blast_radius(pipeline_id: str):
    try:
        return dependency_service.calculate_blast_radius(pipeline_id)
    except Exception as e:
        raise HTTPException(
            status_code=http_status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to calculate blast radius: {str(e)}"
        )


# ---------------------------------------------------------------------
# Demo Simulation Endpoints
# ---------------------------------------------------------------------
@router.post("/simulation/trigger", response_model=SimulationResponse, tags=["Simulation"])
def trigger_simulation(req: SimulationTriggerRequest):
    try:
        return simulator_service.trigger_scenario(
            scenario=req.scenario,
            pipeline_id=req.pipeline_id
        )
    except ValueError as ve:
        raise HTTPException(status_code=http_status.HTTP_400_BAD_REQUEST, detail=str(ve))
    except Exception as e:
        raise HTTPException(
            status_code=http_status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Simulation scenario failed: {str(e)}"
        )


@router.post("/simulation/reset", tags=["Simulation"])
def reset_simulation():
    try:
        return simulator_service.reset_demo()
    except Exception as e:
        raise HTTPException(
            status_code=http_status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Database reset failed: {str(e)}"
        )
