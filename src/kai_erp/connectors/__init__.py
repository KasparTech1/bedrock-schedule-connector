"""
Connector Layer - Business Logic
=================================

Each connector encapsulates a complete data access pattern:

- Which IDOs/tables to fetch
- How to join the data
- Business calculations (percent complete, status, etc.)
- Volume estimation for routing

Available Connectors:
- BedrockOpsScheduler: Production schedule visibility
- SalesOrderTracker: Open orders and backlog
- CustomerSearch: Customer lookup
- InventoryStatus: Stock levels
- OrderAvailabilityConnector: Customer order availability with allocation
"""

from kai_erp.connectors.base import BaseConnector
from kai_erp.connectors.bedrock_ops import BedrockOpsScheduler
from kai_erp.connectors.customers import CustomerSearch
from kai_erp.connectors.inventory import InventoryStatus
from kai_erp.connectors.order_availability import OrderAvailabilityConnector
from kai_erp.connectors.sales_orders import SalesOrderTracker

__all__ = [
    "BaseConnector",
    "BedrockOpsScheduler",
    "CustomerSearch",
    "InventoryStatus",
    "OrderAvailabilityConnector",
    "SalesOrderTracker",
]
