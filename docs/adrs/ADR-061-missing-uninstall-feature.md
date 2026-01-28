# ADR-016: Missing Uninstall/Cleanup Feature

## Status
PROPOSED

## Context
The root README.md references an `/observability-uninstall` command:
```
#### Uninstall

Remove the entire observability stack:

/observability-uninstall

This removes OTEL Collector, Prometheus, Grafana, cert-manager, and all related namespaces.
```

However, this refers to the old OTEL-based architecture that was removed in v2.0.0.

## Finding
There's no current uninstall or cleanup command. The plugin creates files in:
- `~/.claude/session-summaries/` - Session summary JSON files

These can accumulate over time and have no cleanup mechanism.

## Decision
TBD - Needs review

## Options

### Option A: Add Cleanup Command
Create `/observability-cleanup` command to:
- Delete session summaries older than N days
- Show disk usage of summary files
- Option to delete all data

**Pros**: User control over disk usage
**Cons**: New feature to maintain

### Option B: Auto-Cleanup in Hook
Add age-based cleanup to the Stop hook - delete summaries older than 30 days.

**Pros**: Automatic, no user action needed
**Cons**: Invisible to user, may delete wanted data

### Option C: Document Manual Cleanup
Add cleanup instructions to README.

**Pros**: No code changes
**Cons**: User must remember to clean up

### Option D: No Action
Session summaries are small (<5KB each), accumulation is negligible.

**Pros**: No changes needed
**Cons**: Unbounded growth

## Recommendation
Option A - Add simple cleanup command. Session summaries are useful but should be manageable:

```bash
# Show disk usage
/observability-cleanup --stats

# Delete older than 30 days
/observability-cleanup --older-than 30d

# Delete all
/observability-cleanup --all
```

## Impact
- User control over plugin data
- Prevents unbounded disk usage
- Clear data management story

## Review Notes
- Severity: Low (nice-to-have)
- Effort: Low-Medium
- Risk: Low
