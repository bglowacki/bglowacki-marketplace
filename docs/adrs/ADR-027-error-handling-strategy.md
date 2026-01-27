# ADR-027: Error Handling Strategy

**Status:** ACCEPTED
**Date:** 2026-01-27
**Category:** Architecture
**Decision:** Option B (Hybrid structured + stderr)

## Context

Current error handling in collect_usage.py is inconsistent:
- Some errors print to stderr and continue
- Some errors are silently caught
- Some errors would crash the script
- No structured error reporting

## Decision

**ACCEPTED: Option B (Hybrid)**

Structured errors in JSON output for machine consumers, critical errors also to stderr for human visibility.

## Implementation Plan

### Error Categories

| Category | Severity | Behavior |
|----------|----------|----------|
| Configuration | Warning | Continue, report in output |
| Parsing | Warning | Skip item, report |
| Discovery | Info | Skip item, count |
| Critical | Error | Abort analysis, stderr |

### Structured Error Output

Add to JSON output:
```json
{
  "errors": [
    {
      "category": "parsing",
      "severity": "warning",
      "source": "/path/to/file",
      "message": "Invalid YAML frontmatter",
      "recovery": "Fix YAML syntax in file"
    }
  ],
  "error_summary": {
    "warnings": 3,
    "infos": 5,
    "critical": 0
  }
}
```

### Critical Error Handling

For critical errors:
1. Log to structured output
2. Print to stderr (human visibility)
3. Exit with non-zero code

## Review Summary

### Backend Architect Review
- **Verdict:** ACCEPT
- **Assessment:** Solid error model. Hybrid approach serves both machine and human consumers.

## Consequences

- Consistent error handling across codebase
- Machine-readable error output for automation
- Human-readable critical errors on stderr
- Clear recovery guidance where possible
