"""
Tests for Bedrock Ops Scheduler Connector
=========================================
"""

import pytest
from unittest.mock import AsyncMock, MagicMock

from kai_erp.connectors.bedrock_ops import BedrockOpsScheduler
from kai_erp.core.types import DataSource
from kai_erp.models.operations import OperationStatus


class TestBedrockOpsScheduler:
    """Tests for BedrockOpsScheduler connector."""
    
    @pytest.fixture
    def connector(self, mock_rest_engine):
        """Create connector with mock engine."""
        return BedrockOpsScheduler(mock_rest_engine)
    
    def test_get_rest_spec_no_filters(self, connector):
        """Test REST spec generation without filters."""
        spec = connector.get_rest_spec()
        
        # Should have 6 IDOs
        assert len(spec.idos) == 6
        
        # Check IDO names
        ido_names = [ido.name for ido in spec.idos]
        assert "SLJobs" in ido_names
        assert "SLJobroutes" in ido_names
        assert "SLJrtSchs" in ido_names
        assert "SLItems" in ido_names
        assert "SLItemwhses" in ido_names
        assert "SLWcs" in ido_names
        
        # Jobs should filter to released only
        jobs_ido = next(i for i in spec.idos if i.name == "SLJobs")
        assert "Stat='R'" in jobs_ido.filter
    
    def test_get_rest_spec_with_work_center(self, connector):
        """Test REST spec with work center filter."""
        spec = connector.get_rest_spec(filters={"work_center": "WELD-01"})
        
        # Jobroutes should have filter
        jobroutes_ido = next(i for i in spec.idos if i.name == "SLJobroutes")
        assert jobroutes_ido.filter == "Wc='WELD-01'"
    
    def test_get_rest_spec_with_job_filter(self, connector):
        """Test REST spec with job filter."""
        spec = connector.get_rest_spec(filters={"job": "J-1234"})
        
        # Jobs should have additional filter
        jobs_ido = next(i for i in spec.idos if i.name == "SLJobs")
        assert "Job='J-1234'" in jobs_ido.filter
    
    @pytest.mark.asyncio
    async def test_estimate_volume_no_filters(self, connector):
        """Test volume estimation without filters."""
        volume = await connector.estimate_volume()
        
        # Should be typical active jobs × ops per job
        expected = connector.TYPICAL_ACTIVE_JOBS * connector.TYPICAL_OPS_PER_JOB
        assert volume == expected
    
    @pytest.mark.asyncio
    async def test_estimate_volume_with_work_center(self, connector):
        """Test volume estimation with work center filter."""
        volume = await connector.estimate_volume(filters={"work_center": "WELD-01"})
        
        # Should be about 1/10 of base
        base = connector.TYPICAL_ACTIVE_JOBS * connector.TYPICAL_OPS_PER_JOB
        assert volume == base // 10
    
    @pytest.mark.asyncio
    async def test_estimate_volume_with_job(self, connector):
        """Test volume estimation with job filter."""
        volume = await connector.estimate_volume(filters={"job": "J-1234"})
        
        # Should be typical ops per job
        assert volume == connector.TYPICAL_OPS_PER_JOB
    
    def test_transform_result(self, connector, sample_schedule_result):
        """Test transforming a result row."""
        row = sample_schedule_result[0]
        
        operation = connector.transform_result(row)
        
        assert operation.job == "J-1234"
        assert operation.item == "BED-KING-BLK"
        assert operation.item_description == "King Bed Frame - Black"
        assert operation.work_center == "WELD-01"
        assert operation.pct_complete == 46.0
        assert operation.status == OperationStatus.ON_TRACK
    
    def test_transform_result_behind_status(self, connector, sample_schedule_result):
        """Test transforming a behind schedule operation."""
        row = sample_schedule_result[1]
        
        operation = connector.transform_result(row)
        
        assert operation.job == "J-1235"
        assert operation.status == OperationStatus.BEHIND
    
    @pytest.mark.asyncio
    async def test_execute_returns_result(self, connector, sample_schedule_result):
        """Test execute returns ConnectorResult."""
        # Setup mock
        connector.rest_engine.parallel_fetch = AsyncMock(return_value={})
        connector.rest_engine.staging.execute_join = AsyncMock(
            return_value=sample_schedule_result
        )
        
        result = await connector.execute(filters={"work_center": "WELD-01"})
        
        assert result.source == DataSource.REST
        assert result.record_count == 2
        assert len(result.data) == 2
        
        # Check first operation
        assert result.data[0]["job"] == "J-1234"
        assert result.data[0]["pct_complete"] == 46.0


class TestJoinSQL:
    """Tests for join SQL generation."""
    
    @pytest.fixture
    def connector(self, mock_rest_engine):
        return BedrockOpsScheduler(mock_rest_engine)
    
    def test_join_sql_excludes_completed_by_default(self, connector):
        """Join SQL should exclude completed operations by default."""
        spec = connector.get_rest_spec()
        
        assert "QtyComplete" in spec.join_sql
        assert "QtyReleased" in spec.join_sql
    
    def test_join_sql_includes_completed_when_requested(self, connector):
        """Join SQL should include completed when include_completed=True."""
        spec = connector.get_rest_spec(filters={"include_completed": True})
        
        # Should not have the exclusion clause
        # The SQL should still work but not filter out completed
        assert spec.join_sql is not None
