# ADR-010: Improve Error Handling and Logging

## Status
PROPOSED

## Context
Both Python scripts have minimal error handling:
- `generate_session_summary.py` silently exits on errors
- `collect_usage.py` prints warnings to stderr but continues
- No logging framework (just print statements)

## Finding
**generate_session_summary.py:252-256**:
```python
try:
    input_data = json.load(sys.stdin)
except json.JSONDecodeError:
    sys.exit(0)  # Silent failure
```

**collect_usage.py** (various):
```python
except Exception as e:
    print(f"Warning: Could not parse {skill_md}: {e}", file=sys.stderr)
```

Issues:
1. Silent failures in hook make debugging difficult
2. No log file for hook execution
3. Warnings may be missed in stderr
4. No structured logging for analysis

## Decision
TBD - Needs review

## Options

### Option A: Add Simple Logging
Use Python's logging module with file output.

**Pros**: Standard approach, configurable
**Cons**: Adds complexity to simple scripts

### Option B: Add Error Summary File
Write errors to `~/.claude/observability-errors.log`

**Pros**: Persistent record, easy to check
**Cons**: Another file to manage

### Option C: Keep Current Approach
Silent failures are acceptable for non-critical features.

**Pros**: Simple, no overhead
**Cons**: Hard to debug issues

## Recommendation
Option B - Simple error log file that's easy to check. Hook errors especially need visibility since they run silently.

Example:
```python
ERROR_LOG = Path.home() / ".claude" / "observability-errors.log"

def log_error(context: str, error: Exception):
    with ERROR_LOG.open("a") as f:
        f.write(f"{datetime.now().isoformat()} [{context}] {error}\n")
```

## Impact
- Easier debugging
- Visibility into hook failures
- Minimal overhead

## Review Notes
- Severity: Medium (operational concern)
- Effort: Low
- Risk: Low
