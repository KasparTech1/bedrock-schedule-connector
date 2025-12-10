"""
Core Type Definitions
=====================

Shared types used across the core layer and connectors.
These are the interface contracts that enable parallel development.
"""

from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Optional


class DataSource(str, Enum):
    """Available data source backends."""
    REST = "rest"
    DATALAKE = "datalake"


class Freshness(str, Enum):
    """Data freshness requirements."""
    REALTIME = "realtime"        # < 1 minute old, use REST
    NEAR_REALTIME = "near_rt"    # < 15 minutes old, REST or Lake
    BATCH_OK = "batch"           # Can be hours old, prefer Lake


@dataclass
class IDOSpec:
    """
    Specification for a single IDO (Intelligent Data Object) fetch.
    
    IDOs are SyteLine's REST API abstraction over database tables.
    
    Attributes:
        name: IDO name (e.g., "SLJobs", "SLJobroutes")
        properties: List of property names to fetch
        filter: OData-style filter expression (optional)
        orderby: OData-style ordering (optional)
    
    Example:
        IDOSpec(
            name="SLJobs",
            properties=["Job", "Suffix", "Item", "QtyReleased"],
            filter="Stat='R'"
        )
    """
    name: str
    properties: list[str]
    filter: Optional[str] = None
    orderby: Optional[str] = None
    
    def to_query_params(self) -> dict[str, str]:
        """Convert to URL query parameters for SyteLine REST API."""
        params = {
            "$select": ",".join(self.properties)
        }
        if self.filter:
            params["$filter"] = self.filter
        if self.orderby:
            params["$orderby"] = self.orderby
        return params


@dataclass
class RestQuerySpec:
    """
    Complete specification for a multi-IDO REST query with join.
    
    Attributes:
        idos: List of IDO specifications to fetch in parallel
        join_sql: DuckDB SQL to join the fetched data
        
    Example:
        RestQuerySpec(
            idos=[
                IDOSpec("SLJobs", ["Job", "Item"]),
                IDOSpec("SLItems", ["Item", "Description"])
            ],
            join_sql="SELECT j.Job, i.Description FROM SLJobs j JOIN SLItems i ON j.Item = i.Item"
        )
    """
    idos: list[IDOSpec]
    join_sql: str
    
    # Optional table aliases for when IDO name differs from table in SQL
    table_aliases: dict[str, str] = field(default_factory=dict)


@dataclass
class ConnectorResult:
    """
    Result returned from connector execution.
    
    Attributes:
        data: List of result records
        source: Which data source was used
        latency_ms: Total query time in milliseconds
        record_count: Number of records returned
        truncated: Whether results were truncated due to limits
        query_time: When the query was executed
    """
    data: list[dict[str, Any]]
    source: DataSource
    latency_ms: int
    record_count: int
    truncated: bool = False
    query_time: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    
    @property
    def is_empty(self) -> bool:
        """Check if result contains no data."""
        return self.record_count == 0


@dataclass
class TokenInfo:
    """
    OAuth2 token information.
    
    Attributes:
        access_token: The bearer token
        expires_at: When the token expires
        token_type: Token type (usually "Bearer")
    """
    access_token: str
    expires_at: datetime
    token_type: str = "Bearer"
    
    @property
    def is_expired(self) -> bool:
        """Check if token has expired."""
        return datetime.utcnow() >= self.expires_at
    
    @property
    def should_refresh(self, buffer_minutes: int = 5) -> bool:
        """Check if token should be refreshed (within buffer of expiry)."""
        from datetime import timedelta
        refresh_at = self.expires_at - timedelta(minutes=buffer_minutes)
        return datetime.utcnow() >= refresh_at


class VolumeExceedsLimit(Exception):
    """Raised when query volume exceeds configured limits."""
    
    def __init__(self, estimated: int, limit: int, suggestion: str = ""):
        self.estimated = estimated
        self.limit = limit
        self.suggestion = suggestion
        super().__init__(
            f"Estimated volume ({estimated:,}) exceeds limit ({limit:,}). {suggestion}"
        )


class AuthenticationError(Exception):
    """Raised when authentication fails."""
    pass


class RateLimitError(Exception):
    """Raised when rate limit is exceeded."""
    
    def __init__(self, retry_after: Optional[int] = None):
        self.retry_after = retry_after
        super().__init__(f"Rate limit exceeded. Retry after {retry_after}s" if retry_after else "Rate limit exceeded")
