"""
Bedrock Scheduler API Routes
============================

REST API endpoints for Bedrock production schedule data.
"""

from dataclasses import asdict
from typing import Optional

from fastapi import APIRouter, HTTPException, Query
import structlog

from kai_erp.adapters.syteline10_cloud import BedrockScheduler, MongooseConfig
from kai_erp.core.metrics import get_metrics_store, get_connector_anatomy

logger = structlog.get_logger(__name__)

router = APIRouter(prefix="/api/bedrock", tags=["Bedrock Scheduler"])

# Scheduler instance (lazy initialized)
_scheduler: Optional[BedrockScheduler] = None


def get_scheduler() -> BedrockScheduler:
    """Get or create scheduler instance (Bedrock Truck Beds TBE2)."""
    global _scheduler
    if _scheduler is None:
        config = MongooseConfig.bedrock_tbe()
        _scheduler = BedrockScheduler(config)
    return _scheduler


@router.get("/schedule")
async def get_schedule_overview(
    include_complete: bool = Query(False, description="Include completed jobs"),
    limit: int = Query(100, ge=1, le=500, description="Max jobs to return"),
):
    """
    Get overview of current production schedule.
    
    Returns all active jobs with their operations, organized by work center.
    """
    try:
        scheduler = get_scheduler()
        overview = await scheduler.get_schedule_overview(
            include_complete=include_complete,
            limit=limit
        )
        
        return {
            "success": True,
            "data": {
                "total_jobs": overview.total_jobs,
                "active_jobs": overview.active_jobs,
                "jobs_by_status": overview.jobs_by_status,
                "work_centers": overview.work_centers,
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
                        "customer_num": j.customer_num,
                        "customer_name": j.customer_name,
                        "operations": [
                            {
                                "operation_num": op.operation_num,
                                "work_center": op.work_center,
                                "qty_complete": op.qty_complete,
                                "qty_scrapped": op.qty_scrapped,
                            }
                            for op in j.operations
                        ]
                    }
                    for j in overview.jobs
                ],
                "fetched_at": overview.fetched_at.isoformat(),
            }
        }
    except Exception as e:
        logger.error("Failed to get schedule overview", error=str(e))
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/schedule/work-center/{work_center}")
async def get_work_center_jobs(
    work_center: str,
    include_complete: bool = Query(False, description="Include completed jobs"),
    limit: int = Query(50, ge=1, le=200, description="Max jobs to return"),
):
    """
    Get jobs with operations at a specific work center.
    """
    try:
        scheduler = get_scheduler()
        jobs = await scheduler.get_jobs_at_work_center(
            work_center=work_center,
            include_complete=include_complete,
            limit=limit
        )
        
        return {
            "success": True,
            "work_center": work_center,
            "job_count": len(jobs),
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
                    "operations": [
                        {
                            "operation_num": op.operation_num,
                            "work_center": op.work_center,
                            "qty_complete": op.qty_complete,
                        }
                        for op in j.operations
                        if op.work_center == work_center
                    ]
                }
                for j in jobs
            ]
        }
    except Exception as e:
        logger.error("Failed to get work center jobs", work_center=work_center, error=str(e))
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/schedule/work-center/{work_center}/queue")
async def get_work_center_queue(
    work_center: str,
    limit: int = Query(50, ge=1, le=200, description="Max operations to return"),
):
    """
    Get the queue of operations at a work center.
    
    Returns operations ordered by job number and operation sequence.
    """
    try:
        scheduler = get_scheduler()
        queue = await scheduler.get_work_center_queue(
            work_center=work_center,
            limit=limit
        )
        
        return {
            "success": True,
            "work_center": work_center,
            "operation_count": len(queue),
            "queue": queue
        }
    except Exception as e:
        logger.error("Failed to get work center queue", work_center=work_center, error=str(e))
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/job/{job_number}")
async def get_job_details(
    job_number: str,
    suffix: int = Query(0, ge=0, description="Job suffix"),
):
    """
    Get detailed information for a specific job.
    """
    try:
        scheduler = get_scheduler()
        job = await scheduler.get_job_details(job_number, suffix)
        
        if not job:
            raise HTTPException(status_code=404, detail=f"Job {job_number} not found")
        
        return {
            "success": True,
            "job": {
                "job": job.job,
                "suffix": job.suffix,
                "item": job.item,
                "item_description": job.item_description,
                "qty_released": job.qty_released,
                "qty_complete": job.qty_complete,
                "pct_complete": job.pct_complete,
                "is_complete": job.is_complete,
                "status": job.status,
                "customer_num": job.customer_num,
                "customer_name": job.customer_name,
                "operations": [
                    {
                        "operation_num": op.operation_num,
                        "work_center": op.work_center,
                        "qty_complete": op.qty_complete,
                        "qty_scrapped": op.qty_scrapped,
                    }
                    for op in job.operations
                ]
            }
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Failed to get job details", job=job_number, error=str(e))
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/work-centers")
async def get_work_centers():
    """
    Get list of all work centers with active operations.
    """
    try:
        scheduler = get_scheduler()
        overview = await scheduler.get_schedule_overview(limit=500)
        
        return {
            "success": True,
            "work_centers": overview.work_centers,
            "count": len(overview.work_centers)
        }
    except Exception as e:
        logger.error("Failed to get work centers", error=str(e))
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/health")
async def health_check():
    """
    Check if Bedrock API connection is healthy.
    """
    try:
        scheduler = get_scheduler()
        # Quick test - fetch just 1 job
        overview = await scheduler.get_schedule_overview(limit=1)
        
        return {
            "status": "healthy",
            "connected": True,
            "work_centers_available": len(overview.work_centers),
        }
    except Exception as e:
        logger.error("Health check failed", error=str(e))
        return {
            "status": "unhealthy",
            "connected": False,
            "error": str(e)
        }


# =============================================================================
# CUSTOMER SEARCH ENDPOINTS
# =============================================================================

@router.get("/customers")
async def search_customers(
    search: Optional[str] = Query(None, description="Search term for name or customer number"),
    customer_number: Optional[str] = Query(None, description="Exact customer number"),
    city: Optional[str] = Query(None, description="Filter by city"),
    state: Optional[str] = Query(None, description="Filter by state"),
    status: Optional[str] = Query(None, description="Filter by status (A=Active, I=Inactive)"),
    limit: int = Query(50, ge=1, le=200, description="Max customers to return"),
):
    """
    Search Bedrock Truck Beds customers.
    
    Returns customers matching the search criteria with contact and address information.
    """
    try:
        scheduler = get_scheduler()
        result = await scheduler.search_customers(
            search_term=search,
            customer_number=customer_number,
            city=city,
            state=state,
            status=status,
            limit=limit
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
                "fetched_at": result.fetched_at.isoformat(),
            }
        }
    except Exception as e:
        logger.error("Failed to search customers", error=str(e))
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/customers/{customer_number}")
async def get_customer(customer_number: str):
    """
    Get a specific customer by customer number.
    """
    try:
        scheduler = get_scheduler()
        customer = await scheduler.get_customer(customer_number)
        
        if not customer:
            raise HTTPException(status_code=404, detail=f"Customer {customer_number} not found")
        
        return {
            "success": True,
            "customer": {
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
            }
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Failed to get customer", customer_number=customer_number, error=str(e))
        raise HTTPException(status_code=500, detail=str(e))


# =============================================================================
# FLOW OPTIMIZER ENDPOINTS
# =============================================================================

@router.get("/order-availability")
async def get_order_availability(
    customer: Optional[str] = Query(None, description="Filter by customer name (partial match)"),
    item: Optional[str] = Query(None, description="Filter by item number (partial match)"),
    shortage_only: bool = Query(False, description="Only return orders with shortages"),
    limit: int = Query(500, ge=1, le=1000, description="Max order lines to return"),
):
    """
    Get customer order availability with inventory allocation analysis.
    
    Emulates the Syteline 8 TBE_Customer_Order_Availability_Add_Release_Date stored procedure.
    
    Shows open customer orders with how inventory is allocated from different
    production stages: On Hand → Paint → Blast → Weld/Fab. Calculates coverage
    and estimated completion dates based on business day calendar.
    
    Returns:
    - order_lines: List of order lines with allocation details
    - summary: Coverage statistics and totals
    
    Allocation Priority (by due date):
    1. On Hand inventory (immediate availability)
    2. Paint queue (nearly complete production)
    3. Blast queue (in process)
    4. Released Weld/Fab (early production)
    
    Estimated Completion Dates:
    - Weld/Fab: 4 business days from release
    - Blast: 7 business days from release
    - Paint/Assembly: 10 business days from release
    """
    try:
        scheduler = get_scheduler()
        result = await scheduler.get_order_availability(
            customer=customer,
            item=item,
            limit=limit
        )
        
        # Get order lines
        order_lines = result.order_lines
        
        # Filter for shortages if requested
        if shortage_only:
            order_lines = [
                ol for ol in order_lines
                if ol.qty_remaining > ol.qty_remaining_covered
            ]
        
        # Calculate summary statistics
        total_remaining = sum(ol.qty_remaining for ol in order_lines)
        total_covered = sum(ol.qty_remaining_covered for ol in order_lines)
        total_shortage = max(0, total_remaining - total_covered)
        total_amount = sum(ol.line_amount for ol in order_lines)
        
        lines_fully_covered = sum(
            1 for ol in order_lines 
            if ol.qty_remaining_covered >= ol.qty_remaining
        )
        lines_with_shortage = len(order_lines) - lines_fully_covered
        
        coverage_pct = round(
            (total_covered / total_remaining * 100) if total_remaining > 0 else 100,
            1
        )
        
        return {
            "success": True,
            "data": {
                "order_lines": [
                    {
                        "co_data_id": ol.co_data_id,
                        "co_num": ol.co_num,
                        "co_line": ol.co_line,
                        "co_release": ol.co_release,
                        "customer_name": ol.customer_name,
                        "order_date": ol.order_date,
                        "due_date": ol.due_date,
                        "released_date": ol.released_date,
                        "weld_fab_completion_date": ol.weld_fab_completion_date,
                        "blast_completion_date": ol.blast_completion_date,
                        "paint_assembly_completion_date": ol.paint_assembly_completion_date,
                        "item": ol.item,
                        "model": ol.model,
                        "item_description": ol.item_description,
                        "qty_ordered": ol.qty_ordered,
                        "qty_shipped": ol.qty_shipped,
                        "qty_remaining": ol.qty_remaining,
                        "qty_remaining_covered": ol.qty_remaining_covered,
                        "qty_on_hand": ol.qty_on_hand,
                        "current_on_hand": ol.current_on_hand,
                        "qty_nf": ol.qty_nf,
                        "qty_alloc_co": ol.qty_alloc_co,
                        "qty_wip": ol.qty_wip,
                        "qty_released": ol.qty_released,
                        "total_in_paint": ol.total_in_paint,
                        "allocated_from_paint": ol.allocated_from_paint,
                        "total_in_blast": ol.total_in_blast,
                        "allocated_from_blast": ol.allocated_from_blast,
                        "total_in_released_weld_fab": ol.total_in_released_weld_fab,
                        "allocated_from_released_weld_fab": ol.allocated_from_released_weld_fab,
                        "jobs": ol.jobs,
                        "line_amount": ol.line_amount,
                        "is_fully_covered": ol.qty_remaining_covered >= ol.qty_remaining,
                        "shortage": max(0, ol.qty_remaining - ol.qty_remaining_covered),
                        "coverage_percentage": round(
                            (ol.qty_remaining_covered / ol.qty_remaining * 100) 
                            if ol.qty_remaining > 0 else 100,
                            1
                        ),
                    }
                    for ol in order_lines
                ],
                "summary": {
                    "total_lines": len(order_lines),
                    "total_qty_remaining": total_remaining,
                    "total_qty_covered": total_covered,
                    "total_shortage": total_shortage,
                    "total_line_amount": total_amount,
                    "lines_fully_covered": lines_fully_covered,
                    "lines_with_shortage": lines_with_shortage,
                    "coverage_percentage": coverage_pct,
                },
                "fetched_at": result.fetched_at.isoformat(),
            }
        }
    except Exception as e:
        logger.error("Failed to get order availability", error=str(e))
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/order-availability/anatomy")
async def get_order_availability_anatomy():
    """
    Get the anatomy of the Order Availability connector.
    
    Returns:
    - Connector structure and configuration
    - IDO data sources with properties and filters
    - Processing logic steps
    - Allocation algorithm details
    - Historical run metrics and statistics
    """
    metrics_store = get_metrics_store()
    anatomy = get_connector_anatomy("order-availability")
    
    if not anatomy:
        raise HTTPException(status_code=404, detail="Connector anatomy not found")
    
    # Get aggregate stats from historical runs
    stats = metrics_store.get_aggregate_stats("order-availability")
    
    return {
        "success": True,
        "data": {
            "connector": anatomy.to_dict(),
            "metrics": stats,
        }
    }


@router.get("/connector/{connector_id}/anatomy")
async def get_connector_anatomy_by_id(connector_id: str):
    """
    Get the anatomy of any connector by ID.
    
    Supported connectors:
    - order-availability
    - flow-optimizer
    - customer-search
    """
    metrics_store = get_metrics_store()
    anatomy = get_connector_anatomy(connector_id)
    
    if not anatomy:
        raise HTTPException(
            status_code=404, 
            detail=f"Connector '{connector_id}' not found. Available: order-availability, flow-optimizer, customer-search"
        )
    
    # Get aggregate stats from historical runs
    stats = metrics_store.get_aggregate_stats(connector_id)
    
    return {
        "success": True,
        "data": {
            "connector": anatomy.to_dict(),
            "metrics": stats,
        }
    }


@router.get("/open-orders")
async def get_open_orders(limit: int = 500):
    """
    Get open orders with WIP data for Flow Optimizer.
    
    Returns order-centric data (one row per order line) with:
    - Order info: order_num, order_line, customer_name, due_date, urgency
    - Item info: item, model, bed_type, bed_length
    - Quantities: qty_ordered, qty_shipped, qty_remaining
    - WIP by stage: item_at_weld, item_at_blast, item_at_paint, item_at_assy
    - Inventory: item_on_hand, item_total_pipeline
    - Jobs: job_numbers, qty_released
    
    This matches the OPEN ORDERS V5 schema for Flow Optimizer import.
    """
    try:
        scheduler = get_scheduler()
        result = await scheduler.get_open_orders(limit=limit)
        
        # Calculate summary totals (only count each item once via first_for_item flag)
        total_at_weld = sum(ol.item_at_weld for ol in result.order_lines if ol.first_for_item)
        total_at_blast = sum(ol.item_at_blast for ol in result.order_lines if ol.first_for_item)
        total_at_paint = sum(ol.item_at_paint for ol in result.order_lines if ol.first_for_item)
        total_at_assy = sum(ol.item_at_assy for ol in result.order_lines if ol.first_for_item)
        total_on_hand = sum(ol.item_on_hand for ol in result.order_lines if ol.first_for_item)
        
        # In Production = total WIP at all work centers (actively being worked on)
        total_in_production = total_at_weld + total_at_blast + total_at_paint + total_at_assy
        
        # Ready to Schedule = orders that don't have jobs yet (need to be released)
        orders_without_jobs = sum(1 for ol in result.order_lines if not ol.job_numbers)
        
        return {
            "success": True,
            "data": {
                "summary": {
                    "total_orders": result.total_orders,
                    "total_lines": result.total_lines,
                    "in_production": total_in_production,
                    "ready_to_schedule": orders_without_jobs,
                    "on_hand": total_on_hand,  # Finished goods inventory
                    "weld": total_at_weld,
                    "blast": total_at_blast,
                    "paint": total_at_paint,
                    "assembly": total_at_assy,
                },
                "work_centers": result.work_centers,
                "order_lines": [
                    {
                        "order_num": ol.order_num,
                        "order_line": ol.order_line,
                        "customer_name": ol.customer_name,
                        "order_date": ol.order_date,
                        "due_date": ol.due_date,
                        "days_until_due": ol.days_until_due,
                        "urgency": ol.urgency,
                        "item": ol.item,
                        "model": ol.model,
                        "item_description": ol.item_description,
                        "bed_type": ol.bed_type,
                        "bed_length": ol.bed_length,
                        "qty_ordered": ol.qty_ordered,
                        "qty_shipped": ol.qty_shipped,
                        "qty_remaining": ol.qty_remaining,
                        "item_on_hand": ol.item_on_hand,
                        "item_at_weld": ol.item_at_weld,
                        "item_at_blast": ol.item_at_blast,
                        "item_at_paint": ol.item_at_paint,
                        "item_at_assy": ol.item_at_assy,
                        "item_total_pipeline": ol.item_total_pipeline,
                        "job_numbers": ol.job_numbers,
                        "qty_released": ol.qty_released,
                        "released_date": ol.released_date,
                        "line_value": ol.line_value,
                        "first_for_item": ol.first_for_item,
                    }
                    for ol in result.order_lines
                ],
                "fetched_at": result.fetched_at.isoformat(),
            }
        }
    except Exception as e:
        logger.error("Failed to get open orders", error=str(e))
        raise HTTPException(status_code=500, detail=str(e))
