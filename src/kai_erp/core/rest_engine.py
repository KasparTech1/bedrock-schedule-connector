"""
REST API Engine
===============

Handles parallel fetching from SyteLine IDO REST APIs.

Key features:
- Parallel fetch with asyncio.gather
- Rate limit handling with exponential backoff
- DuckDB staging integration
- Response parsing
"""

import asyncio
from datetime import datetime
from typing import Any, Optional

import httpx
import structlog

from kai_erp.config import SyteLineConfig
from kai_erp.core.auth import AuthenticatedClient
from kai_erp.core.staging import StagingEngine
from kai_erp.core.types import IDOSpec, RateLimitError

logger = structlog.get_logger(__name__)


class RestEngine:
    """
    REST API engine for fetching data from SyteLine IDOs.
    
    Fetches from multiple IDOs simultaneously using asyncio,
    stages results in DuckDB for joining, and returns combined data.
    
    Example:
        async with RestEngine(config) as engine:
            # Fetch single IDO
            jobs = await engine.fetch_ido(IDOSpec("SLJobs", ["Job", "Item"]))
            
            # Fetch multiple IDOs in parallel
            data = await engine.parallel_fetch([
                IDOSpec("SLJobs", ["Job", "Item"]),
                IDOSpec("SLItems", ["Item", "Description"])
            ])
    """
    
    # Rate limit handling
    MAX_RETRIES = 3
    INITIAL_BACKOFF_SECONDS = 1
    MAX_BACKOFF_SECONDS = 30
    
    # Concurrency limit
    MAX_CONCURRENT_REQUESTS = 10
    
    def __init__(self, config: SyteLineConfig):
        """
        Initialize REST engine.
        
        Args:
            config: SyteLine configuration
        """
        self.config = config
        self._client: Optional[AuthenticatedClient] = None
        self._staging: Optional[StagingEngine] = None
        self._semaphore: Optional[asyncio.Semaphore] = None
    
    async def __aenter__(self) -> "RestEngine":
        """Async context manager entry."""
        self._client = AuthenticatedClient(self.config)
        await self._client.__aenter__()
        
        self._staging = StagingEngine()
        await self._staging.__aenter__()
        
        self._semaphore = asyncio.Semaphore(self.MAX_CONCURRENT_REQUESTS)
        
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb) -> None:
        """Async context manager exit."""
        if self._staging:
            await self._staging.__aexit__(exc_type, exc_val, exc_tb)
        if self._client:
            await self._client.__aexit__(exc_type, exc_val, exc_tb)
    
    @property
    def staging(self) -> StagingEngine:
        """Get the staging engine for executing joins."""
        if not self._staging:
            raise RuntimeError("RestEngine not initialized (use async with)")
        return self._staging
    
    async def fetch_ido(
        self,
        spec: IDOSpec,
        max_records: Optional[int] = None
    ) -> list[dict[str, Any]]:
        """
        Fetch data from a single IDO.
        
        Args:
            spec: IDO specification (name, properties, filter)
            max_records: Maximum records to fetch (None for all)
        
        Returns:
            List of record dictionaries
        """
        if not self._client:
            raise RuntimeError("RestEngine not initialized (use async with)")
        
        url = self._build_ido_url(spec)
        
        logger.info(
            "Fetching IDO",
            ido=spec.name,
            properties=len(spec.properties),
            filter=spec.filter
        )
        
        start_time = datetime.utcnow()
        
        # Fetch with retry logic
        response = await self._fetch_with_retry(url)
        
        # Parse response
        data = response.json()
        records = data.get("value", [])
        
        # Apply max_records limit
        if max_records and len(records) > max_records:
            records = records[:max_records]
        
        elapsed_ms = int((datetime.utcnow() - start_time).total_seconds() * 1000)
        
        logger.info(
            "IDO fetched",
            ido=spec.name,
            records=len(records),
            elapsed_ms=elapsed_ms
        )
        
        return records
    
    async def parallel_fetch(
        self,
        specs: list[IDOSpec]
    ) -> dict[str, list[dict[str, Any]]]:
        """
        Fetch from multiple IDOs in parallel.
        
        Args:
            specs: List of IDO specifications
        
        Returns:
            Dict mapping IDO names to their records
        
        Example:
            data = await engine.parallel_fetch([
                IDOSpec("SLJobs", ["Job", "Item"]),
                IDOSpec("SLItems", ["Item", "Description"])
            ])
            # data = {"SLJobs": [...], "SLItems": [...]}
        """
        logger.info(f"Starting parallel fetch of {len(specs)} IDOs")
        start_time = datetime.utcnow()
        
        # Create fetch tasks
        tasks = [self._fetch_with_semaphore(spec) for spec in specs]
        
        # Execute in parallel
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Build result dict, handling errors
        data = {}
        for spec, result in zip(specs, results):
            if isinstance(result, Exception):
                logger.error(f"Failed to fetch {spec.name}", error=str(result))
                data[spec.name] = []  # Empty on error
            else:
                data[spec.name] = result
        
        elapsed_ms = int((datetime.utcnow() - start_time).total_seconds() * 1000)
        total_records = sum(len(v) for v in data.values())
        
        logger.info(
            "Parallel fetch complete",
            idos=len(specs),
            total_records=total_records,
            elapsed_ms=elapsed_ms
        )
        
        return data
    
    async def _fetch_with_semaphore(self, spec: IDOSpec) -> list[dict[str, Any]]:
        """Fetch IDO with concurrency limiting."""
        if not self._semaphore:
            return await self.fetch_ido(spec)
        
        async with self._semaphore:
            return await self.fetch_ido(spec)
    
    async def _fetch_with_retry(self, url: str) -> httpx.Response:
        """Fetch URL with exponential backoff retry on rate limit."""
        if not self._client:
            raise RuntimeError("RestEngine not initialized")
        
        backoff = self.INITIAL_BACKOFF_SECONDS
        
        for attempt in range(self.MAX_RETRIES):
            response = await self._client.get(url)
            
            if response.status_code == 429:  # Rate limited
                retry_after = int(response.headers.get("Retry-After", backoff))
                logger.warning(
                    f"Rate limited, waiting {retry_after}s",
                    attempt=attempt + 1
                )
                await asyncio.sleep(retry_after)
                backoff = min(backoff * 2, self.MAX_BACKOFF_SECONDS)
                continue
            
            response.raise_for_status()
            return response
        
        raise RateLimitError(retry_after=backoff)
    
    def _build_ido_url(self, spec: IDOSpec) -> str:
        """Build IDO request URL with query parameters."""
        base = f"/IDORequestService/ido/load/{spec.name}"
        
        params = spec.to_query_params()
        
        # Add config name
        params["_config"] = self.config.config_name
        
        # Build query string
        query_parts = [f"{k}={v}" for k, v in params.items()]
        query_string = "&".join(query_parts)
        
        return f"{base}?{query_string}"


async def create_rest_engine(config: SyteLineConfig) -> RestEngine:
    """
    Factory function to create and initialize a REST engine.
    
    Args:
        config: SyteLine configuration
    
    Returns:
        Initialized RestEngine
    """
    engine = RestEngine(config)
    await engine.__aenter__()
    return engine
