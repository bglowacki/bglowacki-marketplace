# Architecture Documentation

## Overview

The bglowacki-marketplace is a Claude Code plugin marketplace containing the **observability** plugin. This document describes the technical architecture of both the marketplace and the plugin.

## System Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                        Claude Code CLI                          │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  ┌─────────────────┐     ┌─────────────────┐                   │
│  │  Plugin System  │────▶│   Marketplace   │                   │
│  └────────┬────────┘     │   (this repo)   │                   │
│           │              └────────┬────────┘                   │
│           ▼                       │                             │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │                   Observability Plugin                   │   │
│  ├─────────────────────────────────────────────────────────┤   │
│  │                                                         │   │
│  │  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌─────────┐ │   │
│  │  │  Hooks   │  │  Skills  │  │  Agents  │  │Commands │ │   │
│  │  └────┬─────┘  └────┬─────┘  └────┬─────┘  └────┬────┘ │   │
│  │       │             │             │             │       │   │
│  └───────┼─────────────┼─────────────┼─────────────┼───────┘   │
│          │             │             │             │           │
└──────────┼─────────────┼─────────────┼─────────────┼───────────┘
           ▼             ▼             ▼             ▼
    ┌──────────┐  ┌───────────┐  ┌──────────┐  ┌──────────┐
    │ Session  │  │  Usage    │  │ Insights │  │ Pipeline │
    │ Summary  │  │ Collector │  │  Agent   │  │Orchestr. │
    └────┬─────┘  └─────┬─────┘  └────┬─────┘  └────┬─────┘
         │              │             │             │
         ▼              ▼             ▼             ▼
    ~/.claude/     JSON Output    Analysis     Workflow
    session-       for Agent      Results      Automation
    summaries/
```

## Component Details

### 1. Marketplace Layer

**File**: `.claude-plugin/marketplace.json`

```json
{
  "name": "bglowacki-marketplace",
  "plugins": [
    {
      "name": "observability",
      "source": "./observability"
    }
  ]
}
```

The marketplace acts as a registry that Claude Code uses to discover and install plugins.

### 2. Plugin Manifest

**File**: `observability/.claude-plugin/plugin.json`

```json
{
  "name": "observability",
  "version": "2.4.6",
  "hooks": {
    "Stop": [{
      "matcher": "*",
      "hooks": [{
        "type": "command",
        "command": "uv run ${CLAUDE_PLUGIN_ROOT}/hooks/generate_session_summary.py",
        "timeout": 10000
      }]
    }]
  }
}
```

### 3. Hook Architecture

**Stop Hook** (`hooks/generate_session_summary.py`)

```
Trigger: Session end (Stop event)
Input: JSON from stdin {session_id, cwd}
Process:
  1. Locate session JSONL file
  2. Parse entries for tool calls, outcomes, compactions
  3. Infer workflow stages
  4. Classify session type (DEV/READ)
  5. Generate summary JSON
  6. Send macOS notification
Output: ~/.claude/session-summaries/{date}_{session_id}.json
```

### 4. Skill Architecture

**Usage Collector** (`skills/observability-usage-collector/`)

```
Trigger: /observability-usage-collector or trigger phrases
Process:
  1. Discover all skills, agents, commands, hooks
  2. Parse session JSONL files
  3. Match prompts against component triggers
  4. Detect missed opportunities
  5. Generate usage statistics
Output: Structured JSON for agent interpretation
```

### 5. Agent Architecture

**Usage Insights Agent** (`agents/usage-insights-agent.md`)

A delegation-capable agent that can spawn focused sub-agents:

| Sub-Agent | Purpose |
|-----------|---------|
| `usage-setup-analyzer` | Quick setup overview |
| `usage-pattern-detector` | Pattern categorization |
| `usage-finding-expander` | Detailed recommendations |

## Data Model

### Session Summary Schema (v3.0)

```json
{
  "session_id": "string",
  "project": "string",
  "session_type": "DEV | READ",
  "timestamp": "ISO8601",
  "total_tools": "number",
  "tool_breakdown": {"tool_name": "count"},
  "skills_used": {"skill_name": "count"},
  "agents_used": {"agent_name": "count"},
  "stages_visited": ["stage_name"],
  "final_stage": "string",
  "outcomes": {
    "success": "number",
    "failure": "number",
    "interrupted": "number"
  },
  "compactions": "number"
}
```

### Collector Output Schema

```json
{
  "_schema": {"version": "3.0"},
  "setup_profile": {
    "complexity": "number",
    "shape": "string",
    "red_flags": ["string"],
    "coverage_gaps": ["string"]
  },
  "discovery": {
    "skills": [SkillOrAgent],
    "agents": [SkillOrAgent],
    "commands": [SkillOrAgent],
    "hooks": [Hook]
  },
  "sessions": [SessionData],
  "stats": {...},
  "potential_matches_detailed": [Match],
  "pre_computed_findings": [Finding]
}
```

## Key Algorithms

### 1. Outcome Detection

```python
def detect_outcome(tool_name: str, result: str) -> str:
    # Tool-specific detection
    if tool_name == "Bash":
        if "exit code: 0" in result: return "success"
        if "exit code:" in result: return "failure"
    # Generic fallback
    if "error" in result.lower(): return "failure"
    return "success"
```

### 2. Workflow Stage Inference

```
unknown → research → brainstorm → plan → implement → test → review → commit → deploy
```

Stage transitions are inferred from:
- Skill invocations (e.g., `brainstorm` skill → brainstorm stage)
- Tool usage (e.g., `Edit`/`Write` → implement stage)
- Bash commands (e.g., `git commit` → commit stage)

### 3. Trigger Matching (ADR-001)

```python
MIN_TRIGGER_LENGTH = 3
COMMON_WORD_BLOCKLIST = {"the", "for", "and", ...}

def find_matches(prompt: str, triggers: list[str]) -> list[Match]:
    # Tokenize and filter
    # Match against component triggers
    # Score by confidence (ADR-046)
```

## Data Paths

| Data Type | Location |
|-----------|----------|
| Session JSONL | `~/.claude/projects/{project}/*.jsonl` |
| Session Summaries | `~/.claude/session-summaries/{date}_{id}.json` |
| Plugin Cache | `~/.claude/plugins/cache/` |
| Collector Output | User-specified (typically `/tmp/usage-data.json`) |

## Design Decisions

Key architecture decisions are documented in 76 ADRs in `docs/adrs/`. Notable decisions:

| ADR | Decision |
|-----|----------|
| ADR-019 | No ML dependencies - rule-based only |
| ADR-020 | Semantic versioning for data schema |
| ADR-026 | Defensive JSONL parsing with fingerprinting |
| ADR-042 | Code duplication over shared modules (for `uv run --script`) |

## Testing Strategy

```
observability/tests/
├── test_session_parsing.py    # JSONL parsing
├── test_outcome_detection.py  # Outcome classification
├── test_workflow_stages.py    # Stage inference
├── test_find_matches.py       # Trigger matching
├── test_yaml_frontmatter.py   # Skill/agent parsing
└── test_code_sync.py          # Duplicated code sync
```

Run tests: `cd observability && uv run pytest tests/`

## Security Considerations

- No external network calls (JSONL-only architecture)
- No credentials stored
- Local file system access only
- Prompt sanitization available (`--no-prompts` flag)

## Performance Characteristics

- Hook timeout: 10 seconds
- Discovery performance: 100-200ms (ADR-022)
- Session parsing: O(n) where n = JSONL lines
- No persistent background processes

---

*Generated by document-project workflow on 2026-01-28*
