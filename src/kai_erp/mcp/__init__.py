"""
MCP Layer - AI Interface
========================

Model Context Protocol server that exposes ERP data as AI-discoverable tools.
This is the primary interface for AI agents like Claude.
"""

from kai_erp.mcp.server import KaiErpMcpServer
from kai_erp.mcp.tools import (
    ALL_TOOLS,
    CUSTOMER_SEARCH_TOOL,
    INVENTORY_STATUS_TOOL,
    OPEN_ORDERS_TOOL,
    PRODUCTION_SCHEDULE_TOOL,
    Tool,
    ToolParameter,
    get_tool_by_name,
    get_tool_schemas,
)
from kai_erp.mcp.handlers import dispatch_tool_call

__all__ = [
    # Server
    "KaiErpMcpServer",
    # Tools
    "Tool",
    "ToolParameter",
    "ALL_TOOLS",
    "PRODUCTION_SCHEDULE_TOOL",
    "OPEN_ORDERS_TOOL",
    "CUSTOMER_SEARCH_TOOL",
    "INVENTORY_STATUS_TOOL",
    "get_tool_by_name",
    "get_tool_schemas",
    # Handlers
    "dispatch_tool_call",
]
