# ADR-018: Configuration Externalization Strategy

**Status:** ACCEPTED
**Date:** 2026-01-27
**Category:** Architecture
**Decision:** Option A + D (YAML + env var overrides)

## Context

Multiple ADRs identified hardcoded values that should be configurable:
- ADR-004: 8 hardcoded coverage domains
- ADR-012: 5 hardcoded red flag types
- ADR-014: Arbitrary priority thresholds (5 for high, 2-4 for medium)
- ADR-001: Trigger length threshold (>3 chars)
- ADR-015: Truncation limits (500, 100, 200)

Current state: Magic numbers scattered across code with no central configuration.

## Decision

**ACCEPTED: Option A + D hybrid**

YAML configuration file with JSON Schema validation, plus environment variable overrides for deployment flexibility.

## Configuration Schema

Location: `.claude/observability-config.yaml`

```yaml
# observability-config.yaml
config_version: "1.0"  # For config migration

analysis:
  trigger_matching:
    min_length: 3
    min_match_count: 2
    negation_detection: true

  truncation:  # Display-only, analysis uses full text
    prompt: 500
    tool_input: 100
    description: 200

  priority:
    high_threshold: 10
    medium_threshold: 5
    severity_weights:
      critical: 5
      major: 3
      minor: 1

coverage_domains:  # User-extensible
  - name: git_commit
    keywords: ["commit", "pre-commit"]
  - name: testing
    keywords: ["test", "tdd", "spec"]
  # Add custom domains here

red_flags:  # User-extensible
  - id: no_project_claude_md
    severity: warning
  # Add custom red flags here
```

## Implementation Plan

1. Create JSON Schema for validation: `observability/schemas/config-v1.schema.json`
2. Layered configuration precedence:
   - Code defaults (lowest)
   - Project config file
   - Environment variables (highest)
3. Validate at startup with clear error messages
4. Plugin extensions use merge semantics, not replacement
5. Include `config_version` for future migrations

## Environment Variable Pattern

```bash
# Override specific values
OBSERVABILITY_TRIGGER_MIN_LENGTH=4
OBSERVABILITY_PRIORITY_HIGH_THRESHOLD=15
```

## Review Summary

### Backend Architect Review
- **Verdict:** ACCEPT
- **Recommendation:** Combine YAML (human-readable) with JSON Schema (validation + IDE support)
- **Note:** Env vars supplement YAML for deployment flexibility, not replace it

## Consequences

- Users can customize thresholds without code changes
- IDE autocomplete with JSON Schema
- Clear layered configuration precedence
- Requires schema versioning separate from data schema
