"""
DataPulse AI - Backend Test Suite
Executes end-to-end integration tests validating all endpoints against live Exasol Personal.
"""

import pytest
from fastapi.testclient import TestClient

from backend.app.main import app

client = TestClient(app)


def test_root():
    response = client.get("/")
    assert response.status_code == 200
    data = response.json()
    assert data["project"] == "DataPulse AI"


def test_health():
    response = client.get("/api/system/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] in ["UP", "DEGRADED"]
    assert "database" in data
    assert data["database"]["connected"] is True


def test_exasol_status():
    response = client.get("/api/system/exasol-status")
    assert response.status_code == 200
    data = response.json()
    assert data["connected"] is True
    assert data["all_tables_verified"] is True
    assert len(data["existing_tables"]) >= 7
    assert data["schema_name"] == "DATAPULSE"
    assert data["latency_ms"] > 0


def test_dashboard_overview():
    response = client.get("/api/dashboard/overview")
    assert response.status_code == 200
    data = response.json()
    assert data["total_pipelines"] >= 10
    assert data["total_runs_evaluated"] > 100
    assert data["avg_data_quality_score"] > 0


def test_dashboard_trends():
    response = client.get("/api/dashboard/trends?days=14")
    assert response.status_code == 200
    data = response.json()
    assert len(data["trends"]) > 0
    assert "date" in data["trends"][0]
    assert "total_runs" in data["trends"][0]


def test_pipelines_list():
    response = client.get("/api/pipelines")
    assert response.status_code == 200
    data = response.json()
    assert len(data) >= 10
    first = data[0]
    assert "pipeline_id" in first
    assert "pipeline_name" in first
    assert "criticality" in first


def test_pipeline_detail():
    response = client.get("/api/pipelines/PIPE_CUST_ORDER")
    assert response.status_code == 200
    data = response.json()
    assert data["pipeline"]["pipeline_id"] == "PIPE_CUST_ORDER"
    assert len(data["recent_runs"]) > 0
    assert len(data["recent_quality"]) > 0


def test_anomalies_list():
    response = client.get("/api/anomalies?limit=20")
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)


def test_anomaly_detection():
    response = client.post("/api/anomalies/detect", json={"lookback_runs": 100})
    assert response.status_code == 200
    data = response.json()
    assert data["scanned_runs"] > 0
    assert "model_version" in data


def test_model_evaluation():
    response = client.get("/api/models/evaluation")
    assert response.status_code == 200
    data = response.json()
    assert data["accuracy"] > 0.70
    assert data["precision"] > 0.70
    assert len(data["confusion_matrix"]) == 2
    assert len(data["feature_importances"]) > 0


def test_incidents_lifecycle():
    # 1. Fetch incidents
    response = client.get("/api/incidents")
    assert response.status_code == 200
    incidents = response.json()
    assert len(incidents) > 0
    target_id = incidents[0]["incident_id"]

    # 2. Update status to INVESTIGATING
    patch_res = client.patch(
        f"/api/incidents/{target_id}/status",
        json={"resolution_status": "INVESTIGATING", "actor": "TestRunner", "notes": "Automated status validation"}
    )
    assert patch_res.status_code == 200
    updated = patch_res.json()
    assert updated["resolution_status"] == "INVESTIGATING"


def test_investigation_report():
    # Fetch an incident
    inc_res = client.get("/api/incidents")
    incidents = inc_res.json()
    target_id = incidents[0]["incident_id"]

    # Request investigation
    inv_res = client.get(f"/api/investigation/{target_id}")
    assert inv_res.status_code == 200
    data = inv_res.json()
    assert data["incident_id"] == target_id
    assert "evidence_points" in data
    assert "suggested_actions" in data
    assert len(data["suggested_actions"]) > 0


def test_dependency_graph():
    response = client.get("/api/dependencies/graph")
    assert response.status_code == 200
    data = response.json()
    assert len(data["nodes"]) >= 10
    assert len(data["edges"]) >= 5


def test_blast_radius():
    response = client.get("/api/dependencies/blast-radius/PIPE_CUST_MASTER")
    assert response.status_code == 200
    data = response.json()
    assert data["incident_pipeline_id"] == "PIPE_CUST_MASTER"
    assert len(data["affected_downstream_pipelines"]) > 0
    assert data["total_impact_score"] > 0


def test_simulation_trigger():
    response = client.post(
        "/api/simulation/trigger",
        json={"scenario": "MISSING_DATA", "pipeline_id": "PIPE_CUST_ORDER"}
    )
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    assert data["scenario"] == "MISSING_DATA"
    assert "generated_incident_id" in data
