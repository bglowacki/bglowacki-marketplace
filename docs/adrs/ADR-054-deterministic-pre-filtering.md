# ADR-054: Deterministic Pre-Filtering Before LLM Analysis

**Status:** IMPLEMENTED
**Date:** 2026-01-28
**Category:** Architecture
**Source:** Deep research on hybrid AI/rule systems

## Context

Current architecture sends all data to LLM for analysis. Many checks are deterministic and don't need LLM:
- Empty descriptions (string length check)
- Exact trigger matches (regex)
- Never-used components (count = 0)
- Name collisions (set intersection)

## Research Findings

From [Arize AI Observability](https://arize.com/):
> "Modern platforms combine traditional observability (latency, cost, performance) with AI-powered debugging."

From [Augment Code Guide](https://www.augmentcode.com/guides/11-observability-platforms-for-ai-coding-assistants):
> "AI-specific metrics include token consumption rates and costs, token efficiency."

Key insight: **Use LLM only where LLM is needed** - deterministic checks should be pre-computed.

## Problem Statement

1. **Token waste**: Sending data LLM can't help with
2. **Inconsistent simple checks**: LLM might miss obvious issues
3. **Latency**: LLM call for things that could be pre-computed
4. **Cost**: API costs for deterministic operations

## Proposed Solution

### 1. Split Analysis into Tiers

```
Tier 1: Deterministic (Python/collector)
├── Empty descriptions
├── Exact trigger matches
├── Never-used components (count = 0)
├── Name collisions
├── Missing required fields
└── Threshold violations

Tier 2: Pattern-Based (Rules engine)
├── Frequency patterns
├── Temporal patterns
├── Cross-reference violations
└── Statistical anomalies

Tier 3: LLM Analysis (Agent)
├── Semantic similarity
├── Intent inference
├── Natural language recommendations
└── Context-aware prioritization
```

### 2. Pre-Computed Findings

Add to collector output:

```python
@dataclass
class PreComputedFindings:
    empty_descriptions: list[str]      # Component names
    trigger_matches: list[dict]        # {prompt, component, trigger}
    never_used: list[str]              # Component names
    name_collisions: list[tuple]       # (skill, command) pairs
    threshold_violations: list[dict]   # {metric, value, threshold}
```

### 3. Collector Enhancement

```python
def compute_deterministic_findings(
    discovery: dict,
    sessions: list[SessionData],
    setup_profile: SetupProfile,
) -> PreComputedFindings:
    """Pre-compute findings that don't need LLM."""

    # Empty descriptions
    empty = [
        item["name"]
        for category in ["skills", "agents", "commands"]
        for item in discovery.get(category, [])
        if len(item.get("description", "")) < 30
    ]

    # Exact trigger matches not used
    matches = []
    all_used = set()
    for s in sessions:
        all_used.update(s.skills_used)
        all_used.update(s.agents_used)

    for prompt_data in sessions:
        for prompt in prompt_data.prompts:
            for item in discovery["skills"] + discovery["agents"]:
                for trigger in item.get("triggers", []):
                    if trigger.lower() in prompt.lower() and item["name"] not in all_used:
                        matches.append({
                            "prompt": prompt[:100],
                            "component": item["name"],
                            "trigger": trigger,
                        })

    return PreComputedFindings(
        empty_descriptions=empty,
        trigger_matches=matches[:50],  # Limit
        never_used=[...],
        name_collisions=[...],
        threshold_violations=[...],
    )
```

### 4. Agent Prompt Simplification

With pre-computed findings, agent prompt becomes:

```markdown
# Usage Insights Agent (Simplified)

You receive:
1. **pre_computed**: Deterministic findings (already validated)
2. **raw_data**: Sessions and discovery for semantic analysis

## Your Job

1. Format pre_computed findings into Problem → Impact → Action
2. Perform ADDITIONAL semantic analysis for:
   - Intent inference ("user probably wanted X")
   - Similarity matching ("prompt similar to skill Y")
   - Prioritization and recommendations

Don't re-check what's in pre_computed - it's already verified.
```

### 5. Output Structure

```json
{
  "_schema": {"version": "3.3"},
  "pre_computed_findings": {
    "empty_descriptions": ["skill-a", "skill-b"],
    "trigger_matches": [...],
    "never_used": [...],
    "name_collisions": [["commit", "commit"]]
  },
  "discovery": {...},
  "sessions": {...},
  "stats": {...}
}
```

## Consequences

- Faster analysis (deterministic checks instant)
- Lower token usage (less data to LLM)
- More consistent for simple checks
- LLM focused on what it's good at (inference, language)

## Implementation Priority

1. Add PreComputedFindings to collector (HIGH - easy win)
2. Update agent to use pre-computed (MEDIUM)
3. Add rules engine for Tier 2 patterns (LOW - future)

## Metrics to Track

- Token reduction from pre-filtering
- Consistency improvement for deterministic findings
- Latency reduction for analysis
