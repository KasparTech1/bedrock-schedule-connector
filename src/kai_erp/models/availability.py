"""
Order Availability Models
=========================

Models for the Order Availability connector.
Based on the Syteline 8 TBE_Customer_Order_Availability_Add_Release_Date stored procedure.

This model tracks customer order availability with allocation from different
production stages (On Hand, Paint, Blast, Weld/Fab) and calculates estimated
completion dates based on business days.
"""

from datetime import date
from typing import Optional

from pydantic import BaseModel, Field


class OrderAvailabilityLine(BaseModel):
    """
    A customer order line with availability and allocation information.
    
    Represents the availability of a single order line, showing how the
    required quantity is allocated from different production stages.
    
    Allocation Priority Order:
    1. On Hand inventory (immediate availability)
    2. Paint queue (nearly complete production)
    3. Blast queue (in process)
    4. Released Weld/Fab (early production)
    """
    
    # Order identification
    co_data_id: int = Field(description="Internal row ID")
    co_num: str = Field(description="Customer order number")
    co_line: int = Field(description="Line number")
    co_release: int = Field(default=0, description="Release number")
    
    # Customer information
    customer_name: str = Field(default="", description="Customer name")
    
    # Dates
    order_date: Optional[date] = Field(default=None, description="Order date")
    due_date: Optional[date] = Field(default=None, description="Due date for line")
    released_date: Optional[date] = Field(default=None, description="Job release date")
    
    # Estimated completion dates based on business days
    weld_fab_completion_date: Optional[date] = Field(
        default=None,
        description="Estimated Weld/Fab completion (4 business days from release)"
    )
    blast_completion_date: Optional[date] = Field(
        default=None,
        description="Estimated Blast completion (7 business days from release)"
    )
    paint_assembly_completion_date: Optional[date] = Field(
        default=None,
        description="Estimated Paint/Assembly completion (10 business days from release)"
    )
    
    # Item information
    item: str = Field(description="Item number")
    model: str = Field(default="", description="Drawing/Model number")
    item_description: str = Field(default="", description="Item description")
    
    # Quantities
    qty_ordered: float = Field(default=0, description="Quantity ordered")
    qty_shipped: float = Field(default=0, description="Quantity already shipped")
    qty_remaining: float = Field(default=0, description="Quantity remaining to ship")
    qty_remaining_covered: float = Field(
        default=0,
        description="Quantity covered by available inventory/WIP"
    )
    
    # Inventory quantities
    qty_on_hand: float = Field(default=0, description="Allocated from on-hand inventory")
    current_on_hand: float = Field(
        default=0,
        description="Current on-hand at time of allocation"
    )
    qty_nf: float = Field(default=0, description="Not Finished quantity")
    qty_alloc_co: float = Field(default=0, description="Quantity allocated to this CO")
    qty_wip: float = Field(default=0, description="Quantity in WIP")
    qty_released: float = Field(default=0, description="Released job quantity")
    
    # Production stage totals and allocations
    total_in_paint: float = Field(default=0, description="Total quantity in paint")
    allocated_from_paint: float = Field(
        default=0,
        description="Allocated from paint queue"
    )
    
    total_in_blast: float = Field(default=0, description="Total quantity in blast")
    allocated_from_blast: float = Field(
        default=0,
        description="Allocated from blast queue"
    )
    
    total_in_released_weld_fab: float = Field(
        default=0,
        description="Total quantity in released weld/fab"
    )
    allocated_from_released_weld_fab: float = Field(
        default=0,
        description="Allocated from released weld/fab"
    )
    
    # Related jobs
    jobs: str = Field(default="", description="Related job numbers (semicolon-separated)")
    
    # Financial
    line_amount: float = Field(default=0, ge=0, description="Line amount")
    
    @property
    def is_fully_covered(self) -> bool:
        """Check if order line is fully covered by available inventory/WIP."""
        return self.qty_remaining_covered >= self.qty_remaining
    
    @property
    def shortage(self) -> float:
        """Calculate the shortage quantity not covered by inventory/WIP."""
        return max(0, self.qty_remaining - self.qty_remaining_covered)
    
    @property
    def coverage_percentage(self) -> float:
        """Calculate the percentage of remaining quantity that is covered."""
        if self.qty_remaining <= 0:
            return 100.0
        return min(100.0, (self.qty_remaining_covered / self.qty_remaining) * 100)
    
    @property
    def estimated_ship_date(self) -> Optional[date]:
        """
        Get the estimated ship date based on allocation source.
        
        Returns the latest completion date based on where inventory is allocated from.
        """
        if self.allocated_from_released_weld_fab > 0:
            return self.paint_assembly_completion_date
        elif self.allocated_from_blast > 0:
            return self.blast_completion_date
        elif self.allocated_from_paint > 0:
            return self.blast_completion_date  # Paint stage completion
        elif self.qty_on_hand > 0:
            return None  # Available now
        return None
    
    model_config = {
        "json_schema_extra": {
            "example": {
                "co_data_id": 1,
                "co_num": "CO-12345",
                "co_line": 1,
                "co_release": 0,
                "customer_name": "Acme Corporation",
                "order_date": "2024-12-01",
                "due_date": "2024-12-20",
                "released_date": "2024-12-05",
                "weld_fab_completion_date": "2024-12-11",
                "blast_completion_date": "2024-12-16",
                "paint_assembly_completion_date": "2024-12-19",
                "item": "BED-KING-BLK",
                "model": "DWG-1234",
                "item_description": "King Bed Frame - Black",
                "qty_ordered": 10.0,
                "qty_shipped": 2.0,
                "qty_remaining": 8.0,
                "qty_remaining_covered": 8.0,
                "qty_on_hand": 5.0,
                "current_on_hand": 10.0,
                "qty_nf": 0.0,
                "qty_alloc_co": 8.0,
                "qty_wip": 10.0,
                "qty_released": 10.0,
                "total_in_paint": 3.0,
                "allocated_from_paint": 3.0,
                "total_in_blast": 2.0,
                "allocated_from_blast": 0.0,
                "total_in_released_weld_fab": 5.0,
                "allocated_from_released_weld_fab": 0.0,
                "jobs": "J-001; J-002",
                "line_amount": 5000.00
            }
        }
    }


class OrderAvailabilitySummary(BaseModel):
    """
    Summary statistics for order availability analysis.
    """
    
    total_lines: int = Field(default=0, description="Total order lines")
    total_qty_remaining: float = Field(default=0, description="Total quantity remaining")
    total_qty_covered: float = Field(default=0, description="Total quantity covered")
    total_shortage: float = Field(default=0, description="Total shortage")
    total_line_amount: float = Field(default=0, description="Total line amount")
    
    lines_fully_covered: int = Field(
        default=0,
        description="Number of lines fully covered by inventory/WIP"
    )
    lines_partially_covered: int = Field(
        default=0,
        description="Number of lines partially covered"
    )
    lines_not_covered: int = Field(
        default=0,
        description="Number of lines with no coverage"
    )
    
    @property
    def overall_coverage_percentage(self) -> float:
        """Calculate overall coverage percentage."""
        if self.total_qty_remaining <= 0:
            return 100.0
        return min(100.0, (self.total_qty_covered / self.total_qty_remaining) * 100)

