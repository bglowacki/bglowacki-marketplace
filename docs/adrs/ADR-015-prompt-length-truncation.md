# ADR-015: Prompt Length Truncation Impact

**Status:** ACCEPTED
**Date:** 2026-01-27
**Category:** Methodology
**Decision:** Option C (Full Analysis, Truncated Display)

## Context

Prompts are truncated at multiple points (collect_usage.py:31-34):

```python
MAX_DESCRIPTION_LENGTH = 200
MAX_TOOL_INPUT_LENGTH = 100
MAX_PROMPT_LENGTH = 500
```

And in output (collect_usage.py:1144):
```python
"text": p[:MAX_PROMPT_LENGTH],
```

## Problems Identified

1. **Trigger matching on truncated text**: Long prompts may have triggers past 500 chars
2. **Context loss**: Truncated prompts lose nuance needed for accurate matching
3. **Arbitrary limits**: Why 500? What's the tradeoff being made?
4. **No intelligent truncation**: Just cuts at boundary, might cut mid-word or mid-sentence
5. **Different limits for different purposes**: 500 for prompts, 100 for tool input, 200 for descriptions
6. **No visibility into truncation**: User doesn't know analysis is on partial data

## Decision

**ACCEPTED: Option C (Full Analysis, Truncated Display)**

Separate concerns:
1. **Data Collection Layer**: Collect full prompts (no truncation)
2. **Analysis Domain**: Analyze full data
3. **Display Layer**: Truncate for presentation only

## Implementation Plan

1. Remove truncation from analysis paths - analyze full prompts
2. Keep truncation constants for display/output only
3. Add `is_truncated: bool` to output schema for transparency
4. Move `MAX_*` constants to output formatting code, not analysis code

## Review Summary

### DDD Architect Review
- **Recommendation:** ACCEPT
- **Key Issue:** Boundary violation - infrastructure truncation affecting domain behavior
- **Separation:** Truncation for storage, analysis, and display are different concerns

### Cohesion (DNA M08)
- Storage truncation: Prevents unbounded growth
- Analysis truncation: Should not exist
- Display truncation: UX concern

## Architecture After Change

```
+------------------+     +------------------+     +------------------+
| Data Collection  |---->| Analysis Domain  |---->| Display Layer    |
| (full prompts)   |     | (full analysis)  |     | (truncated view) |
+------------------+     +------------------+     +------------------+
                                                   |
                                                   v
                                            is_truncated: true
```

## Consequences

- More accurate trigger matching on long prompts
- Slightly higher memory usage during analysis (acceptable)
- Clear separation of concerns
- Users aware when viewing truncated data
