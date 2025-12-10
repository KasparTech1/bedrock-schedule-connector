"""
MCP Server
==========

Model Context Protocol server for AI agent access to ERP data.

This is the primary interface for AI agents like Claude.
Exposes ERP data as discoverable tools with clear schemas.
"""

import asyncio
import json
from typing import Any

import structlog

from kai_erp.config import get_config
from kai_erp.core import RestEngine
from kai_erp.mcp.tools import get_tool_schemas
from kai_erp.mcp.handlers import dispatch_tool_call

logger = structlog.get_logger(__name__)


class KaiErpMcpServer:
    """
    MCP Server for KAI ERP Connector.
    
    Implements the Model Context Protocol to expose ERP data
    as AI-discoverable tools.
    
    Example:
        async with KaiErpMcpServer() as server:
            await server.run_stdio()
    """
    
    SERVER_NAME = "kai-erp"
    SERVER_VERSION = "3.0.0"
    
    def __init__(self):
        """Initialize MCP server."""
        self.config = get_config()
        self._engine: RestEngine | None = None
    
    async def __aenter__(self) -> "KaiErpMcpServer":
        """Async context manager entry."""
        self._engine = RestEngine(self.config.syteline)
        await self._engine.__aenter__()
        logger.info("MCP server initialized")
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb) -> None:
        """Async context manager exit."""
        if self._engine:
            await self._engine.__aexit__(exc_type, exc_val, exc_tb)
        logger.info("MCP server shutdown")
    
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
        return get_tool_schemas()
    
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
        if not self._engine:
            return {
                "success": False,
                "error": {"message": "Server not initialized"}
            }
        
        logger.info("Tool call", tool=tool_name, arguments=arguments)
        
        result = await dispatch_tool_call(self._engine, tool_name, arguments)
        
        logger.info(
            "Tool result",
            tool=tool_name,
            success=result.get("success", False)
        )
        
        return result
    
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
        import sys
        
        logger.info("Starting MCP server on stdio")
        
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
                # Read line from stdin
                line = await reader.readline()
                if not line:
                    break
                
                # Parse JSON message
                message = json.loads(line.decode())
                
                # Handle message
                response = await self.handle_message(message)
                
                # Write response
                writer.write(json.dumps(response).encode() + b"\n")
                await writer.drain()
                
            except json.JSONDecodeError as e:
                logger.error("Invalid JSON", error=str(e))
            except Exception as e:
                logger.error("Message loop error", error=str(e))
                break
        
        logger.info("MCP server stopped")


async def run_server() -> None:
    """Run the MCP server."""
    async with KaiErpMcpServer() as server:
        await server.run_stdio()


def run() -> None:
    """Entry point for running MCP server."""
    asyncio.run(run_server())


if __name__ == "__main__":
    run()
