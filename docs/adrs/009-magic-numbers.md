# ADR-009: Extract Magic Numbers to Constants

## Status
IMPLEMENTED (2026-01-27)

## Context
The codebase contains several magic numbers without named constants:
- `500` - prompt/description truncation length (multiple locations)
- `100` - tool input summary length
- `200` - description max length
- `50` - minimum characters for non-empty description
- `10` - default sessions to analyze
- `14` - default days for quick stats
- `20` - max interruptions to include in output
- `10` - max overlapping triggers to report
- `3` - minimum trigger length
- `2` - minimum trigger matches for missed opportunity

## Finding
**Files**: `collect_usage.py`, `generate_session_summary.py`

Magic numbers make code harder to understand and maintain. When the same value is used in multiple places, inconsistencies can arise.

## Decision
ACCEPTED - Constants added to collect_usage.py (MAX_DESCRIPTION_LENGTH, MAX_TOOL_INPUT_LENGTH, MAX_PROMPT_LENGTH, DEFAULT_SESSIONS, DEFAULT_DAYS).

## Recommendation
Create constants section at top of each file:
```python
# Configuration
DEFAULT_SESSIONS = 10
DEFAULT_DAYS = 14

# Limits
MAX_PROMPT_LENGTH = 500
MAX_DESCRIPTION_LENGTH = 200
MAX_TOOL_INPUT_SUMMARY = 100
MAX_INTERRUPTIONS_OUTPUT = 20
MAX_OVERLAPPING_TRIGGERS = 10

# Thresholds
MIN_TRIGGER_LENGTH = 3
MIN_TRIGGER_MATCHES = 2
MIN_DESCRIPTION_LENGTH = 50
```

## Impact
- Improves code readability
- Single point of configuration
- Enables easy tuning

## Review Notes
- Severity: Low (code quality)
- Effort: Low (mechanical refactor)
- Risk: None
