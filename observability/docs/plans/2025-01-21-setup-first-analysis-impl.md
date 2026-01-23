# Setup-First Analysis Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Add setup profile computation to the collector and restructure the insights-agent for two-phase analysis.

**Architecture:** Add `compute_setup_profile()` function to collector that computes complexity, shape, red flags, and coverage gaps from existing discovered data. Update insights-agent to present setup summary before usage analysis.

**Tech Stack:** Python 3.10+, YAML frontmatter parsing

---

## Task 1: Add SetupProfile Dataclass

**Files:**
- Modify: `observability/skills/observability-usage-collector/scripts/collect_usage.py:31-79`

**Step 1: Add SetupProfile dataclass after existing dataclasses**

Add after line 79 (after PrometheusData):

```python
@dataclass
class SetupProfile:
    complexity: str  # "minimal", "moderate", "complex"
    total_components: int
    shape: list[str]  # e.g., ["plugin-heavy", "hook-light"]
    by_source: dict[str, dict[str, int]]  # source_type -> {skills, agents, commands, hooks}
    red_flags: list[str]
    coverage: dict[str, bool]
    coverage_gaps: list[str]
    overlapping_triggers: list[dict]  # [{trigger, items}]
```

**Step 2: Run to verify syntax**

Run: `python -m py_compile observability/skills/observability-usage-collector/scripts/collect_usage.py`
Expected: No output (success)

**Step 3: Commit**

```bash
git add observability/skills/observability-usage-collector/scripts/collect_usage.py
git commit -m "feat(observability): add SetupProfile dataclass"
```

---

## Task 2: Add compute_setup_profile Function

**Files:**
- Modify: `observability/skills/observability-usage-collector/scripts/collect_usage.py`

**Step 1: Add compute_setup_profile function after dataclasses**

Add after SetupProfile dataclass (around line 90):

```python
def compute_setup_profile(
    skills: list[SkillOrAgent],
    agents: list[SkillOrAgent],
    commands: list[SkillOrAgent],
    hooks: list[Hook],
    claude_md: dict,
) -> SetupProfile:
    """Compute setup profile for context-first analysis."""

    # Count by source
    by_source: dict[str, dict[str, int]] = defaultdict(lambda: {"skills": 0, "agents": 0, "commands": 0, "hooks": 0})
    for s in skills:
        by_source[s.source_type]["skills"] += 1
    for a in agents:
        by_source[a.source_type]["agents"] += 1
    for c in commands:
        by_source[c.source_type]["commands"] += 1
    for h in hooks:
        by_source[h.source_type]["hooks"] += 1

    # Complexity classification
    total = len(skills) + len(agents) + len(commands) + len(hooks)
    if total < 10:
        complexity = "minimal"
    elif total < 50:
        complexity = "moderate"
    else:
        complexity = "complex"

    # Shape analysis
    shape = []
    total_skills_agents = len(skills) + len(agents)
    plugin_count = sum(
        v["skills"] + v["agents"]
        for k, v in by_source.items()
        if k.startswith("plugin:")
    )
    if total_skills_agents > 0 and (plugin_count / total_skills_agents) > 0.7:
        shape.append("plugin-heavy")
    if len(hooks) < 3:
        shape.append("hook-light")
    if by_source["project"]["skills"] == 0 and by_source["project"]["agents"] == 0:
        if not any(f for f in claude_md.get("files_found", []) if "CLAUDE.md" in f and ".claude" not in f):
            shape.append("no-project-customization")
    if by_source["global"]["skills"] + by_source["global"]["agents"] > 0 and by_source["project"]["skills"] + by_source["project"]["agents"] == 0:
        shape.append("global-heavy")

    # Red flags
    red_flags = []
    project_claude_md = [f for f in claude_md.get("files_found", []) if "CLAUDE.md" in f and ".claude" not in f and str(Path.home()) not in f]
    if not project_claude_md:
        red_flags.append("No project-level CLAUDE.md")
    if by_source["project"]["hooks"] == 0 and by_source.get("project-local", {}).get("hooks", 0) == 0:
        red_flags.append("No project-level hooks")
    if by_source["project"]["skills"] == 0:
        red_flags.append("No project-level skills")

    # Check for empty descriptions
    empty_desc_count = sum(1 for s in skills + agents if not s.description.strip())
    if empty_desc_count > 0:
        red_flags.append(f"{empty_desc_count} components with empty descriptions")

    # Find overlapping triggers
    trigger_map: dict[str, list[str]] = defaultdict(list)
    for item in skills + agents:
        for trigger in item.triggers:
            trigger_lower = trigger.lower()
            if len(trigger_lower) > 4:  # Skip short triggers
                trigger_map[trigger_lower].append(f"{item.type}:{item.name}")

    overlapping = []
    for trigger, items in trigger_map.items():
        if len(items) > 1:
            overlapping.append({"trigger": trigger, "items": items})

    if overlapping:
        red_flags.append(f"{len(overlapping)} triggers overlap across multiple components")

    # Coverage assessment
    all_items = skills + agents
    all_names_desc = " ".join(
        f"{i.name.lower()} {i.description.lower()}" for i in all_items
    )

    coverage = {
        "git_commit": any(kw in all_names_desc for kw in ["commit", "pre-commit"]),
        "code_review": any(kw in all_names_desc for kw in ["review", "pr review"]),
        "testing": any(kw in all_names_desc for kw in ["test", "tdd", "spec"]),
        "debugging": any(kw in all_names_desc for kw in ["debug", "troubleshoot"]),
        "planning": any(kw in all_names_desc for kw in ["plan", "design", "architect"]),
        "event_sourcing": any(kw in all_names_desc for kw in ["aggregate", "event sourc", "projection", "cqrs"]),
        "documentation": any(kw in all_names_desc for kw in ["documentation", "readme", "guide"]),
        "security": any(kw in all_names_desc for kw in ["vulnerab", "secret", "security"]),
    }

    coverage_gaps = [k for k, v in coverage.items() if not v]

    return SetupProfile(
        complexity=complexity,
        total_components=total,
        shape=shape,
        by_source=dict(by_source),
        red_flags=red_flags,
        coverage=coverage,
        coverage_gaps=coverage_gaps,
        overlapping_triggers=overlapping[:10],  # Limit to top 10
    )
```

**Step 2: Run to verify syntax**

Run: `python -m py_compile observability/skills/observability-usage-collector/scripts/collect_usage.py`
Expected: No output (success)

**Step 3: Commit**

```bash
git add observability/skills/observability-usage-collector/scripts/collect_usage.py
git commit -m "feat(observability): add compute_setup_profile function"
```

---

## Task 3: Update generate_analysis_json to Include setup_profile

**Files:**
- Modify: `observability/skills/observability-usage-collector/scripts/collect_usage.py:599-705`

**Step 1: Update generate_analysis_json signature**

Change the function signature at line 599 to add setup_profile parameter:

```python
def generate_analysis_json(
    skills: list[SkillOrAgent],
    agents: list[SkillOrAgent],
    commands: list[SkillOrAgent],
    hooks: list[Hook],
    sessions: list[SessionData],
    jsonl_stats: dict,
    claude_md: dict,
    prom_data: PrometheusData,
    setup_profile: SetupProfile,
) -> dict:
```

**Step 2: Add setup_profile to the returned dict**

After the `_schema` section (around line 622), add:

```python
        "setup_profile": {
            "complexity": setup_profile.complexity,
            "total_components": setup_profile.total_components,
            "shape": setup_profile.shape,
            "by_source": setup_profile.by_source,
            "red_flags": setup_profile.red_flags,
            "coverage": setup_profile.coverage,
            "coverage_gaps": setup_profile.coverage_gaps,
            "overlapping_triggers": setup_profile.overlapping_triggers,
        },
```

**Step 3: Update _schema sections**

Add to `_schema.sections` dict:

```python
                "setup_profile": "Computed setup profile with complexity, shape, red flags, and coverage gaps",
```

**Step 4: Commit**

```bash
git add observability/skills/observability-usage-collector/scripts/collect_usage.py
git commit -m "feat(observability): add setup_profile to JSON output"
```

---

## Task 4: Update main() to Compute and Pass setup_profile

**Files:**
- Modify: `observability/skills/observability-usage-collector/scripts/collect_usage.py:1133-1239`

**Step 1: Add setup_profile computation after hooks discovery**

After line 1193 (`hooks = discover_hooks(...)`), add:

```python
    setup_profile = compute_setup_profile(skills, agents, commands, hooks, claude_md)
    print(f"  ✓ Setup: {setup_profile.complexity} complexity, {len(setup_profile.red_flags)} red flags", file=sys.stderr)
```

**Step 2: Update generate_analysis_json call**

At line 1228, update the call to pass setup_profile:

```python
        output = generate_analysis_json(
            skills, agents, commands, hooks, sessions, jsonl_stats, claude_md, prom_data, setup_profile
        )
```

**Step 3: Run to verify**

Run: `cd /Users/bartoszglowacki/Projects/bglowacki-marketplace && uv run observability/skills/observability-usage-collector/scripts/collect_usage.py --format json --sessions 5 2>/dev/null | head -50`
Expected: JSON output with `setup_profile` section

**Step 4: Commit**

```bash
git add observability/skills/observability-usage-collector/scripts/collect_usage.py
git commit -m "feat(observability): integrate setup_profile in main collection flow"
```

---

## Task 5: Restructure usage-insights-agent.md

**Files:**
- Modify: `observability/agents/usage-insights-agent.md`

**Step 1: Replace entire file content**

```markdown
---
name: usage-insights-agent
description: Analyzes Claude Code usage data to identify patterns, missed opportunities, and configuration issues. Use after running usage-collector with JSON output. Triggers on "analyze usage data", "interpret usage", "what am I missing", or when usage JSON is provided.
model: opus
tools: Read, Bash
---

# Usage Insights Agent

You analyze Claude Code usage data to provide intelligent insights about skill/agent/command usage patterns.

## Input

You receive JSON data from `collect_usage.py --format json` containing:
- **setup_profile**: Computed setup context (complexity, shape, red flags, coverage gaps)
- **discovery**: All available skills, agents, commands, and hooks with descriptions
- **sessions**: Recent user prompts
- **stats**: Usage counts and potential matches
- **claude_md**: Configuration file content
- **prometheus**: Metrics and trends (if available)

## Analysis Workflow

### Phase 1: Setup Understanding (ALWAYS DO FIRST)

Before ANY usage analysis, present the setup summary. Start your response with:

```markdown
## Setup Summary

**Complexity:** {setup_profile.complexity} ({setup_profile.total_components} components)
**Shape:** {setup_profile.shape joined by ", "}

### Component Distribution
| Source | Skills | Agents | Commands | Hooks |
|--------|--------|--------|----------|-------|
| Global | {by_source.global.skills} | {by_source.global.agents} | {by_source.global.commands} | {by_source.global.hooks} |
| Project | {by_source.project.skills} | {by_source.project.agents} | {by_source.project.commands} | {by_source.project.hooks} |
| plugin:X | ... | ... | ... | ... |

### Red Flags (Pre-Usage Issues)
- {red_flag_1}
- {red_flag_2}

### Coverage Gaps
Missing tooling for: {coverage_gaps joined by ", "}

### Overlapping Triggers
- "{trigger}": matched by {items joined by ", "}
```

### Phase 2: Usage Analysis (adapts to complexity)

**CRITICAL:** Adjust your analysis depth based on setup complexity:

| Complexity | Approach |
|------------|----------|
| **Minimal** (<10 components) | Deep dive each component, heavy focus on what's MISSING |
| **Moderate** (10-50) | Standard analysis, balance utilization and gaps |
| **Complex** (50+) | Summary stats + top 5 issues only, avoid component enumeration |

For **complex** setups, output summary stats first:
```markdown
### Usage Summary
- Skills: {total} total, {used} used ({percent}%), {issues} with trigger issues
- Agents: {total} total, {used} used ({percent}%)

### Top Issues
1. {issue with evidence}
2. {issue with evidence}
3. {issue with evidence}
```

### Phase 2a: Opportunity Detection

For each item in `stats.potential_matches`:
- Read the user prompts that triggered the match
- Understand what the user was trying to accomplish
- Determine if the suggested item would have actually helped
- Filter out false positives (e.g., generic word matches)

### Phase 2b: Configuration Analysis

Review `claude_md.content` for:
- Workflow instructions that aren't supported by available tools
- Referenced skills/agents that don't exist (use setup_profile.red_flags for stale refs)
- Contradictions between instructions and actual usage patterns

### Phase 2c: Usage Pattern Analysis

If prometheus data available:
- Identify declining usage (might indicate discovery issues)
- Find underutilized workflow stages
- Spot success rate anomalies

### Phase 2d: Hook Analysis

Review `discovery.hooks` for:
- Hooks in global settings that should be project-level
- Missing hooks for repetitive patterns (e.g., auto-formatting, validation)
- Hook coverage gaps (e.g., no PreToolUse hooks for dangerous commands)

### Phase 2e: Correlation

Connect setup context with usage patterns:
- "Coverage gap 'testing' + 5 prompts about tests = recommend TDD skill"
- "No project-level CLAUDE.md + inconsistent workflow = recommend project setup"
- "Overlapping triggers 'debug' + confusion in sessions = recommend differentiation"

## Output Format

### For Minimal/Moderate Complexity

Provide insights in these categories:

#### High-Priority Findings
Issues that significantly impact workflow effectiveness.

#### Missed Opportunities
Genuine cases where a skill/agent would have helped.

#### Configuration Issues
Problems with CLAUDE.md or missing tools.

#### Hook Recommendations
- Hooks that should be moved from global to project level
- New hooks to add for automation
- Unnecessary or redundant hooks to remove

#### Positive Patterns
What's working well - reinforce good habits.

#### Recommendations
Specific, actionable improvements ordered by impact.

### For Complex Setups

Focus output on actionable items only:

#### Setup Summary
(from Phase 1)

#### Top 5 Issues
With specific evidence and recommended fixes.

#### Removal Candidates
Components that add noise without value:
- Never-used components (0 uses across all sessions)
- Redundant components (multiple covering same area, one never used)
- Stale global components (global items only matching one project)

## Guidelines

- Be specific: "The prompt 'help me debug this error' on Jan 15 could have used systematic-debugging"
- Avoid false positives: Generic words like "help" or "create" shouldn't trigger matches
- Consider context: Sometimes not using a skill is the right choice
- Prioritize: Focus on patterns, not one-off misses
- **Use setup context**: Let red flags and coverage gaps guide your analysis

## Project Relevance Filter

**CRITICAL:** Focus insights on what's relevant to the CURRENT PROJECT.

When the data includes sessions from multiple projects, filter your insights:

**EXCLUDE from recommendations:**
- Skills/agents from unrelated domains (e.g., `plugin-dev` agents for a business app)
- Global configuration issues that don't affect the current project
- Patterns from other projects that happened to be in the data
- Duplicate skill warnings for plugins not used in this project

**INCLUDE only insights about:**
- Skills/agents that match the current project's domain
- Configuration issues in the project's CLAUDE.md
- Missed opportunities from sessions in this project
- Workflow improvements relevant to what this project does

Ask: "Would someone working on THIS project care about this insight?"
```

**Step 2: Commit**

```bash
git add observability/agents/usage-insights-agent.md
git commit -m "feat(observability): restructure insights-agent with Phase 1 (Setup) + Phase 2 (Usage)"
```

---

## Task 6: Update workflow-optimizer SKILL.md

**Files:**
- Modify: `observability/skills/observability-workflow-optimizer/SKILL.md`

**Step 1: Replace entire file content**

```markdown
---
name: observability-workflow-optimizer
description: Takes insights from usage-insights-agent and generates minimal, actionable fixes. Triggers on "optimize workflow", "fix missed opportunities", or after reviewing usage insights.
---

# Workflow Optimizer

Generate minimal, targeted improvements based on usage insights.

## Prerequisites

Run in this order:
1. `uv run ${CLAUDE_PLUGIN_ROOT}/skills/observability-usage-collector/scripts/collect_usage.py --format json > /tmp/usage-data.json`
2. Use usage-insights-agent to interpret the data
3. Use this skill to generate fixes

## Input

You receive insights from usage-insights-agent identifying:
- Setup profile (complexity, shape, red flags, coverage gaps)
- Missed opportunities (with specific prompts)
- Configuration issues
- Usage patterns
- Hook effectiveness

## Project Context Filter

**CRITICAL:** Only generate fixes relevant to the CURRENT PROJECT being worked on.

When analyzing insights, **EXCLUDE** recommendations about:
- Skills/agents from unrelated plugins (e.g., plugin-dev agents when working on a business app)
- Global configuration issues unrelated to current project
- Duplicate skills in `~/.claude/skills/` unless they affect current project
- Patterns from sessions in other projects

**INCLUDE** only:
- Missed opportunities from sessions in the current project
- Skills/agents that would help with the current project's domain
- Project-level CLAUDE.md improvements
- Hooks that would improve the current project's workflow

Ask yourself: "Would this fix help someone working on THIS project specifically?"

## Fix Strategy

### Order of Preference (minimal first)

1. **Add trigger phrases** - Extend description with specific phrases
2. **Clarify description** - Make it clearer when to use
3. **Update CLAUDE.md** - Add workflow guidance
4. **Add/update hooks** - Automate repetitive patterns
5. **Split item** - Only if clearly doing multiple unrelated things
6. **Create new item** - Last resort

### Coverage-Aware Recommendations

When insights include coverage gaps, check for matching patterns in prompts:

| Coverage Gap | Look For in Prompts | Recommendation |
|--------------|---------------------|----------------|
| testing | "test", "spec", "assert", "TDD" | Add test-driven-development skill |
| debugging | "error", "bug", "fix", "investigate" | Add systematic-debugging skill |
| event_sourcing | "aggregate", "event", "projection", "CQRS" | Add domain-specific skills |
| documentation | "doc", "readme", "guide", "explain" | Add documentation skills |
| security | "vulnerable", "secret", "security", "CVE" | Add security scanning skills |

### Shape-Aware Recommendations

Adjust recommendations based on setup shape:

| Shape | Recommendation Approach |
|-------|------------------------|
| plugin-heavy | Don't suggest more plugins, focus on project customization |
| hook-light | Suggest automation opportunities |
| no-project-customization | Prioritize creating project-level CLAUDE.md |
| global-heavy | Recommend moving relevant items to project level |

### Removal Recommendations

Identify components that add noise without value:

| Scenario | Detection | Action |
|----------|-----------|--------|
| Never-used | 0 uses across 20+ sessions AND triggers don't match any prompts | Consider removing |
| Redundant | 2+ skills cover same area, one never used | Remove unused one |
| Stale global | Global component only matches one project's prompts | Move to project |
| Disabled but present | CLAUDE.md says "don't use X" but X exists | Remove X entirely |

Output removal candidates as:
```markdown
### Removal Candidates
| Component | Type | Reason | Last Used | Action |
|-----------|------|--------|-----------|--------|
| old-debug-skill | skill | Replaced by systematic-debugging | Never | Remove |
| legacy-formatter | hook | Conflicts with prettier hook | 30d ago | Remove |
```

### Hook Placement Rules

**ALWAYS prefer project-level hooks over global hooks:**

| Location | When to Use |
|----------|-------------|
| `.claude/settings.json` | Project-specific hooks (shared with team) |
| `.claude/settings.local.json` | Personal project overrides (not committed) |
| `~/.claude/settings.json` | Only for truly global preferences |

**Rationale:** Project hooks are:
- Scoped to where they're needed
- Shared with team via git
- Don't pollute global config
- Take precedence over global settings

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
uv run ${CLAUDE_PLUGIN_ROOT}/skills/observability-usage-collector/scripts/collect_usage.py --format json > /tmp/usage-data.json
# Then use usage-insights-agent to verify improvements
```

## Anti-Patterns

**DON'T:**
- Add generic triggers ("help", "fix", "create")
- Duplicate triggers across items
- Create new items when trigger refinement works
- Change one item without checking conflicts
- Create hooks in global `~/.claude/settings.json` for project-specific behavior
- Add hooks that duplicate existing skill/agent functionality
- Recommend fixes for unrelated plugins (e.g., plugin-dev for a business app)
- Suggest global skill/agent changes based on single-project patterns
- Suggest adding more plugins when setup is already plugin-heavy

**DO:**
- Use specific, distinctive triggers
- Check for conflicts with similar items
- Test with usage-collector after changes
- Prefer description changes over structural changes
- Create hooks in project `.claude/settings.json`
- Use hooks for automation (formatting, validation) not for workflow guidance
- Focus fixes on the current project's domain and needs
- Filter out noise from cross-project analysis
- Recommend removals for unused/redundant components
```

**Step 2: Commit**

```bash
git add observability/skills/observability-workflow-optimizer/SKILL.md
git commit -m "feat(observability): add coverage-aware and removal recommendations to workflow-optimizer"
```

---

## Task 7: Bump Plugin Version

**Files:**
- Modify: `observability/.claude-plugin/plugin.json`

**Step 1: Read current version**

Run: `cat observability/.claude-plugin/plugin.json | grep version`

**Step 2: Bump to next minor version**

Update the version field (e.g., from "1.15.1" to "1.16.0").

**Step 3: Commit**

```bash
git add observability/.claude-plugin/plugin.json
git commit -m "chore(observability): bump version to 1.16.0"
```

---

## Task 8: Test the Complete Pipeline

**Step 1: Run collector and verify setup_profile in output**

Run: `cd /Users/bartoszglowacki/Projects/bglowacki-marketplace && uv run observability/skills/observability-usage-collector/scripts/collect_usage.py --format json --sessions 5 2>&1 | grep -A 20 '"setup_profile"'`

Expected: JSON output with complexity, shape, red_flags, coverage, coverage_gaps, overlapping_triggers

**Step 2: Verify stderr output includes setup info**

Run: `cd /Users/bartoszglowacki/Projects/bglowacki-marketplace && uv run observability/skills/observability-usage-collector/scripts/collect_usage.py --format json --sessions 5 2>&1 1>/dev/null`

Expected: Lines showing "Setup: {complexity} complexity, {N} red flags"
