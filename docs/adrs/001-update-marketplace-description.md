# ADR-001: Update Marketplace Description

## Status
PROPOSED

## Context
The marketplace.json file at `.claude-plugin/marketplace.json` describes the observability plugin as "OTEL metrics, alerts, and session summaries for Claude Code". However, the plugin was refactored to use JSONL-only architecture in v2.0.0, removing OTEL and Prometheus dependencies.

## Finding
**File**: `.claude-plugin/marketplace.json:14`
**Current**: `"description": "OTEL metrics, alerts, and session summaries for Claude Code"`
**Expected**: Description should reflect JSONL-based session analysis

## Decision
TBD - Needs review

## Recommendation
Update description to: "Session analysis and usage insights from Claude Code JSONL logs"

## Impact
- User expectations will match actual functionality
- No breaking changes
- Improves plugin discoverability with accurate keywords

## Review Notes
- Severity: Medium (misleading documentation)
- Effort: Trivial (single line change)
- Risk: None
