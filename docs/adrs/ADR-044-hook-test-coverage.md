# ADR-044: Hook Execution Path Test Coverage

**Status:** ACCEPTED
**Date:** 2026-01-27
**Category:** Quality / Testing
**Source:** Code exploration finding

## Context

Test suite covers outcome detection and stage inference but does NOT test:
- Actual hook execution pipeline
- Subprocess handling (`notify_macos`)
- File I/O error recovery
- Concurrent hook invocations
- Path handling edge cases (Unicode, spaces, symlinks)

## Problem Statement

- `notify_macos()` uses `except Exception: pass` - failures undetected
- Permission denied errors silently fail
- Two hooks running simultaneously could overwrite summaries
- No telemetry for hook success/failure rates

## Proposed Solution

1. Create `test_hook_execution.py` with mock session files
2. Add tests for subprocess error cases
3. Use unique IDs in summary filenames (not just timestamp)
4. Add retry logic with exponential backoff for file operations

Example test:
```python
def test_concurrent_summary_writes(tmp_path):
    """Two hooks writing simultaneously shouldn't lose data."""
    # Use UUID + timestamp to prevent collision
```

## Related ADRs

- ADR-035: find_matches() Test Coverage
- ADR-024: Test Coverage

## Review Summary

### Backend Architect
- **Verdict:** ACCEPT
- **Complexity:** Medium
- **Note:** Add concurrent write safety with file locking

### System Architect
- **Verdict:** ACCEPT
- **Maintainability:** HIGH POSITIVE
- **Decision:** YES to property-based tests for path handling
- **Decision:** Start with 5% failure rate threshold over 24h window

## Implementation Notes

- Create test_hook_execution.py with mock session files
- Use UUID in filenames to prevent collision
- Simple retry sufficient (exponential backoff overkill for local files)
