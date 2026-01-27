# ADR-004: Split collect_usage.py into Modules

## Status
PROPOSED

## Context
The `collect_usage.py` script is 1508 lines long with multiple responsibilities:
- JSONL parsing
- Discovery (skills, agents, commands, hooks)
- Session analysis
- Output formatting (table, dashboard, JSON)
- Setup profile computation
- Plugin usage tracking

## Finding
**File**: `skills/observability-usage-collector/scripts/collect_usage.py`
**Lines**: 1508
**Functions**: 40+
**Dataclasses**: 8

Single file violates SRP (Single Responsibility Principle). Makes it harder to:
- Test individual components
- Navigate the codebase
- Make isolated changes

## Decision
TBD - Needs review

## Recommendation
Split into modules:
```
scripts/
  collect_usage.py      # Main entry point, CLI
  lib/
    discovery.py        # discover_skills, discover_agents, etc.
    parsing.py          # JSONL parsing, session extraction
    analysis.py         # find_matches, analyze_jsonl
    profile.py          # compute_setup_profile
    output.py           # print_table, print_dashboard, generate_json
    models.py           # Dataclasses
```

## Impact
- Improved maintainability
- Easier testing
- Better code navigation
- Requires careful import management for uv script

## Review Notes
- Severity: Low (code quality, not correctness)
- Effort: High (significant refactor)
- Risk: Medium (refactoring working code)
