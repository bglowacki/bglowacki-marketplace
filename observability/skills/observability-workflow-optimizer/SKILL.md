---
name: observability-workflow-optimizer
description: Takes insights from usage-insights-agent and generates minimal, actionable fixes. Triggers on "optimize workflow", "fix missed opportunities", or after reviewing usage insights.
---

# Workflow Optimizer

Generate minimal, targeted improvements based on usage insights.

## Prerequisites

Run in this order:
1. `uv run ${CLAUDE_PLUGIN_ROOT}/skills/observability-usage-analyzer/scripts/analyze_usage.py --format json > /tmp/usage-data.json`
2. Use usage-insights-agent to interpret the data
3. Use this skill to generate fixes

## Input

You receive insights from usage-insights-agent identifying:
- Missed opportunities (with specific prompts)
- Configuration issues
- Usage patterns

## Fix Strategy

### Order of Preference (minimal first)

1. **Add trigger phrases** - Extend description with specific phrases
2. **Clarify description** - Make it clearer when to use
3. **Update CLAUDE.md** - Add workflow guidance
4. **Split item** - Only if clearly doing multiple unrelated things
5. **Create new item** - Last resort

### For Each Fix

1. Identify the root cause
2. Find the minimal change that addresses it
3. Check for conflicts with similar items
4. Propose the specific edit

## Output Format

For each improvement:

```markdown
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
uv run ${CLAUDE_PLUGIN_ROOT}/skills/observability-usage-analyzer/scripts/analyze_usage.py --format json > /tmp/usage-data.json
# Then use usage-insights-agent to verify improvements
```

## Anti-Patterns

**DON'T:**
- Add generic triggers ("help", "fix", "create")
- Duplicate triggers across items
- Create new items when trigger refinement works
- Change one item without checking conflicts

**DO:**
- Use specific, distinctive triggers
- Check for conflicts with similar items
- Test with usage-analyzer after changes
- Prefer description changes over structural changes
