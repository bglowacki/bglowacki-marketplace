#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.10"
# dependencies = ["pyyaml"]
# ///
"""
Usage Collector - Collect Claude Code usage data for analysis.

Gathers data from JSONL session files to provide:
- Tool usage counts and patterns
- Outcomes (success/failure/interrupted)
- Compactions and context efficiency
- Workflow stage detection

Outputs structured data for interpretation by usage-insights-agent.
This script performs DATA COLLECTION only - no analysis or recommendations.
"""

import argparse
import json
import os
import re
import sys
from collections import defaultdict
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from pathlib import Path
from typing import Optional


@dataclass
class SkillOrAgent:
    name: str
    type: str  # "skill", "agent", or "command"
    description: str
    triggers: list[str]
    source_path: str
    source_type: str = "unknown"  # "global", "project", or "plugin:<name>"


@dataclass
class Hook:
    event_type: str  # PreToolUse, PostToolUse, Stop, etc.
    matcher: str  # Tool matcher pattern (e.g., "Bash", "*")
    command: str  # The command/script to run
    source_path: str
    source_type: str  # "global", "project", "project-local", or "plugin:<name>"
    timeout: Optional[int] = None


@dataclass
class InterruptedTool:
    tool_name: str
    tool_input: dict
    followup_message: str  # What user said after interrupting


@dataclass
class SessionData:
    session_id: str
    prompts: list[str] = field(default_factory=list)
    skills_used: set[str] = field(default_factory=set)
    agents_used: set[str] = field(default_factory=set)
    tools_used: set[str] = field(default_factory=set)
    hooks_triggered: dict[str, int] = field(default_factory=lambda: defaultdict(int))
    # Outcome tracking
    success_count: int = 0
    failure_count: int = 0
    interrupted_count: int = 0
    compaction_count: int = 0
    # Interrupted tools with context
    interrupted_tools: list[InterruptedTool] = field(default_factory=list)


@dataclass
class MissedOpportunity:
    prompt: str
    session_id: str
    matched_item: SkillOrAgent
    matched_triggers: list[str]


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
    plugin_usage: dict[str, list[str]]  # {"active": [...], "potential": [...], "unused": [...]}


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
    global_claude_dir = str(Path.home() / ".claude")
    project_claude_md = [f for f in claude_md.get("files_found", []) if "CLAUDE.md" in f and ".claude" not in f and not f.startswith(global_claude_dir)]
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
        plugin_usage={"active": [], "potential": [], "unused": []},  # Computed later
    )


def read_plugin_enabled_states(
    global_settings: Path,
    project_settings: Path,
) -> dict[str, bool]:
    """Read plugin enabled/disabled states from settings.

    Project settings override global settings.
    Returns dict mapping plugin_id -> enabled (True/False).
    """
    enabled_states: dict[str, bool] = {}

    # Read global settings first
    if global_settings.exists():
        try:
            settings = json.loads(global_settings.read_text())
            for plugin_id, enabled in settings.get("enabledPlugins", {}).items():
                enabled_states[plugin_id] = enabled
        except (json.JSONDecodeError, Exception):
            pass

    # Project settings override global
    if project_settings.exists():
        try:
            settings = json.loads(project_settings.read_text())
            for plugin_id, enabled in settings.get("enabledPlugins", {}).items():
                enabled_states[plugin_id] = enabled
        except (json.JSONDecodeError, Exception):
            pass

    return enabled_states


def compute_plugin_usage(
    skills: list[SkillOrAgent],
    agents: list[SkillOrAgent],
    sessions: list,  # list[SessionData]
    potential_matches: list,  # list[MissedOpportunity]
    enabled_states: dict[str, bool] | None = None,
) -> dict[str, list[str]]:
    """Compute plugin usage: active, potential, unused, or disabled_but_matched.

    - active: Plugin was used in sessions (skill/agent triggered)
    - potential: Plugin is ENABLED, matched prompts but wasn't triggered
    - unused: Plugin is ENABLED but has no activity at all
    - disabled_but_matched: Plugin is DISABLED but matched prompts (might want to enable)

    Args:
        enabled_states: Dict mapping plugin_id (e.g., "plugin@marketplace") -> enabled bool.
                       If None, assumes all discovered plugins are enabled.
    """
    enabled_states = enabled_states or {}

    def is_plugin_enabled(plugin_name: str) -> bool:
        """Check if plugin is enabled. Unknown plugins assumed enabled (discovered = installed)."""
        # Find full plugin ID (plugin_name@marketplace) in enabled_states
        for plugin_id, enabled in enabled_states.items():
            # Match by plugin name (before @)
            if plugin_id.split("@")[0] == plugin_name:
                return enabled
        # Plugin not in settings = assumed enabled (it's installed/discovered)
        return True

    # Get all plugins from discovery
    all_plugins: set[str] = set()
    plugin_to_components: dict[str, list[str]] = defaultdict(list)

    for item in skills + agents:
        source = item.source_type
        if source.startswith("plugin:"):
            plugin_name = source.replace("plugin:", "")
            all_plugins.add(plugin_name)
            plugin_to_components[plugin_name].append(item.name)

    # Check which plugins were used in sessions
    active: set[str] = set()
    used_skills = set()
    used_agents = set()

    for session in sessions:
        used_skills.update(session.skills_used)
        used_agents.update(session.agents_used)

    for plugin, components in plugin_to_components.items():
        for comp in components:
            # Check if component was used (handle namespaced names like "plugin:name")
            if comp in used_skills or comp in used_agents:
                active.add(plugin)
                break
            # Also check for plugin-prefixed names
            prefixed = f"{plugin}:{comp}"
            if prefixed in used_skills or prefixed in used_agents:
                active.add(plugin)
                break

    # Check which plugins had potential matches (matched prompts but weren't used)
    matched_but_not_used: set[str] = set()
    for match in potential_matches:
        source = match.matched_item.source_type
        if source.startswith("plugin:"):
            plugin_name = source.replace("plugin:", "")
            if plugin_name not in active:
                matched_but_not_used.add(plugin_name)

    # Classify based on enabled state
    potential: set[str] = set()  # Enabled + matched but not used
    disabled_but_matched: set[str] = set()  # Disabled + matched (might want to enable)

    for plugin in matched_but_not_used:
        if is_plugin_enabled(plugin):
            potential.add(plugin)
        else:
            disabled_but_matched.add(plugin)

    # Unused = enabled plugins with no activity at all
    # Don't include disabled plugins here - they're disabled on purpose
    all_with_no_activity = all_plugins - active - matched_but_not_used
    unused: set[str] = set()
    already_disabled: set[str] = set()

    for plugin in all_with_no_activity:
        if is_plugin_enabled(plugin):
            unused.add(plugin)
        else:
            already_disabled.add(plugin)

    return {
        "active": sorted(active),
        "potential": sorted(potential),
        "unused": sorted(unused),
        "disabled_but_matched": sorted(disabled_but_matched),
        "already_disabled": sorted(already_disabled),
    }


# =============================================================================
# JSONL Parser
# =============================================================================

def extract_yaml_frontmatter(content: str) -> dict:
    """Extract YAML frontmatter from markdown content."""
    import yaml

    if not content.startswith("---"):
        return {}

    parts = content.split("---", 2)
    if len(parts) < 3:
        return {}

    try:
        return yaml.safe_load(parts[1]) or {}
    except yaml.YAMLError:
        return {}


def extract_triggers_from_description(description: str) -> list[str]:
    """Extract trigger phrases from a description string."""
    triggers = []

    trigger_patterns = [
        r'[Tt]riggers?\s+on\s+["\']([^"\']+)["\']',
        r'[Tt]riggers?\s+on\s+([^,.]+(?:,\s*[^,.]+)*)',
        r'[Uu]se\s+(?:this\s+)?(?:skill|agent)\s+when\s+([^.]+)',
        r'[Uu]se\s+for\s+([^.]+)',
    ]

    for pattern in trigger_patterns:
        matches = re.findall(pattern, description)
        for match in matches:
            parts = re.split(r',\s*|\s+or\s+', match)
            triggers.extend([p.strip().strip('"\'') for p in parts if p.strip()])

    quoted = re.findall(r'["\']([^"\']+)["\']', description)
    triggers.extend(quoted)

    return list(set(triggers))


def discover_skills(paths: list[Path]) -> list[SkillOrAgent]:
    """Discover skills from given paths."""
    skills = []
    global_claude_dir = str(Path.home() / ".claude")
    for base_path in paths:
        if not base_path.exists():
            continue

        source_type = "global" if str(base_path).startswith(global_claude_dir) else "project"

        for skill_dir in base_path.iterdir():
            if not skill_dir.is_dir():
                continue

            skill_md = skill_dir / "SKILL.md"
            if not skill_md.exists():
                continue

            try:
                content = skill_md.read_text()
                frontmatter = extract_yaml_frontmatter(content)

                name = frontmatter.get("name", skill_dir.name)
                description = frontmatter.get("description", "")
                triggers = extract_triggers_from_description(description)
                triggers.append(name.lower())

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

    return skills


def discover_agents(paths: list[Path]) -> list[SkillOrAgent]:
    """Discover agents from given paths."""
    agents = []
    global_claude_dir = str(Path.home() / ".claude")
    for base_path in paths:
        if not base_path.exists():
            continue

        source_type = "global" if str(base_path).startswith(global_claude_dir) else "project"

        for agent_file in base_path.glob("*.md"):
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
                triggers.append(name.lower())

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

    return agents


def discover_commands(paths: list[Path]) -> list[SkillOrAgent]:
    """Discover commands from given paths."""
    commands = []
    global_claude_dir = str(Path.home() / ".claude")

    for base_path in paths:
        if not base_path.exists():
            continue

        source_type = "global" if str(base_path).startswith(global_claude_dir) else "project"

        for cmd_file in base_path.glob("*.md"):
            try:
                content = cmd_file.read_text()
                frontmatter = extract_yaml_frontmatter(content)
                name = frontmatter.get("name", cmd_file.stem)
                description = frontmatter.get("description", "")
                triggers = extract_triggers_from_description(description)
                triggers.append(name.lower())
                triggers.append(f"/{name.lower()}")

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
                        try:
                            content = skill_md.read_text()
                            frontmatter = extract_yaml_frontmatter(content)
                            name = frontmatter.get("name", skill_dir.name)
                            triggers = extract_triggers_from_description(frontmatter.get("description", ""))
                            triggers.append(name.lower())
                            skills.append(SkillOrAgent(
                                name=name,
                                type="skill",
                                description=frontmatter.get("description", ""),
                                triggers=triggers,
                                source_path=str(skill_md),
                                source_type=source_type,
                            ))
                        except Exception as e:
                            print(f"Warning: Could not parse {skill_md}: {e}", file=sys.stderr)

            # Agents
            agents_path = latest_version / "agents"
            if agents_path.exists():
                for agent_file in agents_path.glob("*.md"):
                    try:
                        content = agent_file.read_text()
                        frontmatter = extract_yaml_frontmatter(content)
                        name = frontmatter.get("name", agent_file.stem)
                        triggers = extract_triggers_from_description(frontmatter.get("description", ""))
                        triggers.append(name.lower())
                        agents.append(SkillOrAgent(
                            name=name,
                            type="agent",
                            description=frontmatter.get("description", "")[:200],
                            triggers=triggers,
                            source_path=str(agent_file),
                            source_type=source_type,
                        ))
                    except Exception as e:
                        print(f"Warning: Could not parse {agent_file}: {e}", file=sys.stderr)

            # Commands
            commands_path = latest_version / "commands"
            if commands_path.exists():
                for cmd_file in commands_path.glob("*.md"):
                    try:
                        content = cmd_file.read_text()
                        frontmatter = extract_yaml_frontmatter(content)
                        name = frontmatter.get("name", cmd_file.stem)
                        triggers = extract_triggers_from_description(frontmatter.get("description", ""))
                        triggers.append(name.lower())
                        triggers.append(f"/{name.lower()}")
                        commands.append(SkillOrAgent(
                            name=name,
                            type="command",
                            description=frontmatter.get("description", "")[:200],
                            triggers=triggers,
                            source_path=str(cmd_file),
                            source_type=source_type,
                        ))
                    except Exception as e:
                        print(f"Warning: Could not parse {cmd_file}: {e}", file=sys.stderr)

    return skills, agents, commands


def discover_hooks(settings_paths: list[tuple[Path, str]], plugins_cache: Path) -> list[Hook]:
    """Discover hooks from settings files and plugins.

    Args:
        settings_paths: List of (path, source_type) tuples
        plugins_cache: Path to plugins cache directory
    """
    hooks = []

    # Discover from settings files
    for settings_path, source_type in settings_paths:
        if not settings_path.exists():
            continue

        try:
            settings = json.loads(settings_path.read_text())
            hooks_config = settings.get("hooks", {})

            for event_type, matchers in hooks_config.items():
                if isinstance(matchers, dict):
                    # Format: {"Bash": "command"} or {"Bash": [...]}
                    for matcher, hook_def in matchers.items():
                        if isinstance(hook_def, str):
                            hooks.append(Hook(
                                event_type=event_type,
                                matcher=matcher,
                                command=hook_def,
                                source_path=str(settings_path),
                                source_type=source_type,
                            ))
                        elif isinstance(hook_def, list):
                            for h in hook_def:
                                if isinstance(h, dict):
                                    hooks.append(Hook(
                                        event_type=event_type,
                                        matcher=matcher,
                                        command=h.get("command", ""),
                                        source_path=str(settings_path),
                                        source_type=source_type,
                                        timeout=h.get("timeout"),
                                    ))
                elif isinstance(matchers, list):
                    # Format: [{"matcher": "Bash", "hooks": [...]}]
                    for matcher_group in matchers:
                        matcher = matcher_group.get("matcher", "*")
                        for h in matcher_group.get("hooks", []):
                            if isinstance(h, dict):
                                hooks.append(Hook(
                                    event_type=event_type,
                                    matcher=matcher,
                                    command=h.get("command", ""),
                                    source_path=str(settings_path),
                                    source_type=source_type,
                                    timeout=h.get("timeout"),
                                ))
        except (json.JSONDecodeError, Exception) as e:
            print(f"Warning: Could not parse hooks from {settings_path}: {e}", file=sys.stderr)

    # Discover from plugins
    if plugins_cache.exists():
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
                plugin_json = latest_version / ".claude-plugin" / "plugin.json"

                if not plugin_json.exists():
                    plugin_json = latest_version / "plugin.json"

                if plugin_json.exists():
                    try:
                        plugin_config = json.loads(plugin_json.read_text())
                        plugin_name = plugin_config.get("name", plugin_dir.name)
                        hooks_config = plugin_config.get("hooks", {})

                        for event_type, matchers in hooks_config.items():
                            if isinstance(matchers, list):
                                for matcher_group in matchers:
                                    matcher = matcher_group.get("matcher", "*")
                                    for h in matcher_group.get("hooks", []):
                                        if isinstance(h, dict):
                                            hooks.append(Hook(
                                                event_type=event_type,
                                                matcher=matcher,
                                                command=h.get("command", ""),
                                                source_path=str(plugin_json),
                                                source_type=f"plugin:{plugin_name}",
                                                timeout=h.get("timeout"),
                                            ))
                    except (json.JSONDecodeError, Exception) as e:
                        print(f"Warning: Could not parse hooks from {plugin_json}: {e}", file=sys.stderr)

    return hooks


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


def _is_system_prompt(content: str) -> bool:
    """Filter out system-generated prompts."""
    if content.startswith("Base directory for this skill:"):
        return True
    if content.startswith("[TRACE-ID:"):
        return True
    if "<command-message>" in content or "<command-name>" in content:
        return True
    return False


def _summarize_tool_input(tool_name: str, tool_input: dict) -> str:
    """Extract meaningful context from tool input."""
    if tool_name == "Bash":
        cmd = tool_input.get("command", "")
        return cmd[:100] if cmd else ""
    if tool_name in ("Edit", "Write", "Read"):
        return tool_input.get("file_path", "")[:100]
    if tool_name == "Skill":
        return tool_input.get("skill", "")
    if tool_name == "Task":
        agent = tool_input.get("subagent_type", "")
        desc = tool_input.get("description", "")
        return f"{agent}: {desc}"[:100] if desc else agent
    if tool_name == "Grep":
        pattern = tool_input.get("pattern", "")
        return f"pattern: {pattern}"[:100]
    if tool_name == "Glob":
        pattern = tool_input.get("pattern", "")
        return f"glob: {pattern}"[:100]
    return str(tool_input)[:100]


def detect_outcome(tool_name: str, result: str) -> str:
    """Detect outcome from tool result content."""
    result_lower = result.lower()

    if tool_name == "Bash":
        if "exit code: 0" in result_lower or "succeeded" in result_lower:
            return "success"
        if "exit code:" in result_lower:
            return "failure"
        if "timeout" in result_lower:
            return "failure"
        if any(kw in result_lower for kw in ["error:", "failed", "traceback", "permission denied"]):
            return "failure"
        return "success"

    if tool_name in ("Edit", "Write", "NotebookEdit"):
        if any(kw in result_lower for kw in ["permission denied", "file not found", "no such file",
                                              "old_string not found", "not unique", "error"]):
            return "failure"
        return "success"

    if "error" in result_lower or "failed" in result_lower:
        return "failure"
    return "success"


def resolve_project_path(projects_dir: Path, project_path: str) -> tuple[Path | None, list[Path]]:
    """Resolve project path to actual folder, with fuzzy matching.

    Returns (resolved_path, matches) where:
    - resolved_path is the single matching folder or None
    - matches is list of all matching folders (for error reporting)
    """
    # Try exact match first (full path like /Users/foo/project)
    project_folder = project_path.replace("/", "-")
    project_dir = projects_dir / project_folder
    if project_dir.exists():
        return project_dir, [project_dir]

    # Try fuzzy match: find folders ending with the project name
    if not projects_dir.exists():
        return None, []

    matches = [
        d for d in projects_dir.iterdir()
        if d.is_dir() and d.name.endswith(f"-{project_path}")
    ]

    if len(matches) == 1:
        return matches[0], matches
    return None, matches


def find_project_sessions(projects_dir: Path, project_dir: Path, max_sessions: int) -> list[Path]:
    """Find session files for a project."""
    if not project_dir.exists():
        return []

    session_files = sorted(
        project_dir.glob("*.jsonl"),
        key=lambda p: p.stat().st_mtime,
        reverse=True
    )

    return session_files[:max_sessions]


def parse_session_file(session_path: Path) -> SessionData:
    """Parse a session JSONL file with outcome and compaction tracking."""
    session_data = SessionData(session_id=session_path.stem[:8])
    pending_tools: dict[str, tuple[str, dict]] = {}  # tool_use_id -> (tool_name, tool_input)
    awaiting_followup: list[tuple[str, dict]] = []  # Tools that were interrupted, waiting for next user message

    try:
        lines = session_path.read_text().strip().split("\n")

        for line in lines:
            try:
                entry = json.loads(line)
                entry_type = entry.get("type")

                # Detect compactions
                if entry_type == "system" and entry.get("subtype") == "compact_boundary":
                    session_data.compaction_count += 1
                    continue

                if entry_type == "user":
                    message = entry.get("message", {})
                    content = message.get("content", "")

                    # Extract user text from message (for followup capture)
                    user_text = ""
                    is_interruption = False

                    if isinstance(content, str):
                        if "[Request interrupted by user]" in content:
                            is_interruption = True
                        elif content.strip() and not _is_system_prompt(content):
                            user_text = content
                            session_data.prompts.append(content)
                    elif isinstance(content, list):
                        for item in content:
                            if isinstance(item, dict):
                                item_type = item.get("type")
                                if item_type == "text":
                                    text = item.get("text", "")
                                    if "[Request interrupted by user]" in text:
                                        is_interruption = True
                                    elif not _is_system_prompt(text):
                                        if not user_text:  # Take first non-system text
                                            user_text = text
                                        session_data.prompts.append(text)
                                elif item_type == "tool_result":
                                    # Tool results are in user messages
                                    tool_use_id = item.get("tool_use_id", "")
                                    result = item.get("content", "")

                                    # Get tool info and remove from pending
                                    tool_info = pending_tools.pop(tool_use_id, ("unknown", {}))
                                    tool_name = tool_info[0]

                                    if isinstance(result, str):
                                        outcome = detect_outcome(tool_name, result)
                                        if outcome == "success":
                                            session_data.success_count += 1
                                        else:
                                            session_data.failure_count += 1

                    # Handle interruption - capture which tools were pending
                    if is_interruption:
                        session_data.interrupted_count += 1
                        # Mark all pending tools as interrupted, awaiting followup
                        for tool_use_id, (tool_name, tool_input) in pending_tools.items():
                            awaiting_followup.append((tool_name, tool_input))
                        pending_tools.clear()

                    # If we have tools awaiting followup and user said something, capture it
                    elif user_text and awaiting_followup:
                        for tool_name, tool_input in awaiting_followup:
                            session_data.interrupted_tools.append(InterruptedTool(
                                tool_name=tool_name,
                                tool_input=tool_input,
                                followup_message=user_text[:500],  # Limit length
                            ))
                        awaiting_followup.clear()

                elif entry_type == "assistant":
                    message = entry.get("message", {})
                    content = message.get("content", [])

                    if isinstance(content, list):
                        for item in content:
                            if isinstance(item, dict) and item.get("type") == "tool_use":
                                tool_name = item.get("name", "")
                                tool_use_id = item.get("id", "")
                                tool_input = item.get("input", {})

                                # Track pending tools with full info
                                if tool_use_id:
                                    pending_tools[tool_use_id] = (tool_name, tool_input)

                                if tool_name == "Skill":
                                    skill = tool_input.get("skill", "")
                                    if skill:
                                        session_data.skills_used.add(skill)

                                elif tool_name == "Task":
                                    agent = tool_input.get("subagent_type", "")
                                    if agent:
                                        session_data.agents_used.add(agent)

                                else:
                                    session_data.tools_used.add(tool_name)

            except json.JSONDecodeError:
                continue

        # Remaining pending tools at session end are interrupted (no followup available)
        for tool_use_id, (tool_name, tool_input) in pending_tools.items():
            session_data.interrupted_count += 1
            session_data.interrupted_tools.append(InterruptedTool(
                tool_name=tool_name,
                tool_input=tool_input,
                followup_message="[session ended]",
            ))

    except Exception as e:
        print(f"Warning: Could not parse {session_path}: {e}", file=sys.stderr)

    return session_data


def find_matches(prompt: str, items: list[SkillOrAgent], min_triggers: int = 2) -> list[tuple[SkillOrAgent, list[str]]]:
    """Find skills/agents that match a prompt based on triggers."""
    matches = []
    prompt_lower = prompt.lower()

    for item in items:
        matched_triggers = []
        for trigger in item.triggers:
            trigger_lower = trigger.lower()
            if len(trigger_lower) > 3:
                if re.search(r'\b' + re.escape(trigger_lower) + r'\b', prompt_lower):
                    matched_triggers.append(trigger)

        name_matched = item.name.lower() in [t.lower() for t in matched_triggers]
        if len(matched_triggers) >= min_triggers or name_matched:
            matches.append((item, matched_triggers))

    return matches


def analyze_jsonl(
    skills: list[SkillOrAgent],
    agents: list[SkillOrAgent],
    commands: list[SkillOrAgent],
    sessions: list[SessionData],
) -> tuple[list[MissedOpportunity], dict]:
    """Analyze sessions for missed opportunities."""
    missed = []
    stats = {
        "total_sessions": len(sessions),
        "total_prompts": sum(len(s.prompts) for s in sessions),
        "skills_used": defaultdict(int),
        "agents_used": defaultdict(int),
        "commands_used": defaultdict(int),
        "missed_skills": defaultdict(int),
        "missed_agents": defaultdict(int),
        "missed_commands": defaultdict(int),
        # New outcome stats
        "total_success": sum(s.success_count for s in sessions),
        "total_failure": sum(s.failure_count for s in sessions),
        "total_interrupted": sum(s.interrupted_count for s in sessions),
        "total_compactions": sum(s.compaction_count for s in sessions),
    }

    all_items = skills + agents + commands

    for session in sessions:
        for skill in session.skills_used:
            stats["skills_used"][skill] += 1
        for agent in session.agents_used:
            stats["agents_used"][agent] += 1

        for prompt in session.prompts:
            matches = find_matches(prompt, all_items)

            for item, triggers in matches:
                was_used = False
                if item.type == "skill" and item.name in session.skills_used:
                    was_used = True
                elif item.type == "agent" and item.name in session.agents_used:
                    was_used = True
                elif item.type == "command":
                    # Commands are slash commands - check if /command was in the prompt
                    was_used = f"/{item.name}" in prompt.lower()

                if not was_used:
                    missed.append(MissedOpportunity(
                        prompt=prompt,
                        session_id=session.session_id,
                        matched_item=item,
                        matched_triggers=triggers,
                    ))

                    if item.type == "skill":
                        stats["missed_skills"][item.name] += 1
                    elif item.type == "agent":
                        stats["missed_agents"][item.name] += 1
                    else:
                        stats["missed_commands"][item.name] += 1

    return missed, stats


def generate_analysis_json(
    skills: list[SkillOrAgent],
    agents: list[SkillOrAgent],
    commands: list[SkillOrAgent],
    hooks: list[Hook],
    sessions: list[SessionData],
    jsonl_stats: dict,
    claude_md: dict,
    setup_profile: SetupProfile,
) -> dict:
    """Generate rich JSON output for agent interpretation."""

    # Compute outcome stats
    total_outcomes = jsonl_stats["total_success"] + jsonl_stats["total_failure"] + jsonl_stats["total_interrupted"]
    success_rate = (jsonl_stats["total_success"] / total_outcomes * 100) if total_outcomes > 0 else 0

    # Compute avg tools per compaction
    total_tools = sum(len(s.tools_used) + len(s.skills_used) + len(s.agents_used) for s in sessions)
    avg_tools_per_compaction = (total_tools / jsonl_stats["total_compactions"]) if jsonl_stats["total_compactions"] > 0 else 0

    return {
        "_schema": {
            "description": "Claude Code usage analysis data for agent interpretation",
            "version": "3.1",
            "sections": {
                "discovery": "All available skills, agents, commands, and hooks discovered from global, project, and plugin sources",
                "sessions": "Parsed session data showing what was actually used",
                "stats": "Aggregated statistics on usage, outcomes, interruptions with followup context, and missed opportunities",
                "claude_md": "Content and structure of CLAUDE.md configuration files",
                "setup_profile": "Computed setup profile with complexity, shape, red flags, and coverage gaps",
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
            "hooks": [
                {
                    "event_type": h.event_type,
                    "matcher": h.matcher,
                    "command": h.command[:100],
                    "source": h.source_type,
                }
                for h in hooks
            ],
            "totals": {
                "skills": len(skills),
                "agents": len(agents),
                "commands": len(commands),
                "hooks": len(hooks),
            },
        },

        "sessions": {
            "count": len(sessions),
            "prompts": [
                {
                    "session_id": s.session_id,
                    "text": p[:500],
                }
                for s in sessions
                for p in s.prompts[:5]
            ][:50],
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
            "outcomes": {
                "success": jsonl_stats["total_success"],
                "failure": jsonl_stats["total_failure"],
                "interrupted": jsonl_stats["total_interrupted"],
                "success_rate": round(success_rate, 1),
            },
            "compactions": {
                "total": jsonl_stats["total_compactions"],
                "avg_tools_per": round(avg_tools_per_compaction, 1),
            },
            "interruptions": [
                {
                    "tool": it.tool_name,
                    "context": _summarize_tool_input(it.tool_name, it.tool_input),
                    "followup": it.followup_message,
                }
                for s in sessions
                for it in s.interrupted_tools
            ][:20],  # Limit to 20 most recent
        },

        "claude_md": claude_md,

        "setup_profile": {
            "complexity": setup_profile.complexity,
            "total_components": setup_profile.total_components,
            "shape": setup_profile.shape,
            "by_source": setup_profile.by_source,
            "red_flags": setup_profile.red_flags,
            "coverage": setup_profile.coverage,
            "coverage_gaps": setup_profile.coverage_gaps,
            "overlapping_triggers": setup_profile.overlapping_triggers,
            "plugin_usage": setup_profile.plugin_usage,
        },
    }


# =============================================================================
# Output Formatters
# =============================================================================

def progress_bar(value: float, max_value: float, width: int = 10) -> str:
    """Create ASCII progress bar."""
    if max_value == 0:
        return "░" * width
    filled = int((value / max_value) * width)
    return "█" * filled + "░" * (width - filled)


def print_table(
    jsonl_stats: dict,
    missed: list[MissedOpportunity],
    verbose: bool,
):
    """Print collected data as formatted table."""
    print("\n" + "=" * 80)
    print("USAGE DATA COLLECTED")
    print("=" * 80)

    print(f"\nSessions analyzed: {jsonl_stats['total_sessions']}")
    print(f"Prompts analyzed: {jsonl_stats['total_prompts']}")
    print(f"Potential matches found: {len(missed)}")

    # Outcome stats
    total = jsonl_stats["total_success"] + jsonl_stats["total_failure"] + jsonl_stats["total_interrupted"]
    if total > 0:
        success_rate = jsonl_stats["total_success"] / total * 100
        print(f"\nOutcomes: ✓{jsonl_stats['total_success']} ✗{jsonl_stats['total_failure']} ⏹{jsonl_stats['total_interrupted']} ({success_rate:.1f}% success)")
        print(f"Compactions: {jsonl_stats['total_compactions']}")

    # JSONL usage stats
    if jsonl_stats["skills_used"]:
        print("\n--- Skills Used ---")
        for skill, count in sorted(jsonl_stats["skills_used"].items(), key=lambda x: -x[1]):
            print(f"  {skill}: {count}")

    if jsonl_stats["agents_used"]:
        print("\n--- Agents Used ---")
        for agent, count in sorted(jsonl_stats["agents_used"].items(), key=lambda x: -x[1]):
            print(f"  {agent}: {count}")

    # Potential matches (detailed)
    if missed and verbose:
        print("\n--- Potential Matches (detailed) ---")
        by_item = defaultdict(list)
        for m in missed:
            by_item[f"{m.matched_item.type}:{m.matched_item.name}"].append(m)

        for key, items in sorted(by_item.items(), key=lambda x: -len(x[1]))[:10]:
            item_type, item_name = key.split(":", 1)
            print(f"\n  [{item_type.upper()}] {item_name} ({len(items)} matches)")
            for m in items[:3]:
                prompt_preview = m.prompt[:80].replace("\n", " ")
                print(f"    Session {m.session_id}: \"{prompt_preview}...\"")

    print("\n" + "=" * 80)
    print("Use usage-insights-agent to analyze this data for actionable insights.")
    print("=" * 80)


def print_dashboard(jsonl_stats: dict):
    """Print dashboard-style output with ASCII charts."""
    print("\n┌" + "─" * 78 + "┐")
    print("│" + " USAGE DATA DASHBOARD ".center(78) + "│")
    print("└" + "─" * 78 + "┘")

    # Outcome stats
    total = jsonl_stats["total_success"] + jsonl_stats["total_failure"] + jsonl_stats["total_interrupted"]
    if total > 0:
        success_rate = jsonl_stats["total_success"] / total * 100
        print("\n┌─ Outcomes " + "─" * 65 + "┐")
        print(f"│ Success:     {progress_bar(jsonl_stats['total_success'], total, 20)} {jsonl_stats['total_success']:4} ({success_rate:.1f}%)          │")
        print(f"│ Failure:     {progress_bar(jsonl_stats['total_failure'], total, 20)} {jsonl_stats['total_failure']:4}                      │")
        print(f"│ Interrupted: {progress_bar(jsonl_stats['total_interrupted'], total, 20)} {jsonl_stats['total_interrupted']:4}                      │")
        print(f"│ Compactions: {jsonl_stats['total_compactions']:4}                                                    │")
        print("└" + "─" * 76 + "┘")

    # Summary
    print("\n┌─ Summary " + "─" * 66 + "┐")
    print(f"│ Sessions: {jsonl_stats['total_sessions']:4} | Prompts: {jsonl_stats['total_prompts']:5} | Skills used: {len(jsonl_stats['skills_used']):3} | Agents used: {len(jsonl_stats['agents_used']):3}    │")
    print("└" + "─" * 76 + "┘")
    print("\nUse usage-insights-agent to analyze this data for actionable insights.")
    print()


# =============================================================================
# Quick Stats (uses session summaries)
# =============================================================================

def analyze_session_summaries(summary_dir: Path, days: int = 14) -> dict:
    """Analyze session summaries for quick stats."""
    cutoff = datetime.now() - timedelta(days=days)
    stats = {
        "sessions": 0,
        "total_tools": 0,
        "total_success": 0,
        "total_failure": 0,
        "total_compactions": 0,
        "tool_breakdown": defaultdict(int),
        "stages_seen": defaultdict(int),
        "by_project": defaultdict(lambda: {"sessions": 0, "success": 0, "failure": 0}),
    }

    if not summary_dir.exists():
        return stats

    for summary_file in summary_dir.glob("*.json"):
        try:
            date_str = summary_file.name[:10]
            file_date = datetime.strptime(date_str, "%Y-%m-%d")

            if file_date < cutoff:
                continue

            summary = json.loads(summary_file.read_text())
            stats["sessions"] += 1
            stats["total_tools"] += summary.get("total_tools", 0)
            stats["total_success"] += summary.get("outcomes", {}).get("success", 0)
            stats["total_failure"] += summary.get("outcomes", {}).get("failure", 0)
            stats["total_compactions"] += summary.get("compactions", 0)

            for tool, count in summary.get("tool_breakdown", {}).items():
                stats["tool_breakdown"][tool] += count

            for stage in summary.get("stages_visited", []):
                stats["stages_seen"][stage] += 1

            project = summary.get("project", "unknown")
            stats["by_project"][project]["sessions"] += 1
            stats["by_project"][project]["success"] += summary.get("outcomes", {}).get("success", 0)
            stats["by_project"][project]["failure"] += summary.get("outcomes", {}).get("failure", 0)

        except (json.JSONDecodeError, ValueError):
            continue

    return stats


def print_quick_stats(stats: dict, days: int):
    """Print quick stats from session summaries."""
    print("\n" + "=" * 80)
    print(f"QUICK STATS (Last {days} days)")
    print("=" * 80)

    if stats["sessions"] == 0:
        print("\nNo session summaries found. Run some sessions first!")
        print("(Summaries are saved when sessions end)")
        return

    total = stats["total_success"] + stats["total_failure"]
    success_rate = (stats["total_success"] / total * 100) if total > 0 else 0

    print(f"\nSessions: {stats['sessions']}")
    print(f"Total tools: {stats['total_tools']}")
    print(f"Success rate: {success_rate:.1f}% ({stats['total_success']}/{total})")
    print(f"Compactions: {stats['total_compactions']}")

    if stats["tool_breakdown"]:
        print("\n--- Tool Usage ---")
        for tool, count in sorted(stats["tool_breakdown"].items(), key=lambda x: -x[1])[:10]:
            print(f"  {tool}: {count}")

    if stats["stages_seen"]:
        print("\n--- Workflow Stages ---")
        for stage, count in sorted(stats["stages_seen"].items(), key=lambda x: -x[1]):
            print(f"  {stage}: {count} sessions")

    if stats["by_project"]:
        print("\n--- By Project ---")
        for project, data in sorted(stats["by_project"].items(), key=lambda x: -x[1]["sessions"])[:5]:
            total_p = data["success"] + data["failure"]
            rate = (data["success"] / total_p * 100) if total_p > 0 else 0
            print(f"  {project}: {data['sessions']} sessions, {rate:.0f}% success")

    print("\n" + "=" * 80)


# =============================================================================
# Main
# =============================================================================

def main():
    parser = argparse.ArgumentParser(description="Collect Claude Code usage data for analysis")
    parser.add_argument("--sessions", type=int, default=10, help="Sessions to analyze")
    parser.add_argument("--format", choices=["table", "dashboard", "json"], default="table")
    parser.add_argument("--verbose", action="store_true", help="Show examples")
    parser.add_argument("--project", help="Project path (default: current directory)")
    parser.add_argument("--quick-stats", action="store_true", help="Show quick stats from session summaries")
    parser.add_argument("--days", type=int, default=14, help="Days to include in quick stats (default: 14)")
    args = parser.parse_args()

    home = Path.home()
    cwd = Path.cwd()

    # Quick stats mode
    if args.quick_stats:
        summary_dir = home / ".claude" / "session-summaries"
        stats = analyze_session_summaries(summary_dir, args.days)
        print_quick_stats(stats, args.days)
        return

    project_path = args.project or str(cwd)
    projects_dir = home / ".claude" / "projects"

    # Resolve project path early to get actual source directory
    if args.project and not Path(args.project).is_absolute():
        resolved_dir, matches = resolve_project_path(projects_dir, project_path)
        if resolved_dir:
            target_project_dir = Path("/" + resolved_dir.name.replace("-", "/"))
            if not target_project_dir.exists():
                target_project_dir = home / "Projects" / project_path
        else:
            target_project_dir = cwd
    else:
        target_project_dir = Path(project_path) if project_path != str(cwd) else cwd

    print("\n[1/4] Discovering skills, agents, commands, hooks...", file=sys.stderr)
    skill_paths = [home / ".claude" / "skills", target_project_dir / ".claude" / "skills"]
    agent_paths = [home / ".claude" / "agents", target_project_dir / ".claude" / "agents"]
    command_paths = [home / ".claude" / "commands", target_project_dir / ".claude" / "commands"]
    plugins_cache = home / ".claude" / "plugins" / "cache"

    skills = discover_skills(skill_paths)
    agents = discover_agents(agent_paths)
    commands = discover_commands(command_paths)

    plugin_skills, plugin_agents, plugin_commands = discover_from_plugins(plugins_cache)
    skills.extend(plugin_skills)
    agents.extend(plugin_agents)
    commands.extend(plugin_commands)

    settings_paths = [
        (home / ".claude" / "settings.json", "global"),
        (target_project_dir / ".claude" / "settings.json", "project"),
        (target_project_dir / ".claude" / "settings.local.json", "project-local"),
    ]
    hooks = discover_hooks(settings_paths, plugins_cache)

    print(f"  ✓ Found {len(skills)} skills, {len(agents)} agents, {len(commands)} commands, {len(hooks)} hooks", file=sys.stderr)

    print("\n[2/4] Parsing CLAUDE.md files...", file=sys.stderr)
    claude_md_paths = [
        home / ".claude" / "CLAUDE.md",
        target_project_dir / "CLAUDE.md",
        target_project_dir / ".claude" / "instructions.md",
    ]
    claude_md = parse_claude_md_files(claude_md_paths)
    if claude_md["files_found"]:
        print(f"  ✓ Found {len(claude_md['files_found'])} config file(s)", file=sys.stderr)
    else:
        print("  ⊘ No CLAUDE.md files found", file=sys.stderr)

    setup_profile = compute_setup_profile(skills, agents, commands, hooks, claude_md)
    print(f"  ✓ Setup: {setup_profile.complexity} complexity, {len(setup_profile.red_flags)} red flags", file=sys.stderr)

    print("\n[3/4] Parsing session files...", file=sys.stderr)

    if args.project and not Path(args.project).is_absolute():
        resolved_dir, matches = resolve_project_path(projects_dir, project_path)
    else:
        resolved_dir, matches = resolve_project_path(projects_dir, project_path)

    if resolved_dir:
        if resolved_dir.name != project_path.replace("/", "-"):
            print(f"  → Matched: {resolved_dir.name}", file=sys.stderr)
        session_files = find_project_sessions(projects_dir, resolved_dir, args.sessions)
    elif len(matches) > 1:
        print(f"  ✗ Multiple projects match '{project_path}':", file=sys.stderr)
        for m in matches[:5]:
            print(f"    - {m.name}", file=sys.stderr)
        if len(matches) > 5:
            print(f"    ... and {len(matches) - 5} more", file=sys.stderr)
        print("  Use full path or more specific name", file=sys.stderr)
        session_files = []
    else:
        print(f"  ✗ No project found matching '{project_path}'", file=sys.stderr)
        if projects_dir.exists():
            available = sorted([d.name for d in projects_dir.iterdir() if d.is_dir()])[:5]
            if available:
                print("  Available projects:", file=sys.stderr)
                for p in available:
                    print(f"    - {p}", file=sys.stderr)
        session_files = []

    if session_files:
        sessions = [parse_session_file(f) for f in session_files]
        total_prompts = sum(len(s.prompts) for s in sessions)
        print(f"  ✓ Parsed {len(sessions)} sessions ({total_prompts} prompts)", file=sys.stderr)
    else:
        sessions = []
        if resolved_dir:
            print(f"  ✗ No sessions found in {resolved_dir.name}", file=sys.stderr)

    print("\n[4/4] Finding potential matches...", file=sys.stderr)
    missed, jsonl_stats = analyze_jsonl(skills, agents, commands, sessions)
    print(f"  ✓ Found {len(missed)} potential matches", file=sys.stderr)

    # Read plugin enabled states from settings
    enabled_states = read_plugin_enabled_states(
        home / ".claude" / "settings.json",
        target_project_dir / ".claude" / "settings.json",
    )

    # Compute plugin usage
    setup_profile.plugin_usage = compute_plugin_usage(skills, agents, sessions, missed, enabled_states)
    active_count = len(setup_profile.plugin_usage["active"])
    unused_count = len(setup_profile.plugin_usage["unused"])
    disabled_matched_count = len(setup_profile.plugin_usage.get("disabled_but_matched", []))
    already_disabled_count = len(setup_profile.plugin_usage.get("already_disabled", []))

    if unused_count > 0:
        print(f"  → {unused_count} enabled but unused, {active_count} active", file=sys.stderr)
    if disabled_matched_count > 0:
        print(f"  → {disabled_matched_count} disabled but potentially useful", file=sys.stderr)
    if already_disabled_count > 0:
        print(f"  → {already_disabled_count} already disabled (no action needed)", file=sys.stderr)
    print("", file=sys.stderr)

    # Output
    if args.format == "json":
        output = generate_analysis_json(
            skills, agents, commands, hooks, sessions, jsonl_stats, claude_md, setup_profile
        )
        print(json.dumps(output, indent=2))
    elif args.format == "dashboard":
        print_dashboard(jsonl_stats)
    else:
        print_table(jsonl_stats, missed, args.verbose)


if __name__ == "__main__":
    main()
