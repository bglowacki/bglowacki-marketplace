# ADR-013: Data Duplication Strategy

**Status:** ACCEPTED
**Date:** 2026-01-27
**Category:** Architecture
**Decision:** Option C (Keep duplication, add verification tests)

## Context

The codebase intentionally duplicates logic between files (collect_usage.py:777-783):

```python
def detect_outcome(tool_name: str, result: str) -> str:
    """Detect outcome from tool result content.

    NOTE: This function is intentionally duplicated in generate_session_summary.py.
    Both scripts use 'uv run --script' for standalone operation without dependencies.
    Keep implementations in sync when making changes (ADR-003).
    """
```

Both `collect_usage.py` and `generate_session_summary.py` contain:
- `detect_outcome()` function
- Outcome detection keywords
- Tool-specific parsing logic

## Problems Identified

1. **Sync burden**: Changes must be made in two places
2. **Divergence risk**: Easy to update one and forget the other
3. **No automated verification**: No tests ensure implementations match
4. **Documentation drift**: Comments can become outdated
5. **Violates DRY**: Explicit choice against DRY principle

## Rationale for Duplication

The current design prioritizes:
- Standalone operation via `uv run --script`
- Zero external dependencies
- Simple deployment (single file per component)

## Decision

**ACCEPTED: Option C (Keep duplication, add verification tests)**

Keep the duplication for operational simplicity but add automated verification.

## Implementation Plan

Create `observability/tests/test_code_sync.py`:

```python
def test_outcome_detection_sync():
    """Verify detect_outcome implementations are identical."""
    import ast
    from pathlib import Path

    def extract_function(file_path: Path, func_name: str) -> str:
        tree = ast.parse(file_path.read_text())
        for node in ast.walk(tree):
            if isinstance(node, ast.FunctionDef) and node.name == func_name:
                return ast.unparse(node)
        raise ValueError(f"Function {func_name} not found in {file_path}")

    impl1 = extract_function(Path("hooks/generate_session_summary.py"), "detect_outcome")
    impl2 = extract_function(Path("skills/.../collect_usage.py"), "detect_outcome")

    # Normalize and compare (ignore docstrings, whitespace)
    assert impl1 == impl2, "detect_outcome implementations have diverged!"
```

## Review Summary

### Backend Architect Review
- **Recommendation:** ACCEPT (Option C)
- **Rationale:** DRY violation acceptable when alternatives add more complexity
- **Verification:** AST-based comparison catches divergence in CI

### Alternatives Rejected
- **Option A (Shared Library)**: Breaks `uv run --script` standalone requirement
- **Option B (Code Generation)**: Adds build step complexity
- **Option D (Process Only)**: Relies on human diligence, error-prone

## Consequences

- Operational simplicity maintained
- Automated verification prevents silent divergence
- Sync burden still exists but is enforced by tests
