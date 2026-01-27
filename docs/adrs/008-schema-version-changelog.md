# ADR-008: Add JSON Schema Version Changelog

## Status
PROPOSED

## Context
The `collect_usage.py` script outputs JSON with a schema version:
```json
"_schema": {
  "version": "3.1",
  ...
}
```

However, there's no documentation of what changed between versions (3.0 → 3.1, or earlier versions).

## Finding
**File**: `collect_usage.py:1057-1066`

Without a changelog:
- Consumers can't adapt to schema changes
- Breaking changes aren't documented
- No migration guidance for downstream tools

## Decision
TBD - Needs review

## Recommendation
Add `SCHEMA_CHANGELOG.md` documenting:
- v3.1 changes (current)
- v3.0 baseline
- Any field additions/removals/renames
- Breaking vs non-breaking changes

Example:
```markdown
# Output Schema Changelog

## v3.1 (2026-01-27)
- Added `interrupted_tools` with followup context
- Added `disabled_but_matched` to plugin_usage

## v3.0 (2026-01-20)
- Initial schema version tracking
- Added `setup_profile` with complexity/shape/red_flags
```

## Impact
- Enables downstream tools to handle schema evolution
- Documents design decisions
- Facilitates debugging version mismatches

## Review Notes
- Severity: Low (documentation)
- Effort: Low
- Risk: None
