# ADR-024: Test Coverage for Methodology Code

**Status:** DEPRIORITIZED (REVISED after Deep Research)
**Date:** 2026-01-27
**Revised:** 2026-01-27
**Category:** Quality
**Decision:** Update priorities based on actual test coverage; focus on `find_matches()` gap

## Context (OUTDATED)

~~The analysis methodology code has no visible test coverage:~~
~~- `collect_usage.py` - 1500+ lines, no tests found~~
~~- `generate_session_summary.py` - 300 lines, no tests found~~

## Deep Research Findings (2026-01-27)

**The original premise was INCORRECT.** Tests DO exist:

### Existing Test Coverage

| File | Focus | Test Count | Status |
|------|-------|------------|--------|
| `test_outcome_detection.py` | `detect_outcome()` | 45+ tests | ✅ WELL COVERED |
| `test_session_parsing.py` | `parse_session_file()` | 25+ tests | ✅ COVERED |
| `test_workflow_stages.py` | `infer_workflow_stage()` | 48+ tests | ✅ WELL COVERED |
| `conftest.py` | Shared fixtures | N/A | ✅ EXISTS |

### Actual Gaps

| Function | Status | Priority |
|----------|--------|----------|
| `find_matches()` | **ZERO TESTS** | CRITICAL - see ADR-035 |
| `extract_triggers_from_description()` | Not tested | Medium |
| `compute_setup_profile()` | Not tested | Medium |
| `compute_plugin_usage()` | Not tested | Medium |

### Key Finding

`detect_outcome()` tests already verify **parity between hook and collector implementations** (per ADR-013):
```python
def test_error_in_output_not_keyword(self, detect_outcome):
    """Word 'error' as part of normal text shouldn't trigger failure."""
    result = "The error handling code works correctly"
    assert detect_outcome("Read", result) == "failure"  # Documents known issue
```

Tests document known false positives but don't fix them - that's a separate issue (ADR-037).

## Revised Decision

**ACCEPTED with updated priorities:**

1. **ADR-035 supersedes Priority 1**: `find_matches()` is the critical gap
2. **`detect_outcome()` is already covered**: Skip from Priority 1
3. **Add remaining Priority 2 functions**: Unchanged

## Revised Implementation Plan

### Priority 1: Critical Gap (ADR-035)

| Function | Test Cases | ADR |
|----------|-----------|-----|
| `find_matches()` | Exact match, partial, short triggers, blocklist, uppercase rule | ADR-035 |

### Priority 2: Discovery and Profile (Unchanged)

| Function | Test Cases |
|----------|-----------|
| `extract_triggers_from_description()` | Quoted phrases, "triggers on", "use when" patterns |
| `compute_setup_profile()` | Complexity thresholds, red flag detection, coverage gaps |
| `compute_plugin_usage()` | Active, potential, unused, disabled states |

### Priority 3: Integration (Updated)

| Scenario | Verification |
|----------|-------------|
| Full analysis on sample JSONL | Output schema valid |
| Empty session handling | Graceful degradation |
| Schema fingerprint detection | ADR-026 enhancement |

## Test Location (Verified)

```
observability/
  tests/
    test_outcome_detection.py   # ✅ EXISTS (45+ tests)
    test_session_parsing.py     # ✅ EXISTS (25+ tests)
    test_workflow_stages.py     # ✅ EXISTS (48+ tests)
    test_trigger_matching.py    # ❌ MISSING - ADR-035
    test_discovery.py           # ❌ MISSING - Priority 2
    conftest.py                 # ✅ EXISTS
```

## Dependencies

- **ADR-035**: Implements `find_matches()` tests (the actual critical gap)
- **ADR-013**: Test parity verification (already implemented)

## Review Summary

### Backend Architect Review (Original)
- **Verdict:** ACCEPT
- **Key Insight:** `detect_outcome()` and `find_matches()` are decision points - highest ROI

### Deep Research Review (2026-01-27)
- **Finding:** `detect_outcome()` already has 45+ tests with parity verification
- **Finding:** `find_matches()` has ZERO tests - this is the actual gap
- **Action:** Updated priorities to reflect actual state
- **Recommendation:** Focus on ADR-035 implementation

## Consequences

- ~~Core detection logic verified~~ → Already done for `detect_outcome()`
- `find_matches()` remains the critical untested function (ADR-035)
- Incremental approach validated - existing tests are a foundation
- Property-based tests for `find_matches()` would add value (regex edge cases)
