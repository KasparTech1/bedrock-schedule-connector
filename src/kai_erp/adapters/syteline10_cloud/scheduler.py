"""
Bedrock Scheduler Connector
===========================

Production schedule visibility for Bedrock Truck Beds manufacturing operations.

Provides real-time visibility into:
- Active jobs and their status
- Operations/routing at work centers
- Production progress (qty complete vs released)
- Item and customer information

Available IDOs:
- SLJobs: Job headers (job, item, qty, status)
- SLJobRoutes: Operations (work center, operation sequence)
- SLItems: Item descriptions
- SLItemwhses: Inventory levels
- SLCustomers: Customer names
- SLCos: Customer orders
- SLCoitems: Order line items

Not yet available (need to request access):
- SLJrtSchs: Schedule dates (start/finish)
- SLWcs: Work center descriptions
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date, datetime, timezone
from typing import Any, Optional

import structlog

from .mongoose_client import MongooseClient, MongooseConfig

logger = structlog.get_logger(__name__)


@dataclass
class JobOperation:
    """A single operation within a job."""
    job: str
    suffix: int
    operation_num: int
    work_center: str
    qty_complete: float
    qty_scrapped: float
    # Future: sched_start, sched_finish when SLJrtSchs available


@dataclass
class Job:
    """A manufacturing job with its operations."""
    job: str
    suffix: int
    item: str
    item_description: str
    qty_released: float
    qty_complete: float
    status: str
    customer_num: Optional[str]
    customer_name: Optional[str]
    operations: list[JobOperation]
    
    @property
    def pct_complete(self) -> float:
        """Calculate percent complete."""
        if self.qty_released <= 0:
            return 0.0
        return round((self.qty_complete / self.qty_released) * 100, 1)
    
    @property
    def is_complete(self) -> bool:
        """Check if job is fully complete."""
        return self.qty_complete >= self.qty_released


@dataclass  
class ScheduleOverview:
    """Overview of production schedule."""
    total_jobs: int
    active_jobs: int
    jobs_by_status: dict[str, int]
    work_centers: list[str]
    jobs: list[Job]
    fetched_at: datetime


@dataclass
class Customer:
    """A Bedrock customer record."""
    cust_num: str
    name: str
    addr1: Optional[str]
    addr2: Optional[str]
    city: Optional[str]
    state: Optional[str]
    zip_code: Optional[str]
    country: Optional[str]
    phone: Optional[str]
    contact: Optional[str]
    email: Optional[str]
    cust_type: Optional[str]
    status: str  # A=Active, I=Inactive


@dataclass
class CustomerSearchResult:
    """Result of a customer search."""
    total_count: int
    customers: list[Customer]
    fetched_at: datetime


@dataclass
class OpenOrderLine:
    """
    A single open order line for Flow Optimizer export.
    
    Schema matches the TBE_App OPEN ORDERS V5 query output.
    One row per ORDER LINE with item-level WIP data.
    """
    # Order identification
    order_num: str
    order_line: int
    customer_name: str
    order_date: Optional[str]
    due_date: Optional[str]
    days_until_due: int
    urgency: str  # OVERDUE, TODAY, THIS_WEEK, NEXT_WEEK, LATER
    
    # Item details
    item: str
    model: Optional[str]  # Drawing number
    item_description: str
    bed_type: str  # Granite, Diamond, Marble, etc.
    bed_length: int  # For position 7 eligibility
    
    # Order quantities
    qty_ordered: float
    qty_shipped: float
    qty_remaining: float
    
    # Item-level WIP data (same for all orders of this item)
    item_on_hand: float
    item_at_paint: float
    item_at_blast: float
    item_at_weld: float
    item_at_assy: float
    item_total_pipeline: float
    
    # Job information
    job_numbers: str
    qty_released: float
    released_date: Optional[str]
    
    # Line value for prioritization
    line_value: float
    
    # Flags
    first_for_item: bool


@dataclass
class FlowOptimizerResult:
    """Result of flow optimizer data fetch."""
    total_orders: int
    total_lines: int
    order_lines: list[OpenOrderLine]
    work_centers: list[str]
    fetched_at: datetime


@dataclass
class OrderAvailabilityLine:
    """
    A customer order line with availability and allocation information.
    
    Emulates the TBE_Customer_Order_Availability_Add_Release_Date stored procedure output.
    Shows how inventory is allocated from different production stages.
    """
    # Order identification
    co_data_id: int
    co_num: str
    co_line: int
    co_release: int
    
    # Customer information
    customer_name: str
    
    # Dates
    order_date: Optional[str]
    due_date: Optional[str]
    released_date: Optional[str]
    
    # Estimated completion dates
    weld_fab_completion_date: Optional[str]
    blast_completion_date: Optional[str]
    paint_assembly_completion_date: Optional[str]
    
    # Item information
    item: str
    model: Optional[str]
    item_description: str
    
    # Quantities
    qty_ordered: float
    qty_shipped: float
    qty_remaining: float
    qty_remaining_covered: float
    
    # Inventory quantities
    qty_on_hand: float
    current_on_hand: float
    qty_nf: float
    qty_alloc_co: float
    qty_wip: float
    qty_released: float
    
    # Production stage totals and allocations
    total_in_paint: float
    allocated_from_paint: float
    total_in_blast: float
    allocated_from_blast: float
    total_in_released_weld_fab: float
    allocated_from_released_weld_fab: float
    
    # Related jobs
    jobs: str
    
    # Financial
    line_amount: float


@dataclass
class OrderAvailabilityResult:
    """Result of order availability fetch."""
    total_orders: int
    total_lines: int
    order_lines: list[OrderAvailabilityLine]
    fetched_at: datetime


class BedrockScheduler:
    """
    Bedrock production schedule connector.
    
    Fetches job and operation data from SyteLine via Mongoose REST API,
    combines it into a unified view of the production schedule.
    
    Usage:
        config = MongooseConfig.bedrock_hfa()
        scheduler = BedrockScheduler(config)
        
        # Get schedule overview
        overview = await scheduler.get_schedule_overview()
        
        # Get jobs at specific work center
        jobs = await scheduler.get_jobs_at_work_center("HF-CUT")
        
        # Get single job details
        job = await scheduler.get_job_details("123")
    """
    
    def __init__(self, config: Optional[MongooseConfig] = None):
        """
        Initialize scheduler.
        
        Args:
            config: Mongoose configuration. If None, uses bedrock_tbe() default (Bedrock Truck Beds).
        """
        self.config = config or MongooseConfig.bedrock_tbe()
    
    async def get_schedule_overview(
        self,
        include_complete: bool = False,
        limit: int = 100
    ) -> ScheduleOverview:
        """
        Get overview of current production schedule.
        
        Args:
            include_complete: Include completed jobs
            limit: Max jobs to return
            
        Returns:
            ScheduleOverview with jobs and statistics
        """
        async with MongooseClient(self.config) as client:
            # Determine job filter
            job_filter = None if include_complete else "Stat='R'"
            
            # Fetch all data in parallel
            data = await client.parallel_fetch([
                ("SLJobs", ["Job", "Suffix", "Item", "QtyReleased", "QtyComplete", "Stat", "CustNum"], job_filter, limit),
                ("SLJobRoutes", ["Job", "Suffix", "OperNum", "Wc", "QtyComplete", "QtyScrapped"], None, limit * 10),
                ("SLItems", ["Item", "Description"], None, 5000),
                ("SLCustomers", ["CustNum", "Name"], None, 5000),
            ])
            
            # Build lookup tables
            items_lookup = {
                self._clean_str(i.get("Item")): i.get("Description", "")
                for i in data.get("SLItems", [])
            }
            
            customers_lookup = {
                self._clean_str(c.get("CustNum")): c.get("Name", "")
                for c in data.get("SLCustomers", [])
            }
            
            # Group operations by job
            ops_by_job: dict[str, list[dict]] = {}
            for op in data.get("SLJobRoutes", []):
                job_key = f"{self._clean_str(op.get('Job'))}_{op.get('Suffix', '0')}"
                if job_key not in ops_by_job:
                    ops_by_job[job_key] = []
                ops_by_job[job_key].append(op)
            
            # Build job objects
            jobs = []
            jobs_by_status: dict[str, int] = {}
            work_centers_set: set[str] = set()
            
            for job_data in data.get("SLJobs", []):
                job_num = self._clean_str(job_data.get("Job"))
                suffix = int(job_data.get("Suffix", 0) or 0)
                job_key = f"{job_num}_{suffix}"
                
                item = self._clean_str(job_data.get("Item"))
                cust_num = self._clean_str(job_data.get("CustNum"))
                status = self._clean_str(job_data.get("Stat"))
                
                # Build operations
                operations = []
                for op_data in ops_by_job.get(job_key, []):
                    wc = self._clean_str(op_data.get("Wc"))
                    work_centers_set.add(wc)
                    
                    operations.append(JobOperation(
                        job=job_num,
                        suffix=suffix,
                        operation_num=int(op_data.get("OperNum", 0) or 0),
                        work_center=wc,
                        qty_complete=self._parse_float(op_data.get("QtyComplete")),
                        qty_scrapped=self._parse_float(op_data.get("QtyScrapped")),
                    ))
                
                # Sort operations by operation number
                operations.sort(key=lambda x: x.operation_num)
                
                job = Job(
                    job=job_num,
                    suffix=suffix,
                    item=item,
                    item_description=items_lookup.get(item, ""),
                    qty_released=self._parse_float(job_data.get("QtyReleased")),
                    qty_complete=self._parse_float(job_data.get("QtyComplete")),
                    status=status,
                    customer_num=cust_num if cust_num else None,
                    customer_name=customers_lookup.get(cust_num) if cust_num else None,
                    operations=operations,
                )
                
                jobs.append(job)
                
                # Track status counts
                jobs_by_status[status] = jobs_by_status.get(status, 0) + 1
            
            # Sort jobs by job number
            jobs.sort(key=lambda x: (x.job, x.suffix))
            
            return ScheduleOverview(
                total_jobs=len(jobs),
                active_jobs=sum(1 for j in jobs if not j.is_complete),
                jobs_by_status=jobs_by_status,
                work_centers=sorted(work_centers_set),
                jobs=jobs,
                fetched_at=datetime.now(timezone.utc),
            )
    
    async def get_jobs_at_work_center(
        self,
        work_center: str,
        include_complete: bool = False,
        limit: int = 50
    ) -> list[Job]:
        """
        Get jobs with operations at a specific work center.
        
        Args:
            work_center: Work center code (e.g., "HF-CUT")
            include_complete: Include completed jobs
            limit: Max jobs to return
            
        Returns:
            List of jobs with operations at the work center
        """
        overview = await self.get_schedule_overview(
            include_complete=include_complete,
            limit=limit * 2  # Fetch more since we'll filter
        )
        
        # Filter to jobs with operations at this work center
        filtered_jobs = [
            job for job in overview.jobs
            if any(op.work_center == work_center for op in job.operations)
        ]
        
        return filtered_jobs[:limit]
    
    async def get_job_details(self, job_number: str, suffix: int = 0) -> Optional[Job]:
        """
        Get detailed information for a specific job.
        
        Args:
            job_number: Job number
            suffix: Job suffix (default 0)
            
        Returns:
            Job details or None if not found
        """
        async with MongooseClient(self.config) as client:
            # Pad job number if needed (SyteLine uses right-padded strings)
            job_filter = f"Job='{job_number}' AND Suffix={suffix}"
            
            # Fetch job and its operations
            data = await client.parallel_fetch([
                ("SLJobs", ["Job", "Suffix", "Item", "QtyReleased", "QtyComplete", "Stat", "CustNum"], job_filter, 1),
                ("SLJobRoutes", ["Job", "Suffix", "OperNum", "Wc", "QtyComplete", "QtyScrapped"], f"Job='{job_number}'", 100),
            ])
            
            jobs = data.get("SLJobs", [])
            if not jobs:
                return None
            
            job_data = jobs[0]
            job_num = self._clean_str(job_data.get("Job"))
            item = self._clean_str(job_data.get("Item"))
            cust_num = self._clean_str(job_data.get("CustNum"))
            
            # Get item description
            items = await client.query_ido("SLItems", ["Item", "Description"], f"Item='{item}'", 1)
            item_desc = items[0].get("Description", "") if items else ""
            
            # Get customer name if applicable
            cust_name = None
            if cust_num:
                customers = await client.query_ido("SLCustomers", ["CustNum", "Name"], f"CustNum='{cust_num}'", 1)
                cust_name = customers[0].get("Name", "") if customers else None
            
            # Build operations
            operations = []
            for op_data in data.get("SLJobRoutes", []):
                operations.append(JobOperation(
                    job=job_num,
                    suffix=suffix,
                    operation_num=int(op_data.get("OperNum", 0) or 0),
                    work_center=self._clean_str(op_data.get("Wc")),
                    qty_complete=self._parse_float(op_data.get("QtyComplete")),
                    qty_scrapped=self._parse_float(op_data.get("QtyScrapped")),
                ))
            
            operations.sort(key=lambda x: x.operation_num)
            
            return Job(
                job=job_num,
                suffix=suffix,
                item=item,
                item_description=item_desc,
                qty_released=self._parse_float(job_data.get("QtyReleased")),
                qty_complete=self._parse_float(job_data.get("QtyComplete")),
                status=self._clean_str(job_data.get("Stat")),
                customer_num=cust_num if cust_num else None,
                customer_name=cust_name,
                operations=operations,
            )
    
    async def get_work_center_queue(self, work_center: str, limit: int = 50) -> list[dict[str, Any]]:
        """
        Get the queue of operations at a work center.
        
        Args:
            work_center: Work center code
            limit: Max operations to return
            
        Returns:
            List of operations with job details
        """
        async with MongooseClient(self.config) as client:
            # Fetch operations at this work center
            ops = await client.query_ido(
                "SLJobRoutes",
                ["Job", "Suffix", "OperNum", "Wc", "QtyComplete", "QtyScrapped"],
                f"Wc='{work_center}'",
                limit
            )
            
            if not ops:
                return []
            
            # Get unique jobs
            job_nums = list(set(self._clean_str(op.get("Job")) for op in ops))
            
            # Fetch job details (limited batch)
            jobs = await client.query_ido(
                "SLJobs",
                ["Job", "Suffix", "Item", "QtyReleased", "QtyComplete", "Stat"],
                None,  # Would need IN clause - fetch all for now
                1000
            )
            
            # Build job lookup
            jobs_lookup = {
                self._clean_str(j.get("Job")): j
                for j in jobs
            }
            
            # Build queue with job info
            queue = []
            for op in ops:
                job_num = self._clean_str(op.get("Job"))
                job_data = jobs_lookup.get(job_num, {})
                
                queue.append({
                    "job": job_num,
                    "suffix": int(op.get("Suffix", 0) or 0),
                    "operation_num": int(op.get("OperNum", 0) or 0),
                    "work_center": self._clean_str(op.get("Wc")),
                    "item": self._clean_str(job_data.get("Item")),
                    "qty_released": self._parse_float(job_data.get("QtyReleased")),
                    "qty_complete": self._parse_float(op.get("QtyComplete")),
                    "job_status": self._clean_str(job_data.get("Stat")),
                })
            
            # Sort by job number and operation
            queue.sort(key=lambda x: (x["job"], x["operation_num"]))
            
            return queue
    
    # =========================================================================
    # CUSTOMER SEARCH METHODS
    # =========================================================================
    
    async def search_customers(
        self,
        search_term: Optional[str] = None,
        customer_number: Optional[str] = None,
        city: Optional[str] = None,
        state: Optional[str] = None,
        status: Optional[str] = None,
        limit: int = 50
    ) -> CustomerSearchResult:
        """
        Search for Bedrock customers.
        
        Args:
            search_term: Search in name or customer number
            customer_number: Exact customer number match
            city: Filter by city
            state: Filter by state
            status: Filter by status (A=Active, I=Inactive)
            limit: Max customers to return
            
        Returns:
            CustomerSearchResult with matching customers
        """
        async with MongooseClient(self.config) as client:
            # Build filter
            filters = []
            
            if customer_number:
                filters.append(f"CustNum='{customer_number}'")
            
            if city:
                filters.append(f"City LIKE '%{city}%'")
            
            if state:
                filters.append(f"State='{state}'")
            
            if status:
                filters.append(f"Stat='{status}'")
            
            filter_str = " AND ".join(filters) if filters else None
            
            # Fetch customers
            # Note: Using SyteLine standard property names
            raw_customers = await client.query_ido(
                "SLCustomers",
                [
                    "CustNum", "Name", "Addr_1", "Addr_2", "City", "State",
                    "Zip", "Country", "TelexNum", "Contact_1", "CreditHold", "CustType", "Stat"
                ],
                filter_str,
                limit * 2  # Fetch extra for client-side search filter
            )
            
            # Build customer objects
            customers = []
            for cust_data in raw_customers:
                cust_num = self._clean_str(cust_data.get("CustNum"))
                name = self._clean_str(cust_data.get("Name"))
                
                # Apply search_term filter (client-side since LIKE may not work well)
                if search_term:
                    search_lower = search_term.lower()
                    if (search_lower not in cust_num.lower() and 
                        search_lower not in name.lower()):
                        continue
                
                customers.append(Customer(
                    cust_num=cust_num,
                    name=name,
                    addr1=self._clean_str(cust_data.get("Addr_1")) or None,
                    addr2=self._clean_str(cust_data.get("Addr_2")) or None,
                    city=self._clean_str(cust_data.get("City")) or None,
                    state=self._clean_str(cust_data.get("State")) or None,
                    zip_code=self._clean_str(cust_data.get("Zip")) or None,
                    country=self._clean_str(cust_data.get("Country")) or None,
                    phone=self._clean_str(cust_data.get("TelexNum")) or None,  # Phone field
                    contact=self._clean_str(cust_data.get("Contact_1")) or None,
                    email=None,  # Email may need different property
                    cust_type=self._clean_str(cust_data.get("CustType")) or None,
                    status=self._clean_str(cust_data.get("Stat")) or "A",
                ))
            
            # Apply limit
            customers = customers[:limit]
            
            return CustomerSearchResult(
                total_count=len(customers),
                customers=customers,
                fetched_at=datetime.now(timezone.utc),
            )
    
    async def get_customer(self, customer_number: str) -> Optional[Customer]:
        """
        Get a specific customer by number.
        
        Args:
            customer_number: The customer number
            
        Returns:
            Customer if found, None otherwise
        """
        result = await self.search_customers(customer_number=customer_number, limit=1)
        return result.customers[0] if result.customers else None
    
    # =========================================================================
    # FLOW OPTIMIZER METHODS
    # =========================================================================
    
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
                self._clean_str(c.get("CustNum")): self._clean_str(c.get("Name"))
                for c in data.get("SLCustomers", [])
            }
            
            items_lookup = {
                self._clean_str(i.get("Item")): {
                    "description": self._clean_str(i.get("Description")),
                    "drawing": self._clean_str(
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
                self._clean_str(i.get("Item")): {
                    "on_hand": self._parse_float(i.get("QtyOnHand")),
                    "alloc_co": self._parse_float(i.get("QtyAllocCo")),
                    "wip": self._parse_float(i.get("QtyWip")),
                }
                for i in data.get("SLItemwhses", [])
            }
            
            # Calculate WIP at each work center by item
            # WIP = qty_received - qty_complete at each work center
            wip_by_item: dict[str, dict[str, float]] = {}
            for route in data.get("SLJobRoutes", []):
                # Find the job to get the item
                job_num = self._clean_str(route.get("Job"))
                wc = self._clean_str(route.get("Wc")).upper()
                qty_received = self._parse_float(route.get("QtyReceived"))
                qty_complete = self._parse_float(route.get("QtyComplete"))
                qty_at_wc = max(0, qty_received - qty_complete)
                
                if qty_at_wc <= 0:
                    continue
                
                # Find item for this job
                for job in data.get("SLJobs", []):
                    if self._clean_str(job.get("Job")) == job_num:
                        item = self._clean_str(job.get("Item"))
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
                job_num = self._clean_str(job.get("Job"))
                job_type = self._clean_str(job.get("Type"))
                job_stat = self._clean_str(job.get("Stat"))
                
                # Only J-type jobs that are Firm or Released
                # Bedrock job numbers typically start with JT
                if job_type == "J" and job_stat in ("F", "R"):
                    item = self._clean_str(job.get("Item"))
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
                self._clean_str(o.get("CoNum")): {
                    "cust_num": self._clean_str(o.get("CustNum")),
                    "order_date": self._clean_str(o.get("OrderDate")),
                }
                for o in data.get("SLCos", [])
            }
            
            # Build order lines
            order_lines: list[OpenOrderLine] = []
            items_seen: dict[str, int] = {}  # Track first occurrence of each item
            work_centers_set: set[str] = set()
            
            today = datetime.now().date()
            
            for coitem in data.get("SLCoitems", []):
                co_num = self._clean_str(coitem.get("CoNum"))
                item = self._clean_str(coitem.get("Item"))
                
                # Skip if order not found (shouldn't happen)
                if co_num not in orders_lookup:
                    continue
                
                order = orders_lookup[co_num]
                qty_ordered = self._parse_float(coitem.get("QtyOrdered"))
                qty_shipped = self._parse_float(coitem.get("QtyShipped"))
                qty_remaining = qty_ordered - qty_shipped
                
                # Skip fully shipped lines
                if qty_remaining <= 0:
                    continue
                
                # Get item info
                item_info = items_lookup.get(item, {"description": "", "drawing": ""})
                
                # Parse due date and calculate urgency
                # Try DueDate first, then PromiseDate as fallback
                due_date_str = self._clean_str(coitem.get("DueDate") or coitem.get("PromiseDate") or "")
                due_date = None
                days_until_due = 999
                urgency = "LATER"
                
                due_date = self._parse_syteline_date(due_date_str)
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
                job_numbers = "; ".join([self._clean_str(j.get("Job")) for j in item_jobs])
                qty_released = sum(self._parse_float(j.get("QtyReleased")) for j in item_jobs)
                released_date = None
                if item_jobs:
                    dates = [self._clean_str(j.get("JobDate")) for j in item_jobs if j.get("JobDate")]
                    if dates:
                        # Parse and format the most recent job date
                        parsed_dates = [self._parse_syteline_date(d) for d in dates]
                        valid_dates = [d for d in parsed_dates if d]
                        if valid_dates:
                            released_date = max(valid_dates).isoformat()
                
                # Parse bed type and length from drawing number or item code
                # Use drawing if available, otherwise fall back to item code
                model = item_info["drawing"] if item_info["drawing"] else item
                bed_type = self._parse_bed_type(model)
                bed_length = self._parse_bed_length(model)
                
                # Calculate line value
                price = self._parse_float(coitem.get("Price"))
                line_value = qty_remaining * price
                
                # Track first for item
                is_first = item not in items_seen
                if is_first:
                    items_seen[item] = 1
                
                # Format order date
                order_date_formatted = self._format_date(order["order_date"]) if order["order_date"] else None
                
                order_lines.append(OpenOrderLine(
                    order_num=co_num,
                    order_line=int(self._parse_float(coitem.get("CoLine"))),
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
    
    # =========================================================================
    # ORDER AVAILABILITY METHODS
    # =========================================================================
    
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
            
        Returns:
            OrderAvailabilityResult with allocated order lines
        """
        from datetime import timedelta
        from kai_erp.core.metrics import get_metrics_store
        
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
                key = f"{self._clean_str(c.get('CustNum'))}_{self._clean_str(c.get('CustSeq'))}"
                customers_lookup[key] = self._clean_str(c.get("Name"))
            
            # Build items lookup
            items_lookup = {
                self._clean_str(i.get("Item")): {
                    "description": self._clean_str(i.get("Description")),
                    "drawing": self._clean_str(
                        i.get("DerDrawingNbr") or i.get("DrawingNbr") or ""
                    ),
                }
                for i in data.get("SLItems", [])
            }
            
            # Build inventory lookup
            inventory_by_item: dict[str, dict] = {}
            for inv in data.get("SLItemwhses", []):
                item_num = self._clean_str(inv.get("Item"))
                inventory_by_item[item_num] = {
                    "on_hand": self._parse_float(inv.get("QtyOnHand")),
                    "on_hand_cursor": self._parse_float(inv.get("QtyOnHand")),
                    "alloc_co": self._parse_float(inv.get("QtyAllocCo")),
                    "wip": self._parse_float(inv.get("QtyWip")),
                    "in_paint": 0.0,
                    "in_blast": 0.0,
                    "released_weld_fab": 0.0,
                }
            
            # Calculate WIP at each work center by item
            for route in data.get("SLJobRoutes", []):
                job_num = self._clean_str(route.get("Job"))
                wc = self._clean_str(route.get("Wc")).upper()
                qty_received = self._parse_float(route.get("QtyReceived"))
                qty_complete = self._parse_float(route.get("QtyComplete"))
                qty_at_wc = max(0, qty_received - qty_complete)
                
                if qty_at_wc <= 0:
                    continue
                
                # Find item for this job
                for job in data.get("SLJobs", []):
                    if self._clean_str(job.get("Job")) == job_num:
                        item_num = self._clean_str(job.get("Item"))
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
                job_stat = self._clean_str(job.get("Stat"))
                if job_stat in ("F", "R"):
                    item_num = self._clean_str(job.get("Item"))
                    if item_num not in jobs_by_item:
                        jobs_by_item[item_num] = []
                    jobs_by_item[item_num].append(job)
            
            # Build order lookup
            orders_lookup = {
                self._clean_str(o.get("CoNum")): {
                    "cust_num": self._clean_str(o.get("CustNum")),
                    "cust_seq": self._clean_str(o.get("CustSeq") or "0"),
                    "order_date": self._clean_str(o.get("OrderDate")),
                }
                for o in data.get("SLCos", [])
            }
            
            # Build raw order lines (before allocation)
            raw_lines: list[dict] = []
            today = datetime.now().date()
            
            for coitem in data.get("SLCoitems", []):
                co_num = self._clean_str(coitem.get("CoNum"))
                item_num = self._clean_str(coitem.get("Item"))
                
                if co_num not in orders_lookup:
                    continue
                
                order = orders_lookup[co_num]
                qty_ordered = self._parse_float(coitem.get("QtyOrdered"))
                qty_shipped = self._parse_float(coitem.get("QtyShipped"))
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
                due_date_str = self._clean_str(coitem.get("DueDate") or "")
                due_date = self._parse_syteline_date(due_date_str)
                
                # Get job info
                item_jobs = jobs_by_item.get(item_num, [])
                job_numbers = "; ".join([self._clean_str(j.get("Job")) for j in item_jobs])
                qty_released = sum(
                    self._parse_float(j.get("QtyReleased")) 
                    for j in item_jobs if self._clean_str(j.get("Stat")) == "R"
                )
                
                # Get released date (most recent)
                released_date = None
                if item_jobs:
                    dates = [self._parse_syteline_date(self._clean_str(j.get("JobDate"))) for j in item_jobs]
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
                
                price = self._parse_float(coitem.get("Price"))
                line_amount = qty_remaining * price
                
                raw_lines.append({
                    "co_num": co_num,
                    "co_line": int(self._parse_float(coitem.get("CoLine"))),
                    "co_release": int(self._parse_float(coitem.get("CoRelease") or 0)),
                    "customer_name": cust_name,
                    "order_date": self._format_date(order["order_date"]),
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

    def _parse_bed_type(self, model: str) -> str:
        """
        Parse bed type from model/drawing number or item code.
        
        Examples:
        - "14G-7" -> Granite (ends with G before dash)
        - "23D" -> Diamond (ends with D)
        - "14GP-7" or "6GP" -> Granite+ (contains GP)
        - "8M-9" -> Marble (ends with M before dash)
        - "14D-7" -> Diamond
        """
        if not model:
            return "Other"
        
        model_upper = model.upper().strip()
        
        # Check for Granite+ first (GP patterns - must check before G)
        if "GP" in model_upper:
            return "Granite+"
        
        # Get the prefix before first dash (e.g., "14G" from "14G-7")
        prefix = model_upper.split("-")[0] if "-" in model_upper else model_upper
        
        # Remove any trailing numbers from prefix for items like "23D"
        # But keep the letter suffix
        stripped_prefix = prefix.rstrip("0123456789")
        if not stripped_prefix:
            stripped_prefix = prefix
        
        # Check last character of prefix
        last_char = stripped_prefix[-1] if stripped_prefix else ""
        
        if last_char == "D":
            return "Diamond"
        elif last_char == "G":
            return "Granite"
        elif last_char == "M":
            return "Marble"
        elif last_char == "L":
            return "Limestone"
        elif last_char == "P":
            return "Platform"
        elif last_char == "O":
            return "Onyx"
        elif last_char == "S":
            return "Slate"
        elif "QU" in model_upper or (prefix.startswith("Q") and len(prefix) > 1):
            return "Quad"
        
        return "Other"
    
    def _parse_syteline_date(self, date_str: str) -> datetime.date | None:
        """
        Parse SyteLine date format.
        
        SyteLine dates can be in various formats:
        - "20251022 0" (YYYYMMDD with suffix)
        - "2025-10-22"
        - "2025-10-22T00:00:00"
        - "10/22/2025"
        """
        if not date_str:
            return None
        
        date_str = date_str.strip()
        
        # Handle "YYYYMMDD 0" format (SyteLine standard)
        if " " in date_str and len(date_str.split()[0]) == 8:
            try:
                return datetime.strptime(date_str.split()[0], "%Y%m%d").date()
            except ValueError:
                pass
        
        # Try various formats
        for fmt in ["%Y%m%d", "%Y-%m-%d", "%Y-%m-%dT%H:%M:%S", "%m/%d/%Y"]:
            try:
                return datetime.strptime(date_str[:10], fmt).date()
            except ValueError:
                continue
        
        return None
    
    def _format_date(self, date_str: str) -> str | None:
        """Format a SyteLine date string to ISO format."""
        parsed = self._parse_syteline_date(date_str)
        return parsed.isoformat() if parsed else None
    
    def _parse_bed_length(self, drawing: str) -> int:
        """Parse bed length from drawing number (first 1-2 digits)."""
        if not drawing:
            return 0
        
        # Try to extract leading digits
        digits = ""
        for char in drawing:
            if char.isdigit():
                digits += char
            else:
                break
        
        if digits and len(digits) <= 2:
            try:
                return int(digits)
            except ValueError:
                pass
        
        return 0
    
    # =========================================================================
    # UTILITY METHODS
    # =========================================================================
    
    def _clean_str(self, value: Any) -> str:
        """Clean string value - strip whitespace."""
        if value is None:
            return ""
        return str(value).strip()
    
    def _parse_float(self, value: Any) -> float:
        """Parse float value safely."""
        if value is None:
            return 0.0
        try:
            return float(value)
        except (ValueError, TypeError):
            return 0.0
