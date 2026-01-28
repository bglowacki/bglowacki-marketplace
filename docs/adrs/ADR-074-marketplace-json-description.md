# ADR-029: Marketplace.json Description References Removed OTEL Features

## Status
PROPOSED

## Context
The `marketplace.json` description is inconsistent with the current plugin implementation.

## Finding
**Files**:
- `.claude-plugin/marketplace.json:13`: `"description": "OTEL metrics, alerts, and session summaries for Claude Code"`
- `observability/.claude-plugin/plugin.json:3`: `"description": "Usage analysis from Claude Code session logs"`

The marketplace description references "OTEL metrics and alerts", which were removed in v2.0.0 when the plugin switched to JSONL-only architecture.

## Impact
- Users see outdated information in the marketplace
- Creates confusion about what the plugin actually does
- Misaligns with actual plugin capabilities

## Recommendation
Update `marketplace.json` line 13 to match `plugin.json`:
```json
"description": "Usage analysis from Claude Code session logs"
```

## Related
- ADR-001: Similar issue with marketplace description (covers different aspect)
- ADR-002: Root README also references removed features

## Review Notes
- Severity: Medium (user-facing documentation)
- Effort: Trivial (single line change)
- Risk: None
