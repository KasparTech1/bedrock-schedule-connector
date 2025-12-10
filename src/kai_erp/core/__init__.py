"""
Core Layer - Data Source Engines
================================

This layer handles raw data access complexity:

- RestEngine: Parallel fetch from SyteLine IDO REST APIs
- DataLakeEngine: Compass SQL queries against Infor Data Lake  
- StagingEngine: DuckDB for client-side joins
- QueryRouter: Decides REST vs Lake based on volume/freshness
"""

from kai_erp.core.types import (
    AuthenticationError,
    ConnectorResult,
    DataSource,
    Freshness,
    IDOSpec,
    RateLimitError,
    RestQuerySpec,
    TokenInfo,
    VolumeExceedsLimit,
)
from kai_erp.core.auth import AuthenticatedClient, TokenManager
from kai_erp.core.rest_engine import RestEngine
from kai_erp.core.staging import StagingEngine
from kai_erp.core.router import QueryRouter

__all__ = [
    # Types
    "AuthenticationError",
    "ConnectorResult",
    "DataSource",
    "Freshness",
    "IDOSpec",
    "RateLimitError",
    "RestQuerySpec",
    "TokenInfo",
    "VolumeExceedsLimit",
    # Engines
    "AuthenticatedClient",
    "TokenManager",
    "RestEngine",
    "StagingEngine",
    "QueryRouter",
]
