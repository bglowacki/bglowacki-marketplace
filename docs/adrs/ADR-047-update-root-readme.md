# ADR-002: Update Root README.md

## Status
IMPLEMENTED (2026-01-27)

## Context
The root README.md extensively documents OTEL, Prometheus, Alertmanager, and Kubernetes features that were removed in the v2.0.0 refactor. The observability/README.md was updated but the root README was not.

## Finding
**File**: `README.md:17-122`
**Issues**:
1. References to OTEL Collector (lines 37-48)
2. References to Prometheus alerts (lines 41, 66-72)
3. References to Alertmanager (lines 47)
4. Prerequisites list Kubernetes, helm, kubectl (lines 30-34)
5. Troubleshooting section references non-existent components
6. Health check script reference may be stale

## Decision
ACCEPTED - Already implemented. README no longer references OTEL/Prometheus. Current content accurately describes JSONL-based architecture.

## Recommendation
Replace the observability section with content from `observability/README.md` which accurately describes the current JSONL-based architecture.

## Impact
- Eliminates user confusion about missing features
- Reduces support burden from users following outdated instructions
- Medium documentation effort

## Review Notes
- Severity: High (major documentation mismatch)
- Effort: Medium (significant rewrite needed)
- Risk: Low (documentation only)
