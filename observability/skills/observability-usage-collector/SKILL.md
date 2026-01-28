---
name: observability-usage-collector
description: Collects Claude Code session history for analysis. Triggers on "collect usage", "gather usage data", "usage data", or "collect sessions".
allowed-tools: Bash
---

# Usage Collector

## STOP. Read this first.

**DO NOT:**
- Use kubectl or port-forward
- Look for metrics directories
- Run ls commands or exploration

**DO:**
- Run this ONE command immediately:

```bash
uv run ${CLAUDE_PLUGIN_ROOT}/skills/observability-usage-collector/scripts/collect_usage.py --format json --sessions 20 > /tmp/usage-data.json
```

That's it. The script handles everything. Just run it.

---

## Command Options

Add flags to the command above:

| Flag | What it does |
|------|-------------|
| `--format json` | JSON output for agent interpretation (recommended) |
| `--format dashboard` | Compact ASCII dashboard |
| `--quick-stats` | Fast mode from session summaries |
| `--sessions N` | Analyze N sessions (default: 10) |
| `--days N` | Days for quick stats (default: 7) |
| `--verbose` | Show detailed potential matches |

## Pipeline

This collector is step 1 of a 3-step pipeline:

1. **Data Collection** (this skill) -> Structured JSON
2. **Interpretation** (usage-insights-agent) -> Insights
3. **Optimization** (workflow-optimizer skill) -> Fixes

After collecting data, use the usage-insights-agent to interpret the results.

## Output Schema (v3.0)

The JSON output includes:
- `discovery`: All available skills, agents, commands, hooks
- `sessions`: Parsed session data
- `stats`: Usage counts, outcomes, compactions
- `setup_profile`: Complexity, red flags, coverage gaps
- `claude_md`: Configuration file content
