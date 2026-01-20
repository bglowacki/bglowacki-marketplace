---
name: observability-usage-analyzer
description: Analyzes Claude Code session history and Prometheus metrics to identify missed skill/agent opportunities. Triggers on "analyze usage", "missed skills", "usage patterns", or "review my sessions".
allowed-tools: Bash
---

# Usage Analyzer

## STOP. Read this first.

**DO NOT:**
- ❌ Use kubectl
- ❌ Use port-forward
- ❌ Query Prometheus manually
- ❌ Look for metrics directories
- ❌ Run ls commands
- ❌ Do ANY exploration

**DO:**
- ✅ Run this ONE command immediately:

```bash
uv run ${CLAUDE_PLUGIN_ROOT}/skills/observability-usage-analyzer/scripts/analyze_usage.py
```

That's it. The script handles everything - Prometheus, JSONL, fallbacks. Just run it.

---

## Command Options

Add flags to the command above:

| Flag | What it does |
|------|-------------|
| `--format dashboard` | Compact ASCII dashboard |
| `--quick-stats` | Fast mode from session summaries |
| `--sessions N` | Analyze N sessions (default: 10) |
| `--days N` | Days for quick stats (default: 14) |
| `--verbose` | Show detailed examples |

