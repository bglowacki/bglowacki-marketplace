# ADR-013: Archive Stale Design Documents

## Status
PROPOSED

## Context
The `observability/docs/plans/` directory contains design documents for features that were later removed or significantly changed:

1. `2025-01-19-prometheus-integration-design.md` - Status: "Approved" but feature was removed in v2.0.0
2. References `config/endpoint.env` files that don't exist in current architecture
3. References metrics and queries that are no longer relevant

## Finding
**Files**: `observability/docs/plans/2025-01-19-prometheus-integration-design.md`

Having "Approved" design documents for removed features creates confusion:
- New contributors may think Prometheus is still supported
- Design decisions aren't documented as "superseded"
- No record of WHY features were removed

## Decision
TBD - Needs review

## Options

### Option A: Archive with Status Update
Move to `docs/archive/` and update status to "Superseded by JSONL-only architecture"

**Pros**: Preserves history, clarifies current state
**Cons**: Requires directory restructuring

### Option B: Add Superseded Note
Keep in place, add note at top: "⚠️ SUPERSEDED: This feature was removed in v2.0.0"

**Pros**: Minimal change, preserves git history
**Cons**: Clutter in plans directory

### Option C: Delete
Remove outdated documents entirely.

**Pros**: Clean directory
**Cons**: Loses historical context

## Recommendation
Option B as quick fix. Add deprecation note at top of each superseded document:

```markdown
> ⚠️ **SUPERSEDED**: This design was implemented but later removed in v2.0.0
> (refactor to JSONL-only architecture). Kept for historical reference.
```

## Impact
- Clarifies what's current vs historical
- Prevents confusion for new contributors
- Preserves design decision history

## Review Notes
- Severity: Low (documentation)
- Effort: Low
- Risk: None
