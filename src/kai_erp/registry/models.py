"""Pydantic models for connector configuration."""

from typing import Optional
from pydantic import BaseModel, Field


class PropertyConfig(BaseModel):
    """Configuration for a single IDO property/field."""

    name: str = Field(..., description="Property name in the IDO")
    alias: str | None = Field(None, description="Friendly alias for display")
    type: str = Field("string", description="Data type: string, number, date, boolean")
    description: str | None = Field(None, description="Human-readable description")
    filterable: bool = Field(False, description="Can this field be used in filters?")
    sortable: bool = Field(False, description="Can this field be used for sorting?")
    primary_key: bool = Field(False, description="Is this the primary key?")


class IDOConfig(BaseModel):
    """Configuration for an IDO (Intelligent Data Object) data source."""

    name: str = Field(..., description="IDO name in SyteLine (e.g., SLJobRoutes)")
    alias: str | None = Field(None, description="Friendly name for display")
    description: str | None = Field(None, description="What data this IDO provides")
    properties: list[PropertyConfig] = Field(
        default_factory=list, description="List of properties to fetch"
    )
    default_filter: str | None = Field(
        None, description="Default filter expression (e.g., Status = 'O')"
    )


class JoinConfig(BaseModel):
    """Configuration for joining multiple IDOs."""

    type: str = Field("LEFT", description="Join type: INNER, LEFT, RIGHT")
    left_ido: str = Field(..., description="Left IDO alias")
    right_ido: str = Field(..., description="Right IDO alias")
    left_key: str = Field(..., description="Left join key property")
    right_key: str = Field(..., description="Right join key property")


class ToolParameterConfig(BaseModel):
    """Configuration for an MCP tool parameter."""

    name: str = Field(..., description="Parameter name")
    type: str = Field("string", description="Parameter type")
    description: str = Field(..., description="Parameter description for AI")
    required: bool = Field(False, description="Is this parameter required?")
    default: str | None = Field(None, description="Default value")
    enum: list[str] | None = Field(None, description="Allowed values")


class ToolConfig(BaseModel):
    """Configuration for an MCP tool exposed by this connector."""

    name: str = Field(..., description="Tool name (e.g., get_production_schedule)")
    description: str = Field(..., description="What this tool does (for AI)")
    parameters: list[ToolParameterConfig] = Field(
        default_factory=list, description="Tool parameters"
    )


class ConnectorConfig(BaseModel):
    """Complete connector configuration."""

    # Identity
    id: str = Field(..., description="Unique connector identifier (slug)")
    name: str = Field(..., description="Human-readable name")
    description: str = Field(..., description="What this connector does")
    version: str = Field("1.0.0", description="Semantic version")
    category: str = Field("General", description="Category for grouping")
    icon: str = Field("puzzle", description="Lucide icon name")
    tags: list[str] = Field(default_factory=list, description="Search tags")
    status: str = Field("draft", description="draft or published")

    # Data Sources
    idos: list[IDOConfig] = Field(
        default_factory=list, description="IDO data sources"
    )

    # Relationships
    joins: list[JoinConfig] = Field(
        default_factory=list, description="How to join IDOs"
    )

    # Join SQL (for complex joins)
    join_sql: str | None = Field(
        None, description="Custom SQL for DuckDB staging join"
    )

    # Output Schema
    output_fields: list[PropertyConfig] = Field(
        default_factory=list, description="Fields in the final output"
    )

    # MCP Tools
    tools: list[ToolConfig] = Field(
        default_factory=list, description="MCP tools this connector exposes"
    )

    # Performance hints
    estimated_volume: str = Field(
        "medium", description="Expected data volume: low, medium, high"
    )
    freshness_requirement: str = Field(
        "real-time", description="Data freshness: real-time, near-real-time, batch"
    )

    model_config = {"extra": "allow"}
