"""
Mongoose REST API Client
========================

Production client for accessing SyteLine/CSI data via ION API.

Features:
- OAuth2 authentication with token caching
- Automatic token refresh
- Parallel IDO fetching
- Clean response parsing
"""

import asyncio
import base64
import os
from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone
from typing import Any, Optional

import httpx
import structlog

logger = structlog.get_logger(__name__)


@dataclass
class MongooseConfig:
    """Configuration for Mongoose REST API access."""
    
    tenant_id: str
    client_id: str
    client_secret: str
    ion_api_url: str
    sso_url: str
    saak: str  # Service Account Access Key
    sask: str  # Service Account Secret Key
    mongoose_config: str  # Mongoose configuration ID
    logical_id: str = "infor.ims.cp_myapp"
    
    @property
    def token_url(self) -> str:
        return f"{self.sso_url}token.oauth2"
    
    @property
    def api_base_url(self) -> str:
        return f"{self.ion_api_url}/{self.tenant_id}/CSI/IDORequestService/ido"
    
    @classmethod
    def from_env(cls) -> "MongooseConfig":
        """Create config from environment variables."""
        return cls(
            tenant_id=os.environ["MONGOOSE_TENANT_ID"],
            client_id=os.environ["MONGOOSE_CLIENT_ID"],
            client_secret=os.environ["MONGOOSE_CLIENT_SECRET"],
            ion_api_url=os.environ.get("MONGOOSE_ION_API_URL", "https://mingle-ionapi.inforcloudsuite.com"),
            sso_url=os.environ["MONGOOSE_SSO_URL"],
            saak=os.environ["MONGOOSE_SAAK"],
            sask=os.environ["MONGOOSE_SASK"],
            mongoose_config=os.environ["MONGOOSE_CONFIG"],
            logical_id=os.environ.get("MONGOOSE_LOGICAL_ID", "infor.ims.cp_myapp"),
        )
    
    @classmethod
    def bedrock_hfa(cls) -> "MongooseConfig":
        """Deprecated helper for HFA profile.

        This function intentionally does NOT embed credentials in source control.
        Configure `MONGOOSE_*` environment variables and use `from_env()`.
        """
        return cls.from_env()
    
    @classmethod
    def bedrock_tbe(cls) -> "MongooseConfig":
        """Deprecated helper for Bedrock TBE profile.

        This function intentionally does NOT embed credentials in source control.
        Configure `MONGOOSE_*` environment variables and use `from_env()`.
        """
        return cls.from_env()


@dataclass
class TokenInfo:
    """OAuth2 token information."""
    access_token: str
    expires_at: datetime
    token_type: str = "Bearer"
    
    @property
    def is_expired(self) -> bool:
        """Check if token is expired (with 60s buffer)."""
        return datetime.now(timezone.utc) >= (self.expires_at - timedelta(seconds=60))


class MongooseClient:
    """
    Async client for Mongoose REST API.
    
    Usage:
        async with MongooseClient(config) as client:
            items = await client.query_ido("SLItems", ["Item", "Description"])
            
            # Or parallel fetch
            data = await client.parallel_fetch([
                ("SLJobs", ["Job", "Item", "QtyReleased"]),
                ("SLJobRoutes", ["Job", "OperNum", "Wc"]),
            ])
    """
    
    MAX_CONCURRENT = 5
    REQUEST_TIMEOUT = 30.0
    
    def __init__(self, config: MongooseConfig):
        self.config = config
        self._token: Optional[TokenInfo] = None
        self._client: Optional[httpx.AsyncClient] = None
        self._semaphore: Optional[asyncio.Semaphore] = None
    
    async def __aenter__(self) -> "MongooseClient":
        """Initialize async client."""
        self._client = httpx.AsyncClient(timeout=self.REQUEST_TIMEOUT)
        self._semaphore = asyncio.Semaphore(self.MAX_CONCURRENT)
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb) -> None:
        """Cleanup async client."""
        if self._client:
            await self._client.aclose()
    
    async def get_token(self) -> str:
        """
        Get valid access token, refreshing if needed.
        
        Returns:
            Access token string
        """
        if self._token and not self._token.is_expired:
            return self._token.access_token
        
        logger.info("Acquiring OAuth2 token")
        
        if not self._client:
            raise RuntimeError("Client not initialized (use async with)")
        
        # Build Basic auth header
        auth_string = f"{self.config.client_id}:{self.config.client_secret}"
        auth_bytes = base64.b64encode(auth_string.encode()).decode()
        
        response = await self._client.post(
            self.config.token_url,
            headers={
                "Content-Type": "application/x-www-form-urlencoded",
                "Authorization": f"Basic {auth_bytes}"
            },
            data={
                "grant_type": "password",
                "username": self.config.saak,
                "password": self.config.sask,
            }
        )
        
        if response.status_code != 200:
            raise Exception(f"Token request failed: {response.status_code} - {response.text}")
        
        token_data = response.json()
        expires_in = token_data.get("expires_in", 3600)
        
        self._token = TokenInfo(
            access_token=token_data["access_token"],
            expires_at=datetime.now(timezone.utc) + timedelta(seconds=expires_in),
            token_type=token_data.get("token_type", "Bearer")
        )
        
        logger.info("OAuth2 token acquired", expires_in=expires_in)
        return self._token.access_token
    
    async def query_ido(
        self,
        ido_name: str,
        properties: list[str],
        filter_expr: Optional[str] = None,
        record_cap: int = 1000,
    ) -> list[dict[str, Any]]:
        """
        Query a single IDO.
        
        Args:
            ido_name: Name of the IDO (e.g., "SLJobs")
            properties: List of property names to return
            filter_expr: Optional filter expression
            record_cap: Maximum records to return
            
        Returns:
            List of record dictionaries
        """
        if not self._client:
            raise RuntimeError("Client not initialized (use async with)")
        
        token = await self.get_token()
        
        url = f"{self.config.api_base_url}/load/{ido_name}"
        params = {
            "properties": ",".join(properties),
            "recordcap": str(record_cap)
        }
        if filter_expr:
            params["filter"] = filter_expr
        
        headers = {
            "Authorization": f"Bearer {token}",
            "Accept": "application/json",
            "X-Infor-MongooseConfig": self.config.mongoose_config,
        }
        
        logger.debug("Querying IDO", ido=ido_name, properties=len(properties))
        
        response = await self._client.get(url, headers=headers, params=params)
        
        if response.status_code == 401:
            # Token expired, refresh and retry
            self._token = None
            token = await self.get_token()
            headers["Authorization"] = f"Bearer {token}"
            response = await self._client.get(url, headers=headers, params=params)
        
        if response.status_code != 200:
            raise Exception(f"IDO query failed: {response.status_code} - {response.text}")
        
        data = response.json()
        
        if not data.get("Success", False):
            msg = data.get("Message", "Unknown error")
            raise Exception(f"IDO query error: {msg}")
        
        items = data.get("Items") or []
        
        logger.debug("IDO query complete", ido=ido_name, records=len(items))
        return items
    
    async def parallel_fetch(
        self,
        queries: list[tuple[str, list[str], Optional[str], int]],
        metrics_run: Optional[Any] = None,
    ) -> dict[str, list[dict[str, Any]]]:
        """
        Fetch multiple IDOs in parallel.
        
        Args:
            queries: List of (ido_name, properties, filter, record_cap) tuples
            metrics_run: Optional ConnectorRunMetrics to track call details
            
        Returns:
            Dict mapping IDO names to their records
        """
        if not self._semaphore:
            raise RuntimeError("Client not initialized (use async with)")
        
        async def fetch_with_semaphore(query):
            ido_name, properties, filter_expr, record_cap = query
            call_start = datetime.now(timezone.utc)
            
            async with self._semaphore:
                try:
                    records = await self.query_ido(ido_name, properties, filter_expr, record_cap)
                    call_duration = (datetime.now(timezone.utc) - call_start).total_seconds() * 1000
                    
                    # Track metrics if provided
                    if metrics_run:
                        from kai_erp.core.metrics import IDOCallMetrics
                        metrics_run.add_ido_call(IDOCallMetrics(
                            ido_name=ido_name,
                            properties_count=len(properties),
                            filter_expression=filter_expr,
                            record_cap=record_cap,
                            records_returned=len(records),
                            duration_ms=call_duration,
                            started_at=call_start,
                            success=True,
                        ))
                    
                    return ido_name, records
                except Exception as e:
                    call_duration = (datetime.now(timezone.utc) - call_start).total_seconds() * 1000
                    
                    # Track failed call
                    if metrics_run:
                        from kai_erp.core.metrics import IDOCallMetrics
                        metrics_run.add_ido_call(IDOCallMetrics(
                            ido_name=ido_name,
                            properties_count=len(properties),
                            filter_expression=filter_expr,
                            record_cap=record_cap,
                            records_returned=0,
                            duration_ms=call_duration,
                            started_at=call_start,
                            success=False,
                            error_message=str(e),
                        ))
                    raise
        
        logger.info(f"Parallel fetching {len(queries)} IDOs")
        start = datetime.now(timezone.utc)
        
        # Update metrics with parallel batch count
        if metrics_run:
            metrics_run.parallel_batches = (len(queries) + self.MAX_CONCURRENT - 1) // self.MAX_CONCURRENT
            metrics_run.max_concurrent = self.MAX_CONCURRENT
        
        tasks = [fetch_with_semaphore(q) for q in queries]
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        data = {}
        for result in results:
            if isinstance(result, Exception):
                logger.error("IDO fetch failed", error=str(result))
            else:
                ido_name, records = result
                data[ido_name] = records
        
        elapsed = (datetime.now(timezone.utc) - start).total_seconds()
        total_records = sum(len(v) for v in data.values())
        
        logger.info(
            "Parallel fetch complete",
            idos=len(data),
            records=total_records,
            elapsed_s=round(elapsed, 2)
        )
        
        return data
