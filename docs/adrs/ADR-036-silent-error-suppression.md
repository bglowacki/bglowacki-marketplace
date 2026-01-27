# ADR-036: Silent Error Suppression in Plugin/Settings Parsing

**Status:** ACCEPTED
**Date:** 2026-01-27
**Category:** Quality
**Source:** Code exploration finding

## Context

Multiple locations silently suppress errors with `except: pass`:

```python
# Lines 238-239, 247-248 in collect_usage.py
except (json.JSONDecodeError, Exception):
    pass
```

Affected functions:
- `read_plugin_enabled_states()` (lines 232-250)
- `discover_from_plugins()` (lines 521-611)
- `discover_hooks()` (lines 613-714)

## Problem Statement

Silent error suppression causes:
- Corrupted settings.json files return empty dicts
- Plugin discovery silently skips invalid plugins
- Hooks dropped without warning if plugin.json is corrupted
- Users have no feedback that configuration was lost

## Proposed Solution

1. Log warnings to stderr (consistent with existing pattern at line 374)
2. Track failed files in separate structure: `failed_settings_files: list[str]`
3. Include failed file list in warnings output
4. Distinguish "file missing" (expected) vs "file corrupted" (error)

## Implementation Example

```python
try:
    content = json.loads(path.read_text())
except FileNotFoundError:
    pass  # Expected, file may not exist
except json.JSONDecodeError as e:
    print(f"Warning: Corrupted {path}: {e}", file=sys.stderr)
    failed_files.append(str(path))
```

## Related ADRs

- ADR-027: Error Handling Strategy (provides framework for this)

## Review Summary

### Backend Architect
- **Verdict:** ACCEPT
- **Complexity:** LOW
- **Note:** Existing warning pattern is good; add `failed_files` to JSON output

### System Architect
- **Verdict:** ACCEPT
- **Maintainability:** HIGH POSITIVE
- **Decision:** Include in BOTH JSON output AND stderr (per ADR-027 hybrid pattern)
- **Decision:** No threshold - always report failures

## Implementation Notes

- Use structured error format from ADR-027
- Distinguish FileNotFoundError (expected) from JSONDecodeError (error)
- Track failed files in JSON output for machine consumption
