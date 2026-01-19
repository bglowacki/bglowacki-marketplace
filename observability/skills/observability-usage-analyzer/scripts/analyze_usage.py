#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.10"
# dependencies = ["pyyaml"]
# ///
"""
Usage Analyzer - Identify missed skill/agent opportunities in Claude Code sessions.

Dynamically discovers available skills and agents, extracts trigger patterns,
and analyzes session history to find missed opportunities.
"""

import argparse
import json
import re
import sys
from collections import defaultdict
from dataclasses import dataclass, field
from pathlib import Path


@dataclass
class SkillOrAgent:
    name: str
    type: str  # "skill" or "agent"
    description: str
    triggers: list[str]
    source_path: str


@dataclass
class SessionData:
    session_id: str
    prompts: list[str] = field(default_factory=list)
    skills_used: set[str] = field(default_factory=set)
    agents_used: set[str] = field(default_factory=set)
    tools_used: set[str] = field(default_factory=set)


@dataclass
class MissedOpportunity:
    prompt: str
    session_id: str
    matched_item: SkillOrAgent
    matched_triggers: list[str]


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

    # Look for explicit trigger patterns
    trigger_patterns = [
        r'[Tt]riggers?\s+on\s+["\']([^"\']+)["\']',
        r'[Tt]riggers?\s+on\s+([^,.]+(?:,\s*[^,.]+)*)',
        r'[Uu]se\s+(?:this\s+)?(?:skill|agent)\s+when\s+([^.]+)',
        r'[Uu]se\s+for\s+([^.]+)',
    ]

    for pattern in trigger_patterns:
        matches = re.findall(pattern, description)
        for match in matches:
            # Split on commas and "or"
            parts = re.split(r',\s*|\s+or\s+', match)
            triggers.extend([p.strip().strip('"\'') for p in parts if p.strip()])

    # Also extract quoted phrases
    quoted = re.findall(r'["\']([^"\']+)["\']', description)
    triggers.extend(quoted)

    return list(set(triggers))


def discover_skills(paths: list[Path]) -> list[SkillOrAgent]:
    """Discover skills from given paths."""
    skills = []

    for base_path in paths:
        if not base_path.exists():
            continue

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
                triggers.append(name)

                skills.append(SkillOrAgent(
                    name=name,
                    type="skill",
                    description=description,
                    triggers=triggers,
                    source_path=str(skill_md),
                ))
            except Exception as e:
                print(f"Warning: Could not parse {skill_md}: {e}", file=sys.stderr)

    return skills


def discover_agents(paths: list[Path]) -> list[SkillOrAgent]:
    """Discover agents from given paths."""
    agents = []

    for base_path in paths:
        if not base_path.exists():
            continue

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
                triggers.append(name)

                agents.append(SkillOrAgent(
                    name=name,
                    type="agent",
                    description=description[:200],
                    triggers=triggers,
                    source_path=str(agent_file),
                ))
            except Exception as e:
                print(f"Warning: Could not parse {agent_file}: {e}", file=sys.stderr)

    return agents


def _is_system_prompt(content: str) -> bool:
    """Filter out system-generated prompts that shouldn't be analyzed."""
    # Skill loading messages
    if content.startswith("Base directory for this skill:"):
        return True
    # Subagent trace IDs
    if content.startswith("[TRACE-ID:"):
        return True
    # Command messages (skill invocations)
    if "<command-message>" in content or "<command-name>" in content:
        return True
    return False


def find_project_sessions(projects_dir: Path, project_path: str, max_sessions: int) -> list[Path]:
    """Find session files for a project."""
    # Convert project path to folder name format (e.g., /Users/foo/bar -> -Users-foo-bar)
    project_folder = project_path.replace("/", "-")

    project_dir = projects_dir / project_folder
    if not project_dir.exists():
        return []

    # Get most recent session files
    session_files = sorted(
        project_dir.glob("*.jsonl"),
        key=lambda p: p.stat().st_mtime,
        reverse=True
    )

    return session_files[:max_sessions]


def parse_session_file(session_path: Path) -> SessionData:
    """Parse a session JSONL file."""
    session_data = SessionData(session_id=session_path.stem[:8])

    try:
        lines = session_path.read_text().strip().split("\n")

        for line in lines:
            try:
                entry = json.loads(line)
                entry_type = entry.get("type")

                if entry_type == "user":
                    message = entry.get("message", {})
                    content = message.get("content", "")

                    # Extract actual text prompts (not tool results)
                    if isinstance(content, str) and content.strip():
                        # Filter out system-generated messages
                        if not _is_system_prompt(content):
                            session_data.prompts.append(content)
                    elif isinstance(content, list):
                        for item in content:
                            if isinstance(item, dict) and item.get("type") == "text":
                                text = item.get("text", "")
                                if not _is_system_prompt(text):
                                    session_data.prompts.append(text)

                elif entry_type == "assistant":
                    message = entry.get("message", {})
                    content = message.get("content", [])

                    if isinstance(content, list):
                        for item in content:
                            if isinstance(item, dict) and item.get("type") == "tool_use":
                                tool_name = item.get("name", "")
                                tool_input = item.get("input", {})

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

    except Exception as e:
        print(f"Warning: Could not parse {session_path}: {e}", file=sys.stderr)

    return session_data


def find_matches(prompt: str, items: list[SkillOrAgent], min_triggers: int = 2) -> list[tuple[SkillOrAgent, list[str]]]:
    """Find skills/agents that match a prompt based on triggers.

    Args:
        prompt: User prompt to match against
        items: Skills/agents to check
        min_triggers: Minimum number of triggers that must match (reduces false positives)
    """
    matches = []
    prompt_lower = prompt.lower()

    for item in items:
        matched_triggers = []
        for trigger in item.triggers:
            trigger_lower = trigger.lower()
            if len(trigger_lower) > 3:  # Skip very short triggers
                if re.search(r'\b' + re.escape(trigger_lower) + r'\b', prompt_lower):
                    matched_triggers.append(trigger)

        # Require multiple trigger matches to reduce false positives
        # Exception: if the item name itself matched, that's a strong signal
        name_matched = item.name.lower() in [t.lower() for t in matched_triggers]
        if len(matched_triggers) >= min_triggers or name_matched:
            matches.append((item, matched_triggers))

    return matches


def analyze(
    skills: list[SkillOrAgent],
    agents: list[SkillOrAgent],
    sessions: list[SessionData],
) -> tuple[list[MissedOpportunity], dict]:
    """Analyze sessions for missed opportunities."""
    missed = []
    stats = {
        "total_sessions": len(sessions),
        "total_prompts": sum(len(s.prompts) for s in sessions),
        "skills_used": defaultdict(int),
        "agents_used": defaultdict(int),
        "missed_skills": defaultdict(int),
        "missed_agents": defaultdict(int),
    }

    all_items = skills + agents

    for session in sessions:
        # Track actual usage
        for skill in session.skills_used:
            stats["skills_used"][skill] += 1
        for agent in session.agents_used:
            stats["agents_used"][agent] += 1

        # Check each prompt for potential matches
        for prompt in session.prompts:
            matches = find_matches(prompt, all_items)

            for item, triggers in matches:
                was_used = False
                if item.type == "skill" and item.name in session.skills_used:
                    was_used = True
                elif item.type == "agent" and item.name in session.agents_used:
                    was_used = True

                if not was_used:
                    missed.append(MissedOpportunity(
                        prompt=prompt,
                        session_id=session.session_id,
                        matched_item=item,
                        matched_triggers=triggers,
                    ))

                    if item.type == "skill":
                        stats["missed_skills"][item.name] += 1
                    else:
                        stats["missed_agents"][item.name] += 1

    return missed, stats


def print_table(missed: list[MissedOpportunity], stats: dict, verbose: bool):
    """Print analysis results as formatted table."""
    print("\n" + "=" * 80)
    print("USAGE ANALYSIS REPORT")
    print("=" * 80)

    print(f"\nSessions analyzed: {stats['total_sessions']}")
    print(f"Prompts analyzed: {stats['total_prompts']}")
    print(f"Missed opportunities: {len(missed)}")

    if stats["skills_used"]:
        print("\n--- Skills Used ---")
        for skill, count in sorted(stats["skills_used"].items(), key=lambda x: -x[1]):
            print(f"  {skill}: {count}")

    if stats["agents_used"]:
        print("\n--- Agents Used ---")
        for agent, count in sorted(stats["agents_used"].items(), key=lambda x: -x[1]):
            print(f"  {agent}: {count}")

    if missed:
        print("\n--- Missed Opportunities ---")

        by_item = defaultdict(list)
        for m in missed:
            by_item[f"{m.matched_item.type}:{m.matched_item.name}"].append(m)

        for key, items in sorted(by_item.items(), key=lambda x: -len(x[1]))[:10]:
            item_type, item_name = key.split(":", 1)
            print(f"\n  [{item_type.upper()}] {item_name} (missed {len(items)} times)")

            if verbose:
                for m in items[:3]:
                    prompt_preview = m.prompt[:80].replace("\n", " ")
                    print(f"    Session {m.session_id}: \"{prompt_preview}...\"")
                    print(f"      Triggers: {', '.join(m.matched_triggers[:3])}")

    print("\n--- Recommendations ---")

    if stats["missed_skills"]:
        top_missed = sorted(stats["missed_skills"].items(), key=lambda x: -x[1])[:5]
        print("\n  Consider using these skills more:")
        for skill, count in top_missed:
            print(f"    - {skill} ({count} opportunities)")

    if stats["missed_agents"]:
        top_missed = sorted(stats["missed_agents"].items(), key=lambda x: -x[1])[:5]
        print("\n  Consider using these agents more:")
        for agent, count in top_missed:
            print(f"    - {agent} ({count} opportunities)")

    print("\n" + "=" * 80)


def analyze_session_summaries(summary_dir: Path, days: int = 14) -> dict:
    """Analyze session summaries for quick stats."""
    from datetime import datetime, timedelta

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
            # Parse date from filename (YYYY-MM-DD_sessionid.json)
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


def print_json(missed: list[MissedOpportunity], stats: dict):
    """Print analysis results as JSON."""
    output = {
        "summary": {
            "sessions": stats["total_sessions"],
            "prompts": stats["total_prompts"],
            "missed_opportunities": len(missed),
        },
        "usage": {
            "skills": dict(stats["skills_used"]),
            "agents": dict(stats["agents_used"]),
        },
        "missed": {
            "skills": dict(stats["missed_skills"]),
            "agents": dict(stats["missed_agents"]),
        },
        "opportunities": [
            {
                "session": m.session_id,
                "prompt": m.prompt[:200],
                "suggested": m.matched_item.name,
                "type": m.matched_item.type,
                "triggers": m.matched_triggers,
            }
            for m in missed[:50]
        ],
    }
    print(json.dumps(output, indent=2))


def main():
    parser = argparse.ArgumentParser(description="Analyze Claude Code usage patterns")
    parser.add_argument("--sessions", type=int, default=10, help="Sessions to analyze")
    parser.add_argument("--format", choices=["table", "json"], default="table")
    parser.add_argument("--verbose", action="store_true", help="Show examples")
    parser.add_argument("--project", help="Project path (default: current directory)")
    parser.add_argument("--quick-stats", action="store_true", help="Show quick stats from session summaries")
    parser.add_argument("--days", type=int, default=14, help="Days to include in quick stats (default: 14)")
    args = parser.parse_args()

    home = Path.home()
    cwd = Path.cwd()

    # Quick stats mode - uses session summaries
    if args.quick_stats:
        summary_dir = home / ".claude" / "session-summaries"
        stats = analyze_session_summaries(summary_dir, args.days)
        print_quick_stats(stats, args.days)
        return

    project_path = args.project or str(cwd)

    # Discover skills and agents
    skill_paths = [home / ".claude" / "skills", cwd / ".claude" / "skills"]
    agent_paths = [home / ".claude" / "agents", cwd / ".claude" / "agents"]

    print("Discovering skills and agents...", file=sys.stderr)
    skills = discover_skills(skill_paths)
    agents = discover_agents(agent_paths)
    print(f"Found {len(skills)} skills, {len(agents)} agents", file=sys.stderr)

    # Find and parse sessions
    projects_dir = home / ".claude" / "projects"
    session_files = find_project_sessions(projects_dir, project_path, args.sessions)

    print(f"Parsing {len(session_files)} sessions...", file=sys.stderr)
    sessions = [parse_session_file(f) for f in session_files]

    # Analyze
    missed, stats = analyze(skills, agents, sessions)

    # Output
    if args.format == "json":
        print_json(missed, stats)
    else:
        print_table(missed, stats, args.verbose)


if __name__ == "__main__":
    main()
