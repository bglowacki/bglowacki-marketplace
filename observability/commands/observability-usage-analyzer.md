---
name: observability-usage-analyzer
description: Analyze Claude Code session history to identify missed skill/agent opportunities
allowed-tools: Bash
---

# Usage Analyzer

!`uv run ${CLAUDE_PLUGIN_ROOT}/skills/observability-usage-analyzer/scripts/analyze_usage.py`

Present the output to the user. If it shows errors about Prometheus, that's fine - the script falls back to JSONL-only mode.
