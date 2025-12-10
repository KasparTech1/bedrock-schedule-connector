"""API routes for the Connector Registry."""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from kai_erp.registry import ConnectorConfig, get_registry

router = APIRouter(prefix="/api/connectors", tags=["Connectors"])


class ConnectorSummary(BaseModel):
    """Summary view of a connector for list views."""

    id: str
    name: str
    description: str
    category: str
    version: str
    icon: str
    tags: list[str]
    status: str
    tools_count: int


def _to_summary(config: ConnectorConfig) -> ConnectorSummary:
    """Convert a ConnectorConfig to a summary."""
    return ConnectorSummary(
        id=config.id,
        name=config.name,
        description=config.description,
        category=config.category,
        version=config.version,
        icon=config.icon,
        tags=config.tags,
        status=config.status,
        tools_count=len(config.tools),
    )


@router.get("/", response_model=list[ConnectorSummary])
async def list_connectors(published_only: bool = False) -> list[ConnectorSummary]:
    """List all connectors.

    Args:
        published_only: If True, only return published connectors.
    """
    registry = get_registry()

    if published_only:
        connectors = registry.list_published()
    else:
        connectors = registry.list_all()

    return [_to_summary(c) for c in connectors]


@router.get("/{connector_id}", response_model=ConnectorConfig)
async def get_connector(connector_id: str) -> ConnectorConfig:
    """Get a connector's full configuration."""
    registry = get_registry()
    config = registry.get(connector_id)

    if config is None:
        raise HTTPException(status_code=404, detail=f"Connector '{connector_id}' not found")

    return config


@router.post("/", response_model=ConnectorConfig)
async def create_connector(config: ConnectorConfig) -> ConnectorConfig:
    """Create a new connector configuration."""
    registry = get_registry()

    # Check if connector already exists
    existing = registry.get(config.id)
    if existing is not None:
        raise HTTPException(
            status_code=409, detail=f"Connector '{config.id}' already exists"
        )

    registry.save(config)
    return config


@router.put("/{connector_id}", response_model=ConnectorConfig)
async def update_connector(connector_id: str, config: ConnectorConfig) -> ConnectorConfig:
    """Update an existing connector configuration."""
    registry = get_registry()

    # Ensure the connector exists
    existing = registry.get(connector_id)
    if existing is None:
        raise HTTPException(status_code=404, detail=f"Connector '{connector_id}' not found")

    # Ensure IDs match
    if config.id != connector_id:
        raise HTTPException(
            status_code=400,
            detail=f"Connector ID in body '{config.id}' doesn't match URL '{connector_id}'",
        )

    registry.save(config)
    return config


@router.delete("/{connector_id}")
async def delete_connector(connector_id: str) -> dict:
    """Delete a connector configuration."""
    registry = get_registry()

    if not registry.delete(connector_id):
        raise HTTPException(status_code=404, detail=f"Connector '{connector_id}' not found")

    return {"message": f"Connector '{connector_id}' deleted"}


@router.post("/{connector_id}/publish", response_model=ConnectorConfig)
async def publish_connector(connector_id: str) -> ConnectorConfig:
    """Publish a connector (change status to 'published')."""
    registry = get_registry()

    config = registry.get(connector_id)
    if config is None:
        raise HTTPException(status_code=404, detail=f"Connector '{connector_id}' not found")

    config.status = "published"
    registry.save(config)
    return config


@router.post("/{connector_id}/unpublish", response_model=ConnectorConfig)
async def unpublish_connector(connector_id: str) -> ConnectorConfig:
    """Unpublish a connector (change status to 'draft')."""
    registry = get_registry()

    config = registry.get(connector_id)
    if config is None:
        raise HTTPException(status_code=404, detail=f"Connector '{connector_id}' not found")

    config.status = "draft"
    registry.save(config)
    return config


@router.post("/{connector_id}/duplicate", response_model=ConnectorConfig)
async def duplicate_connector(connector_id: str, new_id: str) -> ConnectorConfig:
    """Duplicate a connector with a new ID."""
    registry = get_registry()

    config = registry.get(connector_id)
    if config is None:
        raise HTTPException(status_code=404, detail=f"Connector '{connector_id}' not found")

    # Check new ID doesn't exist
    if registry.get(new_id) is not None:
        raise HTTPException(status_code=409, detail=f"Connector '{new_id}' already exists")

    # Create copy with new ID
    new_config = config.model_copy(
        update={
            "id": new_id,
            "name": f"{config.name} (Copy)",
            "status": "draft",
        }
    )
    registry.save(new_config)
    return new_config
