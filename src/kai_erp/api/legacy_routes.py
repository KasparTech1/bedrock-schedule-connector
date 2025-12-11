"""
Legacy ERP API Routes
=====================

API endpoints for legacy ERP connectors (Global Shop, etc.)
These endpoints provide access to subsidiary legacy systems during ERP migration.

Note: These routes use external bridge APIs, not standard SyteLine IDO calls.
"""

from fastapi import APIRouter, Query
from pydantic import BaseModel
from typing import Any

from kai_erp.adapters.legacy_global_shop.client import DEFAULT_LIMIT, GlobalShopBridgeClient

router = APIRouter(prefix="/api/legacy", tags=["Legacy ERP"])

_global_shop = GlobalShopBridgeClient()


class ProductLineResponse(BaseModel):
    """Response model for product lines."""
    product_lines: list[dict[str, Any]]
    summary: dict[str, Any]


class GlobalShopQueryResponse(BaseModel):
    """Generic response model for Global Shop queries."""
    data: list[dict[str, Any]]
    summary: dict[str, Any]


# ─────────────────────────────────────────────────────────────────────────────
# Health Check
# ─────────────────────────────────────────────────────────────────────────────

@router.get("/global-shop/health")
async def global_shop_health() -> dict[str, Any]:
    """
    Check Global Shop bridge connectivity.
    
    Tests the connection to the Pervasive SQL bridge and returns health status.
    """
    return await _global_shop.health()


# ─────────────────────────────────────────────────────────────────────────────
# Product Lines (PRODLINE_MRE)
# ─────────────────────────────────────────────────────────────────────────────

@router.get("/global-shop/product-lines", response_model=ProductLineResponse)
async def get_product_lines(
    product_line: str | None = Query(
        None,
        description="Filter by specific product line code"
    ),
    limit: int = Query(
        DEFAULT_LIMIT,
        description="Maximum records to return",
        ge=1,
        le=1000
    )
) -> ProductLineResponse:
    """
    Get all product lines from Global Shop.
    
    Queries the PRODLINE_MRE table from the Pervasive SQL database.
    Returns product line codes, descriptions, cost centers, and account mappings.
    
    **Table:** PRODLINE_MRE  
    **Source:** Global Shop (Circle Brands)  
    **Status:** Legacy - Transitional
    
    ## Example Response
    
    ```json
    {
      "product_lines": [
        {
          "PRODLINE": "ELEC",
          "DESCRIP": "Electronics",
          "COST_CENTER": "100",
          "ACCOUNT": "4000"
        }
      ],
      "summary": {
        "total": 1,
        "query": "SELECT TOP 500 * FROM prodline_mre",
        "source": "Global Shop (Pervasive SQL)"
      }
    }
    ```
    """
    payload = await _global_shop.get_product_lines(product_line=product_line, limit=limit)
    return ProductLineResponse(product_lines=payload["product_lines"], summary=payload["summary"])


# ─────────────────────────────────────────────────────────────────────────────
# Salespersons (V_SALESPERSONS)
# ─────────────────────────────────────────────────────────────────────────────

@router.get("/global-shop/salespersons", response_model=GlobalShopQueryResponse)
async def get_salespersons(
    salesperson: str | None = Query(
        None,
        description="Filter by salesperson ID"
    ),
    limit: int = Query(
        DEFAULT_LIMIT,
        description="Maximum records to return",
        ge=1,
        le=1000
    )
) -> GlobalShopQueryResponse:
    """
    Get sales personnel from Global Shop.
    
    Queries the V_SALESPERSONS view for salesperson data including
    IDs, names, and commission information.
    
    **View:** V_SALESPERSONS  
    **Source:** Global Shop (Circle Brands)  
    **Status:** Legacy - Transitional
    
    ## Example Response
    
    ```json
    {
      "data": [
        {
          "SALESSION": "SP001",
          "NAME": "John Smith",
          "COMMISSION": 0.05
        }
      ],
      "summary": {
        "total": 1,
        "query": "SELECT TOP 500 * FROM V_SALESPERSONS",
        "source": "Global Shop (Pervasive SQL)"
      }
    }
    ```
    """
    payload = await _global_shop.get_salespersons(salesperson=salesperson, limit=limit)
    return GlobalShopQueryResponse(data=payload["data"], summary=payload["summary"])


# ─────────────────────────────────────────────────────────────────────────────
# Raw SQL Query (Admin/Debug)
# ─────────────────────────────────────────────────────────────────────────────

@router.post("/global-shop/query", response_model=GlobalShopQueryResponse)
async def execute_raw_query(
    sql: str = Query(
        ...,
        description="SQL query to execute (SELECT only)"
    )
) -> GlobalShopQueryResponse:
    """
    Execute a raw SQL query against Global Shop.
    
    ⚠️ **Admin/Debug endpoint** - Use with caution.
    
    Only SELECT queries are allowed. The query is passed directly to the
    Pervasive SQL database via the bridge API.
    
    **Example:**
    ```
    SELECT TOP 25 * FROM prodline_mre
    ```
    """
    payload = await _global_shop.execute_raw_select(sql)
    return GlobalShopQueryResponse(data=payload["data"], summary=payload["summary"])
