# ADR-049: Alert Fatigue Prevention

**Status:** IMPLEMENTED
**Date:** 2026-01-28
**Category:** UX
**Source:** Deep research on recommendation systems

## Context

Current agent can produce unlimited findings per category. A complex setup with 100+ components could generate dozens of recommendations, overwhelming users.

## Research Findings

From DevSecOps research:
> "Teams struggle with an excessive number of false positives and difficulties related to remediation."

From [Augment Code Observability Guide](https://www.augmentcode.com/guides/11-observability-platforms-for-ai-coding-assistants):
> "Modern platforms combine traditional observability with AI-powered debugging... offering actionable insights."

Key insight: **Actionable** means **limited and prioritized**, not comprehensive.

## Problem Statement

1. **No finding limits**: 50+ findings overwhelm users
2. **No diminishing returns recognition**: 10th similar finding adds little value
3. **Equal presentation**: Minor issues shown same as critical ones
4. **No batching**: All findings shown at once

## Proposed Solution

### 1. Finding Limits

```python
MAX_FINDINGS_PER_CATEGORY = 5
MAX_TOTAL_FINDINGS = 15
FINDINGS_PER_PAGE = 10  # For pagination
```

### 2. Priority Ranking Algorithm

```python
def rank_finding(finding: Finding) -> float:
    """Higher score = show first."""
    score = 0.0

    # Impact factors
    score += finding.confidence * 0.3
    score += finding.recency_weight * 0.25
    score += finding.frequency * 0.2  # How often this pattern occurs
    score += finding.fix_effort_inverse * 0.15  # Easy fixes first
    score += finding.category_priority * 0.1

    return score
```

### 3. Category Batching

Show findings progressively:

```markdown
## Quick Wins (5 findings)
High confidence, easy fixes - start here.

[Show 5 highest-ranked findings]

---

## Additional Findings (10 more available)
Lower priority items for when you have time.

[Expand to see more]
```

### 4. Consolidation Rules

Group similar findings:

| Pattern | Consolidation |
|---------|---------------|
| 5 skills with empty descriptions | "5 skills missing descriptions" (list collapsed) |
| 3 overlapping triggers | "3 trigger overlaps found" (details on expand) |
| Same issue in multiple sessions | Count + most recent example only |

### 5. Output Format

```markdown
## Analysis Summary

**Found 23 potential improvements** (showing top 10)

### Critical (2)
- [HIGH] Skill/command name collision: "commit"
- [HIGH] CLAUDE.md missing

### Quick Wins (5)
- [MED] Add triggers to systematic-debugging
- [MED] Empty description: design-events
- [LOW] Unused plugin: legacy-formatter
- [LOW] Similar: 2 more empty descriptions...

### See More
- 8 additional findings in Configuration category
- 6 additional findings in Cleanup category

[Expand all] | [Export full report]
```

## Consequences

- Users see manageable number of actionable items
- Most important findings surface first
- Reduced cognitive load
- Progressive disclosure for those who want details

## Implementation Notes

- Agent prompt should enforce limits
- Consider user preference for verbosity level
- Full report available via export for auditing
