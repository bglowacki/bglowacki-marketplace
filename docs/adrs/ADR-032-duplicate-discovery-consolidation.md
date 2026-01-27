# ADR-032: Consolidate Duplicate Discovery Logic

**Status:** ACCEPTED
**Date:** 2026-01-27
**Category:** Architecture
**Source:** Research finding from ADR-022 performance analysis

## Context

During ADR-022 research, discovered duplicate version detection logic in:
- `discover_from_plugins()` (line 540)
- `discover_hooks()` (line 685)

Same traversal executed twice per analysis run = ~125 wasted syscalls.

## Proposed Solution

Extract shared `get_latest_plugin_versions()` function to cache version paths.

## Impact

- **Performance**: Eliminate ~125 redundant syscalls per run
- **Maintenance**: Single source of truth for version detection
- **Testing**: Easier to mock version detection in tests

## Implementation Complexity

**Low** - Extract existing code into shared function, update two call sites.

## Review Summary

### Backend Architect Review
- **Verdict:** ACCEPT
- **Complexity:** LOW
- **Note:** Session-scoped cache is appropriate; no invalidation needed

### System Architect Review
- **Verdict:** ACCEPT
- **Maintainability Impact:** Positive
- **Note:** Pure DRY refactoring with O(1) improvement per call site

## Implementation Decisions

- **Cache scope:** Session-scoped (analysis runs are short-lived)
- **Invalidation:** Not needed (filesystem won't change during single run)
- **Priority:** Low (quick win)
