# ADR-035: Add Test Coverage for find_matches() Function

**Status:** ACCEPTED
**Date:** 2026-01-27
**Category:** Quality
**Source:** Research finding from ADR-011 false positive analysis

## Context

During ADR-011 research, discovered critical gap:

**The `find_matches()` function has ZERO test coverage.**

This function (collect_usage.py:974-1052) is responsible for:
- Matching user prompts to skill/agent triggers
- Determining "missed opportunities"
- Core of the recommendation engine

Yet it has no tests, while `infer_workflow_stage()` has 48 tests.

## Problem Statement

Without tests:
- Cannot verify trigger matching accuracy
- Cannot detect regressions when fixing issues (ADR-001, ADR-033)
- Cannot measure false positive rate improvement
- Cannot ensure consistency across changes

## Proposed Test Cases

```python
class TestFindMatches:
    def test_exact_name_match(self):
        """Skill name should always match."""

    def test_minimum_trigger_length(self):
        """Triggers <= 3 chars should be skipped (or >=3 per ADR-001)."""

    def test_word_boundary_matching(self):
        """'debug' should match 'debug this' but not 'debugging'."""

    def test_multiple_trigger_threshold(self):
        """Requires 2+ triggers OR name match."""

    def test_case_insensitive(self):
        """Matching should be case-insensitive."""

    def test_negation_context(self):
        """'don't debug' should NOT match debug trigger (per ADR-033)."""

    def test_partial_word_no_match(self):
        """'debugging' should not match 'debug' trigger."""
```

## Implementation Priority

**HIGH** - This is foundational test coverage for core methodology.

Aligns with ADR-024 (Test Coverage) recommendations.

## Review Summary

### Backend Architect Review
- **Verdict:** ACCEPT (HIGH PRIORITY)
- **Complexity:** LOW
- **Note:** Should be implemented BEFORE ADR-033

### System Architect Review
- **Verdict:** ACCEPT (HIGH PRIORITY)
- **Maintainability Impact:** Strongly Positive
- **Note:** Unblocks ADR-001 and ADR-033

## Dependencies

This ADR must be implemented FIRST:
- ADR-001 (trigger matching fixes) depends on tests
- ADR-033 (negation detection) depends on tests

## Implementation Notes

- Create `test_find_matches.py` following existing patterns
- Function is pure (no side effects, deterministic)
- Consider property-based tests for fuzz testing
