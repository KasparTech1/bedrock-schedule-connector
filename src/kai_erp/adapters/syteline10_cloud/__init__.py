"""
Bedrock Scheduler adapter for SyteLine 10 Cloud.
"""

from .scheduler import BedrockScheduler
from .mongoose_client import MongooseClient, MongooseConfig

# Export models for advanced usage
from .models import (
    JobOperation,
    Job,
    ScheduleOverview,
    Customer,
    CustomerSearchResult,
    OpenOrderLine,
    FlowOptimizerResult,
    OrderAvailabilityLine,
    OrderAvailabilityResult,
)

# Export services for direct usage (optional)
from .services import (
    ScheduleService,
    CustomerService,
    FlowOptimizerService,
    OrderAvailabilityService,
)

__all__ = [
    # Main facade
    "BedrockScheduler",
    # Client
    "MongooseClient",
    "MongooseConfig",
    # Models
    "JobOperation",
    "Job",
    "ScheduleOverview",
    "Customer",
    "CustomerSearchResult",
    "OpenOrderLine",
    "FlowOptimizerResult",
    "OrderAvailabilityLine",
    "OrderAvailabilityResult",
    # Services (for advanced usage)
    "ScheduleService",
    "CustomerService",
    "FlowOptimizerService",
    "OrderAvailabilityService",
]
