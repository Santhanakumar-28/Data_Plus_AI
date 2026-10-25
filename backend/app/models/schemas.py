"""
DataPulse AI - Pydantic Request & Response Models
"""

from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field


# ---------------------------------------------------------------------
# System & Health Models
# ---------------------------------------------------------------------
class HealthResponse(BaseModel):
    status: str
    version: str = "1.0.0"
    timestamp: str
    database: Dict[str, Any]


class ExasolStatusResponse(BaseModel):
    connected: bool
    status: str
    dsn: str
    schema_name: str
    db_version: Optional[str]
    server_time: Optional[str]
    latency_ms: float
    existing_tables: List[str]
    missing_tables: List[str]
    all_tables_verified: bool
    last_check_at: str
    error: Optional[str] = None


# ---------------------------------------------------------------------
# Dashboard Models
# ---------------------------------------------------------------------
class DashboardOverview(BaseModel):
    total_pipelines: int
    healthy_pipelines: int
    warning_pipelines: int
    failed_pipelines: int
    open_incidents: int
    critical_incidents: int
    avg_duration_seconds: float
    avg_data_quality_score: float
    total_runs_evaluated: int
    last_successful_run: Optional[str]
    system_status: str


class TrendPoint(BaseModel):
    date: str
    total_runs: int
    success_runs: int
    failed_runs: int
    degraded_runs: int
    avg_duration: float
    avg_quality: float


class DashboardTrendsResponse(BaseModel):
    trends: List[TrendPoint]
    days: int


# ---------------------------------------------------------------------
# Pipeline Models
# ---------------------------------------------------------------------
class PipelineSummary(BaseModel):
    pipeline_id: str
    pipeline_name: str
    pipeline_type: str
    source_system: str
    destination_system: str
    schedule_type: str
    owner_team: str
    criticality: str
    status: str  # HEALTHY, WARNING, FAILED
    last_run_time: Optional[str]
    last_run_status: Optional[str]
    avg_duration_seconds: float
    failure_rate_pct: float
    avg_completeness_score: float
    open_incidents_count: int


class PipelineRun(BaseModel):
    run_id: str
    pipeline_id: str
    start_time: str
    end_time: Optional[str]
    duration_seconds: Optional[float]
    status: str
    records_processed: int
    error_count: int
    cpu_usage: float
    memory_usage: float
    retry_count: int


class DataQualityCheck(BaseModel):
    check_id: str
    run_id: str
    pipeline_id: str
    checked_at: str
    completeness_score: float
    freshness_minutes: float
    duplicate_count: int
    null_count: int
    schema_error_count: int


class PipelineDependency(BaseModel):
    upstream_pipeline_id: str
    downstream_pipeline_id: str
    dependency_type: str
    upstream_name: Optional[str] = None
    downstream_name: Optional[str] = None


class PipelineDetail(BaseModel):
    pipeline: PipelineSummary
    recent_runs: List[PipelineRun]
    recent_quality: List[DataQualityCheck]
    upstream_dependencies: List[PipelineDependency]
    downstream_dependencies: List[PipelineDependency]


# ---------------------------------------------------------------------
# Incident Models
# ---------------------------------------------------------------------
class Incident(BaseModel):
    incident_id: str
    pipeline_id: str
    pipeline_name: Optional[str] = None
    run_id: Optional[str] = None
    detected_at: str
    incident_type: str
    severity: str
    description: str
    probable_cause: str
    confidence_score: float
    resolution_status: str
    resolved_at: Optional[str] = None


class IncidentUpdateRequest(BaseModel):
    resolution_status: str = Field(..., description="OPEN, ACKNOWLEDGED, INVESTIGATING, RESOLVED")
    actor: str = Field(default="DataEngineer", description="User performing update")
    notes: Optional[str] = Field(default=None, description="Resolution notes")


class InvestigationReport(BaseModel):
    incident_id: str
    pipeline_id: str
    pipeline_name: str
    severity: str
    incident_type: str
    detected_at: str
    status: str
    evidence_points: List[Dict[str, Any]]
    probable_cause: str
    confidence_score: float
    suggested_actions: List[str]
    upstream_culprit: Optional[Dict[str, Any]]
    downstream_impact: List[Dict[str, Any]]
    llm_analysis: Optional[str] = None


# ---------------------------------------------------------------------
# Anomaly & ML Prediction Models
# ---------------------------------------------------------------------
class AnomalyDetectionRequest(BaseModel):
    pipeline_id: Optional[str] = None
    lookback_runs: int = 100


class AnomalyDetectionResult(BaseModel):
    anomalies_detected: int
    scanned_runs: int
    details: List[Dict[str, Any]]
    model_version: str
    executed_at: str


class MLModelEvaluation(BaseModel):
    model_name: str
    precision: float
    recall: float
    f1_score: float
    accuracy: float
    training_samples: int
    test_samples: int
    confusion_matrix: List[List[int]]
    feature_importances: Dict[str, float]


# ---------------------------------------------------------------------
# Dependency Graph Models
# ---------------------------------------------------------------------
class GraphNode(BaseModel):
    id: str
    name: str
    type: str
    criticality: str
    status: str
    owner: str


class GraphEdge(BaseModel):
    source: str
    target: str
    type: str


class DependencyGraphResponse(BaseModel):
    nodes: List[GraphNode]
    edges: List[GraphEdge]


class BlastRadiusReport(BaseModel):
    incident_pipeline_id: str
    incident_pipeline_name: str
    severity: str
    affected_downstream_pipelines: List[Dict[str, Any]]
    affected_business_reports: List[str]
    total_impact_score: float  # 0.0 to 100.0


# ---------------------------------------------------------------------
# Simulation Models
# ---------------------------------------------------------------------
class SimulationTriggerRequest(BaseModel):
    scenario: str = Field(..., description="MISSING_DATA, PIPELINE_DELAY, UPSTREAM_FAILURE")
    pipeline_id: Optional[str] = None


class SimulationResponse(BaseModel):
    success: bool
    scenario: str
    affected_pipeline: str
    generated_incident_id: str
    description: str
    impacted_downstream_count: int
    triggered_at: str
