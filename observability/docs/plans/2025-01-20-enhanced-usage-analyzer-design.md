# Enhanced Usage Analyzer Design (Revised)

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Redesign usage-analyzer with agent-driven interpretation instead of hardcoded rules.

**Architecture:** Two-stage pipeline: Python collects data → Agent interprets and generates insights.

**Tech Stack:** Python 3.10+, PyYAML, Claude Code subagents

---

## Architecture Overview

```
┌─────────────────────────────────────────────────────────────────┐
│  analyze_usage.py (DATA COLLECTION)                             │
│  • Discover skills/agents/commands from all sources             │
│  • Parse JSONL sessions                                         │
│  • Parse CLAUDE.md files                                        │
│  • Output: structured JSON with schema descriptions             │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼ JSON
┌─────────────────────────────────────────────────────────────────┐
│  usage-insights-agent (INTERPRETATION)                          │
│  • Read JSON data                                               │
│  • Pattern detection & anomaly identification                   │
│  • Correlate usage with CLAUDE.md instructions                  │
│  • Generate categorized insights                                │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼ Insights
┌─────────────────────────────────────────────────────────────────┐
│  workflow-optimizer skill (RECOMMENDATIONS)                     │
│  • Take insights as input                                       │
│  • Generate minimal, actionable fixes                           │
│  • Prioritize by impact                                         │
└─────────────────────────────────────────────────────────────────┘
```

---

## Task 1: Simplify analyze_usage.py to Data Collection

**Goal:** Remove hardcoded analysis rules, focus on collecting and structuring data.

**Files:**
- Modify: `skills/observability-usage-analyzer/scripts/analyze_usage.py`

**Changes:**

### 1.1 Update SkillOrAgent dataclass

```python
@dataclass
class SkillOrAgent:
    name: str
    type: str  # "skill", "agent", or "command"
    description: str
    triggers: list[str]
    source_path: str
    source_type: str = "unknown"  # "global", "project", or "plugin:<name>"
```

### 1.2 Add discover_commands function

```python
def discover_commands(paths: list[Path]) -> list[SkillOrAgent]:
    """Discover commands from given paths."""
    commands = []
    for base_path in paths:
        if not base_path.exists():
            continue
        for cmd_file in base_path.glob("*.md"):
            try:
                content = cmd_file.read_text()
                frontmatter = extract_yaml_frontmatter(content)
                name = frontmatter.get("name", cmd_file.stem)
                description = frontmatter.get("description", "")
                triggers = extract_triggers_from_description(description)
                triggers.append(name)
                triggers.append(f"/{name}")

                commands.append(SkillOrAgent(
                    name=name,
                    type="command",
                    description=description[:200],
                    triggers=triggers,
                    source_path=str(cmd_file),
                    source_type="global" if str(Path.home()) in str(base_path) else "project",
                ))
            except Exception as e:
                print(f"Warning: Could not parse {cmd_file}: {e}", file=sys.stderr)
    return commands
```

### 1.3 Add discover_from_plugins function

```python
def discover_from_plugins(plugins_cache: Path) -> tuple[list[SkillOrAgent], list[SkillOrAgent], list[SkillOrAgent]]:
    """Discover skills, agents, and commands from installed plugins."""
    skills, agents, commands = [], [], []

    if not plugins_cache.exists():
        return skills, agents, commands

    for marketplace_dir in plugins_cache.iterdir():
        if not marketplace_dir.is_dir() or marketplace_dir.name.startswith("temp_"):
            continue

        for plugin_dir in marketplace_dir.iterdir():
            if not plugin_dir.is_dir():
                continue

            version_dirs = [d for d in plugin_dir.iterdir() if d.is_dir() and not d.name.startswith(".")]
            if not version_dirs:
                continue

            latest_version = max(version_dirs, key=lambda d: d.stat().st_mtime)
            plugin_name = plugin_dir.name
            source_type = f"plugin:{plugin_name}"

            # Skills
            skills_path = latest_version / "skills"
            if skills_path.exists():
                for skill_dir in skills_path.iterdir():
                    if skill_dir.is_dir() and (skill_dir / "SKILL.md").exists():
                        skill_md = skill_dir / "SKILL.md"
                        content = skill_md.read_text()
                        frontmatter = extract_yaml_frontmatter(content)
                        skills.append(SkillOrAgent(
                            name=frontmatter.get("name", skill_dir.name),
                            type="skill",
                            description=frontmatter.get("description", ""),
                            triggers=extract_triggers_from_description(frontmatter.get("description", "")),
                            source_path=str(skill_md),
                            source_type=source_type,
                        ))

            # Agents
            agents_path = latest_version / "agents"
            if agents_path.exists():
                for agent_file in agents_path.glob("*.md"):
                    content = agent_file.read_text()
                    frontmatter = extract_yaml_frontmatter(content)
                    agents.append(SkillOrAgent(
                        name=frontmatter.get("name", agent_file.stem),
                        type="agent",
                        description=frontmatter.get("description", "")[:200],
                        triggers=extract_triggers_from_description(frontmatter.get("description", "")),
                        source_path=str(agent_file),
                        source_type=source_type,
                    ))

            # Commands
            commands_path = latest_version / "commands"
            if commands_path.exists():
                for cmd_file in commands_path.glob("*.md"):
                    content = cmd_file.read_text()
                    frontmatter = extract_yaml_frontmatter(content)
                    commands.append(SkillOrAgent(
                        name=frontmatter.get("name", cmd_file.stem),
                        type="command",
                        description=frontmatter.get("description", "")[:200],
                        triggers=extract_triggers_from_description(frontmatter.get("description", "")),
                        source_path=str(cmd_file),
                        source_type=source_type,
                    ))

    return skills, agents, commands
```

### 1.4 Add CLAUDE.md parsing

```python
def parse_claude_md_files(paths: list[Path]) -> dict:
    """Parse CLAUDE.md files and return structured data."""
    result = {
        "files_found": [],
        "files_missing": [],
        "content": {},
        "sections": [],
    }

    for path in paths:
        if path.exists():
            result["files_found"].append(str(path))
            content = path.read_text()
            result["content"][str(path)] = content

            # Extract section headers
            for line in content.split("\n"):
                if line.startswith("## "):
                    section = line[3:].strip()
                    if section not in result["sections"]:
                        result["sections"].append(section)
        else:
            result["files_missing"].append(str(path))

    return result
```

### 1.5 Remove hardcoded analysis functions

**DELETE these functions:**
- `correlate_data()` - hardcoded insight rules
- `Insight` dataclass - will be generated by agent
- `print_table()`, `print_dashboard()` - replace with JSON output

**KEEP these functions:**
- `discover_skills()`, `discover_agents()` - add source_type
- `parse_session_file()`, `find_project_sessions()`
- `analyze_jsonl()` - but simplify to just stats collection

---

## Task 2: Add Rich JSON Output with Schema Descriptions

**Goal:** Output JSON that includes descriptions to help the agent understand the data.

**Files:**
- Modify: `skills/observability-usage-analyzer/scripts/analyze_usage.py`

**Add output function:**

```python
def generate_analysis_json(
    skills: list[SkillOrAgent],
    agents: list[SkillOrAgent],
    commands: list[SkillOrAgent],
    sessions: list[SessionData],
    jsonl_stats: dict,
    claude_md: dict,
    prom_data: PrometheusData,
) -> dict:
    """Generate rich JSON output for agent interpretation."""

    return {
        "_schema": {
            "description": "Claude Code usage analysis data for agent interpretation",
            "version": "2.0",
            "sections": {
                "discovery": "All available skills, agents, and commands discovered from global, project, and plugin sources",
                "sessions": "Parsed session data showing what was actually used",
                "stats": "Aggregated statistics on usage and missed opportunities",
                "claude_md": "Content and structure of CLAUDE.md configuration files",
                "prometheus": "Metrics from Prometheus if available (trends, success rates)",
            },
        },

        "discovery": {
            "skills": [
                {
                    "name": s.name,
                    "description": s.description,
                    "triggers": s.triggers,
                    "source": s.source_type,
                }
                for s in skills
            ],
            "agents": [
                {
                    "name": a.name,
                    "description": a.description,
                    "triggers": a.triggers,
                    "source": a.source_type,
                }
                for a in agents
            ],
            "commands": [
                {
                    "name": c.name,
                    "description": c.description,
                    "triggers": c.triggers,
                    "source": c.source_type,
                }
                for c in commands
            ],
            "totals": {
                "skills": len(skills),
                "agents": len(agents),
                "commands": len(commands),
            },
        },

        "sessions": {
            "count": len(sessions),
            "prompts": [
                {
                    "session_id": s.session_id,
                    "text": p[:500],  # Truncate long prompts
                }
                for s in sessions
                for p in s.prompts[:5]  # Limit prompts per session
            ][:50],  # Limit total prompts
        },

        "stats": {
            "total_sessions": jsonl_stats["total_sessions"],
            "total_prompts": jsonl_stats["total_prompts"],
            "skills_used": dict(jsonl_stats["skills_used"]),
            "agents_used": dict(jsonl_stats["agents_used"]),
            "commands_used": dict(jsonl_stats.get("commands_used", {})),
            "potential_matches": {
                "skills": dict(jsonl_stats["missed_skills"]),
                "agents": dict(jsonl_stats["missed_agents"]),
                "commands": dict(jsonl_stats.get("missed_commands", {})),
            },
        },

        "claude_md": claude_md,

        "prometheus": {
            "available": prom_data.available,
            "skill_usage": prom_data.skill_usage,
            "agent_usage": prom_data.agent_usage,
            "skill_trends": prom_data.skill_trends,
            "agent_trends": prom_data.agent_trends,
            "workflow_stages": prom_data.workflow_stages,
            "success_rate": prom_data.overall_success_rate,
        } if prom_data.available else {"available": False},
    }
```

**Update main() to use JSON output:**

```python
def main():
    # ... argument parsing ...

    # Discovery
    skills = discover_skills(skill_paths)
    agents = discover_agents(agent_paths)
    commands = discover_commands(command_paths)

    plugin_skills, plugin_agents, plugin_commands = discover_from_plugins(plugins_cache)
    skills.extend(plugin_skills)
    agents.extend(plugin_agents)
    commands.extend(plugin_commands)

    # Session parsing
    sessions = [parse_session_file(f) for f in session_files]
    missed, jsonl_stats = analyze_jsonl(skills, agents + commands, sessions)

    # CLAUDE.md parsing
    claude_md = parse_claude_md_files(claude_md_paths)

    # Prometheus (optional)
    prom_data = fetch_prometheus_data(endpoint) if endpoint else PrometheusData()

    # Output JSON
    output = generate_analysis_json(
        skills, agents, commands, sessions, jsonl_stats, claude_md, prom_data
    )
    print(json.dumps(output, indent=2))
```

---

## Task 3: Create usage-insights-agent

**Goal:** Agent that interprets the JSON data and generates insights.

**Files:**
- Create: `agents/usage-insights-agent.md`

```markdown
---
name: usage-insights-agent
description: Analyzes Claude Code usage data to identify patterns, missed opportunities, and configuration issues. Use after running usage-analyzer with JSON output. Triggers on "analyze usage data", "interpret usage", "what am I missing", or when usage JSON is provided.
model: sonnet
tools:
  - Read
  - Bash
---

# Usage Insights Agent

You analyze Claude Code usage data to provide intelligent insights about skill/agent/command usage patterns.

## Input

You receive JSON data from `analyze_usage.py --format json` containing:
- **discovery**: All available skills, agents, commands with descriptions
- **sessions**: Recent user prompts
- **stats**: Usage counts and potential matches
- **claude_md**: Configuration file content
- **prometheus**: Metrics and trends (if available)

## Analysis Framework

### 1. Opportunity Detection

For each item in `stats.potential_matches`:
- Read the user prompts that triggered the match
- Understand what the user was trying to accomplish
- Determine if the suggested item would have actually helped
- Filter out false positives (e.g., generic word matches)

### 2. Configuration Analysis

Review `claude_md.content` for:
- Workflow instructions that aren't supported by available tools
- Referenced skills/agents that don't exist
- Contradictions between instructions and actual usage patterns

### 3. Usage Pattern Analysis

If prometheus data available:
- Identify declining usage (might indicate discovery issues)
- Find underutilized workflow stages
- Spot success rate anomalies

### 4. Correlation

Connect the dots:
- "CLAUDE.md says 'always use TDD' but test-driven-development skill used 0 times"
- "User asked about debugging 5 times but never used systematic-debugging skill"
- "brainstorming skill triggered but user was actually asking a simple question"

## Output Format

Provide insights in these categories:

### High-Priority Findings
Issues that significantly impact workflow effectiveness.

### Missed Opportunities
Genuine cases where a skill/agent would have helped.

### Configuration Issues
Problems with CLAUDE.md or missing tools.

### Positive Patterns
What's working well - reinforce good habits.

### Recommendations
Specific, actionable improvements ordered by impact.

## Guidelines

- Be specific: "The prompt 'help me debug this error' on Jan 15 could have used systematic-debugging"
- Avoid false positives: Generic words like "help" or "create" shouldn't trigger matches
- Consider context: Sometimes not using a skill is the right choice
- Prioritize: Focus on patterns, not one-off misses
```

---

## Task 4: Update workflow-optimizer Skill

**Goal:** Update to work with the new agent-driven architecture.

**Files:**
- Modify: `skills/observability-workflow-optimizer/SKILL.md`

**Changes:**

```markdown
---
name: observability-workflow-optimizer
description: Takes insights from usage-insights-agent and generates minimal, actionable fixes. Triggers on "optimize workflow", "fix missed opportunities", or after reviewing usage insights.
---

# Workflow Optimizer

Generate minimal, targeted improvements based on usage insights.

## Prerequisites

Run in this order:
1. `analyze_usage.py --format json > /tmp/usage-data.json`
2. Use usage-insights-agent to interpret the data
3. Use this skill to generate fixes

## Input

You receive insights from usage-insights-agent identifying:
- Missed opportunities (with specific prompts)
- Configuration issues
- Usage patterns

## Fix Strategy

### Order of Preference (minimal first)

1. **Add trigger phrases** - Extend description with specific phrases
2. **Clarify description** - Make it clearer when to use
3. **Update CLAUDE.md** - Add workflow guidance
4. **Split item** - Only if clearly doing multiple unrelated things
5. **Create new item** - Last resort

### For Each Fix

1. Identify the root cause
2. Find the minimal change that addresses it
3. Check for conflicts with similar items
4. Propose the specific edit

## Output Format

For each improvement:

```markdown
### [item name]

**Issue:** [from insights]
**Root Cause:** [why it was missed]
**Fix:**
- File: `path/to/file.md`
- Change: Add "debug", "error", "troubleshoot" to trigger phrases
- Before: `description: Use for systematic debugging`
- After: `description: Use for systematic debugging, troubleshooting errors, investigating bugs`

**Impact:** [expected improvement]
```

## Verification

After applying fixes, re-run the pipeline to verify:
```bash
python analyze_usage.py --format json | usage-insights-agent
```
```

---

## Task 5: Update Command to Orchestrate Pipeline

**Files:**
- Modify: `commands/observability-usage-analyzer.md`

```markdown
---
name: observability-usage-analyzer
description: Analyze Claude Code usage patterns and get AI-powered insights
allowed-tools:
  - Bash
  - Read
  - Task
---

# Usage Analyzer

Analyze your Claude Code usage to find missed opportunities and optimization suggestions.

## Quick Start

Run the full pipeline:

```bash
# 1. Collect data
uv run ${CLAUDE_PLUGIN_ROOT}/skills/observability-usage-analyzer/scripts/analyze_usage.py --format json --sessions 20 > /tmp/usage-data.json

# 2. Interpret with agent
```

Then use the usage-insights-agent to interpret `/tmp/usage-data.json`.

## Options

- `--sessions N` - Number of sessions to analyze (default: 10)
- `--project PATH` - Analyze specific project
- `--no-prometheus` - Skip Prometheus metrics
- `--format json` - Output JSON for agent interpretation

## Pipeline

1. **Data Collection** (Python) → Structured JSON
2. **Interpretation** (usage-insights-agent) → Insights
3. **Optimization** (workflow-optimizer skill) → Fixes
```

---

## Commit Strategy

1. `feat(usage-analyzer): add source_type and command discovery`
2. `feat(usage-analyzer): add plugin discovery`
3. `feat(usage-analyzer): add CLAUDE.md parsing`
4. `refactor(usage-analyzer): simplify to pure data collection with JSON output`
5. `feat(usage-analyzer): create usage-insights-agent for interpretation`
6. `feat(usage-analyzer): update workflow-optimizer for new architecture`
7. `chore: bump version to 1.6.0`
