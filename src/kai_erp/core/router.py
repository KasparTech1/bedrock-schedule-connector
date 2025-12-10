"""
Query Router
============

Decides between REST API and Data Lake based on volume and freshness.

Decision matrix:
- REALTIME + any volume → REST (if within limits)
- BATCH_OK + large volume → Data Lake
- Default → REST for simplicity
"""

import structlog

from kai_erp.config import VolumeThresholds
from kai_erp.core.types import DataSource, Freshness, VolumeExceedsLimit

logger = structlog.get_logger(__name__)


class QueryRouter:
    """
    Routes queries to optimal data source based on requirements.
    
    Considers:
    - Estimated result volume
    - Data freshness requirements
    - Data Lake availability
    
    Example:
        router = QueryRouter(thresholds, lake_available=True)
        source = router.select_source(volume=500, freshness=Freshness.REALTIME)
        # Returns DataSource.REST
    """
    
    def __init__(
        self,
        thresholds: VolumeThresholds,
        lake_available: bool = False
    ):
        """
        Initialize query router.
        
        Args:
            thresholds: Volume thresholds for routing decisions
            lake_available: Whether Data Lake is configured and available
        """
        self.thresholds = thresholds
        self.lake_available = lake_available
    
    def select_source(
        self,
        volume: int,
        freshness: Freshness = Freshness.REALTIME
    ) -> DataSource:
        """
        Select optimal data source for query.
        
        Args:
            volume: Estimated result record count
            freshness: Data freshness requirement
        
        Returns:
            Selected data source
        
        Raises:
            VolumeExceedsLimit: If volume too high for any available source
        """
        logger.debug(
            "Routing query",
            volume=volume,
            freshness=freshness.value,
            lake_available=self.lake_available
        )
        
        # Check if volume exceeds all limits
        if volume > self.thresholds.rest_hard_max and not self.lake_available:
            raise VolumeExceedsLimit(
                estimated=volume,
                limit=self.thresholds.rest_hard_max,
                suggestion="Add filters to reduce volume or enable Data Lake"
            )
        
        # Decision logic
        source = self._decide(volume, freshness)
        
        logger.info(
            "Routed query",
            source=source.value,
            volume=volume,
            freshness=freshness.value
        )
        
        return source
    
    def _decide(self, volume: int, freshness: Freshness) -> DataSource:
        """Internal decision logic."""
        
        # Real-time always uses REST (if within limits)
        if freshness == Freshness.REALTIME:
            if volume > self.thresholds.rest_hard_max:
                raise VolumeExceedsLimit(
                    estimated=volume,
                    limit=self.thresholds.rest_hard_max,
                    suggestion="Real-time queries require smaller volume. Add filters."
                )
            return DataSource.REST
        
        # Near real-time: prefer REST if within preferred limit
        if freshness == Freshness.NEAR_REALTIME:
            if volume <= self.thresholds.rest_preferred_max:
                return DataSource.REST
            elif volume <= self.thresholds.rest_hard_max:
                # In the "caution" zone - still use REST but log warning
                logger.warning(
                    "Volume in caution zone for REST",
                    volume=volume,
                    preferred_max=self.thresholds.rest_preferred_max
                )
                return DataSource.REST
            elif self.lake_available:
                return DataSource.DATALAKE
            else:
                raise VolumeExceedsLimit(
                    estimated=volume,
                    limit=self.thresholds.rest_hard_max,
                    suggestion="Enable Data Lake for large queries"
                )
        
        # Batch OK: prefer Data Lake for large volumes
        if freshness == Freshness.BATCH_OK:
            if volume >= self.thresholds.lake_preferred_min and self.lake_available:
                return DataSource.DATALAKE
            elif volume <= self.thresholds.rest_preferred_max:
                return DataSource.REST
            elif self.lake_available:
                return DataSource.DATALAKE
            else:
                # No lake, fall back to REST with warning
                if volume > self.thresholds.rest_hard_max:
                    raise VolumeExceedsLimit(
                        estimated=volume,
                        limit=self.thresholds.rest_hard_max,
                        suggestion="Enable Data Lake for batch queries"
                    )
                return DataSource.REST
        
        # Default to REST
        return DataSource.REST
    
    def explain_decision(
        self,
        volume: int,
        freshness: Freshness
    ) -> str:
        """
        Explain why a particular source would be selected.
        
        Useful for debugging and documentation.
        
        Args:
            volume: Estimated volume
            freshness: Freshness requirement
        
        Returns:
            Human-readable explanation
        """
        try:
            source = self.select_source(volume, freshness)
        except VolumeExceedsLimit as e:
            return f"ERROR: {e}"
        
        if source == DataSource.REST:
            if freshness == Freshness.REALTIME:
                return f"REST selected: Real-time freshness requires REST API"
            elif volume <= self.thresholds.rest_preferred_max:
                return f"REST selected: Volume ({volume}) within optimal range"
            else:
                return f"REST selected: Volume ({volume}) acceptable, Lake not needed/available"
        else:
            if volume >= self.thresholds.lake_preferred_min:
                return f"Data Lake selected: Volume ({volume}) exceeds REST preference"
            else:
                return f"Data Lake selected: Batch freshness allows historical data"
