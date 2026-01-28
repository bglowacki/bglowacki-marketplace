# ADR-012: Red Flag Detection Completeness

**Status:** REJECTED (Deep Research)
**Date:** 2026-01-27
**Category:** Methodology
**Decision:** Implement comprehensive severity-based, extensible red flag system

## Context

Red flags are detected in `compute_setup_profile()` (collect_usage.py:158-187):

```python
red_flags = []
if not project_claude_md:
    red_flags.append("No project-level CLAUDE.md")
if by_source["project"]["hooks"] == 0 and by_source.get("project-local", {}).get("hooks", 0) == 0:
    red_flags.append("No project-level hooks")
# ... 5 types total
```

## Problems Identified

1. **Limited scope**: Only 5 types of red flags detected
2. **No severity levels**: All red flags presented equally
3. **Missing checks**: No check for stale configs, circular dependencies, invalid paths
4. **Project-agnostic**: Small personal projects don't need project-level customization
5. **No auto-detection of configuration errors**: Invalid YAML, missing required fields
6. **Plugin-specific issues ignored**: Plugin version conflicts, deprecated APIs

## Decision

**ACCEPTED: Implement Options A, B, C, D as cohesive system**

Priority order:
1. **Option C (Severity)** - critical/warning/info levels
2. **Option A (Comprehensive Catalog)** - externalized to YAML configuration
3. **Option D (Project-Type Filtering)** - reduce noise for simple projects
4. **Option B (Plugin-Provided)** - sandboxed extension point

## Implementation Architecture

```
Red Flag Detection System
+-------------------+     +------------------+     +------------------+
| Core Red Flags    |---->| Severity Levels  |---->| Filtered Output  |
| (built-in)        |     | critical/warn/   |     | (by project type |
+-------------------+     | info             |     |  & user prefs)   |
        ^                 +------------------+     +------------------+
        |
+-------------------+
| Plugin-Contributed|
| Red Flags         |
| (sandboxed)       |
+-------------------+
```

## Additional Red Flags to Implement

1. **Conflicting CLAUDE.md directives**: Same setting in multiple places
2. **Orphaned hooks**: Hooks referencing non-existent scripts
3. **Circular skill dependencies**: Skill A triggers B which triggers A
4. **Deprecated patterns**: Using old configuration formats
5. **Security concerns**: Hooks with excessive permissions
6. **Performance issues**: Too many hooks on common events

## Review Summary

### System Architect Review
- **Recommendation:** ACCEPT
- **Architecture:** Externalize catalog to YAML, support user severity preferences
- **Plugin Extension:** Sandboxed - cannot block analysis, only add warnings

### DDD Architect Review
- **Consideration:** Red flags should be modeled as Value Objects with severity

## Consequences

- More comprehensive issue detection
- User control over warning verbosity
- Extensible via plugins
- Requires configuration schema design
