"""
DataPulse AI - Exasol Personal Database Connector
Reusable PyExasol client with connection pooling, retries, TLS handling,
safe execution, and comprehensive health monitoring.
"""

import time
import logging
from typing import Any, Dict, List, Optional, Tuple, Union
import pyexasol
import pandas as pd
from backend.app.core.config import settings

logger = logging.getLogger("datapulse.exasol")
logger.setLevel(logging.INFO)


class ExasolClient:
    """
    Production-grade client for Exasol Personal.
    Handles connection lifecycle, parameterized queries, and health checks.
    """

    def __init__(self):
        self._connection: Optional[pyexasol.ExaConnection] = None
        self._last_connected_at: Optional[float] = None
        self._last_error: Optional[str] = None

    def get_connection_params(self, include_schema: bool = True) -> Dict[str, Any]:
        """
        Builds safe PyExasol connection dictionary from configuration.
        """
        params = {
            "dsn": settings.EXASOL_DSN,
            "user": settings.EXASOL_USER,
            "password": settings.EXASOL_PASSWORD,
            "compression": True,
            "autocommit": True,
            "fetch_dict": True,
            "connection_timeout": 10,
            "query_timeout": 60,
        }

        if include_schema and settings.EXASOL_SCHEMA:
            params["schema"] = settings.EXASOL_SCHEMA

        # Handle TLS verification securely
        if settings.ENVIRONMENT == "production":
            # In production, require strict certificate validation unless explicitly configured
            params["encryption"] = True
            params["websocket_sslopt"] = {"cert_reqs": 2 if settings.EXASOL_VERIFY_TLS else 0}
        else:
            # For local Exasol Personal with self-signed certificate
            params["encryption"] = True
            if not settings.EXASOL_VERIFY_TLS:
                # Local self-signed dev certificate
                params["websocket_sslopt"] = {"check_hostname": False, "cert_reqs": 0}

        return params

    def connect(self, retries: int = 3, retry_delay: float = 1.5, include_schema: bool = True) -> pyexasol.ExaConnection:
        """
        Establishes connection to Exasol with exponential backoff retries.
        Falls back to connecting without default schema if schema does not exist yet.
        """
        if self._connection and self._connection.is_closed is False:
            try:
                # Test if session is still alive
                self._connection.execute("SELECT 1")
                return self._connection
            except Exception:
                logger.warning("Existing Exasol connection dropped. Reconnecting...")
                self.close()

        params = self.get_connection_params(include_schema=include_schema)
        last_exception = None

        for attempt in range(1, retries + 1):
            try:
                logger.info(f"Connecting to Exasol Personal at {settings.EXASOL_DSN} (Attempt {attempt}/{retries})...")
                conn = pyexasol.connect(**params)
                self._connection = conn
                self._last_connected_at = time.time()
                self._last_error = None
                logger.info("Successfully connected to Exasol Personal.")
                return self._connection
            except pyexasol.ExaError as err:
                last_exception = err
                self._last_error = str(err)
                # If schema was not found (code 08004), retry immediately without schema
                if "08004" in str(err) and "schema" in str(err).lower() and "schema" in params:
                    logger.info("Schema not found during initial login. Re-trying connection without schema specification...")
                    params.pop("schema", None)
                    try:
                        conn = pyexasol.connect(**params)
                        self._connection = conn
                        self._last_connected_at = time.time()
                        self._last_error = None
                        logger.info("Connected to Exasol Personal without default schema.")
                        return self._connection
                    except Exception as inner_err:
                        last_exception = inner_err
                        self._last_error = str(inner_err)
                logger.warning(f"Exasol connection attempt {attempt} failed: {err}")
                if attempt < retries:
                    time.sleep(retry_delay * attempt)
            except Exception as err:
                last_exception = err
                self._last_error = str(err)
                logger.warning(f"Unexpected connection error on attempt {attempt}: {err}")
                if attempt < retries:
                    time.sleep(retry_delay * attempt)

        raise ConnectionError(
            f"Failed to connect to Exasol Personal at '{settings.EXASOL_DSN}' after {retries} attempts. "
            f"Last error: {self._last_error}. "
            f"Ensure Exasol Personal is running (`exakit status` / `exasol status`)."
        ) from last_exception

    def close(self):
        """Closes the current connection safely."""
        if self._connection:
            try:
                self._connection.close()
            except Exception as e:
                logger.debug(f"Error while closing Exasol connection: {e}")
            finally:
                self._connection = None

    def execute(self, query: str, query_params: Optional[Dict[str, Any]] = None) -> pyexasol.ExaStatement:
        """
        Executes a SQL statement or query.
        """
        conn = self.connect()
        try:
            return conn.execute(query, query_params or {})
        except Exception as e:
            self._last_error = str(e)
            logger.error(f"Error executing Exasol query: {query[:200]}... Error: {e}")
            raise

    def fetch_all(self, query: str, query_params: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
        """
        Executes query and returns all rows as list of dictionaries.
        """
        stmt = self.execute(query, query_params)
        return stmt.fetchall()

    def execute_query(self, query: str, query_params: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
        """
        Convenience alias for fetch_all.
        """
        return self.fetch_all(query, query_params)

    def fetch_one(self, query: str, query_params: Optional[Dict[str, Any]] = None) -> Optional[Dict[str, Any]]:
        """
        Executes query and returns a single row dictionary or None.
        """
        stmt = self.execute(query, query_params)
        return stmt.fetchone()

    def fetch_df(self, query: str, query_params: Optional[Dict[str, Any]] = None) -> pd.DataFrame:
        """
        Executes query and returns a Pandas DataFrame.
        """
        conn = self.connect()
        try:
            return conn.export_to_pandas(query, query_params or {})
        except Exception as e:
            # Fallback if export_to_pandas raises an exception
            rows = self.fetch_all(query, query_params)
            return pd.DataFrame(rows)

    def import_from_pandas(self, df: pd.DataFrame, table_name: str):
        """
        Bulk imports a Pandas DataFrame into the specified Exasol table.
        """
        if df.empty:
            return
        conn = self.connect()
        conn.import_from_pandas(df, table_name)

    def check_connection(self) -> Dict[str, Any]:
        """
        Performs a deep health check of Exasol database.
        Returns connectivity status, metadata, latency, and table statistics without exposing credentials.
        """
        start_time = time.time()
        try:
            conn = self.connect(retries=1)
            # Execute basic ping query
            stmt = conn.execute("SELECT 1 AS PING, CURRENT_TIMESTAMP AS SERVER_TIME, CURRENT_SCHEMA AS ACTIVE_SCHEMA")
            row = stmt.fetchone()
            latency_ms = round((time.time() - start_time) * 1000, 2)

            # Query database session/version info safely
            meta_stmt = conn.execute("""
                SELECT 
                    PARAM_VALUE AS DB_VERSION
                FROM SYS.EXA_METADATA 
                WHERE PARAM_NAME = 'databaseProductVersion'
            """)
            meta_row = meta_stmt.fetchone()
            db_version = meta_row.get("DB_VERSION", "Unknown Exasol Version") if meta_row else "Exasol Personal"

            # Check required DATAPULSE tables
            tables_stmt = conn.execute(f"""
                SELECT TABLE_NAME 
                FROM SYS.EXA_ALL_TABLES 
                WHERE TABLE_SCHEMA = '{settings.EXASOL_SCHEMA}'
            """)
            existing_tables = [r["TABLE_NAME"] if isinstance(r, dict) else r[0] for r in tables_stmt.fetchall()]

            required_tables = [
                "PIPELINES",
                "PIPELINE_RUNS",
                "DATA_QUALITY",
                "INCIDENTS",
                "PIPELINE_DEPENDENCIES",
                "PREDICTION_RESULTS",
                "AUDIT_EVENTS"
            ]
            missing_tables = [t for t in required_tables if t not in existing_tables]

            return {
                "connected": True,
                "status": "healthy" if not missing_tables else "degraded",
                "dsn": settings.EXASOL_DSN,
                "schema": settings.EXASOL_SCHEMA,
                "schema_name": settings.EXASOL_SCHEMA,
                "db_version": db_version,
                "server_time": str(row.get("SERVER_TIME")) if row else None,
                "latency_ms": latency_ms,
                "existing_tables": existing_tables,
                "missing_tables": missing_tables,
                "all_tables_verified": len(missing_tables) == 0,
                "last_check_at": time.strftime("%Y-%m-%d %H:%M:%S UTC", time.gmtime()),
                "error": None
            }
        except Exception as e:
            latency_ms = round((time.time() - start_time) * 1000, 2)
            self._last_error = str(e)
            return {
                "connected": False,
                "status": "disconnected",
                "dsn": settings.EXASOL_DSN,
                "schema": settings.EXASOL_SCHEMA,
                "schema_name": settings.EXASOL_SCHEMA,
                "db_version": None,
                "server_time": None,
                "latency_ms": latency_ms,
                "existing_tables": [],
                "missing_tables": [
                    "PIPELINES",
                    "PIPELINE_RUNS",
                    "DATA_QUALITY",
                    "INCIDENTS",
                    "PIPELINE_DEPENDENCIES",
                    "PREDICTION_RESULTS",
                    "AUDIT_EVENTS"
                ],
                "all_tables_verified": False,
                "last_check_at": time.strftime("%Y-%m-%d %H:%M:%S UTC", time.gmtime()),
                "error": str(e)
            }


# Singleton instance for application-wide reuse
exasol_client = ExasolClient()
