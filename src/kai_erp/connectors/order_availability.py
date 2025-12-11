"""
Order Availability Connector
============================

Customer order availability with inventory allocation tracking.
Emulates the Syteline 8 TBE_Customer_Order_Availability_Add_Release_Date stored procedure.

This connector provides:
- Open customer order lines with remaining quantities
- Allocation from different production stages (On Hand → Paint → Blast → Weld/Fab)
- Estimated completion dates based on business day calendar
- Coverage analysis showing what's covered vs shortage

Source IDOs:
- SLItemwhses: Inventory levels by warehouse
- SLJobs: Job headers
- SLJobroutes: Job operations with work center quantities
- SLCos: Customer order headers
- SLCoitems: Customer order line items
- SLItems: Item master data
- SLCustaddrs: Customer addresses
"""

from datetime import date, datetime, timedelta
from typing import Any, Optional

from kai_erp.connectors.base import BaseConnector
from kai_erp.core.types import IDOSpec, RestQuerySpec
from kai_erp.models.availability import OrderAvailabilityLine


class OrderAvailabilityConnector(BaseConnector[OrderAvailabilityLine]):
    """
    Order availability connector for customer order allocation analysis.
    
    Provides visibility into:
    - Open customer orders and remaining quantities
    - How inventory is allocated across orders (priority by due date)
    - Production stage coverage (On Hand, Paint, Blast, Weld/Fab)
    - Estimated completion dates
    
    Example:
        async with RestEngine(config) as engine:
            connector = OrderAvailabilityConnector(engine)
            result = await connector.execute(
                filters={"customer": "ACME", "item": "BED-KING"}
            )
            for line in result.data:
                if line["shortage"] > 0:
                    print(f"Order {line['co_num']}: {line['shortage']} short")
    """
    
    # Typical volume estimates
    TYPICAL_OPEN_ORDERS = 500
    TYPICAL_LINES_PER_ORDER = 3
    
    # Business day offset for completion estimates (from stored proc)
    WELDFAB_BUSINESS_DAYS = 4
    BLAST_BUSINESS_DAYS = 7
    PAINT_ASSEMBLY_BUSINESS_DAYS = 10
    
    # Holidays for business day calculations (from stored proc)
    HOLIDAYS_2024_2025 = [
        date(2024, 12, 24),
        date(2024, 12, 25),
        date(2025, 1, 1),    # New Year's Day
        date(2025, 5, 26),   # Memorial Day
        date(2025, 7, 3),    # Independence Day
        date(2025, 9, 1),    # Labor Day
        date(2025, 11, 27),  # Thanksgiving
        date(2025, 12, 24),  # Christmas Eve
        date(2025, 12, 25),  # Christmas Day
    ]
    
    def get_rest_spec(self, filters: Optional[dict[str, Any]] = None) -> RestQuerySpec:
        """
        Define REST API access pattern for order availability.
        
        Fetches multiple IDOs and joins them to create the complete
        availability view with allocation.
        """
        # Build filters for open orders
        co_filter = "Stat='O'"  # Open orders only
        coitem_filter = "Stat='O'"  # Open line items
        
        # Jobs filter - Released and Firm jobs only
        job_filter = "Type='J' and (Stat='F' or Stat='R')"
        
        # ItemWhse filter - Main warehouse
        itemwhse_filter = "Whse='Main'"
        
        # Optional customer filter
        if filters and filters.get("customer"):
            # Note: customer filter applied in join SQL
            pass
        
        # Build parameterized join SQL
        join_sql, join_params = self._build_join_sql(filters)
        
        return RestQuerySpec(
            idos=[
                # Inventory levels
                IDOSpec(
                    name="SLItemwhses",
                    properties=[
                        "Item", "Whse", "QtyOnHand", "QtyAllocCo", "QtyWip"
                    ],
                    filter=itemwhse_filter
                ),
                # Jobs
                IDOSpec(
                    name="SLJobs",
                    properties=[
                        "Job", "Suffix", "Item", "QtyReleased", "Stat", "JobDate"
                    ],
                    filter=job_filter
                ),
                # Job routes for work center positions
                IDOSpec(
                    name="SLJobroutes",
                    properties=[
                        "Job", "Suffix", "OperNum", "Wc", "QtyReceived", "QtyComplete"
                    ]
                ),
                # Customer orders
                IDOSpec(
                    name="SLCos",
                    properties=[
                        "CoNum", "CustNum", "CustSeq", "OrderDate", "Stat"
                    ],
                    filter=co_filter
                ),
                # Customer order items
                IDOSpec(
                    name="SLCoitems",
                    properties=[
                        "CoNum", "CoLine", "CoRelease", "Item", "DueDate",
                        "QtyOrdered", "QtyShipped", "Price", "Stat"
                    ],
                    filter=coitem_filter
                ),
                # Items
                IDOSpec(
                    name="SLItems",
                    properties=["Item", "Description", "DrawingNbr", "PlanCode"]
                ),
                # Customer addresses
                IDOSpec(
                    name="SLCustaddrs",
                    properties=["CustNum", "CustSeq", "Name"]
                )
            ],
            join_sql=join_sql,
            join_params=join_params
        )
    
    def _build_join_sql(self, filters: Optional[dict[str, Any]] = None) -> tuple[str, list[Any]]:
        """
        Build DuckDB SQL for the complex order availability join.
        
        Uses parameterized queries to prevent SQL injection.
        
        Returns:
            Tuple of (sql_query, parameters) for safe execution.
        """
        params: list[Any] = []
        
        # This SQL performs the core join and calculations
        # The allocation logic will be handled in post-processing
        base_sql = """
            WITH 
            -- Base inventory from Main warehouse
            inventory_base AS (
                SELECT 
                    Item,
                    COALESCE(QtyOnHand, 0) as QtyOnHand,
                    COALESCE(QtyAllocCo, 0) as QtyAllocCo,
                    COALESCE(QtyWip, 0) as QtyWIP
                FROM SLItemwhses
                WHERE Whse = 'Main'
            ),
            
            -- Calculate quantities at each work center (PAINT and BLAST)
            job_wc_qty AS (
                SELECT 
                    j.Item,
                    jr.Wc,
                    SUM(COALESCE(jr.QtyReceived, 0) - COALESCE(jr.QtyComplete, 0)) as qty_at_wc
                FROM SLJobs j
                JOIN SLJobroutes jr 
                    ON j.Job = jr.Job AND j.Suffix = jr.Suffix
                WHERE j.Stat != 'C'
                  AND (COALESCE(jr.QtyReceived, 0) - COALESCE(jr.QtyComplete, 0)) > 0
                GROUP BY j.Item, jr.Wc
            ),
            
            -- Pivot work center quantities
            wc_pivot AS (
                SELECT 
                    Item,
                    SUM(CASE WHEN Wc = 'PAINT' THEN qty_at_wc ELSE 0 END) as QtyInPaint,
                    SUM(CASE WHEN Wc = 'BLAST' THEN qty_at_wc ELSE 0 END) as QtyInBlast
                FROM job_wc_qty
                GROUP BY Item
            ),
            
            -- Jobs by item with release info
            jobs_by_item AS (
                SELECT 
                    Item,
                    SUM(CASE WHEN Stat = 'R' THEN QtyReleased ELSE 0 END) as QtyReleased,
                    MAX(JobDate) as ReleasedDate,
                    STRING_AGG(Job, '; ') as Jobs
                FROM SLJobs
                WHERE Stat IN ('F', 'R')
                GROUP BY Item
            ),
            
            -- Combined inventory with all quantities
            inventory_combined AS (
                SELECT 
                    ib.Item,
                    ib.QtyOnHand,
                    ib.QtyOnHand as QtyOnHand_Cursor,
                    ib.QtyAllocCo,
                    ib.QtyWIP,
                    COALESCE(wp.QtyInPaint, 0) as QtyInPaint,
                    COALESCE(wp.QtyInBlast, 0) as QtyInBlast,
                    CASE 
                        WHEN ib.QtyWIP - COALESCE(wp.QtyInPaint, 0) - COALESCE(wp.QtyInBlast, 0) < 0 
                        THEN 0
                        ELSE ib.QtyWIP - COALESCE(wp.QtyInPaint, 0) - COALESCE(wp.QtyInBlast, 0)
                    END as ReleasedWeldFab,
                    jbi.QtyReleased as JobQtyReleased,
                    jbi.ReleasedDate,
                    jbi.Jobs
                FROM inventory_base ib
                LEFT JOIN wc_pivot wp ON ib.Item = wp.Item
                LEFT JOIN jobs_by_item jbi ON ib.Item = jbi.Item
            )
            
            -- Final query: Open customer orders with inventory info
            SELECT 
                ROW_NUMBER() OVER (ORDER BY ci.DueDate, ca.Name, ci.Item) as CO_DataId,
                co.CoNum as co_num,
                ci.CoLine as co_line,
                ci.CoRelease as co_release,
                ca.Name as CustomerName,
                co.OrderDate as OrderDate,
                ci.DueDate as DueDate,
                ci.Item,
                i.DrawingNbr as Model,
                i.Description as ItemDescription,
                i.PlanCode,
                ci.QtyOrdered as QtyOrdered,
                COALESCE(ci.QtyShipped, 0) as QtyShipped,
                ci.QtyOrdered - COALESCE(ci.QtyShipped, 0) as QtyRemaining,
                COALESCE(inv.QtyOnHand, 0) as TotalOnHand,
                COALESCE(inv.QtyAllocCo, 0) as QtyAllocCo,
                COALESCE(inv.JobQtyReleased, 0) as QtyReleased,
                COALESCE(inv.Jobs, '') as Jobs,
                (ci.QtyOrdered - COALESCE(ci.QtyShipped, 0)) * ci.Price as LineAmount,
                COALESCE(inv.QtyWIP, 0) as QtyWIP,
                COALESCE(inv.QtyInPaint, 0) as TotalInPaint,
                COALESCE(inv.QtyInBlast, 0) as TotalInBlast,
                COALESCE(inv.ReleasedWeldFab, 0) as TotalInReleasedWeldFab,
                inv.ReleasedDate
                
            FROM SLCos co
            JOIN SLCoitems ci ON co.CoNum = ci.CoNum
            LEFT JOIN SLItems i ON ci.Item = i.Item
            LEFT JOIN SLCustaddrs ca ON co.CustNum = ca.CustNum AND co.CustSeq = ca.CustSeq
            LEFT JOIN inventory_combined inv ON ci.Item = inv.Item
            
            WHERE co.Stat = 'O'
              AND ci.Stat = 'O'
              AND ci.QtyOrdered - COALESCE(ci.QtyShipped, 0) > 0
        """
        
        # Add optional filters using parameterized queries
        where_additions = []
        
        if filters:
            if filters.get("customer"):
                where_additions.append("ca.Name LIKE ?")
                params.append(f"%{filters['customer']}%")
            if filters.get("item"):
                where_additions.append("ci.Item LIKE ?")
                params.append(f"%{filters['item']}%")
            if filters.get("due_within_days"):
                # Would need date arithmetic in DuckDB
                pass
        
        if where_additions:
            base_sql += " AND " + " AND ".join(where_additions)
        
        base_sql += " ORDER BY ci.DueDate, ca.Name, ci.Item"
        
        return base_sql, params
    
    def get_lake_query(self, filters: Optional[dict[str, Any]] = None) -> str:
        """
        Define Data Lake SQL query for order availability.
        
        Uses Compass SQL syntax against replicated Syteline tables.
        """
        return """
            SELECT 
                co.co_num,
                ci.co_line,
                ci.co_release,
                ca.name as CustomerName,
                co.order_date as OrderDate,
                ci.due_date as DueDate,
                ci.item as Item,
                i.description as ItemDescription,
                ci.qty_ordered as QtyOrdered,
                ci.qty_shipped as QtyShipped,
                ci.qty_ordered - COALESCE(ci.qty_shipped, 0) as QtyRemaining
                
            FROM SYTELINE.co co
            JOIN SYTELINE.coitem ci ON co.co_num = ci.co_num
            LEFT JOIN SYTELINE.item i ON ci.item = i.item
            LEFT JOIN SYTELINE.custaddr ca 
                ON co.cust_num = ca.cust_num AND co.cust_seq = ca.cust_seq
            
            WHERE co.stat = 'O'
              AND ci.stat = 'O'
              AND ci.qty_ordered - COALESCE(ci.qty_shipped, 0) > 0
            
            ORDER BY ci.due_date, ca.name, ci.item
        """
    
    async def estimate_volume(self, filters: Optional[dict[str, Any]] = None) -> int:
        """
        Estimate result count based on typical volumes and filters.
        """
        base = self.TYPICAL_OPEN_ORDERS * self.TYPICAL_LINES_PER_ORDER  # ~1500
        
        if not filters:
            return base
        
        # Filters reduce volume
        if filters.get("customer"):
            return 50  # Specific customer
        if filters.get("item"):
            return 30  # Specific item
        if filters.get("due_within_days"):
            days = filters["due_within_days"]
            return base * min(days, 30) // 90  # Rough estimate
        
        return base
    
    async def execute(
        self,
        filters: Optional[dict[str, Any]] = None,
        **kwargs
    ):
        """
        Execute the connector with post-processing for allocation.
        
        Override base execute to add allocation logic that mimics
        the cursor-based allocation in the stored procedure.
        """
        # Get raw data from base execution
        result = await super().execute(filters=filters, **kwargs)
        
        # Post-process to apply allocation logic
        allocated_data = self._apply_allocation_logic(result.data)
        
        # Replace data with allocated version
        result.data = allocated_data
        
        return result
    
    def _apply_allocation_logic(self, data: list[dict[str, Any]]) -> list[dict[str, Any]]:
        """
        Apply allocation logic similar to the stored procedure cursor.
        
        Allocates inventory to orders in due date priority order:
        1. Allocate from On Hand first
        2. Then from Paint queue
        3. Then from Blast queue  
        4. Then from Released Weld/Fab
        """
        # Build item inventory tracking dict
        inventory_by_item: dict[str, dict[str, float]] = {}
        
        for row in data:
            item = row.get("item", "")
            if item and item not in inventory_by_item:
                inventory_by_item[item] = {
                    "on_hand": row.get("total_on_hand", 0) or 0,
                    "in_paint": row.get("total_in_paint", 0) or 0,
                    "in_blast": row.get("total_in_blast", 0) or 0,
                    "released_weld_fab": row.get("total_in_released_weld_fab", 0) or 0,
                }
        
        # Process each order line in due date order (already sorted)
        for row in data:
            item = row.get("item", "")
            qty_remaining = row.get("qty_remaining", 0) or 0
            
            if not item or qty_remaining <= 0:
                continue
            
            inv = inventory_by_item.get(item, {
                "on_hand": 0, "in_paint": 0, "in_blast": 0, "released_weld_fab": 0
            })
            
            remaining_to_allocate = qty_remaining
            qty_remaining_covered = 0.0
            
            # Record current on hand before allocation
            row["current_on_hand"] = inv["on_hand"]
            
            # 1. Allocate from On Hand
            if remaining_to_allocate > 0 and inv["on_hand"] > 0:
                allocated = min(remaining_to_allocate, inv["on_hand"])
                row["qty_on_hand"] = allocated
                inv["on_hand"] -= allocated
                remaining_to_allocate -= allocated
                qty_remaining_covered += allocated
            else:
                row["qty_on_hand"] = 0
            
            # 2. Allocate from Paint
            if remaining_to_allocate > 0 and inv["in_paint"] > 0:
                allocated = min(remaining_to_allocate, inv["in_paint"])
                row["allocated_from_paint"] = allocated
                inv["in_paint"] -= allocated
                remaining_to_allocate -= allocated
                qty_remaining_covered += allocated
            else:
                row["allocated_from_paint"] = 0
            
            # 3. Allocate from Blast
            if remaining_to_allocate > 0 and inv["in_blast"] > 0:
                allocated = min(remaining_to_allocate, inv["in_blast"])
                row["allocated_from_blast"] = allocated
                inv["in_blast"] -= allocated
                remaining_to_allocate -= allocated
                qty_remaining_covered += allocated
            else:
                row["allocated_from_blast"] = 0
            
            # 4. Allocate from Released Weld/Fab
            if remaining_to_allocate > 0 and inv["released_weld_fab"] > 0:
                allocated = min(remaining_to_allocate, inv["released_weld_fab"])
                row["allocated_from_released_weld_fab"] = allocated
                inv["released_weld_fab"] -= allocated
                remaining_to_allocate -= allocated
                qty_remaining_covered += allocated
            else:
                row["allocated_from_released_weld_fab"] = 0
            
            row["qty_remaining_covered"] = qty_remaining_covered
            
            # Update inventory tracking
            inventory_by_item[item] = inv
        
        return data
    
    def transform_result(self, row: dict[str, Any]) -> OrderAvailabilityLine:
        """
        Transform query result row to OrderAvailabilityLine model.
        """
        # Parse dates
        released_date = self._parse_date(row.get("ReleasedDate") or row.get("released_date"))
        
        # Calculate completion dates based on business days
        weld_fab_date = None
        blast_date = None
        paint_date = None
        
        if released_date:
            weld_fab_date = self._add_business_days(released_date, self.WELDFAB_BUSINESS_DAYS)
            blast_date = self._add_business_days(released_date, self.BLAST_BUSINESS_DAYS)
            paint_date = self._add_business_days(released_date, self.PAINT_ASSEMBLY_BUSINESS_DAYS)
        
        return OrderAvailabilityLine(
            co_data_id=int(row.get("CO_DataId") or row.get("co_data_id") or 0),
            co_num=str(row.get("co_num") or ""),
            co_line=int(row.get("co_line") or 0),
            co_release=int(row.get("co_release") or 0),
            customer_name=str(row.get("CustomerName") or row.get("customer_name") or ""),
            order_date=self._parse_date(row.get("OrderDate") or row.get("order_date")),
            due_date=self._parse_date(row.get("DueDate") or row.get("due_date")),
            released_date=released_date,
            weld_fab_completion_date=weld_fab_date,
            blast_completion_date=blast_date,
            paint_assembly_completion_date=paint_date,
            item=str(row.get("Item") or row.get("item") or ""),
            model=str(row.get("Model") or row.get("model") or ""),
            item_description=str(row.get("ItemDescription") or row.get("item_description") or ""),
            qty_ordered=float(row.get("QtyOrdered") or row.get("qty_ordered") or 0),
            qty_shipped=float(row.get("QtyShipped") or row.get("qty_shipped") or 0),
            qty_remaining=float(row.get("QtyRemaining") or row.get("qty_remaining") or 0),
            qty_remaining_covered=float(row.get("qty_remaining_covered") or 0),
            qty_on_hand=float(row.get("qty_on_hand") or 0),
            current_on_hand=float(row.get("current_on_hand") or row.get("TotalOnHand") or 0),
            qty_nf=float(row.get("QtyNF") or row.get("qty_nf") or 0),
            qty_alloc_co=float(row.get("QtyAllocCo") or row.get("qty_alloc_co") or 0),
            qty_wip=float(row.get("QtyWIP") or row.get("qty_wip") or 0),
            qty_released=float(row.get("QtyReleased") or row.get("qty_released") or 0),
            total_in_paint=float(row.get("TotalInPaint") or row.get("total_in_paint") or 0),
            allocated_from_paint=float(row.get("allocated_from_paint") or 0),
            total_in_blast=float(row.get("TotalInBlast") or row.get("total_in_blast") or 0),
            allocated_from_blast=float(row.get("allocated_from_blast") or 0),
            total_in_released_weld_fab=float(
                row.get("TotalInReleasedWeldFab") or row.get("total_in_released_weld_fab") or 0
            ),
            allocated_from_released_weld_fab=float(row.get("allocated_from_released_weld_fab") or 0),
            jobs=str(row.get("Jobs") or row.get("jobs") or ""),
            line_amount=float(row.get("LineAmount") or row.get("line_amount") or 0)
        )
    
    def _parse_date(self, value: Any) -> Optional[date]:
        """Parse date from various formats."""
        if value is None:
            return None
        if isinstance(value, date) and not isinstance(value, datetime):
            return value
        if isinstance(value, datetime):
            return value.date()
        if isinstance(value, str):
            try:
                # Try ISO format first
                return datetime.fromisoformat(value.replace("Z", "+00:00")).date()
            except ValueError:
                try:
                    # Try common date formats
                    return datetime.strptime(value[:10], "%Y-%m-%d").date()
                except ValueError:
                    return None
        return None
    
    def _is_business_day(self, check_date: date) -> bool:
        """
        Check if a date is a business day.
        
        Business days are Monday-Thursday (not Friday, Saturday, Sunday)
        and not holidays.
        """
        # Weekday: 0=Mon, 1=Tue, 2=Wed, 3=Thu, 4=Fri, 5=Sat, 6=Sun
        # Per stored proc: Fridays (4), Saturdays (5), Sundays (6) are not business days
        if check_date.weekday() >= 4:  # Friday or weekend
            return False
        
        # Check holidays
        if check_date in self.HOLIDAYS_2024_2025:
            return False
        
        return True
    
    def _add_business_days(self, start_date: date, business_days: int) -> date:
        """
        Add business days to a date.
        
        Skips weekends (including Fridays per stored proc) and holidays.
        """
        current = start_date
        days_added = 0
        
        while days_added < business_days:
            current = current + timedelta(days=1)
            if self._is_business_day(current):
                days_added += 1
        
        return current
