---
name: observability-workflow-optimizer
description: Takes insights from usage-insights-agent and generates minimal, actionable fixes. Triggers on "optimize workflow", "fix missed opportunities", or after reviewing usage insights.
---

# Workflow Optimizer

Generate minimal, targeted improvements based on usage insights.

## Prerequisites

Run in this order:
1. `uv run ${CLAUDE_PLUGIN_ROOT}/skills/observability-usage-collector/scripts/collect_usage.py --format json > /tmp/usage-data.json`
2. Use usage-insights-agent to interpret the data
3. Use this skill to generate fixes

## Input

You receive insights from usage-insights-agent identifying:
- Setup profile (complexity, shape, red flags, coverage gaps)
- Missed opportunities (with specific prompts)
- Configuration issues
- Usage patterns
- Hook effectiveness

## Project Context Filter

**CRITICAL:** Only generate fixes relevant to the CURRENT PROJECT being worked on.

When analyzing insights, **EXCLUDE** recommendations about:
- Skills/agents from unrelated plugins (e.g., plugin-dev agents when working on a business app)
- Global configuration issues unrelated to current project
- Duplicate skills in `~/.claude/skills/` unless they affect current project
- Patterns from sessions in other projects

**INCLUDE** only:
- Missed opportunities from sessions in the current project
- Skills/agents that would help with the current project's domain
- Project-level CLAUDE.md improvements
- Hooks that would improve the current project's workflow

Ask yourself: "Would this fix help someone working on THIS project specifically?"

## Fix Strategy

### Order of Preference (minimal first)

1. **Add trigger phrases** - Extend description with specific phrases
2. **Clarify description** - Make it clearer when to use
3. **Update CLAUDE.md** - Add workflow guidance
4. **Add/update hooks** - Automate repetitive patterns
5. **Split item** - Only if clearly doing multiple unrelated things
6. **Create new item** - Last resort

### Coverage-Aware Recommendations

When insights include coverage gaps, check for matching patterns in prompts:

| Coverage Gap | Look For in Prompts | Recommendation |
|--------------|---------------------|----------------|
| testing | "test", "spec", "assert", "TDD" | Add test-driven-development skill |
| debugging | "error", "bug", "fix", "investigate" | Add systematic-debugging skill |
| event_sourcing | "aggregate", "event", "projection", "CQRS" | Add domain-specific skills |
| documentation | "doc", "readme", "guide", "explain" | Add documentation skills |
| security | "vulnerable", "secret", "security", "CVE" | Add security scanning skills |

### Shape-Aware Recommendations

Adjust recommendations based on setup shape:

| Shape | Recommendation Approach |
|-------|------------------------|
| plugin-heavy | Don't suggest more plugins, focus on project customization |
| hook-light | Suggest automation opportunities |
| no-project-customization | Prioritize creating project-level CLAUDE.md |
| global-heavy | Recommend moving relevant items to project level |

### Removal Recommendations

Identify components that add noise without value:

| Scenario | Detection | Action |
|----------|-----------|--------|
| Never-used | 0 uses across 20+ sessions AND triggers don't match any prompts | Consider removing |
| Redundant | 2+ skills cover same area, one never used | Remove unused one |
| Stale global | Global component only matches one project's prompts | Move to project |
| Disabled but present | CLAUDE.md says "don't use X" but X exists | Remove X entirely |

Output removal candidates as:
```
### Removal Candidates
| Component | Type | Reason | Last Used | Action |
|-----------|------|--------|-----------|--------|
| old-debug-skill | skill | Replaced by systematic-debugging | Never | Remove |
| legacy-formatter | hook | Conflicts with prettier hook | 30d ago | Remove |
```

### Hook Placement Rules

**ALWAYS prefer project-level hooks over global hooks:**

| Location | When to Use |
|----------|-------------|
| `.claude/settings.json` | Project-specific hooks (shared with team) |
| `.claude/settings.local.json` | Personal project overrides (not committed) |
| `~/.claude/settings.json` | Only for truly global preferences |

**Rationale:** Project hooks are:
- Scoped to where they're needed
- Shared with team via git
- Don't pollute global config
- Take precedence over global settings

### For Each Fix

1. Identify the root cause
2. Find the minimal change that addresses it
3. Check for conflicts with similar items
4. Propose the specific edit

## Output Format

For each improvement:

```
### [item name]

**Issue:** [from insights]
**Root Cause:** [why it was missed]
**Fix:**
- File: `path/to/file.md`
- Change: Add "debug", "error", "troubleshoot" to trigger phrases
- Before: `description: Use for systematic debugging`
- After: `description: Use for systematic debugging, troubleshooting errors, investigating bugs`

**Impact:** [expected improvement]
```

## Verification

After applying fixes, re-run the pipeline to verify:
```bash
uv run ${CLAUDE_PLUGIN_ROOT}/skills/observability-usage-collector/scripts/collect_usage.py --format json > /tmp/usage-data.json
# Then use usage-insights-agent to verify improvements
```

## Anti-Patterns

**DON'T:**
- Add generic triggers ("help", "fix", "create")
- Duplicate triggers across items
- Create new items when trigger refinement works
- Change one item without checking conflicts
- Create hooks in global `~/.claude/settings.json` for project-specific behavior
- Add hooks that duplicate existing skill/agent functionality
- Recommend fixes for unrelated plugins (e.g., plugin-dev for a business app)
- Suggest global skill/agent changes based on single-project patterns
- Suggest adding more plugins when setup is already plugin-heavy

**DO:**
- Use specific, distinctive triggers
- Check for conflicts with similar items
- Test with usage-collector after changes
- Prefer description changes over structural changes
- Create hooks in project `.claude/settings.json`
- Use hooks for automation (formatting, validation) not for workflow guidance
- Focus fixes on the current project's domain and needs
- Filter out noise from cross-project analysis
- Recommend removals for unused/redundant components
