# ADR-031: Command and Skill Name Collision Creates Confusion

## Status
PROPOSED

## Context
Commands and skills with identical names exist in parallel, causing invocation ambiguity.

## Finding
**Files**:
- `commands/observability-usage-collector.md` (name: observability-usage-collector)
- `skills/observability-usage-collector/SKILL.md` (name: observability-usage-collector)
- `commands/observability-workflow-optimizer.md` (name: observability-workflow-optimizer)
- `skills/observability-workflow-optimizer/SKILL.md` (name: observability-workflow-optimizer)

Both pairs have:
- Identical names
- ~95% similar content
- One invokes the other (command → skill)

## Impact
- Unclear whether to use `/command` or `Skill()`
- Redundant documentation
- Circular dependency: command wraps skill with same name

## Options

### Option A: Remove Commands
Keep only skills, since they provide more context. Users can invoke skills directly.

### Option B: Rename to Differentiate
- Commands: `run-usage-collector`, `run-workflow-optimizer`
- Skills: `observability-usage-collector`, `observability-workflow-optimizer`

### Option C: Document the Pattern
Add documentation explaining that commands are entry points for skills.

## Recommendation
Option C for now. The pattern works, it just needs documentation. Add a note to the commands explaining they are convenience wrappers for the corresponding skills.

## Related
- ADR-005: Skill/Command Redundancy (broader issue, this is specific collision)

## Review Notes
- Severity: Low (confusion, not broken)
- Effort: Low
- Risk: None
