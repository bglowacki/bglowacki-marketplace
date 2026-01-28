# ADR-020: Centralize Path.home() Usage

## Status
IMPLEMENTED (2026-01-27)

## Context
The codebase has multiple occurrences of `Path.home()` creating the same paths:
- `Path.home() / ".claude"` appears 5+ times
- `Path.home() / ".claude" / "session-summaries"` in hook
- `Path.home() / ".claude" / "projects"` in multiple places

## Finding
**Files**: `collect_usage.py`, `generate_session_summary.py`

This repetition:
- Increases risk of typos
- Makes path changes harder
- Unclear if paths are configurable

## Decision
ACCEPTED - Path constants added to both files (HOME, CLAUDE_DIR, PROJECTS_DIR, SUMMARIES_DIR, PLUGINS_CACHE).

## Recommendation
Create a shared constants module or define at module level:

```python
# At top of collect_usage.py
HOME = Path.home()
CLAUDE_DIR = HOME / ".claude"
PROJECTS_DIR = CLAUDE_DIR / "projects"
SUMMARIES_DIR = CLAUDE_DIR / "session-summaries"
PLUGINS_CACHE = CLAUDE_DIR / "plugins" / "cache"
```

Benefits:
- Single source of truth
- Easy to make configurable later
- Clearer naming

## Impact
- Improved maintainability
- Enables future configurability

## Review Notes
- Severity: Very Low (code quality)
- Effort: Low (mechanical refactor)
- Risk: None
