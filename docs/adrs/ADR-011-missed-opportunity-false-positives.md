# ADR-011: Missed Opportunity False Positive Reduction

**Status:** NEEDS_MORE_INFO
**Date:** 2026-01-27
**Category:** Methodology
**Decision:** Pending - requires false positive rate data

## Context

Missed opportunities are detected by matching prompts to unused skills (collect_usage.py:1027-1052):

```python
for prompt in session.prompts:
    matches = find_matches(prompt, all_items)
    for item, triggers in matches:
        was_used = False
        if item.type == "skill" and item.name in session.skills_used:
            was_used = True
        # ... check if used ...
        if not was_used:
            missed.append(MissedOpportunity(...))
```

## Problems Identified

1. **Intent blindness**: User might intentionally not use a skill
2. **Context loss**: Maybe skill was used in previous session for same task
3. **Equivalent alternatives**: User used skill A which does same as skill B
4. **Learning sessions**: User exploring manually before automating
5. **Partial matches count as full**: "debug test" matches "debug" skill but intent was testing
6. **No feedback mechanism**: Can't mark false positives to improve future detection

## Blocking Questions

1. **What is the actual false positive rate?** Need labeled data to assess.
2. **How annoying are false positives to users?** Need user feedback.
3. **Should we err on side of more or fewer recommendations?**

## Domain Model Gap (DDD Review)

The ADR correctly identifies that **UserIntent** is a missing first-class domain concept:
- **Primary intent**: What the user wants to achieve
- **Task context**: Multi-session continuity
- **Exploration mode**: Learning vs doing

Consider Event Storming to model:
- `PromptReceived`
- `IntentClassified`
- `OpportunityIdentified`
- `OpportunityConfirmed` or `OpportunityDismissed` (user feedback)

## Decision Options Under Consideration

### Option A: Intent Classification
Requires defining intent taxonomy first.

### Option B: Skill Equivalence Mapping
Define which skills are alternatives to reduce redundant recommendations.

### Option C: User Feedback Integration
Allow users to mark false positives - most accurate but requires UX work.

### Option D: Confidence Scoring
Report confidence level for each missed opportunity.

## Review Summary

### DDD Architect Review
- **Recommendation:** NEEDS_MORE_INFO
- **Missing:** How is UserIntent captured or inferred?
- **Boundary Question:** What is the aggregate boundary for opportunity tracking across sessions?

## Research Findings (2026-01-27)

**False Positive Sources Identified:**

| Source | Example | Severity |
|--------|---------|----------|
| Intent blindness | User intentionally skips skill | HIGH |
| Negation not handled | "don't debug" matches "debug" | MEDIUM |
| Context loss | Skill used in previous session | MEDIUM |
| 3-char trigger bug | "TDD" filtered out (ADR-001 fix pending) | MEDIUM |
| Equivalent alternatives | User chose different approach | LOW |

**Critical Gap:** No test coverage for `find_matches()` function.

**False Positive Rate:** UNKNOWN - requires labeled dataset to measure.

**Proposed Validation Approach:**
1. Sample 20-30 sessions with diverse prompts
2. Manually label each match: True Positive / False Positive / Uncertain
3. Calculate baseline rate before implementing fixes

## Updated Decision

**Status remains NEEDS_MORE_INFO but path forward is clear:**

**Phase 1 (Required First):**
- Collect validation data per approach above
- Establish baseline false positive rate

**Phase 2 (After Phase 1):**
- If rate >30%: Implement Option D (Confidence Scoring)
- Add negation detection: `(?:don't|do not|avoid)\s+.*?TRIGGER`
- Fix 3-char bug (ADR-001)

**Phase 3 (If needed):**
- Consider Option C (User Feedback) if confidence scoring insufficient

## Consequences

- Cannot proceed without validation data
- Quick win: ADR-001 fixes 3-char trigger bug
- Negation detection is low-risk improvement
