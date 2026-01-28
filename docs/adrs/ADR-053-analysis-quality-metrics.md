# ADR-053: Analysis Quality Metrics and Self-Evaluation

**Status:** IMPLEMENTED
**Date:** 2026-01-28
**Category:** Quality
**Source:** Deep research on LLM observability

## Context

The usage-insights-agent produces analysis but has no way to measure its own quality:
- No precision/recall tracking
- No user satisfaction measurement
- No recommendation acceptance rate
- No drift detection for analysis quality

## Research Findings

From [Arize LLM Platform](https://arize.com/):
> "Model drift detection where behavior variance occurs without version changes."

From [Langfuse LLM Observability](https://www.braintrust.dev/articles/top-10-llm-observability-tools-2025):
> "Langfuse is the most used open source LLM observability tool, providing comprehensive tracing, evaluations, prompt management, and metrics."

From [InsightFinder AI Observability](https://insightfinder.com/products/ai-observability/):
> "Automated data quality checks build trust in data reliability."

## Problem Statement

1. **No quality feedback**: Can't tell if analysis is good or bad
2. **No improvement loop**: Can't measure if changes help
3. **No drift detection**: Quality may degrade silently
4. **No benchmarking**: No way to compare analysis runs

## Proposed Solution

### 1. Analysis Metadata

Each analysis should output quality metadata:

```python
@dataclass
class AnalysisQuality:
    run_id: str
    timestamp: datetime
    input_stats: dict  # sessions, prompts, components analyzed
    output_stats: dict  # findings by category, confidence distribution
    coverage: float    # % of input data that produced findings
    consistency_hash: str  # Hash of key findings for drift detection
```

### 2. Quality Metrics

Track these over time:

| Metric | Definition | Target |
|--------|------------|--------|
| Finding rate | Findings / sessions analyzed | 0.5-2.0 |
| High-confidence rate | % findings with confidence > 0.7 | > 60% |
| Acceptance rate | Accepted / (Accepted + Dismissed) | > 50% |
| Coverage | Categories with findings / total categories | > 30% |
| Consistency | Same input produces similar findings | > 80% |

### 3. Consistency Testing

Run analysis twice on same input to detect LLM variance:

```python
def measure_consistency(input_data: dict, runs: int = 3) -> float:
    """Run analysis multiple times, measure finding overlap."""
    all_findings = []
    for _ in range(runs):
        findings = run_analysis(input_data)
        all_findings.append(set(hash_finding(f) for f in findings))

    # Jaccard similarity across runs
    intersection = set.intersection(*all_findings)
    union = set.union(*all_findings)
    return len(intersection) / len(union) if union else 1.0
```

### 4. Quality Dashboard

```markdown
## Analysis Quality Report

**Run:** 2026-01-28T10:00:00Z
**Input:** 15 sessions, 89 prompts, 127 components

### Output Quality
| Metric | Value | Target | Status |
|--------|-------|--------|--------|
| Findings generated | 12 | 5-20 | ✓ |
| High-confidence (>0.7) | 75% | >60% | ✓ |
| Category coverage | 4/6 (67%) | >30% | ✓ |

### Historical Trends
| Week | Findings | Acceptance Rate | Consistency |
|------|----------|-----------------|-------------|
| W1 | 15 | 45% | 72% |
| W2 | 12 | 58% | 78% |
| W3 | 10 | 62% | 85% ← Improving |

### Alerts
- ⚠️ Acceptance rate below 50% for 'cleanup' category
- ✓ No consistency drift detected
```

### 5. Self-Evaluation Prompt

Add to agent prompt:

```markdown
## Self-Evaluation

Before outputting findings, assess:
1. Do I have enough data? (≥5 sessions recommended)
2. Are my findings specific or generic?
3. Could any finding be a false positive?
4. Am I consistent with previous analyses?

Rate your confidence in this analysis: [Low/Medium/High]
Note any limitations or caveats.
```

## Consequences

- Can measure if analysis is improving
- Detect quality degradation early
- Build user trust through transparency
- Enable data-driven prompt improvements

## Implementation Notes

- Store metrics in observability-feedback.json
- Consider separate quality-check agent
- Run consistency tests periodically, not every analysis
- Make quality report optional (verbose mode)
