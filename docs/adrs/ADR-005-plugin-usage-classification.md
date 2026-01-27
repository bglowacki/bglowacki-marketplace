# ADR-005: Plugin Usage Classification Accuracy

**Status:** ACCEPTED
**Date:** 2026-01-27
**Category:** Methodology
**Decision:** Combine Options A (Frequency Scoring) + D (Component-Level), reject Option C

## Context

The `compute_plugin_usage()` function (collect_usage.py:253-352) classifies plugins into categories:
- active: Used in sessions
- potential: Enabled + matched prompts but not triggered
- unused: Enabled but no activity
- disabled_but_matched: Disabled but matched prompts
- already_disabled: Disabled and no matches

## Problems Identified

1. **Session count dependency**: "Unused" after 10 sessions might become "active" with more data
2. **Prompt matching quality**: Same issues as ADR-001 trigger matching
3. **No decay factor**: Old usage counts same as recent usage
4. **Project-scope confusion**: Plugin might be used heavily in one project but classified by current project only
5. **Binary used/not-used**: No frequency consideration - used once = active
6. **Component-level vs plugin-level**: Plugin with 10 skills might be "used" if 1 skill is invoked once

## Decision

**ACCEPTED: Options A + D, explicitly reject Option C**

1. Implement frequency bands: never/rarely/sometimes/often
2. Track at component-level (individual skills/agents), not just plugin-level
3. **Explicitly REJECT Option C (Cross-Project Awareness)** - architectural anti-pattern that violates project isolation

## Implementation Plan

1. Define frequency thresholds as configurable parameters:
   - never: 0 uses
   - rarely: 1-2 uses
   - sometimes: 3-10 uses
   - often: 10+ uses

2. Track component-level granularity:
   ```python
   {
     "plugin:observability": {
       "frequency": "sometimes",
       "components": {
         "usage-collector": "often",
         "workflow-optimizer": "never"
       }
     }
   }
   ```

3. Add "staleness" flag (last-used > N days) as simpler alternative to full time-weighting

## Review Summary

### System Architect Review
- **Recommendation:** ACCEPT with modifications
- **Key Point:** Cross-project awareness is an architectural anti-pattern - creates coupling and privacy violations
- **Alternative:** Add "staleness" flag instead of time-weighted decay

### Scalability Concerns
- Component-level tracking multiplies storage by avg components/plugin (5-10x) - acceptable
- Time-weighted decay requires either real-time computation or batch job complexity

## Consequences

- More granular recommendations at component level
- Frequency bands provide nuance without over-engineering
- Cross-project isolation maintained
