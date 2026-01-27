# ADR-038: Unsafe Date Parsing in Session Summary Analysis

**Status:** ACCEPTED
**Date:** 2026-01-27
**Category:** Quality
**Source:** Code exploration finding

## Context

`analyze_session_summaries()` (lines 1304-1310) parses dates unsafely:

```python
date_str = summary_file.name[:10]  # Assumes YYYY-MM-DD
file_date = datetime.strptime(date_str, "%Y-%m-%d")
```

## Problem Statement

No validation that first 10 characters are actually a date:
- Filenames like `2025-01-ab.json` crash with ValueError
- Renamed or corrupted files silently skipped
- Stats appear complete but may be partial
- No tracking of which files were problematic

## Proposed Solution

1. Validate format before parsing:
```python
if not re.match(r'^\d{4}-\d{2}-\d{2}', summary_file.name):
    failed_files.append(summary_file.name)
    continue
```

2. Track skipped files in stats return
3. Log warning for unparseable files
4. Include skipped file count in output

## Implementation Complexity

**LOW** - Simple regex validation + tracking list.

## Review Summary

### Backend Architect
- **Verdict:** ACCEPT
- **Complexity:** LOW
- **Note:** Currently caught but silently skipped

### System Architect
- **Verdict:** ACCEPT
- **Maintainability:** HIGH POSITIVE
- **Decision:** NO to mtime recovery (explicit > implicit)
- **Decision:** Enforce `YYYY-MM-DD*.json` convention

## Implementation Notes

- Regex pre-filter then datetime.strptime validation
- Use structured error format from ADR-027
- Track skipped files for observability
