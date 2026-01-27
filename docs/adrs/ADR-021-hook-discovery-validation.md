# ADR-021: Hook Discovery and Validation

**Status:** ACCEPTED
**Date:** 2026-01-27
**Category:** Methodology
**Decision:** Option B (Warning-Based Validation)

## Context

The `discover_hooks()` function (collect_usage.py:613-712) parses hooks from multiple sources:
- Global settings.json
- Project settings.json
- Project-local settings.json
- Plugin manifests

## Problems Identified

1. **No validation of hook commands**: Hooks reference scripts that may not exist
2. **No timeout enforcement check**: Hooks without timeout may hang indefinitely
3. **Multiple format handling**: Hooks can be dict or list, complex parsing required
4. **Plugin hook isolation unclear**: Can plugins override project hooks?
5. **Hook execution order undocumented**: If multiple hooks match, which runs first?
6. **No hook health monitoring**: Failed hooks not tracked in analysis

## Decision

**ACCEPTED: Option B (Warning-Based Validation)**

Continue analysis but surface validation issues as warnings in red flags. Blocking analysis due to misconfigured hooks is too aggressive for a diagnostic tool.

## Implementation Plan

### Validation Checks (as warnings)

1. **Path validation**: Check if hook command path exists
2. **Timeout presence**: Warn if hook lacks timeout field
3. **Timeout range**: Warn if timeout > 30s (excessive) or < 1s (too short)
4. **Permission check**: Verify hook scripts are executable

### Hook Priority Hierarchy (documented)

Explicit precedence when same event has multiple hooks:
1. Project-local settings (highest)
2. Project settings
3. Plugin hooks
4. Global settings (lowest)

### Telemetry Integration

Track hook execution from session data (passive observation):
- Which hooks fired
- Success/failure outcomes
- Execution duration

## Review Summary

### Backend Architect Review
- **Verdict:** ACCEPT
- **Rationale:** Warning-based preserves usability while surfacing issues
- **Addition:** Hook execution telemetry should be passive, not pre-validated
- **Clarification needed:** Behavior when same hook registered multiple times at same level

## Consequences

- Users see hook configuration issues in red flags
- Analysis never blocked by hook misconfigurations
- Clear priority hierarchy documented
- Future: track hook execution patterns from session data
