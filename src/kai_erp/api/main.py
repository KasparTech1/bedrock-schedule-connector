"""
FastAPI Application
===================

REST API server for the KAI ERP Connector.
Provides endpoints for production schedule, sales orders, customers, and inventory.
"""

from contextlib import asynccontextmanager
from typing import Any

import structlog
from fastapi import Depends, FastAPI, HTTPException, Query, Request
from fastapi.middleware.cors import CORSMiddleware
from slowapi import _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded

from kai_erp.config import get_config
from kai_erp.api.rate_limit import limiter, rate_limit_exceeded_handler
from kai_erp.api.errors import setup_exception_handlers
from kai_erp.api.dependencies import get_engine_manager, get_optional_engine
from kai_erp.api.metrics import setup_metrics
from kai_erp.core import RestEngine
from kai_erp.connectors import (
    BedrockOpsScheduler,
    CustomerSearch,
    InventoryStatus,
    SalesOrderTracker,
)
from kai_erp.api.registry_routes import router as registry_router
from kai_erp.api.testdb_routes import router as testdb_router
from kai_erp.api.bedrock_routes import router as bedrock_router
from kai_erp.api.legacy_routes import router as legacy_router
from kai_erp.api.public_api import router as public_api_router
from kai_erp.api.auth_routes import router as auth_router

logger = structlog.get_logger(__name__)

# Compatibility: older tests patch this symbol directly.
# The API now uses EngineManager + dependencies, but keeping this avoids AttributeError.
_engine = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan handler for startup/shutdown."""
    config = get_config()
    manager = get_engine_manager()
    
    logger.info("Starting KAI ERP Connector API")
    
    # Initialize REST engine only if SyteLine config is provided.
    # This allows the API/UI to boot in dev/test environments without ERP credentials.
    syteline_ready = (
        bool(config.syteline.base_url)
        and bool(config.syteline.config_name)
        and bool(config.syteline.username)
        and bool(config.syteline.password.get_secret_value())
    )
    if syteline_ready:
        await manager.initialize(config.syteline)
    else:
        logger.warning("SyteLine not configured; skipping engine init")
    
    logger.info("API ready", port=config.server.port)
    
    yield
    
    # Cleanup
    await manager.shutdown()
    
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

# Configure rate limiting
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, rate_limit_exceeded_handler)

# Configure structured error handling
setup_exception_handlers(app)

# Configure Prometheus metrics
setup_metrics(app)

# Include routers
app.include_router(auth_router)  # Authentication endpoints (/auth/token, /auth/refresh)
app.include_router(registry_router)
app.include_router(testdb_router)
app.include_router(bedrock_router)  # Bedrock production schedule (Mongoose REST API)
app.include_router(legacy_router)  # Legacy ERP connectors (Global Shop)
app.include_router(public_api_router)  # Public API with authentication (X-API-Key)


# ─────────────────────────────────────────────────────────────────────────────
# Health Endpoint
# ─────────────────────────────────────────────────────────────────────────────

@app.get("/health")
@limiter.limit("120/minute")  # Higher limit for health checks (monitoring)
async def health_check(request: Request) -> dict[str, Any]:
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
@limiter.limit("30/minute")  # Rate limit for data queries
async def get_production_schedule(
    request: Request,
    engine: RestEngine | None = Depends(get_optional_engine),
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
    if engine is None:
        raise HTTPException(status_code=503, detail="Service not initialized. REST engine unavailable.")

    connector = BedrockOpsScheduler(engine)
    
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
@limiter.limit("30/minute")
async def get_open_orders(
    request: Request,
    engine: RestEngine | None = Depends(get_optional_engine),
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
    if engine is None:
        raise HTTPException(status_code=503, detail="Service not initialized. REST engine unavailable.")

    connector = SalesOrderTracker(engine)
    
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
@limiter.limit("30/minute")
async def search_customers(
    request: Request,
    engine: RestEngine | None = Depends(get_optional_engine),
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
    if engine is None:
        raise HTTPException(status_code=503, detail="Service not initialized. REST engine unavailable.")

    connector = CustomerSearch(engine)
    
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
@limiter.limit("30/minute")
async def get_inventory_status(
    request: Request,
    engine: RestEngine | None = Depends(get_optional_engine),
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
    if engine is None:
        raise HTTPException(status_code=503, detail="Service not initialized. REST engine unavailable.")

    connector = InventoryStatus(engine)
    
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
