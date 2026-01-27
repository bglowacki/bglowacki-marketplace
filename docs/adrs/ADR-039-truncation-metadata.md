# ADR-039: Track Data Truncation with Metadata

**Status:** ACCEPTED
**Date:** 2026-01-27
**Category:** UX
**Source:** Code exploration finding

## Context

Multiple places truncate data without tracking:

- Line 1140: `p[:MAX_PROMPT_LENGTH]` - prompts to 500 chars
- Line 1143: `s.prompts[:5]` - first 5 prompts per session
- Line 1144: `][:50]` - first 50 prompts total
- Line 1176: `][:20]` - first 20 interruptions

## Problem Statement

Users can't distinguish "no more data" from "data hidden":
- No indicator that truncation occurred
- No count of what was dropped
- Makes analysis seem complete when it isn't
- Hard to debug "why wasn't this pattern found"

## Proposed Solution

Add truncation metadata to JSON output:

```json
{
  "prompts": [...],
  "truncation": {
    "prompts_collected": 500,
    "prompts_shown": 50,
    "sessions_with_truncation": 12
  }
}
```

## Implementation Example

```python
truncation_stats = {
    "total_prompts": len(all_prompts),
    "shown_prompts": len(truncated_prompts),
    "truncated": len(all_prompts) > len(truncated_prompts)
}
```

## Review Summary

### Backend Architect
- **Verdict:** ACCEPT
- **Complexity:** LOW
- **Note:** Standard pattern for paginated/truncated APIs

### System Architect
- **Verdict:** ACCEPT
- **Maintainability:** MODERATE POSITIVE
- **Decision:** YES to CLI args (--max-prompts, --max-sessions)
- **Decision:** YES to "[+47 more]" indicator in text output

## Implementation Notes

- JSON gets full stats, text gets human-readable summary
- Simplified schema: `{"total": N, "shown": M}`
- Add configurable limits via command-line arguments
