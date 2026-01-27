# ADR-016: User Value Validation Process

**Status:** ACCEPTED
**Date:** 2026-01-27
**Category:** Process
**Decision:** Option B (MVP + Validate)

## Context

Multiple ADRs revealed features built without validated user need:
- ADR-010: Compaction metrics collected with no clear user value proposition
- ADR-004: Coverage gaps detected but "Do users even look at coverage gaps?"
- ADR-006: Interruption tracking but "Is interruption tracking even actionable?"

This is a recurring pattern: data collected → no interpretation → no action → wasted effort.

## Problem Statement

Features are being implemented before answering:
1. **Who wants this?** - User persona
2. **What will they do with it?** - Actionable outcome
3. **How will we know it worked?** - Success metric

## Decision

**ACCEPTED: Option B (MVP + Validate)**

Ship fast, measure, deprecate ruthlessly. 30-day validation window prevents analysis paralysis while ensuring dead features are removed.

## Implementation

### Lightweight Checklist (for PR templates)

```markdown
## Value Validation (new features/metrics only)

- [ ] User need identified (who wants this?)
- [ ] Actionable outcome defined (what will user do with it?)
- [ ] Validation plan (how to know if useful within 30 days?)
```

### Deprecation Process

1. Features without validated value after 30 days: mark for review
2. Features without usage after 60 days: mark for deprecation
3. Features deprecated for 30 days: remove in next release

### Integration

- Add checklist to PR template
- CI check: flag PRs adding metrics without linked validation doc (optional)

## Review Summary

### Backend Architect Review
- **Verdict:** ACCEPT
- **Key Point:** Option B aligns with lean principles
- **Concern:** Full validation process is overhead for personal project - lightweight approach preferred

## Consequences

- Prevents accumulation of unused metrics
- Forces thinking about user value early
- Lightweight enough to not block development
- May lead to more features being deprecated (good thing)
