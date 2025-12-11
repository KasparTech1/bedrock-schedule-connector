"""
Shared Test Fixtures
====================

Pytest fixtures used across all test modules.
These provide mock data and test infrastructure.
"""

from datetime import datetime, timedelta, timezone
from typing import Any
from unittest.mock import AsyncMock, MagicMock

import pytest

from kai_erp.config import Config, SyteLineConfig, DataLakeConfig, VolumeThresholds, ServerConfig
from kai_erp.core.types import ConnectorResult, DataSource, IDOSpec, TokenInfo


# ─────────────────────────────────────────────────────────────────────────────
# Configuration Fixtures
# ─────────────────────────────────────────────────────────────────────────────

@pytest.fixture
def test_config() -> Config:
    """Provide test configuration with mock values."""
    return Config(
        syteline=SyteLineConfig(
            base_url="https://test.erpsl.inforcloudsuite.com",
            config_name="TEST_TST",
            username="test_user",
            password="test_pass",
        ),
        lake=DataLakeConfig(enabled=False),
        thresholds=VolumeThresholds(
            rest_preferred_max=100,
            rest_hard_max=500,
        ),
        server=ServerConfig(
            port=8100,
            log_level="DEBUG",
        )
    )


# ─────────────────────────────────────────────────────────────────────────────
# Mock Engine Fixtures
# ─────────────────────────────────────────────────────────────────────────────

@pytest.fixture
def mock_rest_engine() -> MagicMock:
    """Provide a mock REST engine for testing connectors."""
    engine = MagicMock()
    engine.parallel_fetch = AsyncMock(return_value={})
    engine.staging = MagicMock()
    engine.staging.execute_join = AsyncMock(return_value=[])
    return engine


@pytest.fixture
def mock_lake_engine() -> MagicMock:
    """Provide a mock Data Lake engine for testing."""
    engine = MagicMock()
    engine.execute = AsyncMock(return_value=[])
    return engine


# ─────────────────────────────────────────────────────────────────────────────
# Sample Data Fixtures
# ─────────────────────────────────────────────────────────────────────────────

@pytest.fixture
def sample_jobs_data() -> list[dict[str, Any]]:
    """Sample SLJobs IDO response data."""
    return [
        {
            "Job": "J-1234",
            "Suffix": 0,
            "Item": "BED-KING-BLK",
            "QtyReleased": 50.0,
            "QtyComplete": 23.0,
            "Stat": "R",
            "Whse": "MAIN"
        },
        {
            "Job": "J-1235",
            "Suffix": 0,
            "Item": "BED-QUEEN-WHT",
            "QtyReleased": 30.0,
            "QtyComplete": 5.0,
            "Stat": "R",
            "Whse": "MAIN"
        }
    ]


@pytest.fixture
def sample_jobroutes_data() -> list[dict[str, Any]]:
    """Sample SLJobroutes IDO response data."""
    return [
        {
            "Job": "J-1234",
            "Suffix": 0,
            "OperNum": 10,
            "Wc": "CUT-01",
            "QtyComplete": 50.0,
            "QtyScrapped": 0.0
        },
        {
            "Job": "J-1234",
            "Suffix": 0,
            "OperNum": 20,
            "Wc": "WELD-01",
            "QtyComplete": 23.0,
            "QtyScrapped": 0.0
        },
        {
            "Job": "J-1235",
            "Suffix": 0,
            "OperNum": 10,
            "Wc": "CUT-01",
            "QtyComplete": 30.0,
            "QtyScrapped": 0.0
        },
        {
            "Job": "J-1235",
            "Suffix": 0,
            "OperNum": 20,
            "Wc": "WELD-01",
            "QtyComplete": 5.0,
            "QtyScrapped": 0.0
        }
    ]


@pytest.fixture
def sample_items_data() -> list[dict[str, Any]]:
    """Sample SLItems IDO response data."""
    return [
        {"Item": "BED-KING-BLK", "Description": "King Bed Frame - Black"},
        {"Item": "BED-QUEEN-WHT", "Description": "Queen Bed Frame - White"},
    ]


@pytest.fixture
def sample_wcs_data() -> list[dict[str, Any]]:
    """Sample SLWcs IDO response data."""
    return [
        {"Wc": "CUT-01", "Description": "Cutting Station 1"},
        {"Wc": "WELD-01", "Description": "Welding Station 1"},
        {"Wc": "PAINT-01", "Description": "Paint Booth 1"},
    ]


@pytest.fixture
def sample_schedule_result() -> list[dict[str, Any]]:
    """Sample joined schedule result (after DuckDB join)."""
    return [
        {
            "Job": "J-1234",
            "Suffix": 0,
            "Item": "BED-KING-BLK",
            "ItemDescription": "King Bed Frame - Black",
            "QtyReleased": 50.0,
            "OperNum": 20,
            "Wc": "WELD-01",
            "WcDescription": "Welding Station 1",
            "OperQtyComplete": 23.0,
            "SchedStart": datetime(2024, 12, 9, 6, 0),
            "SchedFinish": datetime(2024, 12, 9, 14, 0),
            "PctComplete": 46.0,
            "Status": "on_track",
            "QtyOnHand": 12.0
        },
        {
            "Job": "J-1235",
            "Suffix": 0,
            "Item": "BED-QUEEN-WHT",
            "ItemDescription": "Queen Bed Frame - White",
            "QtyReleased": 30.0,
            "OperNum": 20,
            "Wc": "WELD-01",
            "WcDescription": "Welding Station 1",
            "OperQtyComplete": 5.0,
            "SchedStart": datetime(2024, 12, 8, 6, 0),
            "SchedFinish": datetime(2024, 12, 8, 14, 0),
            "PctComplete": 16.7,
            "Status": "behind",
            "QtyOnHand": 0.0
        }
    ]


@pytest.fixture
def sample_orders_data() -> list[dict[str, Any]]:
    """Sample sales order data."""
    return [
        {
            "OrderNum": "CO-12345",
            "CustomerNum": "C-100",
            "CustomerName": "Acme Corporation",
            "OrderDate": "2024-12-01",
            "DueDate": "2024-12-15",
            "Status": "O",
            "TotalAmount": 5000.00
        }
    ]


@pytest.fixture
def sample_customers_data() -> list[dict[str, Any]]:
    """Sample customer data."""
    return [
        {
            "CustomerNum": "C-100",
            "Name": "Acme Corporation",
            "ContactName": "John Smith",
            "Phone": "555-123-4567",
            "Email": "john@acme.com",
            "City": "Dallas",
            "State": "TX",
            "ZipCode": "75201",
            "Active": True
        }
    ]


@pytest.fixture
def sample_inventory_data() -> list[dict[str, Any]]:
    """Sample inventory data."""
    return [
        {
            "Item": "BED-KING-BLK",
            "Description": "King Bed Frame - Black",
            "Whse": "MAIN",
            "QtyOnHand": 100.0,
            "QtyAllocated": 25.0,
            "ReorderPoint": 20.0
        }
    ]


# ─────────────────────────────────────────────────────────────────────────────
# Token Fixtures
# ─────────────────────────────────────────────────────────────────────────────

@pytest.fixture
def valid_token() -> TokenInfo:
    """Provide a valid (not expired) token."""
    return TokenInfo(
        access_token="valid_test_token_12345",
        expires_at=datetime.now(timezone.utc) + timedelta(hours=1),
        token_type="Bearer"
    )


@pytest.fixture
def expired_token() -> TokenInfo:
    """Provide an expired token."""
    return TokenInfo(
        access_token="expired_test_token_12345",
        expires_at=datetime.now(timezone.utc) - timedelta(hours=1),
        token_type="Bearer"
    )


@pytest.fixture
def expiring_soon_token() -> TokenInfo:
    """Provide a token expiring in 2 minutes."""
    return TokenInfo(
        access_token="expiring_soon_token_12345",
        expires_at=datetime.now(timezone.utc) + timedelta(minutes=2),
        token_type="Bearer"
    )


# ─────────────────────────────────────────────────────────────────────────────
# HTTP Response Fixtures
# ─────────────────────────────────────────────────────────────────────────────

@pytest.fixture
def mock_ido_response() -> dict[str, Any]:
    """Mock IDO REST API response structure."""
    return {
        "@odata.context": "https://test.com/$metadata#SLJobs",
        "value": [
            {"Job": "J-1234", "Item": "TEST-ITEM"}
        ]
    }


@pytest.fixture
def mock_token_response() -> dict[str, Any]:
    """Mock OAuth token response."""
    return {
        "access_token": "new_access_token",
        "token_type": "Bearer",
        "expires_in": 3600
    }


# ─────────────────────────────────────────────────────────────────────────────
# Result Fixtures
# ─────────────────────────────────────────────────────────────────────────────

@pytest.fixture
def empty_connector_result() -> ConnectorResult:
    """Empty connector result."""
    return ConnectorResult(
        data=[],
        source=DataSource.REST,
        latency_ms=50,
        record_count=0
    )


@pytest.fixture
def sample_connector_result(sample_schedule_result: list) -> ConnectorResult:
    """Connector result with sample data."""
    return ConnectorResult(
        data=sample_schedule_result,
        source=DataSource.REST,
        latency_ms=450,
        record_count=len(sample_schedule_result)
    )
