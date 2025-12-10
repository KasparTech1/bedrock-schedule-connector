"""
MCP Tool Definitions
====================

Defines the tools that AI agents can discover and use.
Each tool maps to a connector with clear parameter descriptions.
"""

from dataclasses import dataclass
from typing import Any


@dataclass
class ToolParameter:
    """Definition of a tool parameter."""
    name: str
    type: str
    required: bool
    description: str
    default: Any = None


@dataclass
class Tool:
    """Definition of an MCP tool."""
    name: str
    description: str
    parameters: list[ToolParameter]


# ─────────────────────────────────────────────────────────────────────────────
# Tool Definitions
# ─────────────────────────────────────────────────────────────────────────────

PRODUCTION_SCHEDULE_TOOL = Tool(
    name="get_production_schedule",
    description="""
Get current production schedule for Bedrock manufacturing operations.

Returns scheduled operations showing what's being manufactured, where,
and progress status.

USE THIS WHEN:
• User asks what's being manufactured/produced
• User asks about production status or progress
• User asks what's scheduled for a work center
• User asks about job completion percentages
• User asks what's running on the shop floor

DON'T USE FOR:
• Sales orders → use get_open_orders
• Customer info → use search_customers
• Inventory levels → use get_inventory_status

Common work centers: WELD-01, WELD-02, PAINT-01, ASSY-01, PACK-01
""",
    parameters=[
        ToolParameter(
            name="work_center",
            type="string",
            required=False,
            description="Work center code (e.g., 'WELD-01'). Omit for all."
        ),
        ToolParameter(
            name="job",
            type="string",
            required=False,
            description="Job number (e.g., 'J-12345'). Omit for all jobs."
        ),
        ToolParameter(
            name="include_completed",
            type="boolean",
            required=False,
            default=False,
            description="Include 100% complete operations. Default: false."
        )
    ]
)

OPEN_ORDERS_TOOL = Tool(
    name="get_open_orders",
    description="""
Get open sales orders that haven't shipped yet.

Returns customer orders with line items, quantities, and due dates.

USE THIS WHEN:
• User asks about open orders or backlog
• User asks what needs to ship
• User asks about a customer's orders
• User asks about orders due soon
• User asks about late/overdue orders
""",
    parameters=[
        ToolParameter(
            name="customer",
            type="string",
            required=False,
            description="Customer name or number. Partial match supported."
        ),
        ToolParameter(
            name="days_out",
            type="integer",
            required=False,
            description="Only orders due within N days. E.g., 7 for this week."
        )
    ]
)

CUSTOMER_SEARCH_TOOL = Tool(
    name="search_customers",
    description="""
Search for customer information.

Returns customer details including contact info and account status.

USE THIS WHEN:
• User asks about a specific customer
• User needs customer contact info
• User asks to find customers by location
• User needs a customer number for another query

NOTE: To see customer orders, first search here, then use
get_open_orders with the customer number.
""",
    parameters=[
        ToolParameter(
            name="query",
            type="string",
            required=True,
            description="Search term: name, number, city, or state."
        ),
        ToolParameter(
            name="active_only",
            type="boolean",
            required=False,
            default=True,
            description="Only active customers. False includes inactive."
        )
    ]
)

INVENTORY_STATUS_TOOL = Tool(
    name="get_inventory_status",
    description="""
Get current inventory levels.

Returns quantity on hand, available, and location info.

USE THIS WHEN:
• User asks about stock levels
• User asks if something is in stock
• User asks about inventory availability
• User asks where items are located

NOTE: For items being manufactured, use get_production_schedule.
""",
    parameters=[
        ToolParameter(
            name="item",
            type="string",
            required=False,
            description="Item number. Omit for all (may be slow)."
        ),
        ToolParameter(
            name="warehouse",
            type="string",
            required=False,
            description="Warehouse code. Omit for all locations."
        ),
        ToolParameter(
            name="low_stock_only",
            type="boolean",
            required=False,
            default=False,
            description="Only items below reorder point."
        )
    ]
)

# All available tools
ALL_TOOLS = [
    PRODUCTION_SCHEDULE_TOOL,
    OPEN_ORDERS_TOOL,
    CUSTOMER_SEARCH_TOOL,
    INVENTORY_STATUS_TOOL,
]


def get_tool_by_name(name: str) -> Tool | None:
    """Get a tool definition by name."""
    for tool in ALL_TOOLS:
        if tool.name == name:
            return tool
    return None


def get_tool_schemas() -> list[dict[str, Any]]:
    """
    Get tool schemas in MCP format.
    
    Returns list of tool definitions suitable for MCP server.
    """
    schemas = []
    
    for tool in ALL_TOOLS:
        # Build properties schema
        properties = {}
        required = []
        
        for param in tool.parameters:
            prop = {
                "type": param.type,
                "description": param.description
            }
            if param.default is not None:
                prop["default"] = param.default
            
            properties[param.name] = prop
            
            if param.required:
                required.append(param.name)
        
        schemas.append({
            "name": tool.name,
            "description": tool.description.strip(),
            "inputSchema": {
                "type": "object",
                "properties": properties,
                "required": required
            }
        })
    
    return schemas
