"""
API Request/Response Schemas
============================

Pydantic models for API input validation and response serialization.

These models provide:
- Automatic input validation
- OpenAPI documentation
- Type safety
- Consistent error messages
"""

from datetime import date, datetime
from enum import Enum
from typing import Optional, Any

from pydantic import BaseModel, Field, field_validator


# =============================================================================
# Common Models
# =============================================================================

class DataSourceType(str, Enum):
    """Data source types."""
    REST = "rest"
    DATALAKE = "datalake"


class QuerySummary(BaseModel):
    """Summary information about a query result."""
    
    total: int = Field(..., description="Total number of records returned")
    data_source: DataSourceType = Field(..., description="Data source used")
    query_ms: int = Field(..., description="Query execution time in milliseconds")
    truncated: bool = Field(False, description="Whether results were truncated")


class ErrorResponse(BaseModel):
    """Standard error response."""
    
    error: str = Field(..., description="Error code")
    message: str = Field(..., description="Human-readable error message")
    detail: Optional[str] = Field(None, description="Additional error details")
    
    model_config = {
        "json_schema_extra": {
            "example": {
                "error": "validation_error",
                "message": "Invalid input parameters",
                "detail": "work_center must be alphanumeric"
            }
        }
    }


# =============================================================================
# Production Schedule Models
# =============================================================================

class ScheduleFilters(BaseModel):
    """Filters for production schedule query."""
    
    work_center: Optional[str] = Field(
        None,
        max_length=50,
        pattern=r"^[\w\-]+$",
        description="Filter by work center code (e.g., 'WELD-01')",
        examples=["WELD-01", "PAINT-02"]
    )
    job: Optional[str] = Field(
        None,
        max_length=50,
        pattern=r"^[\w\-]+$",
        description="Filter by job number",
        examples=["J-12345", "MO-001"]
    )
    include_completed: bool = Field(
        False,
        description="Include 100% complete operations"
    )
    
    @field_validator("work_center", "job", mode="before")
    @classmethod
    def strip_whitespace(cls, v: Optional[str]) -> Optional[str]:
        if v:
            return v.strip()
        return v


class ScheduledOperationResponse(BaseModel):
    """A scheduled manufacturing operation."""
    
    job: str = Field(..., description="Job number")
    suffix: int = Field(..., description="Job suffix")
    item: str = Field(..., description="Item being manufactured")
    item_description: str = Field(..., description="Item description")
    operation_num: int = Field(..., description="Operation sequence number")
    work_center: str = Field(..., description="Work center code")
    work_center_description: str = Field(..., description="Work center name")
    qty_released: float = Field(..., description="Quantity released")
    qty_complete: float = Field(..., description="Quantity completed")
    pct_complete: float = Field(..., description="Percent complete (0-100)")
    sched_start: Optional[datetime] = Field(None, description="Scheduled start time")
    sched_finish: Optional[datetime] = Field(None, description="Scheduled finish time")
    status: str = Field(..., description="Status: on_track, behind, complete")


class ScheduleResponse(BaseModel):
    """Production schedule response."""
    
    operations: list[ScheduledOperationResponse] = Field(..., description="List of operations")
    summary: QuerySummary


# =============================================================================
# Sales Order Models
# =============================================================================

class OrderFilters(BaseModel):
    """Filters for sales order query."""
    
    customer: Optional[str] = Field(
        None,
        max_length=100,
        description="Filter by customer name or number (partial match)",
        examples=["ACME", "C-1001"]
    )
    days_out: Optional[int] = Field(
        None,
        ge=1,
        le=365,
        description="Only orders due within N days"
    )
    
    @field_validator("customer", mode="before")
    @classmethod
    def strip_whitespace(cls, v: Optional[str]) -> Optional[str]:
        if v:
            return v.strip()
        return v


class OrderLineResponse(BaseModel):
    """A sales order line item."""
    
    line: int
    item: str
    item_description: str
    qty_ordered: float
    qty_shipped: float
    qty_remaining: float
    unit_price: float
    extended_price: float
    due_date: Optional[date]
    warehouse: str


class SalesOrderResponse(BaseModel):
    """A sales order."""
    
    order_num: str
    customer_num: str
    customer_name: str
    order_date: Optional[date]
    due_date: Optional[date]
    status: str
    ship_to_name: str
    ship_to_city: str
    ship_to_state: str
    lines: list[OrderLineResponse]


class OrdersResponse(BaseModel):
    """Sales orders response."""
    
    orders: list[dict[str, Any]] = Field(..., description="List of orders")
    summary: QuerySummary


# =============================================================================
# Customer Search Models
# =============================================================================

class CustomerFilters(BaseModel):
    """Filters for customer search."""
    
    query: str = Field(
        ...,
        min_length=1,
        max_length=100,
        description="Search term: name, number, city, or state"
    )
    active_only: bool = Field(
        True,
        description="Only return active customers"
    )
    
    @field_validator("query", mode="before")
    @classmethod
    def strip_and_validate_query(cls, v: str) -> str:
        v = v.strip()
        if len(v) < 1:
            raise ValueError("Search query cannot be empty")
        return v


class CustomerAddressResponse(BaseModel):
    """A customer address."""
    
    address_id: str
    name: str
    address_1: str
    address_2: str
    city: str
    state: str
    zip_code: str
    country: str


class CustomerResponse(BaseModel):
    """A customer record."""
    
    customer_num: str
    name: str
    contact_name: str
    phone: str
    email: str
    address_1: str
    address_2: str
    city: str
    state: str
    zip_code: str
    country: str
    active: bool
    credit_hold: bool
    payment_terms: str
    credit_limit: Optional[float]
    addresses: list[CustomerAddressResponse]


class CustomersResponse(BaseModel):
    """Customer search response."""
    
    customers: list[dict[str, Any]] = Field(..., description="List of customers")
    summary: QuerySummary


# =============================================================================
# Inventory Models
# =============================================================================

class InventoryFilters(BaseModel):
    """Filters for inventory query."""
    
    item: Optional[str] = Field(
        None,
        max_length=50,
        pattern=r"^[\w\-]+$",
        description="Filter by item number",
        examples=["BED-KING", "FRAME-001"]
    )
    warehouse: Optional[str] = Field(
        None,
        max_length=20,
        pattern=r"^[\w\-]+$",
        description="Filter by warehouse",
        examples=["MAIN", "WH-01"]
    )
    low_stock_only: bool = Field(
        False,
        description="Only show items at or below reorder point"
    )
    
    @field_validator("item", "warehouse", mode="before")
    @classmethod
    def strip_whitespace(cls, v: Optional[str]) -> Optional[str]:
        if v:
            return v.strip()
        return v


class WarehouseStockResponse(BaseModel):
    """Stock level for a specific warehouse."""
    
    warehouse: str
    qty_on_hand: float
    qty_allocated: float
    qty_available: float


class InventoryItemResponse(BaseModel):
    """An inventory item."""
    
    item: str
    description: str
    product_code: str
    um: str
    total_on_hand: float
    total_allocated: float
    total_available: float
    reorder_point: Optional[float]
    reorder_qty: Optional[float]
    is_low_stock: bool
    warehouse_stock: list[WarehouseStockResponse]
    unit_cost: Optional[float]


class InventoryResponse(BaseModel):
    """Inventory status response."""
    
    items: list[dict[str, Any]] = Field(..., description="List of inventory items")
    summary: QuerySummary


