"""Legacy Global Shop bridge adapter.

Encapsulates access to the on-prem Pervasive SQL database via the Cloudflare/Worker bridge.
This is intentionally isolated from the main SyteLine connector stack.

Security notes:
- API key must be provided via `PERVASIVE_API_KEY` environment variable (server-side).
- Filter inputs are allowlisted to prevent SQL injection.
- Raw SQL endpoint is disabled by default and should never be enabled in production.
"""

from __future__ import annotations

import os
import re
import time
from typing import Any

import httpx
from fastapi import HTTPException

from kai_erp.config import get_config

BRIDGE_URL = "https://bridge-api.kaiville.io/query"
DEFAULT_LIMIT = 500

_SAFE_CODE_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9_\-]{0,31}$")


def _get_api_key() -> str:
    key = os.environ.get("PERVASIVE_API_KEY")
    if not key:
        raise HTTPException(
            status_code=500,
            detail="Missing PERVASIVE_API_KEY. Configure Global Shop bridge credentials via environment.",
        )
    return key.strip()


def _validate_code(value: str, field_name: str) -> str:
    v = (value or "").strip()
    if not _SAFE_CODE_RE.fullmatch(v):
        raise HTTPException(
            status_code=400,
            detail=f"Invalid {field_name}. Only letters, numbers, '_' and '-' are allowed (max 32 chars).",
        )
    return v


class GlobalShopBridgeClient:
    """Client for the Global Shop bridge API."""

    def __init__(self, bridge_url: str = BRIDGE_URL):
        self.bridge_url = bridge_url

    async def _execute_sql(self, sql: str) -> dict[str, Any]:
        api_key = _get_api_key()

        async with httpx.AsyncClient(timeout=30.0) as client:
            try:
                response = await client.post(
                    self.bridge_url,
                    headers={
                        "Content-Type": "application/json",
                        "X-API-Key": api_key,
                    },
                    json={"sql": sql},
                )

                if response.status_code == 401:
                    raise HTTPException(status_code=401, detail="Invalid API key for Global Shop bridge")

                if response.status_code == 502:
                    raise HTTPException(
                        status_code=502,
                        detail="Global Shop bridge is unreachable. Check Cloudflare tunnel.",
                    )

                result = response.json()

                if not result.get("success", True) and "error" in result:
                    raise HTTPException(status_code=500, detail=result["error"])

                return result

            except httpx.TimeoutException as e:
                raise HTTPException(status_code=504, detail="Global Shop bridge request timed out") from e
            except httpx.RequestError as e:
                raise HTTPException(status_code=503, detail=f"Bridge connection error: {e}") from e

    @staticmethod
    def _trim_fixed_width(data: list[dict[str, Any]]) -> list[dict[str, Any]]:
        cleaned: list[dict[str, Any]] = []
        for row in data:
            cleaned.append({k: v.strip() if isinstance(v, str) else v for k, v in row.items()})
        return cleaned

    async def health(self) -> dict[str, Any]:
        start_time = time.time()
        try:
            await self._execute_sql("SELECT 1")
            response_time = int((time.time() - start_time) * 1000)
            return {
                "status": "healthy" if response_time < 2000 else "warning",
                "response_time_ms": response_time,
                "message": "Connection successful" if response_time < 2000 else "Slow response",
                "bridge_url": self.bridge_url,
            }
        except HTTPException as e:
            return {
                "status": "error",
                "message": e.detail,
                "bridge_url": self.bridge_url,
            }

    async def get_product_lines(self, product_line: str | None, limit: int) -> dict[str, Any]:
        if product_line:
            safe_pl = _validate_code(product_line, "product_line")
            sql = f"SELECT TOP {limit} * FROM prodline_mre WHERE PRODLINE = '{safe_pl}'"
        else:
            sql = f"SELECT TOP {limit} * FROM prodline_mre"

        start_time = time.time()
        result = await self._execute_sql(sql)
        response_time = int((time.time() - start_time) * 1000)

        data = self._trim_fixed_width(result.get("data", []))

        return {
            "product_lines": data,
            "summary": {
                "total": len(data),
                "query": sql,
                "response_time_ms": response_time,
                "source": "Global Shop (Pervasive SQL)",
                "table": "PRODLINE_MRE",
            },
        }

    async def get_salespersons(self, salesperson: str | None, limit: int) -> dict[str, Any]:
        if salesperson:
            safe_sp = _validate_code(salesperson, "salesperson")
            sql = f"SELECT TOP {limit} * FROM V_SALESPERSONS WHERE SALESSION = '{safe_sp}'"
        else:
            sql = f"SELECT TOP {limit} * FROM V_SALESPERSONS"

        start_time = time.time()
        result = await self._execute_sql(sql)
        response_time = int((time.time() - start_time) * 1000)

        data = self._trim_fixed_width(result.get("data", []))

        return {
            "data": data,
            "summary": {
                "total": len(data),
                "query": sql,
                "response_time_ms": response_time,
                "source": "Global Shop (Pervasive SQL)",
                "table": "V_SALESPERSONS",
            },
        }

    async def execute_raw_select(self, sql: str) -> dict[str, Any]:
        config = get_config()
        enabled = os.environ.get("ENABLE_LEGACY_GLOBAL_SHOP_RAW_SQL", "").strip().lower() in {
            "1",
            "true",
            "yes",
            "on",
        }
        if config.server.is_production or not enabled:
            raise HTTPException(
                status_code=403,
                detail="Raw Global Shop SQL endpoint is disabled. Enable explicitly for development only.",
            )

        if not sql.strip().upper().startswith("SELECT"):
            raise HTTPException(status_code=400, detail="Only SELECT queries are allowed")

        start_time = time.time()
        result = await self._execute_sql(sql)
        response_time = int((time.time() - start_time) * 1000)

        data = self._trim_fixed_width(result.get("data", []))

        return {
            "data": data,
            "summary": {
                "total": len(data),
                "query": sql,
                "response_time_ms": response_time,
                "source": "Global Shop (Pervasive SQL)",
            },
        }
