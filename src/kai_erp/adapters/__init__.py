"""Upstream adapter boundary.

Adapters encapsulate *how* we talk to upstream systems (SyteLine 10 Cloud, SyteLine 8 on-prem, Global Shop, etc.).
The rest of the system (connectors, API, MCP) should not know low-level auth/protocol details.

Naming convention:
- Current systems: no prefix
- Sunset-bound systems: `legacy_*`
"""

__all__ = []
