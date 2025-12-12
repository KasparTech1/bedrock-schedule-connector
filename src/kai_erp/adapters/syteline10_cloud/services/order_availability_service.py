"""Order availability service."""
from typing import Optional
from datetime import date, datetime, timezone, timedelta

import structlog

from ..mongoose_client import MongooseClient, MongooseConfig
from ..models.orders import OrderAvailabilityLine, OrderAvailabilityResult
from ..utils import clean_str, parse_float, parse_syteline_date, format_date
from ...core.metrics import get_metrics_store

logger = structlog.get_logger(__name__)


class OrderAvailabilityService:
    """Service for order availability and allocation."""
    
    def __init__(self, config: MongooseConfig):
        self.config = config
    
    async def get_order_availability(
        self,
        customer: Optional[str] = None,
        item: Optional[str] = None,
        limit: int = 500,
        track_metrics: bool = True,
    ) -> OrderAvailabilityResult:
        """
        Get order availability with inventory allocation analysis.
        
        Emulates the TBE_Customer_Order_Availability_Add_Release_Date stored procedure.
        
        Shows open customer orders with how inventory is allocated from different
        production stages: On Hand → Paint → Blast → Weld/Fab.
        
        Args:
            customer: Optional customer name filter (partial match)
            item: Optional item filter (partial match)
            limit: Max order lines to return
            track_metrics: Whether to track metrics for this run
            
        Returns:
            OrderAvailabilityResult with allocated order lines
        """
        # Business day configuration
        WELDFAB_DAYS = 4
        BLAST_DAYS = 7
        PAINT_DAYS = 10
        
        HOLIDAYS = [
            date(2024, 12, 24), date(2024, 12, 25),
            date(2025, 1, 1), date(2025, 5, 26), date(2025, 7, 3),
            date(2025, 9, 1), date(2025, 11, 27), date(2025, 12, 24), date(2025, 12, 25),
        ]
        
        def is_business_day(check_date: date) -> bool:
            # Mon-Thu only (Friday = 4, Sat = 5, Sun = 6 are off)
            if check_date.weekday() >= 4:
                return False
            if check_date in HOLIDAYS:
                return False
            return True
        
        def add_business_days(start: date, days: int) -> date:
            current = start
            added = 0
            while added < days:
                current = current + timedelta(days=1)
                if is_business_day(current):
                    added += 1
            return current
        
        # Start metrics tracking
        metrics_store = get_metrics_store()
        metrics_run = None
        if track_metrics:
            metrics_run = metrics_store.start_run(
                "order-availability",
                filters={"customer": customer, "item": item, "limit": limit}
            )
        
        try:
            async with MongooseClient(self.config) as client:
                # Fetch all required data in parallel
                data = await client.parallel_fetch([
                    # Open customer orders
                    ("SLCos", ["CoNum", "CustNum", "CustSeq", "OrderDate", "Stat"], "Stat='O'", 1000),
                    # Order line items
                    ("SLCoitems", ["CoNum", "CoLine", "CoRelease", "Item", "QtyOrdered", "QtyShipped", "DueDate", "Price", "Stat"], "Stat='O'", 5000),
                    # Customer addresses
                    ("SLCustaddrs", ["CustNum", "CustSeq", "Name"], None, 5000),
                    # Item details
                    ("SLItems", ["Item", "Description", "DrawingNbr", "DerDrawingNbr"], None, 10000),
                    # Inventory - Main warehouse
                    ("SLItemwhses", ["Item", "Whse", "QtyOnHand", "QtyAllocCo", "QtyWip"], "Whse='Main'", 10000),
                    # Jobs - Type J, Stat F or R
                    ("SLJobs", ["Job", "Suffix", "Item", "QtyReleased", "Stat", "JobDate"], "Type='J'", 5000),
                    # Job routes
                    ("SLJobRoutes", ["Job", "Suffix", "Wc", "QtyReceived", "QtyComplete"], None, 20000),
                ], metrics_run=metrics_run)
            
            logger.info(
                "Order availability data fetched",
                orders=len(data.get("SLCos", [])),
                order_lines=len(data.get("SLCoitems", [])),
            )
            
            # Build customer lookup (with CustSeq)
            customers_lookup = {}
            for c in data.get("SLCustaddrs", []):
                key = f"{clean_str(c.get('CustNum'))}_{clean_str(c.get('CustSeq'))}"
                customers_lookup[key] = clean_str(c.get("Name"))
            
            # Build items lookup
            items_lookup = {
                clean_str(i.get("Item")): {
                    "description": clean_str(i.get("Description")),
                    "drawing": clean_str(
                        i.get("DerDrawingNbr") or i.get("DrawingNbr") or ""
                    ),
                }
                for i in data.get("SLItems", [])
            }
            
            # Build inventory lookup
            inventory_by_item: dict[str, dict] = {}
            for inv in data.get("SLItemwhses", []):
                item_num = clean_str(inv.get("Item"))
                inventory_by_item[item_num] = {
                    "on_hand": parse_float(inv.get("QtyOnHand")),
                    "on_hand_cursor": parse_float(inv.get("QtyOnHand")),
                    "alloc_co": parse_float(inv.get("QtyAllocCo")),
                    "wip": parse_float(inv.get("QtyWip")),
                    "in_paint": 0.0,
                    "in_blast": 0.0,
                    "released_weld_fab": 0.0,
                }
            
            # Calculate WIP at each work center by item
            for route in data.get("SLJobRoutes", []):
                job_num = clean_str(route.get("Job"))
                wc = clean_str(route.get("Wc")).upper()
                qty_received = parse_float(route.get("QtyReceived"))
                qty_complete = parse_float(route.get("QtyComplete"))
                qty_at_wc = max(0, qty_received - qty_complete)
                
                if qty_at_wc <= 0:
                    continue
                
                # Find item for this job
                for job in data.get("SLJobs", []):
                    if clean_str(job.get("Job")) == job_num:
                        item_num = clean_str(job.get("Item"))
                        if item_num not in inventory_by_item:
                            inventory_by_item[item_num] = {
                                "on_hand": 0, "on_hand_cursor": 0, "alloc_co": 0,
                                "wip": 0, "in_paint": 0, "in_blast": 0, "released_weld_fab": 0
                            }
                        if wc == "PAINT":
                            inventory_by_item[item_num]["in_paint"] += qty_at_wc
                        elif wc == "BLAST":
                            inventory_by_item[item_num]["in_blast"] += qty_at_wc
                        break
            
            # Calculate ReleasedWeldFab = WIP - InPaint - InBlast
            for item_num, inv in inventory_by_item.items():
                released_wf = inv["wip"] - inv["in_paint"] - inv["in_blast"]
                inv["released_weld_fab"] = max(0, released_wf)
            
            # Build jobs by item lookup
            jobs_by_item: dict[str, list[dict]] = {}
            for job in data.get("SLJobs", []):
                job_stat = clean_str(job.get("Stat"))
                if job_stat in ("F", "R"):
                    item_num = clean_str(job.get("Item"))
                    if item_num not in jobs_by_item:
                        jobs_by_item[item_num] = []
                    jobs_by_item[item_num].append(job)
            
            # Build order lookup
            orders_lookup = {
                clean_str(o.get("CoNum")): {
                    "cust_num": clean_str(o.get("CustNum")),
                    "cust_seq": clean_str(o.get("CustSeq") or "0"),
                    "order_date": clean_str(o.get("OrderDate")),
                }
                for o in data.get("SLCos", [])
            }
            
            # Build raw order lines (before allocation)
            raw_lines: list[dict] = []
            today = datetime.now().date()
            
            for coitem in data.get("SLCoitems", []):
                co_num = clean_str(coitem.get("CoNum"))
                item_num = clean_str(coitem.get("Item"))
                
                if co_num not in orders_lookup:
                    continue
                
                order = orders_lookup[co_num]
                qty_ordered = parse_float(coitem.get("QtyOrdered"))
                qty_shipped = parse_float(coitem.get("QtyShipped"))
                qty_remaining = qty_ordered - qty_shipped
                
                if qty_remaining <= 0:
                    continue
                
                # Apply filters
                cust_key = f"{order['cust_num']}_{order['cust_seq']}"
                cust_name = customers_lookup.get(cust_key, "")
                
                if customer and customer.lower() not in cust_name.lower():
                    continue
                if item and item.lower() not in item_num.lower():
                    continue
                
                # Get item info
                item_info = items_lookup.get(item_num, {"description": "", "drawing": ""})
                inv = inventory_by_item.get(item_num, {
                    "on_hand": 0, "on_hand_cursor": 0, "alloc_co": 0,
                    "wip": 0, "in_paint": 0, "in_blast": 0, "released_weld_fab": 0
                })
                
                # Parse due date
                due_date_str = clean_str(coitem.get("DueDate") or "")
                due_date = parse_syteline_date(due_date_str)
                
                # Get job info
                item_jobs = jobs_by_item.get(item_num, [])
                job_numbers = "; ".join([clean_str(j.get("Job")) for j in item_jobs])
                qty_released = sum(
                    parse_float(j.get("QtyReleased")) 
                    for j in item_jobs if clean_str(j.get("Stat")) == "R"
                )
                
                # Get released date (most recent)
                released_date = None
                if item_jobs:
                    dates = [parse_syteline_date(clean_str(j.get("JobDate"))) for j in item_jobs]
                    valid_dates = [d for d in dates if d]
                    if valid_dates:
                        released_date = max(valid_dates)
                
                # Calculate completion dates
                weld_fab_date = None
                blast_date = None
                paint_date = None
                if released_date:
                    weld_fab_date = add_business_days(released_date, WELDFAB_DAYS)
                    blast_date = add_business_days(released_date, BLAST_DAYS)
                    paint_date = add_business_days(released_date, PAINT_DAYS)
                
                price = parse_float(coitem.get("Price"))
                line_amount = qty_remaining * price
                
                raw_lines.append({
                    "co_num": co_num,
                    "co_line": int(parse_float(coitem.get("CoLine"))),
                    "co_release": int(parse_float(coitem.get("CoRelease") or 0)),
                    "customer_name": cust_name,
                    "order_date": format_date(order["order_date"]),
                    "due_date": due_date.isoformat() if due_date else None,
                    "released_date": released_date.isoformat() if released_date else None,
                    "weld_fab_completion_date": weld_fab_date.isoformat() if weld_fab_date else None,
                    "blast_completion_date": blast_date.isoformat() if blast_date else None,
                    "paint_assembly_completion_date": paint_date.isoformat() if paint_date else None,
                    "item": item_num,
                    "model": item_info["drawing"] or item_num,
                    "item_description": item_info["description"],
                    "qty_ordered": qty_ordered,
                    "qty_shipped": qty_shipped,
                    "qty_remaining": qty_remaining,
                    "qty_alloc_co": inv["alloc_co"],
                    "qty_wip": inv["wip"],
                    "qty_released": qty_released,
                    "total_in_paint": inv["in_paint"],
                    "total_in_blast": inv["in_blast"],
                    "total_in_released_weld_fab": inv["released_weld_fab"],
                    "jobs": job_numbers,
                    "line_amount": line_amount,
                    "_due_date_sort": due_date.isoformat() if due_date else "9999-99-99",
                })
            
            # Sort by due date, then customer, then item
            raw_lines.sort(key=lambda x: (x["_due_date_sort"], x["customer_name"], x["item"]))
            
            # Apply allocation logic (cursor emulation)
            # Process in due date order, allocating from On Hand → Paint → Blast → WeldFab
            inv_tracking = {item: dict(inv) for item, inv in inventory_by_item.items()}
            
            order_lines: list[OrderAvailabilityLine] = []
            for idx, line in enumerate(raw_lines[:limit]):
                item_num = line["item"]
                qty_remaining = line["qty_remaining"]
                
                inv = inv_tracking.get(item_num, {
                    "on_hand_cursor": 0, "in_paint": 0, "in_blast": 0, "released_weld_fab": 0
                })
                
                remaining_to_allocate = qty_remaining
                qty_remaining_covered = 0.0
                
                # Record current on hand
                current_on_hand = inv.get("on_hand_cursor", 0)
                
                # 1. Allocate from On Hand
                qty_on_hand = 0.0
                if remaining_to_allocate > 0 and inv.get("on_hand_cursor", 0) > 0:
                    allocated = min(remaining_to_allocate, inv["on_hand_cursor"])
                    qty_on_hand = allocated
                    inv["on_hand_cursor"] -= allocated
                    remaining_to_allocate -= allocated
                    qty_remaining_covered += allocated
                
                # 2. Allocate from Paint
                allocated_from_paint = 0.0
                if remaining_to_allocate > 0 and inv.get("in_paint", 0) > 0:
                    allocated = min(remaining_to_allocate, inv["in_paint"])
                    allocated_from_paint = allocated
                    inv["in_paint"] -= allocated
                    remaining_to_allocate -= allocated
                    qty_remaining_covered += allocated
                
                # 3. Allocate from Blast
                allocated_from_blast = 0.0
                if remaining_to_allocate > 0 and inv.get("in_blast", 0) > 0:
                    allocated = min(remaining_to_allocate, inv["in_blast"])
                    allocated_from_blast = allocated
                    inv["in_blast"] -= allocated
                    remaining_to_allocate -= allocated
                    qty_remaining_covered += allocated
                
                # 4. Allocate from Released Weld/Fab
                allocated_from_weld_fab = 0.0
                if remaining_to_allocate > 0 and inv.get("released_weld_fab", 0) > 0:
                    allocated = min(remaining_to_allocate, inv["released_weld_fab"])
                    allocated_from_weld_fab = allocated
                    inv["released_weld_fab"] -= allocated
                    remaining_to_allocate -= allocated
                    qty_remaining_covered += allocated
                
                # Update tracking
                inv_tracking[item_num] = inv
                
                order_lines.append(OrderAvailabilityLine(
                    co_data_id=idx + 1,
                    co_num=line["co_num"],
                    co_line=line["co_line"],
                    co_release=line["co_release"],
                    customer_name=line["customer_name"],
                    order_date=line["order_date"],
                    due_date=line["due_date"],
                    released_date=line["released_date"],
                    weld_fab_completion_date=line["weld_fab_completion_date"],
                    blast_completion_date=line["blast_completion_date"],
                    paint_assembly_completion_date=line["paint_assembly_completion_date"],
                    item=line["item"],
                    model=line["model"],
                    item_description=line["item_description"],
                    qty_ordered=line["qty_ordered"],
                    qty_shipped=line["qty_shipped"],
                    qty_remaining=line["qty_remaining"],
                    qty_remaining_covered=qty_remaining_covered,
                    qty_on_hand=qty_on_hand,
                    current_on_hand=current_on_hand,
                    qty_nf=0,  # Not calculated in this version
                    qty_alloc_co=line["qty_alloc_co"],
                    qty_wip=line["qty_wip"],
                    qty_released=line["qty_released"],
                    total_in_paint=line["total_in_paint"],
                    allocated_from_paint=allocated_from_paint,
                    total_in_blast=line["total_in_blast"],
                    allocated_from_blast=allocated_from_blast,
                    total_in_released_weld_fab=line["total_in_released_weld_fab"],
                    allocated_from_released_weld_fab=allocated_from_weld_fab,
                    jobs=line["jobs"],
                    line_amount=line["line_amount"],
                ))
            
            # Get unique orders
            unique_orders = set(ol.co_num for ol in order_lines)

            # Complete metrics tracking
            if track_metrics and metrics_run:
                metrics_store.complete_run("order-availability", len(order_lines))

            return OrderAvailabilityResult(
                total_orders=len(unique_orders),
                total_lines=len(order_lines),
                order_lines=order_lines,
                fetched_at=datetime.now(timezone.utc),
            )
        except Exception as e:
            # Track error in metrics
            if track_metrics and metrics_run:
                metrics_store.complete_run("order-availability", 0, error=str(e))
            raise
