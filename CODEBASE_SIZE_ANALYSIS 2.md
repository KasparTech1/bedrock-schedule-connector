# Codebase Size Analysis & God File Evaluation

**Generated:** 2025-01-27

## Executive Summary

Total source code: ~24,600 lines (excluding dependencies)

**God Files Identified:** 1 critical, 3 moderate candidates

---

## Critical God File (Needs Refactoring)

### 1. `src/kai_erp/adapters/syteline10_cloud/scheduler.py` - **1,447 lines** ⚠️

**Status:** **CRITICAL** - This is a true God file violating Single Responsibility Principle

**Current Structure:**
- **9 dataclasses** (JobOperation, Job, ScheduleOverview, Customer, CustomerSearchResult, OpenOrderLine, FlowOptimizerResult, OrderAvailabilityLine, OrderAvailabilityResult)
- **1 massive class** (BedrockScheduler) with **8+ major methods**:
  - Schedule management (4 methods)
  - Customer search (2 methods)
  - Flow optimizer (1 method)
  - Order availability (1 method)
  - Utility helpers (6 methods)

**Problems:**
1. **Multiple responsibilities:** Schedule, customers, orders, flow optimization all in one class
2. **Hard to test:** Tightly coupled functionality
3. **Hard to maintain:** Changes in one area affect others
4. **Difficult to extend:** Adding new features requires modifying the God class

**Recommended Refactoring:**

```
syteline10_cloud/
├── models/
│   ├── __init__.py
│   ├── schedule.py          # JobOperation, Job, ScheduleOverview
│   ├── customers.py          # Customer, CustomerSearchResult
│   └── orders.py            # OpenOrderLine, FlowOptimizerResult, OrderAvailabilityLine, OrderAvailabilityResult
├── services/
│   ├── __init__.py
│   ├── schedule_service.py   # Schedule-related methods (~300 lines)
│   ├── customer_service.py  # Customer search methods (~200 lines)
│   ├── flow_optimizer_service.py  # Flow optimizer methods (~300 lines)
│   └── order_availability_service.py  # Order availability methods (~400 lines)
├── utils.py                 # _parse_bed_type, _parse_syteline_date, etc. (~150 lines)
└── scheduler.py             # Thin facade/coordinator (~100 lines)
```

**Benefits:**
- Each service has single responsibility
- Easier to test in isolation
- Better code organization
- Easier to add new features
- Reduced merge conflicts

---

## Moderate Candidates (Consider Refactoring)

### 2. `client/src/pages/BedrockOrderAvailability.tsx` - **961 lines**

**Status:** Large but manageable - could benefit from component extraction

**Current Structure:**
- Main component with complex state management
- Multiple sub-components defined inline:
  - `CoverageBadge`
  - `StatCard`
  - `AllocationCard`
  - `AnatomyView` (large, ~200 lines)
  - `exportToCSV` function

**Recommendation:**
Extract components to separate files:

```
client/src/pages/BedrockOrderAvailability/
├── index.tsx                    # Main component (~400 lines)
├── components/
│   ├── CoverageBadge.tsx
│   ├── StatCard.tsx
│   ├── AllocationCard.tsx
│   └── AnatomyView.tsx          # Large component (~200 lines)
├── hooks/
│   └── useOrderAvailability.ts  # Data fetching logic
└── utils.ts                     # exportToCSV function
```

**Priority:** Medium - improves maintainability but not critical

---

### 3. `client/src/pages/admin/ConnectorBuilder.tsx` - **930 lines**

**Status:** Acceptable - Single cohesive form builder

**Analysis:**
- Well-organized tabbed form
- Clear separation of concerns (Identity, Data Sources, Join SQL, Tools)
- Complex but cohesive functionality

**Recommendation:** 
- Keep as-is for now
- Consider extracting form sections if it grows beyond 1,200 lines
- Could extract IDO/Property/Tool management to custom hooks

**Priority:** Low - not a God file, just a large form

---

### 4. `src/kai_erp/api/bedrock_routes.py` - **632 lines**

**Status:** Moderate - Could be split by feature area

**Current Structure:**
- Schedule endpoints (~150 lines)
- Customer endpoints (~100 lines)
- Flow optimizer endpoints (~200 lines)
- Order availability endpoints (~180 lines)

**Recommendation:**
Split into feature-based route modules:

```
api/
├── bedrock_routes.py           # Main router (~50 lines)
└── bedrock/
    ├── __init__.py
    ├── schedule_routes.py      # Schedule endpoints
    ├── customer_routes.py      # Customer endpoints
    ├── flow_optimizer_routes.py  # Flow optimizer endpoints
    └── order_availability_routes.py  # Order availability endpoints
```

**Priority:** Medium - improves organization but not critical

---

## Other Large Files (Acceptable)

### Files 500-600 lines:
- `client/src/pages/LegacyConnectors.tsx` (614) - Acceptable for a page component
- `client/src/lib/api.ts` (601) - API client, acceptable
- `client/src/pages/APISettings.tsx` (600) - Acceptable
- `src/kai_erp/connectors/order_availability.py` (570) - Acceptable
- `src/kai_erp/api/public_api.py` (569) - Acceptable
- `src/kai_erp/core/metrics.py` (556) - Acceptable
- `client/src/pages/BedrockFlowOptimizer.tsx` (553) - Acceptable

**Note:** Files in the 500-600 line range are generally acceptable, especially for:
- Page components with complex UI
- API clients
- Core business logic modules

---

## Recommendations Priority

### 🔴 High Priority (Do First)
1. **Refactor `scheduler.py` (1,447 lines)** - Split into models, services, and utils
   - Impact: High - improves maintainability significantly
   - Effort: Medium (2-3 days)
   - Risk: Low - well-defined boundaries

### 🟡 Medium Priority (Consider Soon)
2. **Extract components from `BedrockOrderAvailability.tsx`**
   - Impact: Medium - improves code organization
   - Effort: Low (1 day)
   - Risk: Very Low

3. **Split `bedrock_routes.py` by feature**
   - Impact: Medium - better organization
   - Effort: Low (1 day)
   - Risk: Very Low

### 🟢 Low Priority (Nice to Have)
4. **Monitor `ConnectorBuilder.tsx`** - Only refactor if it grows beyond 1,200 lines

---

## Code Quality Metrics

### File Size Distribution
- **> 1000 lines:** 1 file (God file)
- **500-1000 lines:** 7 files (acceptable to large)
- **300-500 lines:** 15 files (good size)
- **< 300 lines:** Most files (ideal)

### Best Practices
- **Ideal file size:** 200-400 lines
- **Acceptable:** Up to 600 lines for cohesive modules
- **Warning:** 600-1000 lines - consider splitting
- **God file:** > 1000 lines - should be refactored

---

## Refactoring Strategy

### Phase 1: Critical (Week 1)
1. Extract models from `scheduler.py` → `models/` directory
2. Extract utility functions → `utils.py`
3. Create service classes for each major feature area
4. Update imports and tests

### Phase 2: Moderate (Week 2)
1. Extract components from `BedrockOrderAvailability.tsx`
2. Split `bedrock_routes.py` by feature

### Phase 3: Polish (Week 3)
1. Review and optimize extracted code
2. Update documentation
3. Add integration tests

---

## Conclusion

**Main Issue:** `scheduler.py` is a true God file that should be refactored into a service-oriented architecture.

**Overall Health:** Good - only 1 critical God file, rest are manageable.

**Action Items:**
1. ✅ Create refactoring plan for `scheduler.py`
2. ⏳ Schedule refactoring sprint
3. ⏳ Extract components from large React files
4. ⏳ Split API routes by feature

