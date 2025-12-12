"""Order-related data models."""
from dataclasses import dataclass
from datetime import datetime
from typing import Optional


@dataclass
class OpenOrderLine:
    """
    A single open order line for Flow Optimizer export.
    
    Schema matches the TBE_App OPEN ORDERS V5 query output.
    One row per ORDER LINE with item-level WIP data.
    """
    # Order identification
    order_num: str
    order_line: int
    customer_name: str
    order_date: Optional[str]
    due_date: Optional[str]
    days_until_due: int
    urgency: str  # OVERDUE, TODAY, THIS_WEEK, NEXT_WEEK, LATER
    
    # Item details
    item: str
    model: Optional[str]  # Drawing number
    item_description: str
    bed_type: str  # Granite, Diamond, Marble, etc.
    bed_length: int  # For position 7 eligibility
    
    # Order quantities
    qty_ordered: float
    qty_shipped: float
    qty_remaining: float
    
    # Item-level WIP data (same for all orders of this item)
    item_on_hand: float
    item_at_paint: float
    item_at_blast: float
    item_at_weld: float
    item_at_assy: float
    item_total_pipeline: float
    
    # Job information
    job_numbers: str
    qty_released: float
    released_date: Optional[str]
    
    # Line value for prioritization
    line_value: float
    
    # Flags
    first_for_item: bool


@dataclass
class FlowOptimizerResult:
    """Result of flow optimizer data fetch."""
    total_orders: int
    total_lines: int
    order_lines: list[OpenOrderLine]
    work_centers: list[str]
    fetched_at: datetime


@dataclass
class OrderAvailabilityLine:
    """
    A customer order line with availability and allocation information.
    
    Emulates the TBE_Customer_Order_Availability_Add_Release_Date stored procedure output.
    Shows how inventory is allocated from different production stages.
    """
    # Order identification
    co_data_id: int
    co_num: str
    co_line: int
    co_release: int
    
    # Customer information
    customer_name: str
    
    # Dates
    order_date: Optional[str]
    due_date: Optional[str]
    released_date: Optional[str]
    
    # Estimated completion dates
    weld_fab_completion_date: Optional[str]
    blast_completion_date: Optional[str]
    paint_assembly_completion_date: Optional[str]
    
    # Item information
    item: str
    model: Optional[str]
    item_description: str
    
    # Quantities
    qty_ordered: float
    qty_shipped: float
    qty_remaining: float
    qty_remaining_covered: float
    
    # Inventory quantities
    qty_on_hand: float
    current_on_hand: float
    qty_nf: float
    qty_alloc_co: float
    qty_wip: float
    qty_released: float
    
    # Production stage totals and allocations
    total_in_paint: float
    allocated_from_paint: float
    total_in_blast: float
    allocated_from_blast: float
    total_in_released_weld_fab: float
    allocated_from_released_weld_fab: float
    
    # Related jobs
    jobs: str
    
    # Financial
    line_amount: float


@dataclass
class OrderAvailabilityResult:
    """Result of order availability fetch."""
    total_orders: int
    total_lines: int
    order_lines: list[OrderAvailabilityLine]
    fetched_at: datetime
