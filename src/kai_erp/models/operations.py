"""
Production Operations Models
============================

Models for the Bedrock Ops Scheduler connector.
"""

from datetime import datetime
from enum import Enum
from typing import Optional

from pydantic import BaseModel, Field


class OperationStatus(str, Enum):
    """Status of a production operation."""
    ON_TRACK = "on_track"
    BEHIND = "behind"
    COMPLETE = "complete"
    UNKNOWN = "unknown"


class ScheduledOperation(BaseModel):
    """
    A scheduled production operation.
    
    Represents a single operation within a manufacturing job,
    tracking progress and schedule information.
    
    Example:
        {
            "job": "J-1234",
            "item": "BED-KING-BLK",
            "item_description": "King Bed Frame - Black",
            "work_center": "WELD-01",
            "pct_complete": 45.0,
            "status": "on_track"
        }
    """
    
    # Job identification
    job: str = Field(description="Job number (e.g., 'J-12345')")
    suffix: int = Field(default=0, description="Job suffix for split jobs")
    
    # Item information
    item: str = Field(description="Item number being manufactured")
    item_description: str = Field(default="", description="Item description")
    
    # Operation details
    operation_num: int = Field(description="Operation sequence number")
    work_center: str = Field(description="Work center code (e.g., 'WELD-01')")
    work_center_description: str = Field(default="", description="Work center name")
    
    # Quantities
    qty_released: float = Field(description="Quantity released to manufacture")
    qty_complete: float = Field(default=0, description="Quantity completed")
    pct_complete: float = Field(default=0, ge=0, le=100, description="Percent complete (0-100)")
    
    # Schedule
    sched_start: Optional[datetime] = Field(default=None, description="Scheduled start datetime")
    sched_finish: Optional[datetime] = Field(default=None, description="Scheduled finish datetime")
    
    # Status
    status: OperationStatus = Field(
        default=OperationStatus.UNKNOWN,
        description="Operation status (on_track, behind, complete)"
    )
    
    # Related data
    qty_on_hand: Optional[float] = Field(
        default=None,
        description="Quantity on hand of finished item"
    )
    
    model_config = {
        "json_schema_extra": {
            "example": {
                "job": "J-1234",
                "suffix": 0,
                "item": "BED-KING-BLK",
                "item_description": "King Bed Frame - Black",
                "operation_num": 20,
                "work_center": "WELD-01",
                "work_center_description": "Welding Station 1",
                "qty_released": 50.0,
                "qty_complete": 23.0,
                "pct_complete": 46.0,
                "sched_start": "2024-12-09T06:00:00",
                "sched_finish": "2024-12-09T14:00:00",
                "status": "on_track",
                "qty_on_hand": 12.0
            }
        }
    }
