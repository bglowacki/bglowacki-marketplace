# ADR-014: Category Priority Calculation

**Status:** REJECTED (Deep Research)
**Date:** 2026-01-27
**Category:** Methodology
**Decision:** Option A (Weighted Issue Scoring) with Policy pattern

## Context

The usage-insights-agent calculates priority (usage-insights-agent.md:36-38):

```markdown
### Priority Calculation

- **High**: Category has 5+ issues OR contains a red flag from setup_profile
- **Medium**: Category has 2-4 issues
- **Low**: Category has 1 issue
```

## Problems Identified

1. **Issue count is crude**: 5 trivial issues shouldn't outrank 1 critical issue
2. **No issue severity**: All issues weighted equally
3. **Red flag escalation unclear**: Which red flags escalate which categories?
4. **No impact estimation**: Priority should consider user impact, not just count
5. **Threshold values arbitrary**: Why 5 for high? Why not 3 or 7?
6. **No confidence adjustment**: Category with uncertain findings shouldn't be high priority

## Decision

**ACCEPTED: Option A with Policy Pattern**

1. Implement weighted issue scoring with IssueSeverity Value Object
2. Extract priority calculation into explicit Policy object
3. Define severity weights: Critical=5, Major=3, Minor=1

## Implementation Plan

```python
class IssueSeverity(Enum):
    CRITICAL = 5
    MAJOR = 3
    MINOR = 1

class PriorityPolicy:
    def calculate(self, category: ImprovementCategory) -> Priority:
        if category.has_red_flag():
            return Priority.HIGH
        weighted_score = sum(issue.severity.value for issue in category.issues)
        if weighted_score >= 10:
            return Priority.HIGH
        if weighted_score >= 5:
            return Priority.MEDIUM
        return Priority.LOW
```

This separates policy from data, allowing different policies for different contexts.

## Review Summary

### DDD Architect Review
- **Recommendation:** ACCEPT with conditions
- **Key Issue:** Current model is anemic - business logic outside domain model
- **Missing Invariant:** "A category with Critical issue is always High priority"
- **Pattern:** Extract priority as Policy object for flexibility

### Severity Weights
- Critical: Security issues, data loss risks, blocking errors
- Major: Functionality gaps, significant inefficiencies
- Minor: Style issues, minor optimizations, suggestions

## Consequences

- Priority accurately reflects issue impact, not just count
- Policy pattern enables user-specific priority preferences
- Requires categorizing all findings with severity level
