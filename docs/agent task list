# KAI ERP Connector - Parallel Agent Execution Plan

## Executive Summary

This document defines a **Multi-Agent Coordination Strategy** for building the KAI ERP Connector autonomously. The architecture allows 3 parallel agent tracks with minimal synchronization points.

---

## Architecture Analysis: Dependency Graph

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                        DEPENDENCY ANALYSIS                                   │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  FOUNDATIONAL (Must Complete First - ~2 hours)                              │
│  ═══════════════════════════════════════════                                │
│  ├── Project Setup (pyproject.toml, Docker, etc.)                           │
│  ├── Base Interfaces (config.py, models/)                                   │
│  └── Core Abstractions (connectors/base.py)                                 │
│                                                                             │
│            ↓ SYNC POINT #1: Foundation Complete                             │
│  ══════════════════════════════════════════════════════════════════════════ │
│                                                                             │
│  PARALLEL TRACK A           PARALLEL TRACK B           PARALLEL TRACK C     │
│  ─────────────────           ─────────────────         ─────────────────    │
│                                                                             │
│  CORE ENGINE                 CONNECTORS                 INFRA + TESTS       │
│  • auth.py                   • bedrock_ops.py          • Docker/Coolify     │
│  • rest_engine.py            • sales_orders.py         • CI/CD pipelines    │
│  • staging.py (DuckDB)       • customers.py            • test fixtures      │
│  • lake_engine.py            • inventory.py            • integration tests  │
│  • router.py                                           • mock server        │
│                                                                             │
│            ↓ SYNC POINT #2: Core + Connectors Ready                         │
│  ══════════════════════════════════════════════════════════════════════════ │
│                                                                             │
│  FINAL ASSEMBLY (Single Agent)                                              │
│  ════════════════════════════                                               │
│  ├── API Layer (FastAPI routes)                                             │
│  ├── MCP Server Integration                                                 │
│  └── End-to-End Testing                                                     │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## Option A: Fully Parallel Agents (No Runtime Coordination)

Three agents work independently on separate file paths. Requires strict interface contracts defined upfront.

### Pre-Work: Interface Contracts (Completed by Lead Agent First)

These files define the contracts all parallel agents code against:

```
INTERFACE CONTRACT FILES:
├── src/kai_erp/config.py           # Configuration schema
├── src/kai_erp/models/__init__.py  # All Pydantic models  
├── src/kai_erp/core/types.py       # Core type definitions
├── src/kai_erp/connectors/base.py  # BaseConnector ABC
└── tests/conftest.py               # Shared test fixtures
```

---

## AGENT A: Core Data Engine Track

**Scope:** All files in `src/kai_erp/core/`
**No dependencies on:** Connectors, MCP, API routes
**Estimated Time:** 4-6 hours

### Task List - Agent A

```
[ ] A.1  Create src/kai_erp/core/__init__.py
         - Export all public classes
         
[ ] A.2  Create src/kai_erp/core/auth.py
         - TokenManager class
         - Token acquisition via OAuth2 client credentials
         - Token caching with Redis or in-memory
         - Auto-refresh at 55 minutes (5 min before expiry)
         - Retry on 401 errors
         
[ ] A.3  Create src/kai_erp/core/rest_engine.py
         - RestEngine class
         - IDOSpec dataclass
         - async parallel_fetch(ido_specs: list[IDOSpec])
         - Connection pooling with httpx.AsyncClient
         - Rate limit handling (429 → exponential backoff)
         - Configurable timeout (default 30s)
         
[ ] A.4  Create src/kai_erp/core/staging.py
         - StagingEngine class
         - DuckDB in-memory instance management
         - load_dataframe(name: str, df: pd.DataFrame)
         - execute_query(sql: str) -> pd.DataFrame
         - Ephemeral instance pattern (create → use → discard)
         
[ ] A.5  Create src/kai_erp/core/lake_engine.py
         - DataLakeEngine class
         - ION API authentication
         - Compass SQL execution
         - Result pagination (100K rows/page)
         - Query timeout handling (60 min max)
         
[ ] A.6  Create src/kai_erp/core/router.py
         - QueryRouter class
         - Volume thresholds: REST < 5K, Lake > 10K
         - Freshness enum: REALTIME, NEAR_REALTIME, BATCH_OK
         - select_source(volume: int, freshness: Freshness) -> DataSource

[ ] A.7  Create tests/test_core/test_auth.py
         - Mock OAuth server responses
         - Test token refresh
         - Test 401 retry logic
         
[ ] A.8  Create tests/test_core/test_rest_engine.py
         - Mock IDO responses
         - Test parallel fetch timing
         - Test rate limit backoff
         
[ ] A.9  Create tests/test_core/test_staging.py
         - Test DuckDB join queries
         - Test DataFrame loading
         - Test ephemeral cleanup
```

---

## AGENT B: Business Connectors Track

**Scope:** All files in `src/kai_erp/connectors/` and `src/kai_erp/models/`
**Depends on:** Interface contracts only (not implementations)
**Estimated Time:** 4-6 hours

### Task List - Agent B

```
[ ] B.1  Create src/kai_erp/models/__init__.py
         - Re-export all model classes
         
[ ] B.2  Create src/kai_erp/models/operations.py
         - ScheduledOperation Pydantic model
         - All fields from BLUEPRINT §7.1
         
[ ] B.3  Create src/kai_erp/models/orders.py
         - SalesOrder Pydantic model
         - OrderLine Pydantic model
         
[ ] B.4  Create src/kai_erp/models/customers.py
         - Customer Pydantic model
         - CustomerAddress Pydantic model
         
[ ] B.5  Create src/kai_erp/models/inventory.py
         - InventoryItem Pydantic model
         - WarehouseStock Pydantic model

[ ] B.6  Create src/kai_erp/connectors/__init__.py
         - Export all connector classes
         
[ ] B.7  Create src/kai_erp/connectors/base.py
         - BaseConnector ABC
         - Abstract methods: get_rest_spec, get_lake_query, estimate_volume, transform_result
         - Concrete execute() method with routing logic
         - RestQuerySpec and IDOSpec dataclasses
         - ConnectorResult dataclass
         
[ ] B.8  Create src/kai_erp/connectors/bedrock_ops.py
         - BedrockOpsScheduler(BaseConnector)
         - 6 IDO specs: SLJobs, SLJobroutes, SLJrtSchs, SLItems, SLItemwhses, SLWcs
         - Join SQL from BLUEPRINT §7.2
         - Filter handling: work_center, job, include_completed
         - Transform row → ScheduledOperation
         
[ ] B.9  Create src/kai_erp/connectors/sales_orders.py
         - SalesOrderTracker(BaseConnector)
         - IDOs: SLCos, SLCoitems, SLCustomers, SLItems
         - Filter: customer, days_out
         
[ ] B.10 Create src/kai_erp/connectors/customers.py
         - CustomerSearch(BaseConnector)
         - IDOs: SLCustomers, SLCustaddrs
         - Filter: query (search term), active_only
         
[ ] B.11 Create src/kai_erp/connectors/inventory.py
         - InventoryStatus(BaseConnector)
         - IDOs: SLItems, SLItemwhses, SLItemlocs
         - Filter: item, warehouse, low_stock_only

[ ] B.12 Create tests/test_connectors/test_bedrock_ops.py
         - Test with mock REST engine
         - Test filter application
         - Test result transformation
         
[ ] B.13 Create tests/test_connectors/test_sales_orders.py
         
[ ] B.14 Create tests/test_connectors/test_customers.py
         
[ ] B.15 Create tests/test_connectors/test_inventory.py
```

---

## AGENT C: Infrastructure + Integration Track

**Scope:** Docker, API routes, MCP server, CI/CD
**Depends on:** Interface contracts only
**Estimated Time:** 4-6 hours

### Task List - Agent C

```
[ ] C.1  Create pyproject.toml
         - Python 3.11+
         - Dependencies: httpx, duckdb, pydantic, fastapi, uvicorn, mcp
         - Dev dependencies: pytest, pytest-asyncio, respx (HTTP mocking)
         
[ ] C.2  Create Dockerfile
         - Multi-stage build
         - Python 3.11-slim base
         - Non-root user
         - Health check endpoint
         
[ ] C.3  Create docker-compose.yml
         - Service: kai-erp-connector
         - Port mapping: 8100:8100
         - Environment file reference
         - Health check

[ ] C.4  Create .env.example
         - All config vars from BLUEPRINT §9.2
         
[ ] C.5  Create src/kai_erp/api/__init__.py
         
[ ] C.6  Create src/kai_erp/api/main.py
         - FastAPI app initialization
         - CORS configuration
         - Lifespan handler (startup/shutdown)
         - Health endpoint
         
[ ] C.7  Create src/kai_erp/api/routes/__init__.py
         
[ ] C.8  Create src/kai_erp/api/routes/bedrock.py
         - GET /bedrock/schedule
         - Query params: work_center, job, include_completed
         
[ ] C.9  Create src/kai_erp/api/routes/sales.py
         - GET /sales/orders
         - Query params: customer, days_out
         
[ ] C.10 Create src/kai_erp/api/routes/inventory.py
         - GET /inventory/status
         - Query params: item, warehouse, low_stock_only

[ ] C.11 Create src/kai_erp/mcp/__init__.py
         
[ ] C.12 Create src/kai_erp/mcp/tools.py
         - Tool definitions from BLUEPRINT §6.2
         - get_production_schedule
         - get_open_orders
         - search_customers
         - get_inventory_status
         
[ ] C.13 Create src/kai_erp/mcp/server.py
         - KaiErpMcpServer(Server)
         - Tool registration
         - Error translation
         
[ ] C.14 Create src/kai_erp/mcp/handlers.py
         - Handler functions bridging tools → connectors
         
[ ] C.15 Create tests/conftest.py
         - Shared fixtures
         - Mock SyteLine responses
         - Test database setup
         
[ ] C.16 Create tests/test_api/test_bedrock_routes.py
         
[ ] C.17 Create tests/test_mcp/test_tools.py
         - Test tool discovery
         - Test parameter validation
         
[ ] C.18 Create .github/workflows/ci.yml (optional)
         - Run tests on push
         - Build Docker image
```

---

## Option B: Orchestrated Sub-Agent System (Recommended)

For fully autonomous execution with coordination, implement this sub-agent architecture:

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                     ORCHESTRATED AGENT SYSTEM                                │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│                        ┌─────────────────────┐                              │
│                        │   ORCHESTRATOR      │                              │
│                        │   AGENT             │                              │
│                        │                     │                              │
│                        │  • Reads this plan  │                              │
│                        │  • Assigns tasks    │                              │
│                        │  • Monitors status  │                              │
│                        │  • Handles blocks   │                              │
│                        └─────────┬───────────┘                              │
│                                  │                                          │
│              ┌───────────────────┼───────────────────┐                      │
│              ▼                   ▼                   ▼                      │
│     ┌────────────────┐  ┌────────────────┐  ┌────────────────┐             │
│     │   AGENT A      │  │   AGENT B      │  │   AGENT C      │             │
│     │   Core Engine  │  │   Connectors   │  │   Infra/API    │             │
│     │                │  │                │  │                │             │
│     │  Files:        │  │  Files:        │  │  Files:        │             │
│     │  core/*        │  │  connectors/*  │  │  api/*         │             │
│     │                │  │  models/*      │  │  mcp/*         │             │
│     │                │  │                │  │  Docker        │             │
│     └────────────────┘  └────────────────┘  └────────────────┘             │
│                                                                             │
│  COORDINATION MECHANISM: Shared Status File                                 │
│  ══════════════════════════════════════════                                 │
│                                                                             │
│  File: docs/agent-status.json                                               │
│                                                                             │
│  {                                                                          │
│    "phase": "parallel_development",                                         │
│    "sync_point": 1,                                                         │
│    "agents": {                                                              │
│      "A": {"status": "working", "current_task": "A.3", "blocked": false},  │
│      "B": {"status": "waiting", "waiting_for": "A.2", "blocked": true},    │
│      "C": {"status": "working", "current_task": "C.4", "blocked": false}   │
│    },                                                                       │
│    "completed_tasks": ["A.1", "A.2", "B.1", "C.1", "C.2", "C.3"],          │
│    "integration_tests_passed": false                                        │
│  }                                                                          │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

### Coordination Protocol

1. **Before Starting a Task:**
   - Read `agent-status.json`
   - Check if dependencies are complete
   - Update status to "working" with current task

2. **After Completing a Task:**
   - Update `completed_tasks` array
   - Move to next task in sequence
   - If blocked, set `blocked: true` and `waiting_for: "<task_id>"`

3. **Orchestrator Checks:**
   - Every 5 minutes, review status file
   - Resolve conflicts (two agents editing same file)
   - Trigger sync point when all agents reach checkpoint

---

## Sync Point Definitions

### Sync Point #1: Foundation Complete

**Trigger:** All interface contracts are committed and tested

**Files that must exist:**
- [ ] `src/kai_erp/__init__.py`
- [ ] `src/kai_erp/config.py`
- [ ] `src/kai_erp/models/__init__.py` (with all Pydantic models)
- [ ] `src/kai_erp/connectors/base.py` (BaseConnector ABC)
- [ ] `src/kai_erp/core/types.py` (shared types)
- [ ] `tests/conftest.py` (shared fixtures)
- [ ] `pyproject.toml`

**Gate:** `pytest tests/test_models/ -v` passes

### Sync Point #2: Core + Connectors Ready

**Trigger:** All core engine and connector implementations complete

**Gate Criteria:**
- [ ] `pytest tests/test_core/ -v` passes
- [ ] `pytest tests/test_connectors/ -v` passes
- [ ] BedrockOpsScheduler.execute() returns valid data (mock mode)

### Sync Point #3: Integration Complete

**Trigger:** API and MCP layers integrated

**Gate Criteria:**
- [ ] `pytest tests/test_api/ -v` passes
- [ ] `pytest tests/test_mcp/ -v` passes
- [ ] Docker container starts and health check passes
- [ ] Manual test: `curl http://localhost:8100/bedrock/schedule` returns 200

---

## Quick Start: Running Parallel Agents

### Method 1: Cursor Multi-Window (Simplest)

1. Open 3 Cursor windows pointing to same repo
2. Each window runs one agent track
3. Use git branches:
   ```
   main
   ├── agent-a/core-engine
   ├── agent-b/connectors
   └── agent-c/infrastructure
   ```
4. Merge at sync points

### Method 2: Cursor + Background Agents

1. One Cursor window runs Orchestrator
2. Use `cursor --agent` CLI for background agents:
   ```bash
   cursor --agent "Run Agent A tasks from docs/agent-task-list.md" &
   cursor --agent "Run Agent B tasks from docs/agent-task-list.md" &
   cursor --agent "Run Agent C tasks from docs/agent-task-list.md" &
   ```

### Method 3: Task Queue (Most Robust)

Create a simple task queue in `docs/task-queue.json`:

```json
{
  "available": ["A.1", "A.2", "B.1", "C.1", "C.2"],
  "in_progress": [],
  "completed": [],
  "failed": []
}
```

Each agent:
1. Pops a task from `available`
2. Moves to `in_progress`
3. Completes and moves to `completed`
4. Handles failures gracefully

---

## Execution Timeline (Optimistic)

```
Hour 0:    Lead Agent creates interface contracts (Sync Point #1 prep)
Hour 1:    Sync Point #1 - Foundation Complete
           ├── Agent A starts on core/
           ├── Agent B starts on models/ and connectors/
           └── Agent C starts on Docker and API structure
           
Hour 3:    Mid-point check
           ├── Agent A: ~60% core engine done
           ├── Agent B: ~70% connectors done (models complete)
           └── Agent C: ~80% infrastructure done
           
Hour 5:    Sync Point #2 - Core + Connectors Ready
           └── All agents converge on integration
           
Hour 6:    Sync Point #3 - Integration Complete
           └── Full system operational
           
Hour 7:    Final testing and documentation
           └── Deployment ready
```

---

## File Ownership (Conflict Prevention)

| Directory/File | Owner Agent | Notes |
|---------------|-------------|-------|
| `src/kai_erp/core/` | Agent A | Exclusive |
| `src/kai_erp/connectors/` | Agent B | Except base.py |
| `src/kai_erp/connectors/base.py` | Lead (pre-work) | Interface contract |
| `src/kai_erp/models/` | Agent B | Exclusive |
| `src/kai_erp/api/` | Agent C | Exclusive |
| `src/kai_erp/mcp/` | Agent C | Exclusive |
| `tests/test_core/` | Agent A | Exclusive |
| `tests/test_connectors/` | Agent B | Exclusive |
| `tests/test_api/` | Agent C | Exclusive |
| `tests/test_mcp/` | Agent C | Exclusive |
| `tests/conftest.py` | Lead (pre-work) | Shared fixtures |
| `pyproject.toml` | Agent C | May need Agent A input |
| `Dockerfile` | Agent C | Exclusive |
| `docker-compose.yml` | Agent C | Exclusive |

---

## Emergency Procedures

### If an Agent is Blocked

1. Check `agent-status.json` for blocking task
2. Prioritize unblocking work
3. If circular dependency: Orchestrator creates stub implementation

### If Tests Fail at Sync Point

1. Identify failing test and owning agent
2. All agents pause until fixed
3. Orchestrator coordinates fix

### If Merge Conflicts Occur

1. Agent who created conflict resolves
2. Use interface contracts as source of truth
3. Orchestrator has final say on API design decisions

---

## Recommendation

**For autonomous execution without human intervention:**

Use **Option B (Orchestrated Sub-Agent System)** with:

1. **Pre-work Phase:** Single lead agent creates all interface contracts
2. **Parallel Phase:** Three agents work independently on owned directories
3. **Integration Phase:** Single agent assembles and tests full system

This approach:
- ✅ Minimizes coordination overhead
- ✅ Prevents file conflicts through clear ownership
- ✅ Has defined sync points for quality gates
- ✅ Can recover from individual agent failures
- ✅ Produces working system in ~7 hours

---

## Next Steps

1. Create `src/kai_erp/__init__.py` and directory structure
2. Create interface contracts (config.py, models/, base.py)
3. Create `docs/agent-status.json` for coordination
4. Launch parallel agents on their respective tracks
