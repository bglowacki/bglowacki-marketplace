# ADR-052: Impact Analysis Over Pattern Matching

**Status:** IMPLEMENTED
**Date:** 2026-01-28
**Category:** Methodology
**Source:** Deep research on product analytics

## Context

Current analysis focuses on pattern detection:
- "Trigger X matched prompt Y but wasn't used"
- "Skill Z has empty description"

This shows WHAT but not WHY IT MATTERS in business/productivity terms.

## Research Findings

From [CPO Club Product Analytics](https://cpoclub.com/tools/product-analytics-tools/):
> "Traditional analytics tools show what happened, but they don't always explain why... there's a growing emphasis on impact analysis, where analytics tools help product teams measure how specific changes influence user behavior and business outcomes."

From [Splunk GenAI Metrics](https://www.splunk.com/en_us/blog/artificial-intelligence/generative-ai-for-metrics-in-observability.html):
> "Beyond traditional tracking and reporting... companies are demanding deeper, more actionable insights."

## Problem Statement

1. **Pattern-centric**: "X matched Y" doesn't explain impact
2. **No cost quantification**: How much time/effort is wasted?
3. **No benefit projection**: What would user gain from fix?
4. **Equal treatment**: Minor aesthetic issues vs major productivity losses

## Proposed Solution

### 1. Impact Categories

Define impact dimensions:

```python
@dataclass
class Impact:
    time_saved_estimate: str  # "~5 min/session", "~1 hour/week"
    error_prevention: str     # "Prevents common mistake X"
    discovery_improvement: str # "Enables finding skill 30% faster"
    quality_improvement: str  # "Better code review coverage"
```

### 2. Impact Estimation Rules

| Finding Type | Impact Estimation |
|--------------|-------------------|
| Missed skill opportunity | Time saved per invocation × frequency |
| Empty description | Discovery failure rate × skill value |
| Trigger overlap | Confusion incidents × resolution time |
| Missing hook | Manual steps saved × frequency |

### 3. Output Format Change

Before:
```markdown
### Missed Skill: systematic-debugging
**Prompt:** "help me debug this error"
**Action:** Use /systematic-debugging
```

After:
```markdown
### Missed Skill: systematic-debugging

**What happened:** "help me debug this error" matched but wasn't used

**Impact:**
- You manually debugged for ~15 min (3 occurrences this week)
- systematic-debugging averages 8 min with structured root cause analysis
- **Estimated savings: ~21 min/week**

**Why it matters:** Without the skill's 4-phase process, you might:
- Miss the actual root cause (fix symptoms, not cause)
- Spend time on wrong hypotheses
- Lack systematic documentation for future reference

**Action:** Next time you see an error, try `/systematic-debugging`
```

### 4. Impact Scoring

```python
def calculate_impact_score(finding: Finding) -> float:
    """Quantify impact for prioritization."""
    frequency_weight = min(finding.occurrences / 10, 1.0)  # Cap at 10
    time_weight = estimate_time_savings(finding) / 60  # Hours
    error_weight = 0.5 if finding.prevents_errors else 0.0

    return frequency_weight * 0.4 + time_weight * 0.4 + error_weight * 0.2
```

### 5. Aggregate Impact Summary

```markdown
## Potential Improvements Summary

**Total estimated savings if all recommendations applied:**
- Time: ~2.5 hours/week
- Errors prevented: ~3/month
- Discovery improvement: 40% faster skill finding

**Top 3 by Impact:**
1. systematic-debugging usage → 21 min/week
2. Add triggers to design-events → 15 min/week
3. Fix CLAUDE.md structure → 10 min/week (one-time + ongoing)
```

## Consequences

- Users understand WHY to act on recommendations
- Prioritization based on real impact, not just pattern frequency
- More compelling case for taking action
- Enables ROI tracking after fixes applied

## Implementation Notes

- Impact estimation requires heuristics (time per manual task, etc.)
- Consider making estimates configurable
- Track actual impact post-fix for calibration
- Avoid false precision ("saves 7.3 minutes" → "saves ~5-10 minutes")
