---
name: observability-usage-analyzer
description: Analyzes Claude Code session history to identify missed skill/agent opportunities. Triggers on "analyze usage", "missed skills", "usage patterns", or "review my sessions".
---

# Usage Analyzer

Analyze Claude Code session history to identify missed skill/agent opportunities.

## When to Use

- After work sessions to review efficiency
- To audit skill/agent adoption patterns
- To identify workflow automation gaps

## Quick Start

Run the analysis:

```bash
uv run ${CLAUDE_PLUGIN_ROOT}/skills/usage-analyzer/scripts/analyze_usage.py
```

**Quick stats from session summaries:**
```bash
uv run ${CLAUDE_PLUGIN_ROOT}/skills/usage-analyzer/scripts/analyze_usage.py --quick-stats
```

Options:
- `--sessions N` - Analyze last N sessions (default: 10)
- `--format json|table` - Output format (default: table)
- `--verbose` - Show detailed match reasoning
- `--quick-stats` - Show aggregate stats from session summaries (fast)
- `--days N` - Days to include in quick stats (default: 14)

## How It Works

1. **Discover Available Skills/Agents** - Dynamically scans `~/.claude/skills/`, `~/.claude/agents/`, `.claude/skills/`, and `.claude/agents/`
2. **Extract Trigger Patterns** - Parses skill descriptions and agent definitions for trigger keywords
3. **Parse Session History** - Reads `~/.claude/history.jsonl` for user prompts
4. **Pattern Match** - Compares prompts against discovered triggers
5. **Identify Misses** - Finds prompts matching patterns where skill/agent wasn't invoked
6. **Generate Report** - Produces actionable recommendations

## Output

- **Missed Opportunities** - Prompts where a skill/agent should have been used
- **Usage Statistics** - Which skills/agents are used most/least
- **Recommendations** - Suggestions for workflow improvement

## Resources

### scripts/
- `analyze_usage.py` - Main analysis script with dynamic discovery
