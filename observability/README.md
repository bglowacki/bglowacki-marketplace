# Observability Plugin

Claude Code plugin for session analysis and usage insights using built-in JSONL session logs.

## Features

- Generates session summaries saved to `~/.claude/session-summaries/`
- Tracks tool outcomes (success/failure/interrupted)
- Monitors workflow stages and compactions
- Analyzes skill/agent usage patterns
- Sends macOS notifications on session end

## Quick Start

No setup required - the plugin works automatically with Claude Code's built-in session logs.

## Available Skills

| Skill | Description |
|-------|-------------|
| `/observability-usage-collector` | Collect session data for analysis |
| `/observability-workflow-optimizer` | Suggest improvements based on usage analysis |

## How It Works

```
Session JSONL files → collect_usage.py → usage-insights-agent → recommendations
                   ↓
         Stop hook → generate_session_summary.py → session summaries
```

### Data Sources

- **Session JSONL files**: `~/.claude/projects/{project}/*.jsonl`
- **Session summaries**: `~/.claude/session-summaries/{date}_{session_id}.json`

### What Gets Tracked

- Tool invocations and outcomes
- Skill and agent usage
- Workflow stages (brainstorm, plan, implement, test, review, commit)
- Context compactions
- User interruptions

## Usage

### Collect Usage Data

```bash
uv run observability/skills/observability-usage-collector/scripts/collect_usage.py --format json --sessions 20
```

### Quick Stats

```bash
uv run observability/skills/observability-usage-collector/scripts/collect_usage.py --quick-stats --days 14
```

### Analyze with Agent

After collecting data, use the usage-insights-agent:

```
Analyze this usage data: <output from collector>
```

## Architecture

The plugin uses a Stop hook that runs when sessions end:

1. **Stop hook** reads the session JSONL file
2. Parses tool usage, outcomes, compactions, stages
3. Writes summary JSON to `~/.claude/session-summaries/`
4. Shows macOS notification with session stats

The collector script can then aggregate these summaries for analysis.
