"""Local LLM Service for KAI ERP Connector."""

from .chat_service import ChatService, ChatMessage
from .ollama_client import OllamaClient

__all__ = ["ChatService", "ChatMessage", "OllamaClient"]
