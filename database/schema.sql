-- =====================================================================
-- DataPulse AI — Exasol Personal Database Schema
-- Schema: DATAPULSE
-- Description: Observability tables for pipelines, runs, data quality,
--              incidents, dependencies, predictions and audit events.
-- =====================================================================

CREATE SCHEMA IF NOT EXISTS DATAPULSE;
OPEN SCHEMA DATAPULSE;

-- ---------------------------------------------------------------------
-- 1. PIPELINES: Core catalog of monitored data pipelines
-- ---------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS DATAPULSE.PIPELINES (
    pipeline_id         VARCHAR(64) NOT NULL,
    pipeline_name       VARCHAR(128) NOT NULL,
    pipeline_type       VARCHAR(64) NOT NULL,
    source_system       VARCHAR(128) NOT NULL,
    destination_system  VARCHAR(128) NOT NULL,
    schedule_type       VARCHAR(64) NOT NULL,
    owner_team          VARCHAR(128) NOT NULL,
    criticality         VARCHAR(32) NOT NULL, -- 'CRITICAL', 'HIGH', 'MEDIUM', 'LOW'
    created_at          TIMESTAMP DEFAULT CURRENT_TIMESTAMP NOT NULL,
    CONSTRAINT pk_pipelines PRIMARY KEY (pipeline_id)
);

-- ---------------------------------------------------------------------
-- 2. PIPELINE_RUNS: Historical and real-time execution telemetry
-- ---------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS DATAPULSE.PIPELINE_RUNS (
    run_id              VARCHAR(64) NOT NULL,
    pipeline_id         VARCHAR(64) NOT NULL,
    start_time          TIMESTAMP NOT NULL,
    end_time            TIMESTAMP,
    duration_seconds    DECIMAL(10, 2),
    status              VARCHAR(32) NOT NULL, -- 'SUCCESS', 'FAILED', 'RUNNING', 'DEGRADED'
    records_processed   DECIMAL(18, 0) DEFAULT 0,
    error_count         DECIMAL(9, 0) DEFAULT 0,
    cpu_usage           DECIMAL(5, 2) DEFAULT 0.0,
    memory_usage        DECIMAL(5, 2) DEFAULT 0.0,
    retry_count         DECIMAL(9, 0) DEFAULT 0,
    CONSTRAINT pk_pipeline_runs PRIMARY KEY (run_id),
    CONSTRAINT fk_runs_pipeline FOREIGN KEY (pipeline_id) REFERENCES DATAPULSE.PIPELINES(pipeline_id)
);

-- ---------------------------------------------------------------------
-- 3. DATA_QUALITY: Data health and validation metrics per run
-- ---------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS DATAPULSE.DATA_QUALITY (
    check_id            VARCHAR(64) NOT NULL,
    run_id              VARCHAR(64) NOT NULL,
    pipeline_id         VARCHAR(64) NOT NULL,
    checked_at          TIMESTAMP DEFAULT CURRENT_TIMESTAMP NOT NULL,
    completeness_score  DECIMAL(5, 2) NOT NULL, -- 0.00 to 100.00%
    freshness_minutes   DECIMAL(10, 2) NOT NULL,
    duplicate_count     DECIMAL(12, 0) DEFAULT 0,
    null_count          DECIMAL(12, 0) DEFAULT 0,
    schema_error_count  DECIMAL(9, 0) DEFAULT 0,
    CONSTRAINT pk_data_quality PRIMARY KEY (check_id),
    CONSTRAINT fk_dq_run FOREIGN KEY (run_id) REFERENCES DATAPULSE.PIPELINE_RUNS(run_id),
    CONSTRAINT fk_dq_pipeline FOREIGN KEY (pipeline_id) REFERENCES DATAPULSE.PIPELINES(pipeline_id)
);

-- ---------------------------------------------------------------------
-- 4. INCIDENTS: Pipeline degradation, failure and anomaly incidents
-- ---------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS DATAPULSE.INCIDENTS (
    incident_id         VARCHAR(64) NOT NULL,
    pipeline_id         VARCHAR(64) NOT NULL,
    run_id              VARCHAR(64),
    detected_at         TIMESTAMP DEFAULT CURRENT_TIMESTAMP NOT NULL,
    incident_type       VARCHAR(64) NOT NULL, -- 'DURATION_SPIKE', 'QUALITY_DEGRADATION', 'UPSTREAM_FAILURE', 'SCHEMA_MISMATCH', 'RETRY_STORM'
    severity            VARCHAR(32) NOT NULL, -- 'CRITICAL', 'HIGH', 'MEDIUM', 'LOW'
    description         VARCHAR(1000) NOT NULL,
    probable_cause      VARCHAR(1000) NOT NULL,
    confidence_score    DECIMAL(5, 2) NOT NULL, -- 0.00 to 100.00%
    resolution_status   VARCHAR(32) DEFAULT 'OPEN' NOT NULL, -- 'OPEN', 'ACKNOWLEDGED', 'INVESTIGATING', 'RESOLVED'
    resolved_at         TIMESTAMP,
    CONSTRAINT pk_incidents PRIMARY KEY (incident_id),
    CONSTRAINT fk_incidents_pipeline FOREIGN KEY (pipeline_id) REFERENCES DATAPULSE.PIPELINES(pipeline_id)
);

-- ---------------------------------------------------------------------
-- 5. PIPELINE_DEPENDENCIES: Directed lineage graph between pipelines
-- ---------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS DATAPULSE.PIPELINE_DEPENDENCIES (
    upstream_pipeline_id    VARCHAR(64) NOT NULL,
    downstream_pipeline_id  VARCHAR(64) NOT NULL,
    dependency_type         VARCHAR(64) DEFAULT 'HARD_BLOCKING' NOT NULL, -- 'HARD_BLOCKING', 'SOFT_TRIGGER', 'DATA_FEED'
    CONSTRAINT pk_pipeline_deps PRIMARY KEY (upstream_pipeline_id, downstream_pipeline_id),
    CONSTRAINT fk_dep_upstream FOREIGN KEY (upstream_pipeline_id) REFERENCES DATAPULSE.PIPELINES(pipeline_id),
    CONSTRAINT fk_dep_downstream FOREIGN KEY (downstream_pipeline_id) REFERENCES DATAPULSE.PIPELINES(pipeline_id)
);

-- ---------------------------------------------------------------------
-- 6. PREDICTION_RESULTS: ML anomaly scores & failure risk predictions
-- ---------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS DATAPULSE.PREDICTION_RESULTS (
    prediction_id       VARCHAR(64) NOT NULL,
    pipeline_id         VARCHAR(64) NOT NULL,
    run_id              VARCHAR(64),
    prediction_time     TIMESTAMP DEFAULT CURRENT_TIMESTAMP NOT NULL,
    anomaly_score       DECIMAL(5, 4) NOT NULL, -- 0.0000 to 1.0000
    failure_risk_score  DECIMAL(5, 4) NOT NULL, -- 0.0000 to 1.0000
    model_version       VARCHAR(64) NOT NULL,
    explanation         VARCHAR(2000),
    CONSTRAINT pk_predictions PRIMARY KEY (prediction_id),
    CONSTRAINT fk_pred_pipeline FOREIGN KEY (pipeline_id) REFERENCES DATAPULSE.PIPELINES(pipeline_id)
);

-- ---------------------------------------------------------------------
-- 7. AUDIT_EVENTS: Full traceability of actions & simulator runs
-- ---------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS DATAPULSE.AUDIT_EVENTS (
    event_id            VARCHAR(64) NOT NULL,
    event_time          TIMESTAMP DEFAULT CURRENT_TIMESTAMP NOT NULL,
    actor               VARCHAR(128) NOT NULL,
    "ACTION"            VARCHAR(64) NOT NULL, -- 'INCIDENT_ACK', 'INCIDENT_RESOLVE', 'SIMULATE_ANOMALY', 'SEED_DATA'
    entity_type         VARCHAR(64) NOT NULL,
    entity_id           VARCHAR(64) NOT NULL,
    event_details       VARCHAR(2000),
    CONSTRAINT pk_audit_events PRIMARY KEY (event_id)
);
