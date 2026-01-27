# bglowacki-marketplace

Personal Claude Code plugins.

## Installation

```bash
# Add marketplace
claude plugins add-marketplace github:bglowacki/bglowacki-marketplace

# Install observability plugin
claude plugins install observability@bglowacki-marketplace
```

## Plugins

### observability

Usage analysis from Claude Code session logs.

**Features:**
- Generates session summaries saved to `~/.claude/session-summaries/`
- Tracks tool outcomes (success/failure/interrupted)
- Monitors workflow stages (brainstorm → plan → implement → test → review → commit)
- Analyzes skill/agent usage patterns
- Context efficiency tracking (compaction metrics)
- macOS notifications on session end

**No external dependencies** - works with Claude Code's built-in JSONL session logs.

#### Usage

The plugin works automatically via a Stop hook. For detailed analysis:

| Skill | Description |
|-------|-------------|
| `/observability-usage-collector` | Collect session data for analysis |
| `/observability-workflow-optimizer` | Suggest improvements based on usage analysis |

#### Quick Stats

```bash
uv run observability/skills/observability-usage-collector/scripts/collect_usage.py --quick-stats --days 14
```

#### Full Analysis Pipeline

1. **Collect data:**
```bash
uv run observability/skills/observability-usage-collector/scripts/collect_usage.py --format json --sessions 20 > /tmp/usage-data.json
```

2. **Analyze with agent:**
```
Analyze this usage data in /tmp/usage-data.json
```

3. **Optimize workflow:**
```
/observability-workflow-optimizer
```

#### Data Locations

- Session JSONL files: `~/.claude/projects/{project}/*.jsonl`
- Session summaries: `~/.claude/session-summaries/{date}_{session_id}.json`

## License

MIT
