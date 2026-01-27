# ADR-003: Deduplicate Outcome Detection Logic

## Status
IMPLEMENTED (2026-01-27) - Option B

## Context
The `detect_outcome` function exists in two files with identical logic:
1. `hooks/generate_session_summary.py:52-75`
2. `skills/observability-usage-collector/scripts/collect_usage.py:761-784`

Both functions detect success/failure from tool results using the same patterns.

## Finding
**DRY violation**: 24 lines of duplicated code that must be kept in sync.

**Risk**: If one implementation is updated, the other may be forgotten, leading to inconsistent behavior between session summaries and usage analysis.

## Decision
ACCEPTED - Implemented Option B (keep duplication with sync comments). Both files have NOTE comments linking them and tests verify both implementations behave identically.

## Options

### Option A: Create Shared Module
Extract to `observability/lib/outcome_detection.py` and import in both scripts.

**Pros**:
- Single source of truth
- Easy to test independently

**Cons**:
- Adds import complexity to standalone scripts
- May complicate uv script dependencies

### Option B: Accept Duplication
Keep both copies with a comment linking them.

**Pros**:
- Scripts remain fully standalone
- No import path issues

**Cons**:
- Maintenance burden
- Risk of drift

### Option C: Inline in generate_session_summary only
The hook script needs to be fast and standalone. Keep it there, and have collect_usage.py import from session_summary_utils.

## Recommendation
Option A with careful dependency management. The benefit of consistent behavior outweighs the complexity.

## Impact
- Ensures consistent outcome detection across all analysis
- Reduces code maintenance

## Review Notes
- Severity: Low (works correctly, just duplicated)
- Effort: Medium (module extraction + testing)
- Risk: Low
