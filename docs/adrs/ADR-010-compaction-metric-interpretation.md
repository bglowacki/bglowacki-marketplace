# ADR-010: Compaction Metric Interpretation

**Status:** REJECTED
**Date:** 2026-01-27
**Category:** Methodology
**Decision:** Reject improvements - validate user need first

## Context

Compactions are tracked and reported (collect_usage.py:150-151, 1075-1076):

```python
if entry_type == "system" and entry.get("subtype") == "compact_boundary":
    session_data.compaction_count += 1

# Compute avg tools per compaction
avg_tools_per_compaction = (total_tools / jsonl_stats["total_compactions"]) if jsonl_stats["total_compactions"] > 0 else 0
```

## Problems Identified

1. **Metric without guidance**: What's a "good" compaction rate? No benchmarks
2. **No context size tracking**: Compactions triggered by context size, but we don't track size
3. **Tool count correlation unclear**: "Avg tools per compaction" - is higher better or worse?
4. **No actionable recommendations**: Data collected but no guidance on reducing compactions
5. **Session length confound**: Long sessions naturally have more compactions
6. **Quality impact unknown**: Do compactions affect response quality? Not measured

## Decision

**REJECTED: Feature may lack validated user need**

The ADR reveals that this feature was built without validated user need. Questions like "Do users care about compaction rates?" and "Is compaction frequency even controllable by users?" should have been answered BEFORE implementing the tracking.

## Review Summary

### System Architect Review
- **Recommendation:** REJECT
- **Rationale:** Data without interpretation is noise. If users cannot control or act on compaction rates, the metric should be removed, not enhanced.
- **Core Issue:** Metrics collected without clear user value proposition.

### Alternatives Considered
- Option B (Quality Metrics) - undefined success criteria, introduces ML dependency
- Option C (Benchmarking) - requires population-level data, privacy concerns

## Next Steps

1. Conduct user research on whether compaction visibility is valued
2. If valued: implement Option D (Actionable Recommendations) as text guidance
3. If not valued: **deprecate compaction tracking entirely**
4. Do not invest in Options B or C without proven user demand

## Consequences

- No immediate changes to codebase
- Research required before further investment
- Possible future deprecation of compaction metrics
