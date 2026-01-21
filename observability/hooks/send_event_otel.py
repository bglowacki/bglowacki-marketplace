#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.10"
# dependencies = [
#     "opentelemetry-api",
#     "opentelemetry-sdk",
#     "opentelemetry-exporter-otlp-proto-http",
# ]
# ///
"""
OTEL-based hook for Claude Code observability.
Exports custom events and metrics for skills/agents tracking.

Tracks:
- Skill invocations (tool_name == "Skill")
- Subagent invocations (tool_name == "Task")
- Tool usage by type
- Outcomes (success/failure/interrupted)
- Interrupted tools (PreToolUse without PostToolUse)
- Workflow stages
- Context compactions
"""

import json
import sys
import os
import argparse
import atexit
import tempfile
from pathlib import Path
from datetime import datetime

# Global config location
GLOBAL_CONFIG = Path.home() / ".claude" / "observability" / "endpoint.env"

if not GLOBAL_CONFIG.exists():
    # Not configured - run /observability-setup first
    sys.exit(0)

STATE_DIR = Path(tempfile.gettempdir()) / "claude_code_metrics"
SUMMARY_DIR = Path.home() / ".claude" / "session-summaries"

_connection_warned = False


def get_otel_endpoint() -> str:
    """Get OTEL endpoint from global config."""
    for line in GLOBAL_CONFIG.read_text().splitlines():
        if line.startswith("OTEL_ENDPOINT="):
            return line.split("=", 1)[1].strip()
    return "http://localhost:30418"


OTEL_ENDPOINT = get_otel_endpoint()

from opentelemetry import metrics
from opentelemetry.sdk.metrics import MeterProvider
from opentelemetry.sdk.resources import Resource
from opentelemetry.exporter.otlp.proto.http.metric_exporter import OTLPMetricExporter
from opentelemetry.sdk.metrics.export import PeriodicExportingMetricReader

resource = Resource.create({
    "service.name": "claude-code-hooks",
    "service.version": "1.0.0",
})

exporter = OTLPMetricExporter(endpoint=f"{OTEL_ENDPOINT}/v1/metrics")
reader = PeriodicExportingMetricReader(exporter, export_interval_millis=5000)
provider = MeterProvider(resource=resource, metric_readers=[reader])
metrics.set_meter_provider(provider)

meter = metrics.get_meter("claude_code_hooks", version="1.0.0")

skill_invocations = meter.create_counter(
    "claude_code.skill.invocations",
    description="Number of skill invocations",
    unit="1"
)

agent_invocations = meter.create_counter(
    "claude_code.agent.invocations",
    description="Number of subagent invocations",
    unit="1"
)

tool_invocations = meter.create_counter(
    "claude_code.hook.tool_invocations",
    description="Tool invocations tracked by hooks",
    unit="1"
)

prompt_submissions = meter.create_counter(
    "claude_code.hook.prompt_submissions",
    description="User prompt submissions",
    unit="1"
)

subagent_completions = meter.create_counter(
    "claude_code.hook.subagent_completions",
    description="Subagent completions",
    unit="1"
)

outcome_success = meter.create_counter(
    "claude_code.outcome.success",
    description="Successful tool completions",
    unit="1"
)

outcome_failure = meter.create_counter(
    "claude_code.outcome.failure",
    description="Failed tool completions",
    unit="1"
)

workflow_stage_transition = meter.create_counter(
    "claude_code.workflow.stage_transition",
    description="Workflow stage transitions",
    unit="1"
)

context_compaction = meter.create_counter(
    "claude_code.context.compaction",
    description="Context compaction events",
    unit="1"
)

tools_per_compaction = meter.create_histogram(
    "claude_code.context.tools_per_compaction",
    description="Number of tools used between compactions",
    unit="1"
)

tool_interrupted = meter.create_counter(
    "claude_code.tool.interrupted",
    description="Tool calls interrupted by user (ESC) or failed before completion",
    unit="1"
)

tool_started = meter.create_counter(
    "claude_code.tool.started",
    description="Tool calls started (PreToolUse)",
    unit="1"
)


def flush_metrics():
    global _connection_warned
    try:
        provider.force_flush(timeout_millis=2000)
    except Exception as e:
        if not _connection_warned:
            print(f"[observability] Warning: Could not send metrics - {e}", file=sys.stderr)
            _connection_warned = True
    try:
        provider.shutdown()
    except Exception:
        pass


atexit.register(flush_metrics)


def extract_skill_info(payload: dict) -> dict:
    tool_input = payload.get("tool_input", {})
    return {
        "skill_name": tool_input.get("skill", "unknown"),
        "skill_args": str(tool_input.get("args", ""))[:50],
    }


def extract_agent_info(payload: dict) -> dict:
    tool_input = payload.get("tool_input", {})
    return {
        "agent_type": tool_input.get("subagent_type", "unknown"),
        "agent_description": str(tool_input.get("description", ""))[:50],
    }


def get_project_name(cwd: str) -> str:
    if not cwd:
        return "unknown"
    return os.path.basename(cwd.rstrip("/")) or "root"


def get_session_state(session_id: str) -> dict:
    state_file = STATE_DIR / f"{session_id}.json"
    if state_file.exists():
        try:
            return json.loads(state_file.read_text())
        except (json.JSONDecodeError, IOError):
            pass
    return {
        "prev_tool": None,
        "workflow_stage": "unknown",
        "tool_sequence": [],
        "stages_visited": [],
        "success_count": 0,
        "failure_count": 0,
        "interrupted_count": 0,
        "compaction_count": 0,
        "pending_tools": {},  # tool_use_id -> tool_name
    }


def save_session_state(session_id: str, state: dict):
    try:
        STATE_DIR.mkdir(exist_ok=True)
        state_file = STATE_DIR / f"{session_id}.json"
        state["tool_sequence"] = state["tool_sequence"][-50:]
        state_file.write_text(json.dumps(state))
    except (IOError, OSError):
        pass


def cleanup_session_state(session_id: str):
    state_file = STATE_DIR / f"{session_id}.json"
    try:
        state_file.unlink(missing_ok=True)
    except (IOError, OSError):
        pass


def notify_macos(title: str, message: str):
    import subprocess
    try:
        subprocess.run([
            "osascript", "-e",
            f'display notification "{message}" with title "{title}"'
        ], capture_output=True, timeout=5)
    except Exception:
        pass


def generate_and_save_summary(session_id: str, state: dict, project: str):
    tool_counts = {}
    for tool in state.get("tool_sequence", []):
        tool_counts[tool] = tool_counts.get(tool, 0) + 1

    summary = {
        "session_id": session_id,
        "project": project,
        "timestamp": datetime.now().isoformat(),
        "total_tools": len(state.get("tool_sequence", [])),
        "tool_breakdown": tool_counts,
        "stages_visited": state.get("stages_visited", []),
        "final_stage": state.get("workflow_stage", "unknown"),
        "outcomes": {
            "success": state.get("success_count", 0),
            "failure": state.get("failure_count", 0),
            "interrupted": state.get("interrupted_count", 0),
        },
        "compactions": state.get("compaction_count", 0),
    }

    SUMMARY_DIR.mkdir(parents=True, exist_ok=True)
    filename = f"{datetime.now().strftime('%Y-%m-%d')}_{session_id}.json"
    (SUMMARY_DIR / filename).write_text(json.dumps(summary, indent=2))

    success = summary["outcomes"]["success"]
    failure = summary["outcomes"]["failure"]
    interrupted = summary["outcomes"]["interrupted"]
    notify_macos(
        f"Session Complete: {project}",
        f"Tools: {summary['total_tools']} | ✓{success} ✗{failure} ⏹{interrupted} | Stages: {len(summary['stages_visited'])}"
    )

    return summary


def detect_bash_outcome(payload: dict) -> tuple:
    result = str(payload.get("tool_result", "")).lower()

    if "exit code: 0" in result or "succeeded" in result:
        return ("success", None)
    if "exit code:" in result:
        return ("failure", "nonzero_exit")
    if "timeout" in result:
        return ("failure", "timeout")
    if "error:" in result or "failed" in result or "traceback" in result:
        return ("failure", "error")
    if "permission denied" in result:
        return ("failure", "permission")

    return ("success", None)


def detect_edit_outcome(payload: dict) -> tuple:
    result = str(payload.get("tool_result", "")).lower()

    if "permission denied" in result:
        return ("failure", "permission")
    if "file not found" in result or "no such file" in result:
        return ("failure", "not_found")
    if "old_string not found" in result or "not unique" in result:
        return ("failure", "match_failed")
    if "error" in result:
        return ("failure", "error")

    return ("success", None)


def detect_skill_outcome(payload: dict) -> tuple:
    result = str(payload.get("tool_result", "")).lower()

    if payload.get("was_rejected"):
        return ("failure", "rejected")
    if "error" in result or "failed" in result:
        return ("failure", "error")

    return ("success", None)


def detect_outcome(tool_name: str, payload: dict) -> tuple:
    if tool_name == "Bash":
        return detect_bash_outcome(payload)
    if tool_name in ("Edit", "Write", "NotebookEdit"):
        return detect_edit_outcome(payload)
    if tool_name in ("Skill", "Task"):
        return detect_skill_outcome(payload)

    result = str(payload.get("tool_result", "")).lower()
    if "error" in result or "failed" in result:
        return ("failure", "error")
    return ("success", None)


def infer_workflow_stage(tool_name: str, payload: dict, current_stage: str) -> str:
    tool_input = payload.get("tool_input", {})

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


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--event-type", required=True)
    parser.add_argument("--source-app", default="plugin")
    args = parser.parse_args()

    try:
        input_data = json.load(sys.stdin)
    except json.JSONDecodeError:
        sys.exit(0)

    session_id = input_data.get("session_id", "unknown")[:8]
    tool_name = input_data.get("tool_name", "")
    cwd = input_data.get("cwd", "")
    project = get_project_name(cwd)

    base_attributes = {
        "session_id": session_id,
        "source_app": args.source_app,
        "event_type": args.event_type,
        "project": project,
    }

    if args.event_type == "PreToolUse":
        state = get_session_state(session_id)
        tool_use_id = input_data.get("tool_use_id", "")

        # Track this tool as pending (started but not yet completed)
        if tool_use_id:
            pending = state.get("pending_tools", {})
            pending[tool_use_id] = tool_name
            state["pending_tools"] = pending

        tool_started.add(1, {**base_attributes, "tool_name": tool_name})
        save_session_state(session_id, state)

    elif args.event_type == "PostToolUse":
        state = get_session_state(session_id)
        tool_use_id = input_data.get("tool_use_id", "")

        # Remove from pending (tool completed successfully)
        if tool_use_id:
            pending = state.get("pending_tools", {})
            pending.pop(tool_use_id, None)
            state["pending_tools"] = pending

        outcome, failure_reason = detect_outcome(tool_name, input_data)

        if outcome == "success":
            state["success_count"] += 1
            outcome_success.add(1, {**base_attributes, "tool_name": tool_name})
        else:
            state["failure_count"] += 1
            outcome_failure.add(1, {
                **base_attributes,
                "tool_name": tool_name,
                "failure_reason": failure_reason or "unknown",
            })

        new_stage = infer_workflow_stage(tool_name, input_data, state["workflow_stage"])
        if new_stage != state["workflow_stage"]:
            workflow_stage_transition.add(1, {
                **base_attributes,
                "from_stage": state["workflow_stage"],
                "to_stage": new_stage,
            })
            if new_stage not in state["stages_visited"]:
                state["stages_visited"].append(new_stage)
            state["workflow_stage"] = new_stage

        prev_tool = state["prev_tool"]
        state["tool_sequence"].append(tool_name)
        state["prev_tool"] = tool_name

        tool_invocations.add(1, {
            **base_attributes,
            "tool_name": tool_name,
            "outcome": outcome,
            "workflow_stage": state["workflow_stage"],
            "prev_tool": prev_tool or "none",
        })

        if tool_name == "Skill":
            skill_info = extract_skill_info(input_data)
            skill_invocations.add(1, {
                **base_attributes,
                "skill_name": skill_info["skill_name"],
                "outcome": outcome,
            })

        if tool_name == "Task":
            agent_info = extract_agent_info(input_data)
            agent_invocations.add(1, {
                **base_attributes,
                "agent_type": agent_info["agent_type"],
                "outcome": outcome,
            })

        save_session_state(session_id, state)

    elif args.event_type == "UserPromptSubmit":
        prompt_submissions.add(1, base_attributes)

    elif args.event_type == "SubagentStop":
        subagent_completions.add(1, {
            **base_attributes,
            "agent_id": input_data.get("agent_id", "unknown")[:8],
        })

    elif args.event_type == "PreCompact":
        state = get_session_state(session_id)
        tool_count = len(state.get("tool_sequence", []))

        context_compaction.add(1, {
            **base_attributes,
            "tools_before_compaction": str(tool_count),
        })

        if tool_count > 0:
            tools_per_compaction.record(tool_count, base_attributes)

        state["compaction_count"] = state.get("compaction_count", 0) + 1
        state["tool_sequence"] = []
        save_session_state(session_id, state)

    elif args.event_type in ("Stop", "SessionStop"):
        state = get_session_state(session_id)

        # Count pending tools as interrupted (PreToolUse fired but PostToolUse never came)
        pending = state.get("pending_tools", {})
        if pending:
            for tool_use_id, pending_tool_name in pending.items():
                tool_interrupted.add(1, {
                    **base_attributes,
                    "tool_name": pending_tool_name,
                    "tool_use_id": tool_use_id[:8] if tool_use_id else "unknown",
                })
                state["interrupted_count"] = state.get("interrupted_count", 0) + 1
            state["pending_tools"] = {}

        if state.get("tool_sequence") or state.get("success_count", 0) > 0:
            generate_and_save_summary(session_id, state, project)

        cleanup_session_state(session_id)

    flush_metrics()
    sys.exit(0)


if __name__ == "__main__":
    main()
