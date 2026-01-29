"""Tests for per-skill usage counts (Story 1.2, AC-2).

Requirements:
- Count invocations per skill across all sessions
- Track which sessions used each skill (session context)
- Add usage_count and sessions_used fields to output
"""

import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).parent.parent / "skills" / "observability-usage-collector" / "scripts"))
from collect_usage import (
    SkillOrAgent,
    SessionData,
    generate_analysis_json,
    SetupProfile,
)


@pytest.fixture
def skill_used_multiple_times():
    """A skill that will be used in multiple sessions."""
    return SkillOrAgent(
        name="systematic-debugging",
        type="skill",
        description="Debug issues systematically",
        triggers=["debug", "debugging", "bug", "issue", "error", "fix"],
        source_path="/test/path",
        source_type="global",
    )


@pytest.fixture
def sessions_with_skill_usage(skill_used_multiple_times):
    """Sessions where the skill was invoked multiple times."""
    # Session 1 - skill used once
    s1 = SessionData(session_id="session-1")
    s1.prompts = ["help me debug this"]
    s1.skills_used = {"systematic-debugging"}

    # Session 2 - skill used again
    s2 = SessionData(session_id="session-2")
    s2.prompts = ["another debugging task"]
    s2.skills_used = {"systematic-debugging"}

    # Session 3 - skill NOT used
    s3 = SessionData(session_id="session-3")
    s3.prompts = ["write hello world"]
    s3.skills_used = set()

    return [s1, s2, s3]


class TestUsageCountField:
    """Test that usage_count field is present in output."""

    def test_skill_has_usage_count_field(self, skill_used_multiple_times, sessions_with_skill_usage):
        """discovery.skills should include usage_count field."""
        output = generate_analysis_json(
            skills=[skill_used_multiple_times],
            agents=[],
            commands=[],
            hooks=[],
            sessions=sessions_with_skill_usage,
            jsonl_stats={"total_sessions": 3, "total_prompts": 3, "skills_used": {"systematic-debugging": 2}, "agents_used": {}, "commands_used": {}, "missed_skills": {}, "missed_agents": {}, "missed_commands": {}, "total_success": 0, "total_failure": 0, "total_interrupted": 0, "total_compactions": 0},
            claude_md={"files_found": [], "content": {}},
            setup_profile=SetupProfile("low", "minimal", [], [], [], [], {}, {}, []),
            missed=[],
            feedback={},
        )

        skill_output = output["discovery"]["skills"][0]
        assert "usage_count" in skill_output
        assert skill_output["usage_count"] == 2  # Used in 2 sessions

    def test_unused_skill_has_zero_usage_count(self, skill_used_multiple_times):
        """Unused skill should have usage_count of 0."""
        session = SessionData(session_id="test")
        session.prompts = ["hello world"]
        session.skills_used = set()

        output = generate_analysis_json(
            skills=[skill_used_multiple_times],
            agents=[],
            commands=[],
            hooks=[],
            sessions=[session],
            jsonl_stats={"total_sessions": 1, "total_prompts": 1, "skills_used": {}, "agents_used": {}, "commands_used": {}, "missed_skills": {}, "missed_agents": {}, "missed_commands": {}, "total_success": 0, "total_failure": 0, "total_interrupted": 0, "total_compactions": 0},
            claude_md={"files_found": [], "content": {}},
            setup_profile=SetupProfile("low", "minimal", [], [], [], [], {}, {}, []),
            missed=[],
            feedback={},
        )

        skill_output = output["discovery"]["skills"][0]
        assert skill_output["usage_count"] == 0


class TestSessionsUsedField:
    """Test that sessions_used field is present in output."""

    def test_skill_has_sessions_used_field(self, skill_used_multiple_times, sessions_with_skill_usage):
        """discovery.skills should include sessions_used field with session IDs."""
        output = generate_analysis_json(
            skills=[skill_used_multiple_times],
            agents=[],
            commands=[],
            hooks=[],
            sessions=sessions_with_skill_usage,
            jsonl_stats={"total_sessions": 3, "total_prompts": 3, "skills_used": {"systematic-debugging": 2}, "agents_used": {}, "commands_used": {}, "missed_skills": {}, "missed_agents": {}, "missed_commands": {}, "total_success": 0, "total_failure": 0, "total_interrupted": 0, "total_compactions": 0},
            claude_md={"files_found": [], "content": {}},
            setup_profile=SetupProfile("low", "minimal", [], [], [], [], {}, {}, []),
            missed=[],
            feedback={},
        )

        skill_output = output["discovery"]["skills"][0]
        assert "sessions_used" in skill_output
        assert isinstance(skill_output["sessions_used"], list)
        assert "session-1" in skill_output["sessions_used"]
        assert "session-2" in skill_output["sessions_used"]
        assert "session-3" not in skill_output["sessions_used"]  # Not used in this session

    def test_unused_skill_has_empty_sessions_used(self, skill_used_multiple_times):
        """Unused skill should have empty sessions_used list."""
        session = SessionData(session_id="test")
        session.prompts = ["hello world"]
        session.skills_used = set()

        output = generate_analysis_json(
            skills=[skill_used_multiple_times],
            agents=[],
            commands=[],
            hooks=[],
            sessions=[session],
            jsonl_stats={"total_sessions": 1, "total_prompts": 1, "skills_used": {}, "agents_used": {}, "commands_used": {}, "missed_skills": {}, "missed_agents": {}, "missed_commands": {}, "total_success": 0, "total_failure": 0, "total_interrupted": 0, "total_compactions": 0},
            claude_md={"files_found": [], "content": {}},
            setup_profile=SetupProfile("low", "minimal", [], [], [], [], {}, {}, []),
            missed=[],
            feedback={},
        )

        skill_output = output["discovery"]["skills"][0]
        assert skill_output["sessions_used"] == []


class TestAgentUsageCounts:
    """Test that agents also have usage counts and sessions_used fields."""

    def test_agent_has_usage_count_and_sessions_used(self):
        """Agents should also have usage_count and sessions_used fields."""
        agent = SkillOrAgent(
            name="code-reviewer",
            type="agent",
            description="Review code",
            triggers=["review", "code review"],
            source_path="/test/path",
            source_type="global",
        )

        s1 = SessionData(session_id="session-1")
        s1.prompts = ["review my code"]
        s1.agents_used = {"code-reviewer"}

        s2 = SessionData(session_id="session-2")
        s2.prompts = ["hello"]
        s2.agents_used = set()

        output = generate_analysis_json(
            skills=[],
            agents=[agent],
            commands=[],
            hooks=[],
            sessions=[s1, s2],
            jsonl_stats={"total_sessions": 2, "total_prompts": 2, "skills_used": {}, "agents_used": {"code-reviewer": 1}, "commands_used": {}, "missed_skills": {}, "missed_agents": {}, "missed_commands": {}, "total_success": 0, "total_failure": 0, "total_interrupted": 0, "total_compactions": 0},
            claude_md={"files_found": [], "content": {}},
            setup_profile=SetupProfile("low", "minimal", [], [], [], [], {}, {}, []),
            missed=[],
            feedback={},
        )

        agent_output = output["discovery"]["agents"][0]
        assert "usage_count" in agent_output
        assert agent_output["usage_count"] == 1
        assert "sessions_used" in agent_output
        assert agent_output["sessions_used"] == ["session-1"]
