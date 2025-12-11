"""SyteLine 10 REST API Client.

This client implements the Mongoose REST Service API for SyteLine 10 CloudSuite.
Based on the Kaspar DW Postman collection patterns.
"""

import logging
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from typing import Any

import httpx

logger = logging.getLogger(__name__)


@dataclass
class SyteLineConfig:
    """SyteLine 10 connection configuration."""
    
    base_url: str
    config_name: str
    username: str
    password: str
    timeout: int = 30


class SyteLineClient:
    """Client for SyteLine 10 REST API (Mongoose REST Service).
    
    Handles token authentication and IDO queries.
    """

    def __init__(self, config: SyteLineConfig):
        """Initialize the client.
        
        Args:
            config: SyteLine connection configuration.
        """
        self.config = config
        self._token: str | None = None
        self._token_expires: datetime | None = None
        self._client: httpx.AsyncClient | None = None

    async def __aenter__(self) -> "SyteLineClient":
        """Enter async context."""
        self._client = httpx.AsyncClient(timeout=self.config.timeout)
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb) -> None:
        """Exit async context."""
        if self._client:
            await self._client.aclose()
            self._client = None

    async def _get_token(self) -> str:
        """Get authentication token, refreshing if needed.
        
        Returns:
            Valid authentication token.
        """
        # Check if we have a valid token
        if self._token and self._token_expires and datetime.now(timezone.utc) < self._token_expires:
            return self._token

        # Request new token
        url = f"{self.config.base_url}/IDORequestService/MGRestService.svc/json/token/{self.config.config_name}"
        
        logger.info(f"Requesting token from {url}")
        
        if not self._client:
            raise RuntimeError("Client not initialized. Use async with context manager.")
        
        response = await self._client.get(
            url,
            headers={
                "userid": self.config.username,
                "password": self.config.password,
            }
        )
        response.raise_for_status()
        
        # Token response is JSON: {"Message":"Success","Token":"..."}
        data = response.json()
        if isinstance(data, dict) and "Token" in data:
            self._token = data["Token"]
        else:
            # Fallback to plain text format
            self._token = response.text.strip().strip('"')
        
        # Tokens typically last 60 minutes, refresh at 55
        self._token_expires = datetime.now(timezone.utc) + timedelta(minutes=55)
        
        logger.info("Token acquired successfully")
        return self._token

    async def query_ido(
        self,
        ido_name: str,
        properties: list[str] | None = None,
        filter_expr: str | None = None,
        order_by: str | None = None,
        row_cap: int = 100,
    ) -> list[dict[str, Any]]:
        """Query an IDO (Intelligent Data Object).
        
        Args:
            ido_name: Name of the IDO to query (e.g., "SLItems").
            properties: List of property names to return.
            filter_expr: Filter expression (e.g., "Stat='A'").
            order_by: Property to order by.
            row_cap: Maximum rows to return.
            
        Returns:
            List of records as dictionaries.
        """
        if not self._client:
            raise RuntimeError("Client not initialized. Use async with context manager.")
        
        token = await self._get_token()
        
        # Build URL
        url = f"{self.config.base_url}/IDORequestService/MGRestService.svc/json/{ido_name}/adv/"
        
        # Build query params
        params: dict[str, str] = {
            "rowcap": str(row_cap),
        }
        
        if properties:
            params["props"] = ",".join(properties)
        
        if filter_expr:
            params["filter"] = filter_expr
        
        if order_by:
            params["orderby"] = order_by
        
        logger.info(f"Querying IDO {ido_name} with params: {params}")
        
        response = await self._client.get(
            url,
            params=params,
            headers={
                "Authorization": token,
                "Content-Type": "application/json",
            }
        )
        response.raise_for_status()
        
        data = response.json()
        
        # Handle response format
        # The response has "Items" array where each item is an array of {Name, Value} objects
        if isinstance(data, dict) and "Items" in data:
            items = data["Items"]
            if not items:
                return []
            
            # Convert to list of dicts
            records = []
            for item in items:
                record = {}
                if isinstance(item, list):
                    # Array of {Name: "PropName", Value: "value"} objects
                    for prop in item:
                        if isinstance(prop, dict) and "Name" in prop and "Value" in prop:
                            name = prop["Name"]
                            # Skip internal _ItemId field
                            if not name.startswith("_"):
                                record[name] = prop["Value"]
                elif isinstance(item, dict):
                    # Dict format (less common)
                    for key, val in item.items():
                        if isinstance(val, dict) and "Value" in val:
                            record[key] = val["Value"]
                        else:
                            record[key] = val
                
                if record:
                    records.append(record)
            
            logger.info(f"Query returned {len(records)} records")
            return records
        
        # Fallback for other formats
        if isinstance(data, list):
            return data
        
        return []

    async def health_check(self) -> bool:
        """Check if the connection is working.
        
        Returns:
            True if connection is healthy.
        """
        try:
            await self._get_token()
            return True
        except Exception as e:
            logger.error(f"Health check failed: {e}")
            return False
