"""Compatibility shim for SyteLine 10 (Mongoose/ION) client.

The canonical location for SyteLine 10 Cloud adapters is now:
- `kai_erp.adapters.syteline10_cloud`

This module remains for backward compatibility and will be removed after
call sites are migrated.
"""

from kai_erp.adapters.syteline10_cloud.mongoose_client import MongooseClient, MongooseConfig
from kai_erp.adapters.syteline10_cloud.scheduler import BedrockScheduler

__all__ = ["MongooseClient", "MongooseConfig", "BedrockScheduler"]

