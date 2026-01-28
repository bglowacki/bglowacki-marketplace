# ADR-051: Agent Prompt Simplification and Consistency

**Status:** PROPOSED
**Date:** 2026-01-28
**Category:** Architecture
**Source:** Deep research on LLM best practices

## Context

The usage-insights-agent.md is 361 lines with:
- 6 distinct phases with conditional branches
- Complex state management (JSON output for parent agent in Phase 3)
- Multiple output format specifications
- Deeply nested conditionals

## Research Findings

From [Arize LLM Observability](https://arize.com/):
> "Unlike traditional software, LLMs produce probabilistic outputs, meaning identical inputs can yield different responses."

From [Microsoft Copilot Observability](https://learn.microsoft.com/en-us/microsoft-cloud/dev/copilot/isv/observability-for-ai):
> "AI observability succeeds when treated as instrumentation architecture, not tool selection."

Key insight: **Simpler prompts produce more consistent LLM outputs**.

## Problem Statement

1. **Inconsistent execution**: 361-line prompt with phases → variable adherence
2. **Phase coupling**: Phase 3 outputs JSON expecting parent to resume
3. **Format proliferation**: Multiple markdown table formats throughout
4. **Recovery issues**: If interrupted mid-workflow, resuming is error-prone
5. **Maintenance burden**: Changes ripple through multiple sections

## Proposed Solution

### Option A: Split into Focused Agents (Recommended)

Replace 1 complex agent with 3 focused ones:

```
usage-setup-analyzer     # Phase 0-1: Plugin efficiency + Setup summary
usage-pattern-detector   # Phase 2-3: Internal analysis + Category summary
usage-finding-expander   # Phase 4: Expand selected categories
```

Each agent:
- Single responsibility
- < 100 lines
- Deterministic input/output contract
- Testable independently

### Option B: State Machine with Explicit Checkpoints

Keep single agent but add explicit state:

```python
@dataclass
class AnalysisState:
    phase: int
    setup_summary: str | None
    categories: list[dict]
    expanded: list[str]
    checkpoint_file: Path

def save_checkpoint(state: AnalysisState):
    """Save state for recovery."""
    state.checkpoint_file.write_text(json.dumps(asdict(state)))
```

### Option C: Template-Based Output (Partial Fix)

Extract output formats to templates:

```markdown
<!-- template: category_table -->
| Category | Issues | Priority | Description |
|----------|--------|----------|-------------|
{{#each categories}}
| {{label}} | {{count}} | {{priority}} | {{description}} |
{{/each}}
```

## Recommendation

**Option A (Split Agents)** because:
1. Aligns with single-responsibility principle
2. Each agent can be tested/validated independently
3. Reduces LLM variance by simplifying prompts
4. Easier to maintain and extend

## Implementation Sketch

### usage-setup-analyzer.md (~80 lines)
```markdown
# Setup Analyzer

Input: JSON from collect_usage.py
Output: Setup summary + plugin efficiency report

## Steps
1. Read setup_profile from input
2. Generate plugin efficiency section
3. Generate component distribution table
4. List red flags and coverage gaps
5. Output structured markdown
```

### usage-pattern-detector.md (~100 lines)
```markdown
# Pattern Detector

Input: JSON + setup summary
Output: Categorized findings with counts

## Steps
1. Analyze sessions for missed opportunities
2. Categorize findings (one per category)
3. Calculate priority per category
4. Output category summary + JSON block
```

### usage-finding-expander.md (~80 lines)
```markdown
# Finding Expander

Input: Category list + user selection
Output: Detailed findings for selected categories

## Steps
1. For each selected category
2. Generate Problem → Impact → Action format
3. Include specific examples and fixes
```

## Consequences

- More predictable agent behavior
- Easier testing (unit test each agent)
- Clearer ownership of each phase
- Simpler recovery (restart from any agent)

## Migration Path

1. Extract Phase 0-1 to usage-setup-analyzer
2. Test with real data
3. Extract Phase 2-3 to usage-pattern-detector
4. Update workflow-optimizer to call new agents
5. Deprecate monolithic agent
