"""
DataPulse AI - Incident Management Service
Handles querying, status lifecycle updates, and audit logging for pipeline incidents in Exasol.
"""

from datetime import datetime, timezone
from typing import Any, Dict, List, Optional
import uuid

from backend.app.core.config import settings
from backend.app.database.exasol_client import exasol_client
from backend.app.models.schemas import Incident


class IncidentService:
    def get_incidents(
        self,
        severity: Optional[str] = None,
        status: Optional[str] = None,
        pipeline_id: Optional[str] = None,
        limit: int = 50
    ) -> List[Incident]:
        """
        Query incidents from Exasol with optional filters.
        """
        filters = []
        if severity and severity.upper() != "ALL":
            filters.append(f"i.severity = '{severity.upper()}'")
        if status and status.upper() != "ALL":
            filters.append(f"i.resolution_status = '{status.upper()}'")
        if pipeline_id:
            filters.append(f"i.pipeline_id = '{pipeline_id}'")

        where_clause = ""
        if filters:
            where_clause = "WHERE " + " AND ".join(filters)

        query = f"""
            SELECT 
                i.incident_id,
                i.pipeline_id,
                p.pipeline_name,
                i.run_id,
                i.detected_at,
                i.incident_type,
                i.severity,
                i.description,
                i.probable_cause,
                i.confidence_score,
                i.resolution_status,
                i.resolved_at
            FROM {settings.EXASOL_SCHEMA}.INCIDENTS i
            JOIN {settings.EXASOL_SCHEMA}.PIPELINES p ON i.pipeline_id = p.pipeline_id
            {where_clause}
            ORDER BY i.detected_at DESC
            LIMIT {int(limit)}
        """
        rows = exasol_client.execute_query(query)
        incidents = []
        for r in rows:
            incidents.append(Incident(
                incident_id=r.get("INCIDENT_ID"),
                pipeline_id=r.get("PIPELINE_ID"),
                pipeline_name=r.get("PIPELINE_NAME"),
                run_id=r.get("RUN_ID"),
                detected_at=str(r.get("DETECTED_AT")),
                incident_type=r.get("INCIDENT_TYPE"),
                severity=r.get("SEVERITY"),
                description=r.get("DESCRIPTION"),
                probable_cause=r.get("PROBABLE_CAUSE"),
                confidence_score=float(r.get("CONFIDENCE_SCORE") or 0.0),
                resolution_status=r.get("RESOLUTION_STATUS"),
                resolved_at=str(r.get("RESOLVED_AT")) if r.get("RESOLVED_AT") else None
            ))
        return incidents

    def get_incident_by_id(self, incident_id: str) -> Optional[Incident]:
        incidents = self.get_incidents()
        for inc in incidents:
            if inc.incident_id == incident_id:
                return inc
        
        # Direct query if not in recent 50
        query = f"""
            SELECT 
                i.incident_id,
                i.pipeline_id,
                p.pipeline_name,
                i.run_id,
                i.detected_at,
                i.incident_type,
                i.severity,
                i.description,
                i.probable_cause,
                i.confidence_score,
                i.resolution_status,
                i.resolved_at
            FROM {settings.EXASOL_SCHEMA}.INCIDENTS i
            JOIN {settings.EXASOL_SCHEMA}.PIPELINES p ON i.pipeline_id = p.pipeline_id
            WHERE i.incident_id = '{incident_id}'
        """
        rows = exasol_client.execute_query(query)
        if not rows:
            return None
        r = rows[0]
        return Incident(
            incident_id=r.get("INCIDENT_ID"),
            pipeline_id=r.get("PIPELINE_ID"),
            pipeline_name=r.get("PIPELINE_NAME"),
            run_id=r.get("RUN_ID"),
            detected_at=str(r.get("DETECTED_AT")),
            incident_type=r.get("INCIDENT_TYPE"),
            severity=r.get("SEVERITY"),
            description=r.get("DESCRIPTION"),
            probable_cause=r.get("PROBABLE_CAUSE"),
            confidence_score=float(r.get("CONFIDENCE_SCORE") or 0.0),
            resolution_status=r.get("RESOLUTION_STATUS"),
            resolved_at=str(r.get("RESOLVED_AT")) if r.get("RESOLVED_AT") else None
        )

    def update_incident_status(
        self,
        incident_id: str,
        new_status: str,
        actor: str = "DataEngineer",
        notes: Optional[str] = None
    ) -> Incident:
        """
        Update status in Exasol INCIDENTS table and insert audit log into AUDIT_EVENTS.
        """
        new_status = new_status.upper()
        now_str = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S")

        resolved_clause = ""
        if new_status == "RESOLVED":
            resolved_clause = f", resolved_at = TIMESTAMP '{now_str}'"

        update_sql = f"""
            UPDATE {settings.EXASOL_SCHEMA}.INCIDENTS
            SET resolution_status = '{new_status}'{resolved_clause}
            WHERE incident_id = '{incident_id}'
        """
        exasol_client.execute(update_sql)

        # Insert audit trail
        event_id = f"EVT_{uuid.uuid4().hex[:8].upper()}"
        details = notes or f"Incident status transitioned to {new_status}"
        # Escape quotes in details
        clean_details = details.replace("'", "''")

        audit_sql = f"""
            INSERT INTO {settings.EXASOL_SCHEMA}.AUDIT_EVENTS
            (event_id, event_time, actor, "ACTION", entity_type, entity_id, event_details)
            VALUES (
                '{event_id}',
                TIMESTAMP '{now_str}',
                '{actor}',
                'UPDATE_STATUS_{new_status}',
                'INCIDENT',
                '{incident_id}',
                '{clean_details}'
            )
        """
        exasol_client.execute(audit_sql)

        updated = self.get_incident_by_id(incident_id)
        if not updated:
            raise ValueError(f"Incident {incident_id} not found after update")
        return updated


incident_service = IncidentService()
