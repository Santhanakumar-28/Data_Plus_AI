"""
DataPulse AI - Anomaly Detection Service
Combines deterministic statistical rules with Scikit-learn Isolation Forest
to detect operational anomalies in data pipelines using Exasol telemetry.
"""

from datetime import datetime, timezone
from typing import Any, Dict, List, Optional
import numpy as np
import pandas as pd
from sklearn.ensemble import IsolationForest

from backend.app.core.config import settings
from backend.app.database.exasol_client import exasol_client
from backend.app.models.schemas import AnomalyDetectionResult


class AnomalyService:
    def __init__(self):
        self.model_version = "v1.2-isolation-forest-rules"

    def get_recent_anomalies(self, limit: int = 50) -> List[Dict[str, Any]]:
        """
        Fetch recent prediction/anomaly records from Exasol.
        """
        query = f"""
            SELECT 
                pr.prediction_id,
                pr.pipeline_id,
                p.pipeline_name,
                pr.run_id,
                pr.prediction_time,
                pr.anomaly_score,
                pr.failure_risk_score,
                pr.model_version,
                pr.explanation,
                r.duration_seconds,
                r.status as run_status,
                r.records_processed,
                r.error_count
            FROM {settings.EXASOL_SCHEMA}.PREDICTION_RESULTS pr
            JOIN {settings.EXASOL_SCHEMA}.PIPELINES p ON pr.pipeline_id = p.pipeline_id
            LEFT JOIN {settings.EXASOL_SCHEMA}.PIPELINE_RUNS r ON pr.run_id = r.run_id
            WHERE pr.anomaly_score > 0.45 OR pr.failure_risk_score > 0.40
            ORDER BY pr.prediction_time DESC
            LIMIT {int(limit)}
        """
        rows = exasol_client.execute_query(query)
        anomalies = []
        for r in rows:
            anomalies.append({
                "prediction_id": r.get("PREDICTION_ID"),
                "pipeline_id": r.get("PIPELINE_ID"),
                "pipeline_name": r.get("PIPELINE_NAME"),
                "run_id": r.get("RUN_ID"),
                "prediction_time": str(r.get("PREDICTION_TIME")),
                "anomaly_score": float(r.get("ANOMALY_SCORE") or 0.0),
                "failure_risk_score": float(r.get("FAILURE_RISK_SCORE") or 0.0),
                "model_version": r.get("MODEL_VERSION"),
                "explanation": r.get("EXPLANATION"),
                "duration_seconds": float(r.get("DURATION_SECONDS") or 0.0),
                "run_status": r.get("RUN_STATUS"),
                "records_processed": int(r.get("RECORDS_PROCESSED") or 0),
                "error_count": int(r.get("ERROR_COUNT") or 0)
            })
        return anomalies

    def run_detection(self, pipeline_id: Optional[str] = None, lookback_runs: int = 200) -> AnomalyDetectionResult:
        """
        Run two-stage anomaly detection:
        Stage 1: Deterministic rule verification (threshold spikes, missing data, quality drops)
        Stage 2: Unsupervised Scikit-Learn IsolationForest on standardized telemetry vectors
        """
        where_clause = ""
        if pipeline_id:
            where_clause = f"WHERE r.pipeline_id = '{pipeline_id}'"

        # Pull combined execution & quality features from Exasol
        query = f"""
            SELECT 
                r.run_id,
                r.pipeline_id,
                p.pipeline_name,
                r.start_time,
                r.duration_seconds,
                r.status,
                r.records_processed,
                r.error_count,
                r.cpu_usage,
                r.memory_usage,
                r.retry_count,
                COALESCE(dq.completeness_score, 100.0) as completeness_score,
                COALESCE(dq.freshness_minutes, 15.0) as freshness_minutes,
                COALESCE(dq.duplicate_count, 0) as duplicate_count,
                COALESCE(dq.null_count, 0) as null_count,
                COALESCE(dq.schema_error_count, 0) as schema_error_count
            FROM {settings.EXASOL_SCHEMA}.PIPELINE_RUNS r
            JOIN {settings.EXASOL_SCHEMA}.PIPELINES p ON r.pipeline_id = p.pipeline_id
            LEFT JOIN {settings.EXASOL_SCHEMA}.DATA_QUALITY dq ON r.run_id = dq.run_id
            {where_clause}
            ORDER BY r.start_time DESC
            LIMIT {int(lookback_runs)}
        """
        records = exasol_client.execute_query(query)
        if not records:
            return AnomalyDetectionResult(
                anomalies_detected=0,
                scanned_runs=0,
                details=[],
                model_version=self.model_version,
                executed_at=datetime.now(timezone.utc).isoformat()
            )

        df = pd.DataFrame(records)
        df.columns = [c.lower() for c in df.columns]

        # Convert types
        numeric_cols = [
            "duration_seconds", "records_processed", "error_count", 
            "cpu_usage", "memory_usage", "retry_count",
            "completeness_score", "freshness_minutes", "duplicate_count", "null_count", "schema_error_count"
        ]
        for col in numeric_cols:
            if col in df.columns:
                df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0)

        # 1. Deterministic Rule Engine
        detected_details: List[Dict[str, Any]] = []

        # Compute pipeline-specific baseline means and std
        means = df.groupby('pipeline_id')[['duration_seconds', 'completeness_score']].transform('mean')
        stds = df.groupby('pipeline_id')[['duration_seconds', 'completeness_score']].transform('std').fillna(1.0)
        stds.replace(0.0, 1.0, inplace=True)

        df['duration_zscore'] = (df['duration_seconds'] - means['duration_seconds']) / stds['duration_seconds']
        
        # Fit Isolation Forest on numeric feature matrix
        feature_cols = [
            "duration_seconds", "records_processed", "error_count",
            "cpu_usage", "memory_usage", "completeness_score", 
            "freshness_minutes", "duplicate_count", "null_count"
        ]
        X = df[feature_cols].copy()
        
        # If sufficient sample size, train IsolationForest
        if len(df) >= 10:
            iso = IsolationForest(n_estimators=100, contamination=0.08, random_state=42)
            preds = iso.fit_predict(X)  # -1 for anomaly, 1 for normal
            scores = -iso.score_samples(X)  # Higher is more anomalous
            # Normalize scores to 0.0 - 1.0 range
            min_s, max_s = scores.min(), scores.max()
            if max_s > min_s:
                norm_scores = (scores - min_s) / (max_s - min_s)
            else:
                norm_scores = np.zeros(len(scores))
            df['iforest_anomaly'] = preds == -1
            df['iforest_score'] = norm_scores
        else:
            df['iforest_anomaly'] = False
            df['iforest_score'] = 0.0

        for idx, row in df.iterrows():
            triggers = []
            anomaly_score = float(row.get('iforest_score', 0.0))

            # Rule 1: High error count or failed status
            if row['error_count'] > 0 or row['status'] == 'FAILED':
                triggers.append(f"Execution failed with {int(row['error_count'])} errors")
                anomaly_score = max(anomaly_score, 0.88)

            # Rule 2: Duration spike > 2.5 Z-score
            if row['duration_zscore'] > 2.5 and row['duration_seconds'] > 120:
                triggers.append(f"Duration {row['duration_seconds']:.1f}s is abnormal (+{row['duration_zscore']:.1f} std deviations)")
                anomaly_score = max(anomaly_score, 0.75)

            # Rule 3: Data completeness drop
            if row['completeness_score'] < 95.0:
                triggers.append(f"Data completeness degraded to {row['completeness_score']:.1f}%")
                anomaly_score = max(anomaly_score, 0.70)

            # Rule 4: Data freshness delay
            if row['freshness_minutes'] > 90:
                triggers.append(f"Freshness SLA violated ({row['freshness_minutes']:.0f} mins lag)")
                anomaly_score = max(anomaly_score, 0.65)

            # Rule 5: Schema errors or high null counts
            if row['schema_error_count'] > 0:
                triggers.append(f"Encountered {int(row['schema_error_count'])} unexpected schema mismatches")
                anomaly_score = max(anomaly_score, 0.82)
            elif row['null_count'] > 2500:
                triggers.append(f"Abnormal null value count: {int(row['null_count'])} fields")
                anomaly_score = max(anomaly_score, 0.68)

            # Rule 6: Retry storm
            if row['retry_count'] >= 3:
                triggers.append(f"Excessive retries detected ({int(row['retry_count'])} attempts)")
                anomaly_score = max(anomaly_score, 0.72)

            # Rule 7: Isolation forest detected pattern anomaly
            if row.get('iforest_anomaly') and anomaly_score < 0.50:
                triggers.append(f"Multivariate telemetry deviation detected by Isolation Forest")
                anomaly_score = max(anomaly_score, 0.55)

            if triggers or anomaly_score >= 0.50:
                explanation = " | ".join(triggers) if triggers else "Unsupervised statistical anomaly detected across resource and throughput metrics"
                detected_details.append({
                    "run_id": row['run_id'],
                    "pipeline_id": row['pipeline_id'],
                    "pipeline_name": row['pipeline_name'],
                    "start_time": str(row['start_time']),
                    "anomaly_score": round(float(anomaly_score), 4),
                    "failure_risk_score": round(float(min(1.0, anomaly_score * 1.05)), 4),
                    "triggers": triggers,
                    "explanation": explanation,
                    "metrics": {
                        "duration_seconds": float(row['duration_seconds']),
                        "records_processed": int(row['records_processed']),
                        "error_count": int(row['error_count']),
                        "completeness_score": float(row['completeness_score']),
                        "freshness_minutes": float(row['freshness_minutes']),
                        "null_count": int(row['null_count']),
                        "cpu_usage": float(row['cpu_usage']),
                        "memory_usage": float(row['memory_usage'])
                    }
                })

        return AnomalyDetectionResult(
            anomalies_detected=len(detected_details),
            scanned_runs=len(df),
            details=detected_details,
            model_version=self.model_version,
            executed_at=datetime.now(timezone.utc).isoformat()
        )


anomaly_service = AnomalyService()
