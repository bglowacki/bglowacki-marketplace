# ADR-042: Shared Logic Module for Hook/Collector Sync

**Status:** REJECTED
**Date:** 2026-01-27
**Category:** Architecture
**Source:** Code exploration finding (extends ADR-013)

## Context

ADR-013 documents intentional duplication of `detect_outcome()` for `uv run --script` support, but no automated sync mechanism exists.

Current state:
- Hook (line 53-58) and collector (line 777-782) have identical functions
- Comment says "keep in sync" but no enforcement
- Pattern extends to other functions that could benefit from sharing

## Problem Statement

- Logic could diverge over time without detection
- Session summaries and usage analysis could produce conflicting results
- Maintenance burden grows with each shared function
- No structural guarantee of parity

## Proposed Solution

Create `observability/lib/shared_logic.py` with runtime import fallback:

```python
# At top of both scripts:
try:
    from observability.lib.shared_logic import detect_outcome
except ImportError:
    # Fallback for uv run --script mode
    def detect_outcome(tool_name, result):
        # Inline implementation...
        pass
```

Also:
- Add pre-commit hook to validate function signatures match
- Add test that compares AST of duplicated functions

## Related ADRs

- ADR-013: Data Duplication Strategy

## Review Summary

### Backend Architect
- **Verdict:** ACCEPT with conditions
- **Note:** Requires sync verification test

### System Architect
- **Verdict:** REJECT
- **Reason:** Contradicts already-accepted ADR-013 (Data Duplication Strategy)
- **Issue:** ADR-013 explicitly chose duplication with tests over shared library
- **Problem:** Import fallback creates three code paths, harder to maintain

## Final Decision

**REJECTED** - Contradicts ADR-013.

The correct solution per ADR-013 is AST verification tests to ensure sync, not shared modules. If AST tests are not yet implemented, implement them rather than adding import fallback complexity.
