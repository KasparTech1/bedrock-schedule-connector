"""Compatibility shim for the SyteLine 10 direct client.

The canonical location for SyteLine 10 Cloud adapters is now:
- `kai_erp.adapters.syteline10_cloud`

This package remains for backward compatibility and will be removed after
call sites are migrated.
"""

from kai_erp.adapters.syteline10_cloud.direct_client import SyteLineClient, SyteLineConfig

__all__ = ["SyteLineClient", "SyteLineConfig"]
