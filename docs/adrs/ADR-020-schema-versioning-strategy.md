# ADR-020: Schema Versioning Strategy

**Status:** ACCEPTED
**Date:** 2026-01-27
**Category:** Architecture
**Decision:** Option A (Batch Minor Changes)

## Context

Multiple ADRs propose schema changes:
- ADR-002: Add confidence scoring to outcomes
- ADR-005: Component-level granularity in plugin usage
- ADR-006: Duration field for interrupted tools
- ADR-015: Add `is_truncated` flag to output

Current schema version: 3.1 (from collect_usage.py:1079)

## Decision

**ACCEPTED: Option A (Batch Minor Changes)**

All proposed changes from ADR-002/005/006/015 are additive. Ship as single minor version bump to 3.2.

## Versioning Policy

### Semantic Versioning for Schema

- **Major (X.0.0)**: Breaking changes, consumers must update
- **Minor (X.Y.0)**: Additive changes, backwards compatible
- **Patch (X.Y.Z)**: Clarifications, no structural changes

### Compatibility Matrix

| Change Type | Version Bump | Migration Required |
|------------|--------------|-------------------|
| Add optional field | Minor | No |
| Add required field | Major | Yes |
| Remove field | Major | Yes |
| Change field type | Major | Yes |
| Add enum value | Minor | No |

### Support Policy

- Support N-1 major version for 6 months
- Minor versions are always backwards compatible
- Prefer single-version with migration scripts over multi-version support

## Implementation Plan

1. Create `observability/schemas/` directory:
   - `analysis_v3.1.json` - Current schema
   - `analysis_v3.2.json` - New schema with all ADR changes
   - `CHANGELOG.md` - Schema version history

2. Version 3.2 changes (all additive):
   ```json
   {
     "stats.outcomes.confidence": "number (0-1)",  // ADR-002
     "setup_profile.plugin_usage.components": "object",  // ADR-005
     "stats.interruptions[].duration_ms": "integer",  // ADR-006
     "sessions.prompts[].is_truncated": "boolean"  // ADR-015
   }
   ```

3. Migration strategy:
   - Re-analyze from source JSONL (source of truth)
   - No stored aggregate migration needed (regenerate)

## Review Summary

### Backend Architect Review
- **Verdict:** ACCEPT
- **Recommendation:** JSON Schema is worth the cost for validation and documentation
- **Key Point:** Batching additive changes reduces version churn

## Consequences

- Single version bump (3.2) for all pending changes
- Formal JSON Schema provides validation and documentation
- Clear support policy for consumers
- Re-analysis migration keeps source JSONL as authority
