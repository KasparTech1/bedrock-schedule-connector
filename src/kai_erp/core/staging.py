"""
DuckDB Staging Layer
====================

Provides in-memory staging for joining data from multiple IDO responses.

Key features:
- Ephemeral DuckDB instances (create → use → discard)
- DataFrame to table loading
- SQL query execution
- Automatic cleanup
"""

from typing import Any, Optional

import duckdb
import pandas as pd
import structlog

logger = structlog.get_logger(__name__)


class StagingEngine:
    """
    DuckDB-based staging engine for client-side joins.
    
    Loads JSON/DataFrame data into ephemeral DuckDB tables,
    executes SQL joins, and returns results.
    
    Example:
        async with StagingEngine() as staging:
            staging.load_dataframe("jobs", jobs_df)
            staging.load_dataframe("items", items_df)
            result = staging.execute_query('''
                SELECT j.Job, i.Description
                FROM jobs j JOIN items i ON j.Item = i.Item
            ''')
    """
    
    def __init__(self):
        """Initialize staging engine."""
        self._conn: Optional[duckdb.DuckDBPyConnection] = None
    
    async def __aenter__(self) -> "StagingEngine":
        """Async context manager entry - create in-memory database."""
        self._conn = duckdb.connect(":memory:")
        logger.debug("DuckDB staging instance created")
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb) -> None:
        """Async context manager exit - cleanup database."""
        if self._conn:
            self._conn.close()
            self._conn = None
            logger.debug("DuckDB staging instance closed")
    
    def __enter__(self) -> "StagingEngine":
        """Sync context manager entry."""
        self._conn = duckdb.connect(":memory:")
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb) -> None:
        """Sync context manager exit."""
        if self._conn:
            self._conn.close()
            self._conn = None
    
    def load_dataframe(self, table_name: str, df: pd.DataFrame) -> None:
        """
        Load a DataFrame into a DuckDB table.
        
        Args:
            table_name: Name for the table
            df: Pandas DataFrame to load
        """
        if not self._conn:
            raise RuntimeError("StagingEngine not initialized (use context manager)")
        
        if df.empty:
            logger.debug(f"Loading empty DataFrame as {table_name}")
            # Create empty table - DuckDB needs at least one column
            self._conn.execute(f"CREATE TABLE {table_name} (placeholder INTEGER)")
            return
        else:
            self._conn.execute(f"CREATE TABLE {table_name} AS SELECT * FROM df")
            logger.debug(f"Loaded {len(df)} rows into {table_name}")
    
    def load_records(self, table_name: str, records: list[dict[str, Any]]) -> None:
        """
        Load a list of dictionaries into a DuckDB table.
        
        Args:
            table_name: Name for the table
            records: List of record dictionaries
        """
        df = pd.DataFrame(records) if records else pd.DataFrame()
        self.load_dataframe(table_name, df)
    
    def execute_query(self, sql: str) -> list[dict[str, Any]]:
        """
        Execute SQL query and return results as list of dicts.
        
        Args:
            sql: SQL query string
        
        Returns:
            List of result dictionaries
        """
        if not self._conn:
            raise RuntimeError("StagingEngine not initialized (use context manager)")
        
        logger.debug("Executing staging query", sql=sql[:100] + "..." if len(sql) > 100 else sql)
        
        result = self._conn.execute(sql)
        df = result.fetchdf()
        
        logger.debug(f"Query returned {len(df)} rows")
        
        return df.to_dict(orient="records")
    
    def execute_query_df(self, sql: str) -> pd.DataFrame:
        """
        Execute SQL query and return results as DataFrame.
        
        Args:
            sql: SQL query string
        
        Returns:
            Pandas DataFrame with results
        """
        if not self._conn:
            raise RuntimeError("StagingEngine not initialized (use context manager)")
        
        result = self._conn.execute(sql)
        return result.fetchdf()
    
    async def execute_join(
        self,
        ido_data: dict[str, list[dict[str, Any]]],
        join_sql: str,
        table_aliases: Optional[dict[str, str]] = None
    ) -> list[dict[str, Any]]:
        """
        Load multiple IDO responses and execute join query.
        
        This is the main entry point for connector joins.
        
        Args:
            ido_data: Dict mapping IDO names to their response records
            join_sql: SQL query to join the tables
            table_aliases: Optional mapping of IDO names to table names in SQL
        
        Returns:
            Joined result records
        
        Example:
            result = await staging.execute_join(
                ido_data={
                    "SLJobs": [...],
                    "SLItems": [...]
                },
                join_sql="SELECT j.Job, i.Description FROM SLJobs j JOIN SLItems i ON j.Item = i.Item"
            )
        """
        # Load each IDO response into a table
        for ido_name, records in ido_data.items():
            table_name = table_aliases.get(ido_name, ido_name) if table_aliases else ido_name
            self.load_records(table_name, records)
        
        # Execute join query
        return self.execute_query(join_sql)
    
    def table_exists(self, table_name: str) -> bool:
        """Check if a table exists in the staging database."""
        if not self._conn:
            return False
        
        result = self._conn.execute(
            "SELECT COUNT(*) FROM information_schema.tables WHERE table_name = ?",
            [table_name]
        ).fetchone()
        
        return result[0] > 0 if result else False
    
    def get_table_count(self, table_name: str) -> int:
        """Get row count for a table."""
        if not self._conn:
            return 0
        
        result = self._conn.execute(f"SELECT COUNT(*) FROM {table_name}").fetchone()
        return result[0] if result else 0
