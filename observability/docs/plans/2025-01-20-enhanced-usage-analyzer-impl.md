# Enhanced Usage Analyzer Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Enhance usage-analyzer to discover commands from plugins, analyze CLAUDE.md files, and output multi-subject reports.

**Architecture:** Extend existing analyze_usage.py with new discovery functions, CLAUDE.md parser, and refactored output system. No new files needed - all changes in single script.

**Tech Stack:** Python 3.10+, PyYAML, existing dataclasses

---

## Task 1: Add source_type to SkillOrAgent Dataclass

**Files:**
- Modify: `skills/observability-usage-analyzer/scripts/analyze_usage.py:30-37`

**Step 1: Update dataclass definition**

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

**Step 2: Run script to verify no syntax errors**

Run: `python observability/skills/observability-usage-analyzer/scripts/analyze_usage.py --help`
Expected: Help message displays without errors

**Step 3: Commit**

```bash
git add observability/skills/observability-usage-analyzer/scripts/analyze_usage.py
git commit -m "feat(usage-analyzer): add source_type to SkillOrAgent dataclass"
```

---

## Task 2: Add Command Discovery Function

**Files:**
- Modify: `skills/observability-usage-analyzer/scripts/analyze_usage.py` (after discover_agents function, ~line 318)

**Step 1: Add discover_commands function**

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

                if not description:
                    lines = content.split("\n")
                    for i, line in enumerate(lines):
                        if line.startswith("#"):
                            for next_line in lines[i+1:]:
                                if next_line.strip() and not next_line.startswith("#"):
                                    description = next_line.strip()
                                    break
                            break

                triggers = extract_triggers_from_description(description)
                triggers.append(name)
                triggers.append(f"/{name}")  # Commands are invoked with /

                # Determine source type from path
                source_type = "unknown"
                path_str = str(base_path)
                if "/.claude/" in path_str and "/plugins/" not in path_str:
                    source_type = "global" if str(Path.home()) in path_str else "project"

                commands.append(SkillOrAgent(
                    name=name,
                    type="command",
                    description=description[:200],
                    triggers=triggers,
                    source_path=str(cmd_file),
                    source_type=source_type,
                ))
            except Exception as e:
                print(f"Warning: Could not parse {cmd_file}: {e}", file=sys.stderr)

    return commands
```

**Step 2: Run script to verify**

Run: `python observability/skills/observability-usage-analyzer/scripts/analyze_usage.py --help`
Expected: Help displays without errors

**Step 3: Commit**

```bash
git add observability/skills/observability-usage-analyzer/scripts/analyze_usage.py
git commit -m "feat(usage-analyzer): add command discovery function"
```

---

## Task 3: Add Plugin Discovery Function

**Files:**
- Modify: `skills/observability-usage-analyzer/scripts/analyze_usage.py` (after discover_commands)

**Step 1: Add discover_from_plugins function**

```python
def discover_from_plugins(plugins_cache: Path) -> tuple[list[SkillOrAgent], list[SkillOrAgent], list[SkillOrAgent]]:
    """Discover skills, agents, and commands from installed plugins."""
    skills = []
    agents = []
    commands = []

    if not plugins_cache.exists():
        return skills, agents, commands

    # Structure: cache/<marketplace>/<plugin-name>/<version>/
    for marketplace_dir in plugins_cache.iterdir():
        if not marketplace_dir.is_dir() or marketplace_dir.name.startswith("temp_"):
            continue

        for plugin_dir in marketplace_dir.iterdir():
            if not plugin_dir.is_dir():
                continue

            # Find latest version directory
            version_dirs = [d for d in plugin_dir.iterdir() if d.is_dir() and not d.name.startswith(".")]
            if not version_dirs:
                continue

            # Use most recently modified version
            latest_version = max(version_dirs, key=lambda d: d.stat().st_mtime)
            plugin_name = plugin_dir.name
            source_type = f"plugin:{plugin_name}"

            # Discover skills
            skills_path = latest_version / "skills"
            if skills_path.exists():
                for skill_dir in skills_path.iterdir():
                    if not skill_dir.is_dir():
                        continue
                    skill_md = skill_dir / "SKILL.md"
                    if skill_md.exists():
                        try:
                            content = skill_md.read_text()
                            frontmatter = extract_yaml_frontmatter(content)
                            name = frontmatter.get("name", skill_dir.name)
                            description = frontmatter.get("description", "")
                            triggers = extract_triggers_from_description(description)
                            triggers.append(name)

                            skills.append(SkillOrAgent(
                                name=name,
                                type="skill",
                                description=description,
                                triggers=triggers,
                                source_path=str(skill_md),
                                source_type=source_type,
                            ))
                        except Exception as e:
                            print(f"Warning: Could not parse {skill_md}: {e}", file=sys.stderr)

            # Discover agents
            agents_path = latest_version / "agents"
            if agents_path.exists():
                for agent_file in agents_path.glob("*.md"):
                    try:
                        content = agent_file.read_text()
                        frontmatter = extract_yaml_frontmatter(content)
                        name = frontmatter.get("name", agent_file.stem)
                        description = frontmatter.get("description", "")
                        if not description:
                            lines = content.split("\n")
                            for i, line in enumerate(lines):
                                if line.startswith("#"):
                                    for next_line in lines[i+1:]:
                                        if next_line.strip() and not next_line.startswith("#"):
                                            description = next_line.strip()
                                            break
                                    break
                        triggers = extract_triggers_from_description(description)
                        triggers.append(name)

                        agents.append(SkillOrAgent(
                            name=name,
                            type="agent",
                            description=description[:200],
                            triggers=triggers,
                            source_path=str(agent_file),
                            source_type=source_type,
                        ))
                    except Exception as e:
                        print(f"Warning: Could not parse {agent_file}: {e}", file=sys.stderr)

            # Discover commands
            commands_path = latest_version / "commands"
            if commands_path.exists():
                for cmd_file in commands_path.glob("*.md"):
                    try:
                        content = cmd_file.read_text()
                        frontmatter = extract_yaml_frontmatter(content)
                        name = frontmatter.get("name", cmd_file.stem)
                        description = frontmatter.get("description", "")
                        if not description:
                            lines = content.split("\n")
                            for i, line in enumerate(lines):
                                if line.startswith("#"):
                                    for next_line in lines[i+1:]:
                                        if next_line.strip() and not next_line.startswith("#"):
                                            description = next_line.strip()
                                            break
                                    break
                        triggers = extract_triggers_from_description(description)
                        triggers.append(name)
                        triggers.append(f"/{name}")

                        commands.append(SkillOrAgent(
                            name=name,
                            type="command",
                            description=description[:200],
                            triggers=triggers,
                            source_path=str(cmd_file),
                            source_type=source_type,
                        ))
                    except Exception as e:
                        print(f"Warning: Could not parse {cmd_file}: {e}", file=sys.stderr)

    return skills, agents, commands
```

**Step 2: Run script to verify**

Run: `python observability/skills/observability-usage-analyzer/scripts/analyze_usage.py --help`
Expected: Help displays without errors

**Step 3: Commit**

```bash
git add observability/skills/observability-usage-analyzer/scripts/analyze_usage.py
git commit -m "feat(usage-analyzer): add plugin discovery for skills, agents, commands"
```

---

## Task 4: Add CLAUDE.md Parsing Functions

**Files:**
- Modify: `skills/observability-usage-analyzer/scripts/analyze_usage.py` (add new section after discovery functions)

**Step 1: Add ClaudeMdAnalysis dataclass**

```python
@dataclass
class ClaudeMdAnalysis:
    files_found: list[str] = field(default_factory=list)
    files_missing: list[str] = field(default_factory=list)
    subjects: list[str] = field(default_factory=list)
    referenced_items: list[str] = field(default_factory=list)
    subject_keywords: dict[str, list[str]] = field(default_factory=dict)
```

**Step 2: Add parse_claude_md function**

```python
def parse_claude_md(paths: list[Path]) -> ClaudeMdAnalysis:
    """Parse CLAUDE.md files to extract subjects and referenced items."""
    analysis = ClaudeMdAnalysis()

    # Subject extraction patterns
    subject_patterns = {
        "TDD": ["tdd", "test-driven", "test driven", "write test first", "failing test"],
        "Git": ["git", "commit", "branch", "merge", "pr", "pull request"],
        "Architecture": ["architecture", "ddd", "domain", "bounded context", "aggregate"],
        "Parallelization": ["parallel", "concurrent", "multiple agents", "simultaneously"],
        "Code Review": ["review", "code review", "pr review"],
        "Debugging": ["debug", "debugger", "troubleshoot", "investigate"],
        "Planning": ["plan", "planning", "brainstorm", "design"],
        "Documentation": ["document", "docs", "readme", "docstring"],
    }

    for path in paths:
        if path.exists():
            analysis.files_found.append(str(path))
            try:
                content = path.read_text().lower()

                # Extract section headers as subjects
                for line in path.read_text().split("\n"):
                    if line.startswith("## "):
                        subject = line[3:].strip()
                        if subject and subject not in analysis.subjects:
                            analysis.subjects.append(subject)

                # Match subject patterns
                for subject, keywords in subject_patterns.items():
                    matched_keywords = [kw for kw in keywords if kw in content]
                    if matched_keywords:
                        if subject not in analysis.subjects:
                            analysis.subjects.append(subject)
                        analysis.subject_keywords[subject] = matched_keywords

                # Find referenced skill/agent/command names
                # Look for patterns like "use X skill", "@agent-name", "/command"
                skill_refs = re.findall(r'["\']([a-z0-9-]+)["\'](?:\s+skill|\s+agent)', content)
                cmd_refs = re.findall(r'/([a-z0-9-]+)', content)
                at_refs = re.findall(r'@([a-z0-9-]+)', content)

                analysis.referenced_items.extend(skill_refs)
                analysis.referenced_items.extend(cmd_refs)
                analysis.referenced_items.extend(at_refs)

            except Exception as e:
                print(f"Warning: Could not parse {path}: {e}", file=sys.stderr)
        else:
            analysis.files_missing.append(str(path))

    analysis.referenced_items = list(set(analysis.referenced_items))
    return analysis
```

**Step 3: Run script to verify**

Run: `python observability/skills/observability-usage-analyzer/scripts/analyze_usage.py --help`
Expected: Help displays without errors

**Step 4: Commit**

```bash
git add observability/skills/observability-usage-analyzer/scripts/analyze_usage.py
git commit -m "feat(usage-analyzer): add CLAUDE.md parsing for subjects and references"
```

---

## Task 5: Add Health Check Analysis

**Files:**
- Modify: `skills/observability-usage-analyzer/scripts/analyze_usage.py` (after parse_claude_md)

**Step 1: Add HealthCheckResult dataclass**

```python
@dataclass
class HealthCheckResult:
    referenced_missing: list[str] = field(default_factory=list)
    workflow_contradictions: list[str] = field(default_factory=list)
    coverage_gaps: list[str] = field(default_factory=list)
    well_configured: list[str] = field(default_factory=list)
```

**Step 2: Add analyze_health function**

```python
def analyze_health(
    claude_md: ClaudeMdAnalysis,
    all_items: list[SkillOrAgent],
    jsonl_stats: dict,
) -> HealthCheckResult:
    """Analyze CLAUDE.md configuration health."""
    result = HealthCheckResult()

    all_item_names = {item.name.lower() for item in all_items}

    # Check referenced but missing items
    for ref in claude_md.referenced_items:
        if ref.lower() not in all_item_names:
            result.referenced_missing.append(ref)

    # Check workflow contradictions
    # If CLAUDE.md mentions "always use X" but X is rarely used
    for subject, keywords in claude_md.subject_keywords.items():
        if "always" in " ".join(keywords) or "must" in " ".join(keywords):
            # Find related items
            related_items = [
                item for item in all_items
                if any(kw in item.name.lower() or kw in item.description.lower()
                       for kw in keywords)
            ]
            for item in related_items:
                used_count = jsonl_stats.get(f"{item.type}s_used", {}).get(item.name, 0)
                missed_count = jsonl_stats.get(f"missed_{item.type}s", {}).get(item.name, 0)
                if missed_count > used_count:
                    result.workflow_contradictions.append(
                        f"CLAUDE.md emphasizes '{subject}' but {item.name} missed {missed_count} times vs used {used_count}"
                    )

    # Check coverage gaps - subjects without supporting tools
    subject_to_item_keywords = {
        "TDD": ["tdd", "test", "driven"],
        "Git": ["git", "commit", "review"],
        "Architecture": ["architect", "ddd", "domain"],
        "Parallelization": ["parallel", "dispatch", "concurrent"],
        "Debugging": ["debug", "diagnos", "troubleshoot"],
        "Planning": ["plan", "brainstorm", "design"],
    }

    for subject in claude_md.subjects:
        keywords = subject_to_item_keywords.get(subject, [subject.lower()])
        supporting_items = [
            item for item in all_items
            if any(kw in item.name.lower() or kw in item.description.lower()
                   for kw in keywords)
        ]
        if not supporting_items:
            result.coverage_gaps.append(f"Subject '{subject}' has no supporting skills/agents")

    # Find well-configured areas
    for subject in claude_md.subjects:
        keywords = subject_to_item_keywords.get(subject, [subject.lower()])
        supporting_items = [
            item for item in all_items
            if any(kw in item.name.lower() or kw in item.description.lower()
                   for kw in keywords)
        ]
        used_items = [
            item for item in supporting_items
            if jsonl_stats.get(f"{item.type}s_used", {}).get(item.name, 0) > 0
        ]
        if used_items:
            result.well_configured.append(f"{subject}: using {', '.join(i.name for i in used_items)}")

    return result
```

**Step 3: Run script to verify**

Run: `python observability/skills/observability-usage-analyzer/scripts/analyze_usage.py --help`
Expected: Help displays without errors

**Step 4: Commit**

```bash
git add observability/skills/observability-usage-analyzer/scripts/analyze_usage.py
git commit -m "feat(usage-analyzer): add CLAUDE.md health check analysis"
```

---

## Task 6: Add Multi-Subject Output Formatters

**Files:**
- Modify: `skills/observability-usage-analyzer/scripts/analyze_usage.py` (in Output Formatters section)

**Step 1: Add print_by_type function**

```python
def print_by_type(
    skills: list[SkillOrAgent],
    agents: list[SkillOrAgent],
    commands: list[SkillOrAgent],
    jsonl_stats: dict,
):
    """Print analysis grouped by tool type."""
    print("\n" + "═" * 60)
    print(" BY TOOL TYPE")
    print("═" * 60)

    for type_name, items, used_key, missed_key in [
        ("SKILLS", skills, "skills_used", "missed_skills"),
        ("AGENTS", agents, "agents_used", "missed_agents"),
        ("COMMANDS", commands, "commands_used", "missed_commands"),
    ]:
        discovered = len(items)
        used = len(jsonl_stats.get(used_key, {}))
        missed = sum(jsonl_stats.get(missed_key, {}).values())

        print(f"\n═══ {type_name} ═══")
        print(f"  Discovered: {discovered} | Used: {used} | Missed: {missed}")

        top_missed = sorted(jsonl_stats.get(missed_key, {}).items(), key=lambda x: -x[1])[:3]
        if top_missed:
            print(f"  Top missed: {', '.join(f'{n} ({c})' for n, c in top_missed)}")
```

**Step 2: Add print_by_stage function**

```python
def print_by_stage(prom_data: PrometheusData, jsonl_stats: dict):
    """Print analysis grouped by workflow stage."""
    print("\n" + "═" * 60)
    print(" BY WORKFLOW STAGE")
    print("═" * 60)

    stages = ["brainstorm", "plan", "implement", "test", "review", "commit"]
    max_count = max(prom_data.workflow_stages.values()) if prom_data.workflow_stages else 1

    for stage in stages:
        count = prom_data.workflow_stages.get(stage, 0)
        pct = (count / max_count * 100) if max_count > 0 else 0
        bar = "█" * int(pct / 10) + "░" * (10 - int(pct / 10))

        gap_marker = " ← Gap" if count == 0 else ""
        print(f"  {stage:12} {bar} {pct:3.0f}%{gap_marker}")
```

**Step 3: Add print_by_subject function**

```python
def print_by_subject(
    claude_md: ClaudeMdAnalysis,
    all_items: list[SkillOrAgent],
    jsonl_stats: dict,
):
    """Print analysis grouped by CLAUDE.md subjects."""
    print("\n" + "═" * 60)
    print(" BY PROJECT CONTEXT (from CLAUDE.md)")
    print("═" * 60)

    subject_keywords = {
        "TDD": ["tdd", "test", "driven"],
        "Git": ["git", "commit", "review"],
        "Architecture": ["architect", "ddd", "domain"],
        "Parallelization": ["parallel", "dispatch", "concurrent"],
        "Debugging": ["debug", "diagnos", "troubleshoot"],
        "Planning": ["plan", "brainstorm", "design"],
    }

    for subject in claude_md.subjects[:8]:  # Limit to 8 subjects
        keywords = subject_keywords.get(subject, [subject.lower()])

        related_items = [
            item for item in all_items
            if any(kw in item.name.lower() or kw in item.description.lower()
                   for kw in keywords)
        ]

        print(f"\n═══ {subject.upper()} ═══")

        if related_items:
            print(f"  Related: {', '.join(i.name for i in related_items[:5])}")
            used = sum(
                1 for i in related_items
                if jsonl_stats.get(f"{i.type}s_used", {}).get(i.name, 0) > 0
            )
            missed = sum(
                jsonl_stats.get(f"missed_{i.type}s", {}).get(i.name, 0)
                for i in related_items
            )
            print(f"  Coverage: {used} used, {missed} missed opportunities")
        else:
            print("  No supporting skills/agents found")
```

**Step 4: Add print_health_check function**

```python
def print_health_check(
    claude_md: ClaudeMdAnalysis,
    health: HealthCheckResult,
):
    """Print CLAUDE.md health check results."""
    print("\n" + "═" * 60)
    print(" CLAUDE.MD HEALTH CHECK")
    print("═" * 60)

    print("\n📄 Files Analyzed:")
    for f in claude_md.files_found:
        print(f"  ✓ {f}")
    for f in claude_md.files_missing:
        print(f"  ✗ {f} (not found)")

    if health.referenced_missing:
        print("\n⚠️  Referenced But Missing:")
        for item in health.referenced_missing[:5]:
            print(f"  • '{item}' mentioned but not installed")

    if health.workflow_contradictions:
        print("\n🔄 Workflow Contradictions:")
        for c in health.workflow_contradictions[:5]:
            print(f"  • {c}")

    if health.coverage_gaps:
        print("\n📊 Coverage Gaps:")
        for g in health.coverage_gaps[:5]:
            print(f"  • {g}")

    if health.well_configured:
        print("\n✅ Well-Configured:")
        for w in health.well_configured[:5]:
            print(f"  • {w}")
```

**Step 5: Run script to verify**

Run: `python observability/skills/observability-usage-analyzer/scripts/analyze_usage.py --help`
Expected: Help displays without errors

**Step 6: Commit**

```bash
git add observability/skills/observability-usage-analyzer/scripts/analyze_usage.py
git commit -m "feat(usage-analyzer): add multi-subject output formatters"
```

---

## Task 7: Update CLI Arguments and main()

**Files:**
- Modify: `skills/observability-usage-analyzer/scripts/analyze_usage.py` (main function)

**Step 1: Add new CLI arguments**

In the `main()` function, add after existing arguments:

```python
    parser.add_argument("--health-check", action="store_true", help="Run CLAUDE.md health analysis only")
    parser.add_argument("--by-subject", action="store_true", help="Group output by CLAUDE.md subjects")
    parser.add_argument("--by-stage", action="store_true", help="Group output by workflow stage")
    parser.add_argument("--by-type", action="store_true", help="Group output by tool type")
    parser.add_argument("--all-sections", action="store_true", help="Show all groupings")
```

**Step 2: Update discovery section in main()**

Replace the discovery section with:

```python
    # Discover skills, agents, and commands from all sources
    home = Path.home()
    cwd = Path.cwd()

    skill_paths = [home / ".claude" / "skills", cwd / ".claude" / "skills"]
    agent_paths = [home / ".claude" / "agents", cwd / ".claude" / "agents"]
    command_paths = [home / ".claude" / "commands", cwd / ".claude" / "commands"]
    plugins_cache = home / ".claude" / "plugins" / "cache"

    print("Discovering skills, agents, and commands...", file=sys.stderr)

    # From standard paths
    skills = discover_skills(skill_paths)
    agents = discover_agents(agent_paths)
    commands = discover_commands(command_paths)

    # From plugins
    plugin_skills, plugin_agents, plugin_commands = discover_from_plugins(plugins_cache)
    skills.extend(plugin_skills)
    agents.extend(plugin_agents)
    commands.extend(plugin_commands)

    print(f"Found {len(skills)} skills, {len(agents)} agents, {len(commands)} commands", file=sys.stderr)

    # Parse CLAUDE.md files
    claude_md_paths = [
        home / ".claude" / "CLAUDE.md",
        cwd / "CLAUDE.md",
        cwd / ".claude" / "instructions.md",
    ]
    claude_md = parse_claude_md(claude_md_paths)
    print(f"Parsed {len(claude_md.files_found)} CLAUDE.md files, found {len(claude_md.subjects)} subjects", file=sys.stderr)
```

**Step 3: Update stats dict to include commands**

In `analyze_jsonl`, add commands tracking:

```python
    stats = {
        "total_sessions": len(sessions),
        "total_prompts": sum(len(s.prompts) for s in sessions),
        "skills_used": defaultdict(int),
        "agents_used": defaultdict(int),
        "commands_used": defaultdict(int),  # Add this
        "missed_skills": defaultdict(int),
        "missed_agents": defaultdict(int),
        "missed_commands": defaultdict(int),  # Add this
    }
```

**Step 4: Update output section in main()**

Replace the output section:

```python
    # Analyze JSONL (now includes commands)
    all_items = skills + agents + commands
    missed, jsonl_stats = analyze_jsonl(skills, agents, sessions)  # Note: extend this to include commands

    # Health check analysis
    health = analyze_health(claude_md, all_items, jsonl_stats)

    # Correlate data
    insights = correlate_data(prom_data, jsonl_stats, missed)

    # Output based on flags
    if args.health_check:
        print_health_check(claude_md, health)
        return

    if args.format == "json":
        # Extend JSON output with new data
        print_json(prom_data, jsonl_stats, insights, missed)
    elif args.format == "dashboard":
        print_dashboard(prom_data, jsonl_stats, insights)
    else:
        # Default table or multi-section output
        if args.all_sections or (not args.by_type and not args.by_stage and not args.by_subject):
            # Show all sections by default
            print_table(prom_data, jsonl_stats, insights, missed, args.verbose)
            print_by_type(skills, agents, commands, jsonl_stats)
            if prom_data.available:
                print_by_stage(prom_data, jsonl_stats)
            if claude_md.files_found:
                print_by_subject(claude_md, all_items, jsonl_stats)
                print_health_check(claude_md, health)
        else:
            if args.by_type:
                print_by_type(skills, agents, commands, jsonl_stats)
            if args.by_stage and prom_data.available:
                print_by_stage(prom_data, jsonl_stats)
            if args.by_subject and claude_md.files_found:
                print_by_subject(claude_md, all_items, jsonl_stats)
                print_health_check(claude_md, health)
```

**Step 5: Test the complete implementation**

Run: `python observability/skills/observability-usage-analyzer/scripts/analyze_usage.py --all-sections --no-prometheus`
Expected: Multi-section output with skills, agents, commands, and CLAUDE.md analysis

**Step 6: Commit**

```bash
git add observability/skills/observability-usage-analyzer/scripts/analyze_usage.py
git commit -m "feat(usage-analyzer): integrate enhanced discovery and multi-subject output"
```

---

## Final Verification

**Run full test:**

```bash
cd /Users/bartoszglowacki/Projects/bglowacki-marketplace/observability
python skills/observability-usage-analyzer/scripts/analyze_usage.py --all-sections --verbose --no-prometheus
```

**Expected output sections:**
1. USAGE ANALYSIS REPORT (existing)
2. BY TOOL TYPE (new)
3. BY WORKFLOW STAGE (if Prometheus available)
4. BY PROJECT CONTEXT (new)
5. CLAUDE.MD HEALTH CHECK (new)

**Bump version:**

```bash
# Update version in plugin.json to next minor version
```
