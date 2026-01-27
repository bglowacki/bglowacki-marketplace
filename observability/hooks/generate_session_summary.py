#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.10"
# dependencies = []
# ///
"""
Session Summary Generator - Pure Python, no external dependencies.

Reads Claude Code session JSONL files and generates summary JSON files.
Tracks: tool counts, outcomes, compactions, interruptions, workflow stages.

Output: ~/.claude/session-summaries/{date}_{session_id}.json
"""

import json
import os
import re
import subprocess
import sys
from collections import defaultdict
from datetime import datetime
from pathlib import Path


SUMMARY_DIR = Path.home() / ".claude" / "session-summaries"


def get_session_file(session_id: str, cwd: str) -> Path | None:
    """Find the session JSONL file for a given session ID and cwd."""
    if not session_id or not cwd:
        return None

    projects_dir = Path.home() / ".claude" / "projects"
    project_folder = cwd.replace("/", "-")
    if project_folder.startswith("-"):
        project_folder = project_folder[1:]

    project_dir = projects_dir / f"-{project_folder}"
    if not project_dir.exists():
        project_dir = projects_dir / project_folder

    if not project_dir.exists():
        return None

    for jsonl_file in project_dir.glob("*.jsonl"):
        if session_id in jsonl_file.name:
            return jsonl_file

    return None


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


def infer_workflow_stage(tool_name: str, tool_input: dict, current_stage: str) -> str:
    """Infer workflow stage from tool usage."""
    if tool_name == "Skill":
        skill = tool_input.get("skill", "").lower()
        if "brainstorm" in skill:
            return "brainstorm"
        if "plan" in skill or "writing-plans" in skill:
            return "plan"
        if "review" in skill or "code-review" in skill:
            return "review"
        if "tdd" in skill or "test-driven" in skill:
            return "test"
        if "commit" in skill:
            return "commit"

    if tool_name in ("Edit", "Write"):
        return "implement"

    if tool_name == "Bash":
        cmd = tool_input.get("command", "").lower()
        if any(t in cmd for t in ["pytest", "test", "unittest", "jest", "npm test"]):
            return "test"
        if "git commit" in cmd:
            return "commit"
        if "git push" in cmd:
            return "deploy"

    if tool_name == "Task":
        agent = tool_input.get("subagent_type", "").lower()
        if "review" in agent:
            return "review"
        if "test" in agent:
            return "test"

    return current_stage


def parse_session_file(session_path: Path) -> dict:
    """Parse a session JSONL file and extract summary data."""
    stats = {
        "tool_counts": defaultdict(int),
        "success_count": 0,
        "failure_count": 0,
        "interrupted_count": 0,
        "compaction_count": 0,
        "stages_visited": [],
        "current_stage": "unknown",
        "pending_tools": {},  # tool_use_id -> tool_name (for interruption detection)
        "skills_used": defaultdict(int),
        "agents_used": defaultdict(int),
    }

    try:
        lines = session_path.read_text().strip().split("\n")
    except Exception:
        return stats

    for line in lines:
        try:
            entry = json.loads(line)
        except json.JSONDecodeError:
            continue

        entry_type = entry.get("type")

        # Detect compactions
        if entry_type == "system" and entry.get("subtype") == "compact_boundary":
            stats["compaction_count"] += 1
            continue

        # Process assistant messages (tool calls)
        if entry_type == "assistant":
            message = entry.get("message", {})
            content = message.get("content", [])

            if isinstance(content, list):
                for item in content:
                    if isinstance(item, dict) and item.get("type") == "tool_use":
                        tool_name = item.get("name", "")
                        tool_use_id = item.get("id", "")
                        tool_input = item.get("input", {})

                        if tool_name:
                            stats["tool_counts"][tool_name] += 1
                            # Track pending for interruption detection
                            if tool_use_id:
                                stats["pending_tools"][tool_use_id] = tool_name

                            # Track skill/agent usage
                            if tool_name == "Skill":
                                skill = tool_input.get("skill", "unknown")
                                stats["skills_used"][skill] += 1
                            elif tool_name == "Task":
                                agent = tool_input.get("subagent_type", "unknown")
                                stats["agents_used"][agent] += 1

                            # Infer workflow stage
                            new_stage = infer_workflow_stage(tool_name, tool_input, stats["current_stage"])
                            if new_stage != stats["current_stage"]:
                                if new_stage not in stats["stages_visited"]:
                                    stats["stages_visited"].append(new_stage)
                                stats["current_stage"] = new_stage

        # Process user messages (contain prompts, interruptions, and tool results)
        if entry_type == "user":
            message = entry.get("message", {})
            content = message.get("content", "")

            if isinstance(content, str):
                if "[Request interrupted by user]" in content:
                    stats["interrupted_count"] += 1
            elif isinstance(content, list):
                for item in content:
                    if isinstance(item, dict):
                        item_type = item.get("type")
                        if item_type == "text":
                            text = item.get("text", "")
                            if "[Request interrupted by user]" in text:
                                stats["interrupted_count"] += 1
                        elif item_type == "tool_result":
                            # Tool results are in user messages
                            tool_use_id = item.get("tool_use_id", "")
                            result = item.get("content", "")

                            # Get tool name from pending and remove (completed)
                            tool_name = stats["pending_tools"].pop(tool_use_id, "unknown")

                            if isinstance(result, str):
                                outcome = detect_outcome(tool_name, result)
                                if outcome == "success":
                                    stats["success_count"] += 1
                                else:
                                    stats["failure_count"] += 1

    # Any remaining pending tools are interrupted (PreToolUse without PostToolUse/result)
    stats["interrupted_count"] += len(stats["pending_tools"])

    return stats


def notify_macos(title: str, message: str):
    """Send macOS notification."""
    try:
        subprocess.run([
            "osascript", "-e",
            f'display notification "{message}" with title "{title}"'
        ], capture_output=True, timeout=5)
    except Exception:
        pass


def generate_summary(session_id: str, cwd: str, stats: dict) -> dict:
    """Generate summary JSON from parsed stats."""
    project = os.path.basename(cwd.rstrip("/")) if cwd else "unknown"

    return {
        "session_id": session_id,
        "project": project,
        "timestamp": datetime.now().isoformat(),
        "total_tools": sum(stats["tool_counts"].values()),
        "tool_breakdown": dict(stats["tool_counts"]),
        "skills_used": dict(stats["skills_used"]),
        "agents_used": dict(stats["agents_used"]),
        "stages_visited": stats["stages_visited"],
        "final_stage": stats["current_stage"],
        "outcomes": {
            "success": stats["success_count"],
            "failure": stats["failure_count"],
            "interrupted": stats["interrupted_count"],
        },
        "compactions": stats["compaction_count"],
    }


def main():
    try:
        input_data = json.load(sys.stdin)
    except json.JSONDecodeError:
        sys.exit(0)

    session_id = input_data.get("session_id", "")
    cwd = input_data.get("cwd", "")

    if not session_id:
        sys.exit(0)

    # Find and parse session file
    session_file = get_session_file(session_id, cwd)
    if not session_file:
        sys.exit(0)

    stats = parse_session_file(session_file)

    # Only generate summary if there was actual activity
    if sum(stats["tool_counts"].values()) == 0:
        sys.exit(0)

    summary = generate_summary(session_id, cwd, stats)

    # Save summary
    SUMMARY_DIR.mkdir(parents=True, exist_ok=True)
    filename = f"{datetime.now().strftime('%Y-%m-%d')}_{session_id[:8]}.json"
    (SUMMARY_DIR / filename).write_text(json.dumps(summary, indent=2))

    # Send notification
    success = summary["outcomes"]["success"]
    failure = summary["outcomes"]["failure"]
    interrupted = summary["outcomes"]["interrupted"]
    notify_macos(
        f"Session Complete: {summary['project']}",
        f"Tools: {summary['total_tools']} | \u2713{success} \u2717{failure} \u23f9{interrupted}"
    )


if __name__ == "__main__":
    main()
