#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.10"
# dependencies = ["pyyaml", "requests"]
# ///
"""
Usage Analyzer - Identify missed skill/agent opportunities in Claude Code sessions.

Combines two data sources:
1. Prometheus metrics - aggregates, trends, success rates
2. JSONL session files - detailed context, exact prompts

Produces enriched insights with both trend data and specific examples.
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

import requests


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


@dataclass
class PrometheusData:
    skill_usage: dict[str, float] = field(default_factory=dict)
    agent_usage: dict[str, float] = field(default_factory=dict)
    skill_trends: dict[str, float] = field(default_factory=dict)  # % change
    agent_trends: dict[str, float] = field(default_factory=dict)
    overall_success_rate: float = 0.0
    skill_success_rates: dict[str, float] = field(default_factory=dict)
    workflow_stages: dict[str, int] = field(default_factory=dict)
    available: bool = False
    error: Optional[str] = None


# =============================================================================
# Prometheus Fetcher
# =============================================================================

def get_prometheus_endpoint() -> Optional[str]:
    """Get Prometheus endpoint from global config."""
    global_config = Path.home() / ".claude" / "observability" / "endpoint.env"
    if global_config.exists():
        for line in global_config.read_text().splitlines():
            if line.startswith("PROMETHEUS_ENDPOINT="):
                return line.split("=", 1)[1].strip()
    return None


def query_prometheus(endpoint: str, query: str, timeout: int = 5) -> Optional[dict]:
    """Execute a PromQL query."""
    try:
        response = requests.get(
            f"{endpoint}/api/v1/query",
            params={"query": query},
            timeout=timeout
        )
        if response.status_code == 200:
            return response.json()
    except requests.RequestException:
        pass
    return None


def fetch_prometheus_data(endpoint: str, time_range: str = "7d") -> PrometheusData:
    """Fetch all relevant metrics from Prometheus."""
    data = PrometheusData()

    # Test connection
    test = query_prometheus(endpoint, "up", timeout=3)
    if test is None:
        data.error = f"Cannot connect to Prometheus at {endpoint}"
        return data

    data.available = True

    # Skill usage (current period)
    result = query_prometheus(
        endpoint,
        f'sum by (skill_name) (increase(claude_code_skill_invocations[{time_range}]))'
    )
    if result and result.get("data", {}).get("result"):
        for item in result["data"]["result"]:
            skill = item["metric"].get("skill_name", "unknown")
            value = float(item["value"][1])
            if value > 0:
                data.skill_usage[skill] = value

    # Agent usage (current period)
    result = query_prometheus(
        endpoint,
        f'sum by (agent_type) (increase(claude_code_agent_invocations[{time_range}]))'
    )
    if result and result.get("data", {}).get("result"):
        for item in result["data"]["result"]:
            agent = item["metric"].get("agent_type", "unknown")
            value = float(item["value"][1])
            if value > 0:
                data.agent_usage[agent] = value

    # Skill trends (compare with previous period)
    result = query_prometheus(
        endpoint,
        f'sum by (skill_name) (increase(claude_code_skill_invocations[{time_range}] offset {time_range}))'
    )
    if result and result.get("data", {}).get("result"):
        prev_usage = {}
        for item in result["data"]["result"]:
            skill = item["metric"].get("skill_name", "unknown")
            prev_usage[skill] = float(item["value"][1])

        for skill, current in data.skill_usage.items():
            prev = prev_usage.get(skill, 0)
            if prev > 0:
                data.skill_trends[skill] = ((current - prev) / prev) * 100
            elif current > 0:
                data.skill_trends[skill] = 100.0  # New usage

    # Agent trends
    result = query_prometheus(
        endpoint,
        f'sum by (agent_type) (increase(claude_code_agent_invocations[{time_range}] offset {time_range}))'
    )
    if result and result.get("data", {}).get("result"):
        prev_usage = {}
        for item in result["data"]["result"]:
            agent = item["metric"].get("agent_type", "unknown")
            prev_usage[agent] = float(item["value"][1])

        for agent, current in data.agent_usage.items():
            prev = prev_usage.get(agent, 0)
            if prev > 0:
                data.agent_trends[agent] = ((current - prev) / prev) * 100
            elif current > 0:
                data.agent_trends[agent] = 100.0

    # Overall success rate
    result = query_prometheus(
        endpoint,
        f'sum(increase(claude_code_outcome_success[{time_range}])) / '
        f'(sum(increase(claude_code_outcome_success[{time_range}])) + '
        f'sum(increase(claude_code_outcome_failure[{time_range}])))'
    )
    if result and result.get("data", {}).get("result"):
        value = result["data"]["result"][0]["value"][1]
        if value != "NaN":
            data.overall_success_rate = float(value) * 100

    # Workflow stages
    result = query_prometheus(
        endpoint,
        f'sum by (to_stage) (increase(claude_code_workflow_stage_transition[{time_range}]))'
    )
    if result and result.get("data", {}).get("result"):
        for item in result["data"]["result"]:
            stage = item["metric"].get("to_stage", "unknown")
            value = int(float(item["value"][1]))
            if value > 0:
                data.workflow_stages[stage] = value

    return data


# =============================================================================
# JSONL Parser (existing, slightly modified)
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
    """Filter out system-generated prompts."""
    if content.startswith("Base directory for this skill:"):
        return True
    if content.startswith("[TRACE-ID:"):
        return True
    if "<command-message>" in content or "<command-name>" in content:
        return True
    return False


def find_project_sessions(projects_dir: Path, project_path: str, max_sessions: int) -> list[Path]:
    """Find session files for a project."""
    project_folder = project_path.replace("/", "-")
    project_dir = projects_dir / project_folder

    if not project_dir.exists():
        return []

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

                    if isinstance(content, str) and content.strip():
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


# =============================================================================
# Correlation Engine
# =============================================================================

@dataclass
class Insight:
    type: str  # declining_usage, low_success, workflow_gap, missed_opportunity
    severity: str  # high, medium, low
    item_name: str
    item_type: str  # skill, agent
    message: str
    details: dict = field(default_factory=dict)


def correlate_data(
    prom_data: PrometheusData,
    jsonl_stats: dict,
    missed: list[MissedOpportunity],
) -> list[Insight]:
    """Generate insights by correlating Prometheus and JSONL data."""
    insights = []

    if prom_data.available:
        # Declining usage with missed opportunities
        for skill, trend in prom_data.skill_trends.items():
            if trend < -20:  # Declining more than 20%
                missed_count = jsonl_stats["missed_skills"].get(skill, 0)
                if missed_count > 0:
                    insights.append(Insight(
                        type="declining_with_missed",
                        severity="high",
                        item_name=skill,
                        item_type="skill",
                        message=f"{skill} usage down {abs(trend):.0f}% but {missed_count} prompts matched triggers",
                        details={
                            "trend": trend,
                            "missed_count": missed_count,
                            "current_usage": prom_data.skill_usage.get(skill, 0),
                        }
                    ))

        # Same for agents
        for agent, trend in prom_data.agent_trends.items():
            if trend < -20:
                missed_count = jsonl_stats["missed_agents"].get(agent, 0)
                if missed_count > 0:
                    insights.append(Insight(
                        type="declining_with_missed",
                        severity="high",
                        item_name=agent,
                        item_type="agent",
                        message=f"{agent} usage down {abs(trend):.0f}% but {missed_count} prompts matched triggers",
                        details={
                            "trend": trend,
                            "missed_count": missed_count,
                            "current_usage": prom_data.agent_usage.get(agent, 0),
                        }
                    ))

        # Workflow stage gaps
        expected_stages = ["brainstorm", "plan", "implement", "test", "review", "commit"]
        missing_stages = [s for s in expected_stages if s not in prom_data.workflow_stages]
        if missing_stages:
            insights.append(Insight(
                type="workflow_gap",
                severity="medium",
                item_name="workflow",
                item_type="process",
                message=f"Workflow stages rarely used: {', '.join(missing_stages)}",
                details={
                    "missing": missing_stages,
                    "present": list(prom_data.workflow_stages.keys()),
                }
            ))

    # Pure JSONL insights (missed opportunities)
    top_missed_skills = sorted(jsonl_stats["missed_skills"].items(), key=lambda x: -x[1])[:3]
    for skill, count in top_missed_skills:
        if count >= 2:
            examples = [m for m in missed if m.matched_item.name == skill][:2]
            insights.append(Insight(
                type="missed_opportunity",
                severity="medium" if count >= 3 else "low",
                item_name=skill,
                item_type="skill",
                message=f"{skill} could have been used {count} times",
                details={
                    "count": count,
                    "examples": [{"session": e.session_id, "prompt": e.prompt[:80]} for e in examples],
                }
            ))

    top_missed_agents = sorted(jsonl_stats["missed_agents"].items(), key=lambda x: -x[1])[:3]
    for agent, count in top_missed_agents:
        if count >= 2:
            examples = [m for m in missed if m.matched_item.name == agent][:2]
            insights.append(Insight(
                type="missed_opportunity",
                severity="medium" if count >= 3 else "low",
                item_name=agent,
                item_type="agent",
                message=f"{agent} could have been used {count} times",
                details={
                    "count": count,
                    "examples": [{"session": e.session_id, "prompt": e.prompt[:80]} for e in examples],
                }
            ))

    return sorted(insights, key=lambda x: {"high": 0, "medium": 1, "low": 2}[x.severity])


# =============================================================================
# Output Formatters
# =============================================================================

def trend_arrow(value: float) -> str:
    """Return trend arrow based on percentage change."""
    if value > 10:
        return "↑"
    elif value < -10:
        return "↓"
    return "↔"


def progress_bar(value: float, max_value: float, width: int = 10) -> str:
    """Create ASCII progress bar."""
    if max_value == 0:
        return "░" * width
    filled = int((value / max_value) * width)
    return "█" * filled + "░" * (width - filled)


def print_table(
    prom_data: PrometheusData,
    jsonl_stats: dict,
    insights: list[Insight],
    missed: list[MissedOpportunity],
    verbose: bool,
):
    """Print analysis results as formatted table."""
    print("\n" + "=" * 80)
    print("USAGE ANALYSIS REPORT")
    if prom_data.available:
        print("(with Prometheus metrics)")
    else:
        print("(JSONL only - Prometheus unavailable)")
    print("=" * 80)

    print(f"\nSessions analyzed: {jsonl_stats['total_sessions']}")
    print(f"Prompts analyzed: {jsonl_stats['total_prompts']}")
    print(f"Missed opportunities: {len(missed)}")

    if prom_data.available:
        print(f"Overall success rate: {prom_data.overall_success_rate:.1f}%")

    # Prometheus trends section
    if prom_data.available and (prom_data.skill_usage or prom_data.agent_usage):
        print("\n📊 TRENDS (vs previous period)")

        if prom_data.skill_usage:
            print("\n  Skills:")
            for skill, count in sorted(prom_data.skill_usage.items(), key=lambda x: -x[1])[:8]:
                trend = prom_data.skill_trends.get(skill, 0)
                arrow = trend_arrow(trend)
                trend_str = f"{trend:+.0f}%" if trend != 0 else ""
                print(f"    {skill:25} {count:4.0f} {arrow} {trend_str}")

        if prom_data.agent_usage:
            print("\n  Agents:")
            for agent, count in sorted(prom_data.agent_usage.items(), key=lambda x: -x[1])[:8]:
                trend = prom_data.agent_trends.get(agent, 0)
                arrow = trend_arrow(trend)
                trend_str = f"{trend:+.0f}%" if trend != 0 else ""
                print(f"    {agent:25} {count:4.0f} {arrow} {trend_str}")

        if prom_data.workflow_stages:
            print("\n📋 WORKFLOW STAGES")
            for stage, count in sorted(prom_data.workflow_stages.items(), key=lambda x: -x[1]):
                print(f"    {stage:15} {count:4}")

    # JSONL usage stats
    if jsonl_stats["skills_used"]:
        print("\n--- Skills Used (from JSONL) ---")
        for skill, count in sorted(jsonl_stats["skills_used"].items(), key=lambda x: -x[1]):
            print(f"  {skill}: {count}")

    if jsonl_stats["agents_used"]:
        print("\n--- Agents Used (from JSONL) ---")
        for agent, count in sorted(jsonl_stats["agents_used"].items(), key=lambda x: -x[1]):
            print(f"  {agent}: {count}")

    # Insights section
    if insights:
        print("\n💡 INSIGHTS")
        for insight in insights:
            severity_icon = {"high": "🔴", "medium": "🟡", "low": "🟢"}[insight.severity]
            print(f"\n  {severity_icon} [{insight.item_type.upper()}] {insight.message}")

            if verbose and insight.details.get("examples"):
                for ex in insight.details["examples"][:2]:
                    print(f"      Session {ex['session']}: \"{ex['prompt']}...\"")

    # Missed opportunities (detailed)
    if missed and verbose:
        print("\n--- Missed Opportunities (detailed) ---")
        by_item = defaultdict(list)
        for m in missed:
            by_item[f"{m.matched_item.type}:{m.matched_item.name}"].append(m)

        for key, items in sorted(by_item.items(), key=lambda x: -len(x[1]))[:10]:
            item_type, item_name = key.split(":", 1)
            print(f"\n  [{item_type.upper()}] {item_name} (missed {len(items)} times)")
            for m in items[:3]:
                prompt_preview = m.prompt[:80].replace("\n", " ")
                print(f"    Session {m.session_id}: \"{prompt_preview}...\"")

    # Recommendations
    print("\n--- Recommendations ---")
    if insights:
        for insight in insights[:5]:
            if insight.type == "declining_with_missed":
                print(f"  • Use {insight.item_name} more - usage declining but opportunities exist")
            elif insight.type == "workflow_gap":
                print(f"  • Add missing workflow stages: {', '.join(insight.details.get('missing', []))}")
            elif insight.type == "missed_opportunity":
                print(f"  • Consider using {insight.item_name} ({insight.item_type}) more often")
    elif not missed:
        print("  ✓ Great job! No significant missed opportunities detected.")

    print("\n" + "=" * 80)


def print_dashboard(
    prom_data: PrometheusData,
    jsonl_stats: dict,
    insights: list[Insight],
):
    """Print dashboard-style output with ASCII charts."""
    print("\n┌" + "─" * 78 + "┐")
    print("│" + " USAGE DASHBOARD ".center(78) + "│")
    print("└" + "─" * 78 + "┘")

    # Two-column layout
    if prom_data.available:
        # Skills column
        print("\n┌─ Skills " + "─" * 27 + "┐  ┌─ Success Rate " + "─" * 20 + "┐")

        max_skill = max(prom_data.skill_usage.values()) if prom_data.skill_usage else 1
        skill_lines = []
        for skill, count in sorted(prom_data.skill_usage.items(), key=lambda x: -x[1])[:5]:
            trend = prom_data.skill_trends.get(skill, 0)
            arrow = trend_arrow(trend)
            bar = progress_bar(count, max_skill, 8)
            skill_lines.append(f"│ {skill[:15]:15} {bar} {count:3.0f} {arrow} │")

        # Success rate column
        success_lines = [
            f"│ Overall:  {progress_bar(prom_data.overall_success_rate, 100, 10)} {prom_data.overall_success_rate:5.1f}% │",
        ]

        # Pad to same length
        while len(skill_lines) < 5:
            skill_lines.append("│" + " " * 36 + "│")
        while len(success_lines) < 5:
            success_lines.append("│" + " " * 36 + "│")

        for s, r in zip(skill_lines, success_lines):
            print(f"{s}  {r}")

        print("└" + "─" * 36 + "┘  └" + "─" * 36 + "┘")

        # Workflow stages
        if prom_data.workflow_stages:
            print("\n┌─ Workflow Stages " + "─" * 58 + "┐")
            stages = ["brainstorm", "plan", "implement", "test", "review", "commit"]
            stage_str = ""
            for stage in stages:
                count = prom_data.workflow_stages.get(stage, 0)
                if count > 0:
                    stage_str += f" {stage}({count}) →"
                else:
                    stage_str += f" [{stage}] →"
            print(f"│ {stage_str[:-2]:74} │")
            print("└" + "─" * 76 + "┘")
    else:
        print("\n⚠ Prometheus unavailable - showing JSONL data only")
        print(f"\n  Sessions: {jsonl_stats['total_sessions']} | Prompts: {jsonl_stats['total_prompts']}")

    # Insights summary
    if insights:
        print("\n┌─ Top Insights " + "─" * 61 + "┐")
        for insight in insights[:4]:
            severity_icon = {"high": "🔴", "medium": "🟡", "low": "🟢"}[insight.severity]
            msg = insight.message[:70]
            print(f"│ {severity_icon} {msg:72} │")
        print("└" + "─" * 76 + "┘")

    print()


def print_json(
    prom_data: PrometheusData,
    jsonl_stats: dict,
    insights: list[Insight],
    missed: list[MissedOpportunity],
):
    """Print analysis results as JSON."""
    output = {
        "prometheus": {
            "available": prom_data.available,
            "error": prom_data.error,
            "skill_usage": prom_data.skill_usage,
            "agent_usage": prom_data.agent_usage,
            "skill_trends": prom_data.skill_trends,
            "agent_trends": prom_data.agent_trends,
            "overall_success_rate": prom_data.overall_success_rate,
            "workflow_stages": prom_data.workflow_stages,
        },
        "jsonl": {
            "sessions": jsonl_stats["total_sessions"],
            "prompts": jsonl_stats["total_prompts"],
            "skills_used": dict(jsonl_stats["skills_used"]),
            "agents_used": dict(jsonl_stats["agents_used"]),
            "missed_skills": dict(jsonl_stats["missed_skills"]),
            "missed_agents": dict(jsonl_stats["missed_agents"]),
        },
        "insights": [
            {
                "type": i.type,
                "severity": i.severity,
                "item_name": i.item_name,
                "item_type": i.item_type,
                "message": i.message,
                "details": i.details,
            }
            for i in insights
        ],
        "missed_opportunities": [
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


# =============================================================================
# Quick Stats (existing, uses session summaries)
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
    parser = argparse.ArgumentParser(description="Analyze Claude Code usage patterns")
    parser.add_argument("--sessions", type=int, default=10, help="Sessions to analyze")
    parser.add_argument("--format", choices=["table", "dashboard", "json"], default="table")
    parser.add_argument("--verbose", action="store_true", help="Show examples")
    parser.add_argument("--project", help="Project path (default: current directory)")
    parser.add_argument("--quick-stats", action="store_true", help="Show quick stats from session summaries")
    parser.add_argument("--days", type=int, default=14, help="Days to include in quick stats (default: 14)")
    parser.add_argument("--no-prometheus", action="store_true", help="Skip Prometheus even if available")
    parser.add_argument("--prometheus-endpoint", help="Override Prometheus endpoint")
    parser.add_argument("--range", choices=["7d", "14d", "30d"], default="7d", help="Time range for Prometheus queries")
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

    # Fetch Prometheus data (unless disabled)
    prom_data = PrometheusData()
    if not args.no_prometheus:
        endpoint = args.prometheus_endpoint or get_prometheus_endpoint()
        if endpoint:
            print(f"Fetching Prometheus data from {endpoint}...", file=sys.stderr)
            prom_data = fetch_prometheus_data(endpoint, args.range)
            if prom_data.error:
                print(f"Warning: {prom_data.error}", file=sys.stderr)
        else:
            print("No Prometheus endpoint configured, using JSONL only", file=sys.stderr)

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

    # Analyze JSONL
    missed, jsonl_stats = analyze_jsonl(skills, agents, sessions)

    # Correlate data
    insights = correlate_data(prom_data, jsonl_stats, missed)

    # Output
    if args.format == "json":
        print_json(prom_data, jsonl_stats, insights, missed)
    elif args.format == "dashboard":
        print_dashboard(prom_data, jsonl_stats, insights)
    else:
        print_table(prom_data, jsonl_stats, insights, missed, args.verbose)


if __name__ == "__main__":
    main()
