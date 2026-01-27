# ADR-041: Hook Input Validation and Silent Failure Prevention

**Status:** ACCEPTED
**Date:** 2026-01-27
**Category:** Methodology / Quality
**Source:** Code exploration finding

## Context

The Stop hook (`generate_session_summary.py`) silently exits with code 0 on errors:

```python
except json.JSONDecodeError as e:
    print(f"ERROR: Invalid JSON on stdin: {e}", file=sys.stderr)
    sys.exit(0)  # Silent exit even on error

if not session_id:
    sys.exit(0)  # Silent exit - no audit trail
```

## Problem Statement

- Sessions with incomplete data never generate summaries with no audit trail
- If Claude Code changes hook input format, summaries silently stop
- Debugging requires manual session file inspection
- No distinction between success exit and failure exit

## Proposed Solution

1. Add validation schema checking with clear error codes
2. Log to persistent hook error log (`~/.claude/hooks-errors.log`)
3. Use exit code 1 for errors, 0 only on success
4. Add `--validate` mode to check hook payload format

## Related ADRs

- ADR-027: Error Handling Strategy
- ADR-036: Silent Error Suppression

## Review Summary

### Backend Architect
- **Verdict:** ACCEPT
- **Complexity:** Low-Medium
- **Recommendations:** Define exit codes (0=success, 1=invalid, 2=not found)

### System Architect
- **Verdict:** ACCEPT
- **Maintainability:** HIGH POSITIVE
- **Decision:** Hook errors should be advisory (not blocking)
- **Decision:** 30-day retention (consistent with ADR-043)

## Implementation Notes

- Aligns with ADR-027 error handling strategy
- Use JSONL format for error log
- Add --validate-only flag for debugging
