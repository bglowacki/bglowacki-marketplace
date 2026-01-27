---
name: observability-usage-collector
description: Collect Claude Code usage data for analysis
allowed-tools:
  - Bash
  - Read
  - Task
---

# Usage Collector

Collect your Claude Code usage data for analysis by the usage-insights-agent.

## Quick Start

Run the full pipeline:

```bash
# 1. Collect data
uv run ${CLAUDE_PLUGIN_ROOT}/skills/observability-usage-collector/scripts/collect_usage.py --format json --sessions 20 > /tmp/usage-data.json

# 2. Interpret with agent
```

Then use the usage-insights-agent to interpret `/tmp/usage-data.json`.

## Options

- `--sessions N` - Number of sessions to analyze (default: 10)
- `--project PATH` - Analyze specific project
- `--format json` - Output JSON for agent interpretation (required for pipeline)

## Pipeline

1. **Data Collection** (this command) → Structured JSON
2. **Interpretation** (usage-insights-agent) → Insights
3. **Optimization** (workflow-optimizer skill) → Fixes

## Example Usage

```bash
# Collect usage data
uv run ${CLAUDE_PLUGIN_ROOT}/skills/observability-usage-collector/scripts/collect_usage.py --format json --sessions 20 > /tmp/usage-data.json

# Then ask: "Analyze the usage data in /tmp/usage-data.json and give me insights"
# After insights: "Now help me optimize my workflow based on these insights"
```
