# ADR-012: Plugin Version Documentation Mismatch

## Status
PROPOSED

## Context
Various documentation references different versions:
- `plugin.json`: version 2.2.0
- `CLAUDE.md`: mentions "v2.0.0" refactor
- Schema version: 3.1
- No CHANGELOG file

## Finding
There's no single source of truth for version history. Users can't determine:
- What changed in each version
- Which features were added/removed when
- Breaking changes between versions

## Decision
TBD - Needs review

## Recommendation
1. Add `CHANGELOG.md` following Keep a Changelog format:
```markdown
# Changelog

## [2.2.0] - 2026-01-27
### Added
- Best Practices category in usage-insights-agent
- Context7 integration for documentation lookup

## [2.1.0] - 2026-01-27
- Interrupted tool tracking with followup context

## [2.0.0] - 2026-01-19
### Changed
- Removed OTEL/Prometheus dependencies
- New JSONL-only architecture

### Removed
- OTEL Collector integration
- Prometheus alerts
- Kubernetes deployment scripts
```

2. Reference CHANGELOG in README
3. Update all version references to be consistent

## Impact
- Clear version history
- Users know what to expect from each version
- Easier to report and track issues

## Review Notes
- Severity: Low (documentation)
- Effort: Medium (archaeology of changes)
- Risk: None
