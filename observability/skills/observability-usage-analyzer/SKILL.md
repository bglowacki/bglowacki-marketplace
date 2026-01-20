---
name: observability-usage-analyzer
description: Analyzes Claude Code session history and Prometheus metrics to identify missed skill/agent opportunities. Triggers on "analyze usage", "missed skills", "usage patterns", or "review my sessions".
allowed-tools: Bash
---

# Usage Analyzer

**IMPORTANT: Just run the script. Do NOT manually query Prometheus or use kubectl.**

```bash
uv run ${CLAUDE_PLUGIN_ROOT}/skills/observability-usage-analyzer/scripts/analyze_usage.py
```

The script handles Prometheus connectivity automatically (falls back to JSONL-only if unavailable).

---

## Examples

**Default analysis:**
```bash
uv run ${CLAUDE_PLUGIN_ROOT}/skills/observability-usage-analyzer/scripts/analyze_usage.py
```

**Dashboard view:**
```bash
uv run ${CLAUDE_PLUGIN_ROOT}/skills/observability-usage-analyzer/scripts/analyze_usage.py --format dashboard
```

**Quick stats:**
```bash
uv run ${CLAUDE_PLUGIN_ROOT}/skills/observability-usage-analyzer/scripts/analyze_usage.py --quick-stats
```

## Options

| Flag | Description | Default |
|------|-------------|---------|
| `--sessions N` | Number of sessions to analyze | 10 |
| `--format table\|dashboard\|json` | Output format | table |
| `--verbose` | Show detailed examples | false |
| `--quick-stats` | Fast mode from session summaries | false |
| `--days N` | Days to include in quick stats | 14 |
| `--no-prometheus` | Skip Prometheus even if available | false |
| `--prometheus-endpoint URL` | Override Prometheus endpoint | from config |
| `--range 7d\|14d\|30d` | Time range for Prometheus queries | 7d |

## Output Formats

### Table (default)

Shows detailed analysis with:
- Prometheus trends (skills/agents usage with ↑↓↔ indicators)
- Workflow stages coverage
- JSONL usage stats
- Correlated insights (combining both data sources)
- Missed opportunities with examples
- Recommendations

### Dashboard

Compact ASCII dashboard with:
- Progress bars for skill usage
- Success rate visualization
- Workflow stage flow diagram
- Top insights summary

### JSON

Machine-readable output for programmatic use.

## How It Works

1. **Fetch Prometheus Data** - Queries metrics for trends, success rates, workflow stages
2. **Discover Skills/Agents** - Scans `~/.claude/skills/`, `~/.claude/agents/`, and project directories
3. **Parse JSONL Sessions** - Reads session files for detailed context
4. **Correlate Data** - Combines both sources for richer insights:
   - Declining usage + missed opportunities → high priority recommendation
   - Workflow stage gaps → process improvement suggestions
   - Success rate correlation → skill effectiveness analysis
5. **Generate Report** - Produces actionable insights with specific examples

## Insights Generated

| Insight Type | Severity | Example |
|--------------|----------|---------|
| `declining_with_missed` | 🔴 High | "brainstorming usage down 40% but 3 prompts matched triggers" |
| `workflow_gap` | 🟡 Medium | "Workflow stages rarely used: review, test" |
| `missed_opportunity` | 🟢 Low | "systematic-debugging could have been used 2 times" |

## Configuration

Prometheus endpoint is configured during `/observability:setup`:

```bash
# In ${CLAUDE_PLUGIN_ROOT}/config/endpoint.env
OTEL_ENDPOINT=http://localhost:30418
PROMETHEUS_ENDPOINT=http://localhost:30090
```

If Prometheus is unavailable, the analyzer gracefully falls back to JSONL-only mode.

## Troubleshooting

### No Prometheus data

1. Check endpoint is configured: `cat ${CLAUDE_PLUGIN_ROOT}/config/endpoint.env`
2. Verify Prometheus is accessible via NodePort:
   ```bash
   curl "http://localhost:30090/api/v1/query?query=up"
   ```
3. If NodePort isn't working, check the service:
   ```bash
   kubectl get svc prometheus-external -n observability
   ```

### No JSONL sessions found

Sessions are stored in `~/.claude/projects/<project-path>/`. Ensure you're running from the correct project directory or use `--project /path/to/project`.
