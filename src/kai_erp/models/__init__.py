"""
Data Models
===========

Pydantic models for all business objects returned by connectors.
These models serve as the contract between connectors and consumers.

Models:
- ScheduledOperation: Production schedule operation
- SalesOrder, OrderLine: Sales order with line items
- Customer, CustomerAddress: Customer information
- InventoryItem, WarehouseStock: Inventory levels
"""

from kai_erp.models.operations import ScheduledOperation
from kai_erp.models.orders import OrderLine, SalesOrder
from kai_erp.models.customers import Customer, CustomerAddress
from kai_erp.models.inventory import InventoryItem, WarehouseStock

__all__ = [
    # Operations
    "ScheduledOperation",
    # Orders
    "SalesOrder",
    "OrderLine",
    # Customers
    "Customer",
    "CustomerAddress",
    # Inventory
    "InventoryItem",
    "WarehouseStock",
]
