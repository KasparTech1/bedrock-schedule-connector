"""
Simple UI Server for KAI ERP Connector Catalog
==============================================

A lightweight server that only exposes the registry and test database
endpoints, without requiring SyteLine configuration.
"""

from contextlib import asynccontextmanager

import structlog
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from kai_erp.api.registry_routes import router as registry_router
from kai_erp.api.testdb_routes import router as testdb_router
from kai_erp.api.demo_routes import router as demo_router
from kai_erp.api.chat_routes import router as chat_router
from kai_erp.api.bedrock_routes import router as bedrock_router

logger = structlog.get_logger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan handler."""
    logger.info("Starting KAI ERP Connector Catalog UI Server")
    yield
    logger.info("UI Server shutdown")


# Create FastAPI app
app = FastAPI(
    title="KAI ERP Connector Catalog",
    description="UI Server for managing ERP connectors",
    version="1.0.0",
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc"
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(registry_router)
app.include_router(testdb_router)
app.include_router(demo_router)
app.include_router(chat_router)
app.include_router(bedrock_router)  # Live Bedrock Truck Beds data


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {
        "status": "healthy",
        "service": "kai-erp-connector-catalog",
        "version": "1.0.0"
    }


def run():
    """Run the UI server."""
    import uvicorn
    
    uvicorn.run(
        "kai_erp.api.ui_server:app",
        host="0.0.0.0",
        port=8100,
        log_level="info",
        reload=True
    )


if __name__ == "__main__":
    run()
