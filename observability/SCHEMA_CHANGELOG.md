# Output Schema Changelog

Schema versions for the JSON output from `collect_usage.py`.

## v3.2 (2026-01-30)

### Added
- `rendered` dict on each overlap entry in `setup_profile.overlapping_triggers` with `problem`, `evidence`, `action` fields
- `overlap_findings` array in `pre_computed_findings` with `finding_type: "overlap_resolution"` entries
- Walk-through agent template for overlap resolution findings

### Migration Notes (v3.1 → v3.2)
- Non-breaking: new fields are additive
- Consumers should handle missing `rendered` gracefully (use `hint` as fallback for `problem`)

## v3.1 (2026-01-27)

### Added
- `interrupted_tools` array with followup context tracking
- `disabled_but_matched` field in `plugin_usage` for components that match but are disabled
- `research` and `debug` workflow stages

## v3.0 (2026-01-20)

### Added
- Initial schema version tracking
- `_schema` metadata block with version, generated_at, generator
- `setup_profile` with complexity, shape, red_flags analysis
- `plugin_usage` with skills, agents, commands, hooks breakdown
- `workflow_stages` tracking (brainstorm, plan, implement, test, review, commit)

### Structure
```json
{
  "_schema": {
    "version": "3.1",
    "generated_at": "ISO timestamp",
    "generator": "collect_usage.py"
  },
  "summary": { ... },
  "sessions": [ ... ],
  "setup_profile": { ... },
  "plugin_usage": { ... }
}
```

## Migration Notes

### v3.0 → v3.1
- Non-breaking: new fields are additive
- Consumers should handle missing `interrupted_tools` gracefully
