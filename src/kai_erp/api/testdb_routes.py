"""API routes for the Test Database."""

from typing import Any

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel

from kai_erp.testdb import TestDatabaseEngine, seed_test_data

router = APIRouter(prefix="/api/testdb", tags=["Test Database"])

# Global test database instance
_engine: TestDatabaseEngine | None = None


def get_engine() -> TestDatabaseEngine:
    """Get or create the test database engine."""
    global _engine
    if _engine is None:
        _engine = TestDatabaseEngine()
        _engine.connect()
    return _engine


class SeedRequest(BaseModel):
    """Request to seed test data."""

    num_jobs: int = 20
    num_orders: int = 15


class QueryRequest(BaseModel):
    """Request to query the test database."""

    ido_name: str
    properties: list[str] | None = None
    filter_expr: str | None = None
    limit: int = 100


@router.get("/status")
async def get_status() -> dict[str, Any]:
    """Get test database status."""
    engine = get_engine()
    
    # Get table counts
    tables = {
        "Jobs": engine.query("SELECT COUNT(*) as count FROM Jobs")[0]["count"],
        "JobRoutes": engine.query("SELECT COUNT(*) as count FROM JobRoutes")[0]["count"],
        "Cos": engine.query("SELECT COUNT(*) as count FROM Cos")[0]["count"],
        "CoItems": engine.query("SELECT COUNT(*) as count FROM CoItems")[0]["count"],
        "Customers": engine.query("SELECT COUNT(*) as count FROM Customers")[0]["count"],
        "Items": engine.query("SELECT COUNT(*) as count FROM Items")[0]["count"],
        "ItemLocs": engine.query("SELECT COUNT(*) as count FROM ItemLocs")[0]["count"],
    }
    
    return {
        "connected": True,
        "db_path": str(engine.db_path),
        "tables": tables,
        "total_records": sum(tables.values()),
    }


@router.post("/seed")
async def seed_database(request: SeedRequest) -> dict[str, str]:
    """Seed the test database with sample data."""
    engine = get_engine()
    seed_test_data(engine, num_jobs=request.num_jobs, num_orders=request.num_orders)
    return {"message": f"Seeded {request.num_jobs} jobs and {request.num_orders} orders"}


@router.post("/clear")
async def clear_database() -> dict[str, str]:
    """Clear all test data."""
    engine = get_engine()
    engine.clear_all_data()
    return {"message": "All test data cleared"}


@router.post("/query")
async def query_ido(request: QueryRequest) -> dict[str, Any]:
    """Query an IDO table."""
    engine = get_engine()
    
    results = engine.query_ido(
        ido_name=request.ido_name,
        properties=request.properties,
        filter_expr=request.filter_expr,
        limit=request.limit,
    )
    
    return {
        "ido": request.ido_name,
        "records": results,
        "count": len(results),
    }


@router.get("/tables")
async def list_tables() -> list[str]:
    """List available test database tables."""
    return ["SLJobs", "SLJobRoutes", "SLCos", "SLCoItems", "SLCustomers", "SLItems", "SLItemLocs"]


@router.get("/tables/{table_name}")
async def get_table_data(
    table_name: str,
    limit: int = Query(50, ge=1, le=1000),
) -> dict[str, Any]:
    """Get data from a specific table."""
    engine = get_engine()
    
    # Remove SL prefix if present
    actual_table = table_name[2:] if table_name.startswith("SL") else table_name
    
    try:
        results = engine.query(f"SELECT * FROM {actual_table} LIMIT ?", (limit,))
        return {
            "table": table_name,
            "records": results,
            "count": len(results),
        }
    except Exception as e:
        raise HTTPException(status_code=404, detail=f"Table not found: {table_name}")
