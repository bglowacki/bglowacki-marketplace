# Changelog

All notable changes to the observability plugin.

## [2.8.0] - 2026-02-04

### Added
- Outdated plugin detection: compares installed versions against remote marketplace via GitHub API
- Stale cache detection: temp_git leftovers, old version accumulation, orphaned marketplaces
- New pre-computed finding types: `outdated_plugins` and `stale_cache`
- 19 new tests in `test_outdated_checks.py`

## [2.3.0] - 2026-01-27

### Added
- Test suite for core functionality (ADR-006)
  - `test_outcome_detection.py`
  - `test_session_parsing.py`
  - `test_workflow_stages.py`
- Research and debug workflow stages (ADR-011)

### Changed
- Hook timeout increased to 10000ms (ADR-007)

## [2.2.0] - 2026-01-27

### Added
- Best Practices category in usage-insights-agent
- Context7 integration for documentation lookup

## [2.1.0] - 2026-01-27

### Added
- Interrupted tool tracking with followup context

## [2.0.0] - 2026-01-19

### Changed
- Complete architecture refactor to JSONL-only
- Removed all external infrastructure dependencies

### Removed
- OTEL Collector integration
- Prometheus metrics and alerts
- Alertmanager integration
- Kubernetes deployment scripts

## [1.16.0] - 2026-01-23

### Added
- Coverage-aware recommendations in workflow-optimizer
- Removal recommendations for unused components

## [1.15.0] - 2026-01-22

### Added
- Setup profile analysis
- Category-based filtering in insights agent
- Fuzzy project matching in collector

## [1.0.0] - 2026-01-19

### Added
- Initial release
- Session summary generation via Stop hook
- Usage collector skill
- Workflow optimizer skill
- Usage insights agent
