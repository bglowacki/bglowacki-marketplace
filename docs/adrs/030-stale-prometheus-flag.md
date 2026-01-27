# ADR-030: Documentation References Non-Existent --no-prometheus Flag

## Status
PROPOSED

## Context
Command documentation shows a flag that doesn't exist in the implementation.

## Finding
**File**: `observability/commands/observability-usage-collector.md:44`

```bash
uv run ... --no-prometheus > /tmp/usage-data.json
```

The `--no-prometheus` flag is documented but doesn't exist in `collect_usage.py`. The actual argument parser (lines 1358-1366) only supports:
- `--sessions`
- `--format`
- `--verbose`
- `--project`
- `--quick-stats`
- `--days`

## Impact
- Users may try non-existent flag and get argument parsing errors
- Suggests Prometheus is still a feature option (it was removed in v2.0.0)

## Recommendation
Remove `--no-prometheus` from the documentation. The flag is no longer needed since Prometheus infrastructure was completely removed.

## Review Notes
- Severity: Low (documentation only)
- Effort: Trivial
- Risk: None
