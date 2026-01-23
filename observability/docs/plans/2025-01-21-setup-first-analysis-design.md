# Setup-First Analysis Design

## Problem

The workflow-optimizer pipeline analyzes usage patterns without first establishing context about the user's setup. This leads to:
- Shallow analysis that doesn't account for setup complexity
- Recommendations that ignore coverage gaps
- No adaptive depth based on how many components exist

## Solution

Two-phase analysis with setup-first approach.

```
┌─────────────────────────────────────────────────────────────────┐
│                    REVISED PIPELINE                              │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  collect_usage.py                                                │
│  ├── Discover components (skills, agents, commands, hooks)       │
│  ├── NEW: Compute setup_profile                                  │
│  │   ├── complexity (minimal/moderate/complex)                   │
│  │   ├── shape (plugin-heavy, hook-light, etc.)                  │
│  │   ├── red_flags (pre-usage issues)                            │
│  │   └── coverage_gaps (missing workflow areas)                  │
│  ├── Parse sessions and prometheus                               │
│  └── Output: JSON with setup_profile section                     │
│                         ↓                                        │
│  usage-insights-agent                                            │
│  ├── PHASE 1: Setup Understanding                                │
│  │   └── Present setup summary table FIRST                       │
│  ├── PHASE 2: Usage Analysis (depth adapts to complexity)        │
│  │   └── Contextualize findings with setup knowledge             │
│  └── Output: Insights with setup context                         │
│                         ↓                                        │
│  workflow-optimizer                                              │
│  └── Generate fixes informed by coverage gaps + removals         │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

## Changes

### 1. Collector Changes (`collect_usage.py`)

Add `setup_profile` section to JSON output:

```json
{
  "_schema": { ... },
  "setup_profile": {
    "complexity": "moderate",
    "total_components": 43,
    "shape": ["plugin-heavy", "hook-light"],
    "by_source": {
      "global": {"skills": 2, "agents": 0, "commands": 0, "hooks": 2},
      "project": {"skills": 0, "agents": 0, "commands": 0, "hooks": 1},
      "plugin:observability": {"skills": 3, "agents": 1, "commands": 4, "hooks": 0},
      "plugin:superpowers": {"skills": 15, "agents": 0, "commands": 0, "hooks": 2}
    },
    "red_flags": [
      "No project-level CLAUDE.md",
      "No project-level skills",
      "3 skills have overlapping triggers"
    ],
    "coverage": {
      "git_commit": true,
      "code_review": true,
      "testing": true,
      "debugging": true,
      "planning": true,
      "event_sourcing": false,
      "documentation": false,
      "security": true
    },
    "coverage_gaps": ["event_sourcing", "documentation"],
    "overlapping_triggers": [
      {"trigger": "debug", "items": ["systematic-debugging", "debugger", "root-cause-analyst"]}
    ]
  },
  "discovery": { ... },
  "sessions": { ... },
  "stats": { ... },
  "claude_md": { ... },
  "prometheus": { ... }
}
```

#### Complexity Thresholds

| Complexity | Component Count | Analysis Approach |
|------------|-----------------|-------------------|
| Minimal | <10 | Deep dive each component, focus on what's MISSING |
| Moderate | 10-50 | Standard analysis, balance utilization and gaps |
| Complex | 50+ | Summary stats + top issues only |

#### Shape Detection

| Shape | Detection Logic |
|-------|-----------------|
| `plugin-heavy` | >70% components from plugins |
| `hook-light` | <3 hooks total |
| `no-project-customization` | No project-level skills/agents/CLAUDE.md |
| `global-heavy` | Everything in ~/.claude, nothing project-specific |
| `duplicate-triggers` | Multiple skills respond to same phrases |
| `stale-config` | CLAUDE.md references non-existent skills |

#### Coverage Categories

| Category | Detection Keywords |
|----------|-------------------|
| `git_commit` | commit, pre-commit |
| `code_review` | review, pr |
| `testing` | test, tdd, spec |
| `debugging` | debug, troubleshoot |
| `planning` | plan, design |
| `event_sourcing` | aggregate, event, projection, cqrs |
| `documentation` | doc, readme, guide |
| `security` | vulnerability, secret, security |

#### Red Flags

| Red Flag | Detection Logic |
|----------|-----------------|
| No project-level CLAUDE.md | Only global or no config files found |
| No project-level hooks | No hooks in `.claude/settings.json` |
| No project-level skills | No skills in `.claude/skills/` |
| Stale config references | CLAUDE.md mentions skills/agents that don't exist |
| Duplicate triggers | Multiple skills match same phrases |
| Overlapping agents | Multiple agents with similar triggers/descriptions |
| Global hooks that should be project-level | Hooks in `~/.claude/settings.json` that reference project paths |
| Empty descriptions | Skills/agents without meaningful descriptions |

### 2. Insights-Agent Restructure

Update `usage-insights-agent.md` to follow two-phase workflow:

#### Phase 1: Setup Understanding (ALWAYS FIRST)

Before ANY usage analysis, present the setup summary:

```markdown
## Setup Summary

**Complexity:** {complexity} ({total_components} components)
**Shape:** {shape_list}

### Component Distribution
| Source | Skills | Agents | Commands | Hooks |
|--------|--------|--------|----------|-------|
| Global | ... | ... | ... | ... |
| Project | ... | ... | ... | ... |
| plugin:X | ... | ... | ... | ... |

### Red Flags (Pre-Usage Issues)
- {red_flag_1}
- {red_flag_2}

### Coverage Gaps
Missing tooling for: {coverage_gaps}

### Overlapping Triggers
{trigger}: matched by {item1}, {item2}, {item3}
```

#### Phase 2: Usage Analysis (adapts to complexity)

| Complexity | Approach |
|------------|----------|
| Minimal | Deep dive each component, heavy focus on what's MISSING |
| Moderate | Standard analysis, balance utilization and gaps |
| Complex | Summary stats + top 5 issues only |

For complex setups, output:
```markdown
### Usage Summary
- Skills: 30 total, 8 used (27%), 5 with trigger issues
- Agents: 8 total, 2 used (25%)

### Top Issues
1. {issue with evidence}
2. {issue with evidence}
3. {issue with evidence}
```

### 3. Workflow-Optimizer Updates

Update `workflow-optimizer/SKILL.md` to use setup context:

#### Coverage-Aware Recommendations

When generating fixes, check `setup_profile.coverage_gaps`:

| Gap | Look For | Recommendation |
|-----|----------|----------------|
| testing | "test", "spec", "assert", "TDD" in prompts | Add test-driven-development skill |
| debugging | "error", "bug", "fix", "investigate" in prompts | Add systematic-debugging skill |
| event_sourcing | "aggregate", "event", "projection" in prompts | Add domain-specific skills |

#### Shape-Aware Recommendations

| Shape | Recommendation Approach |
|-------|------------------------|
| plugin-heavy | Don't suggest more plugins, focus on project customization |
| hook-light | Suggest automation opportunities |
| no-project-customization | Prioritize creating project-level CLAUDE.md |

#### Removal Recommendations

Identify components that add noise without value:

| Scenario | Detection | Action |
|----------|-----------|--------|
| Never-used | 0 uses across 20+ sessions AND triggers don't match any prompts | Consider removing |
| Redundant | 2+ skills cover same area, one never used | Remove unused one |
| Stale global | Global component only matches one project's prompts | Move to project |
| Disabled but present | CLAUDE.md says "don't use X" but X exists | Remove X entirely |

Output format:
```markdown
### Removal Candidates
| Component | Type | Reason | Last Used | Action |
|-----------|------|--------|-----------|--------|
| old-debug-skill | skill | Replaced by systematic-debugging | Never | Remove |
| legacy-formatter | hook | Conflicts with prettier hook | 30d ago | Remove |
```

## Files to Modify

1. `observability/skills/observability-usage-collector/scripts/collect_usage.py`
   - Add `compute_setup_profile()` function
   - Add `setup_profile` to `generate_analysis_json()` output

2. `observability/agents/usage-insights-agent.md`
   - Restructure to Phase 1 (Setup) + Phase 2 (Usage) workflow
   - Add setup summary template
   - Add adaptive depth instructions based on complexity

3. `observability/skills/observability-workflow-optimizer/SKILL.md`
   - Add coverage gap recommendations section
   - Add shape-aware recommendations
   - Add removal recommendations section
