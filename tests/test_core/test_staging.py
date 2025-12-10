"""
Tests for DuckDB Staging Engine
===============================
"""

import pytest

from kai_erp.core.staging import StagingEngine


class TestStagingEngine:
    """Tests for StagingEngine."""
    
    def test_sync_context_manager(self):
        """Test synchronous context manager."""
        with StagingEngine() as staging:
            assert staging._conn is not None
        assert staging._conn is None
    
    @pytest.mark.asyncio
    async def test_async_context_manager(self):
        """Test asynchronous context manager."""
        async with StagingEngine() as staging:
            assert staging._conn is not None
        assert staging._conn is None
    
    def test_load_records(self, sample_jobs_data):
        """Test loading records into a table."""
        with StagingEngine() as staging:
            staging.load_records("jobs", sample_jobs_data)
            
            assert staging.table_exists("jobs")
            assert staging.get_table_count("jobs") == len(sample_jobs_data)
    
    def test_load_empty_records(self):
        """Test loading empty records."""
        with StagingEngine() as staging:
            staging.load_records("empty_table", [])
            
            assert staging.table_exists("empty_table")
            assert staging.get_table_count("empty_table") == 0
    
    def test_execute_query(self, sample_jobs_data):
        """Test executing a query."""
        with StagingEngine() as staging:
            staging.load_records("jobs", sample_jobs_data)
            
            result = staging.execute_query("SELECT Job, Item FROM jobs ORDER BY Job")
            
            assert len(result) == 2
            assert result[0]["Job"] == "J-1234"
            assert result[0]["Item"] == "BED-KING-BLK"
    
    def test_join_query(self, sample_jobs_data, sample_items_data):
        """Test joining multiple tables."""
        with StagingEngine() as staging:
            staging.load_records("SLJobs", sample_jobs_data)
            staging.load_records("SLItems", sample_items_data)
            
            result = staging.execute_query("""
                SELECT j.Job, j.Item, i.Description
                FROM SLJobs j
                LEFT JOIN SLItems i ON j.Item = i.Item
                ORDER BY j.Job
            """)
            
            assert len(result) == 2
            assert result[0]["Description"] == "King Bed Frame - Black"
            assert result[1]["Description"] == "Queen Bed Frame - White"
    
    @pytest.mark.asyncio
    async def test_execute_join_method(self, sample_jobs_data, sample_items_data):
        """Test the execute_join convenience method."""
        async with StagingEngine() as staging:
            ido_data = {
                "SLJobs": sample_jobs_data,
                "SLItems": sample_items_data
            }
            
            join_sql = """
                SELECT j.Job, i.Description
                FROM SLJobs j
                LEFT JOIN SLItems i ON j.Item = i.Item
            """
            
            result = await staging.execute_join(ido_data, join_sql)
            
            assert len(result) == 2
    
    def test_calculated_columns(self, sample_jobs_data):
        """Test queries with calculated columns."""
        with StagingEngine() as staging:
            staging.load_records("jobs", sample_jobs_data)
            
            result = staging.execute_query("""
                SELECT 
                    Job,
                    QtyComplete,
                    QtyReleased,
                    ROUND((QtyComplete / QtyReleased) * 100, 1) as PctComplete
                FROM jobs
                ORDER BY Job
            """)
            
            assert result[0]["PctComplete"] == 46.0  # 23/50 * 100
