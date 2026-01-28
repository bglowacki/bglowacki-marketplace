# ADR-021: Document macOS-Only Notification Feature

## Status
PROPOSED

## Context
The plugin uses `osascript` for notifications which only works on macOS:
```python
def notify_macos(title: str, message: str):
    """Send macOS notification."""
    subprocess.run([
        "osascript", "-e",
        f'display notification "{message}" with title "{title}"'
    ], capture_output=True, timeout=5)
```

## Finding
**File**: `hooks/generate_session_summary.py:218-226`

Issues:
1. Function named `notify_macos` implies macOS-only but no platform check
2. On non-macOS, `osascript` will fail silently (captured output)
3. Documentation doesn't clarify platform requirements
4. README lists "macOS notifications" but doesn't say the plugin is macOS-specific

## Decision
TBD - Needs review

## Options

### Option A: Document as macOS-Only Feature
Clarify in README that notifications are macOS-only, other features work cross-platform.

**Pros**: Simple, honest
**Cons**: May disappoint non-macOS users

### Option B: Add Platform Check
```python
import platform

def notify(title: str, message: str):
    if platform.system() == "Darwin":
        notify_macos(title, message)
    elif platform.system() == "Linux":
        notify_linux(title, message)  # e.g., notify-send
    # Windows would need toast-notification or similar
```

**Pros**: Cross-platform support
**Cons**: More code, more dependencies

### Option C: Make Notification Optional
Check for osascript availability, skip gracefully if not found.

**Pros**: Works everywhere (notification just skipped)
**Cons**: Silent feature degradation

## Recommendation
Option A + Option C combined:
1. Document that notifications are macOS-only
2. Add explicit platform check so failures are expected, not silent errors

```python
import platform

def notify(title: str, message: str):
    if platform.system() != "Darwin":
        return  # Notifications only supported on macOS
    # ... existing osascript code
```

## Impact
- Clearer expectations for users
- Graceful handling on non-macOS

## Review Notes
- Severity: Low (usability)
- Effort: Low
- Risk: None
