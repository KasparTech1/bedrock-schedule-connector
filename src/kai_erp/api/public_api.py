"""
Public API Routes
=================

External-facing API endpoints for kai_erp connectors.

These endpoints are designed for:
- External integrations (third-party apps, custom tools)
- Internal microservices
- AI agents and automation tools
- Mobile applications

All endpoints require API key authentication via X-API-Key header.

Base URL: https://your-domain.com/api/v1
"""

from datetime import datetime, timezone
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query
import structlog

from kai_erp.api.auth import (
    APIKey,
    APIScope,
    require_api_key,
    require_scope,
    get_key_manager,
)
from kai_erp.adapters.syteline10_cloud import BedrockScheduler, MongooseConfig

logger = structlog.get_logger(__name__)

# Create router with prefix and tags
router = APIRouter(
    prefix="/api/v1",
    tags=["Public API"],
    responses={
        401: {"description": "Invalid or missing API key"},
        403: {"description": "Insufficient permissions"},
        429: {"description": "Rate limit exceeded"},
    }
)

# Lazy-initialized scheduler
_scheduler: Optional[BedrockScheduler] = None


def get_scheduler() -> BedrockScheduler:
    """Get or create scheduler instance."""
    global _scheduler
    if _scheduler is None:
        config = MongooseConfig.bedrock_tbe()
        _scheduler = BedrockScheduler(config)
    return _scheduler


# =============================================================================
# CUSTOMER SEARCH API
# =============================================================================

@router.get(
    "/customers",
    summary="Search Customers",
    description="""
Search for customers in Bedrock Truck Beds SyteLine system.

**Use Cases:**
- Customer lookup for quoting/ordering
- CRM integration
- Address validation
- Customer analytics

**Rate Limits:**
- 60 requests/minute (standard)
- 10,000 requests/day (standard)

**Example Request:**
```bash
curl -X GET "https://api.kai-erp.com/api/v1/customers?search=acme&limit=10" \\
  -H "X-API-Key: your_api_key_here"
```

**Example Response:**
```json
{
  "success": true,
  "data": {
    "total_count": 3,
    "customers": [
      {
        "cust_num": "C000123",
        "name": "Acme Corp",
        "city": "Houston",
        "state": "TX",
        "phone": "555-123-4567"
      }
    ]
  },
  "meta": {
    "request_id": "abc123",
    "timestamp": "2025-12-11T15:30:00Z"
  }
}
```
""",
    response_description="List of matching customers",
)
async def search_customers(
    search: Optional[str] = Query(None, description="Search term (matches name or customer number)"),
    customer_number: Optional[str] = Query(None, description="Exact customer number lookup"),
    city: Optional[str] = Query(None, description="Filter by city"),
    state: Optional[str] = Query(None, description="Filter by state code (e.g., TX, CA)"),
    status: Optional[str] = Query("A", description="Customer status: A=Active, I=Inactive"),
    limit: int = Query(50, ge=1, le=200, description="Maximum results to return"),
    api_key: APIKey = Depends(require_scope(APIScope.READ_CUSTOMERS)),
):
    """
    Search and retrieve customer information.
    
    Requires scope: customers:read
    """
    try:
        scheduler = get_scheduler()
        result = await scheduler.search_customers(
            search_term=search,
            customer_number=customer_number,
            city=city,
            state=state,
            status=status,
            limit=limit,
        )
        
        return {
            "success": True,
            "data": {
                "total_count": result.total_count,
                "customers": [
                    {
                        "cust_num": c.cust_num,
                        "name": c.name,
                        "addr1": c.addr1,
                        "addr2": c.addr2,
                        "city": c.city,
                        "state": c.state,
                        "zip_code": c.zip_code,
                        "country": c.country,
                        "phone": c.phone,
                        "contact": c.contact,
                        "email": c.email,
                        "cust_type": c.cust_type,
                        "status": c.status,
                    }
                    for c in result.customers
                ],
            },
            "meta": {
                "timestamp": datetime.now(timezone.utc).isoformat() + "Z",
                "api_key_id": api_key.key_id,
            }
        }
    except Exception as e:
        logger.error("Customer search failed", error=str(e), api_key=api_key.key_id)
        raise HTTPException(status_code=500, detail=str(e))


@router.get(
    "/customers/{customer_number}",
    summary="Get Customer by Number",
    description="Retrieve detailed information for a specific customer.",
)
async def get_customer(
    customer_number: str,
    api_key: APIKey = Depends(require_scope(APIScope.READ_CUSTOMERS)),
):
    """Get a specific customer by customer number."""
    try:
        scheduler = get_scheduler()
        customer = await scheduler.get_customer(customer_number)
        
        if not customer:
            raise HTTPException(status_code=404, detail=f"Customer {customer_number} not found")
        
        return {
            "success": True,
            "data": {
                "cust_num": customer.cust_num,
                "name": customer.name,
                "addr1": customer.addr1,
                "addr2": customer.addr2,
                "city": customer.city,
                "state": customer.state,
                "zip_code": customer.zip_code,
                "country": customer.country,
                "phone": customer.phone,
                "contact": customer.contact,
                "email": customer.email,
                "cust_type": customer.cust_type,
                "status": customer.status,
            },
            "meta": {
                "timestamp": datetime.now(timezone.utc).isoformat() + "Z",
            }
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Get customer failed", customer=customer_number, error=str(e))
        raise HTTPException(status_code=500, detail=str(e))


# =============================================================================
# ORDER AVAILABILITY API
# =============================================================================

@router.get(
    "/orders/availability",
    summary="Get Order Availability",
    description="""
Get customer order availability with inventory allocation analysis.

Shows open orders with how inventory is allocated from production stages:
1. On Hand inventory (immediate)
2. Paint queue (nearly complete)
3. Blast queue (in process)
4. Released Weld/Fab (early production)

**Use Cases:**
- Customer service: Answer "When will my order ship?"
- Sales: Check coverage before promising delivery
- Production planning: Identify shortage risks
- Dashboards: Overall coverage visibility

**Example Request:**
```bash
curl -X GET "https://api.kai-erp.com/api/v1/orders/availability?shortage_only=true&limit=100" \\
  -H "X-API-Key: your_api_key_here"
```
""",
)
async def get_order_availability(
    customer: Optional[str] = Query(None, description="Filter by customer name (partial match)"),
    item: Optional[str] = Query(None, description="Filter by item number (partial match)"),
    shortage_only: bool = Query(False, description="Only return orders with shortages"),
    limit: int = Query(500, ge=1, le=1000, description="Maximum order lines to return"),
    api_key: APIKey = Depends(require_scope(APIScope.READ_ORDERS)),
):
    """Get order availability with allocation analysis."""
    try:
        scheduler = get_scheduler()
        result = await scheduler.get_order_availability(
            customer=customer,
            item=item,
            limit=limit,
        )
        
        order_lines = result.order_lines
        
        # Filter for shortages if requested
        if shortage_only:
            order_lines = [
                ol for ol in order_lines
                if ol.qty_remaining > ol.qty_remaining_covered
            ]
        
        # Calculate summary
        total_remaining = sum(ol.qty_remaining for ol in order_lines)
        total_covered = sum(ol.qty_remaining_covered for ol in order_lines)
        total_shortage = max(0, total_remaining - total_covered)
        
        return {
            "success": True,
            "data": {
                "order_lines": [
                    {
                        "co_num": ol.co_num,
                        "co_line": ol.co_line,
                        "customer_name": ol.customer_name,
                        "due_date": ol.due_date,
                        "item": ol.item,
                        "item_description": ol.item_description,
                        "qty_remaining": ol.qty_remaining,
                        "qty_covered": ol.qty_remaining_covered,
                        "shortage": max(0, ol.qty_remaining - ol.qty_remaining_covered),
                        "coverage_pct": round(
                            (ol.qty_remaining_covered / ol.qty_remaining * 100)
                            if ol.qty_remaining > 0 else 100,
                            1
                        ),
                        "allocation": {
                            "on_hand": ol.qty_on_hand,
                            "from_paint": ol.allocated_from_paint,
                            "from_blast": ol.allocated_from_blast,
                            "from_weld_fab": ol.allocated_from_released_weld_fab,
                        },
                        "estimated_dates": {
                            "weld_fab_complete": ol.weld_fab_completion_date,
                            "blast_complete": ol.blast_completion_date,
                            "paint_complete": ol.paint_assembly_completion_date,
                        }
                    }
                    for ol in order_lines
                ],
                "summary": {
                    "total_lines": len(order_lines),
                    "total_qty_remaining": total_remaining,
                    "total_qty_covered": total_covered,
                    "total_shortage": total_shortage,
                    "coverage_percentage": round(
                        (total_covered / total_remaining * 100) if total_remaining > 0 else 100,
                        1
                    ),
                },
            },
            "meta": {
                "timestamp": datetime.now(timezone.utc).isoformat() + "Z",
                "filters_applied": {
                    "customer": customer,
                    "item": item,
                    "shortage_only": shortage_only,
                },
            }
        }
    except Exception as e:
        logger.error("Order availability failed", error=str(e))
        raise HTTPException(status_code=500, detail=str(e))


# =============================================================================
# SCHEDULE / JOBS API
# =============================================================================

@router.get(
    "/jobs",
    summary="Get Production Jobs",
    description="Get manufacturing jobs with operations and status.",
)
async def get_jobs(
    status: Optional[str] = Query(None, description="Filter by status: F=Firm, R=Released"),
    work_center: Optional[str] = Query(None, description="Filter by work center"),
    include_complete: bool = Query(False, description="Include completed jobs"),
    limit: int = Query(100, ge=1, le=500),
    api_key: APIKey = Depends(require_scope(APIScope.READ_JOBS)),
):
    """Get production jobs."""
    try:
        scheduler = get_scheduler()
        overview = await scheduler.get_schedule_overview(
            include_complete=include_complete,
            limit=limit,
        )
        
        jobs = overview.jobs
        
        # Filter by work center if specified
        if work_center:
            jobs = [
                j for j in jobs
                if any(op.work_center == work_center for op in j.operations)
            ]
        
        return {
            "success": True,
            "data": {
                "total_jobs": len(jobs),
                "jobs": [
                    {
                        "job": j.job,
                        "suffix": j.suffix,
                        "item": j.item,
                        "item_description": j.item_description,
                        "qty_released": j.qty_released,
                        "qty_complete": j.qty_complete,
                        "pct_complete": j.pct_complete,
                        "status": j.status,
                        "customer_name": j.customer_name,
                        "operations": [
                            {
                                "operation_num": op.operation_num,
                                "work_center": op.work_center,
                                "qty_complete": op.qty_complete,
                            }
                            for op in j.operations
                        ],
                    }
                    for j in jobs
                ],
                "work_centers": overview.work_centers,
            },
            "meta": {
                "timestamp": datetime.now(timezone.utc).isoformat() + "Z",
            }
        }
    except Exception as e:
        logger.error("Get jobs failed", error=str(e))
        raise HTTPException(status_code=500, detail=str(e))


@router.get(
    "/jobs/{job_number}",
    summary="Get Job Details",
    description="Get detailed information for a specific job.",
)
async def get_job(
    job_number: str,
    suffix: int = Query(0, ge=0),
    api_key: APIKey = Depends(require_scope(APIScope.READ_JOBS)),
):
    """Get a specific job by number."""
    try:
        scheduler = get_scheduler()
        job = await scheduler.get_job_details(job_number, suffix)
        
        if not job:
            raise HTTPException(status_code=404, detail=f"Job {job_number} not found")
        
        return {
            "success": True,
            "data": {
                "job": job.job,
                "suffix": job.suffix,
                "item": job.item,
                "item_description": job.item_description,
                "qty_released": job.qty_released,
                "qty_complete": job.qty_complete,
                "pct_complete": job.pct_complete,
                "is_complete": job.is_complete,
                "status": job.status,
                "customer_name": job.customer_name,
                "operations": [
                    {
                        "operation_num": op.operation_num,
                        "work_center": op.work_center,
                        "qty_complete": op.qty_complete,
                        "qty_scrapped": op.qty_scrapped,
                    }
                    for op in job.operations
                ],
            },
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Get job failed", job=job_number, error=str(e))
        raise HTTPException(status_code=500, detail=str(e))


# =============================================================================
# API KEY MANAGEMENT (Admin only)
# =============================================================================

@router.get(
    "/admin/keys",
    summary="List API Keys",
    description="List all API keys (admin only).",
    tags=["Admin"],
)
async def list_api_keys(
    api_key: APIKey = Depends(require_scope(APIScope.ADMIN)),
):
    """List all API keys."""
    manager = get_key_manager()
    return {
        "success": True,
        "data": {
            "keys": manager.list_keys(),
        }
    }


@router.post(
    "/admin/keys",
    summary="Create API Key",
    description="Create a new API key (admin only).",
    tags=["Admin"],
)
async def create_api_key(
    name: str = Query(..., description="Key name"),
    owner: str = Query(..., description="Owner email"),
    scopes: str = Query("*", description="Comma-separated scopes"),
    expires_days: Optional[int] = Query(None, description="Days until expiration"),
    api_key: APIKey = Depends(require_scope(APIScope.ADMIN)),
):
    """Create a new API key."""
    manager = get_key_manager()
    
    # Parse scopes
    scope_list = []
    for s in scopes.split(","):
        s = s.strip()
        if s == "*":
            scope_list.append(APIScope.ALL)
        else:
            try:
                scope_list.append(APIScope(s))
            except ValueError:
                raise HTTPException(status_code=400, detail=f"Invalid scope: {s}")
    
    key_id, secret_key = manager.create_key(
        name=name,
        owner=owner,
        scopes=scope_list,
        expires_in_days=expires_days,
    )
    
    return {
        "success": True,
        "data": {
            "key_id": key_id,
            "secret_key": secret_key,  # Only shown once!
            "message": "Save this secret key - it won't be shown again!",
        }
    }


@router.delete(
    "/admin/keys/{key_id}",
    summary="Revoke API Key",
    description="Revoke an API key (admin only).",
    tags=["Admin"],
)
async def revoke_api_key(
    key_id: str,
    api_key: APIKey = Depends(require_scope(APIScope.ADMIN)),
):
    """Revoke an API key."""
    manager = get_key_manager()
    
    if not manager.revoke_key(key_id):
        raise HTTPException(status_code=404, detail=f"Key {key_id} not found")
    
    return {
        "success": True,
        "message": f"Key {key_id} has been revoked",
    }


# =============================================================================
# HEALTH / INFO
# =============================================================================

@router.get(
    "/health",
    summary="API Health Check",
    description="Check if the API is healthy and can connect to SyteLine.",
)
async def health_check(
    api_key: APIKey = Depends(require_api_key),
):
    """Health check endpoint."""
    try:
        scheduler = get_scheduler()
        # Quick test - fetch 1 job
        overview = await scheduler.get_schedule_overview(limit=1)
        
        return {
            "status": "healthy",
            "syteline_connected": True,
            "work_centers_available": len(overview.work_centers),
            "timestamp": datetime.now(timezone.utc).isoformat() + "Z",
        }
    except Exception as e:
        return {
            "status": "degraded",
            "syteline_connected": False,
            "error": str(e),
            "timestamp": datetime.now(timezone.utc).isoformat() + "Z",
        }
