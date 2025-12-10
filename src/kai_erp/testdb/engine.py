"""Test Database Engine - SQLite backend for testing connectors."""

import logging
import sqlite3
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)


class TestDatabaseEngine:
    """SQLite-based test database that simulates SyteLine IDOs."""

    def __init__(self, db_path: Path | str | None = None):
        """Initialize the test database.

        Args:
            db_path: Path to SQLite database file.
                    Defaults to ./testdata.db in the package directory.
        """
        if db_path is None:
            self._db_path = Path(__file__).parent / "testdata.db"
        else:
            self._db_path = Path(db_path)

        self._conn: sqlite3.Connection | None = None

    @property
    def db_path(self) -> Path:
        """Get the database file path."""
        return self._db_path

    def connect(self) -> None:
        """Connect to the database."""
        self._db_path.parent.mkdir(parents=True, exist_ok=True)
        self._conn = sqlite3.connect(str(self._db_path))
        self._conn.row_factory = sqlite3.Row
        logger.info(f"Connected to test database: {self._db_path}")

    def close(self) -> None:
        """Close the database connection."""
        if self._conn:
            self._conn.close()
            self._conn = None

    def __enter__(self) -> "TestDatabaseEngine":
        self.connect()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb) -> None:
        self.close()

    def execute(self, sql: str, params: tuple = ()) -> sqlite3.Cursor:
        """Execute SQL and return cursor."""
        if not self._conn:
            raise RuntimeError("Database not connected")
        return self._conn.execute(sql, params)

    def executemany(self, sql: str, params_list: list[tuple]) -> sqlite3.Cursor:
        """Execute SQL with multiple parameter sets."""
        if not self._conn:
            raise RuntimeError("Database not connected")
        return self._conn.executemany(sql, params_list)

    def commit(self) -> None:
        """Commit transaction."""
        if self._conn:
            self._conn.commit()

    def query(self, sql: str, params: tuple = ()) -> list[dict[str, Any]]:
        """Execute query and return list of dicts."""
        cursor = self.execute(sql, params)
        columns = [desc[0] for desc in cursor.description]
        return [dict(zip(columns, row)) for row in cursor.fetchall()]

    def query_ido(
        self,
        ido_name: str,
        properties: list[str] | None = None,
        filter_expr: str | None = None,
        limit: int = 100,
    ) -> list[dict[str, Any]]:
        """Query a simulated IDO table.

        Args:
            ido_name: The IDO/table name.
            properties: List of properties to select (None = all).
            filter_expr: SQL WHERE clause (without WHERE keyword).
            limit: Max rows to return.

        Returns:
            List of records as dicts.
        """
        # Map IDO name to table name (remove SL prefix if present)
        table_name = ido_name
        if table_name.startswith("SL"):
            table_name = table_name[2:]

        # Build SELECT clause
        if properties:
            select = ", ".join(properties)
        else:
            select = "*"

        # Build query
        sql = f"SELECT {select} FROM {table_name}"
        if filter_expr:
            sql += f" WHERE {filter_expr}"
        sql += f" LIMIT {limit}"

        try:
            return self.query(sql)
        except sqlite3.OperationalError as e:
            logger.error(f"Query failed for {ido_name}: {e}")
            return []

    def create_tables(self) -> None:
        """Create test database tables matching SyteLine IDO structure."""
        # Jobs table (SLJobs)
        self.execute("""
            CREATE TABLE IF NOT EXISTS Jobs (
                Job TEXT PRIMARY KEY,
                Suffix INTEGER DEFAULT 0,
                Item TEXT,
                Description TEXT,
                QtyReleased REAL,
                QtyComplete REAL,
                CustNum TEXT,
                CustName TEXT,
                Status TEXT DEFAULT 'R',
                OrderDate TEXT,
                DueDate TEXT
            )
        """)

        # Job Routes table (SLJobRoutes)
        self.execute("""
            CREATE TABLE IF NOT EXISTS JobRoutes (
                Job TEXT,
                Suffix INTEGER DEFAULT 0,
                OperNum INTEGER,
                Wc TEXT,
                WcDescription TEXT,
                StartDate TEXT,
                EndDate TEXT,
                Status TEXT DEFAULT 'R',
                RunHrsRemaining REAL,
                PRIMARY KEY (Job, Suffix, OperNum)
            )
        """)

        # Customer Orders table (SLCos)
        self.execute("""
            CREATE TABLE IF NOT EXISTS Cos (
                CoNum TEXT PRIMARY KEY,
                CustNum TEXT,
                CustName TEXT,
                OrderDate TEXT,
                Stat TEXT DEFAULT 'O'
            )
        """)

        # Customer Order Lines table (SLCoItems)
        self.execute("""
            CREATE TABLE IF NOT EXISTS CoItems (
                CoNum TEXT,
                CoLine INTEGER,
                Item TEXT,
                Description TEXT,
                QtyOrdered REAL,
                QtyShipped REAL,
                DueDate TEXT,
                Stat TEXT DEFAULT 'O',
                PRIMARY KEY (CoNum, CoLine)
            )
        """)

        # Customers table (SLCustomers)
        self.execute("""
            CREATE TABLE IF NOT EXISTS Customers (
                CustNum TEXT PRIMARY KEY,
                Name TEXT,
                Addr1 TEXT,
                Addr2 TEXT,
                City TEXT,
                State TEXT,
                Zip TEXT,
                Country TEXT DEFAULT 'USA',
                Phone TEXT,
                Contact TEXT,
                Email TEXT,
                CustType TEXT,
                Stat TEXT DEFAULT 'A'
            )
        """)

        # Items table (SLItems)
        self.execute("""
            CREATE TABLE IF NOT EXISTS Items (
                Item TEXT PRIMARY KEY,
                Description TEXT,
                UM TEXT DEFAULT 'EA',
                ProductCode TEXT,
                Stat TEXT DEFAULT 'A'
            )
        """)

        # Item Locations table (SLItemLocs)
        self.execute("""
            CREATE TABLE IF NOT EXISTS ItemLocs (
                Item TEXT,
                Whse TEXT,
                Loc TEXT,
                QtyOnHand REAL DEFAULT 0,
                QtyRsvd REAL DEFAULT 0,
                SafetyStockQty REAL DEFAULT 0,
                PRIMARY KEY (Item, Whse, Loc)
            )
        """)

        self.commit()
        logger.info("Test database tables created")

    def clear_all_data(self) -> None:
        """Clear all data from tables."""
        tables = ["Jobs", "JobRoutes", "Cos", "CoItems", "Customers", "Items", "ItemLocs"]
        for table in tables:
            self.execute(f"DELETE FROM {table}")
        self.commit()
        logger.info("All test data cleared")
