"""
MCP Tool Handlers
=================

Handler functions that bridge MCP tool calls to connectors.
"""

from typing import Any

import structlog

from kai_erp.core import RestEngine, VolumeExceedsLimit
from kai_erp.connectors import (
    BedrockOpsScheduler,
    CustomerSearch,
    InventoryStatus,
    OrderAvailabilityConnector,
    SalesOrderTracker,
)

logger = structlog.get_logger(__name__)


async def handle_production_schedule(
    engine: RestEngine,
    work_center: str | None = None,
    job: str | None = None,
    include_completed: bool = False
) -> dict[str, Any]:
    """
    Handle get_production_schedule tool call.
    
    Args:
        engine: REST engine instance
        work_center: Optional work center filter
        job: Optional job filter
        include_completed: Include completed operations
    
    Returns:
        Tool result dict
    """
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
            "success": True,
            "data": {
                "operations": result.data,
                "summary": {
                    "total": result.record_count,
                    "data_source": result.source.value,
                    "query_ms": result.latency_ms
                }
            }
        }
    
    except VolumeExceedsLimit as e:
        return {
            "success": False,
            "error": {
                "message": str(e),
                "suggestion": "Add a work_center or job filter to reduce results."
            }
        }
    except Exception as e:
        logger.error("Production schedule handler failed", error=str(e))
        return {
            "success": False,
            "error": {"message": str(e)}
        }


async def handle_open_orders(
    engine: RestEngine,
    customer: str | None = None,
    days_out: int | None = None
) -> dict[str, Any]:
    """
    Handle get_open_orders tool call.
    
    Args:
        engine: REST engine instance
        customer: Optional customer filter
        days_out: Optional days until due filter
    
    Returns:
        Tool result dict
    """
    connector = SalesOrderTracker(engine)
    
    filters = {}
    if customer:
        filters["customer"] = customer
    if days_out:
        filters["days_out"] = days_out
    
    try:
        result = await connector.execute(filters=filters if filters else None)
        
        return {
            "success": True,
            "data": {
                "orders": result.data,
                "summary": {
                    "total": result.record_count,
                    "data_source": result.source.value,
                    "query_ms": result.latency_ms
                }
            }
        }
    
    except Exception as e:
        logger.error("Open orders handler failed", error=str(e))
        return {
            "success": False,
            "error": {"message": str(e)}
        }


async def handle_customer_search(
    engine: RestEngine,
    query: str,
    active_only: bool = True
) -> dict[str, Any]:
    """
    Handle search_customers tool call.
    
    Args:
        engine: REST engine instance
        query: Search term
        active_only: Only active customers
    
    Returns:
        Tool result dict
    """
    connector = CustomerSearch(engine)
    
    filters = {
        "query": query,
        "active_only": active_only
    }
    
    try:
        result = await connector.execute(filters=filters)
        
        return {
            "success": True,
            "data": {
                "customers": result.data,
                "summary": {
                    "total": result.record_count,
                    "data_source": result.source.value,
                    "query_ms": result.latency_ms
                }
            }
        }
    
    except Exception as e:
        logger.error("Customer search handler failed", error=str(e))
        return {
            "success": False,
            "error": {"message": str(e)}
        }


async def handle_inventory_status(
    engine: RestEngine,
    item: str | None = None,
    warehouse: str | None = None,
    low_stock_only: bool = False
) -> dict[str, Any]:
    """
    Handle get_inventory_status tool call.
    
    Args:
        engine: REST engine instance
        item: Optional item filter
        warehouse: Optional warehouse filter
        low_stock_only: Only low stock items
    
    Returns:
        Tool result dict
    """
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
            "success": True,
            "data": {
                "inventory": result.data,
                "summary": {
                    "total": result.record_count,
                    "data_source": result.source.value,
                    "query_ms": result.latency_ms
                }
            }
        }
    
    except VolumeExceedsLimit as e:
        return {
            "success": False,
            "error": {
                "message": str(e),
                "suggestion": "Add an item or warehouse filter to reduce results."
            }
        }
    except Exception as e:
        logger.error("Inventory status handler failed", error=str(e))
        return {
            "success": False,
            "error": {"message": str(e)}
        }


async def handle_order_availability(
    engine: RestEngine,
    customer: str | None = None,
    item: str | None = None,
    due_within_days: int | None = None,
    shortage_only: bool = False
) -> dict[str, Any]:
    """
    Handle get_order_availability tool call.
    
    Args:
        engine: REST engine instance
        customer: Optional customer name filter
        item: Optional item filter
        due_within_days: Optional filter for orders due within N days
        shortage_only: Only return orders with shortages
    
    Returns:
        Tool result dict with order availability data
    """
    connector = OrderAvailabilityConnector(engine)
    
    filters = {}
    if customer:
        filters["customer"] = customer
    if item:
        filters["item"] = item
    if due_within_days:
        filters["due_within_days"] = due_within_days
    
    try:
        result = await connector.execute(filters=filters if filters else None)
        
        # Post-filter for shortage_only if requested
        orders = result.data
        if shortage_only:
            orders = [
                o for o in orders 
                if o.get("qty_remaining", 0) > o.get("qty_remaining_covered", 0)
            ]
        
        # Calculate summary statistics
        total_remaining = sum(o.get("qty_remaining", 0) for o in orders)
        total_covered = sum(o.get("qty_remaining_covered", 0) for o in orders)
        total_shortage = max(0, total_remaining - total_covered)
        total_amount = sum(o.get("line_amount", 0) for o in orders)
        
        lines_fully_covered = sum(
            1 for o in orders 
            if o.get("qty_remaining_covered", 0) >= o.get("qty_remaining", 0)
        )
        lines_with_shortage = len(orders) - lines_fully_covered
        
        return {
            "success": True,
            "data": {
                "order_lines": orders,
                "summary": {
                    "total_lines": len(orders),
                    "total_qty_remaining": total_remaining,
                    "total_qty_covered": total_covered,
                    "total_shortage": total_shortage,
                    "total_line_amount": total_amount,
                    "lines_fully_covered": lines_fully_covered,
                    "lines_with_shortage": lines_with_shortage,
                    "coverage_percentage": round(
                        (total_covered / total_remaining * 100) if total_remaining > 0 else 100,
                        1
                    ),
                    "data_source": result.source.value,
                    "query_ms": result.latency_ms
                }
            }
        }
    
    except VolumeExceedsLimit as e:
        return {
            "success": False,
            "error": {
                "message": str(e),
                "suggestion": "Add a customer or item filter to reduce results."
            }
        }
    except Exception as e:
        logger.error("Order availability handler failed", error=str(e))
        return {
            "success": False,
            "error": {"message": str(e)}
        }


# Handler dispatch map
HANDLERS = {
    "get_production_schedule": handle_production_schedule,
    "get_open_orders": handle_open_orders,
    "search_customers": handle_customer_search,
    "get_inventory_status": handle_inventory_status,
    "get_order_availability": handle_order_availability,
}


async def dispatch_tool_call(
    engine: RestEngine,
    tool_name: str,
    arguments: dict[str, Any]
) -> dict[str, Any]:
    """
    Dispatch a tool call to the appropriate handler.
    
    Args:
        engine: REST engine instance
        tool_name: Name of the tool to call
        arguments: Tool arguments
    
    Returns:
        Tool result dict
    """
    handler = HANDLERS.get(tool_name)
    
    if not handler:
        return {
            "success": False,
            "error": {"message": f"Unknown tool: {tool_name}"}
        }
    
    return await handler(engine, **arguments)
