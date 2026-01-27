# ADR-009: Session Sampling Strategy

**Status:** ACCEPTED
**Date:** 2026-01-27
**Category:** Methodology
**Decision:** Option D (Incremental Analysis) with Option A fallback for cold-start

## Context

The collector uses a simple most-recent sampling (collect_usage.py:835-846):

```python
def find_project_sessions(projects_dir: Path, project_dir: Path, max_sessions: int) -> list[Path]:
    session_files = sorted(
        project_dir.glob("*.jsonl"),
        key=lambda p: p.stat().st_mtime,
        reverse=True
    )
    return session_files[:max_sessions]
```

Default is 10 sessions, configurable via `--sessions`.

## Problems Identified

1. **Recency bias**: Only recent sessions analyzed, historical patterns lost
2. **No diversity sampling**: Might get 10 similar sessions vs diverse workflows
3. **Session size ignored**: Short sessions (2 prompts) weighted same as long (100 prompts)
4. **No stratification**: Can't ensure coverage of different workflow types
5. **Fixed count arbitrary**: Why 10? Maybe need 5 for simple, 50 for complex analysis
6. **No incremental updates**: Re-analyzes everything instead of tracking deltas

## Decision

**ACCEPTED: Option D (Incremental) as primary, Option A (Stratified) for cold-start**

Implement incremental analysis as the default mechanism. Store `last_processed_timestamp` in state file. For first run or explicit full-analysis, use stratified sampling with deterministic seed.

## Implementation Plan

1. Create `.claude/observability-state.json` to track processing state
2. On normal run: only process sessions newer than `last_processed_timestamp`
3. Aggregates must be **additive** (counters, histograms) - store sums and counts separately for averages
4. Add `--full-analysis` flag for stratified cold-start behavior
5. Weight sessions by prompt count in aggregation

## Review Summary

### Backend Architect Review
- **Recommendation:** ACCEPT (Option D with A for cold-start)
- **Key Point:** Incremental is idempotent, resumable, and scales with session volume
- **Implementation Note:** Aggregates must be additive; averages require sums + counts

### System Architect Review
- **Note:** Recency bias often acceptable for operational analytics - old sessions may reflect outdated tooling
- **Consideration:** Weight by prompt count or tool invocations

## Consequences

- Faster analysis on repeat runs (only new sessions processed)
- Requires persistent state management
- Full historical analysis still available via flag
