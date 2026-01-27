# Changelog

All notable changes to the bglowacki-marketplace plugins.

## [observability]

### [2.3.0] - 2026-01-27

#### Added
- Error logging for silent failures (ADR-023)
- Path constants for maintainability (ADR-020)
- Magic number constants for readability (ADR-009)
- YAML parse error context (ADR-028)
- Documentation for intentionally duplicated functions (ADR-003)
- Test suite with pytest (ADR-006)
  - test_outcome_detection.py - 40+ test cases
  - test_workflow_stages.py - 30+ test cases
  - test_session_parsing.py - 20+ test cases
- Research stage detection for Read/Grep/Glob/WebFetch (ADR-011)
- Debug stage detection for debugging skills/agents (ADR-011)

#### Changed
- Increased hook timeout from 5000ms to 10000ms (ADR-007)
- Rewritten root README.md to reflect current architecture (ADR-002)

#### Fixed
- Removed obsolete --no-prometheus flag from documentation (ADR-030)
- Updated marketplace.json description (ADR-029)

#### Security
- Added *.local.json to .gitignore (ADR-017)

### [2.2.0] - 2026-01-27

#### Added
- Best Practices category with Context7 integration in usage-insights-agent
- Interrupted tools tracking with followup context

#### Changed
- Plugin version bump for new features

### [2.1.0] - 2026-01-27

#### Added
- Interrupted tools detection in session parsing
- Followup context tracking

### [2.0.0] - 2026-01-27

#### Changed
- **BREAKING**: Removed OTEL/Prometheus infrastructure entirely
- Refactored to JSONL-only architecture
- Session analysis now uses built-in Claude Code session logs
- No external dependencies required

#### Removed
- OTEL Collector integration
- Prometheus alerts
- Alertmanager configuration
- Kubernetes deployment scripts
- `/observability-setup` and `/observability-uninstall` commands
- `PostToolUse`, `PreCompact`, `SessionStart` hooks

#### Added
- Stop hook for session summary generation
- Pure Python session parser (no dependencies)
- `usage-insights-agent` for data interpretation
- `workflow-optimizer` skill for recommendations

### [1.5.0] - 2026-01-20

#### Added
- Prometheus integration with alerts
- OTEL metrics pipeline
- Kubernetes deployment support

### [1.0.0] - 2026-01-15

#### Added
- Initial release
- Basic session tracking
- macOS notifications
