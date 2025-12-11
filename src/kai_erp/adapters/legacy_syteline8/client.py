"""Legacy SyteLine 8 on-prem adapter (pyodbc).

SyteLine 8 typically allowed direct SQL access to the underlying database. This adapter is a
placeholder for that legacy path.

NOTE:
- This module intentionally avoids importing `pyodbc` at import-time so the rest of the
  codebase (and CI) can run without ODBC drivers installed.
- When you implement this for real, add `pyodbc` as an optional dependency and gate
  usage behind environment configuration.
"""

from __future__ import annotations

import asyncio
from dataclasses import dataclass
from typing import Any, Iterable


@dataclass
class SyteLine8Config:
    """SyteLine 8 SQL Server connection configuration."""

    server: str
    database: str
    username: str
    password: str
    driver: str = "ODBC Driver 17 for SQL Server"

    @property
    def connection_string(self) -> str:
        return (
            f"DRIVER={{{self.driver}}};"
            f"SERVER={self.server};"
            f"DATABASE={self.database};"
            f"UID={self.username};"
            f"PWD={self.password};"
            "TrustServerCertificate=yes;"
        )


class SyteLine8Client:
    """Async wrapper around a synchronous ODBC connection."""

    def __init__(self, config: SyteLine8Config):
        self.config = config
        self._conn: Any | None = None

    async def __aenter__(self) -> "SyteLine8Client":
        pyodbc = _import_pyodbc()
        loop = asyncio.get_event_loop()
        self._conn = await loop.run_in_executor(None, lambda: pyodbc.connect(self.config.connection_string))
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb) -> None:
        if self._conn is not None:
            self._conn.close()
            self._conn = None

    async def query(self, sql: str, params: Iterable[Any] = (), max_rows: int = 1000) -> list[dict[str, Any]]:
        if self._conn is None:
            raise RuntimeError("SyteLine8Client not connected (use 'async with').")

        def _exec() -> list[dict[str, Any]]:
            cursor = self._conn.cursor()
            cursor.execute(sql, tuple(params))
            columns = [c[0] for c in cursor.description]
            rows = cursor.fetchmany(max_rows)
            return [dict(zip(columns, row)) for row in rows]

        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(None, _exec)


def _import_pyodbc():
    try:
        import pyodbc  # type: ignore

        return pyodbc
    except Exception as e:  # pragma: no cover
        raise RuntimeError(
            "pyodbc is required for legacy SyteLine 8 connectivity but is not installed/configured."
        ) from e

