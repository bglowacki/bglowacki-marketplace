# ADR-046: Confidence Scoring for Analysis Findings

**Status:** PROPOSED
**Date:** 2026-01-28
**Category:** Methodology
**Source:** Deep research on usage analytics best practices

## Context

The usage-insights-agent produces findings without confidence levels. Currently:
- Priority is based on count (5+ issues = High, 2-4 = Medium, 1 = Low)
- No distinction between high-certainty and speculative findings
- All recommendations treated equally regardless of evidence strength

## Research Findings

From [Fiddler AI LLM Observability](https://www.fiddler.ai/llmops):
> "Modern platforms combine traditional observability with AI-powered debugging and evaluation... offering actionable insights to improve agent and LLM behavior."

From [Braintrust LLM Observability Guide](https://www.braintrust.dev/articles/top-10-llm-observability-tools-2025):
> "LLM observability monitors Large Language Model behavior... through comprehensive tracking, tracing, and analysis."

Key insight: **Probabilistic outputs require confidence scoring** - the same input to an LLM can produce different analysis results.

## Problem Statement

1. **No confidence gradation**: "skill X was never used" (certain) treated same as "prompt Y might have benefited from skill Z" (speculative)
2. **No evidence trail**: Findings don't show what evidence supports them
3. **User can't prioritize**: Without confidence, users can't distinguish quick wins from uncertain suggestions

## Proposed Solution

Add confidence scoring to each finding:

```python
@dataclass
class Finding:
    category: str
    description: str
    confidence: float  # 0.0 - 1.0
    evidence: list[str]  # What supports this finding
    action: str

CONFIDENCE_LEVELS = {
    "high": 0.8,    # Direct evidence (e.g., exact trigger match)
    "medium": 0.5,  # Indirect evidence (e.g., semantic similarity)
    "low": 0.3,     # Speculative (e.g., pattern inference)
}
```

### Confidence Calculation Rules

| Finding Type | Confidence Basis |
|--------------|------------------|
| Never-used component | HIGH - binary fact |
| Exact trigger match not invoked | HIGH - direct match |
| Semantic similarity match | MEDIUM - inference |
| Coverage gap suggestion | LOW - speculative |
| Pattern-based recommendation | Varies by pattern frequency |

### Output Format Change

```markdown
### Missed Skill Opportunities (3 findings)

| Finding | Confidence | Evidence | Action |
|---------|------------|----------|--------|
| systematic-debugging not used for "help debug this error" | HIGH (0.85) | Exact trigger "debug" matched | Invoke with /systematic-debugging |
| brainstorming might help "let's think about approach" | MEDIUM (0.45) | Semantic similarity to "plan" | Consider using brainstorming skill |
```

## Consequences

- Users can filter low-confidence findings
- Reduces alert fatigue
- Enables learning from acceptance rates
- More honest about uncertainty

## Implementation Notes

- Agent prompt should request confidence scoring
- Collector output should include match evidence
- Consider confidence threshold config (default: show >= 0.3)
