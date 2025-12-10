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
"""

from kai_erp.connectors.base import BaseConnector
from kai_erp.connectors.bedrock_ops import BedrockOpsScheduler
from kai_erp.connectors.sales_orders import SalesOrderTracker
from kai_erp.connectors.customers import CustomerSearch
from kai_erp.connectors.inventory import InventoryStatus

__all__ = [
    "BaseConnector",
    "BedrockOpsScheduler",
    "SalesOrderTracker",
    "CustomerSearch",
    "InventoryStatus",
]
