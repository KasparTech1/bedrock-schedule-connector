# Mongoose REST API Credentials - Bedrock Connectors

> **Status:** ✅ WORKING  
> **Environment:** Training (TRN) - TBE2 Config (Bedrock Truck Beds)  
> **Verified:** December 11, 2025

---

## ION API Credentials (Working - Bedrock TBE2)

| Field | Value |
|-------|-------|
| **Tenant ID (ti)** | `DUU6QAFE74D2YDYW_TRN` |
| **Client ID (ci)** | `DUU6QAFE74D2YDYW_TRN~RKPRDN3Sen39SrXEHTtszZplRbjTOcB7W0lnibbG0T0` |
| **Client Secret (cs)** | `<REDACTED>` |
| **ION API URL (iu)** | `https://mingle-ionapi.inforcloudsuite.com` |
| **SSO URL (pu)** | `https://mingle-sso.inforcloudsuite.com:443/DUU6QAFE74D2YDYW_TRN/as/` |
| **Authorization Endpoint (oa)** | `authorization.oauth2` |
| **Token Endpoint (ot)** | `token.oauth2` |
| **Mongoose Config** | `DUU6QAFE74D2YDYW_TRN_TBE2` |
| **Logical ID** | `infor.ims.cp_myapp` |

### Service Account Keys

| Key | Value |
|-----|-------|
| **Service Account Access Key (saak)** | `<REDACTED>` |
| **Service Account Secret Key (sask)** | `<REDACTED>` |

---

## Full ION API JSON Credential File

```json
{
  "ti": "DUU6QAFE74D2YDYW_TRN",
  "ci": "DUU6QAFE74D2YDYW_TRN~RKPRDN3Sen39SrXEHTtszZplRbjTOcB7W0lnibbG0T0",
  "cs": "<REDACTED>",
  "iu": "https://mingle-ionapi.inforcloudsuite.com",
  "pu": "https://mingle-sso.inforcloudsuite.com:443/DUU6QAFE74D2YDYW_TRN/as/",
  "oa": "authorization.oauth2",
  "ot": "token.oauth2",
  "saak": "<REDACTED>",
  "sask": "<REDACTED>",
  "config": "DUU6QAFE74D2YDYW_TRN_TBE2",
  "logicalId": "infor.ims.cp_myapp"
}
```

---

## API Endpoints

### Base URL Construction

```
{iu}/{ti}/CSI/IDORequestService/ido/load/{IDO}
```

**Full Base URL:**
```
https://mingle-ionapi.inforcloudsuite.com/DUU6QAFE74D2YDYW_TRN/CSI/IDORequestService/ido/load/
```

### Token Endpoint (OAuth2)

```
{pu}{ot}
```

**Full Token URL:**
```
https://mingle-sso.inforcloudsuite.com:443/DUU6QAFE74D2YDYW_TRN/as/token.oauth2
```

---

## Example API Requests

### General GET Statement Format

```
{iu}/{ti}/CSI/IDORequestService/ido/load/{IDO}?properties={Properties}&recordcap={RecordCap}
```

### Example: Get SLItems (Items List)

```http
GET https://mingle-ionapi.inforcloudsuite.com/DUU6QAFE74D2YDYW_TRN/CSI/IDORequestService/ido/load/SLItems?properties=Item,Description&recordcap=10
```

**Query Parameters:**
- `properties` - Comma-separated list of fields to return
- `recordcap` - Maximum number of records to return

---

## OAuth2 Authentication Flow

### 1. Request Access Token

```http
POST https://mingle-sso.inforcloudsuite.com:443/DUU6QAFE74D2YDYW_TRN/as/token.oauth2
Content-Type: application/x-www-form-urlencoded

grant_type=password
&username={saak}
&password={sask}
&client_id={ci}
&client_secret={cs}
```

### 2. Use Token in API Requests

```http
GET {api_endpoint}
Authorization: Bearer {access_token}
```

---

## Granted IDO Permissions

**User:** `kai_conference@kasparcompanies.com`  
**Object Type:** IDO  
**Access Level:** Read Only

| # | IDO Name | Read Privilege | Write/Update |
|---|----------|----------------|--------------|
| 1 | `SLCoitems` | ✅ Granted | ❌ Revoked |
| 2 | `SLCos` | ✅ Granted | ❌ Revoked |
| 3 | `SLCustomers` | ✅ Granted | ❌ Revoked |
| 4 | `SLItems` | ✅ Granted | ❌ Revoked |
| 5 | `SLItemwhses` | ✅ Granted | ❌ Revoked |
| 6 | `SLJobRoutes` | ✅ Granted | ❌ Revoked |
| 7 | `SLJobs` | ✅ Granted | ❌ Revoked |

> **Note:** Delete, Edit, Execute, Insert, Bulk Update, and Update privileges are all **Revoked** for these IDOs. This is a read-only integration.

---

## Additional Environment Variables

These are configured in the Postman environment for testing:

| Variable | Value |
|----------|-------|
| **logicalId** | `infor.ims.cp_myapp` |
| **config** | `DUU6QAFE74D2YDYW_TRN_TBE` |
| **directIMSURL** | `https://localhost:28090/api/ion/messaging/service` |
| **directIMSTenant** | `INFOR` |

---

## IDO Reference

| IDO Name | Description | Common Properties |
|----------|-------------|-------------------|
| `SLItems` | Items/Products | `Item`, `Description`, `UM`, `ProductCode` |
| `SLItemwhses` | Item Warehouse Locations | `Item`, `Whse`, `QtyOnHand`, `QtyAllocated` |
| `SLJobs` | Job Orders | `Job`, `Suffix`, `Item`, `QtyComplete`, `JobDate` |
| `SLJobRoutes` | Job Routing/Operations | `Job`, `Suffix`, `OperNum`, `Wc`, `RunHrsT` |
| `SLCos` | Customer Orders | `CoNum`, `CustNum`, `OrderDate`, `Stat` |
| `SLCoitems` | Customer Order Line Items | `CoNum`, `CoLine`, `Item`, `QtyOrdered` |
| `SLCustomers` | Customer Master | `CustNum`, `Name`, `City`, `State` |

---

## ✅ Status: Working

**Verified:** December 11, 2025

All 7 IDOs returning data successfully:
- ✅ SLJobs
- ✅ SLJobRoutes  
- ✅ SLItems
- ✅ SLItemwhses
- ✅ SLCustomers
- ✅ SLCos
- ✅ SLCoitems

**Still needed for full scheduler:**
- ❓ SLJrtSchs (schedule dates)
- ❓ SLWcs (work center descriptions)

---

## Notes

- **Environment:** This is a TRAINING environment (`_TRN` suffix)
- **Credential File:** `KAI Labs.ionapi` - stored securely
- **Documentation Reference:** See `docs/DEMO_POSTMAN/Mongoose REST Service.docx` for additional details

---

## Related Files

- `.env` - Environment variables (add credentials here for runtime use)
- `src/kai_erp/adapters/syteline10_cloud/mongoose_client.py` - SyteLine 10 Cloud (ION/Mongoose) client
- `src/kai_erp/adapters/syteline10_cloud/direct_client.py` - SyteLine 10 direct client (deprecated fallback)
- `src/kai_erp/connectors/bedrock_ops.py` - Bedrock operations connector
