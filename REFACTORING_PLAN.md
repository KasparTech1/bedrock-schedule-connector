# Refactoring Plan: scheduler.py God File

**Target:** `src/kai_erp/adapters/syteline10_cloud/scheduler.py` (1,447 lines)

**Goal:** Split into maintainable, testable modules while maintaining backward compatibility
**Branch:** `refactor/scheduler-god-file` (create before changes)

---

## Phase 1: Preparation & Analysis (Day 1)

### Step 1.1: Create Test Coverage Baseline (smoke)
```bash
# Quick smoke (fast)
pytest tests/test_api/test_endpoints.py -k bedrock -v || true

# Broader (optional if fast enough)
pytest tests/ -k bedrock -v || true
```

**Action Items:**
- [ ] Create branch `refactor/scheduler-god-file`
- [ ] Document all current test cases
- [ ] Identify edge cases
- [ ] Note any integration test dependencies

### Step 1.2: Map Dependencies
**Current imports of BedrockScheduler:**
- `src/kai_erp/api/bedrock_routes.py`
- `src/kai_erp/api/public_api.py`
- `src/kai_erp/mongoose/__init__.py`
- `src/kai_erp/adapters/syteline10_cloud/__init__.py`
- Test scripts

**Action Items:**
- [x] Document all import locations
- [ ] Verify no dynamic imports
- [ ] Check for monkey-patching in tests
- [ ] Confirm no direct relative imports outside adapter package

---

## Phase 2: Extract Models (Day 1-2)

### Step 2.1: Create Models Directory Structure
```
src/kai_erp/adapters/syteline10_cloud/
├── models/
│   ├── __init__.py
│   ├── schedule.py      # JobOperation, Job, ScheduleOverview
│   ├── customers.py     # Customer, CustomerSearchResult
│   └── orders.py        # OpenOrderLine, FlowOptimizerResult, OrderAvailabilityLine, OrderAvailabilityResult
```

### Step 2.2: Extract Schedule Models
**File:** `models/schedule.py`
```python
"""Schedule-related data models."""
from dataclasses import dataclass
from datetime import datetime
from typing import Optional

@dataclass
class JobOperation:
    """A single operation within a job."""
    job: str
    suffix: int
    operation_num: int
    work_center: str
    qty_complete: float
    qty_scrapped: float

@dataclass
class Job:
    """A manufacturing job with its operations."""
    job: str
    suffix: int
    item: str
    item_description: str
    qty_released: float
    qty_complete: float
    status: str
    customer_num: Optional[str]
    customer_name: Optional[str]
    operations: list[JobOperation]
    
    @property
    def pct_complete(self) -> float:
        """Calculate percent complete."""
        if self.qty_released <= 0:
            return 0.0
        return round((self.qty_complete / self.qty_released) * 100, 1)
    
    @property
    def is_complete(self) -> bool:
        """Check if job is fully complete."""
        return self.qty_complete >= self.qty_released

@dataclass  
class ScheduleOverview:
    """Overview of production schedule."""
    total_jobs: int
    active_jobs: int
    jobs_by_status: dict[str, int]
    work_centers: list[str]
    jobs: list[Job]
    fetched_at: datetime
```

### Step 2.3: Extract Customer Models
**File:** `models/customers.py`
```python
"""Customer-related data models."""
from dataclasses import dataclass
from datetime import datetime
from typing import Optional

@dataclass
class Customer:
    """A Bedrock customer record."""
    cust_num: str
    name: str
    addr1: Optional[str]
    addr2: Optional[str]
    city: Optional[str]
    state: Optional[str]
    zip_code: Optional[str]
    country: Optional[str]
    phone: Optional[str]
    contact: Optional[str]
    email: Optional[str]
    cust_type: Optional[str]
    status: str  # A=Active, I=Inactive

@dataclass
class CustomerSearchResult:
    """Result of a customer search."""
    total_count: int
    customers: list[Customer]
    fetched_at: datetime
```

### Step 2.4: Extract Order Models
**File:** `models/orders.py`
```python
"""Order-related data models."""
from dataclasses import dataclass
from datetime import datetime
from typing import Optional

@dataclass
class OpenOrderLine:
    """A single open order line for Flow Optimizer export."""
    # ... (all fields from original)
    pass

@dataclass
class FlowOptimizerResult:
    """Result of flow optimizer data fetch."""
    # ... (all fields from original)
    pass

@dataclass
class OrderAvailabilityLine:
    """A customer order line with availability and allocation information."""
    # ... (all fields from original)
    pass

@dataclass
class OrderAvailabilityResult:
    """Result of order availability fetch."""
    # ... (all fields from original)
    pass
```

### Step 2.5: Update Models __init__.py
**File:** `models/__init__.py`
```python
"""Data models for Bedrock Scheduler."""
from .schedule import JobOperation, Job, ScheduleOverview
from .customers import Customer, CustomerSearchResult
from .orders import (
    OpenOrderLine,
    FlowOptimizerResult,
    OrderAvailabilityLine,
    OrderAvailabilityResult,
)

__all__ = [
    # Schedule
    "JobOperation",
    "Job",
    "ScheduleOverview",
    # Customers
    "Customer",
    "CustomerSearchResult",
    # Orders
    "OpenOrderLine",
    "FlowOptimizerResult",
    "OrderAvailabilityLine",
    "OrderAvailabilityResult",
]
```

**Action Items:**
- [ ] Create models directory
- [ ] Extract all dataclasses
- [ ] Update imports in scheduler.py (temporary)
- [ ] Run quick smoke: `pytest tests/test_api/test_endpoints.py -k bedrock -v`
- [ ] Commit checkpoint: “refactor: extract scheduler models”

---

## Phase 3: Extract Utilities (Day 2)

### Step 3.1: Create Utils Module
**File:** `utils.py`
```python
"""Utility functions for Bedrock Scheduler."""
from typing import Any
from datetime import date, datetime

def clean_str(value: Any) -> str:
    """Clean string value - strip whitespace."""
    if value is None:
        return ""
    return str(value).strip()

def parse_float(value: Any) -> float:
    """Parse float value safely."""
    if value is None:
        return 0.0
    try:
        return float(value)
    except (ValueError, TypeError):
        return 0.0

def parse_syteline_date(date_str: str) -> date | None:
    """
    Parse SyteLine date format.
    
    SyteLine dates can be in various formats:
    - "20251022 0" (YYYYMMDD with suffix)
    - "2025-10-22"
    - "2025-10-22T00:00:00"
    - "10/22/2025"
    """
    if not date_str:
        return None
    
    date_str = date_str.strip()
    
    # Handle "YYYYMMDD 0" format (SyteLine standard)
    if " " in date_str and len(date_str.split()[0]) == 8:
        try:
            return datetime.strptime(date_str.split()[0], "%Y%m%d").date()
        except ValueError:
            pass
    
    # Try various formats
    for fmt in ["%Y%m%d", "%Y-%m-%d", "%Y-%m-%dT%H:%M:%S", "%m/%d/%Y"]:
        try:
            return datetime.strptime(date_str[:10], fmt).date()
        except ValueError:
            continue
    
    return None

def format_date(date_str: str) -> str | None:
    """Format a SyteLine date string to ISO format."""
    parsed = parse_syteline_date(date_str)
    return parsed.isoformat() if parsed else None

def parse_bed_length(drawing: str) -> int:
    """Parse bed length from drawing number (first 1-2 digits)."""
    if not drawing:
        return 0
    
    # Try to extract leading digits
    digits = ""
    for char in drawing:
        if char.isdigit():
            digits += char
        else:
            break
    
    if digits and len(digits) <= 2:
        try:
            return int(digits)
        except ValueError:
            pass
    
    return 0

def parse_bed_type(model: str) -> str:
    """
    Parse bed type from model/drawing number or item code.
    
    Examples:
    - "14G-7" -> Granite (ends with G before dash)
    - "23D" -> Diamond (ends with D)
    - "14GP-7" or "6GP" -> Granite+ (contains GP)
    - "8M-9" -> Marble (ends with M before dash)
    """
    if not model:
        return "Other"
    
    model_upper = model.upper().strip()
    
    # Check for Granite+ first (GP patterns - must check before G)
    if "GP" in model_upper:
        return "Granite+"
    
    # Get the prefix before first dash (e.g., "14G" from "14G-7")
    prefix = model_upper.split("-")[0] if "-" in model_upper else model_upper
    
    # Remove any trailing numbers from prefix for items like "23D"
    stripped_prefix = prefix.rstrip("0123456789")
    if not stripped_prefix:
        stripped_prefix = prefix
    
    # Check last character of prefix
    last_char = stripped_prefix[-1] if stripped_prefix else ""
    
    if last_char == "D":
        return "Diamond"
    elif last_char == "G":
        return "Granite"
    elif last_char == "M":
        return "Marble"
    elif last_char == "L":
        return "Limestone"
    elif last_char == "P":
        return "Platform"
    elif last_char == "O":
        return "Onyx"
    elif last_char == "S":
        return "Slate"
    elif "QU" in model_upper or (prefix.startswith("Q") and len(prefix) > 1):
        return "Quad"
    
    return "Other"
```

**Action Items:**
- [ ] Extract all utility functions
- [ ] Update scheduler.py to use utils
- [ ] Run quick smoke: `pytest tests/test_api/test_endpoints.py -k bedrock -v`
- [ ] Commit checkpoint: “refactor: extract scheduler utils”

---

## Phase 4: Extract Services (Day 2-3)

### Step 4.1: Create Services Directory
```
src/kai_erp/adapters/syteline10_cloud/
├── services/
│   ├── __init__.py
│   ├── schedule_service.py
│   ├── customer_service.py
│   ├── flow_optimizer_service.py
│   └── order_availability_service.py
```

### Step 4.2: Extract Schedule Service
**File:** `services/schedule_service.py` (~300 lines)
```python
"""Schedule management service."""
from typing import Optional
from datetime import datetime, timezone

import structlog

from ..mongoose_client import MongooseClient, MongooseConfig
from ..models.schedule import JobOperation, Job, ScheduleOverview
from ..utils import clean_str, parse_float

logger = structlog.get_logger(__name__)


class ScheduleService:
    """Service for managing production schedules."""
    
    def __init__(self, config: MongooseConfig):
        self.config = config
    
    async def get_schedule_overview(
        self,
        include_complete: bool = False,
        limit: int = 100
    ) -> ScheduleOverview:
        """Get overview of current production schedule."""
        # Move implementation from BedrockScheduler.get_schedule_overview
        pass
    
    async def get_jobs_at_work_center(
        self,
        work_center: str,
        include_complete: bool = False,
        limit: int = 50
    ) -> list[Job]:
        """Get jobs with operations at a specific work center."""
        # Move implementation
        pass
    
    async def get_job_details(
        self,
        job_number: str,
        suffix: int = 0
    ) -> Optional[Job]:
        """Get detailed information for a specific job."""
        # Move implementation
        pass
    
    async def get_work_center_queue(
        self,
        work_center: str,
        limit: int = 50
    ) -> list[dict]:
        """Get the queue of operations at a work center."""
        # Move implementation
        pass
```

### Step 4.3: Extract Customer Service
**File:** `services/customer_service.py` (~200 lines)
```python
"""Customer search service."""
from typing import Optional
from datetime import datetime, timezone

import structlog

from ..mongoose_client import MongooseClient, MongooseConfig
from ..models.customers import Customer, CustomerSearchResult
from ..utils import clean_str

logger = structlog.get_logger(__name__)


class CustomerService:
    """Service for customer search and management."""
    
    def __init__(self, config: MongooseConfig):
        self.config = config
    
    async def search_customers(
        self,
        search_term: Optional[str] = None,
        customer_number: Optional[str] = None,
        city: Optional[str] = None,
        state: Optional[str] = None,
        status: Optional[str] = None,
        limit: int = 50
    ) -> CustomerSearchResult:
        """Search for Bedrock customers."""
        # Move implementation from BedrockScheduler.search_customers
        pass
    
    async def get_customer(self, customer_number: str) -> Optional[Customer]:
        """Get a specific customer by number."""
        # Move implementation
        pass
```

### Step 4.4: Extract Flow Optimizer Service
**File:** `services/flow_optimizer_service.py` (~300 lines)
```python
"""Flow optimizer service."""
from datetime import datetime, timezone

import structlog

from ..mongoose_client import MongooseConfig
from ..models.orders import OpenOrderLine, FlowOptimizerResult
from ..utils import clean_str, parse_float, parse_syteline_date, format_date, parse_bed_type, parse_bed_length

logger = structlog.get_logger(__name__)


class FlowOptimizerService:
    """Service for flow optimizer data."""
    
    def __init__(self, config: MongooseConfig):
        self.config = config
    
    async def get_open_orders(self, limit: int = 500) -> FlowOptimizerResult:
        """Get open orders with WIP data for Flow Optimizer."""
        # Move implementation from BedrockScheduler.get_open_orders
        pass
```

### Step 4.5: Extract Order Availability Service
**File:** `services/order_availability_service.py` (~400 lines)
```python
"""Order availability service."""
from typing import Optional
from datetime import date, datetime, timezone, timedelta

import structlog

from ..mongoose_client import MongooseConfig
from ..models.orders import OrderAvailabilityLine, OrderAvailabilityResult
from ..utils import clean_str, parse_float, parse_syteline_date, format_date
from ...core.metrics import get_metrics_store

logger = structlog.get_logger(__name__)


class OrderAvailabilityService:
    """Service for order availability and allocation."""
    
    def __init__(self, config: MongooseConfig):
        self.config = config
    
    async def get_order_availability(
        self,
        customer: Optional[str] = None,
        item: Optional[str] = None,
        limit: int = 500,
        track_metrics: bool = True,
    ) -> OrderAvailabilityResult:
        """Get order availability with inventory allocation analysis."""
        # Move implementation from BedrockScheduler.get_order_availability
        pass
```

### Step 4.6: Update Services __init__.py
**File:** `services/__init__.py`
```python
"""Services for Bedrock Scheduler."""
from .schedule_service import ScheduleService
from .customer_service import CustomerService
from .flow_optimizer_service import FlowOptimizerService
from .order_availability_service import OrderAvailabilityService

__all__ = [
    "ScheduleService",
    "CustomerService",
    "FlowOptimizerService",
    "OrderAvailabilityService",
]
```

**Action Items:**
- [ ] Create services directory
- [ ] Extract each service class (one at a time: schedule → customer → flow → order availability)
- [ ] Move method implementations
- [ ] Update imports to use utils
- [ ] After each service extraction, run smoke: `pytest tests/test_api/test_endpoints.py -k bedrock -v`
- [ ] After all services, run: `pytest tests/test_api -k bedrock -v`
- [ ] Commit checkpoint: “refactor: extract scheduler services”

---

## Phase 5: Create Facade (Day 3)

### Step 5.1: Refactor BedrockScheduler as Facade
**File:** `scheduler.py` (new, ~150 lines)
```python
"""
Bedrock Scheduler Connector
===========================

Production schedule visibility for Bedrock Truck Beds manufacturing operations.

This is a facade that delegates to specialized services:
- ScheduleService: Production schedule management
- CustomerService: Customer search
- FlowOptimizerService: Flow optimizer data
- OrderAvailabilityService: Order availability and allocation
"""

from __future__ import annotations

from typing import Optional

from .mongoose_client import MongooseConfig
from .models import (
    Job,
    JobOperation,
    ScheduleOverview,
    Customer,
    CustomerSearchResult,
    OpenOrderLine,
    FlowOptimizerResult,
    OrderAvailabilityLine,
    OrderAvailabilityResult,
)
from .services import (
    ScheduleService,
    CustomerService,
    FlowOptimizerService,
    OrderAvailabilityService,
)


class BedrockScheduler:
    """
    Bedrock production schedule connector (Facade).
    
    This class provides a unified interface for all Bedrock scheduler operations.
    It delegates to specialized services for each feature area.
    
    Usage:
        config = MongooseConfig.bedrock_hfa()
        scheduler = BedrockScheduler(config)
        
        # Get schedule overview
        overview = await scheduler.get_schedule_overview()
        
        # Search customers
        customers = await scheduler.search_customers(search_term="Acme")
        
        # Get order availability
        availability = await scheduler.get_order_availability()
    """
    
    def __init__(self, config: Optional[MongooseConfig] = None):
        """
        Initialize scheduler.
        
        Args:
            config: Mongoose configuration. If None, uses bedrock_tbe() default.
        """
        self.config = config or MongooseConfig.bedrock_tbe()
        
        # Initialize services
        self._schedule_service = ScheduleService(self.config)
        self._customer_service = CustomerService(self.config)
        self._flow_optimizer_service = FlowOptimizerService(self.config)
        self._order_availability_service = OrderAvailabilityService(self.config)
    
    # Schedule methods (delegate to ScheduleService)
    async def get_schedule_overview(
        self,
        include_complete: bool = False,
        limit: int = 100
    ) -> ScheduleOverview:
        """Get overview of current production schedule."""
        return await self._schedule_service.get_schedule_overview(
            include_complete=include_complete,
            limit=limit
        )
    
    async def get_jobs_at_work_center(
        self,
        work_center: str,
        include_complete: bool = False,
        limit: int = 50
    ) -> list[Job]:
        """Get jobs with operations at a specific work center."""
        return await self._schedule_service.get_jobs_at_work_center(
            work_center=work_center,
            include_complete=include_complete,
            limit=limit
        )
    
    async def get_job_details(
        self,
        job_number: str,
        suffix: int = 0
    ) -> Optional[Job]:
        """Get detailed information for a specific job."""
        return await self._schedule_service.get_job_details(
            job_number=job_number,
            suffix=suffix
        )
    
    async def get_work_center_queue(
        self,
        work_center: str,
        limit: int = 50
    ) -> list[dict]:
        """Get the queue of operations at a work center."""
        return await self._schedule_service.get_work_center_queue(
            work_center=work_center,
            limit=limit
        )
    
    # Customer methods (delegate to CustomerService)
    async def search_customers(
        self,
        search_term: Optional[str] = None,
        customer_number: Optional[str] = None,
        city: Optional[str] = None,
        state: Optional[str] = None,
        status: Optional[str] = None,
        limit: int = 50
    ) -> CustomerSearchResult:
        """Search for Bedrock customers."""
        return await self._customer_service.search_customers(
            search_term=search_term,
            customer_number=customer_number,
            city=city,
            state=state,
            status=status,
            limit=limit
        )
    
    async def get_customer(self, customer_number: str) -> Optional[Customer]:
        """Get a specific customer by number."""
        return await self._customer_service.get_customer(customer_number)
    
    # Flow optimizer methods (delegate to FlowOptimizerService)
    async def get_open_orders(self, limit: int = 500) -> FlowOptimizerResult:
        """Get open orders with WIP data for Flow Optimizer."""
        return await self._flow_optimizer_service.get_open_orders(limit=limit)
    
    # Order availability methods (delegate to OrderAvailabilityService)
    async def get_order_availability(
        self,
        customer: Optional[str] = None,
        item: Optional[str] = None,
        limit: int = 500,
        track_metrics: bool = True,
    ) -> OrderAvailabilityResult:
        """Get order availability with inventory allocation analysis."""
        return await self._order_availability_service.get_order_availability(
            customer=customer,
            item=item,
            limit=limit,
            track_metrics=track_metrics,
        )
```

**Action Items:**
- [ ] Replace scheduler.py with facade
- [ ] Verify all methods delegate correctly
- [ ] Update any direct imports if needed (should be none)
- [ ] Run broader tests: `pytest tests/test_api -k bedrock -v`
- [ ] Commit checkpoint: “refactor: scheduler facade”
- [ ] Check backward compatibility (existing imports still valid)

---

## Phase 6: Update Imports & Exports (Day 3)

### Step 6.1: Update __init__.py
**File:** `adapters/syteline10_cloud/__init__.py`
```python
"""Bedrock Scheduler adapter for SyteLine 10 Cloud."""
from .scheduler import BedrockScheduler
from .mongoose_client import MongooseClient, MongooseConfig

# Export models for advanced usage
from .models import (
    JobOperation,
    Job,
    ScheduleOverview,
    Customer,
    CustomerSearchResult,
    OpenOrderLine,
    FlowOptimizerResult,
    OrderAvailabilityLine,
    OrderAvailabilityResult,
)

# Export services for direct usage (optional)
from .services import (
    ScheduleService,
    CustomerService,
    FlowOptimizerService,
    OrderAvailabilityService,
)

__all__ = [
    # Main facade
    "BedrockScheduler",
    # Client
    "MongooseClient",
    "MongooseConfig",
    # Models
    "JobOperation",
    "Job",
    "ScheduleOverview",
    "Customer",
    "CustomerSearchResult",
    "OpenOrderLine",
    "FlowOptimizerResult",
    "OrderAvailabilityLine",
    "OrderAvailabilityResult",
    # Services (for advanced usage)
    "ScheduleService",
    "CustomerService",
    "FlowOptimizerService",
    "OrderAvailabilityService",
]
```

**Action Items:**
- [ ] Update __init__.py exports
- [ ] Verify all existing imports still work
- [ ] Test backward compatibility (import paths in api/public_api/legacy scripts)
- [ ] Commit checkpoint: “chore: update scheduler exports”

---

## Phase 7: Testing & Validation (Day 4)

### Step 7.1: Run Full Test Suite
```bash
# Run all tests
pytest tests/ -v

# Run with coverage
pytest tests/ --cov=src/kai_erp/adapters/syteline10_cloud --cov-report=html

# Run integration tests
pytest tests/test_api/ -v

# Run specific scheduler tests
pytest tests/ -k scheduler -v

# Optional perf sanity (before/after comparison if captured)
python scripts/test_bedrock_scheduler.py || true
```

### Step 7.2: Manual Testing Checklist
- [ ] Schedule overview endpoint works
- [ ] Customer search endpoint works
- [ ] Order availability endpoint works
- [ ] Flow optimizer endpoint works
- [ ] All existing API calls succeed
- [ ] No performance regression
- [ ] Error handling works correctly

### Step 7.3: Integration Testing
- [ ] Test with real Bedrock API
- [ ] Verify metrics tracking still works
- [ ] Check logging output
- [ ] Validate response formats

**Action Items:**
- [ ] Run all tests
- [ ] Fix any broken tests
- [ ] Document any breaking changes (should be none)
- [ ] Update test coverage
- [ ] Commit checkpoint: “test: verify scheduler refactor”

---

## Phase 8: Documentation & Cleanup (Day 4)

### Step 8.1: Update Documentation
- [ ] Update docstrings in new modules
- [ ] Add module-level documentation
- [ ] Update README if needed
- [ ] Document new structure
- [ ] Add short migration note: “Existing imports remain valid; services are optional”

### Step 8.2: Code Review
- [ ] Review each service for consistency
- [ ] Check for code duplication
- [ ] Verify error handling
- [ ] Ensure logging is consistent

### Step 8.3: Final Cleanup
- [ ] Remove any temporary code
- [ ] Remove commented-out code
- [ ] Format code (black, isort)
- [ ] Run linters
- [ ] Final commit: “refactor: split scheduler into services”

---

## Final Structure

```
src/kai_erp/adapters/syteline10_cloud/
├── __init__.py                    # Exports (backward compatible)
├── scheduler.py                    # Facade (~150 lines) ⬇️ from 1,447
├── mongoose_client.py              # Existing
├── direct_client.py                # Existing
├── utils.py                        # Utility functions (~150 lines) ✨ NEW
├── models/
│   ├── __init__.py                 # Model exports
│   ├── schedule.py                 # Schedule models (~100 lines) ✨ NEW
│   ├── customers.py                # Customer models (~50 lines) ✨ NEW
│   └── orders.py                   # Order models (~200 lines) ✨ NEW
└── services/
    ├── __init__.py                 # Service exports
    ├── schedule_service.py         # Schedule service (~300 lines) ✨ NEW
    ├── customer_service.py        # Customer service (~200 lines) ✨ NEW
    ├── flow_optimizer_service.py   # Flow optimizer service (~300 lines) ✨ NEW
    └── order_availability_service.py # Order availability service (~400 lines) ✨ NEW
```

**Line Count Reduction:**
- Original: 1,447 lines in one file
- New: ~1,700 lines total, but organized into 9 focused modules
- Largest file: ~400 lines (order_availability_service.py)
- Average file size: ~190 lines ✅

---

## Migration Strategy

### Backward Compatibility
✅ **100% Backward Compatible**

All existing code will continue to work:
```python
# This still works exactly the same
from kai_erp.adapters.syteline10_cloud import BedrockScheduler

scheduler = BedrockScheduler(config)
overview = await scheduler.get_schedule_overview()
```

### Optional: Direct Service Usage
New code can optionally use services directly:
```python
# New: Direct service usage (optional)
from kai_erp.adapters.syteline10_cloud import ScheduleService

service = ScheduleService(config)
overview = await service.get_schedule_overview()
```

### Gradual Migration
- Phase 1-4: Extract code (no breaking changes)
- Phase 5: Replace facade (backward compatible)
- Phase 6: Update exports (backward compatible)
- Phase 7-8: Test and document

---

## Risk Mitigation

### Risks & Mitigations

1. **Risk:** Breaking existing code
   - **Mitigation:** Maintain facade pattern, 100% backward compatible

2. **Risk:** Performance regression
   - **Mitigation:** Same code, just reorganized. Run benchmarks before/after

3. **Risk:** Missing edge cases
   - **Mitigation:** Comprehensive test coverage, run all existing tests

4. **Risk:** Circular imports
   - **Mitigation:** Careful import structure, services don't import each other

5. **Risk:** Merge conflicts
   - **Mitigation:** Do refactoring in separate branch, merge after tests pass

---

## Success Criteria

✅ **Refactoring is successful when:**
1. All existing tests pass
2. No breaking changes to public API
3. Code is organized into logical modules
4. Each file is < 500 lines
5. Services are independently testable
6. Documentation is updated
7. No performance regression

---

## Timeline

**Total Estimated Time:** 4 days

- **Day 1:** Extract models and utils (Phases 2-3)
- **Day 2:** Extract services (Phase 4)
- **Day 3:** Create facade and update imports (Phases 5-6)
- **Day 4:** Testing and documentation (Phases 7-8)

**Buffer:** Add 1-2 days for unexpected issues

---

## Next Steps

1. ✅ Review this plan
2. ⏳ Create feature branch: `refactor/scheduler-god-file`
3. ⏳ Start with Phase 1 (Preparation)
4. ⏳ Execute phases sequentially
5. ⏳ Merge after all tests pass

---

## Questions to Consider

1. **Should we add type hints everywhere?** ✅ Yes, maintain existing style
2. **Should we add async context managers?** ✅ Keep existing patterns
3. **Should we add caching?** ⏸️ Defer to separate PR
4. **Should we add retry logic?** ⏸️ Defer to separate PR
5. **Should we add more unit tests?** ✅ Yes, as we extract services

---

## Notes

- This refactoring maintains 100% backward compatibility
- No changes to public API
- All existing code continues to work
- New structure enables better testing and maintenance
- Services can be used independently if needed

