# ADR-050: Statistical Significance for Pattern Detection

**Status:** PROPOSED
**Date:** 2026-01-28
**Category:** Methodology
**Source:** Deep research on analytics best practices

## Context

Current analysis uses simple counts without statistical validation:
- "3 missed opportunities" reported without sample size context
- No significance testing for patterns
- Small samples can lead to spurious recommendations

## Research Findings

From [IBM Observability for GenAI](https://www.ibm.com/think/insights/observability-gen-ai):
> "Traditional monitoring falls short for AI because it lacks statistical frameworks, multivariate analysis, and business impact insights."

From [dbt Labs Analytics Engineering](https://www.getdbt.com/blog/state-of-analytics-engineering-2025-summary):
> "Observability and data quality became more prominent concerns... automated data quality checks build trust in data reliability."

## Problem Statement

1. **No sample size awareness**: "50% miss rate" from 2 sessions vs 100 sessions
2. **No statistical tests**: Can't distinguish signal from noise
3. **Pattern inflation**: Small samples produce false patterns
4. **No baseline**: What's "normal" for this setup?

## Proposed Solution

### 1. Minimum Sample Size Requirements

```python
MIN_SESSIONS_FOR_PATTERN = 5
MIN_OCCURRENCES_FOR_SIGNIFICANCE = 3

def is_pattern_significant(occurrences: int, total_sessions: int) -> bool:
    """Require minimum evidence before reporting pattern."""
    if total_sessions < MIN_SESSIONS_FOR_PATTERN:
        return False  # Insufficient data
    if occurrences < MIN_OCCURRENCES_FOR_SIGNIFICANCE:
        return False  # Too rare to be pattern
    return True
```

### 2. Confidence Intervals

Report ranges, not point estimates:

```python
from scipy.stats import beta

def binomial_confidence_interval(successes: int, trials: int, confidence: float = 0.95) -> tuple[float, float]:
    """Wilson score interval for proportion."""
    if trials == 0:
        return (0.0, 1.0)
    alpha = 1 - confidence
    lower = beta.ppf(alpha/2, successes, trials - successes + 1)
    upper = beta.ppf(1 - alpha/2, successes + 1, trials - successes)
    return (lower, upper)
```

### 3. Baseline Comparison

Track historical baselines:

```python
@dataclass
class Metric:
    name: str
    current: float
    baseline: float
    deviation: float  # How many std devs from baseline
    status: str  # "normal", "above_baseline", "below_baseline"
```

### 4. Output Format

```markdown
## Pattern Analysis (10 sessions analyzed)

| Pattern | Occurrences | Rate | 95% CI | Status |
|---------|-------------|------|--------|--------|
| Missed skill opportunities | 7/10 | 70% | (39%, 90%) | ⚠️ Significant |
| Interruptions | 2/10 | 20% | (5%, 48%) | Within normal range |
| Empty prompts | 1/10 | 10% | (1%, 40%) | Insufficient data |

**Note:** Patterns require ≥3 occurrences across ≥5 sessions to be flagged.

### Insufficient Data Warnings

The following patterns couldn't be validated due to small sample size:
- Skill X usage (2 sessions, need ≥5)
- Hook Y triggers (1 occurrence, need ≥3)
```

### 5. Spurious Pattern Filtering

```python
def filter_spurious_patterns(findings: list[Finding], sessions: int) -> list[Finding]:
    """Remove patterns likely due to chance."""
    # Bonferroni correction for multiple comparisons
    significance_threshold = 0.05 / len(findings)

    significant = []
    for f in findings:
        p_value = calculate_p_value(f.occurrences, sessions, f.expected_rate)
        if p_value < significance_threshold:
            significant.append(f)

    return significant
```

## Consequences

- Reduces false positive patterns from small samples
- Users understand confidence in findings
- Baseline tracking enables trend detection
- More trustworthy recommendations

## Implementation Notes

- Requires scipy or pure Python implementation
- Store historical baselines in feedback file
- Consider user-configurable significance level
- Don't report insufficient-data items as findings, just note them
