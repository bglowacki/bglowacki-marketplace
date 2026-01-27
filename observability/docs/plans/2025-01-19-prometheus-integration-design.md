# Usage Analyzer Prometheus Integration Design

> **SUPERSEDED**: This design was implemented but later removed in v2.0.0
> (refactor to JSONL-only architecture). Kept for historical reference.

**Date:** 2025-01-19
**Status:** Superseded

## Overview

Enhance the usage-analyzer skill to combine Prometheus metrics with JSONL session data for richer insights.

## Problem

Current usage-analyzer only reads local JSONL files, missing:
- Time-series trends (usage increasing/decreasing)
- Success rate correlations (do certain skills improve outcomes?)
- Cross-session aggregate patterns

## Solution

Combine two data sources:

| Source | Provides | Limitations |
|--------|----------|-------------|
| Prometheus | Aggregates, trends, success rates | No prompt context |
| JSONL | Full session context, exact prompts | No time aggregation |

## Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                    Usage Analyzer Enhanced                       │
├─────────────────────────────────────────────────────────────────┤
│  ┌──────────────┐          ┌──────────────┐                     │
│  │  Prometheus  │          │    JSONL     │                     │
│  │   Fetcher    │          │    Parser    │                     │
│  └──────┬───────┘          └──────┬───────┘                     │
│         │                         │                              │
│         └────────────┬────────────┘                              │
│                      ▼                                           │
│            ┌─────────────────┐                                   │
│            │   Correlator    │                                   │
│            └────────┬────────┘                                   │
│                     ▼                                            │
│            ┌─────────────────┐                                   │
│            │    Reporter     │                                   │
│            │  table|dash|json│                                   │
│            └─────────────────┘                                   │
└─────────────────────────────────────────────────────────────────┘
```

## Prometheus Queries

| Metric | Query | Purpose |
|--------|-------|---------|
| Skill usage | `sum by (skill_name) (increase(claude_code_skill_invocations[7d]))` | Usage trends |
| Agent usage | `sum by (agent_type) (increase(claude_code_agent_invocations[7d]))` | Usage trends |
| Success rate | `sum(claude_code_outcome_success) / (sum(claude_code_outcome_success) + sum(claude_code_outcome_failure))` | Overall health |
| Skill success | `sum by (skill_name) (claude_code_outcome_success{tool_name="Skill"})` | Per-skill success |
| Workflow stages | `sum by (to_stage) (increase(claude_code_workflow_stage_transition[7d]))` | Stage coverage |
| Week-over-week | Compare `[7d]` vs `[7d] offset 7d` | Trend direction |

## Configuration

Added to `${CLAUDE_PLUGIN_ROOT}/config/endpoint.env`:

```bash
OTEL_ENDPOINT=http://localhost:30418
PROMETHEUS_ENDPOINT=http://localhost:9090
```

## CLI Interface

```bash
# Existing flags
--sessions N          # Sessions to analyze (default: 10)
--format table|json   # Output format
--verbose             # Show examples
--quick-stats         # Fast mode from summaries
--days N              # Days for quick stats

# New flags
--format table|dashboard|json  # Extended formats
--no-prometheus                # Skip Prometheus even if available
--prometheus-endpoint URL      # Override configured endpoint
--range 7d|14d|30d             # Time range for Prometheus queries
```

## Output Formats

### Table (default)

```
================================================================================
USAGE ANALYSIS REPORT (with Prometheus data)
================================================================================

📊 TRENDS (Last 7 days vs previous 7 days)
  brainstorming:  5 uses  ↓40%   (was 8)
  tdd:            2 uses  ↑100%  (was 1)
  commit-handler: 12 uses ↔0%    (was 12)

📈 SUCCESS CORRELATION
  With brainstorming:    85% success
  Without brainstorming: 62% success  → +23% improvement

📋 WORKFLOW COVERAGE
  Stages hit: brainstorm → plan → implement → test → commit
  Missing:    review (skipped in 4/10 sessions)

--- Missed Opportunities (from JSONL) ---
  [SKILL] systematic-debugging (missed 3 times)
    Session abc123: "fix this bug..."

--- Recommendations ---
  • brainstorming usage down 40% but matched 3 prompts - consider using more
  • review stage skipped frequently - run domain-code-review before commits
================================================================================
```

### Dashboard

```
┌─ Skills ──────────────────┐  ┌─ Success Rate ─────────────┐
│ brainstorming  ████░ 5 ↓  │  │ Overall:  ████████░░ 82%  │
│ tdd            ██░░░ 2 ↑  │  │ w/skills: █████████░ 91%  │
│ commit-handler ████████ 12│  │ w/o:      ██████░░░░ 64%  │
└───────────────────────────┘  └────────────────────────────┘
```

### JSON

Full structured output for programmatic use.

## Correlation Rules

1. **Declining + Missed** → "Usage down but opportunities exist"
2. **Low success rate** → Compare sessions with/without skill
3. **Stage gaps** → Missing workflow stages vs expected flow

## Fallback Behavior

1. Check `${CLAUDE_PLUGIN_ROOT}/config/endpoint.env` for `PROMETHEUS_ENDPOINT`
2. If not set or connection fails → warn once, continue JSONL-only
3. Report clearly shows which data source contributed each insight

## Files to Modify

| File | Changes |
|------|---------|
| `skills/observability-setup/SKILL.md` | Add Step 6b: Configure Prometheus endpoint |
| `skills/observability-usage-analyzer/SKILL.md` | Update docs with new flags and outputs |
| `skills/observability-usage-analyzer/scripts/analyze_usage.py` | Main implementation |

## Dependencies

```python
# /// script
# dependencies = ["pyyaml", "requests"]
# ///
```
