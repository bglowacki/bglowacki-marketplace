# ADR-031: Plugin Version Cleanup Policy

**Status:** BLOCKED
**Date:** 2026-01-27
**Category:** Operations
**Source:** Research finding from ADR-022 performance analysis

## Context

During ADR-022 research, discovered the observability plugin has accumulated 24 version directories in the plugin cache. This causes:

1. **Performance overhead**: 24 stat() calls just for version detection
2. **Storage waste**: Multiple outdated versions consuming disk space
3. **Confusion**: Users may wonder why old versions persist

## Problem Statement

No policy exists for cleaning up old plugin versions. They accumulate indefinitely.

## Proposed Options

### Option A: Keep Last N Versions (Recommended)
Retain only the 5 most recent versions per plugin.

- Pro: Simple rule, easy to implement
- Pro: Preserves recent rollback capability
- Con: May lose specific version needed for debugging

### Option B: Time-Based Retention
Delete versions older than 90 days.

### Option C: Manual Cleanup Only
Document cleanup command, leave to user discretion.

## Recommendation

**Option A: Keep Last 5 Versions**

For observability plugin: 24 → 5 versions = ~19 fewer stat() calls per discovery.

## Review Summary

### Backend Architect Review
- **Verdict:** ACCEPT
- **Complexity:** LOW
- **Recommendation:** Implement as manual cleanup command first

### System Architect Review
- **Verdict:** NEEDS_MORE_INFO
- **Missing:** Execution model (CLI command, hook, or background?)
- **Concern:** Failure modes if user actively uses older version
- **Concern:** Rollback scenarios if user wants to pin to older version

## Questions Requiring Answers

1. What is the execution trigger? (manual command / hook / scheduled)
2. How to handle pinned versions if user intentionally uses older version?
3. What if cleanup runs while another session uses an old version?
4. Should cleanup be automatic or require user confirmation?
