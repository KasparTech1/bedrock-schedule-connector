"""
API Dependencies
================

FastAPI dependency injection for shared resources.

This module provides:
- RestEngine injection (replaces global state)
- Configuration injection
- Request-scoped resources
- Testable dependency overrides

Usage:
    @app.get("/endpoint")
    async def endpoint(engine: RestEngine = Depends(get_rest_engine)):
        result = await engine.fetch_ido(...)
"""

from contextlib import asynccontextmanager
from typing import AsyncGenerator, Optional

from fastapi import Depends, Request
import structlog

from kai_erp.config import Config, get_config, SyteLineConfig
from kai_erp.core.rest_engine import RestEngine

logger = structlog.get_logger(__name__)


# =============================================================================
# Engine State Management
# =============================================================================

class EngineManager:
    """
    Manages REST engine lifecycle for the application.
    
    Provides a single engine instance that is initialized on startup
    and cleaned up on shutdown. The engine can be overridden for testing.
    
    Example:
        # In tests
        manager = EngineManager()
        manager.set_engine(mock_engine)
    """
    
    def __init__(self):
        self._engine: Optional[RestEngine] = None
        self._override: Optional[RestEngine] = None
    
    async def initialize(self, config: SyteLineConfig) -> None:
        """Initialize the REST engine."""
        if self._engine is not None:
            logger.warning("Engine already initialized, skipping")
            return
        
        self._engine = RestEngine(config)
        await self._engine.__aenter__()
        logger.info("REST engine initialized")
    
    async def shutdown(self) -> None:
        """Shutdown the REST engine."""
        if self._engine is not None:
            await self._engine.__aexit__(None, None, None)
            self._engine = None
            logger.info("REST engine shutdown")
    
    def get_engine(self) -> Optional[RestEngine]:
        """Get the current engine (or override if set)."""
        if self._override is not None:
            return self._override
        return self._engine
    
    def set_override(self, engine: Optional[RestEngine]) -> None:
        """
        Set an override engine (for testing).
        
        Args:
            engine: Override engine, or None to clear override
        """
        self._override = engine
    
    @property
    def is_initialized(self) -> bool:
        """Check if engine is initialized."""
        return self._engine is not None or self._override is not None


# Global engine manager instance
_engine_manager = EngineManager()


def get_engine_manager() -> EngineManager:
    """Get the global engine manager."""
    return _engine_manager


# =============================================================================
# FastAPI Dependencies
# =============================================================================

async def get_rest_engine(
    request: Request,
) -> RestEngine:
    """
    Dependency to get the REST engine.
    
    Usage:
        @app.get("/data")
        async def get_data(engine: RestEngine = Depends(get_rest_engine)):
            data = await engine.fetch_ido(...)
            return data
    
    Raises:
        HTTPException(503): If engine is not initialized
    """
    from fastapi import HTTPException
    
    manager = get_engine_manager()
    engine = manager.get_engine()
    
    if engine is None:
        raise HTTPException(
            status_code=503,
            detail="Service not initialized. REST engine unavailable."
        )
    
    return engine


async def get_optional_engine(
    request: Request,
) -> Optional[RestEngine]:
    """
    Dependency to get the REST engine optionally.
    
    Returns None instead of raising if engine is not initialized.
    Useful for endpoints that can work without the engine.
    """
    manager = get_engine_manager()
    return manager.get_engine()


def get_app_config() -> Config:
    """Dependency to get application configuration."""
    return get_config()


def get_syteline_config() -> SyteLineConfig:
    """Dependency to get SyteLine configuration."""
    config = get_config()
    return config.syteline


# =============================================================================
# Lifespan Management
# =============================================================================

@asynccontextmanager
async def engine_lifespan():
    """
    Async context manager for engine lifecycle.
    
    Use in FastAPI lifespan:
        @asynccontextmanager
        async def lifespan(app: FastAPI):
            async with engine_lifespan():
                yield
    """
    config = get_config()
    manager = get_engine_manager()
    
    try:
        await manager.initialize(config.syteline)
        yield
    finally:
        await manager.shutdown()


# =============================================================================
# Testing Utilities
# =============================================================================

class EngineDependencyOverride:
    """
    Context manager for overriding engine dependency in tests.
    
    Example:
        def test_with_mock_engine():
            mock_engine = MagicMock()
            
            with EngineDependencyOverride(mock_engine):
                response = client.get("/data")
    """
    
    def __init__(self, engine: RestEngine):
        self.engine = engine
        self._manager = get_engine_manager()
    
    def __enter__(self):
        self._manager.set_override(self.engine)
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        self._manager.set_override(None)
        return False


async def create_test_engine() -> AsyncGenerator[RestEngine, None]:
    """
    Create a test engine for testing.
    
    Usage:
        @pytest.fixture
        async def test_engine():
            async for engine in create_test_engine():
                yield engine
    """
    from kai_erp.config import SyteLineConfig
    
    config = SyteLineConfig(
        base_url="https://test.example.com",
        config_name="TEST",
        username="test",
        password="test",
    )
    
    engine = RestEngine(config)
    async with engine:
        yield engine

