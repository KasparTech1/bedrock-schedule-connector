"""
FastAPI Application
===================

REST API server for the KAI ERP Connector.
Provides endpoints for production schedule, sales orders, customers, and inventory.
"""

from contextlib import asynccontextmanager
from typing import Any

import structlog
from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware

from kai_erp.config import get_config
from kai_erp.core import RestEngine
from kai_erp.connectors import (
    BedrockOpsScheduler,
    CustomerSearch,
    InventoryStatus,
    SalesOrderTracker,
)

logger = structlog.get_logger(__name__)

# Global engine instance (initialized on startup)
_engine: RestEngine | None = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan handler for startup/shutdown."""
    global _engine
    
    config = get_config()
    
    logger.info("Starting KAI ERP Connector API")
    
    # Initialize REST engine
    _engine = RestEngine(config.syteline)
    await _engine.__aenter__()
    
    logger.info("API ready", port=config.server.port)
    
    yield
    
    # Cleanup
    if _engine:
        await _engine.__aexit__(None, None, None)
    
    logger.info("API shutdown complete")


# Create FastAPI app
app = FastAPI(
    title="KAI ERP Connector",
    description="AI-Ready ERP Data Access for SyteLine 10 CloudSuite",
    version="3.0.0",
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc"
)

# Configure CORS
config = get_config()
app.add_middleware(
    CORSMiddleware,
    allow_origins=config.server.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ─────────────────────────────────────────────────────────────────────────────
# Health Endpoint
# ─────────────────────────────────────────────────────────────────────────────

@app.get("/health")
async def health_check() -> dict[str, Any]:
    """
    Health check endpoint.
    
    Returns service status and version.
    """
    return {
        "status": "healthy",
        "service": "kai-erp-connector",
        "version": "3.0.0"
    }


# ─────────────────────────────────────────────────────────────────────────────
# Bedrock Production Schedule
# ─────────────────────────────────────────────────────────────────────────────

@app.get("/bedrock/schedule")
async def get_production_schedule(
    work_center: str | None = Query(
        None,
        description="Filter by work center code (e.g., 'WELD-01')"
    ),
    job: str | None = Query(
        None,
        description="Filter by job number (e.g., 'J-12345')"
    ),
    include_completed: bool = Query(
        False,
        description="Include 100% complete operations"
    )
) -> dict[str, Any]:
    """
    Get current production schedule for Bedrock operations.
    
    Returns scheduled operations showing what's being manufactured,
    where, and progress status.
    """
    if not _engine:
        raise HTTPException(status_code=503, detail="Service not initialized")
    
    connector = BedrockOpsScheduler(_engine)
    
    filters = {}
    if work_center:
        filters["work_center"] = work_center
    if job:
        filters["job"] = job
    if include_completed:
        filters["include_completed"] = include_completed
    
    try:
        result = await connector.execute(filters=filters if filters else None)
        
        return {
            "operations": result.data,
            "summary": {
                "total": result.record_count,
                "data_source": result.source.value,
                "query_ms": result.latency_ms
            }
        }
    except Exception as e:
        logger.error("Production schedule query failed", error=str(e))
        raise HTTPException(status_code=500, detail=str(e))


# ─────────────────────────────────────────────────────────────────────────────
# Sales Orders
# ─────────────────────────────────────────────────────────────────────────────

@app.get("/sales/orders")
async def get_open_orders(
    customer: str | None = Query(
        None,
        description="Filter by customer name or number (partial match)"
    ),
    days_out: int | None = Query(
        None,
        description="Only orders due within N days"
    )
) -> dict[str, Any]:
    """
    Get open sales orders that haven't shipped yet.
    
    Returns customer orders with line items, quantities, and due dates.
    """
    if not _engine:
        raise HTTPException(status_code=503, detail="Service not initialized")
    
    connector = SalesOrderTracker(_engine)
    
    filters = {}
    if customer:
        filters["customer"] = customer
    if days_out:
        filters["days_out"] = days_out
    
    try:
        result = await connector.execute(filters=filters if filters else None)
        
        return {
            "orders": result.data,
            "summary": {
                "total": result.record_count,
                "data_source": result.source.value,
                "query_ms": result.latency_ms
            }
        }
    except Exception as e:
        logger.error("Sales order query failed", error=str(e))
        raise HTTPException(status_code=500, detail=str(e))


# ─────────────────────────────────────────────────────────────────────────────
# Customer Search
# ─────────────────────────────────────────────────────────────────────────────

@app.get("/customers/search")
async def search_customers(
    query: str = Query(
        ...,
        description="Search term: name, number, city, or state"
    ),
    active_only: bool = Query(
        True,
        description="Only active customers"
    )
) -> dict[str, Any]:
    """
    Search for customer information.
    
    Returns customer details including contact info and account status.
    """
    if not _engine:
        raise HTTPException(status_code=503, detail="Service not initialized")
    
    connector = CustomerSearch(_engine)
    
    filters = {
        "query": query,
        "active_only": active_only
    }
    
    try:
        result = await connector.execute(filters=filters)
        
        return {
            "customers": result.data,
            "summary": {
                "total": result.record_count,
                "data_source": result.source.value,
                "query_ms": result.latency_ms
            }
        }
    except Exception as e:
        logger.error("Customer search failed", error=str(e))
        raise HTTPException(status_code=500, detail=str(e))


# ─────────────────────────────────────────────────────────────────────────────
# Inventory Status
# ─────────────────────────────────────────────────────────────────────────────

@app.get("/inventory/status")
async def get_inventory_status(
    item: str | None = Query(
        None,
        description="Item number to look up"
    ),
    warehouse: str | None = Query(
        None,
        description="Warehouse code to filter by"
    ),
    low_stock_only: bool = Query(
        False,
        description="Only items below reorder point"
    )
) -> dict[str, Any]:
    """
    Get current inventory levels.
    
    Returns quantity on hand, available, and location info.
    """
    if not _engine:
        raise HTTPException(status_code=503, detail="Service not initialized")
    
    connector = InventoryStatus(_engine)
    
    filters = {}
    if item:
        filters["item"] = item
    if warehouse:
        filters["warehouse"] = warehouse
    if low_stock_only:
        filters["low_stock_only"] = low_stock_only
    
    try:
        result = await connector.execute(filters=filters if filters else None)
        
        return {
            "inventory": result.data,
            "summary": {
                "total": result.record_count,
                "data_source": result.source.value,
                "query_ms": result.latency_ms
            }
        }
    except Exception as e:
        logger.error("Inventory query failed", error=str(e))
        raise HTTPException(status_code=500, detail=str(e))


# ─────────────────────────────────────────────────────────────────────────────
# Entry Point
# ─────────────────────────────────────────────────────────────────────────────

def run():
    """Run the API server."""
    import uvicorn
    
    config = get_config()
    
    uvicorn.run(
        "kai_erp.api.main:app",
        host=config.server.host,
        port=config.server.port,
        log_level=config.server.log_level.lower(),
        reload=config.server.environment.value == "development"
    )


if __name__ == "__main__":
    run()
