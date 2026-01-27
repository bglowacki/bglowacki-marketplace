# ADR-017: Define Clear Domain Aggregates

**Status:** REJECTED
**Date:** 2026-01-27
**Category:** Architecture
**Decision:** Procedural approach is adequate; DDD aggregates not warranted

## Context

DDD review (DNA architect) identified missing aggregate boundaries:
- No clear ownership of trigger uniqueness
- No aggregate for opportunity tracking across sessions
- Priority calculation logic exists outside any aggregate
- Setup profile is a data struct, not a proper aggregate

From DNA M07: "Aggregates should be as small as possible and enforce invariants."

## Current State

Data structures exist without clear aggregate boundaries:
```python
@dataclass
class SetupProfile:
    # Just a data container, no behavior
    complexity: str
    total_components: int
    red_flags: list[str]
    # No invariant enforcement
```

## Blocking Questions

Before proceeding, we must answer:

1. **What bad thing happens if these invariants are violated?**
   - If trigger uniqueness fails: ?
   - If opportunity tracking is inconsistent: ?

2. **Does this domain have true transactional consistency requirements?**
   - This is an analysis tool, not a transactional system
   - Eventual consistency may be perfectly acceptable

3. **What is the cost of an inconsistent state?**
   - User sees incorrect analysis → re-run analysis (acceptable?)
   - Data corruption → need recovery (critical?)

## Proposed Option

**Option B: Rich Domain Objects** appears most appropriate.

From DNA M07: "An aggregate can be an object graph, can also be an anemic model, some data structure and a service."

Implementation:
- Keep dataclasses but add behavior methods with invariant checks
- Move validation into constructors
- Use Domain Services where appropriate (e.g., `TriggerRegistry` as service, not aggregate)

## Review Summary

### DDD Architect Review
- **Verdict:** NEEDS_MORE_INFO
- **Key Issue:** Proposes DDD aggregates without establishing domain complexity warrants them
- **Concern:** `UsageIntelligence` spanning sessions violates aggregate sizing principles
- **Concern:** `SetupProfile` is a read model, not a transactional aggregate
- **Recommendation:** Consider Option B, remove `UsageIntelligence` from scope

## Research Findings (2026-01-27)

**Domain Complexity Assessment:**

| Criterion | Assessment | Meets DDD Threshold? |
|-----------|-----------|-----|
| Bounded Context Size | Single script (~600 LOC) | ✓ Small |
| Complex Business Rules | Simple heuristics | ✗ Below threshold |
| Entity Interactions | Independent processing | ✗ No invariants |
| State Consistency | Pure transformations | ✗ N/A |
| Persistence | None (script output) | ✗ N/A |
| Concurrency | Single-threaded | ✗ N/A |

**DDD Fit Score: 3/10** (threshold for recommendation: 6+)

**Current Architecture:**
- Functional pipeline: discover → parse → analyze → output
- Pure functions with minimal coupling
- No state mutations across boundaries
- Business rules are analytical, not normative

**Cost-Benefit Analysis:**

| Aspect | Procedural | DDD |
|--------|------------|-----|
| Lines of code | ~600 | ~900 (+50%) |
| Data classes | 6 | 15+ |
| Onboarding time | ~30 min | ~60 min |
| Testability | Good (pure functions) | Slightly better |

## Final Decision

**REJECTED: DDD aggregates are overkill**

**Rationale:**
1. No transactional consistency requirements
2. No state persistence or concurrency concerns
3. Pure transformation functions unsuitable for aggregate patterns
4. Lower onboarding cost with procedural approach

**Conditions to Revisit:**
- Codebase grows to >1000 LOC core logic
- Multiple concurrent analysis engines needed
- Persistent state management added

## Consequences

- Keep current procedural/functional design
- May add validation to dataclass constructors (light improvement)
- No aggregate roots or repository pattern
