# ADR-047: Temporal Weighting for Usage Analysis

**Status:** IMPLEMENTED
**Date:** 2026-01-28
**Category:** Methodology
**Source:** Deep research on usage analytics best practices

## Context

Current analysis treats all sessions equally regardless of recency:
- A prompt from 14 days ago weighted same as today's prompt
- No trend detection (is usage improving or declining?)
- No decay factor for stale data

## Research Findings

From [CPO Club Product Analytics](https://cpoclub.com/tools/product-analytics-tools/):
> "Traditional analytics tools show what happened, but they don't always explain why... there's a growing emphasis on impact analysis."

From [IBM Observability for GenAI](https://www.ibm.com/think/insights/observability-gen-ai):
> "Real-time dashboards track current system performance... while historical analysis identifies trends over time."

## Problem Statement

1. **Recency blindness**: User's recent behavior more predictive than old behavior
2. **No trend detection**: Can't see if missed opportunities are increasing or decreasing
3. **Stale recommendations**: May suggest fixes for patterns user already corrected
4. **Equal weighting**: 14-day-old session counts same as today

## Proposed Solution

### 1. Recency Weighting

Apply exponential decay to session data:

```python
def calculate_recency_weight(session_date: datetime, half_life_days: int = 7) -> float:
    """More recent sessions have higher weight."""
    age_days = (datetime.now() - session_date).days
    return 0.5 ** (age_days / half_life_days)

# Example: 7-day half-life
# Today: weight = 1.0
# 7 days ago: weight = 0.5
# 14 days ago: weight = 0.25
```

### 2. Trend Detection

Calculate week-over-week changes:

```python
@dataclass
class UsageTrend:
    metric: str
    this_week: float
    last_week: float
    trend: str  # "improving", "stable", "declining"
    change_pct: float
```

### 3. Output Enhancement

```markdown
## Usage Trends

| Metric | This Week | Last Week | Trend |
|--------|-----------|-----------|-------|
| Skill usage rate | 45% | 32% | +40% ↑ Improving |
| Missed opportunities | 3 | 8 | -62% ↓ Improving |
| Interruptions | 12% | 10% | +20% ↑ Watch |

## Recommendations (Weighted by Recency)

| Finding | Recency | Weight | Action |
|---------|---------|--------|--------|
| "debug" prompt without skill (yesterday) | 1 day | 0.91 | High priority |
| "plan feature" without skill (12 days ago) | 12 days | 0.22 | Lower priority |
```

### 4. Staleness Filter

Suppress findings based only on old data:

```python
MIN_RECENT_EVIDENCE = 0.5  # At least 50% of evidence from last 7 days

def should_report_finding(evidence_dates: list[datetime]) -> bool:
    recent = sum(1 for d in evidence_dates if (datetime.now() - d).days <= 7)
    return recent / len(evidence_dates) >= MIN_RECENT_EVIDENCE
```

## Consequences

- Recommendations reflect current behavior, not historical
- Users see if their workflow is improving
- Reduces noise from stale patterns
- Requires timestamp tracking in collector (already available)

## Implementation Notes

- collect_usage.py already has session timestamps
- Need to propagate timestamps to finding-level evidence
- Consider making half-life configurable
