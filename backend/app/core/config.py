"""
DataPulse AI - Application Configuration
Reads environment variables with Pydantic Settings and validates defaults.
"""

from typing import List, Optional
from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    PROJECT_NAME: str = Field(default="DataPulse AI", description="Project Name")
    VERSION: str = Field(default="1.0.0", description="Application Version")

    # Exasol Personal connection settings
    EXASOL_DSN: str = Field(default="127.0.0.1:8563", description="Exasol host:port DSN")
    EXASOL_USER: str = Field(default="sys", description="Exasol database username")
    EXASOL_PASSWORD: str = Field(default="exasol", description="Exasol database password")
    EXASOL_SCHEMA: str = Field(default="DATAPULSE", description="Target database schema")
    EXASOL_VERIFY_TLS: bool = Field(default=False, description="Verify TLS certificate on connection")
    EXASOL_ENABLED: bool = Field(default=True, description="Whether Exasol is expected to be enabled")

    # FastAPI Server settings
    HOST: str = Field(default="0.0.0.0", description="Server bind host")
    PORT: int = Field(default=8000, description="Server bind port")
    API_HOST: str = Field(default="0.0.0.0", description="API server host alias")
    API_PORT: int = Field(default=8000, description="API server port alias")
    ENVIRONMENT: str = Field(default="development", description="Environment stage: development/production")
    CORS_ORIGINS: str = Field(
        default="http://localhost:5173,http://localhost:3000,http://127.0.0.1:5173,http://127.0.0.1:3000",
        description="Allowed CORS origins comma-separated"
    )

    # Optional LLM integration
    OPENAI_API_KEY: Optional[str] = Field(default=None, description="Optional OpenAI API key for enriched explanations")
    LLM_MODEL: str = Field(default="gpt-4o-mini", description="LLM model identifier")

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore"
    )

    @property
    def cors_origins_list(self) -> List[str]:
        return [origin.strip() for origin in self.CORS_ORIGINS.split(",") if origin.strip()]


settings = Settings()
