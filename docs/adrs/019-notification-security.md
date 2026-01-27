# ADR-019: Review macOS Notification Security

## Status
PROPOSED

## Context
The `generate_session_summary.py` hook uses `subprocess.run` with `osascript` to display macOS notifications:

```python
subprocess.run([
    "osascript", "-e",
    f'display notification "{message}" with title "{title}"'
], capture_output=True, timeout=5)
```

## Finding
**File**: `hooks/generate_session_summary.py:221-224`

### Current State
- `title` is derived from `summary['project']` which comes from `os.path.basename(cwd)`
- `message` contains tool counts and emojis

### Risk Assessment
**LOW RISK** - The inputs are derived from:
1. Project name (from cwd path - not user input)
2. Computed statistics (integers)

However, the pattern of string interpolation into shell commands is a code smell.

## Decision
TBD - Needs review

## Options

### Option A: Accept Current Implementation
Risk is low because inputs are controlled.

**Pros**: No changes needed
**Cons**: Sets bad precedent for future code

### Option B: Sanitize Inputs
Add escaping for `title` and `message`:

```python
def escape_applescript(s: str) -> str:
    return s.replace('\\', '\\\\').replace('"', '\\"')
```

**Pros**: Defense in depth
**Cons**: Slightly more code

### Option C: Use Alternative Notification Method
Use `terminal-notifier` or Python library instead of osascript.

**Pros**: Cleaner implementation
**Cons**: Adds dependency

## Recommendation
Option A - Accept current implementation. The inputs are derived from controlled sources (cwd path and computed stats), not user input. The osascript approach is common for macOS notifications in Python scripts.

Add a comment documenting why this is safe.

## Impact
- Minimal (documentation only if accepted)

## Review Notes
- Severity: Very Low (defense in depth)
- Effort: Low
- Risk: None
