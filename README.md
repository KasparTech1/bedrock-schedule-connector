# KAI ERP Connector

**Making ERP Data AI-Ready**

A three-layer system for accessing SyteLine 10 CloudSuite data, designed for both AI agents and traditional applications.

## Quick Start

```bash
# Install dependencies
pip install -e ".[dev]"

# Copy and configure environment
cp .env.example .env
# Edit .env with your SyteLine credentials

# Run tests
pytest

# Start API server
uvicorn kai_erp.api.main:app --reload --port 8100

# Start MCP server (for AI agents)
python -m kai_erp.mcp.server
```

## Architecture

```
┌─────────────────────────────────────────────────────────────────────┐
│  Layer 3: MCP SERVER                              ← AI talks here   │
│  Tools that AI agents can discover and use                          │
├─────────────────────────────────────────────────────────────────────┤
│  Layer 2: CONNECTORS                              ← Business logic  │
│  Bedrock Scheduler, Sales Orders, Inventory, etc.                   │
├─────────────────────────────────────────────────────────────────────┤
│  Layer 1: DATA SOURCES                            ← Complexity hide │
│  REST APIs (real-time) + Data Lake (bulk/history)                   │
└─────────────────────────────────────────────────────────────────────┘
```

## Available Tools

| Tool | Description | Connector |
|------|-------------|-----------|
| `get_production_schedule` | Production operations by work center | BedrockOpsScheduler |
| `get_open_orders` | Open sales orders and backlog | SalesOrderTracker |
| `search_customers` | Customer lookup | CustomerSearch |
| `get_inventory_status` | Stock levels and availability | InventoryStatus |

## API Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/bedrock/schedule` | GET | Production schedule |
| `/sales/orders` | GET | Open sales orders |
| `/customers/search` | GET | Customer search |
| `/inventory/status` | GET | Inventory status |
| `/health` | GET | Health check |

## Project Structure

```
kai-erp-connector/
├── src/kai_erp/
│   ├── core/           # Layer 1: Data source engines
│   ├── connectors/     # Layer 2: Business logic
│   ├── mcp/            # Layer 3: AI interface
│   ├── models/         # Pydantic data models
│   └── api/            # REST API routes
├── tests/
├── docs/
│   ├── BLUEPRINT.md    # Full technical specification
│   └── agent task list # Multi-agent execution plan
└── pyproject.toml
```

## Development

See `docs/agent task list` for the multi-agent development plan.

### Running Tests

```bash
# All tests
pytest

# With coverage
pytest --cov=kai_erp

# Specific layer
pytest tests/test_core/
pytest tests/test_connectors/
pytest tests/test_mcp/
```

## Documentation

- [BLUEPRINT.md](docs/BLUEPRINT.md) - Complete technical specification
- [Agent Task List](docs/agent%20task%20list) - Multi-agent development plan

## License

Proprietary - Kaspar Companies IT
