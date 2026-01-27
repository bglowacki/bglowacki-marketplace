# ADR-025: Cross-Context Insights (Best Practices vs Usage)

**Status:** ACCEPTED
**Date:** 2026-01-27
**Category:** Methodology
**Decision:** Option C (Prioritized Sections) with opt-in best practices

## Context

The analysis combines two distinct types of insights:
1. **Usage-based**: What the user actually did (from JSONL sessions)
2. **Best practices**: What the user should do (from Context7/docs)

Currently these are mixed in the same analysis output.

## Problems Identified

1. **Source confusion**: User may not know if insight is from their data or docs
2. **Relevance mismatch**: Best practice may not apply to user's workflow
3. **Context7 dependency**: Best practices require MCP, usage analysis doesn't
4. **Different confidence**: Usage data is factual, best practices are advisory
5. **Update frequency**: Usage changes per-session, best practices are static

## Decision

**ACCEPTED: Option C with clear attribution**

Usage findings first (always available, high confidence), best practices second (opt-in, requires Context7).

## Implementation

### Command Line Flag

```bash
# Default: usage analysis only
collect_usage.py --format json

# With best practices (requires Context7)
collect_usage.py --format json --include-best-practices
```

### Output Structure

```markdown
## Usage Analysis (from your sessions)

### [High Confidence] Missed Skill Opportunities
*Based on 10 sessions analyzed*
...

### [Medium Confidence] Pattern Inference
*Based on prompt analysis*
...

---

## Best Practices (from Claude Code docs)

### [Advisory] Hook Configuration
*From official documentation*
...
```

### Confidence Levels

| Source | Confidence | Display |
|--------|-----------|---------|
| Usage data | High | `[High Confidence]` |
| Pattern inference | Medium | `[Medium Confidence]` |
| Best practices | Advisory | `[Advisory]` |

### Caching Strategy

Cache Context7 results locally with TTL:
- Location: `.claude/context7-cache.json`
- TTL: 24 hours (best practices don't change frequently)
- Fallback: Hardcoded recommendations if cache miss and offline

## Review Summary

### System Architect Review
- **Verdict:** ACCEPT
- **Key Insight:** Separation of concerns by data source is sound
- **Recommendation:** Best practices should be opt-in (not all users have Context7)
- **Addition:** Add local caching for offline support

## Consequences

- Clear provenance for all insights
- Usage analysis works without network
- Best practices optional, Context7-dependent
- Confidence levels help users prioritize
