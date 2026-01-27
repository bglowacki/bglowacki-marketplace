# ADR-023: Silent JSON Failures Hide Data Corruption

## Status
PROPOSED

## Context
Multiple places in the codebase silently catch exceptions and return default values, hiding data corruption from users.

## Finding
**Files**:
- `generate_session_summary.py:131-133, 254-256`
- `collect_usage.py:358-359` (YAML)

Issues:
1. `parse_session_file()` returns default stats on ANY exception (line 132-133)
2. `main()` silently exits on JSON decode errors (line 255-256)
3. YAML errors return empty dict without context (line 358)

## Impact
- Users won't know if their session data is corrupted
- No logging of what went wrong
- Empty summaries for corrupted sessions appear as "no activity"
- Debugging data issues becomes extremely difficult

## Recommendation
Add error logging to stderr before returning defaults:

```python
# At line 131-133:
try:
    lines = session_path.read_text().strip().split("\n")
except Exception as e:
    print(f"ERROR: Failed to read {session_path}: {e}", file=sys.stderr)
    return stats

# At line 254-256:
except json.JSONDecodeError as e:
    print(f"ERROR: Invalid JSON on stdin: {e}", file=sys.stderr)
    sys.exit(0)
```

## Review Notes
- Severity: High (data integrity)
- Effort: Low
- Risk: None (logging only)
