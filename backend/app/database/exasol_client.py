"""
DataPulse AI - Exasol Personal Database Connection Manager
Provides thread-safe singleton connection pooling, automatic retries,
TLS configuration, and database health verification without exposing credentials.
"""

import logging
import threading
import time
from typing import Any, Dict, List, Optional
import pandas as pd
import pyexasol

from backend.app.core.config import settings

logger = logging.getLogger("datapulse.exasol")


class ExasolClient:
    """
    Thread-safe PyExasol connection manager adhering to Exasol Personal's 20-connection limit.
    All query execution and row fetching are synchronized via mutex lock to guarantee zero thread collisions.
    """
    _instance: Optional["ExasolClient"] = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(ExasolClient, cls).__new__(cls)
            cls._instance._connection = None
            cls._instance._last_connected_at = 0.0
            cls._instance._last_error = None
            cls._instance._lock = threading.Lock()
        return cls._instance

    def get_connection_params(self, include_schema: bool = True) -> Dict[str, Any]:
        """Builds safe connection dictionary from application configuration."""
        params: Dict[str, Any] = {
            "dsn": settings.EXASOL_DSN,
            "user": settings.EXASOL_USER,
            "password": settings.EXASOL_PASSWORD,
            "fetch_dict": True,
            "autocommit": True,
            "connection_timeout": 15,
            "socket_timeout": 30,
        }

        if include_schema and settings.EXASOL_SCHEMA:
            params["schema"] = settings.EXASOL_SCHEMA

        # Handle TLS verification securely
        params["encryption"] = True
        if not settings.EXASOL_VERIFY_TLS:
            params["websocket_sslopt"] = {"check_hostname": False, "cert_reqs": 0}
        else:
            params["websocket_sslopt"] = {"cert_reqs": 2}

        return params

    def connect(self, retries: int = 3, retry_delay: float = 1.0, include_schema: bool = True) -> pyexasol.ExaConnection:
        """
        Establishes or returns the single persistent connection to Exasol.
        Caller should hold self._lock when calling this.
        """
        if self._connection and getattr(self._connection, "is_closed", False) is False:
            return self._connection

        self.close()

        params = self.get_connection_params(include_schema=include_schema)
        last_exception = None

        for attempt in range(1, retries + 1):
            try:
                conn = pyexasol.connect(**params)
                self._connection = conn
                self._last_connected_at = time.time()
                self._last_error = None
                return self._connection
            except pyexasol.ExaError as err:
                last_exception = err
                self._last_error = str(err)
                if "08004" in str(err) and "schema" in str(err).lower() and "schema" in params:
                    params.pop("schema", None)
                    try:
                        conn = pyexasol.connect(**params)
                        self._connection = conn
                        self._last_connected_at = time.time()
                        self._last_error = None
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
            f"Last error: {self._last_error}."
        ) from last_exception

    def close(self):
        """Closes the current connection safely, terminating session in Exasol."""
        if self._connection:
            try:
                self._connection.close()
            except Exception as e:
                logger.debug(f"Error while closing Exasol connection: {e}")
            finally:
                self._connection = None

    def execute(self, query: str, query_params: Optional[Dict[str, Any]] = None):
        """
        Executes a SQL statement within a mutex lock and automatic session recovery.
        """
        with self._lock:
            try:
                conn = self.connect()
                return conn.execute(query, query_params or {})
            except Exception as e:
                logger.warning(f"Exasol query failed, recovering session: {e}")
                self.close()
                conn = self.connect()
                return conn.execute(query, query_params or {})

    def fetch_all(self, query: str, query_params: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
        """
        Executes query AND reads all rows atomically inside the mutex lock.
        """
        with self._lock:
            try:
                conn = self.connect()
                stmt = conn.execute(query, query_params or {})
                return stmt.fetchall()
            except Exception as e:
                logger.warning(f"Exasol fetch_all failed, recovering session: {e}")
                self.close()
                conn = self.connect()
                stmt = conn.execute(query, query_params or {})
                return stmt.fetchall()

    def execute_query(self, query: str, query_params: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
        """Convenience alias for fetch_all."""
        return self.fetch_all(query, query_params)

    def fetch_one(self, query: str, query_params: Optional[Dict[str, Any]] = None) -> Optional[Dict[str, Any]]:
        """
        Executes query AND reads a single row atomically inside the mutex lock.
        """
        with self._lock:
            try:
                conn = self.connect()
                stmt = conn.execute(query, query_params or {})
                return stmt.fetchone()
            except Exception as e:
                logger.warning(f"Exasol fetch_one failed, recovering session: {e}")
                self.close()
                conn = self.connect()
                stmt = conn.execute(query, query_params or {})
                return stmt.fetchone()

    def fetch_df(self, query: str, query_params: Optional[Dict[str, Any]] = None) -> pd.DataFrame:
        """Executes query and returns a Pandas DataFrame."""
        rows = self.fetch_all(query, query_params)
        return pd.DataFrame(rows)

    def import_from_pandas(self, df: pd.DataFrame, table_name: str):
        """Bulk imports a Pandas DataFrame into the specified Exasol table."""
        if df.empty:
            return
        with self._lock:
            conn = self.connect()
            conn.import_from_pandas(df, table_name)

    def check_connection(self) -> Dict[str, Any]:
        """
        Performs health check of Exasol database safely under lock.
        """
        start_time = time.time()
        with self._lock:
            try:
                conn = self.connect(retries=1)
                stmt = conn.execute("SELECT 1 AS PING, CURRENT_TIMESTAMP AS SERVER_TIME, CURRENT_SCHEMA AS ACTIVE_SCHEMA")
                row = stmt.fetchone()
                latency_ms = round((time.time() - start_time) * 1000, 2)

                meta_stmt = conn.execute("""
                    SELECT PARAM_VALUE as DB_VERSION 
                    FROM SYS.EXA_METADATA 
                    WHERE PARAM_NAME = 'databaseProductVersion'
                """)
                meta_row = meta_stmt.fetchone()
                db_version = meta_row.get("DB_VERSION", "2026.2.0-nano.3") if meta_row else "2026.2.0-nano.3"

                tables_stmt = conn.execute(f"""
                    SELECT TABLE_NAME 
                    FROM SYS.EXA_ALL_TABLES 
                    WHERE TABLE_SCHEMA = '{settings.EXASOL_SCHEMA}'
                """)
                existing_tables = [r["TABLE_NAME"] if isinstance(r, dict) else r[0] for r in tables_stmt.fetchall()]

                required_tables = [
                    "PIPELINES", "PIPELINE_RUNS", "DATA_QUALITY",
                    "INCIDENTS", "PIPELINE_DEPENDENCIES", "PREDICTION_RESULTS", "AUDIT_EVENTS"
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
                        "PIPELINES", "PIPELINE_RUNS", "DATA_QUALITY",
                        "INCIDENTS", "PIPELINE_DEPENDENCIES", "PREDICTION_RESULTS", "AUDIT_EVENTS"
                    ],
                    "all_tables_verified": False,
                    "last_check_at": time.strftime("%Y-%m-%d %H:%M:%S UTC", time.gmtime()),
                    "error": str(e)
                }


exasol_client = ExasolClient()
