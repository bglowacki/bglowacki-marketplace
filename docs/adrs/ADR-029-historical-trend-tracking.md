# ADR-029: Historical Trend Tracking

**Status:** REJECTED
**Date:** 2026-01-27
**Category:** Feature
**Decision:** Defer - speculative feature

## Context

Current analysis is point-in-time snapshot. Proposal to track trends over time.

## Proposed Use Cases

1. **Skill adoption**: Is skill X being used more over time?
2. **Error rate trends**: Are failures increasing or decreasing?
3. **Compaction trends**: Is context efficiency improving?
4. **Regression detection**: Did recent changes break patterns?

## Decision

**REJECTED: Speculative feature with unclear value**

Build when users explicitly request trends, not speculatively.

## Concerns That Led to Rejection

1. **Storage growth**: History accumulates over time
2. **Comparison validity**: Different session counts may not be comparable
3. **Configuration changes**: Trend invalid if analysis config changed
4. **Value unclear**: Do users actually want trends?

## Review Summary

### Backend Architect Review
- **Verdict:** REJECT
- **Assessment:** Speculative feature with storage and comparison validity concerns
- **Recommendation:** Build when users explicitly request

## Alternative

If trend tracking is needed later:
- Start with simple 7-day rolling comparison
- Store minimal delta (not full history)
- Validate with real users first

## Consequences

- No storage overhead from history
- Simpler codebase
- May revisit if user demand emerges
