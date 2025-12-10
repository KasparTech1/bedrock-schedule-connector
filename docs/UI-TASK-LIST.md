# KAI ERP Connector Catalog - UI Implementation Task List

## Overview

Build a web-based management UI for the KAI ERP Connector library, enabling developers to create/edit connectors and customers to browse/test available connectors for SyteLine 10 ERP.

---

## Technology Stack (Per AI Agent Style Guide)

### Frontend
```
React 18 + TypeScript
Vite (build tool)
Tailwind CSS v3.4 + tailwindcss-animate
shadcn/ui (New York style variant)
Radix UI primitives
Lucide React (icons)
```

### Backend API
```
FastAPI (existing)
Python 3.11+
```

### Key Dependencies
```json
{
  "lucide-react": "^0.453.0",
  "framer-motion": "^11.13.1",
  "react-hook-form": "^7.55.0",
  "zod": "^3.24.2",
  "date-fns": "^3.6.0",
  "wouter": "^3.3.5",
  "@tanstack/react-query": "^5.60.5"
}
```

### Design Principles (From Style Guide)
1. **Scanability First** - Dense information with clear visual hierarchy
2. **Consistent Patterns** - Reusable components reduce cognitive load
3. **Data Clarity** - Tables, metrics are heroes—UI recedes to support them
4. **Progressive Disclosure** - Complex workflows broken into digestible steps

### Color Palette
```css
--primary: 211 92% 42%;     /* #0C6FD9 - Kai Blue */
--background: 210 4% 98%;   /* #F9FAFB - Light gray */
--foreground: 210 6% 12%;   /* #1F2937 - Dark text */
--success: 142 76% 36%;     /* #16A34A - Green */
--warning: 38 92% 50%;      /* #F59E0B - Amber */
--destructive: 0 84% 48%;   /* #DC2626 - Red */
```

---

## Phase 1: Project Setup (Day 1 - 4 hours)

### 1.1 Create React Frontend Project

```
[ ] Create client/ directory in project root
    client/
    ├── src/
    │   ├── components/
    │   │   └── ui/           # shadcn components
    │   ├── pages/
    │   ├── hooks/
    │   ├── lib/
    │   └── index.css
    ├── public/
    │   └── favicon.png       # Kai Labs logo
    ├── package.json
    ├── vite.config.ts
    ├── tailwind.config.ts
    └── tsconfig.json

[ ] Initialize Vite + React + TypeScript:
    npm create vite@latest client -- --template react-ts

[ ] Install dependencies:
    npm install tailwindcss postcss autoprefixer
    npm install lucide-react framer-motion
    npm install react-hook-form zod @hookform/resolvers
    npm install @tanstack/react-query wouter
    npm install class-variance-authority clsx tailwind-merge

[ ] Configure Tailwind with Kai Labs color system:
    - Copy CSS variables from AI_AGENT_STYLE_GUIDE.md
    - Set up light/dark mode support

[ ] Install shadcn/ui components:
    npx shadcn-ui@latest init
    # Style: new-york
    # Base color: neutral
    
    npx shadcn-ui@latest add button card badge input
    npx shadcn-ui@latest add dialog table tabs form
    npx shadcn-ui@latest add select textarea tooltip
    npx shadcn-ui@latest add dropdown-menu separator
    npx shadcn-ui@latest add accordion skeleton toast
```

### 1.2 Branding & Assets

```
[ ] Copy favicon.png to client/public/
    - Use the Kai Labs "K" with sparkle logo

[ ] Add to index.html:
    <link rel="icon" type="image/png" href="/favicon.png" />

[ ] Set up Inter font from Google Fonts

[ ] Create logo component with favicon for sidebar
```

### 1.3 Base Layout

```
[ ] Create src/components/AppSidebar.tsx
    - Collapsible sidebar (256px wide, 48px collapsed)
    - Kai Labs logo at top
    - Navigation sections:
      - Library (customer view)
      - Connectors (admin)
      - Connections (admin)
      - Settings (admin)
    - Dark mode toggle at bottom
    - User menu

[ ] Create src/components/Layout.tsx
    - AppSidebar + main content area
    - Responsive (sidebar hidden on mobile)
    - Page header with breadcrumbs
```

### 1.4 API Integration Setup

```
[ ] Create src/lib/queryClient.ts
    - Configure TanStack Query

[ ] Create src/lib/api.ts
    - Fetch wrapper for FastAPI backend
    - Error handling

[ ] Update FastAPI to serve frontend:
    - Mount static files from client/dist
    - API routes under /api/*
```

---

## Phase 2: Connector Registry (Backend - Day 1-2)

### 2.1 Registry Data Models

```
[ ] Create src/kai_erp/registry/__init__.py

[ ] Create src/kai_erp/registry/models.py
    
    @dataclass
    class DataSourceConfig:
        ido: str
        alias: str
        description: str
        primary_key: list[str]
        base_filter: Optional[str]
        properties: list[PropertyConfig]

    @dataclass
    class PropertyConfig:
        name: str
        type: str  # string, integer, float, datetime, boolean
        description: str
        include: bool = True

    @dataclass
    class JoinConfig:
        from_source: str
        to_source: str
        join_type: str  # INNER, LEFT, RIGHT
        on_condition: str

    @dataclass
    class CalculatedFieldConfig:
        name: str
        type: str
        formula: str
        description: str
        enum_values: Optional[list[str]]

    @dataclass
    class ParameterConfig:
        name: str
        type: str
        required: bool
        default: Optional[Any]
        description: str
        applies_to: str
        examples: list[str]

    @dataclass
    class OutputFieldConfig:
        name: str
        source: str  # column ref or "CALCULATED"
        type: str
        description: str

    @dataclass
    class ToolConfig:
        name: str
        description: str
        parameters: list[str]  # refs to ParameterConfig names
        enabled: bool = True

    @dataclass
    class ConnectorConfig:
        id: str
        name: str
        version: str
        category: str
        description: str
        author: str
        tags: list[str]
        icon: str
        connection_ref: str
        sources: list[DataSourceConfig]
        joins: list[JoinConfig]
        calculated_fields: list[CalculatedFieldConfig]
        parameters: list[ParameterConfig]
        output: list[OutputFieldConfig]
        tools: list[ToolConfig]
        performance: dict  # typical_volume, max_volume, etc.
        status: str  # draft, published
```

### 2.2 YAML Storage Backend

```
[ ] Create src/kai_erp/registry/store.py

    class ConnectorStore:
        def __init__(self, data_dir: Path):
            self.data_dir = data_dir
        
        def list_connectors() -> list[ConnectorSummary]
        def get_connector(id: str) -> ConnectorConfig
        def save_connector(config: ConnectorConfig) -> None
        def delete_connector(id: str) -> None
        def validate_connector(config: ConnectorConfig) -> list[str]

[ ] Create data/connectors/ directory

[ ] Migrate existing connectors to YAML:
    - data/connectors/bedrock-ops-scheduler.yaml
    - data/connectors/sales-order-tracker.yaml
    - data/connectors/customer-search.yaml
    - data/connectors/inventory-status.yaml
```

### 2.3 Registry API Endpoints

```
[ ] Create src/kai_erp/api/routes/registry.py

    GET  /api/connectors                    - List all connectors
    GET  /api/connectors/{id}               - Get connector details
    POST /api/connectors                    - Create connector
    PUT  /api/connectors/{id}               - Update connector
    DELETE /api/connectors/{id}             - Delete connector
    POST /api/connectors/{id}/validate      - Validate connector
    POST /api/connectors/{id}/publish       - Publish draft
    GET  /api/connectors/categories         - List categories
    GET  /api/connectors/tags               - List all tags
```

---

## Phase 3: Customer Library View (Day 2 - 4 hours)

### 3.1 Library Browser Page

```
[ ] Create src/pages/Library.tsx
    - Grid of connector cards
    - Category filter sidebar (collapsible on mobile)
    - Search box (instant filter)
    - Tag pills for filtering
    - Sort: name, newest, popular

[ ] Create src/components/ConnectorCard.tsx
    - Connector icon (from Lucide)
    - Name, description (truncated)
    - Category badge
    - Version badge
    - Tags (up to 3)
    - [View Details] [Try It] buttons
    
    Classes (from style guide):
    "rounded-xl border bg-card border-card-border 
     text-card-foreground shadow-sm hover-elevate 
     cursor-pointer active-elevate-2 p-6"

[ ] Create src/components/CategoryFilter.tsx
    - Accordion of categories
    - Count per category
    - Clear filters button
```

### 3.2 Connector Detail Page

```
[ ] Create src/pages/ConnectorDetail.tsx
    - Tabs: Overview | Tools | Output Schema | Try It | Get Code
    - Breadcrumb: Library > Connector Name

[ ] Create Overview tab:
    - Full description (markdown support)
    - Metadata table (author, version, category)
    - Tags
    - Data sources used (list)
    - Performance metrics

[ ] Create Tools tab:
    - List of available MCP tools
    - Per-tool: name, description, parameters table
    - Example usage

[ ] Create Output Schema tab:
    - Field table: name, type, source, description
    - JSON schema viewer
    - Example output (syntax highlighted)

[ ] Create Get Code tab:
    - Tabs: API | MCP | Python
    - Code snippets with copy button
    - API endpoint examples
    - MCP tool config example
```

### 3.3 Interactive Tool Tester

```
[ ] Create src/pages/ToolTester.tsx (or as tab in detail page)
    - Connector selector (if standalone page)
    - Tool selector dropdown
    - Dynamic parameter form (based on tool schema)
    - [Execute] button
    - Loading state with skeleton
    - Results panel:
      - Success/error status badge
      - Response time
      - JSON viewer (collapsible)
      - Record count

[ ] Create src/components/ParameterForm.tsx
    - Render form fields based on parameter types
    - string → Input
    - integer → Input type="number"
    - boolean → Checkbox
    - enum → Select
    - Validation with Zod
    - Default values

[ ] API endpoint:
    POST /api/test-tool
    Body: { connector_id, tool_name, parameters }
    Response: { success, data, latency_ms, error? }
```

---

## Phase 4: DEV Admin - Connector Builder (Day 3-4 - 8 hours)

### 4.1 Connector List Page

```
[ ] Create src/pages/admin/Connectors.tsx
    - Table with columns: Name, Category, Version, Status, Actions
    - Status badges: draft (blue), published (green)
    - Actions: Edit, Clone, Delete
    - [+ New Connector] button
    - Bulk actions: Publish, Delete

[ ] Table classes (from style guide):
    "w-full caption-bottom text-sm"
    Row: "border-b transition-colors hover:bg-muted/50"
    Head: "h-12 px-4 text-left align-middle font-medium text-muted-foreground"
```

### 4.2 Connector Editor - Multi-Step Wizard

```
[ ] Create src/pages/admin/ConnectorEdit.tsx
    - Wizard steps OR tabbed interface:
      1. General Info
      2. Data Sources
      3. Properties
      4. Joins
      5. Calculated Fields
      6. Parameters
      7. Output Mapping
      8. Tools
    - Progress indicator
    - Save Draft / Publish buttons
    - Cancel with unsaved changes warning

[ ] Create src/components/admin/StepIndicator.tsx
    - Horizontal step list
    - Current step highlighted
    - Completed steps checked
```

### 4.3 Step 1: General Info

```
[ ] Create src/components/admin/GeneralForm.tsx
    - Name (required)
    - ID (auto-generated from name, editable)
    - Description (textarea)
    - Category (select from existing + add new)
    - Version (semver input)
    - Author (text)
    - Tags (multi-select with create option)
    - Icon (Lucide icon picker)
    - Connection (select from configured connections)
```

### 4.4 Step 2: Data Sources (IDOs)

```
[ ] Create src/components/admin/SourcesEditor.tsx
    - List of configured IDOs
    - [+ Add Data Source] button
    - Per-IDO card (expandable):
      - IDO name (autocomplete from SyteLine)
      - Alias (short name for joins)
      - Description
      - Primary key fields
      - Base filter
      - [Remove] button

[ ] Create src/components/admin/IDOPicker.tsx
    - Autocomplete search
    - Load IDO list from test connection
    - Show IDO description on hover

[ ] API endpoint:
    GET /api/admin/idos - List available IDOs
    GET /api/admin/idos/{name}/properties - Get IDO schema
```

### 4.5 Step 3: Properties Selector

```
[ ] Create src/components/admin/PropertiesEditor.tsx
    - Accordion per IDO
    - Checkbox list of properties
    - Property info: name, type, description
    - [Select All] [Clear All] per IDO
    - Included count badge

[ ] Fetch properties dynamically when IDO added
```

### 4.6 Step 4: Join Builder

```
[ ] Create src/components/admin/JoinsEditor.tsx
    - Visual diagram showing tables and connections (optional)
    - Join list:
      - From: [IDO selector]
      - To: [IDO selector]
      - Type: [INNER / LEFT / RIGHT]
      - ON: [condition builder or text]
    - [+ Add Join] button
    - Validation: orphan tables warning

[ ] Create src/components/admin/JoinConditionBuilder.tsx
    - Simple mode: dropdowns for column = column
    - Advanced mode: raw SQL input
    - Suggest common patterns (Job=Job, Item=Item)
```

### 4.7 Step 5: Calculated Fields

```
[ ] Create src/components/admin/CalculatedFieldsEditor.tsx
    - List of calculated fields
    - Per-field form:
      - Name
      - Type (string, float, integer, boolean, enum)
      - Formula (SQL expression with syntax highlighting)
      - Description
      - Enum values (if type=enum)
    - [+ Add Field] button
    - [Test Formula] button (runs against test data)

[ ] Use CodeMirror or Monaco for formula editing
```

### 4.8 Step 6: Parameters

```
[ ] Create src/components/admin/ParametersEditor.tsx
    - List of filter parameters
    - Per-parameter form:
      - Name (snake_case)
      - Display Label
      - Type (string, integer, boolean, date)
      - Required (toggle)
      - Default value
      - Description
      - Applies to (column reference picker)
      - Examples (comma-separated)
    - [+ Add Parameter] button
```

### 4.9 Step 7: Output Mapping

```
[ ] Create src/components/admin/OutputEditor.tsx
    - Model name input
    - Field mapping table:
      - Output field name
      - Source (dropdown: columns + calculated fields)
      - Type
      - Description
    - [+ Add Field] button
    - Reorder fields (drag handle)
    - Preview example output (live)
```

### 4.10 Step 8: Tools Definition

```
[ ] Create src/components/admin/ToolsEditor.tsx
    - List of MCP tools
    - Per-tool form:
      - Name (snake_case)
      - Description (markdown textarea)
      - Parameters (multi-select from defined parameters)
      - Enabled (toggle)
    - [+ Add Tool] button
    - Preview MCP schema
```

---

## Phase 5: Test Database Backend (Day 4 - 3 hours)

### 5.1 SQLite Test Database

```
[ ] Create src/kai_erp/test_db/__init__.py

[ ] Create src/kai_erp/test_db/schema.py
    - SQLite schema matching SyteLine structure:
      - jobs (Job, Suffix, Item, QtyReleased, QtyComplete, Stat)
      - jobroutes (Job, Suffix, OperNum, Wc, QtyComplete)
      - jrt_schs (Job, Suffix, OperNum, SchedStart, SchedFinish)
      - items (Item, Description, ProductCode)
      - itemwhses (Item, Whse, QtyOnHand, QtyAllocated)
      - wcs (Wc, Description)
      - cos (CoNum, CustNum, OrderDate, DueDate, Stat)
      - coitems (CoNum, CoLine, Item, QtyOrdered, Price)
      - customers (CustNum, Name, City, State, Phone)
    - Create with: CREATE TABLE IF NOT EXISTS

[ ] Create src/kai_erp/test_db/seed.py
    - Generate realistic test data:
      - 50-200 jobs with operations
      - 100-500 orders
      - 200+ customers
      - 500+ items
    - Realistic statuses (70% on_track, 20% behind, 10% complete)
    - Command: python -m kai_erp.test_db.seed --count 100
```

### 5.2 Test Database Engine

```
[ ] Create src/kai_erp/test_db/engine.py
    
    class TestDatabaseEngine:
        def __init__(self, db_path: str = "data/test.db"):
            self.conn = sqlite3.connect(db_path)
        
        async def execute_query(self, sql: str) -> list[dict]:
            # Execute SQL and return results
        
        async def parallel_fetch(self, ido_specs: list) -> dict:
            # Simulate IDO fetches from SQLite tables

[ ] Create data/connectors/test-db-scheduler.yaml
    - Copy of Bedrock connector
    - connection_ref: test-db
```

### 5.3 Connection Types

```
[ ] Update connection management to support:
    - syteline10 (real SyteLine REST API)
    - sqlite_test (local SQLite for testing)
    - (future: datalake)

[ ] Add "Use Test Data" toggle in Tool Tester UI
```

---

## Phase 6: Connection Management (Day 5 - 2 hours)

### 6.1 Connections Page

```
[ ] Create src/pages/admin/Connections.tsx
    - Table of configured connections
    - Columns: Name, Type, Environment, Status, Actions
    - Status: connected (green), error (red), untested (gray)
    - [+ New Connection] button
    - [Test] button per row

[ ] Create src/components/admin/ConnectionForm.tsx
    - Connection name
    - Type selector (SyteLine 10, SQLite Test)
    - Environment (Development, Test, Production)
    - Type-specific fields:
      - SyteLine: Base URL, Config Name, Username, Password
      - SQLite: File path
    - [Test Connection] button with live feedback
```

### 6.2 Connection API

```
[ ] Create src/kai_erp/api/routes/connections.py

    GET  /api/connections              - List connections
    POST /api/connections              - Create connection
    PUT  /api/connections/{id}         - Update connection
    DELETE /api/connections/{id}       - Delete connection
    POST /api/connections/{id}/test    - Test connection
```

---

## Phase 7: Polish & Deploy (Day 5-6 - 4 hours)

### 7.1 UI Polish

```
[ ] Add loading states (Skeleton components)
[ ] Add toast notifications (success, error, info)
[ ] Add confirmation dialogs (delete actions)
[ ] Form validation with error messages
[ ] Responsive design for tablet/mobile
[ ] Dark mode toggle (use style guide dark theme)
[ ] Keyboard shortcuts:
    - Cmd/Ctrl+K: Search
    - Cmd/Ctrl+S: Save
    - Esc: Close modals
```

### 7.2 Error Handling

```
[ ] Global error boundary
[ ] API error toast notifications
[ ] Retry logic for failed requests
[ ] Offline indicator
```

### 7.3 Build & Deploy

```
[ ] Update Dockerfile for frontend build:
    - Build React app in multi-stage
    - Copy dist to static serving
    
[ ] Update docker-compose.yml:
    - Build frontend
    - Serve via FastAPI

[ ] Create production build script:
    cd client && npm run build
```

### 7.4 Tests

```
[ ] Frontend tests with Vitest:
    - Component unit tests
    - Page integration tests
    
[ ] Backend tests:
    - Registry store tests
    - API endpoint tests
    - Test database tests
```

---

## File Structure (Final)

```
kai-erp-connector/
├── client/                          # React Frontend
│   ├── public/
│   │   └── favicon.png              # Kai Labs logo
│   ├── src/
│   │   ├── components/
│   │   │   ├── ui/                  # shadcn/ui components
│   │   │   ├── AppSidebar.tsx
│   │   │   ├── Layout.tsx
│   │   │   ├── ConnectorCard.tsx
│   │   │   ├── ParameterForm.tsx
│   │   │   └── admin/
│   │   │       ├── GeneralForm.tsx
│   │   │       ├── SourcesEditor.tsx
│   │   │       ├── PropertiesEditor.tsx
│   │   │       ├── JoinsEditor.tsx
│   │   │       ├── CalculatedFieldsEditor.tsx
│   │   │       ├── ParametersEditor.tsx
│   │   │       ├── OutputEditor.tsx
│   │   │       └── ToolsEditor.tsx
│   │   ├── pages/
│   │   │   ├── Library.tsx
│   │   │   ├── ConnectorDetail.tsx
│   │   │   ├── ToolTester.tsx
│   │   │   └── admin/
│   │   │       ├── Connectors.tsx
│   │   │       ├── ConnectorEdit.tsx
│   │   │       ├── Connections.tsx
│   │   │       └── Settings.tsx
│   │   ├── hooks/
│   │   ├── lib/
│   │   │   ├── utils.ts
│   │   │   ├── api.ts
│   │   │   └── queryClient.ts
│   │   ├── index.css
│   │   └── main.tsx
│   ├── package.json
│   ├── vite.config.ts
│   ├── tailwind.config.ts
│   └── tsconfig.json
│
├── src/kai_erp/
│   ├── registry/                    # Connector Registry
│   │   ├── __init__.py
│   │   ├── models.py
│   │   └── store.py
│   ├── test_db/                     # Test Database
│   │   ├── __init__.py
│   │   ├── schema.py
│   │   ├── seed.py
│   │   └── engine.py
│   └── api/routes/
│       ├── registry.py              # Connector API
│       └── connections.py           # Connection API
│
├── data/
│   ├── connectors/                  # YAML configs
│   │   ├── bedrock-ops-scheduler.yaml
│   │   ├── sales-order-tracker.yaml
│   │   └── test-db-scheduler.yaml
│   └── test.db                      # SQLite test database
│
├── AI_AGENT_STYLE_GUIDE.md          # Design reference
├── favicon.png                      # Kai Labs logo
└── docs/
    └── UI-TASK-LIST.md              # This file
```

---

## Estimated Timeline

| Phase | Duration | Deliverable |
|-------|----------|-------------|
| Phase 1: Setup | 4 hours | React + Tailwind + shadcn/ui |
| Phase 2: Registry | 4 hours | YAML backend + API |
| Phase 3: Library View | 4 hours | Customer connector browser |
| Phase 4: Connector Builder | 8 hours | Full admin editor |
| Phase 5: Test Database | 3 hours | SQLite backend + seed |
| Phase 6: Connections | 2 hours | Connection management |
| Phase 7: Polish | 4 hours | UX, tests, deploy |
| **Total** | **~29 hours** | **Complete UI** |

---

## Quick Start Commands

```bash
# Install frontend dependencies
cd client && npm install

# Start frontend dev server
cd client && npm run dev

# Start backend
python -m kai_erp.api.main

# Build for production
cd client && npm run build

# Seed test database
python -m kai_erp.test_db.seed --count 100

# Access UI
open http://localhost:5173          # Frontend dev
open http://localhost:8100/library  # Production
open http://localhost:8100/admin    # Admin view
```

---

## Branding Notes

- **Favicon**: Kai Labs "K" with sparkle (`favicon.png`)
- **Primary Color**: #0C6FD9 (Kai Blue)
- **Font**: Inter
- **Style**: Clean, data-focused, Linear/Notion-inspired
- **Dark Mode**: Full support per style guide

---

## Next Steps

1. ✅ Task list updated with React + shadcn/ui stack
2. [ ] Begin Phase 1: Create React frontend project
3. [ ] Install shadcn/ui with New York style
4. [ ] Set up Kai Labs color theme
5. [ ] Add favicon.png
