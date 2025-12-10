"""
Inventory Models
================

Models for the Inventory Status connector.
"""

from typing import Optional

from pydantic import BaseModel, Field


class WarehouseStock(BaseModel):
    """
    Stock level at a specific warehouse location.
    """
    
    warehouse: str = Field(description="Warehouse code")
    location: str = Field(default="", description="Location within warehouse")
    qty_on_hand: float = Field(default=0, description="Quantity on hand")
    qty_allocated: float = Field(default=0, description="Quantity allocated to orders")
    qty_available: float = Field(default=0, description="Quantity available (on hand - allocated)")


class InventoryItem(BaseModel):
    """
    An inventory item with stock levels.
    
    Represents an item across all warehouse locations.
    
    Example:
        {
            "item": "BED-KING-BLK",
            "description": "King Bed Frame - Black",
            "total_on_hand": 100.0,
            "total_available": 75.0,
            "is_low_stock": false
        }
    """
    
    # Item identification
    item: str = Field(description="Item number")
    description: str = Field(default="", description="Item description")
    
    # Classification
    product_code: str = Field(default="", description="Product code/category")
    um: str = Field(default="EA", description="Unit of measure")
    
    # Totals across all locations
    total_on_hand: float = Field(default=0, description="Total quantity on hand")
    total_allocated: float = Field(default=0, description="Total quantity allocated")
    total_available: float = Field(default=0, description="Total available (on hand - allocated)")
    
    # Reorder
    reorder_point: Optional[float] = Field(default=None, description="Reorder point")
    reorder_qty: Optional[float] = Field(default=None, description="Reorder quantity")
    is_low_stock: bool = Field(default=False, description="Is below reorder point")
    
    # Stock by location
    warehouse_stock: list[WarehouseStock] = Field(
        default_factory=list,
        description="Stock levels by warehouse"
    )
    
    # Costing
    unit_cost: Optional[float] = Field(default=None, description="Standard unit cost")
    total_value: Optional[float] = Field(default=None, description="Total inventory value")
    
    @property
    def needs_reorder(self) -> bool:
        """Check if item needs to be reordered."""
        if self.reorder_point is not None:
            return self.total_available <= self.reorder_point
        return False
    
    model_config = {
        "json_schema_extra": {
            "example": {
                "item": "BED-KING-BLK",
                "description": "King Bed Frame - Black",
                "product_code": "BEDS",
                "um": "EA",
                "total_on_hand": 100.0,
                "total_allocated": 25.0,
                "total_available": 75.0,
                "reorder_point": 20.0,
                "is_low_stock": False,
                "warehouse_stock": [
                    {
                        "warehouse": "MAIN",
                        "qty_on_hand": 80.0,
                        "qty_allocated": 20.0,
                        "qty_available": 60.0
                    },
                    {
                        "warehouse": "WEST",
                        "qty_on_hand": 20.0,
                        "qty_allocated": 5.0,
                        "qty_available": 15.0
                    }
                ]
            }
        }
    }
