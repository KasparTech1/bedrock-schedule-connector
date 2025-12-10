"""
Sales Order Models
==================

Models for the Sales Order Tracker connector.
"""

from datetime import date, datetime
from enum import Enum
from typing import Optional

from pydantic import BaseModel, Field


class OrderStatus(str, Enum):
    """Status of a sales order."""
    OPEN = "open"
    SHIPPED = "shipped"
    INVOICED = "invoiced"
    CLOSED = "closed"
    HOLD = "hold"


class OrderLine(BaseModel):
    """
    A line item on a sales order.
    
    Represents a single item being ordered with quantity and pricing.
    """
    
    line: int = Field(description="Line number")
    item: str = Field(description="Item number")
    item_description: str = Field(default="", description="Item description")
    qty_ordered: float = Field(description="Quantity ordered")
    qty_shipped: float = Field(default=0, description="Quantity shipped")
    qty_remaining: float = Field(default=0, description="Quantity remaining to ship")
    unit_price: float = Field(default=0, ge=0, description="Unit price")
    extended_price: float = Field(default=0, ge=0, description="Extended price (qty × unit)")
    due_date: Optional[date] = Field(default=None, description="Line due date")
    warehouse: str = Field(default="", description="Shipping warehouse")


class SalesOrder(BaseModel):
    """
    A sales order header with line items.
    
    Represents a customer order with all line items and summary.
    
    Example:
        {
            "order_num": "CO-12345",
            "customer_num": "C-100",
            "customer_name": "Acme Corp",
            "order_date": "2024-12-01",
            "due_date": "2024-12-15",
            "status": "open",
            "total_amount": 5000.00,
            "lines": [...]
        }
    """
    
    # Order identification
    order_num: str = Field(description="Sales order number")
    
    # Customer
    customer_num: str = Field(description="Customer number")
    customer_name: str = Field(default="", description="Customer name")
    
    # Dates
    order_date: Optional[date] = Field(default=None, description="Order date")
    due_date: Optional[date] = Field(default=None, description="Order due date")
    ship_date: Optional[date] = Field(default=None, description="Actual ship date")
    
    # Status
    status: OrderStatus = Field(default=OrderStatus.OPEN, description="Order status")
    
    # Amounts
    total_amount: float = Field(default=0, ge=0, description="Order total")
    
    # Line items
    lines: list[OrderLine] = Field(default_factory=list, description="Order lines")
    
    # Shipping
    ship_to_name: str = Field(default="", description="Ship to name")
    ship_to_city: str = Field(default="", description="Ship to city")
    ship_to_state: str = Field(default="", description="Ship to state")
    
    @property
    def is_late(self) -> bool:
        """Check if order is past due date."""
        if self.due_date and self.status == OrderStatus.OPEN:
            return date.today() > self.due_date
        return False
    
    @property
    def days_until_due(self) -> Optional[int]:
        """Days until due date (negative if past due)."""
        if self.due_date:
            return (self.due_date - date.today()).days
        return None
    
    model_config = {
        "json_schema_extra": {
            "example": {
                "order_num": "CO-12345",
                "customer_num": "C-100",
                "customer_name": "Acme Corporation",
                "order_date": "2024-12-01",
                "due_date": "2024-12-15",
                "status": "open",
                "total_amount": 5000.00,
                "lines": [
                    {
                        "line": 1,
                        "item": "BED-KING-BLK",
                        "item_description": "King Bed Frame - Black",
                        "qty_ordered": 10.0,
                        "qty_shipped": 0.0,
                        "unit_price": 500.00
                    }
                ]
            }
        }
    }
