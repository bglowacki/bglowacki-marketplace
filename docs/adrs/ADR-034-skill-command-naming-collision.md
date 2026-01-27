# ADR-034: Skill/Command Naming Collision Prevention

**Status:** ACCEPTED
**Date:** 2026-01-27
**Category:** Methodology
**Source:** Research finding from ADR-008 overlapping triggers analysis

## Context

During ADR-008 research, identified structural issue:

Both skills and commands exist with identical names:
- `observability-usage-collector` (skill)
- `observability-usage-collector` (command)

This creates HIGH severity trigger overlap - user intent becomes ambiguous.

## Problem Statement

When user says "collect usage data", Claude must choose:
1. Load the skill (provides guidance + runs script)
2. Run the command (orchestrates full pipeline)

No mechanism prevents this collision or guides resolution.

## Proposed Options

### Option A: Warn on Name Collision (Recommended)
Add red flag when skill and command share the same name.

```python
# In compute_setup_profile()
skill_names = {s.name.lower() for s in skills}
command_names = {c.name.lower() for c in commands}
collisions = skill_names & command_names
if collisions:
    red_flags.append(f"Skill/command name collision: {', '.join(collisions)}")
```

### Option B: Require Unique Names
Enforce uniqueness across all component types.

### Option C: Namespace Components
Prefix with type: `skill:collector`, `command:collector`

## Recommendation

**Option A: Warn on Collision**

Low-cost detection that surfaces the issue without breaking existing setups.

## Review Summary

### Backend Architect Review
- **Verdict:** ACCEPT
- **Complexity:** LOW (5-10 lines)
- **Note:** Also check agent/command and agent/skill collisions

### System Architect Review
- **Verdict:** ACCEPT (Option A)
- **Maintainability Impact:** Positive
- **Note:** Collision may be intentional (skill wraps command pattern)

## Implementation Notes

- Use existing `red_flags` list infrastructure
- Check all component type pairs (skill/command, agent/command, agent/skill)
- Distinguish intentional "wrapper pattern" from accidental collision
