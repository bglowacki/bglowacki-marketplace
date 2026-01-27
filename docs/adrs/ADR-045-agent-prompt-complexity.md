# ADR-045: Agent Prompt Complexity Reduction

**Status:** NEEDS_MORE_INFO
**Date:** 2026-01-27
**Category:** UX / Methodology
**Source:** Code exploration finding

## Context

The `usage-insights-agent.md` is 360 lines with:
- 6 distinct phases with conditional branches
- Complex state management (JSON selection in Phase 3)
- No error handling if parent doesn't resume correctly
- Deeply nested conditionals requiring careful sequencing

## Problem Statement

1. **Cognitive overload**: Agent has 6 phases with conditional branches
2. **State management**: Phase 3 outputs JSON expecting parent to resume
3. **Recovery**: If user interrupts mid-workflow, resuming is error-prone
4. **Maintainability**: Future maintainers struggle with phase dependencies

## Proposed Options

### Option A: Split into Focused Agents
Create 2-3 smaller agents, one per workflow phase:
- `usage-setup-analyzer` (Phase 1-2)
- `usage-category-recommender` (Phase 3-4)
- Benefits: Simpler prompts, better testability

### Option B: State Persistence
Add explicit state saving between phases:
- Save phase state to files for recovery
- Enables resumption after interruption

### Option C: Simplify Phase Logic
Use lookup tables instead of nested if-trees:
- Extract phase conditions into data structure
- Reduce prompt complexity

## Related ADRs

- ADR-023: Agent Output Structure
- ADR-030: Insights Agent Resumability

## Review Summary

### Backend Architect
- **Verdict:** NEEDS_MORE_INFO
- **Complexity:** HIGH
- **Missing:** Failure mode data, token counts, user validation

### System Architect
- **Verdict:** NEEDS_MORE_INFO
- **Missing:** Interruption frequency, phase dependency graph

## Questions Requiring Answers

1. How often are sessions interrupted mid-workflow?
2. What's the phase dependency graph? Can phases run independently?
3. What failure modes have been observed?
4. What is token count of typical agent response?

## Guidance

- If phases are truly independent: Option A (split agents)
- If phases have heavy dependencies: Option C (lookup tables)
- Avoid Option B unless resumability is user-facing requirement
