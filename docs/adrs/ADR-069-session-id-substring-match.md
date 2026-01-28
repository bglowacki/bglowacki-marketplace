# ADR-024: Session ID Substring Match Ambiguity

## Status
PROPOSED

## Context
The `get_session_file()` function uses substring matching for session IDs.

## Finding
**File**: `generate_session_summary.py:46`

```python
if session_id in jsonl_file.name:
```

This is a substring match, not an exact match. If session IDs share prefixes (e.g., `abc123` and `abc123def`), the wrong file could be matched.

## Impact
- Potential for matching wrong session file
- First matching file is returned, which may not be the intended one
- Edge case but could cause confusing behavior

## Recommendation
Use more precise matching:

```python
# Option A: Check stem matches exactly
if jsonl_file.stem == session_id:
    return jsonl_file

# Option B: Check as suffix (UUID-style IDs)
if jsonl_file.stem.endswith(f"-{session_id}"):
    return jsonl_file
```

## Review Notes
- Severity: Medium (edge case)
- Effort: Low
- Risk: Low (need to verify expected file naming pattern)
