"""
Demo MCP Server
===============

MCP Server connected to the Kaspar Development Workshop demo environment.
Uses the live SyteLine 10 connection for real data.
"""

import asyncio
import json
import sys
from typing import Any

import structlog

from kai_erp.syteline import SyteLineClient, SyteLineConfig

logger = structlog.get_logger(__name__)

# Demo connection config
DEMO_CONFIG = SyteLineConfig(
    base_url="https://Csi10g.erpsl.inforcloudsuite.com",
    config_name="DUU6QAFE74D2YDYW_TST_DALS",
    username="DevWorkshop06",
    password="WeTest$Code1",
)

# Tool definitions
DEMO_TOOLS = [
    {
        "name": "get_syteline_items",
        "description": """
Query items from the live SyteLine 10 demo environment.

Returns item master data including:
- Item number and description
- Product code category
- Unit of measure
- Status (Active/Inactive)
- Custom color codes

USE THIS WHEN:
• User asks about items or products
• User needs item descriptions
• User asks about product codes
• User wants to search for items

EXAMPLE QUERIES:
• "What items do we have?" → call with no filters
• "Show me items starting with 30" → item="30"
• "What's in product code FG-100?" → product_code="FG-100"
""".strip(),
        "inputSchema": {
            "type": "object",
            "properties": {
                "item": {
                    "type": "string",
                    "description": "Filter by item number (partial match). Omit for all items."
                },
                "product_code": {
                    "type": "string",
                    "description": "Filter by exact product code (e.g., 'FG-100')."
                },
                "limit": {
                    "type": "integer",
                    "description": "Maximum records to return. Default: 10, Max: 100.",
                    "default": 10
                }
            },
            "required": []
        }
    },
    {
        "name": "get_syteline_customers",
        "description": """
Query customers from the live SyteLine 10 demo environment.

Returns customer master data including:
- Customer number and name
- Contact information
- Address details

USE THIS WHEN:
• User asks about customers
• User needs customer contact info
• User wants to look up a customer
""".strip(),
        "inputSchema": {
            "type": "object",
            "properties": {
                "customer": {
                    "type": "string",
                    "description": "Filter by customer name or number (partial match)."
                },
                "limit": {
                    "type": "integer",
                    "description": "Maximum records to return. Default: 10.",
                    "default": 10
                }
            },
            "required": []
        }
    },
    {
        "name": "query_syteline_ido",
        "description": """
Query any SyteLine IDO (Intelligent Data Object) directly.

This is an advanced tool for querying any IDO with custom properties.

COMMON IDOs:
• SLItems - Item master
• SLCustomers - Customer master  
• SLCos - Customer orders
• SLJobs - Production jobs
• SLItemLocs - Inventory by location

USE THIS WHEN:
• User needs data not covered by other tools
• User asks about specific SyteLine objects
• Advanced queries with custom filters
""".strip(),
        "inputSchema": {
            "type": "object",
            "properties": {
                "ido_name": {
                    "type": "string",
                    "description": "Name of the IDO to query (e.g., 'SLItems', 'SLCustomers')."
                },
                "properties": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "List of property names to return."
                },
                "filter": {
                    "type": "string",
                    "description": "Filter expression (e.g., \"Status = 'A'\")."
                },
                "limit": {
                    "type": "integer",
                    "description": "Maximum records to return. Default: 10.",
                    "default": 10
                }
            },
            "required": ["ido_name"]
        }
    }
]


class DemoMcpServer:
    """
    Demo MCP Server for KAI ERP Connector.
    
    Connects to Kaspar Development Workshop SyteLine 10 environment.
    """
    
    SERVER_NAME = "kai-erp-demo"
    SERVER_VERSION = "1.0.0"
    
    def __init__(self):
        """Initialize demo MCP server."""
        self._client: SyteLineClient | None = None
    
    async def __aenter__(self) -> "DemoMcpServer":
        """Async context manager entry."""
        self._client = SyteLineClient(DEMO_CONFIG)
        await self._client.__aenter__()
        logger.info("Demo MCP server initialized", base_url=DEMO_CONFIG.base_url)
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb) -> None:
        """Async context manager exit."""
        if self._client:
            await self._client.__aexit__(exc_type, exc_val, exc_tb)
        logger.info("Demo MCP server shutdown")
    
    def get_server_info(self) -> dict[str, Any]:
        """Get server information for MCP handshake."""
        return {
            "name": self.SERVER_NAME,
            "version": self.SERVER_VERSION,
            "capabilities": {
                "tools": True,
                "resources": False,
                "prompts": False
            }
        }
    
    def get_tools(self) -> list[dict[str, Any]]:
        """Get list of available tools."""
        return DEMO_TOOLS
    
    async def call_tool(
        self,
        tool_name: str,
        arguments: dict[str, Any]
    ) -> dict[str, Any]:
        """
        Call a tool with given arguments.
        
        Args:
            tool_name: Name of tool to call
            arguments: Tool arguments
        
        Returns:
            Tool result
        """
        if not self._client:
            return {
                "success": False,
                "error": {"message": "Server not initialized"}
            }
        
        logger.info("Tool call", tool=tool_name, arguments=arguments)
        
        try:
            if tool_name == "get_syteline_items":
                result = await self._handle_get_items(arguments)
            elif tool_name == "get_syteline_customers":
                result = await self._handle_get_customers(arguments)
            elif tool_name == "query_syteline_ido":
                result = await self._handle_query_ido(arguments)
            else:
                result = {
                    "success": False,
                    "error": {"message": f"Unknown tool: {tool_name}"}
                }
        except Exception as e:
            logger.error("Tool call failed", tool=tool_name, error=str(e))
            result = {
                "success": False,
                "error": {"message": str(e)}
            }
        
        logger.info("Tool result", tool=tool_name, success=result.get("success", False))
        return result
    
    async def _handle_get_items(self, args: dict[str, Any]) -> dict[str, Any]:
        """Handle get_syteline_items tool call."""
        item_filter = args.get("item")
        product_code = args.get("product_code")
        limit = min(args.get("limit", 10), 100)
        
        # Build filter
        filters = []
        if item_filter:
            filters.append(f"Item LIKE '%{item_filter}%'")
        if product_code:
            filters.append(f"ProductCode = '{product_code}'")
        
        filter_expr = " AND ".join(filters) if filters else None
        
        properties = [
            "Item", "Description", "ProductCode", "UM", "Stat",
            "itmUf_colorcode01", "itmUf_colorCode02", "itmUf_ColorCode03"
        ]
        
        records = await self._client.query_ido(
            ido_name="SLItems",
            properties=properties,
            filter_expr=filter_expr,
            row_cap=limit,
        )
        
        return {
            "success": True,
            "data": {
                "items": records,
                "count": len(records),
                "source": "SyteLine 10 Demo (Kaspar DW)"
            }
        }
    
    async def _handle_get_customers(self, args: dict[str, Any]) -> dict[str, Any]:
        """Handle get_syteline_customers tool call."""
        customer_filter = args.get("customer")
        limit = min(args.get("limit", 10), 100)
        
        filter_expr = None
        if customer_filter:
            filter_expr = f"Name LIKE '%{customer_filter}%' OR CustNum LIKE '%{customer_filter}%'"
        
        properties = ["CustNum", "Name", "Contact", "Phone", "City", "State"]
        
        records = await self._client.query_ido(
            ido_name="SLCustomers",
            properties=properties,
            filter_expr=filter_expr,
            row_cap=limit,
        )
        
        return {
            "success": True,
            "data": {
                "customers": records,
                "count": len(records),
                "source": "SyteLine 10 Demo (Kaspar DW)"
            }
        }
    
    async def _handle_query_ido(self, args: dict[str, Any]) -> dict[str, Any]:
        """Handle query_syteline_ido tool call."""
        ido_name = args.get("ido_name")
        if not ido_name:
            return {
                "success": False,
                "error": {"message": "ido_name is required"}
            }
        
        properties = args.get("properties")
        filter_expr = args.get("filter")
        limit = min(args.get("limit", 10), 100)
        
        records = await self._client.query_ido(
            ido_name=ido_name,
            properties=properties,
            filter_expr=filter_expr,
            row_cap=limit,
        )
        
        return {
            "success": True,
            "data": {
                "ido": ido_name,
                "records": records,
                "count": len(records),
                "source": "SyteLine 10 Demo (Kaspar DW)"
            }
        }
    
    async def handle_message(self, message: dict[str, Any]) -> dict[str, Any]:
        """
        Handle an incoming MCP message.
        
        Args:
            message: MCP protocol message
        
        Returns:
            Response message
        """
        msg_type = message.get("method", "")
        msg_id = message.get("id")
        params = message.get("params", {})
        
        try:
            if msg_type == "initialize":
                result = self.get_server_info()
            
            elif msg_type == "tools/list":
                result = {"tools": self.get_tools()}
            
            elif msg_type == "tools/call":
                tool_name = params.get("name", "")
                arguments = params.get("arguments", {})
                result = await self.call_tool(tool_name, arguments)
            
            else:
                result = {"error": f"Unknown method: {msg_type}"}
            
            return {
                "jsonrpc": "2.0",
                "id": msg_id,
                "result": result
            }
        
        except Exception as e:
            logger.error("Message handling failed", error=str(e))
            return {
                "jsonrpc": "2.0",
                "id": msg_id,
                "error": {
                    "code": -32603,
                    "message": str(e)
                }
            }
    
    async def run_stdio(self) -> None:
        """
        Run MCP server using stdio transport.
        
        Reads JSON-RPC messages from stdin, writes responses to stdout.
        """
        logger.info("Starting Demo MCP server on stdio")
        
        reader = asyncio.StreamReader()
        protocol = asyncio.StreamReaderProtocol(reader)
        await asyncio.get_event_loop().connect_read_pipe(
            lambda: protocol, sys.stdin
        )
        
        writer_transport, writer_protocol = await asyncio.get_event_loop().connect_write_pipe(
            asyncio.streams.FlowControlMixin, sys.stdout
        )
        writer = asyncio.StreamWriter(
            writer_transport, writer_protocol, reader, asyncio.get_event_loop()
        )
        
        while True:
            try:
                line = await reader.readline()
                if not line:
                    break
                
                message = json.loads(line.decode())
                response = await self.handle_message(message)
                
                writer.write(json.dumps(response).encode() + b"\n")
                await writer.drain()
                
            except json.JSONDecodeError as e:
                logger.error("Invalid JSON", error=str(e))
            except Exception as e:
                logger.error("Message loop error", error=str(e))
                break
        
        logger.info("Demo MCP server stopped")


async def run_demo_server() -> None:
    """Run the demo MCP server."""
    async with DemoMcpServer() as server:
        await server.run_stdio()


def run() -> None:
    """Entry point for running demo MCP server."""
    asyncio.run(run_demo_server())


if __name__ == "__main__":
    run()
