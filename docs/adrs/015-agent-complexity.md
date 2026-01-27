# ADR-015: Reduce Usage-Insights-Agent Complexity

## Status
PROPOSED

## Context
The `usage-insights-agent.md` file is 361 lines with complex multi-phase workflows:
- Phase 0: Plugin Efficiency
- Phase 1: Setup Understanding
- Phase 2: Internal Analysis
- Phase 3: Category Summary
- Phase 4: Expand Selected Categories

Plus extensive tables, formatting templates, and edge case handling.

## Finding
**File**: `observability/agents/usage-insights-agent.md`
**Lines**: 361

This complexity:
- Makes the agent hard to maintain
- Increases chance of LLM not following instructions
- Difficult to test or validate behavior
- Contains embedded JSON schema documentation

## Decision
TBD - Needs review

## Options

### Option A: Split into Multiple Agents
Create specialized sub-agents:
- `setup-analyzer-agent.md` - Phase 0-1
- `usage-pattern-agent.md` - Phase 2-3
- `finding-expander-agent.md` - Phase 4

**Pros**: Focused responsibilities, easier to test
**Cons**: Orchestration complexity, more files

### Option B: Simplify the Agent
Reduce phases, simplify output format, remove edge cases to separate documentation.

**Pros**: Easier to follow, more reliable
**Cons**: May lose functionality

### Option C: Accept Complexity
The complexity is necessary for the feature set.

**Pros**: Full functionality preserved
**Cons**: Maintenance burden

### Option D: Extract Templates
Move output templates and tables to separate reference file.

**Pros**: Agent focuses on logic, templates in one place
**Cons**: Agent needs to reference external file

## Recommendation
Option D first - extract templates and format specifications to a separate file. This reduces agent size while preserving functionality.

Create `docs/agent-templates/usage-insights-templates.md` with all the markdown templates, and reference it from the agent.

## Impact
- Easier agent maintenance
- More reliable LLM following
- Better separation of concerns

## Review Notes
- Severity: Medium (maintainability)
- Effort: Medium
- Risk: Low (refactoring, not functional change)
