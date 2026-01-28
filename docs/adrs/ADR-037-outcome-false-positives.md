# ADR-037: Outcome Detection False Positives from Generic Matching

**Status:** DEFERRED
**Date:** 2026-01-27
**Category:** Methodology
**Source:** Code exploration finding

## Context

`detect_outcome()` (lines 777-805) uses substring matching:

```python
if any(kw in result_lower for kw in ["error:", "failed", "traceback"]):
    return "failure"
if "error" in result_lower:
    return "failure"
```

## Problem Statement

Generic keywords cause false positives:
- "No error in operation" → marked as failure
- "Error handling completed successfully" → failure
- Documentation mentioning "error" → failure

This skews success_rate metrics and pollutes missed opportunity analysis.

## Proposed Solution

1. Use word-boundary regex: `r'\berror\b:'` instead of substring
2. Require pattern specificity (e.g., "error:" with colon)
3. Add context override: if "succeeded" appears, don't mark as failure
4. Consider "warning" outcome for partial success

## Related ADRs

- ADR-002: Outcome Detection Reliability (tri-state approach)

## Impact

Improves accuracy of success_rate metrics without breaking existing behavior.

## Review Summary

### Backend Architect
- **Verdict:** ACCEPT
- **Complexity:** LOW
- **Note:** Check success patterns first, then error patterns

### System Architect
- **Verdict:** ACCEPT
- **Maintainability:** MODERATE POSITIVE
- **Decision:** YES to test cases for false positives
- **Decision:** NO to "warning" outcome (ADR-002 handles tri-state separately)

## Implementation Notes

- Use word-boundary regex: `\berror\b`
- Check success patterns FIRST (succeeded, passed, no error)
- Then check failure patterns
- Add tests for false positive scenarios
- Keep synced with generate_session_summary.py
