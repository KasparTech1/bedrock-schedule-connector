"""API routes for DEMO SyteLine connection."""

import os
from typing import Any

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel

from kai_erp.syteline import SyteLineClient, SyteLineConfig

router = APIRouter(prefix="/api/demo", tags=["Demo SyteLine"])

def _get_demo_config() -> SyteLineConfig:
    """Build demo SyteLine config from environment variables.

    Intentionally does not embed any credentials in source control.
    """
    username = os.getenv("DEMO_SL10_USERNAME")
    password = os.getenv("DEMO_SL10_PASSWORD")
    if not username or not password:
        raise HTTPException(
            status_code=503,
            detail="Demo SyteLine not configured. Set DEMO_SL10_USERNAME and DEMO_SL10_PASSWORD.",
        )

    return SyteLineConfig(
        base_url=os.getenv("DEMO_SL10_BASE_URL", "https://Csi10g.erpsl.inforcloudsuite.com"),
        config_name=os.getenv("DEMO_SL10_CONFIG_NAME", "DUU6QAFE74D2YDYW_TST_DALS"),
        username=username,
        password=password,
    )


class QueryRequest(BaseModel):
    """Request to query an IDO."""
    
    ido_name: str
    properties: list[str] | None = None
    filter_expr: str | None = None
    order_by: str | None = None
    row_cap: int = 10


@router.get("/health")
async def demo_health_check() -> dict[str, Any]:
    """Check if the demo SyteLine connection is working."""
    config = _get_demo_config()
    async with SyteLineClient(config) as client:
        healthy = await client.health_check()
        
    return {
        "status": "healthy" if healthy else "unhealthy",
        "base_url": config.base_url,
        "config_name": config.config_name,
    }


@router.get("/items")
async def get_demo_items(
    item: str | None = Query(None, description="Filter by item number"),
    product_code: str | None = Query(None, description="Filter by product code"),
    limit: int = Query(10, ge=1, le=100, description="Max rows to return"),
) -> dict[str, Any]:
    """Query items from the demo SyteLine environment."""
    
    # Build filter
    filters = []
    if item:
        filters.append(f"Item LIKE '%{item}%'")
    if product_code:
        filters.append(f"ProductCode = '{product_code}'")
    
    filter_expr = " AND ".join(filters) if filters else None
    
    properties = [
        "Item",
        "Description", 
        "ProductCode",
        "UM",
        "Stat",
        "itmUf_colorcode01",
        "itmUf_colorCode02",
        "itmUf_ColorCode03",
    ]
    
    try:
        config = _get_demo_config()
        async with SyteLineClient(config) as client:
            records = await client.query_ido(
                ido_name="SLItems",
                properties=properties,
                filter_expr=filter_expr,
                row_cap=limit,
            )
        
        return {
            "source": "syteline-demo",
            "base_url": config.base_url,
            "ido": "SLItems",
            "records": records,
            "count": len(records),
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/query")
async def query_demo_ido(request: QueryRequest) -> dict[str, Any]:
    """Query any IDO from the demo SyteLine environment."""
    
    try:
        config = _get_demo_config()
        async with SyteLineClient(config) as client:
            records = await client.query_ido(
                ido_name=request.ido_name,
                properties=request.properties,
                filter_expr=request.filter_expr,
                order_by=request.order_by,
                row_cap=request.row_cap,
            )
        
        return {
            "source": "syteline-demo",
            "base_url": config.base_url,
            "ido": request.ido_name,
            "records": records,
            "count": len(records),
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/idos")
async def list_common_idos() -> list[dict[str, str]]:
    """List commonly used SyteLine IDOs for reference."""
    return [
        {"name": "SLItems", "description": "Item master data"},
        {"name": "SLCustomers", "description": "Customer master data"},
        {"name": "SLCos", "description": "Customer order headers"},
        {"name": "SLCoItems", "description": "Customer order line items"},
        {"name": "SLJobs", "description": "Production job headers"},
        {"name": "SLJobRoutes", "description": "Job routing operations"},
        {"name": "SLItemLocs", "description": "Item inventory by location"},
        {"name": "SLShipments", "description": "Shipment headers"},
        {"name": "SLVendors", "description": "Vendor master data"},
        {"name": "SLPos", "description": "Purchase order headers"},
    ]
