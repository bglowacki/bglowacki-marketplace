# ADR-040: Validate Tool Input Structure Before Processing

**Status:** ACCEPTED
**Date:** 2026-01-27
**Category:** Quality
**Source:** Code exploration finding

## Context

`_summarize_tool_input()` (lines 755-774) accesses tool_input without validation:

```python
agent = tool_input.get("subagent_type", "")
desc = tool_input.get("description", "")
```

## Problem Statement

No type checking:
- `tool_input.get()` crashes if tool_input is not a dict
- Assumes specific fields exist for each tool type
- No handling for malformed JSONL entries
- String formatting produces garbage for non-string types

## Proposed Solution

Add validation helper:

```python
def validate_tool_input(tool_name: str, tool_input: any) -> bool:
    if not isinstance(tool_input, dict):
        return False
    required = TOOL_REQUIRED_FIELDS.get(tool_name, [])
    return all(k in tool_input for k in required)
```

Log validation failures:

```python
if not isinstance(tool_input, dict):
    print(f"Warning: invalid tool_input for {tool_name}", file=sys.stderr)
    return "[invalid input]"
```

## Related ADRs

- ADR-026: JSONL Schema Stability (defensive parsing)
- ADR-027: Error Handling Strategy (structured errors)

## Review Summary

### Backend Architect
- **Verdict:** ACCEPT
- **Complexity:** LOW
- **Risk if not addressed:** MEDIUM (crashes on malformed JSONL)

### System Architect
- **Verdict:** ACCEPT
- **Maintainability:** HIGH POSITIVE
- **Decision:** YES to counting validation errors in stats
- **Degradation:** Return `"[invalid input]"`, increment counter, add to errors array

## Implementation Notes

- Consider renaming to `safe_get_tool_input()` for clarity
- Make TOOL_REQUIRED_FIELDS registry extensible
- Aligns with ADR-026 (defensive parsing) and ADR-027 (error handling)
