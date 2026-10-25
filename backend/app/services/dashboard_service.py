"""
DataPulse AI - Dashboard Analytics Service
Executes analytical Exasol SQL queries for operational overviews and time-series trends.
"""

from typing import Dict, List, Optional
from backend.app.core.config import settings
from backend.app.database.exasol_client import exasol_client
from backend.app.models.schemas import DashboardOverview, DashboardTrendsResponse, TrendPoint


class DashboardService:
    @staticmethod
    def get_overview() -> DashboardOverview:
        """
        Executes analytical queries to summarize monitored pipelines, health distribution,
        open incidents, and overall platform data-quality index.
        """
        schema = settings.EXASOL_SCHEMA
        conn = exasol_client.connect()

        # Analytical SQL query retrieving top-level counts and averages
        overview_sql = f"""
            WITH latest_run_status AS (
                SELECT 
                    pipeline_id,
                    status,
                    ROW_NUMBER() OVER (PARTITION BY pipeline_id ORDER BY start_time DESC) AS rn
                FROM {schema}.PIPELINE_RUNS
            ),
            pipeline_health AS (
                SELECT 
                    p.pipeline_id,
                    COALESCE(r.status, 'UNKNOWN') AS current_status
                FROM {schema}.PIPELINES p
                LEFT JOIN latest_run_status r ON p.pipeline_id = r.pipeline_id AND r.rn = 1
            ),
            metrics AS (
                SELECT 
                    ROUND(AVG(duration_seconds), 1) AS avg_duration,
                    COUNT(*) AS total_runs,
                    MAX(CASE WHEN status = 'SUCCESS' THEN end_time END) AS last_success
                FROM {schema}.PIPELINE_RUNS
            ),
            dq_metrics AS (
                SELECT 
                    ROUND(AVG(completeness_score), 1) AS avg_quality
                FROM {schema}.DATA_QUALITY
            ),
            incident_metrics AS (
                SELECT 
                    COUNT(*) AS open_count,
                    SUM(CASE WHEN severity = 'CRITICAL' THEN 1 ELSE 0 END) AS critical_count
                FROM {schema}.INCIDENTS
                WHERE resolution_status != 'RESOLVED'
            )
            SELECT 
                (SELECT COUNT(*) FROM {schema}.PIPELINES) AS total_pipelines,
                (SELECT COUNT(*) FROM pipeline_health WHERE current_status = 'SUCCESS') AS healthy_count,
                (SELECT COUNT(*) FROM pipeline_health WHERE current_status = 'DEGRADED') AS warning_count,
                (SELECT COUNT(*) FROM pipeline_health WHERE current_status = 'FAILED') AS failed_count,
                i.open_count,
                COALESCE(i.critical_count, 0) AS critical_count,
                COALESCE(m.avg_duration, 0.0) AS avg_duration,
                COALESCE(m.total_runs, 0) AS total_runs,
                CAST(m.last_success AS VARCHAR(32)) AS last_success_str,
                COALESCE(d.avg_quality, 100.0) AS avg_quality
            FROM incident_metrics i
            CROSS JOIN metrics m
            CROSS JOIN dq_metrics d
        """

        stmt = conn.execute(overview_sql)
        row = stmt.fetchone() or {}

        total_p = row.get("TOTAL_PIPELINES", 0)
        healthy_p = row.get("HEALTHY_COUNT", 0)
        warning_p = row.get("WARNING_COUNT", 0)
        failed_p = row.get("FAILED_COUNT", 0)
        open_inc = row.get("OPEN_COUNT", 0)
        crit_inc = row.get("CRITICAL_COUNT", 0)
        avg_dur = float(row.get("AVG_DURATION", 0.0))
        total_runs = row.get("TOTAL_RUNS", 0)
        last_succ = row.get("LAST_SUCCESS_STR")
        avg_dq = float(row.get("AVG_QUALITY", 100.0))

        # Determine overall system status
        if failed_p > 0 or crit_inc > 0:
            sys_status = "CRITICAL"
        elif warning_p > 0 or open_inc > 0:
            sys_status = "WARNING"
        else:
            sys_status = "HEALTHY"

        return DashboardOverview(
            total_pipelines=total_p,
            healthy_pipelines=healthy_p,
            warning_pipelines=warning_p,
            failed_pipelines=failed_p,
            open_incidents=open_inc,
            critical_incidents=crit_inc,
            avg_duration_seconds=avg_dur,
            avg_data_quality_score=avg_dq,
            total_runs_evaluated=total_runs,
            last_successful_run=last_succ,
            system_status=sys_status,
        )

    @staticmethod
    def get_trends(days: int = 14) -> DashboardTrendsResponse:
        """
        Executes date-level aggregations on historical executions and quality in Exasol.
        """
        schema = settings.EXASOL_SCHEMA
        conn = exasol_client.connect()

        trends_sql = f"""
            SELECT 
                TO_CHAR(r.start_time, 'YYYY-MM-DD') AS run_date,
                COUNT(*) AS total_runs,
                SUM(CASE WHEN r.status = 'SUCCESS' THEN 1 ELSE 0 END) AS success_runs,
                SUM(CASE WHEN r.status = 'FAILED' THEN 1 ELSE 0 END) AS failed_runs,
                SUM(CASE WHEN r.status = 'DEGRADED' THEN 1 ELSE 0 END) AS degraded_runs,
                ROUND(AVG(r.duration_seconds), 1) AS avg_duration,
                ROUND(AVG(q.completeness_score), 1) AS avg_quality
            FROM {schema}.PIPELINE_RUNS r
            LEFT JOIN {schema}.DATA_QUALITY q ON r.run_id = q.run_id
            WHERE r.start_time >= ADD_DAYS(CURRENT_TIMESTAMP, -{days})
            GROUP BY TO_CHAR(r.start_time, 'YYYY-MM-DD')
            ORDER BY run_date ASC
        """

        stmt = conn.execute(trends_sql)
        rows = stmt.fetchall()

        trend_points = []
        for r in rows:
            trend_points.append(TrendPoint(
                date=str(r.get("RUN_DATE")),
                total_runs=int(r.get("TOTAL_RUNS", 0)),
                success_runs=int(r.get("SUCCESS_RUNS", 0)),
                failed_runs=int(r.get("FAILED_RUNS", 0)),
                degraded_runs=int(r.get("DEGRADED_RUNS", 0)),
                avg_duration=float(r.get("AVG_DURATION", 0.0) or 0.0),
                avg_quality=float(r.get("AVG_QUALITY", 100.0) or 100.0),
            ))

        return DashboardTrendsResponse(trends=trend_points, days=days)


dashboard_service = DashboardService()
