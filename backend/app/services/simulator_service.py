"""
DataPulse AI - Interactive Scenario Simulation Service
Injects realistic operational failure scenarios directly into Exasol Personal
for live judge demonstrations, and provides a deterministic reset-and-reseed mechanism.
"""

from datetime import datetime, timezone
import subprocess
import sys
import uuid
from typing import Any, Dict

from backend.app.core.config import settings
from backend.app.database.exasol_client import exasol_client
from backend.app.models.schemas import SimulationResponse
from backend.app.services.dependency_service import dependency_service


class SimulatorService:
    def trigger_scenario(self, scenario: str, pipeline_id: str = None) -> SimulationResponse:
        """
        Inject a live failure scenario into Exasol Personal.
        """
        scenario = scenario.upper()
        now = datetime.now(timezone.utc)
        now_str = now.strftime("%Y-%m-%d %H:%M:%S")

        if scenario == "MISSING_DATA":
            target_pipeline = pipeline_id or "PIPE_CUST_ORDER"
            p_name = "Customer Order ETL"
            run_id = f"RUN_SIM_{uuid.uuid4().hex[:8].upper()}"
            inc_id = f"INC_SIM_{uuid.uuid4().hex[:8].upper()}"
            chk_id = f"CHK_SIM_{uuid.uuid4().hex[:8].upper()}"

            # 1. Insert degraded run
            run_sql = f"""
                INSERT INTO {settings.EXASOL_SCHEMA}.PIPELINE_RUNS
                (run_id, pipeline_id, start_time, end_time, duration_seconds, status, records_processed, error_count, cpu_usage, memory_usage, retry_count)
                VALUES (
                    '{run_id}', '{target_pipeline}', TIMESTAMP '{now_str}', TIMESTAMP '{now_str}',
                    245.0, 'DEGRADED', 12400, 3, 44.5, 52.0, 1
                )
            """
            exasol_client.execute(run_sql)

            # 2. Insert quality check with severe null spike and completeness drop
            dq_sql = f"""
                INSERT INTO {settings.EXASOL_SCHEMA}.DATA_QUALITY
                (check_id, run_id, pipeline_id, checked_at, completeness_score, freshness_minutes, duplicate_count, null_count, schema_error_count)
                VALUES (
                    '{chk_id}', '{run_id}', '{target_pipeline}', TIMESTAMP '{now_str}',
                    68.5, 18.0, 142, 8420, 0
                )
            """
            exasol_client.execute(dq_sql)

            # 3. Insert Incident
            inc_sql = f"""
                INSERT INTO {settings.EXASOL_SCHEMA}.INCIDENTS
                (incident_id, pipeline_id, run_id, detected_at, incident_type, severity, description, probable_cause, confidence_score, resolution_status)
                VALUES (
                    '{inc_id}', '{target_pipeline}', '{run_id}', TIMESTAMP '{now_str}',
                    'DATA_QUALITY_DEGRADATION', 'HIGH',
                    'Completeness plunged to 68.5% with 8,420 unexpected null values in mandatory order_amount and customer_id fields.',
                    'Upstream e-commerce checkout service database migration produced incomplete payload exports.',
                    0.94, 'OPEN'
                )
            """
            exasol_client.execute(inc_sql)

            # 4. Insert Prediction
            pred_id = f"PRD_SIM_{uuid.uuid4().hex[:8].upper()}"
            pred_sql = f"""
                INSERT INTO {settings.EXASOL_SCHEMA}.PREDICTION_RESULTS
                (prediction_id, pipeline_id, run_id, prediction_time, anomaly_score, failure_risk_score, model_version, explanation)
                VALUES (
                    '{pred_id}', '{target_pipeline}', '{run_id}', TIMESTAMP '{now_str}',
                    0.88, 0.92, 'v1.2-isolation-forest-rules',
                    'Severe drop in data completeness (68.5%) and anomalous null count (+8,420)'
                )
            """
            exasol_client.execute(pred_sql)

            # Calculate downstream impact
            blast = dependency_service.calculate_blast_radius(target_pipeline)

            return SimulationResponse(
                success=True,
                scenario="MISSING_DATA",
                affected_pipeline=f"{p_name} ({target_pipeline})",
                generated_incident_id=inc_id,
                description="Simulated missing data and quality degradation with 8,420 null fields.",
                impacted_downstream_count=len(blast.affected_downstream_pipelines),
                triggered_at=now.isoformat()
            )

        elif scenario == "PIPELINE_DELAY":
            target_pipeline = pipeline_id or "PIPE_INV_SYNC"
            p_name = "Inventory Synchronization"
            run_id = f"RUN_SIM_{uuid.uuid4().hex[:8].upper()}"
            inc_id = f"INC_SIM_{uuid.uuid4().hex[:8].upper()}"
            chk_id = f"CHK_SIM_{uuid.uuid4().hex[:8].upper()}"

            # Insert execution delay
            run_sql = f"""
                INSERT INTO {settings.EXASOL_SCHEMA}.PIPELINE_RUNS
                (run_id, pipeline_id, start_time, end_time, duration_seconds, status, records_processed, error_count, cpu_usage, memory_usage, retry_count)
                VALUES (
                    '{run_id}', '{target_pipeline}', TIMESTAMP '{now_str}', TIMESTAMP '{now_str}',
                    780.0, 'DEGRADED', 89000, 1, 94.8, 89.2, 2
                )
            """
            exasol_client.execute(run_sql)

            dq_sql = f"""
                INSERT INTO {settings.EXASOL_SCHEMA}.DATA_QUALITY
                (check_id, run_id, pipeline_id, checked_at, completeness_score, freshness_minutes, duplicate_count, null_count, schema_error_count)
                VALUES (
                    '{chk_id}', '{run_id}', '{target_pipeline}', TIMESTAMP '{now_str}',
                    99.1, 145.0, 5, 12, 0
                )
            """
            exasol_client.execute(dq_sql)

            inc_sql = f"""
                INSERT INTO {settings.EXASOL_SCHEMA}.INCIDENTS
                (incident_id, pipeline_id, run_id, detected_at, incident_type, severity, description, probable_cause, confidence_score, resolution_status)
                VALUES (
                    '{inc_id}', '{target_pipeline}', '{run_id}', TIMESTAMP '{now_str}',
                    'EXECUTION_DELAY', 'MEDIUM',
                    'Pipeline runtime spiked to 780s (+420% over 150s baseline) causing Freshness SLA breach of 145 mins.',
                    'Exasol warehouse lock contention during peak concurrent analytical BI queries and high CPU throttling (94.8%).',
                    0.89, 'OPEN'
                )
            """
            exasol_client.execute(inc_sql)

            blast = dependency_service.calculate_blast_radius(target_pipeline)

            return SimulationResponse(
                success=True,
                scenario="PIPELINE_DELAY",
                affected_pipeline=f"{p_name} ({target_pipeline})",
                generated_incident_id=inc_id,
                description="Simulated runtime surge to 780s and SLA freshness breach.",
                impacted_downstream_count=len(blast.affected_downstream_pipelines),
                triggered_at=now.isoformat()
            )

        elif scenario == "UPSTREAM_FAILURE":
            target_pipeline = "PIPE_CUST_MASTER"
            p_name = "Customer Master Data"
            run_id = f"RUN_SIM_{uuid.uuid4().hex[:8].upper()}"
            inc_id = f"INC_SIM_{uuid.uuid4().hex[:8].upper()}"
            chk_id = f"CHK_SIM_{uuid.uuid4().hex[:8].upper()}"

            # Insert critical failure in root upstream pipeline
            run_sql = f"""
                INSERT INTO {settings.EXASOL_SCHEMA}.PIPELINE_RUNS
                (run_id, pipeline_id, start_time, end_time, duration_seconds, status, records_processed, error_count, cpu_usage, memory_usage, retry_count)
                VALUES (
                    '{run_id}', '{target_pipeline}', TIMESTAMP '{now_str}', TIMESTAMP '{now_str}',
                    45.0, 'FAILED', 0, 18, 22.0, 31.0, 3
                )
            """
            exasol_client.execute(run_sql)

            dq_sql = f"""
                INSERT INTO {settings.EXASOL_SCHEMA}.DATA_QUALITY
                (check_id, run_id, pipeline_id, checked_at, completeness_score, freshness_minutes, duplicate_count, null_count, schema_error_count)
                VALUES (
                    '{chk_id}', '{run_id}', '{target_pipeline}', TIMESTAMP '{now_str}',
                    0.0, 180.0, 0, 0, 12
                )
            """
            exasol_client.execute(dq_sql)

            inc_sql = f"""
                INSERT INTO {settings.EXASOL_SCHEMA}.INCIDENTS
                (incident_id, pipeline_id, run_id, detected_at, incident_type, severity, description, probable_cause, confidence_score, resolution_status)
                VALUES (
                    '{inc_id}', '{target_pipeline}', '{run_id}', TIMESTAMP '{now_str}',
                    'SCHEMA_MISMATCH', 'CRITICAL',
                    'Customer Master sync aborted with 18 fatal errors: missing target column customer_tax_code_v2.',
                    'Unannounced upstream schema modification in Salesforce CRM REST API endpoint v59.0.',
                    0.98, 'OPEN'
                )
            """
            exasol_client.execute(inc_sql)

            blast = dependency_service.calculate_blast_radius(target_pipeline)

            return SimulationResponse(
                success=True,
                scenario="UPSTREAM_FAILURE",
                affected_pipeline=f"{p_name} ({target_pipeline})",
                generated_incident_id=inc_id,
                description="Simulated upstream root schema failure cascading to all downstream systems.",
                impacted_downstream_count=len(blast.affected_downstream_pipelines),
                triggered_at=now.isoformat()
            )

        else:
            raise ValueError(f"Unknown scenario '{scenario}'. Supported: MISSING_DATA, PIPELINE_DELAY, UPSTREAM_FAILURE")

    def reset_demo(self) -> Dict[str, Any]:
        """
        Reset Exasol database back to the standard deterministic seed dataset.
        """
        # Run init_db and generate_synthetic_data
        cmd1 = [sys.executable, "backend/scripts/init_db.py"]
        cmd2 = [sys.executable, "backend/scripts/generate_synthetic_data.py"]

        res1 = subprocess.run(cmd1, capture_output=True, text=True)
        if res1.returncode != 0:
            raise RuntimeError(f"Database reset failed at init_db: {res1.stderr}")

        res2 = subprocess.run(cmd2, capture_output=True, text=True)
        if res2.returncode != 0:
            raise RuntimeError(f"Database reset failed at generate_synthetic_data: {res2.stderr}")

        return {
            "success": True,
            "message": "Exasol Personal database successfully reset and seeded to baseline demo state.",
            "reset_at": datetime.now(timezone.utc).isoformat()
        }


simulator_service = SimulatorService()
