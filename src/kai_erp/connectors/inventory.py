"""
Inventory Status Connector
==========================

Stock levels and availability.

Source IDOs:
- SLItems: Item master
- SLItemwhses: Warehouse stock levels
- SLItemlocs: Location-level stock (optional)
"""

from typing import Any, Optional

from kai_erp.connectors.base import BaseConnector
from kai_erp.core.types import IDOSpec, RestQuerySpec
from kai_erp.models.inventory import InventoryItem, WarehouseStock


class InventoryStatus(BaseConnector[InventoryItem]):
    """
    Inventory status connector for stock levels.
    
    Provides visibility into quantity on hand, allocated, and available.
    
    Example:
        async with RestEngine(config) as engine:
            inventory = InventoryStatus(engine)
            result = await inventory.execute(
                filters={"warehouse": "MAIN", "low_stock_only": True}
            )
    """
    
    TYPICAL_ACTIVE_ITEMS = 1000
    
    def get_rest_spec(self, filters: Optional[dict[str, Any]] = None) -> RestQuerySpec:
        """Define REST API access pattern for inventory status."""
        
        # Build item filter
        item_filter = None
        if filters and filters.get("item"):
            item_filter = f"Item='{filters['item']}'"
        
        # Build warehouse filter
        whse_filter = None
        if filters and filters.get("warehouse"):
            whse_filter = f"Whse='{filters['warehouse']}'"
        
        return RestQuerySpec(
            idos=[
                IDOSpec(
                    name="SLItems",
                    properties=[
                        "Item", "Description", "ProductCode", "UM",
                        "ReorderPoint", "ReorderQty", "UnitCost"
                    ],
                    filter=item_filter
                ),
                IDOSpec(
                    name="SLItemwhses",
                    properties=[
                        "Item", "Whse", "QtyOnHand", "QtyAllocCo",
                        "QtyAllocWo", "SafetyStockQty"
                    ],
                    filter=whse_filter
                )
            ],
            join_sql=self._build_join_sql(filters)
        )
    
    def _build_join_sql(self, filters: Optional[dict[str, Any]] = None) -> str:
        """Build the DuckDB join SQL."""
        sql = """
            SELECT 
                i.Item,
                i.Description,
                i.ProductCode,
                i.UM,
                i.ReorderPoint,
                i.ReorderQty,
                i.UnitCost,
                iw.Whse as Warehouse,
                iw.QtyOnHand,
                COALESCE(iw.QtyAllocCo, 0) + COALESCE(iw.QtyAllocWo, 0) as QtyAllocated,
                iw.QtyOnHand - COALESCE(iw.QtyAllocCo, 0) - COALESCE(iw.QtyAllocWo, 0) as QtyAvailable,
                CASE 
                    WHEN i.ReorderPoint IS NOT NULL 
                    AND (iw.QtyOnHand - COALESCE(iw.QtyAllocCo, 0) - COALESCE(iw.QtyAllocWo, 0)) <= i.ReorderPoint
                    THEN true
                    ELSE false
                END as IsLowStock
                
            FROM SLItems i
            LEFT JOIN SLItemwhses iw ON i.Item = iw.Item
        """
        
        where_parts = []
        if filters:
            if filters.get("item"):
                where_parts.append(f"i.Item = '{filters['item']}'")
            if filters.get("warehouse"):
                where_parts.append(f"iw.Whse = '{filters['warehouse']}'")
            if filters.get("low_stock_only"):
                where_parts.append("""
                    i.ReorderPoint IS NOT NULL 
                    AND (iw.QtyOnHand - COALESCE(iw.QtyAllocCo, 0) - COALESCE(iw.QtyAllocWo, 0)) <= i.ReorderPoint
                """)
        
        if where_parts:
            sql += " WHERE " + " AND ".join(where_parts)
        
        sql += " ORDER BY i.Item, iw.Whse"
        
        return sql
    
    def get_lake_query(self, filters: Optional[dict[str, Any]] = None) -> str:
        """Define Data Lake SQL query."""
        return """
            SELECT 
                i.item as Item,
                i.description as Description,
                iw.whse as Warehouse,
                iw.qty_on_hand as QtyOnHand,
                iw.qty_alloc_co + iw.qty_alloc_wo as QtyAllocated
                
            FROM SYTELINE.item i
            LEFT JOIN SYTELINE.itemwhse iw ON i.item = iw.item
            
            ORDER BY i.item
        """
    
    async def estimate_volume(self, filters: Optional[dict[str, Any]] = None) -> int:
        """Estimate result count."""
        if filters and filters.get("item"):
            return 5  # Single item, few warehouses
        if filters and filters.get("warehouse"):
            return self.TYPICAL_ACTIVE_ITEMS  # One warehouse
        if filters and filters.get("low_stock_only"):
            return 50  # Typically small subset
        return self.TYPICAL_ACTIVE_ITEMS * 3  # All items × warehouses
    
    def transform_result(self, row: dict[str, Any]) -> InventoryItem:
        """Transform query result to InventoryItem model."""
        # Build warehouse stock if warehouse data present
        warehouse_stock = []
        if row.get("Warehouse"):
            warehouse_stock.append(WarehouseStock(
                warehouse=str(row.get("Warehouse", "")),
                qty_on_hand=float(row.get("QtyOnHand", 0)),
                qty_allocated=float(row.get("QtyAllocated", 0)),
                qty_available=float(row.get("QtyAvailable", 0))
            ))
        
        return InventoryItem(
            item=str(row.get("Item", "")),
            description=str(row.get("Description", "")),
            product_code=str(row.get("ProductCode", "")),
            um=str(row.get("UM", "EA")),
            total_on_hand=float(row.get("QtyOnHand", 0)),
            total_allocated=float(row.get("QtyAllocated", 0)),
            total_available=float(row.get("QtyAvailable", 0)),
            reorder_point=float(row.get("ReorderPoint")) if row.get("ReorderPoint") else None,
            reorder_qty=float(row.get("ReorderQty")) if row.get("ReorderQty") else None,
            is_low_stock=bool(row.get("IsLowStock", False)),
            warehouse_stock=warehouse_stock,
            unit_cost=float(row.get("UnitCost")) if row.get("UnitCost") else None
        )
