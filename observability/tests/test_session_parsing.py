"""Tests for session JSONL parsing logic.

Tests the parse_session_file function and related utilities that
process Claude Code session files.
"""

import json
import pytest
import tempfile
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "hooks"))
from generate_session_summary import parse_session_file, get_session_file


def create_temp_session_file(entries: list[dict]) -> Path:
    """Create a temporary JSONL file with given entries."""
    with tempfile.NamedTemporaryFile(mode='w', suffix='.jsonl', delete=False) as f:
        for entry in entries:
            f.write(json.dumps(entry) + '\n')
        return Path(f.name)


class TestParseSessionFile:
    """Tests for parse_session_file function."""

    def test_empty_file(self, tmp_path):
        """Empty file should return default stats."""
        session_file = tmp_path / "session.jsonl"
        session_file.write_text("")
        stats = parse_session_file(session_file)
        assert stats["compaction_count"] == 0
        assert stats["success_count"] == 0
        assert stats["failure_count"] == 0

    def test_single_tool_success(self):
        """Single successful tool call."""
        entries = [
            {
                "type": "assistant",
                "message": {
                    "content": [{
                        "type": "tool_use",
                        "id": "tool_1",
                        "name": "Read",
                        "input": {"file_path": "test.py"}
                    }]
                }
            },
            {
                "type": "user",
                "message": {
                    "content": [{
                        "type": "tool_result",
                        "tool_use_id": "tool_1",
                        "content": "file contents here"
                    }]
                }
            }
        ]
        session_file = create_temp_session_file(entries)
        try:
            stats = parse_session_file(session_file)
            assert stats["tool_counts"]["Read"] == 1
            assert stats["success_count"] == 1
            assert stats["failure_count"] == 0
        finally:
            session_file.unlink()

    def test_single_tool_failure(self):
        """Single failed tool call."""
        entries = [
            {
                "type": "assistant",
                "message": {
                    "content": [{
                        "type": "tool_use",
                        "id": "tool_1",
                        "name": "Edit",
                        "input": {"file_path": "test.py"}
                    }]
                }
            },
            {
                "type": "user",
                "message": {
                    "content": [{
                        "type": "tool_result",
                        "tool_use_id": "tool_1",
                        "content": "Error: file not found"
                    }]
                }
            }
        ]
        session_file = create_temp_session_file(entries)
        try:
            stats = parse_session_file(session_file)
            assert stats["tool_counts"]["Edit"] == 1
            assert stats["failure_count"] == 1
            assert stats["success_count"] == 0
        finally:
            session_file.unlink()

    def test_compaction_detection(self):
        """Compaction boundaries should be counted."""
        entries = [
            {"type": "system", "subtype": "compact_boundary"},
            {"type": "system", "subtype": "compact_boundary"},
        ]
        session_file = create_temp_session_file(entries)
        try:
            stats = parse_session_file(session_file)
            assert stats["compaction_count"] == 2
        finally:
            session_file.unlink()

    def test_interruption_detection(self):
        """User interruptions should be counted."""
        entries = [
            {
                "type": "user",
                "message": {"content": "[Request interrupted by user]"}
            }
        ]
        session_file = create_temp_session_file(entries)
        try:
            stats = parse_session_file(session_file)
            assert stats["interrupted_count"] == 1
        finally:
            session_file.unlink()

    def test_pending_tools_as_interrupted(self):
        """Tools without results should be counted as interrupted."""
        entries = [
            {
                "type": "assistant",
                "message": {
                    "content": [{
                        "type": "tool_use",
                        "id": "tool_1",
                        "name": "Bash",
                        "input": {"command": "sleep 100"}
                    }]
                }
            }
            # No tool_result - user interrupted
        ]
        session_file = create_temp_session_file(entries)
        try:
            stats = parse_session_file(session_file)
            assert stats["tool_counts"]["Bash"] == 1
            assert stats["interrupted_count"] == 1
        finally:
            session_file.unlink()

    def test_skill_tracking(self):
        """Skill invocations should be tracked."""
        entries = [
            {
                "type": "assistant",
                "message": {
                    "content": [{
                        "type": "tool_use",
                        "id": "tool_1",
                        "name": "Skill",
                        "input": {"skill": "commit"}
                    }]
                }
            },
            {
                "type": "user",
                "message": {
                    "content": [{
                        "type": "tool_result",
                        "tool_use_id": "tool_1",
                        "content": "Done"
                    }]
                }
            }
        ]
        session_file = create_temp_session_file(entries)
        try:
            stats = parse_session_file(session_file)
            assert stats["skills_used"]["commit"] == 1
        finally:
            session_file.unlink()

    def test_agent_tracking(self):
        """Agent (Task) invocations should be tracked."""
        entries = [
            {
                "type": "assistant",
                "message": {
                    "content": [{
                        "type": "tool_use",
                        "id": "tool_1",
                        "name": "Task",
                        "input": {"subagent_type": "code-reviewer"}
                    }]
                }
            },
            {
                "type": "user",
                "message": {
                    "content": [{
                        "type": "tool_result",
                        "tool_use_id": "tool_1",
                        "content": "Review complete"
                    }]
                }
            }
        ]
        session_file = create_temp_session_file(entries)
        try:
            stats = parse_session_file(session_file)
            assert stats["agents_used"]["code-reviewer"] == 1
        finally:
            session_file.unlink()

    def test_stage_tracking(self):
        """Workflow stages should be tracked."""
        entries = [
            {
                "type": "assistant",
                "message": {
                    "content": [{
                        "type": "tool_use",
                        "id": "tool_1",
                        "name": "Skill",
                        "input": {"skill": "brainstorming"}
                    }]
                }
            },
            {
                "type": "user",
                "message": {
                    "content": [{
                        "type": "tool_result",
                        "tool_use_id": "tool_1",
                        "content": "Ideas generated"
                    }]
                }
            },
            {
                "type": "assistant",
                "message": {
                    "content": [{
                        "type": "tool_use",
                        "id": "tool_2",
                        "name": "Edit",
                        "input": {"file_path": "main.py"}
                    }]
                }
            },
            {
                "type": "user",
                "message": {
                    "content": [{
                        "type": "tool_result",
                        "tool_use_id": "tool_2",
                        "content": "File updated"
                    }]
                }
            }
        ]
        session_file = create_temp_session_file(entries)
        try:
            stats = parse_session_file(session_file)
            assert "brainstorm" in stats["stages_visited"]
            assert "implement" in stats["stages_visited"]
            assert stats["current_stage"] == "implement"
        finally:
            session_file.unlink()

    def test_malformed_jsonl_line_skipped(self):
        """Malformed JSON lines should be skipped, not crash."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.jsonl', delete=False) as f:
            f.write('{"type": "system"}\n')
            f.write('this is not json\n')
            f.write('{"type": "system", "subtype": "compact_boundary"}\n')
            session_file = Path(f.name)
        try:
            stats = parse_session_file(session_file)
            assert stats["compaction_count"] == 1  # Only valid line counted
        finally:
            session_file.unlink()

    def test_multiple_tools_in_single_message(self):
        """Multiple tool calls in one assistant message."""
        entries = [
            {
                "type": "assistant",
                "message": {
                    "content": [
                        {
                            "type": "tool_use",
                            "id": "tool_1",
                            "name": "Read",
                            "input": {"file_path": "a.py"}
                        },
                        {
                            "type": "tool_use",
                            "id": "tool_2",
                            "name": "Read",
                            "input": {"file_path": "b.py"}
                        }
                    ]
                }
            },
            {
                "type": "user",
                "message": {
                    "content": [
                        {"type": "tool_result", "tool_use_id": "tool_1", "content": "a content"},
                        {"type": "tool_result", "tool_use_id": "tool_2", "content": "b content"}
                    ]
                }
            }
        ]
        session_file = create_temp_session_file(entries)
        try:
            stats = parse_session_file(session_file)
            assert stats["tool_counts"]["Read"] == 2
            assert stats["success_count"] == 2
        finally:
            session_file.unlink()


class TestGetSessionFile:
    """Tests for get_session_file function."""

    def test_no_session_id_returns_none(self, tmp_path):
        assert get_session_file("", "/some/path") is None

    def test_no_cwd_returns_none(self, tmp_path):
        assert get_session_file("abc123", "") is None

    def test_nonexistent_project_returns_none(self):
        result = get_session_file("abc123", "/nonexistent/project/path")
        assert result is None


class TestEdgeCases:
    """Tests for edge cases and error handling."""

    def test_nonexistent_file_returns_defaults(self):
        """Reading nonexistent file should return default stats."""
        stats = parse_session_file(Path("/nonexistent/file.jsonl"))
        assert stats["compaction_count"] == 0
        assert stats["success_count"] == 0

    def test_content_as_string_in_user_message(self):
        """User message content can be string (simple prompt)."""
        entries = [
            {
                "type": "user",
                "message": {"content": "Hello, help me with code"}
            }
        ]
        session_file = create_temp_session_file(entries)
        try:
            stats = parse_session_file(session_file)
            # Should parse without error
            assert stats["interrupted_count"] == 0
        finally:
            session_file.unlink()

    def test_interruption_in_content_list(self):
        """Interruption message in content list format."""
        entries = [
            {
                "type": "user",
                "message": {
                    "content": [
                        {"type": "text", "text": "[Request interrupted by user]"}
                    ]
                }
            }
        ]
        session_file = create_temp_session_file(entries)
        try:
            stats = parse_session_file(session_file)
            assert stats["interrupted_count"] == 1
        finally:
            session_file.unlink()
