"""
Bedrock Scheduler Connector
===========================

Production schedule visibility for Bedrock Truck Beds manufacturing operations.

This is a facade that delegates to specialized services:
- ScheduleService: Production schedule management
- CustomerService: Customer search
- FlowOptimizerService: Flow optimizer data
- OrderAvailabilityService: Order availability and allocation

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

from typing import Any, Optional

from .mongoose_client import MongooseConfig
from .models import (
    Customer,
    CustomerSearchResult,
    FlowOptimizerResult,
    Job,
    OrderAvailabilityLine,
    OrderAvailabilityResult,
    ScheduleOverview,
)
from .services import (
    CustomerService,
    FlowOptimizerService,
    OrderAvailabilityService,
    ScheduleService,
)


class BedrockScheduler:
    """
    Bedrock production schedule connector (Facade).
    
    This class provides a unified interface for all Bedrock scheduler operations.
    It delegates to specialized services for each feature area.
    
    Usage:
        config = MongooseConfig.bedrock_hfa()
        scheduler = BedrockScheduler(config)
        
        # Get schedule overview
        overview = await scheduler.get_schedule_overview()
        
        # Search customers
        customers = await scheduler.search_customers(search_term="Acme")
        
        # Get order availability
        availability = await scheduler.get_order_availability()
    """
    
    def __init__(self, config: Optional[MongooseConfig] = None):
        """
        Initialize scheduler.
        
        Args:
            config: Mongoose configuration. If None, uses bedrock_tbe() default.
        """
        self.config = config or MongooseConfig.bedrock_tbe()
        
        # Initialize services
        self._schedule_service = ScheduleService(self.config)
        self._customer_service = CustomerService(self.config)
        self._flow_optimizer_service = FlowOptimizerService(self.config)
        self._order_availability_service = OrderAvailabilityService(self.config)
    
    # Schedule methods (delegate to ScheduleService)
    async def get_schedule_overview(
        self,
        include_complete: bool = False,
        limit: int = 100
    ) -> ScheduleOverview:
        """Get overview of current production schedule."""
        return await self._schedule_service.get_schedule_overview(
            include_complete=include_complete,
            limit=limit
        )
    
    async def get_jobs_at_work_center(
        self,
        work_center: str,
        include_complete: bool = False,
        limit: int = 50
    ) -> list[Job]:
        """Get jobs with operations at a specific work center."""
        return await self._schedule_service.get_jobs_at_work_center(
            work_center=work_center,
            include_complete=include_complete,
            limit=limit
        )
    
    async def get_job_details(
        self,
        job_number: str,
        suffix: int = 0
    ) -> Optional[Job]:
        """Get detailed information for a specific job."""
        return await self._schedule_service.get_job_details(
            job_number=job_number,
            suffix=suffix
        )
    
    async def get_work_center_queue(
        self,
        work_center: str,
        limit: int = 50
    ) -> list[dict[str, Any]]:
        """Get the queue of operations at a work center."""
        return await self._schedule_service.get_work_center_queue(
            work_center=work_center,
            limit=limit
        )
    
    # Customer methods (delegate to CustomerService)
    async def search_customers(
        self,
        search_term: Optional[str] = None,
        customer_number: Optional[str] = None,
        city: Optional[str] = None,
        state: Optional[str] = None,
        status: Optional[str] = None,
        limit: int = 50
    ) -> CustomerSearchResult:
        """Search for Bedrock customers."""
        return await self._customer_service.search_customers(
            search_term=search_term,
            customer_number=customer_number,
            city=city,
            state=state,
            status=status,
            limit=limit
        )
    
    async def get_customer(self, customer_number: str) -> Optional[Customer]:
        """Get a specific customer by number."""
        return await self._customer_service.get_customer(customer_number)
    
    # Flow optimizer methods (delegate to FlowOptimizerService)
    async def get_open_orders(self, limit: int = 500) -> FlowOptimizerResult:
        """Get open orders with WIP data for Flow Optimizer."""
        return await self._flow_optimizer_service.get_open_orders(limit=limit)
    
    # Order availability methods (delegate to OrderAvailabilityService)
    async def get_order_availability(
        self,
        customer: Optional[str] = None,
        item: Optional[str] = None,
        limit: int = 500,
        track_metrics: bool = True,
    ) -> OrderAvailabilityResult:
        """Get order availability with inventory allocation analysis."""
        return await self._order_availability_service.get_order_availability(
            customer=customer,
            item=item,
            limit=limit,
            track_metrics=track_metrics,
        )
