"""
Sales Order Tracker Connector
=============================

Open orders and backlog visibility.

Source IDOs:
- SLCos: Order headers
- SLCoitems: Order line items
- SLCustomers: Customer information
- SLItems: Item descriptions
"""

from datetime import date, datetime
from typing import Any, Optional

from kai_erp.connectors.base import BaseConnector
from kai_erp.core.types import IDOSpec, RestQuerySpec
from kai_erp.models.orders import OrderLine, OrderStatus, SalesOrder


class SalesOrderTracker(BaseConnector[SalesOrder]):
    """
    Sales order connector for tracking open orders.
    
    Provides visibility into open orders, backlog, and customer orders.
    
    Example:
        async with RestEngine(config) as engine:
            tracker = SalesOrderTracker(engine)
            result = await tracker.execute(
                filters={"customer": "ACME", "days_out": 7}
            )
    """
    
    TYPICAL_OPEN_ORDERS = 500
    
    def get_rest_spec(self, filters: Optional[dict[str, Any]] = None) -> RestQuerySpec:
        """Define REST API access pattern for sales orders."""
        
        # Build order filter - open orders only
        order_filter = "Stat='O'"  # Open orders
        
        if filters:
            if filters.get("customer"):
                order_filter += f" and CustNum like '%{filters['customer']}%'"
            if filters.get("days_out"):
                # Filter by due date within N days
                pass  # Would need date calculation
        
        return RestQuerySpec(
            idos=[
                IDOSpec(
                    name="SLCos",
                    properties=[
                        "CoNum", "CustNum", "OrderDate", "DueDate",
                        "Stat", "ShipToName", "ShipToCity", "ShipToState"
                    ],
                    filter=order_filter
                ),
                IDOSpec(
                    name="SLCoitems",
                    properties=[
                        "CoNum", "CoLine", "Item", "QtyOrdered",
                        "QtyShipped", "Price", "DueDate", "Whse"
                    ]
                ),
                IDOSpec(
                    name="SLCustomers",
                    properties=["CustNum", "Name"]
                ),
                IDOSpec(
                    name="SLItems",
                    properties=["Item", "Description"]
                )
            ],
            join_sql=self._build_join_sql(filters)
        )
    
    def _build_join_sql(self, filters: Optional[dict[str, Any]] = None) -> str:
        """Build the DuckDB join SQL."""
        return """
            SELECT 
                o.CoNum as OrderNum,
                o.CustNum as CustomerNum,
                c.Name as CustomerName,
                o.OrderDate,
                o.DueDate,
                o.Stat as Status,
                o.ShipToName,
                o.ShipToCity,
                o.ShipToState,
                oi.CoLine as Line,
                oi.Item,
                i.Description as ItemDescription,
                oi.QtyOrdered,
                oi.QtyShipped,
                oi.QtyOrdered - COALESCE(oi.QtyShipped, 0) as QtyRemaining,
                oi.Price as UnitPrice,
                oi.QtyOrdered * oi.Price as ExtendedPrice,
                oi.DueDate as LineDueDate,
                oi.Whse as Warehouse
                
            FROM SLCos o
            LEFT JOIN SLCoitems oi ON o.CoNum = oi.CoNum
            LEFT JOIN SLCustomers c ON o.CustNum = c.CustNum
            LEFT JOIN SLItems i ON oi.Item = i.Item
            
            ORDER BY o.DueDate, o.CoNum, oi.CoLine
        """
    
    def get_lake_query(self, filters: Optional[dict[str, Any]] = None) -> str:
        """Define Data Lake SQL query."""
        return """
            SELECT 
                o.co_num as OrderNum,
                o.cust_num as CustomerNum,
                c.name as CustomerName,
                o.order_date as OrderDate,
                o.due_date as DueDate,
                o.stat as Status
                
            FROM SYTELINE.co o
            LEFT JOIN SYTELINE.customer c ON o.cust_num = c.cust_num
            
            WHERE o.stat = 'O'
            ORDER BY o.due_date
        """
    
    async def estimate_volume(self, filters: Optional[dict[str, Any]] = None) -> int:
        """Estimate result count."""
        if filters and filters.get("customer"):
            return 50  # Specific customer
        if filters and filters.get("days_out"):
            return self.TYPICAL_OPEN_ORDERS // 4  # Subset by date
        return self.TYPICAL_OPEN_ORDERS
    
    def transform_result(self, row: dict[str, Any]) -> SalesOrder:
        """Transform query result to SalesOrder model."""
        # Map status codes
        status_map = {
            "O": OrderStatus.OPEN,
            "S": OrderStatus.SHIPPED,
            "I": OrderStatus.INVOICED,
            "C": OrderStatus.CLOSED,
            "H": OrderStatus.HOLD
        }
        status = status_map.get(str(row.get("Status", "O")), OrderStatus.OPEN)
        
        # Build order line if line data present
        lines = []
        if row.get("Line"):
            lines.append(OrderLine(
                line=int(row.get("Line", 0)),
                item=str(row.get("Item", "")),
                item_description=str(row.get("ItemDescription", "")),
                qty_ordered=float(row.get("QtyOrdered", 0)),
                qty_shipped=float(row.get("QtyShipped", 0)),
                qty_remaining=float(row.get("QtyRemaining", 0)),
                unit_price=float(row.get("UnitPrice", 0)),
                extended_price=float(row.get("ExtendedPrice", 0)),
                due_date=self._parse_date(row.get("LineDueDate")),
                warehouse=str(row.get("Warehouse", ""))
            ))
        
        return SalesOrder(
            order_num=str(row.get("OrderNum", "")),
            customer_num=str(row.get("CustomerNum", "")),
            customer_name=str(row.get("CustomerName", "")),
            order_date=self._parse_date(row.get("OrderDate")),
            due_date=self._parse_date(row.get("DueDate")),
            status=status,
            ship_to_name=str(row.get("ShipToName", "")),
            ship_to_city=str(row.get("ShipToCity", "")),
            ship_to_state=str(row.get("ShipToState", "")),
            lines=lines
        )
    
    def _parse_date(self, value: Any) -> Optional[date]:
        """Parse date from various formats."""
        if value is None:
            return None
        if isinstance(value, date):
            return value
        if isinstance(value, datetime):
            return value.date()
        if isinstance(value, str):
            try:
                return datetime.fromisoformat(value.replace("Z", "+00:00")).date()
            except ValueError:
                return None
        return None
