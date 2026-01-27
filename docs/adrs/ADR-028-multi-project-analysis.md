# ADR-028: Multi-Project Analysis Scope

**Status:** REJECTED
**Date:** 2026-01-27
**Category:** Feature
**Decision:** Speculative feature with no validated demand; defer indefinitely

## Context

Current analysis is single-project scoped. Users may want to analyze patterns across multiple projects.

## Use Cases

1. **Global skill effectiveness**: Which skills are used across all projects?
2. **Cross-project patterns**: Do certain workflows repeat?
3. **Plugin ROI**: Is a plugin valuable across the portfolio?
4. **Learning transfer**: Patterns from one project applicable to others?

## Proposed Privacy Mitigation

For global scope (if implemented):
- Aggregate counts only (no prompts)
- No session details
- Plugin/skill usage frequency only
- No cross-project correlation

## Blocking Questions

1. **Who consumes global stats?** Unclear what decisions they enable.
2. **Is this a real user need?** Or speculative feature?
3. **What specific insights are valuable?** Need concrete examples.

## Review Summary

### Backend Architect Review
- **Verdict:** NEEDS_MORE_INFO
- **Assessment:** Privacy mitigation is sound, but unclear value proposition
- **Recommendation:** Defer until concrete user demand exists

## Previous Concern

From ADR-005 review:
> "Cross-project awareness is an architectural anti-pattern"

This concern addressed by aggregation-only approach, but value still unclear.

## Research Findings (2026-01-27)

**User Demand Analysis:**

| Source | Evidence Found |
|--------|---------------|
| CHANGELOG | None |
| GitHub issues | None |
| Feature requests | None |
| Design documents | None |
| User feedback | None |

**Architectural Stance (from ADR-005):**
> "Cross-project awareness is an architectural anti-pattern - creates coupling and privacy violations"

**Alternative Already Implemented:**
Project context filtering addresses the actual problem:
- Tags plugin usage status (active/potential/unused)
- Filters insights to relevant plugins only
- Excludes patterns from other projects

## Final Decision

**REJECTED: Speculative feature, defer indefinitely**

**Rationale:**
1. Zero validated user demand
2. Explicitly marked as anti-pattern in ADR-005
3. Alternative (project filtering) already implemented
4. Privacy/isolation concerns remain even with aggregation-only approach
5. Cannot answer "what decisions does this enable?"

**When to Revisit:**
- User submits feature request with specific use case
- Use case includes concrete business value
- Justification for architectural coupling accepted

## Consequences

- No cross-project analysis implementation
- Continue with project-scoped analysis
- May revisit only if explicit user demand emerges
