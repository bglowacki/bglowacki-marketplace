# ADR-003: Workflow Stage Inference Accuracy

**Status:** IMPLEMENTED
**Date:** 2026-01-27
**Category:** Methodology
**Decision:** Keep as informational-only; no accuracy fixes until consumer exists

## Context

The `infer_workflow_stage()` function (generate_session_summary.py:83-117) attempts to track workflow progression:

```python
def infer_workflow_stage(tool_name: str, tool_input: dict, current_stage: str) -> str:
    if tool_name == "Skill":
        skill = tool_input.get("skill", "").lower()
        if "brainstorm" in skill:
            return "brainstorm"
        if "plan" in skill or "writing-plans" in skill:
            return "plan"
    if tool_name in ("Edit", "Write"):
        return "implement"
```

## Problems Identified

1. **Edit/Write always means "implement"**: But editing a test file should be "test" stage
2. **No regression detection**: Going from test -> implement isn't captured as re-work
3. **Missing stages**: No "research", "debug", "refactor" stages
4. **Skill name dependency**: Relies on skill names containing keywords like "brainstorm"
5. **Bash command parsing is fragile**: "git commit" detection won't catch "GIT_EDITOR=vim git commit"
6. **No time-based inference**: Long gaps might indicate stage transitions
7. **Order-dependent**: Same tools in different order suggest different workflows

## Blocking Questions

Before making a decision, we need answers to:

1. **What decisions are made based on workflow stage data?**
   - If advisory only: lower accuracy is acceptable
   - If drives automation: need explicit markers

2. **What's the acceptable error rate?**

3. **Is "no stage detected" better than "wrong stage"?**

## Decision Options Under Consideration

### Option A: File-Path Aware Staging (Recommended if advisory)
Parse file paths - edits to `*_test.py` are "test" stage, edits to `docs/` are "document".

### Option D: Explicit Stage Markers (Recommended if automation-driving)
Require/encourage users to mark stages explicitly via skills or comments.

## Review Summary

### Backend Architect Review
- **Recommendation:** NEEDS_MORE_INFO
- **Key Question:** What are these metrics used for?
- **Concern:** State machine approach adds rigid constraints that real workflows violate

### DDD Architect Review
- **Recommendation:** Consider Event Storming (DNA M06) to model stage transitions
- **Concern:** Stage is not a first-class domain concept in current model

## Research Findings (2026-01-27)

**Downstream Usage Analysis Complete:**

| Consumer | Usage | Impact |
|----------|-------|--------|
| Quick Stats Display | Decorative (line counts) | None |
| JSON Output | Included but buried | None |
| usage-insights-agent | **NOT USED** | No recommendations based on stages |
| Prometheus Integration | Design only, never implemented | N/A |

**Key Finding:** Workflow stages are collected and stored but the insights agent does NOT use them for any recommendations. The feature provides "overhead without benefit" in its current form.

**Test Coverage:** 48 test cases validate the mechanism, but no tests validate that stages drive decisions.

## Final Decision

**ACCEPTED as informational-only feature.**

**Rationale:**
1. Data collection works correctly (48 tests prove mechanism)
2. Quick stats display is useful for user awareness
3. No consumer currently needs higher accuracy
4. Fixing accuracy issues (file-path awareness, regression detection) is wasted effort until a consumer exists

**Conditions to Revisit:**
- If insights agent is updated to use workflow stages for recommendations
- If users explicitly request stage-based insights
- If Prometheus integration is revived

## Consequences

- Keep current implementation as-is
- No accuracy improvements planned
- May revisit if user demand emerges for stage-based recommendations
