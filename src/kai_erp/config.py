"""
Configuration Management
========================

Central configuration for the KAI ERP Connector.
All settings are loaded from environment variables with sensible defaults.
"""

import os
from enum import Enum
from functools import lru_cache
from typing import Any, Optional

from pydantic import Field, SecretStr, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Environment(str, Enum):
    """Deployment environment."""
    DEVELOPMENT = "development"
    STAGING = "staging"
    PRODUCTION = "production"


class SyteLineConfig(BaseSettings):
    """SyteLine 10 REST API configuration."""
    
    model_config = SettingsConfigDict(env_prefix="SL10_")
    
    # NOTE: These default to empty to allow the app to boot without SyteLine configured.
    # The API will return 503 for data endpoints until credentials are provided.
    base_url: str = Field(
        default="",
        description="SyteLine 10 CloudSuite base URL",
        examples=["https://xxx.erpsl.inforcloudsuite.com"]
    )
    config_name: str = Field(
        default="",
        description="SyteLine configuration name (e.g., XXX_TST or XXX_PRD)"
    )
    username: str = Field(
        default="",
        description="API username for authentication"
    )
    password: SecretStr = Field(
        default=SecretStr(""),
        description="API password"
    )
    
    # Timeouts
    request_timeout_seconds: int = Field(default=30, ge=5, le=120)
    token_refresh_minutes: int = Field(
        default=55,
        description="Refresh token this many minutes before expiry (tokens last 60 min)"
    )


class DataLakeConfig(BaseSettings):
    """Infor Data Lake configuration (optional)."""
    
    model_config = SettingsConfigDict(env_prefix="LAKE_")
    
    enabled: bool = Field(default=False, description="Enable Data Lake queries")
    compass_url: Optional[str] = Field(
        default=None,
        description="Compass SQL endpoint URL"
    )
    ion_client_id: Optional[str] = Field(default=None)
    ion_client_secret: Optional[SecretStr] = Field(default=None)
    
    # Query limits
    query_timeout_minutes: int = Field(default=60, ge=1, le=60)
    max_rows_per_page: int = Field(default=100_000)


class VolumeThresholds(BaseSettings):
    """Volume thresholds for REST vs Data Lake routing."""
    
    model_config = SettingsConfigDict(env_prefix="VOLUME_")
    
    rest_preferred_max: int = Field(
        default=2000,
        description="Prefer REST below this count"
    )
    rest_hard_max: int = Field(
        default=5000,
        description="Never use REST above this count"
    )
    lake_preferred_min: int = Field(
        default=10000,
        description="Prefer Data Lake above this count"
    )


class ServerConfig(BaseSettings):
    """API server configuration."""
    
    model_config = SettingsConfigDict(env_prefix="")
    
    host: str = Field(default="0.0.0.0")
    port: int = Field(
        default=8100,
        description="API server port (reads from API_PORT or PORT environment variable)"
    )
    log_level: str = Field(default="INFO")
    environment: Environment = Field(default=Environment.DEVELOPMENT)
    
    @model_validator(mode="before")
    @classmethod
    def _read_port_from_env(cls, data: Any) -> Any:
        """Read port from API_PORT or PORT environment variable (API_PORT takes precedence)."""
        if isinstance(data, dict):
            # API_PORT takes precedence - always check it first and override any existing port value
            api_port = os.getenv("API_PORT")
            if api_port:
                data["port"] = int(api_port)
            # If API_PORT not set, ensure PORT is used if it exists (Pydantic may have already set this)
            elif "port" not in data:
                port = os.getenv("PORT")
                if port:
                    data["port"] = int(port)
        return data
    
    # CORS - configurable via CORS_ORIGINS env var (comma-separated)
    # SECURITY: In production, set explicit origins instead of ["*"]
    cors_origins: list[str] = Field(
        default_factory=lambda: ["http://localhost:5173", "http://localhost:3000"],
        description="Allowed CORS origins (set via CORS_ORIGINS env var, comma-separated)"
    )
    
    @property
    def is_production(self) -> bool:
        """Check if running in production environment."""
        return self.environment == Environment.PRODUCTION


class Config(BaseSettings):
    """Root configuration aggregating all sub-configs."""
    
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore"
    )
    
    syteline: SyteLineConfig = Field(default_factory=SyteLineConfig)
    lake: DataLakeConfig = Field(default_factory=DataLakeConfig)
    thresholds: VolumeThresholds = Field(default_factory=VolumeThresholds)
    server: ServerConfig = Field(default_factory=ServerConfig)


@lru_cache
def get_config() -> Config:
    """
    Get cached configuration instance.
    
    Returns:
        Config: Application configuration
    
    Example:
        config = get_config()
        print(config.syteline.base_url)
    """
    return Config()
