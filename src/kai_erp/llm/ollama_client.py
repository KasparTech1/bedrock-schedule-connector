"""
Ollama Client
=============

Client for interacting with the local Ollama LLM service.
"""

import json
from dataclasses import dataclass
from typing import Any, AsyncIterator

import httpx
import structlog

logger = structlog.get_logger(__name__)


@dataclass
class OllamaConfig:
    """Ollama connection configuration."""
    
    base_url: str = "http://localhost:11434"
    model: str = "llama3.2:1b"
    timeout: int = 120


class OllamaClient:
    """Client for Ollama LLM service.
    
    Provides chat completions with tool/function calling support.
    """

    def __init__(self, config: OllamaConfig | None = None):
        """Initialize Ollama client.
        
        Args:
            config: Ollama configuration. Uses defaults if not provided.
        """
        self.config = config or OllamaConfig()
        self._client: httpx.AsyncClient | None = None

    async def __aenter__(self) -> "OllamaClient":
        """Enter async context."""
        self._client = httpx.AsyncClient(timeout=self.config.timeout)
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb) -> None:
        """Exit async context."""
        if self._client:
            await self._client.aclose()
            self._client = None

    async def health_check(self) -> bool:
        """Check if Ollama is running and responsive."""
        try:
            if not self._client:
                async with httpx.AsyncClient(timeout=5) as client:
                    response = await client.get(f"{self.config.base_url}/api/tags")
                    return response.status_code == 200
            else:
                response = await self._client.get(f"{self.config.base_url}/api/tags")
                return response.status_code == 200
        except Exception as e:
            logger.warning("Ollama health check failed", error=str(e))
            return False

    async def list_models(self) -> list[str]:
        """List available models."""
        if not self._client:
            raise RuntimeError("Client not initialized. Use async with context manager.")
        
        response = await self._client.get(f"{self.config.base_url}/api/tags")
        response.raise_for_status()
        
        data = response.json()
        return [model["name"] for model in data.get("models", [])]

    async def chat(
        self,
        messages: list[dict[str, str]],
        tools: list[dict[str, Any]] | None = None,
        stream: bool = False,
    ) -> dict[str, Any]:
        """
        Send a chat completion request.
        
        Args:
            messages: List of message dicts with 'role' and 'content'.
            tools: Optional list of tool definitions for function calling.
            stream: Whether to stream the response.
        
        Returns:
            Response dict with 'message' containing assistant's reply.
        """
        if not self._client:
            raise RuntimeError("Client not initialized. Use async with context manager.")
        
        payload = {
            "model": self.config.model,
            "messages": messages,
            "stream": stream,
        }
        
        # Add tools if provided (Ollama supports function calling)
        if tools:
            payload["tools"] = tools
        
        logger.debug("Sending chat request", model=self.config.model, num_messages=len(messages))
        
        response = await self._client.post(
            f"{self.config.base_url}/api/chat",
            json=payload,
        )
        response.raise_for_status()
        
        result = response.json()
        logger.debug("Chat response received", has_tool_calls="tool_calls" in result.get("message", {}))
        
        return result

    async def chat_stream(
        self,
        messages: list[dict[str, str]],
    ) -> AsyncIterator[str]:
        """
        Stream a chat completion response.
        
        Args:
            messages: List of message dicts with 'role' and 'content'.
        
        Yields:
            Content chunks as they arrive.
        """
        if not self._client:
            raise RuntimeError("Client not initialized. Use async with context manager.")
        
        payload = {
            "model": self.config.model,
            "messages": messages,
            "stream": True,
        }
        
        async with self._client.stream(
            "POST",
            f"{self.config.base_url}/api/chat",
            json=payload,
        ) as response:
            response.raise_for_status()
            
            async for line in response.aiter_lines():
                if line:
                    try:
                        data = json.loads(line)
                        content = data.get("message", {}).get("content", "")
                        if content:
                            yield content
                    except json.JSONDecodeError:
                        continue

    async def generate(
        self,
        prompt: str,
        system: str | None = None,
    ) -> str:
        """
        Simple text generation (non-chat format).
        
        Args:
            prompt: The prompt to complete.
            system: Optional system prompt.
        
        Returns:
            Generated text.
        """
        if not self._client:
            raise RuntimeError("Client not initialized. Use async with context manager.")
        
        payload = {
            "model": self.config.model,
            "prompt": prompt,
            "stream": False,
        }
        
        if system:
            payload["system"] = system
        
        response = await self._client.post(
            f"{self.config.base_url}/api/generate",
            json=payload,
        )
        response.raise_for_status()
        
        return response.json().get("response", "")
