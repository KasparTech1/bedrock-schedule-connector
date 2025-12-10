"""
Chat Service
============

Service that bridges user prompts to the local LLM and MCP tools.
Handles the full conversation loop including tool calls.
"""

import json
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any
from enum import Enum

import structlog

from kai_erp.llm.ollama_client import OllamaClient, OllamaConfig
from kai_erp.mcp.demo_server import DemoMcpServer, DEMO_TOOLS

logger = structlog.get_logger(__name__)


class MessageRole(str, Enum):
    """Chat message roles."""
    USER = "user"
    ASSISTANT = "assistant"
    SYSTEM = "system"
    TOOL = "tool"


@dataclass
class ChatMessage:
    """A message in the chat conversation."""
    role: MessageRole
    content: str
    tool_calls: list[dict[str, Any]] | None = None
    tool_call_id: str | None = None
    timestamp: datetime = field(default_factory=datetime.now)

    def to_dict(self) -> dict[str, Any]:
        """Convert to dict for API/Ollama."""
        d = {"role": self.role.value, "content": self.content}
        if self.tool_calls:
            d["tool_calls"] = self.tool_calls
        if self.tool_call_id:
            d["tool_call_id"] = self.tool_call_id
        return d


# System prompt that teaches the LLM how to use tools
SYSTEM_PROMPT = """You are a helpful ERP assistant for Bedrock Manufacturing, connected to SyteLine 10.

You have access to these tools to query live ERP data:

1. **get_syteline_items** - Query item/product master data
   - Use when asked about items, products, SKUs, inventory items
   - Parameters: item (partial match), product_code (exact), limit

2. **get_syteline_customers** - Query customer master data  
   - Use when asked about customers, contacts, accounts
   - Parameters: customer (partial match), limit

3. **query_syteline_ido** - Query any SyteLine IDO directly
   - Use for advanced queries or data not covered by other tools
   - Parameters: ido_name (required), properties, filter, limit

When users ask about ERP data, use the appropriate tool to fetch real data.
Always explain what you found in a clear, helpful way.
If no data is found, explain that and suggest alternative queries.

Current environment: Kaspar Development Workshop (Demo)
"""


@dataclass
class ChatService:
    """
    Chat service that integrates LLM with MCP tools.
    
    Handles the conversation loop:
    1. User sends message
    2. LLM processes and may call tools
    3. Tool results fed back to LLM
    4. LLM generates final response
    """
    
    ollama_config: OllamaConfig = field(default_factory=OllamaConfig)
    conversation: list[ChatMessage] = field(default_factory=list)
    
    def __post_init__(self):
        """Initialize after dataclass creation."""
        self._ollama: OllamaClient | None = None
        self._mcp: DemoMcpServer | None = None
        self._initialized = False

    async def initialize(self) -> None:
        """Initialize the chat service."""
        if self._initialized:
            return
        
        self._ollama = OllamaClient(self.ollama_config)
        await self._ollama.__aenter__()
        
        self._mcp = DemoMcpServer()
        await self._mcp.__aenter__()
        
        # Add system message
        self.conversation = [
            ChatMessage(role=MessageRole.SYSTEM, content=SYSTEM_PROMPT)
        ]
        
        self._initialized = True
        logger.info("Chat service initialized", model=self.ollama_config.model)

    async def shutdown(self) -> None:
        """Shutdown the chat service."""
        if self._ollama:
            await self._ollama.__aexit__(None, None, None)
        if self._mcp:
            await self._mcp.__aexit__(None, None, None)
        self._initialized = False
        logger.info("Chat service shutdown")

    async def __aenter__(self) -> "ChatService":
        """Async context manager entry."""
        await self.initialize()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb) -> None:
        """Async context manager exit."""
        await self.shutdown()

    def _get_tools_for_ollama(self) -> list[dict[str, Any]]:
        """Convert MCP tool definitions to Ollama format."""
        tools = []
        for tool in DEMO_TOOLS:
            tools.append({
                "type": "function",
                "function": {
                    "name": tool["name"],
                    "description": tool["description"],
                    "parameters": tool["inputSchema"]
                }
            })
        return tools

    async def _execute_tool(self, name: str, arguments: dict[str, Any]) -> str:
        """Execute an MCP tool and return result as string."""
        if not self._mcp:
            return json.dumps({"error": "MCP not initialized"})
        
        logger.info("Executing tool", tool=name, arguments=arguments)
        
        result = await self._mcp.call_tool(name, arguments)
        
        # Format result for LLM consumption
        if result.get("success"):
            return json.dumps(result["data"], indent=2)
        else:
            return json.dumps({"error": result.get("error", {}).get("message", "Unknown error")})

    async def chat(self, user_message: str) -> str:
        """
        Process a user message and return the assistant's response.
        
        Handles tool calls automatically.
        
        Args:
            user_message: The user's input message.
        
        Returns:
            The assistant's response text.
        """
        if not self._initialized:
            await self.initialize()
        
        # Add user message to conversation
        self.conversation.append(
            ChatMessage(role=MessageRole.USER, content=user_message)
        )
        
        # Convert conversation to Ollama format
        messages = [msg.to_dict() for msg in self.conversation]
        
        # Get tools for function calling
        tools = self._get_tools_for_ollama()
        
        # Call LLM
        try:
            response = await self._ollama.chat(messages=messages, tools=tools)
        except Exception as e:
            logger.error("LLM call failed", error=str(e))
            error_msg = f"I'm having trouble connecting to the language model. Error: {str(e)}"
            self.conversation.append(
                ChatMessage(role=MessageRole.ASSISTANT, content=error_msg)
            )
            return error_msg
        
        assistant_message = response.get("message", {})
        content = assistant_message.get("content", "")
        tool_calls = assistant_message.get("tool_calls", [])
        
        # If there are tool calls, execute them
        if tool_calls:
            logger.info("Processing tool calls", count=len(tool_calls))
            
            # Add assistant message with tool calls
            self.conversation.append(
                ChatMessage(
                    role=MessageRole.ASSISTANT,
                    content=content or "",
                    tool_calls=tool_calls
                )
            )
            
            # Execute each tool call
            for tool_call in tool_calls:
                func = tool_call.get("function", {})
                tool_name = func.get("name", "")
                
                # Parse arguments
                args_str = func.get("arguments", "{}")
                try:
                    arguments = json.loads(args_str) if isinstance(args_str, str) else args_str
                except json.JSONDecodeError:
                    arguments = {}
                
                # Execute tool
                tool_result = await self._execute_tool(tool_name, arguments)
                
                # Add tool result to conversation
                self.conversation.append(
                    ChatMessage(
                        role=MessageRole.TOOL,
                        content=tool_result,
                        tool_call_id=tool_call.get("id", tool_name)
                    )
                )
            
            # Get final response from LLM with tool results
            messages = [msg.to_dict() for msg in self.conversation]
            
            try:
                final_response = await self._ollama.chat(messages=messages)
                content = final_response.get("message", {}).get("content", "")
            except Exception as e:
                logger.error("Final LLM call failed", error=str(e))
                content = "I retrieved the data but had trouble formatting the response."
        
        # Add final assistant message
        if content:
            self.conversation.append(
                ChatMessage(role=MessageRole.ASSISTANT, content=content)
            )
        
        return content or "I'm not sure how to respond to that."

    async def chat_simple(self, user_message: str) -> str:
        """
        Simple chat without tool calling.
        
        Use this when Ollama doesn't support function calling or
        for models that don't handle tools well.
        
        Args:
            user_message: The user's input message.
        
        Returns:
            The assistant's response text.
        """
        if not self._initialized:
            await self.initialize()
        
        # Add user message
        self.conversation.append(
            ChatMessage(role=MessageRole.USER, content=user_message)
        )
        
        # Check if this looks like an ERP query
        erp_keywords = ["item", "product", "customer", "inventory", "order", "job", "show", "find", "list", "what"]
        is_erp_query = any(kw in user_message.lower() for kw in erp_keywords)
        
        if is_erp_query:
            # Try to detect what tool to use and call it
            tool_result = await self._smart_tool_call(user_message)
            if tool_result:
                # Build a prompt with the data
                enhanced_prompt = f"""The user asked: "{user_message}"

I queried the ERP system and got this data:
{tool_result}

Please provide a helpful response summarizing this information for the user."""
                
                messages = [
                    {"role": "system", "content": SYSTEM_PROMPT},
                    {"role": "user", "content": enhanced_prompt}
                ]
            else:
                messages = [msg.to_dict() for msg in self.conversation]
        else:
            messages = [msg.to_dict() for msg in self.conversation]
        
        # Call LLM
        try:
            response = await self._ollama.chat(messages=messages)
            content = response.get("message", {}).get("content", "")
        except Exception as e:
            logger.error("LLM call failed", error=str(e))
            content = f"Sorry, I encountered an error: {str(e)}"
        
        # Add response to conversation
        self.conversation.append(
            ChatMessage(role=MessageRole.ASSISTANT, content=content)
        )
        
        return content

    async def _smart_tool_call(self, user_message: str) -> str | None:
        """
        Intelligently determine which tool to call based on user message.
        
        This is a fallback for models that don't support function calling.
        """
        msg_lower = user_message.lower()
        
        try:
            # Item queries
            if any(kw in msg_lower for kw in ["item", "product", "sku", "inventory item"]):
                # Try to extract filter
                item_filter = None
                for word in user_message.split():
                    if word.isalnum() and len(word) >= 2 and word.upper() == word:
                        item_filter = word
                        break
                
                result = await self._execute_tool("get_syteline_items", {
                    "item": item_filter,
                    "limit": 10
                })
                return result
            
            # Customer queries
            elif any(kw in msg_lower for kw in ["customer", "client", "account"]):
                result = await self._execute_tool("get_syteline_customers", {"limit": 10})
                return result
            
            # Generic "show me" or "list" queries
            elif any(kw in msg_lower for kw in ["show", "list", "find", "get"]):
                # Default to items
                result = await self._execute_tool("get_syteline_items", {"limit": 5})
                return result
        
        except Exception as e:
            logger.error("Smart tool call failed", error=str(e))
        
        return None

    def clear_history(self) -> None:
        """Clear conversation history (keeps system prompt)."""
        self.conversation = [
            ChatMessage(role=MessageRole.SYSTEM, content=SYSTEM_PROMPT)
        ]
        logger.info("Conversation history cleared")

    def get_history(self) -> list[dict[str, Any]]:
        """Get conversation history as list of dicts."""
        return [
            {
                "role": msg.role.value,
                "content": msg.content,
                "timestamp": msg.timestamp.isoformat()
            }
            for msg in self.conversation
            if msg.role != MessageRole.SYSTEM  # Don't expose system prompt
        ]
