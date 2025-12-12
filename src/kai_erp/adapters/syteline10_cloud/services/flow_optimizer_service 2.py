"""Flow optimizer service."""
from datetime import datetime, timezone

import structlog

from ..mongoose_client import MongooseClient, MongooseConfig
from ..models.orders import OpenOrderLine, FlowOptimizerResult
from ..utils import (
    clean_str,
    format_date,
    parse_bed_length,
    parse_bed_type,
    parse_float,
    parse_syteline_date,
)

logger = structlog.get_logger(__name__)


class FlowOptimizerService:
    """Service for flow optimizer data."""
    
    def __init__(self, config: MongooseConfig):
        self.config = config
    
    async def get_open_orders(self, limit: int = 500) -> FlowOptimizerResult:
        """
        Get open orders with WIP data for Flow Optimizer.
        
        Matches the TBE_App OPEN ORDERS V5 query schema:
        - One row per ORDER LINE
        - Item-level WIP data (qty at each work center stage)
        - Customer name, due date, urgency bucket
        - Job numbers and released quantities
        
        Args:
            limit: Max order lines to return
            
        Returns:
            FlowOptimizerResult with open order lines
        """
        async with MongooseClient(self.config) as client:
            # Fetch all required data in parallel
            data = await client.parallel_fetch([
                # Open customer orders (Stat='O')
                ("SLCos", ["CoNum", "CustNum", "OrderDate", "Stat"], "Stat='O'", 1000),
                # Order line items (Stat='O' for open lines)
                # DueDate may also be named Due_Date or PromiseDate in SyteLine
                ("SLCoitems", ["CoNum", "CoLine", "Item", "QtyOrdered", "QtyShipped", "DueDate", "PromiseDate", "Price", "Stat"], "Stat='O'", 5000),
                # Customer names
                ("SLCustomers", ["CustNum", "Name"], None, 5000),
                # Item details - DerDrawingNbr or Drawing_Nbr
                ("SLItems", ["Item", "Description", "DerDrawingNbr", "DrawingNbr"], None, 10000),
                # Jobs - Bedrock uses JT prefix for their jobs, Type='J', Stat in F/R
                # Get all J-type jobs that are open (Firm or Released)
                ("SLJobs", ["Job", "Suffix", "Item", "QtyReleased", "QtyComplete", "Stat", "Type", "JobDate"], "Type='J'", 5000),
                # Job routes for WIP at work centers
                ("SLJobRoutes", ["Job", "Suffix", "Wc", "QtyReceived", "QtyComplete"], None, 20000),
                # On-hand inventory
                ("SLItemwhses", ["Item", "QtyOnHand", "QtyAllocCo", "QtyWip"], None, 10000),
            ])
            
            # Log what we got for debugging
            logger.info(
                "Flow optimizer data fetched",
                orders=len(data.get("SLCos", [])),
                order_lines=len(data.get("SLCoitems", [])),
                customers=len(data.get("SLCustomers", [])),
                items=len(data.get("SLItems", [])),
                jobs=len(data.get("SLJobs", [])),
                routes=len(data.get("SLJobRoutes", [])),
                inventory=len(data.get("SLItemwhses", [])),
            )
            
            # Sample first coitem to see property names
            if data.get("SLCoitems"):
                sample = data["SLCoitems"][0]
                logger.info("Sample CoItem properties", keys=list(sample.keys()))
            
            # Build lookup tables
            customers_lookup = {
                clean_str(c.get("CustNum")): clean_str(c.get("Name"))
                for c in data.get("SLCustomers", [])
            }
            
            items_lookup = {
                clean_str(i.get("Item")): {
                    "description": clean_str(i.get("Description")),
                    "drawing": clean_str(
                        i.get("DerDrawingNbr") or 
                        i.get("DrawingNbr") or 
                        i.get("Drawing_Nbr") or 
                        ""
                    ),
                }
                for i in data.get("SLItems", [])
            }
            
            # Build inventory lookup
            inventory_lookup = {
                clean_str(i.get("Item")): {
                    "on_hand": parse_float(i.get("QtyOnHand")),
                    "alloc_co": parse_float(i.get("QtyAllocCo")),
                    "wip": parse_float(i.get("QtyWip")),
                }
                for i in data.get("SLItemwhses", [])
            }
            
            # Calculate WIP at each work center by item
            # WIP = qty_received - qty_complete at each work center
            wip_by_item: dict[str, dict[str, float]] = {}
            for route in data.get("SLJobRoutes", []):
                # Find the job to get the item
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
                        item = clean_str(job.get("Item"))
                        if item not in wip_by_item:
                            wip_by_item[item] = {"WELD": 0, "AWELD": 0, "BLAST": 0, "PAINT": 0, "ASSY": 0}
                        if wc in wip_by_item[item]:
                            wip_by_item[item][wc] += qty_at_wc
                        break
            
            # Build jobs by item lookup
            # Log sample job to understand structure
            if data.get("SLJobs"):
                sample_job = data["SLJobs"][0]
                logger.info("Sample Job", 
                    job=sample_job.get("Job"),
                    item=sample_job.get("Item"),
                    type=sample_job.get("Type"),
                    stat=sample_job.get("Stat"),
                    keys=list(sample_job.keys())
                )
            
            jobs_by_item: dict[str, list[dict]] = {}
            for job in data.get("SLJobs", []):
                job_num = clean_str(job.get("Job"))
                job_type = clean_str(job.get("Type"))
                job_stat = clean_str(job.get("Stat"))
                
                # Only J-type jobs that are Firm or Released
                # Bedrock job numbers typically start with JT
                if job_type == "J" and job_stat in ("F", "R"):
                    item = clean_str(job.get("Item"))
                    if item not in jobs_by_item:
                        jobs_by_item[item] = []
                    jobs_by_item[item].append(job)
            
            logger.info("Jobs by item", 
                total_jobs=len(data.get("SLJobs", [])),
                items_with_jobs=len(jobs_by_item),
                sample_items=list(jobs_by_item.keys())[:5]
            )
            
            # Build order lookup
            orders_lookup = {
                clean_str(o.get("CoNum")): {
                    "cust_num": clean_str(o.get("CustNum")),
                    "order_date": clean_str(o.get("OrderDate")),
                }
                for o in data.get("SLCos", [])
            }
            
            # Build order lines
            order_lines: list[OpenOrderLine] = []
            items_seen: dict[str, int] = {}  # Track first occurrence of each item
            work_centers_set: set[str] = set()
            
            today = datetime.now().date()
            
            for coitem in data.get("SLCoitems", []):
                co_num = clean_str(coitem.get("CoNum"))
                item = clean_str(coitem.get("Item"))
                
                # Skip if order not found (shouldn't happen)
                if co_num not in orders_lookup:
                    continue
                
                order = orders_lookup[co_num]
                qty_ordered = parse_float(coitem.get("QtyOrdered"))
                qty_shipped = parse_float(coitem.get("QtyShipped"))
                qty_remaining = qty_ordered - qty_shipped
                
                # Skip fully shipped lines
                if qty_remaining <= 0:
                    continue
                
                # Get item info
                item_info = items_lookup.get(item, {"description": "", "drawing": ""})
                
                # Parse due date and calculate urgency
                # Try DueDate first, then PromiseDate as fallback
                due_date_str = clean_str(coitem.get("DueDate") or coitem.get("PromiseDate") or "")
                due_date = None
                days_until_due = 999
                urgency = "LATER"
                
                due_date = parse_syteline_date(due_date_str)
                if due_date:
                    days_until_due = (due_date - today).days
                    if days_until_due < 0:
                        urgency = "OVERDUE"
                    elif days_until_due == 0:
                        urgency = "TODAY"
                    elif days_until_due <= 7:
                        urgency = "THIS_WEEK"
                    elif days_until_due <= 14:
                        urgency = "NEXT_WEEK"
                    else:
                        urgency = "LATER"
                
                # Get WIP data for this item
                wip = wip_by_item.get(item, {"WELD": 0, "AWELD": 0, "BLAST": 0, "PAINT": 0, "ASSY": 0})
                inv = inventory_lookup.get(item, {"on_hand": 0, "alloc_co": 0, "wip": 0})
                
                # Track work centers
                for wc in wip.keys():
                    if wip[wc] > 0:
                        work_centers_set.add(wc)
                
                # Get job info for this item
                item_jobs = jobs_by_item.get(item, [])
                job_numbers = "; ".join([clean_str(j.get("Job")) for j in item_jobs])
                qty_released = sum(parse_float(j.get("QtyReleased")) for j in item_jobs)
                released_date = None
                if item_jobs:
                    dates = [clean_str(j.get("JobDate")) for j in item_jobs if j.get("JobDate")]
                    if dates:
                        # Parse and format the most recent job date
                        parsed_dates = [parse_syteline_date(d) for d in dates]
                        valid_dates = [d for d in parsed_dates if d]
                        if valid_dates:
                            released_date = max(valid_dates).isoformat()
                
                # Parse bed type and length from drawing number or item code
                # Use drawing if available, otherwise fall back to item code
                model = item_info["drawing"] if item_info["drawing"] else item
                bed_type = parse_bed_type(model)
                bed_length = parse_bed_length(model)
                
                # Calculate line value
                price = parse_float(coitem.get("Price"))
                line_value = qty_remaining * price
                
                # Track first for item
                is_first = item not in items_seen
                if is_first:
                    items_seen[item] = 1
                
                # Format order date
                order_date_formatted = format_date(order["order_date"]) if order["order_date"] else None
                
                order_lines.append(OpenOrderLine(
                    order_num=co_num,
                    order_line=int(parse_float(coitem.get("CoLine"))),
                    customer_name=customers_lookup.get(order["cust_num"], ""),
                    order_date=order_date_formatted,
                    due_date=due_date.isoformat() if due_date else None,
                    days_until_due=days_until_due,
                    urgency=urgency,
                    item=item,
                    model=model,  # Use model which falls back to item if no drawing
                    item_description=item_info["description"],
                    bed_type=bed_type,
                    bed_length=bed_length,
                    qty_ordered=qty_ordered,
                    qty_shipped=qty_shipped,
                    qty_remaining=qty_remaining,
                    item_on_hand=inv["on_hand"],
                    item_at_paint=wip.get("PAINT", 0),
                    item_at_blast=wip.get("BLAST", 0),
                    item_at_weld=wip.get("WELD", 0) + wip.get("AWELD", 0),  # Combine weld work centers
                    item_at_assy=wip.get("ASSY", 0),
                    item_total_pipeline=inv["on_hand"] + wip.get("PAINT", 0) + wip.get("BLAST", 0) + wip.get("WELD", 0) + wip.get("AWELD", 0),
                    job_numbers=job_numbers,
                    qty_released=qty_released,
                    released_date=released_date,
                    line_value=line_value,
                    first_for_item=is_first,
                ))
            
            # Sort by due date, then customer, then item
            order_lines.sort(key=lambda x: (x.due_date or "9999-99-99", x.customer_name, x.item))
            
            # Apply limit
            order_lines = order_lines[:limit]
            
            # Get unique order numbers
            unique_orders = set(ol.order_num for ol in order_lines)
            
            return FlowOptimizerResult(
                total_orders=len(unique_orders),
                total_lines=len(order_lines),
                order_lines=order_lines,
                work_centers=sorted(work_centers_set),
                fetched_at=datetime.now(timezone.utc),
            )

