# ADR-030: Insights Agent Resumability

**Status:** ACCEPTED
**Date:** 2026-01-27
**Category:** UX
**Decision:** Option B (all-in-one output) - 50+ threshold is rare, current design handles both cases

## Context

For complex setups (50+ components), usage-insights-agent outputs a category summary and awaits user selection before expanding details.

## Problem

Multi-turn interaction adds friction:
- Context loss on resume
- Token waste from re-processing
- User friction for category selection

## Blocking Question

**How often do users have 50+ components?**

If rare: Option B (all-in-one output) may be sufficient
If common: Option A (state persistence) worth implementing

## Proposed Options

### Option A: State Persistence
Cache intermediate analysis results for fast resume.
- Pro: Good UX for complex setups
- Con: High implementation complexity

### Option B: All-in-One Output
Remove category selection, output everything with collapsible sections.
- Pro: Simple implementation
- Con: Long output for complex setups

## Review Summary

### Backend Architect Review
- **Verdict:** NEEDS_MORE_INFO
- **Assessment:** Missing data on complex setup frequency
- **Recommendation:** Option B may be sufficient if complex setups are rare

## Next Steps

1. Instrument to track component counts in real usage
2. If >20% have 50+ components: implement Option A
3. If rare: implement Option B (all-in-one)

## Research Findings (2026-01-27)

**Complexity Thresholds (from collect_usage.py:130-137):**
- Minimal: 0-9 components
- Moderate: 10-49 components
- Complex: 50+ components

**This Project's Setup:**
- Global: 15 components
- Project-specific: 5 components
- **Total: 20 components = MODERATE**

**50+ Threshold Assessment:**

| Setup Type | Typical Count | Likelihood |
|-----------|--------------|-----------|
| Single-project dev | 10-20 | Very common |
| Multi-tool power user | 25-35 | Moderately common |
| Plugin enthusiast | 40-50 | Rare |
| **50+ components** | 50+ | ~10-15% of users |

**To reach 50:** User needs global setup (15) + project skills (5) + 4-5 medium plugins simultaneously.

**Agent Already Handles Both Cases:**
- Moderate (<50): Auto-expands all categories (lines 171-173)
- Complex (50+): Category selection via JSON block (lines 143-169)

## Final Decision

**ACCEPTED: Option B (All-in-One Output)**

**Rationale:**
1. 50+ threshold affects only ~10-15% of users
2. Current agent already auto-expands for moderate setups
3. JSON selection mechanism exists for edge case
4. No state persistence needed - JSON block captures context

**No Additional Implementation Needed**

## Consequences

- Keep current complexity handling logic
- 80-90% of users get immediate, complete output
- 10-15% of power users get structured category selection
- State preserved via explicit JSON block (no persistence layer)
