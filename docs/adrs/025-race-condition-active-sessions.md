# ADR-025: Race Condition Reading Active Sessions

## Status
PROPOSED

## Context
Session files are read without checking if they're still being written to.

## Finding
**File**: `generate_session_summary.py:45-48`

```python
for jsonl_file in project_dir.glob("*.jsonl"):
    if session_id in jsonl_file.name:
        return jsonl_file
```

If Claude Code is writing to a session file when the hook reads it, partial or corrupted data will be processed.

## Impact
- Corrupted summaries for active sessions
- Race condition if multiple hooks run simultaneously
- Incomplete data if session is mid-write

## Options

### Option A: Staleness Check
Only process files not modified in last N seconds:
```python
if time.time() - jsonl_file.stat().st_mtime < 5:
    continue  # Still being written to
```

### Option B: File Lock Check
Use `fcntl.lockf()` to check if file is locked.

### Option C: Accept Current Behavior
The hook only runs on session end, so the file should be complete.

## Recommendation
Option C - Accept current behavior. The Stop hook runs when the session ends, so the file should be complete. The race condition is theoretical.

However, if issues are observed in practice, Option A is the simplest mitigation.

## Review Notes
- Severity: Medium (theoretical)
- Effort: Low
- Risk: None if accepted as-is
