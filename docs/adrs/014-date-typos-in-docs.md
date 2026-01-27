# ADR-014: Date Typos in Design Documents

## Status
PROPOSED

## Context
Several design documents are dated 2025 but we're in 2026:
- `2025-01-19-prometheus-integration-design.md`
- `2025-01-20-enhanced-usage-analyzer-impl.md`
- `2025-01-20-enhanced-usage-analyzer-design.md`
- `2025-01-21-setup-first-analysis-design.md`
- `2025-01-21-setup-first-analysis-impl.md`
- `2025-01-23-focused-improvement-groups-design.md`
- `2025-01-23-plugin-usage-tagging-design.md`

The only correctly dated file is:
- `2026-01-27-best-practices-category-design.md`

## Finding
The dates appear to be typos (2025 vs 2026). This affects:
- File sorting by name
- Understanding the timeline of development
- Git archaeology (comparing dates to commits)

## Decision
TBD - Needs review

## Options

### Option A: Rename All Files
Correct dates to 2026.

**Pros**: Accurate timeline
**Cons**: Breaks git history, may be wrong if actually from 2025

### Option B: Leave As-Is
These could legitimately be from 2025 if the project started then.

**Pros**: Preserves original dates
**Cons**: Potentially confusing if they were typos

### Option C: Add README
Create `docs/plans/README.md` explaining the naming convention.

**Pros**: Context without file changes
**Cons**: Another file to maintain

## Recommendation
Verify via git history whether these are typos. If recent commits created these files in 2026, rename them. If they genuinely are from 2025, leave them.

```bash
git log --follow --format="%ai %s" -- observability/docs/plans/2025-01-19-prometheus-integration-design.md
```

## Impact
- Minor documentation correctness
- Helps with timeline understanding

## Review Notes
- Severity: Very Low (cosmetic)
- Effort: Low
- Risk: None
