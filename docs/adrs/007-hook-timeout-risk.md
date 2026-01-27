# ADR-007: Review Stop Hook Timeout

## Status
PROPOSED

## Context
The Stop hook in `plugin.json` has a 5000ms timeout:
```json
"hooks": {
  "Stop": [{
    "matcher": "*",
    "hooks": [{
      "type": "command",
      "command": "uv run ${CLAUDE_PLUGIN_ROOT}/hooks/generate_session_summary.py",
      "timeout": 5000
    }]
  }]
}
```

## Finding
**File**: `observability/.claude-plugin/plugin.json:6-14`

5 seconds may be insufficient for:
- Large session files (many tool invocations)
- Slow disk I/O
- First-run uv dependency resolution

If timeout occurs:
- Session summary won't be generated
- User gets silent failure (no notification)
- No error feedback to user

## Decision
TBD - Needs review

## Options

### Option A: Increase Timeout to 10000ms
More buffer for large sessions.

**Pros**: Safer for edge cases
**Cons**: Delays session exit by up to 10s if stuck

### Option B: Optimize Script Performance
Profile and optimize `generate_session_summary.py`.

**Pros**: Addresses root cause
**Cons**: May not be possible if I/O bound

### Option C: Add Timeout Handling
Script could write partial results or log timeout.

**Pros**: Graceful degradation
**Cons**: More complex implementation

### Option D: Keep Current Timeout
5s is sufficient for typical sessions.

**Pros**: No change needed
**Cons**: Risk of silent failures

## Recommendation
Option A as quick fix, then investigate Option B. The script is simple enough that 5s should suffice, but safety margin is cheap.

## Impact
- Prevents silent failures on large sessions
- Negligible impact on user experience

## Review Notes
- Severity: Low (edge case)
- Effort: Trivial (single number change)
- Risk: Low
