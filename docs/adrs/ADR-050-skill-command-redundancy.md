# ADR-005: Resolve Skill/Command File Redundancy

## Status
PROPOSED

## Context
Two files serve similar purposes for the usage collector:
1. `skills/observability-usage-collector/SKILL.md` - Loaded by Skill tool
2. `commands/observability-usage-collector.md` - Loaded by /command

Both contain the same core instructions but with slight differences.

## Finding
**SKILL.md focus**: Direct command execution, emphasizes "just run this command"
**Command focus**: Pipeline orchestration with Task and Skill tool usage

This redundancy can cause confusion about which to use.

## Decision
TBD - Needs review

## Options

### Option A: Keep Both, Differentiate Clearly
- Command = Quick invocation via `/observability-usage-collector`
- Skill = Detailed workflow when invoked programmatically

**Pros**: Flexibility for different use cases
**Cons**: Maintenance of two files

### Option B: Consolidate to Command Only
Remove skill, keep command which can be invoked as `/observability-usage-collector`

**Pros**: Single source, commands are user-invokable
**Cons**: Loses skill-based invocation

### Option C: Consolidate to Skill Only
Keep skill, rename/redirect command to skill.

**Pros**: Skills are the preferred Claude Code pattern
**Cons**: Commands provide slash-command UX

## Recommendation
Option A with clearer differentiation. Document when to use each:
- `/observability-usage-collector` for quick data collection
- Skill invocation for integration into larger workflows

## Impact
- Clearer documentation reduces confusion
- May need to update both files when logic changes

## Review Notes
- Severity: Low (usability concern)
- Effort: Low (documentation update)
- Risk: None
