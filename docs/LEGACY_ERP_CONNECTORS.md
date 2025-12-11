# Legacy ERP Connectors

> **Isolation Notice:** Legacy ERP connectors are intentionally isolated from the core connector architecture. These connectors support subsidiary systems during transitional periods and follow bespoke patterns due to infrastructure constraints.

---

## Table of Contents

- [Overview](#overview)
- [Global Shop ERP Connector](#global-shop-erp-connector)
  - [Context & Timeline](#context--timeline)
  - [Architecture](#architecture)
  - [Bridge API](#bridge-api)
  - [Authentication](#authentication)
  - [REST API Endpoints](#rest-api-endpoints)
    - [Product Lines (PRODLINE_MRE)](#product-lines-prodline_mre)
    - [Salespersons (V_SALESPERSONS)](#salespersons-v_salespersons)
  - [Core Components](#core-components)
  - [Connection Health & Metrics](#connection-health--metrics)
  - [Testing & Diagnostics](#testing--diagnostics)
  - [Troubleshooting](#troubleshooting)

---

## Overview

Legacy ERP Connectors serve subsidiary companies during ERP migration periods. These connectors:

- Are **isolated** from the main connector UI and infrastructure
- Follow **bespoke patterns** dictated by legacy system constraints
- Have **defined sunset dates** aligned with migration timelines
- Require **special infrastructure** (on-prem bridges, tunnels, etc.)

| Connector | Subsidiary | Legacy System | Target System | Timeline |
|-----------|------------|---------------|---------------|----------|
| Global Shop | Circle Brands | Pervasive SQL | Syteline 10 | 6-10 months |

---

## Global Shop ERP Connector

### Context & Timeline

**Subsidiary:** Circle Brands  
**Legacy ERP:** Global Shop (Pervasive SQL database)  
**Target ERP:** Syteline 10  
**Expected Duration:** 6-10 months  
**Status:** Active - Transitional

This connector exists to maintain operational continuity for Circle Brands while migrating from Global Shop to Syteline 10. Due to the legacy nature of the Pervasive database and on-premises network requirements, this connector uses a bespoke architecture that differs from our standard connector patterns.

---

### Architecture

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                           CLOUD INFRASTRUCTURE                               │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│   ┌──────────────────┐         HTTPS          ┌─────────────────────────┐   │
│   │                  │ ◄─────────────────────► │                         │   │
│   │   Flask App      │    POST /query          │   Cloudflare Worker     │   │
│   │   (Railway)      │    X-API-Key auth       │   bridge-api.kaiville.io│   │
│   │                  │                         │                         │   │
│   │  ┌────────────┐  │                         └───────────┬─────────────┘   │
│   │  │Pervasive   │  │                                     │                 │
│   │  │DBAnalyzer  │  │                                     │ Cloudflare      │
│   │  └────────────┘  │                                     │ Tunnel          │
│   │                  │                                     │                 │
│   │  ┌────────────┐  │                                     │                 │
│   │  │Streaming   │  │                                     │                 │
│   │  │Analysis    │  │                                     │                 │
│   │  │Manager     │  │                                     │                 │
│   │  └────────────┘  │                                     │                 │
│   │                  │                                     │                 │
│   └──────────────────┘                                     │                 │
│                                                            │                 │
└────────────────────────────────────────────────────────────┼─────────────────┘
                                                             │
                         ════════════════════════════════════╪═══════════════
                                    NETWORK BOUNDARY         │
                         ════════════════════════════════════╪═══════════════
                                                             │
┌────────────────────────────────────────────────────────────┼─────────────────┐
│                     CIRCLE BRANDS ON-PREM NETWORK          │                 │
├────────────────────────────────────────────────────────────┼─────────────────┤
│                                                            │                 │
│   ┌─────────────────────────────┐                          │                 │
│   │                             │ ◄────────────────────────┘                 │
│   │   Bridge Service            │   Cloudflare Tunnel                        │
│   │   (Local Windows Service)   │   (cloudflared daemon)                     │
│   │                             │                                            │
│   └─────────────┬───────────────┘                                            │
│                 │                                                            │
│                 │ ODBC / Pervasive PSQL                                      │
│                 │                                                            │
│   ┌─────────────▼───────────────┐                                            │
│   │                             │                                            │
│   │   Global Shop Database      │                                            │
│   │   (Pervasive SQL)           │                                            │
│   │                             │                                            │
│   └─────────────────────────────┘                                            │
│                                                                              │
└──────────────────────────────────────────────────────────────────────────────┘
```

#### Component Summary

| Component | Location | Purpose |
|-----------|----------|---------|
| Flask App | Railway (Cloud) | Main application, hosts analysis endpoints and UI |
| PervasiveDBAnalyzer | Flask App | Wraps bridge API, normalizes responses |
| StreamingAnalysisManager | Flask App | Manages resumable analysis runs, Supabase persistence |
| Cloudflare Worker | Cloudflare Edge | Public HTTPS endpoint (`bridge-api.kaiville.io`) |
| Cloudflare Tunnel | On-Prem | Secure tunnel from edge to local bridge |
| Bridge Service | On-Prem Windows | Local service with ODBC access to Pervasive |
| Global Shop DB | On-Prem | Pervasive SQL database |

---

### Bridge API

The bridge is an external REST service running near the on-prem Pervasive database. Our application authenticates over HTTPS with an API key, submits plain SQL in JSON, and receives JSON result sets.

#### Endpoint

```
POST https://bridge-api.kaiville.io/query
```

#### Request Format

```json
{
  "sql": "SELECT TOP 25 * FROM prodline_mre"
}
```

#### Headers

| Header | Value | Required |
|--------|-------|----------|
| `Content-Type` | `application/json` | Yes |
| `X-API-Key` | `<PERVASIVE_API_KEY>` | Yes |

#### Response Format

**Success:**
```json
{
  "success": true,
  "data": [
    {"column1": "value1", "column2": "value2"},
    {"column1": "value3", "column2": "value4"}
  ]
}
```

**Error:**
```json
{
  "success": false,
  "error": "Error message describing the issue"
}
```

#### Important Constraints

- **Single statements only:** One SQL statement per request
- **No session state:** Each request is independent
- **Fixed-width strings:** Bridge returns fixed-width strings that require trimming
- **Column alias quirks:** `COUNT(*)` may return as `EXPR_1` or similar

---

### Authentication

#### Environment Variable

```bash
PERVASIVE_API_KEY=<your-api-key>
```

The API key is read from the environment when the analyzer is constructed. If missing, initialization fails.

#### Security Notes

- **Never commit the key to source control**
- Inject at runtime via:
  - Railway environment variables (production)
  - `.env` file (local development)
  - Secrets manager (enterprise deployments)

#### Current API Key

```
<REDACTED>
```

> ⚠️ **Do not store API keys in this repo.** Rotate the Global Shop bridge API key if it was ever committed here.

---

### REST API Endpoints

The Legacy ERP API provides RESTful endpoints for querying Global Shop data. All endpoints are prefixed with `/api/legacy/global-shop`.

#### Health Check

```
GET /api/legacy/global-shop/health
```

Returns connection health status for the Global Shop bridge.

**Response:**
```json
{
  "status": "healthy",
  "response_time_ms": 245,
  "message": "Connection successful",
  "bridge_url": "https://bridge-api.kaiville.io/query"
}
```

---

#### Product Lines (PRODLINE_MRE)

```
GET /api/legacy/global-shop/product-lines
```

Get all product lines from Global Shop.

**Query Parameters:**

| Parameter | Type | Description |
|-----------|------|-------------|
| `product_line` | string | Filter by specific product line code |
| `limit` | integer | Maximum records to return (default: 500, max: 1000) |

**Example Request:**
```bash
curl -X GET "http://localhost:8000/api/legacy/global-shop/product-lines?limit=100"
```

**Response:**
```json
{
  "product_lines": [
    {
      "PRODLINE": "ELEC",
      "DESCRIP": "Electronics",
      "COST_CENTER": "100",
      "ACCOUNT": "4000"
    }
  ],
  "summary": {
    "total": 1,
    "query": "SELECT TOP 100 * FROM prodline_mre",
    "response_time_ms": 312,
    "source": "Global Shop (Pervasive SQL)",
    "table": "PRODLINE_MRE"
  }
}
```

---

#### Salespersons (V_SALESPERSONS)

```
GET /api/legacy/global-shop/salespersons
```

Get sales personnel from Global Shop.

**Query Parameters:**

| Parameter | Type | Description |
|-----------|------|-------------|
| `salesperson` | string | Filter by salesperson ID |
| `limit` | integer | Maximum records to return (default: 500, max: 1000) |

**Example Request:**
```bash
curl -X GET "http://localhost:8000/api/legacy/global-shop/salespersons?limit=100"
```

**Response:**
```json
{
  "data": [
    {
      "SALESSION": "SP001",
      "NAME": "John Smith",
      "COMMISSION": 0.05
    }
  ],
  "summary": {
    "total": 1,
    "query": "SELECT TOP 100 * FROM V_SALESPERSONS",
    "response_time_ms": 287,
    "source": "Global Shop (Pervasive SQL)",
    "table": "V_SALESPERSONS"
  }
}
```

---

#### Raw SQL Query (Admin)

```
POST /api/legacy/global-shop/query?sql=<query>
```

Execute a raw SQL query against Global Shop. Only SELECT queries are allowed.

**Example:**
```bash
curl -X POST "http://localhost:8000/api/legacy/global-shop/query?sql=SELECT%20TOP%2025%20*%20FROM%20prodline_mre"
```

---

### Core Components

#### PervasiveDBAnalyzer

**Location:** `app/services/pervasive_analyzer.py`

Primary interface to the bridge API. Responsibilities:

| Method | Purpose |
|--------|---------|
| `_send_query()` | Low-level POST to bridge endpoint |
| `get_all_tables()` | Discovers user tables via `X$File` system table |
| `get_table_schema()` | Introspects columns via `X$Field` join |
| `get_row_count()` | Returns row count for a table |
| `run_full_analysis()` | Synchronous full database sweep |
| `analyze_tables_streaming()` | Generator for live UX with progress updates |

**Response Normalization:**
- Trims fixed-width strings
- Handles alias quirks (e.g., `COUNT(*)` → `EXPR_1`)
- Filters out `X$` system tables
- Converts types for clean Python data structures

#### StreamingAnalysisManager

**Location:** `app/services/streaming_analysis_manager.py`

Manages analysis runs with persistence. Features:

- **Resumable runs** via checkpoints
- **Supabase persistence** for discovered tables and analysis results
- **SSE streaming** for real-time progress updates
- **Aggregate statistics** tracking

#### Analysis Endpoints

| Endpoint | Purpose |
|----------|---------|
| `GET /api/test-env` | Verify API key is loaded |
| `GET /api/test-tables` | Confirm bridge returns data |
| `GET /api/debug-table/<table>` | Diagnose table-specific failures |
| `GET /api/stream-analysis` | SSE stream for live analysis |

---

### Connection Health & Metrics

#### Health Check Endpoints

```bash
# Verify environment configuration
GET /api/test-env

# Verify bridge connectivity and data access  
GET /api/test-tables
```

#### Key Health Indicators

| Metric | Healthy | Warning | Critical |
|--------|---------|---------|----------|
| Bridge Response Time | < 2s | 2-5s | > 5s or timeout |
| API Key Status | Present | - | Missing |
| Bridge Reachability | 200 OK | - | 502/timeout |
| Tables Discovered | > 0 | - | 0 (after init) |

#### Monitoring Checklist

- [ ] `PERVASIVE_API_KEY` environment variable set
- [ ] Bridge endpoint responding (`https://bridge-api.kaiville.io/query`)
- [ ] Cloudflare tunnel active (on-prem)
- [ ] Local bridge service running (on-prem Windows)
- [ ] Pervasive database accessible (on-prem)

#### Common Response Codes

| Code | Meaning | Action |
|------|---------|--------|
| 200 | Success | - |
| 401 | Invalid API key | Verify `PERVASIVE_API_KEY` |
| 502 | Bridge unreachable | Check Cloudflare tunnel / on-prem service |
| 504 | Gateway timeout | Check on-prem network / database load |

---

### Testing & Diagnostics

#### Quick Environment Verification

After setting `PERVASIVE_API_KEY`, hit `/api/test-env` to confirm credentials are loaded.

#### Postman Test

1. **Method:** `POST`
2. **URL:** `https://bridge-api.kaiville.io/query`
3. **Headers:**
   - `Content-Type: application/json`
   - `X-API-Key: <your PERVASIVE_API_KEY>`
4. **Body (raw JSON):**
   ```json
   {
     "sql": "SELECT TOP 25 * FROM prodline_mre"
   }
   ```

#### cURL Test

```bash
curl -X POST https://bridge-api.kaiville.io/query \
  -H "Content-Type: application/json" \
  -H "X-API-Key: <your PERVASIVE_API_KEY>" \
  -d '{"sql":"SELECT TOP 25 * FROM prodline_mre"}'
```

#### Smoke Test Script

**Location:** `scripts/test_simple_query.py`

Standalone script for verifying connectivity outside the application:

```bash
PERVASIVE_API_KEY=<key> python scripts/test_simple_query.py
```

#### Debug Endpoint

For table-specific issues, use the debug endpoint which tries multiple quoting strategies:

```
GET /api/debug-table/<table_name>
```

Returns raw SQL and responses for troubleshooting.

---

### Troubleshooting

#### Common Issues

| Symptom | Likely Cause | Solution |
|---------|--------------|----------|
| "API key not found" | Missing `PERVASIVE_API_KEY` | Set environment variable |
| 401 Unauthorized | Invalid or expired API key | Verify key, check for whitespace |
| 502 Bad Gateway | Cloudflare tunnel down | Check on-prem `cloudflared` service |
| Timeout on queries | Database overloaded or network issues | Check on-prem resources |
| Empty results | Table doesn't exist or wrong case | Use `/api/debug-table` to test quoting |
| `EXPR_1` in results | Alias normalization needed | Handled by analyzer; check column mappings |

#### Checklist: No Connection

1. **Verify API key has no hidden whitespace**
   - Copy fresh from source, strip trailing spaces
   
2. **Test bridge directly via cURL**
   ```bash
   curl -X POST https://bridge-api.kaiville.io/query \
     -H "Content-Type: application/json" \
     -H "X-API-Key: $PERVASIVE_API_KEY" \
     -d '{"sql":"SELECT 1"}'
   ```

3. **Check Cloudflare tunnel status** (on-prem)
   ```bash
   systemctl status cloudflared  # Linux
   # or check Windows Services for cloudflared
   ```

4. **Verify local bridge service** (on-prem Windows)
   - Check Windows Services
   - Review bridge service logs

5. **Test Pervasive connectivity** (on-prem)
   - Use Pervasive Control Center
   - Verify ODBC DSN configuration

#### Escalation Path

1. **L1:** Verify environment variables and run `/api/test-env`
2. **L2:** Test bridge directly via cURL/Postman
3. **L3:** Check on-prem Cloudflare tunnel and bridge service
4. **L4:** Verify Pervasive database and ODBC configuration

---

## Sunset Plan

As Circle Brands migrates to Syteline 10, this connector will be deprecated:

| Phase | Timeline | Actions |
|-------|----------|---------|
| Active | Months 1-6 | Full operation, monitoring |
| Parallel | Months 6-8 | Both systems active, validation |
| Wind-down | Months 8-10 | Read-only access, data verification |
| Decommission | Month 10+ | Remove connector, archive documentation |

---

## Appendix

### File References

| File | Purpose |
|------|---------|
| `app/services/pervasive_analyzer.py` | Core bridge API wrapper |
| `app/services/streaming_analysis_manager.py` | Supabase-backed analysis persistence |
| `app/routes/analysis.py` | HTTP endpoints for analysis and diagnostics |
| `scripts/test_simple_query.py` | Standalone connectivity test |

### Related Documentation

- [Cloudflare Tunnel Setup](https://developers.cloudflare.com/cloudflare-one/connections/connect-apps/)
- [Pervasive PSQL Documentation](https://www.pervasive.com/database/Home/Products/PSQLv13)


