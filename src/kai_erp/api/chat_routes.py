"""API routes for LLM chat service."""

from typing import Any

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from kai_erp.llm.chat_service import ChatService
from kai_erp.llm.ollama_client import OllamaClient, OllamaConfig

router = APIRouter(prefix="/api/chat", tags=["Chat"])

# Global chat service instance (initialized on first use)
_chat_service: ChatService | None = None


class ChatRequest(BaseModel):
    """Request to send a chat message."""
    message: str
    use_tools: bool = True  # Whether to use MCP tool calling


class ChatResponse(BaseModel):
    """Response from chat."""
    response: str
    tool_calls: list[dict[str, Any]] | None = None


class OllamaStatus(BaseModel):
    """Ollama service status."""
    available: bool
    base_url: str
    model: str
    models_installed: list[str] | None = None
    error: str | None = None


async def get_chat_service() -> ChatService:
    """Get or create the chat service."""
    global _chat_service
    
    if _chat_service is None:
        config = OllamaConfig(
            base_url="http://localhost:11434",
            model="llama3.2:1b",  # Default small model
        )
        _chat_service = ChatService(ollama_config=config)
        await _chat_service.initialize()
    
    return _chat_service


@router.get("/status")
async def get_chat_status() -> OllamaStatus:
    """Check if Ollama is running and available."""
    config = OllamaConfig()
    
    try:
        async with OllamaClient(config) as client:
            is_healthy = await client.health_check()
            
            if is_healthy:
                models = await client.list_models()
                return OllamaStatus(
                    available=True,
                    base_url=config.base_url,
                    model=config.model,
                    models_installed=models
                )
            else:
                return OllamaStatus(
                    available=False,
                    base_url=config.base_url,
                    model=config.model,
                    error="Ollama not responding"
                )
    except Exception as e:
        return OllamaStatus(
            available=False,
            base_url=config.base_url,
            model=config.model,
            error=str(e)
        )


@router.post("/send")
async def send_message(request: ChatRequest) -> ChatResponse:
    """
    Send a message to the chat service.
    
    The LLM will process the message and may call MCP tools
    to fetch ERP data if needed.
    """
    try:
        service = await get_chat_service()
        
        if request.use_tools:
            response = await service.chat(request.message)
        else:
            response = await service.chat_simple(request.message)
        
        return ChatResponse(response=response)
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/send-simple")
async def send_message_simple(request: ChatRequest) -> ChatResponse:
    """
    Send a message without function calling.
    
    Uses smart detection to call tools based on message content.
    Better for models that don't support function calling.
    """
    try:
        service = await get_chat_service()
        response = await service.chat_simple(request.message)
        return ChatResponse(response=response)
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/history")
async def get_history() -> list[dict[str, Any]]:
    """Get conversation history."""
    try:
        service = await get_chat_service()
        return service.get_history()
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/clear")
async def clear_history() -> dict[str, str]:
    """Clear conversation history."""
    try:
        service = await get_chat_service()
        service.clear_history()
        return {"status": "ok", "message": "History cleared"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/set-model")
async def set_model(model: str) -> dict[str, str]:
    """Change the active model."""
    global _chat_service
    
    # Shutdown existing service
    if _chat_service:
        await _chat_service.shutdown()
        _chat_service = None
    
    # Create new service with new model
    config = OllamaConfig(model=model)
    _chat_service = ChatService(ollama_config=config)
    await _chat_service.initialize()
    
    return {"status": "ok", "model": model}
