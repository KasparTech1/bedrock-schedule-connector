"""
Tests for Operations Models
===========================

Validates the ScheduledOperation model interface.
"""

from datetime import datetime

import pytest

from kai_erp.models.operations import OperationStatus, ScheduledOperation


class TestScheduledOperation:
    """Tests for ScheduledOperation model."""
    
    def test_create_basic_operation(self):
        """Test creating a basic operation with required fields."""
        op = ScheduledOperation(
            job="J-1234",
            item="BED-KING-BLK",
            operation_num=20,
            work_center="WELD-01",
            qty_released=50.0
        )
        
        assert op.job == "J-1234"
        assert op.item == "BED-KING-BLK"
        assert op.operation_num == 20
        assert op.work_center == "WELD-01"
        assert op.qty_released == 50.0
        # Defaults
        assert op.suffix == 0
        assert op.qty_complete == 0
        assert op.pct_complete == 0
        assert op.status == OperationStatus.UNKNOWN
    
    def test_create_complete_operation(self, sample_schedule_result):
        """Test creating operation from sample data."""
        row = sample_schedule_result[0]
        
        op = ScheduledOperation(
            job=row["Job"],
            suffix=row["Suffix"],
            item=row["Item"],
            item_description=row["ItemDescription"],
            operation_num=row["OperNum"],
            work_center=row["Wc"],
            work_center_description=row["WcDescription"],
            qty_released=row["QtyReleased"],
            qty_complete=row["OperQtyComplete"],
            pct_complete=row["PctComplete"],
            sched_start=row["SchedStart"],
            sched_finish=row["SchedFinish"],
            status=OperationStatus.ON_TRACK,
            qty_on_hand=row["QtyOnHand"]
        )
        
        assert op.job == "J-1234"
        assert op.item_description == "King Bed Frame - Black"
        assert op.pct_complete == 46.0
        assert op.status == OperationStatus.ON_TRACK
    
    def test_pct_complete_validation(self):
        """Test percent complete is validated between 0-100."""
        # Valid values
        op = ScheduledOperation(
            job="J-1", item="X", operation_num=1, work_center="W", 
            qty_released=10, pct_complete=50.0
        )
        assert op.pct_complete == 50.0
        
        # Edge cases
        op = ScheduledOperation(
            job="J-1", item="X", operation_num=1, work_center="W",
            qty_released=10, pct_complete=0.0
        )
        assert op.pct_complete == 0.0
        
        op = ScheduledOperation(
            job="J-1", item="X", operation_num=1, work_center="W",
            qty_released=10, pct_complete=100.0
        )
        assert op.pct_complete == 100.0
    
    def test_status_enum_values(self):
        """Test all status enum values."""
        assert OperationStatus.ON_TRACK.value == "on_track"
        assert OperationStatus.BEHIND.value == "behind"
        assert OperationStatus.COMPLETE.value == "complete"
        assert OperationStatus.UNKNOWN.value == "unknown"
    
    def test_model_dump(self):
        """Test serialization to dict."""
        op = ScheduledOperation(
            job="J-1234",
            item="BED-KING-BLK",
            operation_num=20,
            work_center="WELD-01",
            qty_released=50.0,
            status=OperationStatus.ON_TRACK
        )
        
        data = op.model_dump()
        
        assert isinstance(data, dict)
        assert data["job"] == "J-1234"
        assert data["status"] == "on_track"  # Enum serialized to value
    
    def test_model_json_schema(self):
        """Test JSON schema generation."""
        schema = ScheduledOperation.model_json_schema()
        
        assert "properties" in schema
        assert "job" in schema["properties"]
        assert "operation_num" in schema["properties"]
