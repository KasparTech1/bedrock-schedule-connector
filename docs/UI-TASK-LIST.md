# KAI ERP Connector Catalog - UI Implementation Task List

## Overview

Build a web-based management UI for the KAI ERP Connector library, enabling developers to create/edit connectors and customers to browse/test available connectors for SyteLine 10 ERP.

**Stack:** FastAPI + Jinja2 + Bootstrap 5 + HTMX

---

## Phase 1: Foundation (Day 1)

### 1.1 Project Structure Setup

```
[ ] Create UI directory structure:
    src/kai_erp/
    └── ui/
        ├── __init__.py
        ├── app.py              # FastAPI UI routes
        ├── templates/
        │   ├── base.html       # Base template with nav
        │   ├── components/     # Reusable partials
        │   └── pages/          # Full page templates
        └── static/
            ├── css/
            └── js/

[ ] Add UI dependencies to pyproject.toml:
    - jinja2
    - python-multipart (forms)

[ ] Create base.html with:
    - Bootstrap 5 CDN
    - HTMX CDN
    - Navigation header
    - Flash message area
    - Footer
```

### 1.2 Connector Registry (Data Layer)

```
[ ] Create src/kai_erp/registry/__init__.py

[ ] Create src/kai_erp/registry/models.py
    - ConnectorConfig (Pydantic model matching YAML schema)
    - DataSourceConfig
    - PropertyConfig
    - JoinConfig
    - ParameterConfig
    - OutputFieldConfig
    - ToolConfig

[ ] Create src/kai_erp/registry/store.py
    - ConnectorStore class
    - load_connector(id: str) -> ConnectorConfig
    - save_connector(config: ConnectorConfig)
    - list_connectors() -> list[ConnectorSummary]
    - delete_connector(id: str)
    
[ ] Create src/kai_erp/registry/yaml_backend.py
    - YAML file-based storage
    - Directory: data/connectors/*.yaml
    
[ ] Create data/connectors/ directory

[ ] Migrate Bedrock connector to YAML format:
    - data/connectors/bedrock-ops-scheduler.yaml
```

---

## Phase 2: Customer Library View (Day 2)

### 2.1 Library Browser

```
[ ] Create templates/pages/library/index.html
    - Grid of connector cards
    - Category filter sidebar
    - Search box
    - Tag filtering

[ ] Create templates/components/connector-card.html
    - Connector name, icon, description
    - Category badge
    - Version
    - [View Details] [Try It] buttons

[ ] Create ui/routes/library.py
    - GET /library - List all connectors
    - GET /library/search - HTMX search endpoint
```

### 2.2 Connector Detail Page

```
[ ] Create templates/pages/library/detail.html
    - Tabbed interface:
      - Overview (description, use cases)
      - Tools (available MCP tools)
      - Output Schema (fields and types)
      - Try It (interactive tester)
      - Get Code (snippets)

[ ] Create templates/components/tool-docs.html
    - Tool name, description
    - Parameters table
    - Example inputs/outputs

[ ] Create templates/components/schema-viewer.html
    - Output field table
    - JSON schema display
    - Example output

[ ] Create ui/routes/library.py additions:
    - GET /library/{connector_id} - Detail page
```

### 2.3 Interactive Tool Tester

```
[ ] Create templates/components/tool-tester.html
    - Tool selector dropdown
    - Dynamic parameter form (based on tool schema)
    - Execute button
    - Results panel (JSON viewer)
    - Latency display

[ ] Create ui/routes/tester.py
    - POST /api/test-tool - Execute tool and return results
    - Uses actual connector or mock data

[ ] Add HTMX for live updates:
    - Form submission without page reload
    - Loading spinner during execution
```

---

## Phase 3: DEV Admin - Connector Builder (Day 3-4)

### 3.1 Connector List & CRUD

```
[ ] Create templates/pages/admin/connectors/index.html
    - Table of connectors (name, version, status)
    - [+ New Connector] button
    - [Edit] [Clone] [Delete] actions
    - Status badges (draft, published)

[ ] Create ui/routes/admin/connectors.py
    - GET /admin/connectors - List
    - GET /admin/connectors/new - Create form
    - POST /admin/connectors - Save new
    - GET /admin/connectors/{id}/edit - Edit form
    - PUT /admin/connectors/{id} - Update
    - DELETE /admin/connectors/{id} - Delete
```

### 3.2 Connector Builder - General Info

```
[ ] Create templates/pages/admin/connectors/edit.html
    - Multi-step wizard OR tabbed interface
    - Sections:
      1. General (name, description, category, tags)
      2. Data Sources
      3. Properties
      4. Joins
      5. Calculated Fields
      6. Parameters
      7. Output Mapping
      8. Tools

[ ] Create templates/components/admin/general-form.html
    - Name, ID (auto-generated)
    - Description (textarea)
    - Category dropdown
    - Version input
    - Tags (multi-select or chips)
    - Icon selector
```

### 3.3 Connector Builder - Data Sources

```
[ ] Create templates/components/admin/sources-editor.html
    - List of configured IDOs
    - [+ Add IDO] button
    - Per-IDO card:
      - IDO name (dropdown or autocomplete)
      - Alias input
      - Description
      - Base filter
      - [Remove] button

[ ] Create ui/routes/admin/ido_lookup.py
    - GET /api/admin/idos - List available IDOs (from SyteLine)
    - GET /api/admin/idos/{name}/properties - Get IDO properties
    - (Requires connection to test environment)
```

### 3.4 Connector Builder - Properties Selector

```
[ ] Create templates/components/admin/properties-editor.html
    - Per-IDO accordion
    - Checkbox list of properties
    - Property metadata display (type, description)
    - [Select All] [Clear All] buttons

[ ] HTMX integration:
    - Load properties dynamically when IDO selected
```

### 3.5 Connector Builder - Join Builder

```
[ ] Create templates/components/admin/joins-editor.html
    - Visual representation (simple or diagram)
    - Join list:
      - From IDO (dropdown)
      - To IDO (dropdown)
      - Join Type (INNER, LEFT, RIGHT)
      - ON condition (text input with helpers)
    - [+ Add Join] button
    - Validation: check for orphan tables

[ ] Create ui/routes/admin/join_helper.py
    - GET /api/admin/join-suggest - Suggest join conditions
    - Based on common patterns (Job=Job, Item=Item)
```

### 3.6 Connector Builder - Calculated Fields

```
[ ] Create templates/components/admin/calculated-editor.html
    - List of calculated fields
    - Per-field form:
      - Field name
      - Type (string, float, enum, etc.)
      - Formula (SQL expression)
      - Description
      - Enum values (if type=enum)
    - SQL syntax highlighting (CodeMirror or similar)
    - [Test Formula] button
```

### 3.7 Connector Builder - Parameters

```
[ ] Create templates/components/admin/parameters-editor.html
    - List of user-facing filter parameters
    - Per-parameter form:
      - Name (snake_case)
      - Type (string, integer, boolean, date)
      - Required (checkbox)
      - Default value
      - Description
      - Applies to (column reference)
      - Examples
    - [+ Add Parameter] button
```

### 3.8 Connector Builder - Output Mapping

```
[ ] Create templates/components/admin/output-editor.html
    - Output model name
    - Field mapping table:
      - Output field name
      - Source (column or calculated field)
      - Type
      - Description
    - [+ Add Field] button
    - Example output preview (live)
```

### 3.9 Connector Builder - Tools Definition

```
[ ] Create templates/components/admin/tools-editor.html
    - List of MCP tools for this connector
    - Per-tool form:
      - Tool name
      - Description (markdown)
      - Parameters (select from connector parameters)
      - Enabled (checkbox)
    - [+ Add Tool] button
    - Preview of MCP schema
```

---

## Phase 4: Test Database Connector (Day 4)

### 4.1 SQLite Test Backend

```
[ ] Create src/kai_erp/test_db/__init__.py

[ ] Create src/kai_erp/test_db/schema.py
    - SQLite schema matching SyteLine structure
    - Tables: jobs, jobroutes, jrt_schs, items, itemwhses, wcs
    - Create indexes

[ ] Create src/kai_erp/test_db/seed.py
    - Seed data generator
    - Realistic job numbers, item codes
    - Various statuses (on_track, behind, complete)
    - Configurable volume (10, 100, 1000 records)

[ ] Create src/kai_erp/test_db/engine.py
    - TestDatabaseEngine class
    - Compatible with connector interface
    - execute_query(sql) -> list[dict]
```

### 4.2 Test Connector Integration

```
[ ] Create data/connectors/test-db-scheduler.yaml
    - Mirror of Bedrock connector
    - Connection type: sqlite_test

[ ] Update ConnectorStore to support test connections

[ ] Add "Use Test Data" toggle in Tool Tester UI
```

---

## Phase 5: Settings & Configuration (Day 5)

### 5.1 Connection Management

```
[ ] Create templates/pages/admin/connections/index.html
    - List of configured connections
    - Types: SyteLine 10, SQLite Test, (future: Data Lake)
    - Per-connection:
      - Name
      - Type
      - Environment (Dev, Test, Prod)
      - Status (connected, error)
      - [Test Connection] button

[ ] Create templates/pages/admin/connections/edit.html
    - Connection form based on type
    - SyteLine: Base URL, Config Name, Username, Password
    - SQLite: File path

[ ] Create ui/routes/admin/connections.py
    - CRUD for connections
    - POST /api/admin/connections/{id}/test - Test connection
```

### 5.2 System Settings

```
[ ] Create templates/pages/admin/settings.html
    - Volume thresholds
    - Default routing (REST vs Lake)
    - Logging level
    - Cache settings
```

---

## Phase 6: Polish & Testing (Day 5-6)

### 6.1 UI Polish

```
[ ] Add loading states (HTMX indicators)
[ ] Add toast notifications (success, error)
[ ] Add confirmation dialogs (delete actions)
[ ] Add form validation (client + server)
[ ] Responsive design for mobile
[ ] Dark mode toggle (optional)
```

### 6.2 Tests

```
[ ] Create tests/test_ui/test_library.py
    - Test library listing
    - Test connector detail page
    - Test tool tester

[ ] Create tests/test_ui/test_admin.py
    - Test connector CRUD
    - Test validation

[ ] Create tests/test_registry/test_store.py
    - Test YAML loading/saving
    - Test connector validation
```

### 6.3 Documentation

```
[ ] Create docs/UI-GUIDE.md
    - How to use the library browser
    - How to create a new connector
    - How to configure connections

[ ] Update README.md with UI instructions
```

---

## File Structure (Final)

```
src/kai_erp/
├── ui/
│   ├── __init__.py
│   ├── app.py                    # Main UI app
│   ├── routes/
│   │   ├── __init__.py
│   │   ├── library.py            # Customer library routes
│   │   ├── tester.py             # Tool tester API
│   │   └── admin/
│   │       ├── __init__.py
│   │       ├── connectors.py     # Connector CRUD
│   │       ├── connections.py    # Connection management
│   │       └── settings.py       # System settings
│   ├── templates/
│   │   ├── base.html
│   │   ├── components/
│   │   │   ├── connector-card.html
│   │   │   ├── tool-docs.html
│   │   │   ├── tool-tester.html
│   │   │   └── admin/
│   │   │       ├── general-form.html
│   │   │       ├── sources-editor.html
│   │   │       ├── properties-editor.html
│   │   │       ├── joins-editor.html
│   │   │       ├── calculated-editor.html
│   │   │       ├── parameters-editor.html
│   │   │       ├── output-editor.html
│   │   │       └── tools-editor.html
│   │   └── pages/
│   │       ├── library/
│   │       │   ├── index.html
│   │       │   └── detail.html
│   │       └── admin/
│   │           ├── connectors/
│   │           │   ├── index.html
│   │           │   └── edit.html
│   │           ├── connections/
│   │           │   ├── index.html
│   │           │   └── edit.html
│   │           └── settings.html
│   └── static/
│       ├── css/
│       │   └── custom.css
│       └── js/
│           └── app.js
│
├── registry/
│   ├── __init__.py
│   ├── models.py                 # ConnectorConfig etc.
│   ├── store.py                  # ConnectorStore
│   └── yaml_backend.py           # YAML file storage
│
├── test_db/
│   ├── __init__.py
│   ├── schema.py                 # SQLite schema
│   ├── seed.py                   # Test data generator
│   └── engine.py                 # Test database engine
│
data/
├── connectors/
│   ├── bedrock-ops-scheduler.yaml
│   ├── sales-order-tracker.yaml
│   ├── customer-search.yaml
│   ├── inventory-status.yaml
│   └── test-db-scheduler.yaml
│
└── test.db                       # SQLite test database
```

---

## Estimated Timeline

| Phase | Duration | Deliverable |
|-------|----------|-------------|
| Phase 1: Foundation | 4 hours | Project structure, registry models |
| Phase 2: Library View | 4 hours | Customer-facing connector browser |
| Phase 3: Connector Builder | 8 hours | Full admin CRUD for connectors |
| Phase 4: Test Database | 3 hours | SQLite backend with seed data |
| Phase 5: Settings | 2 hours | Connection and system configuration |
| Phase 6: Polish | 3 hours | UX improvements, tests, docs |
| **Total** | **~24 hours** | **Complete UI** |

---

## Quick Start Commands

```bash
# Start UI server
python -m kai_erp.ui.app

# Access UI
open http://localhost:8100/library    # Customer view
open http://localhost:8100/admin      # Admin view

# Seed test database
python -m kai_erp.test_db.seed --count 100
```

---

## Next Steps

1. ✅ Task list created
2. [ ] Begin Phase 1: Foundation
3. [ ] Create registry models
4. [ ] Migrate Bedrock connector to YAML
5. [ ] Build library browser UI
