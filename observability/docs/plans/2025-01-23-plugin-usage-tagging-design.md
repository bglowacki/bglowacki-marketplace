# Plugin Usage Tagging Design

## Problem

The insights agent shows findings for ALL plugins regardless of project relevance. For widget-service, it reported plugin-dev issues even though plugin-dev is never used there.

Additionally, unused plugins consume context window resources with no benefit.

## Solution

Tag each plugin with usage status during data collection. The insights agent then:
1. Shows a Plugin Efficiency summary
2. Filters findings to only relevant plugins

## Plugin Usage Categories

| Status | Definition | Action |
|--------|------------|--------|
| **active** | Triggered in sessions (tool calls, skill invocations) | Keep, improve config |
| **potential** | Matched prompts but not triggered | Keep, consider using |
| **unused** | No triggers, no matches | Consider disabling |

## Collector Changes

### New field in setup_profile

```python
"plugin_usage": {
    "active": ["superpowers", "handbook"],
    "potential": ["kubernetes-deployment-creator"],
    "unused": ["plugin-dev", "sql-query-optimizer", ...]
}
```

### Implementation

```python
def compute_plugin_usage(sessions: list, discovery: dict, stats: dict) -> dict:
    # 1. Get all plugins from discovery
    all_plugins = {
        s['source'] for s in discovery.get('skills', [])
        if s.get('source', '').startswith('plugin:')
    }
    all_plugins.update({
        a['source'] for a in discovery.get('agents', [])
        if a.get('source', '').startswith('plugin:')
    })

    # 2. Check which were triggered (from session tool calls)
    active = set()
    for session in sessions:
        for tool_call in session.get('tool_calls', []):
            # Extract plugin from tool/skill/agent name
            source = get_source_from_tool_call(tool_call)
            if source:
                active.add(source)

    # 3. Check which matched prompts (from stats.potential_matches)
    potential = set()
    for match in stats.get('potential_matches', []):
        source = match.get('source', '')
        if source.startswith('plugin:'):
            potential.add(source)
    potential = potential - active

    # 4. Rest are unused
    unused = all_plugins - active - potential

    return {
        "active": sorted(active),
        "potential": sorted(potential),
        "unused": sorted(unused)
    }
```

## Insights Agent Changes

### New Phase 0: Plugin Efficiency

Before category analysis, output:

```markdown
## Plugin Efficiency

**Active plugins (2):** superpowers, handbook
Used in your sessions - keep these.

**Potential plugins (1):** kubernetes-deployment-creator
Matched your prompts but never triggered. Consider using or improving triggers.

**Unused plugins (8):** plugin-dev, mutation-test-runner, sql-query-optimizer...
Taking up context with no benefit for this project.

**Recommendation:** Disable unused plugins to reduce context by ~15%

How to disable for this project only:
Add to .claude/settings.json:
{ "disabled_plugins": ["plugin-dev", ...] }
```

### Filtering Rule

Only show findings for:
- Global components (always relevant)
- Project components (always relevant)
- Active plugins (used)
- Potential plugins (could be used)

Skip findings for unused plugins entirely.

## Files to Modify

| File | Change |
|------|--------|
| `skills/observability-usage-collector/scripts/collect_usage.py` | Add `compute_plugin_usage()`, include in setup_profile |
| `agents/usage-insights-agent.md` | Add Phase 0, add filtering rule |

## Expected Outcomes

1. Plugin-dev findings won't appear for widget-service
2. Users see actionable plugin efficiency recommendations
3. ~15-20% context reduction by disabling unused plugins
