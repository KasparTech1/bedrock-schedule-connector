"""
Base Connector Abstract Class
==============================

All connectors inherit from BaseConnector and implement:
- get_rest_spec(): Define REST API access pattern
- get_lake_query(): Define Data Lake SQL query
- estimate_volume(): Estimate result count for routing
- transform_result(): Map raw data to business objects

The base class provides:
- Automatic routing between REST and Data Lake
- Common error handling
- Metrics collection
"""

from abc import ABC, abstractmethod
from datetime import datetime, timezone
from typing import Any, Generic, Optional, TypeVar

from pydantic import BaseModel

from kai_erp.core.types import (
    ConnectorResult,
    DataSource,
    Freshness,
    RestQuerySpec,
    VolumeExceedsLimit,
)

# Type variable for the output model type
T = TypeVar("T", bound=BaseModel)


class BaseConnector(ABC, Generic[T]):
    """
    Abstract base class for all KAI ERP Connectors.
    
    Each connector encapsulates a complete data access pattern,
    including which data sources to fetch, how to join/transform
    the data, and what business object to return.
    
    Type Parameters:
        T: The Pydantic model type returned by transform_result()
    
    Example:
        class BedrockOpsScheduler(BaseConnector[ScheduledOperation]):
            def get_rest_spec(self) -> RestQuerySpec:
                ...
            
            def transform_result(self, row: dict) -> ScheduledOperation:
                return ScheduledOperation(**row)
    """
    
    def __init__(
        self,
        rest_engine: Any,  # Will be RestEngine when implemented
        lake_engine: Optional[Any] = None,  # Will be DataLakeEngine when implemented
        router: Optional[Any] = None,  # Will be QueryRouter when implemented
    ):
        """
        Initialize connector with data source engines.
        
        Args:
            rest_engine: REST API engine for real-time queries
            lake_engine: Data Lake engine for bulk/historical queries (optional)
            router: Query router for source selection (optional, created if not provided)
        """
        self.rest_engine = rest_engine
        self.lake_engine = lake_engine
        self.router = router
    
    # ─────────────────────────────────────────────────────────────────────────
    # Abstract Methods - Must be implemented by each connector
    # ─────────────────────────────────────────────────────────────────────────
    
    @abstractmethod
    def get_rest_spec(self, filters: Optional[dict[str, Any]] = None) -> RestQuerySpec:
        """
        Define the REST API access pattern.
        
        Args:
            filters: Optional filters to apply (e.g., work_center, job)
        
        Returns:
            RestQuerySpec with IDOs to fetch and join SQL
        """
        pass
    
    @abstractmethod
    def get_lake_query(self, filters: Optional[dict[str, Any]] = None) -> str:
        """
        Define the Data Lake SQL query.
        
        Args:
            filters: Optional filters to apply
        
        Returns:
            Compass SQL query string
        """
        pass
    
    @abstractmethod
    async def estimate_volume(self, filters: Optional[dict[str, Any]] = None) -> int:
        """
        Estimate the number of records that will be returned.
        
        This is used by the router to decide REST vs Data Lake.
        Can be a rough estimate based on typical volumes.
        
        Args:
            filters: Optional filters that may reduce volume
        
        Returns:
            Estimated record count
        """
        pass
    
    @abstractmethod
    def transform_result(self, row: dict[str, Any]) -> T:
        """
        Transform a raw result row into the business model.
        
        Args:
            row: Dictionary of column values from query result
        
        Returns:
            Pydantic model instance
        """
        pass
    
    # ─────────────────────────────────────────────────────────────────────────
    # Concrete Methods - Provided by base class
    # ─────────────────────────────────────────────────────────────────────────
    
    async def execute(
        self,
        filters: Optional[dict[str, Any]] = None,
        freshness: Freshness = Freshness.REALTIME,
        force_source: Optional[DataSource] = None,
    ) -> ConnectorResult:
        """
        Execute the connector query via optimal data source.
        
        The connector doesn't decide REST vs Data Lake directly -
        the router does, based on volume and freshness requirements.
        
        Args:
            filters: Optional filters to apply
            freshness: Data freshness requirement
            force_source: Force specific data source (skip routing)
        
        Returns:
            ConnectorResult with data and metadata
        
        Raises:
            VolumeExceedsLimit: If estimated volume exceeds limits
            AuthenticationError: If authentication fails
        """
        start_time = datetime.now(timezone.utc)
        
        # Estimate volume
        volume = await self.estimate_volume(filters)
        
        # Select data source
        if force_source:
            source = force_source
        else:
            source = self._select_source(volume, freshness)
        
        # Execute query
        if source == DataSource.REST:
            raw_data = await self._execute_rest(filters)
        else:
            raw_data = await self._execute_lake(filters)
        
        # Transform results
        transformed = [self.transform_result(row) for row in raw_data]
        
        # Calculate latency
        latency_ms = int((datetime.now(timezone.utc) - start_time).total_seconds() * 1000)
        
        return ConnectorResult(
            data=[item.model_dump() for item in transformed],
            source=source,
            latency_ms=latency_ms,
            record_count=len(transformed),
        )
    
    def _select_source(self, volume: int, freshness: Freshness) -> DataSource:
        """
        Select optimal data source based on volume and freshness.
        
        Decision matrix:
        - REALTIME + any volume: REST (if within limits)
        - BATCH_OK + large volume: Data Lake
        - Default: REST for simplicity
        """
        if self.router:
            return self.router.select_source(volume, freshness)
        
        # Default routing logic if no router provided
        if freshness == Freshness.REALTIME:
            if volume > 5000:
                raise VolumeExceedsLimit(
                    volume, 5000,
                    "Add filters to reduce result count or use BATCH_OK freshness"
                )
            return DataSource.REST
        
        if freshness == Freshness.BATCH_OK and volume > 2000 and self.lake_engine:
            return DataSource.DATALAKE
        
        return DataSource.REST
    
    async def _execute_rest(self, filters: Optional[dict[str, Any]] = None) -> list[dict]:
        """Execute query via REST API engine."""
        spec = self.get_rest_spec(filters)
        
        # Fetch all IDOs in parallel
        ido_data = await self.rest_engine.parallel_fetch(spec.idos)
        
        # Stage in DuckDB and execute join with parameterized query
        result = await self.rest_engine.staging.execute_join(
            ido_data,
            spec.join_sql,
            spec.table_aliases,
            spec.join_params  # Pass parameters to prevent SQL injection
        )
        
        return result
    
    async def _execute_lake(self, filters: Optional[dict[str, Any]] = None) -> list[dict]:
        """Execute query via Data Lake engine."""
        if not self.lake_engine:
            raise RuntimeError("Data Lake engine not configured")
        
        query = self.get_lake_query(filters)
        return await self.lake_engine.execute(query)
    
    # ─────────────────────────────────────────────────────────────────────────
    # Helper Methods
    # ─────────────────────────────────────────────────────────────────────────
    
    def apply_filters_to_sql(
        self,
        base_sql: str,
        filters: Optional[dict[str, Any]],
        filter_mappings: dict[str, str]
    ) -> str:
        """
        Apply filters to a SQL query.
        
        Args:
            base_sql: Base SQL query (may have WHERE clause)
            filters: Filter dict (e.g., {"work_center": "WELD-01"})
            filter_mappings: Map filter keys to SQL column expressions
                             (e.g., {"work_center": "jr.Wc"})
        
        Returns:
            Modified SQL with filters applied
        """
        if not filters:
            return base_sql
        
        conditions = []
        for key, value in filters.items():
            if key in filter_mappings and value is not None:
                column = filter_mappings[key]
                # Handle different value types
                if isinstance(value, bool):
                    # Boolean filter (like include_completed)
                    continue  # Handled separately
                elif isinstance(value, str):
                    conditions.append(f"{column} = '{value}'")
                elif isinstance(value, (int, float)):
                    conditions.append(f"{column} = {value}")
        
        if not conditions:
            return base_sql
        
        # Add conditions to existing WHERE or create new one
        if "WHERE" in base_sql.upper():
            return f"{base_sql} AND {' AND '.join(conditions)}"
        else:
            return f"{base_sql} WHERE {' AND '.join(conditions)}"
