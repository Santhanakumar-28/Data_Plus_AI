"""
DataPulse AI - Pipeline Explorer Service
Queries pipeline inventory, status metrics, execution histories, and quality checks from Exasol.
"""

from typing import Dict, List, Optional
from backend.app.core.config import settings
from backend.app.database.exasol_client import exasol_client
from backend.app.models.schemas import (
    DataQualityCheck,
    PipelineDependency,
    PipelineDetail,
    PipelineRun,
    PipelineSummary,
)


class PipelineService:
    @staticmethod
    def list_pipelines() -> List[PipelineSummary]:
        """
        Retrieves all monitored pipelines joined with execution statistics,
        latest run status, failure rates, and active incidents.
        """
        schema = settings.EXASOL_SCHEMA

        sql = f"""
            WITH latest_run AS (
                SELECT 
                    pipeline_id,
                    status,
                    CAST(start_time AS VARCHAR(32)) AS last_run_time,
                    ROW_NUMBER() OVER (PARTITION BY pipeline_id ORDER BY start_time DESC) AS rn
                FROM {schema}.PIPELINE_RUNS
            ),
            run_stats AS (
                SELECT 
                    pipeline_id,
                    ROUND(AVG(duration_seconds), 1) AS avg_duration,
                    COUNT(*) AS total_runs,
                    SUM(CASE WHEN status = 'FAILED' THEN 1 ELSE 0 END) AS failed_runs,
                    ROUND(SUM(CASE WHEN status = 'FAILED' THEN 1.0 ELSE 0.0 END) * 100.0 / NULLIF(COUNT(*), 0), 2) AS failure_rate_pct
                FROM {schema}.PIPELINE_RUNS
                GROUP BY pipeline_id
            ),
            quality_stats AS (
                SELECT 
                    pipeline_id,
                    ROUND(AVG(completeness_score), 1) AS avg_completeness
                FROM {schema}.DATA_QUALITY
                GROUP BY pipeline_id
            ),
            incidents_stats AS (
                SELECT 
                    pipeline_id,
                    COUNT(*) AS open_incidents
                FROM {schema}.INCIDENTS
                WHERE resolution_status != 'RESOLVED'
                GROUP BY pipeline_id
            )
            SELECT 
                p.pipeline_id,
                p.pipeline_name,
                p.pipeline_type,
                p.source_system,
                p.destination_system,
                p.schedule_type,
                p.owner_team,
                p.criticality,
                COALESCE(lr.status, 'UNKNOWN') AS latest_status,
                lr.last_run_time,
                COALESCE(rs.avg_duration, 0.0) AS avg_duration,
                COALESCE(rs.failure_rate_pct, 0.0) AS failure_rate_pct,
                COALESCE(qs.avg_completeness, 100.0) AS avg_completeness,
                COALESCE(ist.open_incidents, 0) AS open_incidents
            FROM {schema}.PIPELINES p
            LEFT JOIN latest_run lr ON p.pipeline_id = lr.pipeline_id AND lr.rn = 1
            LEFT JOIN run_stats rs ON p.pipeline_id = rs.pipeline_id
            LEFT JOIN quality_stats qs ON p.pipeline_id = qs.pipeline_id
            LEFT JOIN incidents_stats ist ON p.pipeline_id = ist.pipeline_id
            ORDER BY 
                ist.open_incidents DESC,
                CASE p.criticality 
                    WHEN 'CRITICAL' THEN 1 
                    WHEN 'HIGH' THEN 2 
                    WHEN 'MEDIUM' THEN 3 
                    ELSE 4 
                END ASC,
                p.pipeline_name ASC
        """

        rows = exasol_client.fetch_all(sql)

        summaries = []
        for r in rows:
            latest_st = str(r.get("LATEST_STATUS", "UNKNOWN"))
            open_inc = int(r.get("OPEN_INCIDENTS", 0))

            if latest_st == "FAILED" or open_inc > 0:
                health_status = "FAILED" if latest_st == "FAILED" else "WARNING"
            elif latest_st == "DEGRADED":
                health_status = "WARNING"
            else:
                health_status = "HEALTHY"

            summaries.append(PipelineSummary(
                pipeline_id=r["PIPELINE_ID"],
                pipeline_name=r["PIPELINE_NAME"],
                pipeline_type=r["PIPELINE_TYPE"],
                source_system=r["SOURCE_SYSTEM"],
                destination_system=r["DESTINATION_SYSTEM"],
                schedule_type=r["SCHEDULE_TYPE"],
                owner_team=r["OWNER_TEAM"],
                criticality=r["CRITICALITY"],
                status=health_status,
                last_run_time=str(r.get("LAST_RUN_TIME")) if r.get("LAST_RUN_TIME") else None,
                last_run_status=latest_st,
                avg_duration_seconds=float(r.get("AVG_DURATION", 0.0)),
                failure_rate_pct=float(r.get("FAILURE_RATE_PCT", 0.0)),
                avg_completeness_score=float(r.get("AVG_COMPLETENESS", 100.0)),
                open_incidents_count=open_inc,
            ))

        return summaries

    @staticmethod
    def get_pipeline(pipeline_id: str) -> Optional[PipelineDetail]:
        """
        Retrieves detailed information, recent runs, quality checks,
        and dependency chains for a single pipeline.
        """
        schema = settings.EXASOL_SCHEMA

        # 1. Pipeline metadata
        pipelines = PipelineService.list_pipelines()
        matched = [p for p in pipelines if p.pipeline_id == pipeline_id]
        if not matched:
            return None
        summary = matched[0]

        # 2. Recent runs (last 50)
        runs_sql = f"""
            SELECT 
                run_id,
                pipeline_id,
                CAST(start_time AS VARCHAR(32)) AS start_time_str,
                CAST(end_time AS VARCHAR(32)) AS end_time_str,
                duration_seconds,
                status,
                records_processed,
                error_count,
                cpu_usage,
                memory_usage,
                retry_count
            FROM {schema}.PIPELINE_RUNS
            WHERE pipeline_id = '{pipeline_id}'
            ORDER BY start_time DESC
            LIMIT 50
        """
        runs_rows = exasol_client.fetch_all(runs_sql)
        recent_runs = [
            PipelineRun(
                run_id=r["RUN_ID"],
                pipeline_id=r["PIPELINE_ID"],
                start_time=r["START_TIME_STR"],
                end_time=r.get("END_TIME_STR"),
                duration_seconds=float(r["DURATION_SECONDS"]) if r.get("DURATION_SECONDS") is not None else None,
                status=r["STATUS"],
                records_processed=int(r.get("RECORDS_PROCESSED", 0)),
                error_count=int(r.get("ERROR_COUNT", 0)),
                cpu_usage=float(r.get("CPU_USAGE", 0.0)),
                memory_usage=float(r.get("MEMORY_USAGE", 0.0)),
                retry_count=int(r.get("RETRY_COUNT", 0)),
            )
            for r in runs_rows
        ]

        # 3. Recent Data Quality checks (last 50)
        dq_sql = f"""
            SELECT 
                check_id,
                run_id,
                pipeline_id,
                CAST(checked_at AS VARCHAR(32)) AS checked_at_str,
                completeness_score,
                freshness_minutes,
                duplicate_count,
                null_count,
                schema_error_count
            FROM {schema}.DATA_QUALITY
            WHERE pipeline_id = '{pipeline_id}'
            ORDER BY checked_at DESC
            LIMIT 50
        """
        dq_rows = exasol_client.fetch_all(dq_sql)
        recent_quality = [
            DataQualityCheck(
                check_id=r["CHECK_ID"],
                run_id=r["RUN_ID"],
                pipeline_id=r["PIPELINE_ID"],
                checked_at=r["CHECKED_AT_STR"],
                completeness_score=float(r["COMPLETENESS_SCORE"]),
                freshness_minutes=float(r["FRESHNESS_MINUTES"]),
                duplicate_count=int(r.get("DUPLICATE_COUNT", 0)),
                null_count=int(r.get("NULL_COUNT", 0)),
                schema_error_count=int(r.get("SCHEMA_ERROR_COUNT", 0)),
            )
            for r in dq_rows
        ]

        # 4. Upstream dependencies
        up_sql = f"""
            SELECT 
                d.upstream_pipeline_id,
                d.downstream_pipeline_id,
                d.dependency_type,
                p.pipeline_name AS upstream_name
            FROM {schema}.PIPELINE_DEPENDENCIES d
            JOIN {schema}.PIPELINES p ON d.upstream_pipeline_id = p.pipeline_id
            WHERE d.downstream_pipeline_id = '{pipeline_id}'
        """
        up_rows = exasol_client.fetch_all(up_sql)
        upstream_deps = [
            PipelineDependency(
                upstream_pipeline_id=r["UPSTREAM_PIPELINE_ID"],
                downstream_pipeline_id=r["DOWNSTREAM_PIPELINE_ID"],
                dependency_type=r["DEPENDENCY_TYPE"],
                upstream_name=r.get("UPSTREAM_NAME"),
            )
            for r in up_rows
        ]

        # 5. Downstream dependencies
        down_sql = f"""
            SELECT 
                d.upstream_pipeline_id,
                d.downstream_pipeline_id,
                d.dependency_type,
                p.pipeline_name AS downstream_name
            FROM {schema}.PIPELINE_DEPENDENCIES d
            JOIN {schema}.PIPELINES p ON d.downstream_pipeline_id = p.pipeline_id
            WHERE d.upstream_pipeline_id = '{pipeline_id}'
        """
        down_rows = exasol_client.fetch_all(down_sql)
        downstream_deps = [
            PipelineDependency(
                upstream_pipeline_id=r["UPSTREAM_PIPELINE_ID"],
                downstream_pipeline_id=r["DOWNSTREAM_PIPELINE_ID"],
                dependency_type=r["DEPENDENCY_TYPE"],
                downstream_name=r.get("DOWNSTREAM_NAME"),
            )
            for r in down_rows
        ]

        return PipelineDetail(
            pipeline=summary,
            recent_runs=recent_runs,
            recent_quality=recent_quality,
            upstream_dependencies=upstream_deps,
            downstream_dependencies=downstream_deps,
        )


pipeline_service = PipelineService()
