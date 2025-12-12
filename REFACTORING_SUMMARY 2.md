# Refactoring Summary: scheduler.py

## Quick Overview

**Problem:** 1,447-line God file with multiple responsibilities  
**Solution:** Split into focused modules with facade pattern  
**Result:** 9 focused modules, largest file ~400 lines  
**Compatibility:** 100% backward compatible  
**Branch:** `refactor/scheduler-god-file` with checkpoint commits each phase

---

## Before & After

### Before
```
scheduler.py (1,447 lines)
├── 9 dataclasses
├── 1 massive class (BedrockScheduler)
│   ├── Schedule methods (4)
│   ├── Customer methods (2)
│   ├── Flow optimizer methods (1)
│   ├── Order availability methods (1)
│   └── Utility methods (6)
```

### After
```
syteline10_cloud/
├── scheduler.py (150 lines) - Facade
├── utils.py (150 lines) - Utilities
├── models/
│   ├── schedule.py (100 lines)
│   ├── customers.py (50 lines)
│   └── orders.py (200 lines)
└── services/
    ├── schedule_service.py (300 lines)
    ├── customer_service.py (200 lines)
    ├── flow_optimizer_service.py (300 lines)
    └── order_availability_service.py (400 lines)
```

---

## Architecture

```
┌─────────────────────────────────────────────────────────┐
│              BedrockScheduler (Facade)                   │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐│
│  │Schedule  │  │Customer  │  │Flow      │  │Order     ││
│  │Service   │  │Service   │  │Optimizer │  │Availability││
│  └──────────┘  └──────────┘  │Service   │  │Service   ││
│                               └──────────┘  └──────────┘│
└─────────────────────────────────────────────────────────┘
         │              │              │              │
         ▼              ▼              ▼              ▼
┌─────────────────────────────────────────────────────────┐
│                      Models                             │
│  ┌──────────┐  ┌──────────┐  ┌──────────────────────┐  │
│  │Schedule  │  │Customer  │  │Orders                │  │
│  │Models    │  │Models    │  │Models                │  │
│  └──────────┘  └──────────┘  └──────────────────────┘  │
└─────────────────────────────────────────────────────────┘
         │              │              │
         └──────────────┴──────────────┘
                        │
                        ▼
              ┌──────────────────┐
              │     Utils        │
              │  (helpers)       │
              └──────────────────┘
```

---

## Key Benefits

### 1. Single Responsibility
- Each service handles one domain
- Models are separated by concern
- Utilities are reusable

### 2. Testability
- Services can be tested independently
- Mock dependencies easily
- Faster unit tests

### 3. Maintainability
- Changes isolated to relevant service
- Easier to find code
- Reduced merge conflicts

### 4. Extensibility
- Add new features without touching existing code
- Services can evolve independently
- Easy to add new services

### 5. Backward Compatibility
- Existing code works unchanged
- Facade maintains same interface
- Gradual migration possible

---

## File Size Breakdown

| File | Lines | Status |
|------|-------|--------|
| `scheduler.py` (old) | 1,447 | ❌ God file |
| `scheduler.py` (new) | 150 | ✅ Facade |
| `utils.py` | 150 | ✅ Utilities |
| `models/schedule.py` | 100 | ✅ Models |
| `models/customers.py` | 50 | ✅ Models |
| `models/orders.py` | 200 | ✅ Models |
| `services/schedule_service.py` | 300 | ✅ Service |
| `services/customer_service.py` | 200 | ✅ Service |
| `services/flow_optimizer_service.py` | 300 | ✅ Service |
| `services/order_availability_service.py` | 400 | ✅ Service |

**Largest file:** 400 lines (acceptable)  
**Average file:** ~190 lines (ideal)

---

## Migration Path

### Phase 1: Extract Models (Day 1)
- Move dataclasses to `models/`; update imports only in scheduler
- Smoke test: `pytest tests/test_api/test_endpoints.py -k bedrock -v`
- Commit: “refactor: extract scheduler models”

### Phase 2: Extract Utils (Day 1)
- Move helpers to `utils.py`; update references
- Smoke test: `pytest tests/test_api/test_endpoints.py -k bedrock -v`
- Commit: “refactor: extract scheduler utils”

### Phase 3: Extract Services (Day 2)
- Services one-by-one (schedule → customer → flow → order availability)
- After each, smoke: `pytest tests/test_api/test_endpoints.py -k bedrock -v`
- After all, `pytest tests/test_api -k bedrock -v`
- Commit: “refactor: extract scheduler services”

### Phase 4: Create Facade (Day 3)
- Replace scheduler.py with delegating facade; update exports
- Tests: `pytest tests/test_api -k bedrock -v`
- Commit: “refactor: scheduler facade” + “chore: update scheduler exports”

### Phase 5: Test & Document (Day 4)
- Full suite `pytest tests/ -v`; coverage optional
- Optional perf sanity: `python scripts/test_bedrock_scheduler.py`
- Docs/migration notes; final commit: “refactor: split scheduler into services”

---

## Usage Examples

### Existing Code (Still Works)
```python
from kai_erp.adapters.syteline10_cloud import BedrockScheduler

scheduler = BedrockScheduler(config)
overview = await scheduler.get_schedule_overview()
customers = await scheduler.search_customers("Acme")
```

### New: Direct Service Usage (Optional)
```python
from kai_erp.adapters.syteline10_cloud import ScheduleService

service = ScheduleService(config)
overview = await service.get_schedule_overview()
```

### New: Use Models Directly
```python
from kai_erp.adapters.syteline10_cloud.models import Job, ScheduleOverview

# Create models directly if needed
job = Job(...)
```

---

## Testing Strategy

### Unit Tests
- Test each service independently
- Mock MongooseClient
- Test edge cases per service

### Integration Tests
- Test facade delegates correctly
- Test end-to-end flows
- Verify backward compatibility

### Regression Tests
- Run all existing tests
- Verify API endpoints work
- Check performance metrics

---

## Risk Assessment

| Risk | Probability | Impact | Mitigation |
|------|------------|--------|------------|
| Breaking changes | Low | High | Facade pattern, 100% compatible |
| Performance regression | Low | Medium | Same code, just reorganized |
| Missing edge cases | Medium | Medium | Comprehensive test coverage |
| Circular imports | Low | Low | Careful import structure |
| Merge conflicts | Medium | Low | Feature branch, sequential phases |

**Overall Risk:** Low ✅

---

## Success Metrics

✅ **Refactoring successful when:**
- [ ] All tests pass
- [ ] No breaking changes
- [ ] Files < 500 lines
- [ ] Services independently testable
- [ ] Documentation updated
- [ ] No performance regression

---

## Timeline

**Estimated:** 4 days
- Day 1: Models + Utils
- Day 2: Services
- Day 3: Facade + Imports
- Day 4: Testing + Docs

**Buffer:** +1-2 days for unexpected issues

---

## Next Actions

1. ✅ Review refactoring plan
2. ⏳ Create feature branch
3. ⏳ Start Phase 1 (Extract Models)
4. ⏳ Execute phases sequentially
5. ⏳ Merge after all tests pass

---

## Questions?

See `REFACTORING_PLAN.md` for detailed step-by-step instructions.

