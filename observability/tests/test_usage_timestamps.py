"""Tests for usage timestamps (Story 1.2, AC-4).

Requirements:
- Track first_used timestamp for each skill
- Track last_used timestamp for each skill
- Add timestamp fields to skill output
"""

import sys
from pathlib import Path
from datetime import datetime

import pytest

sys.path.insert(0, str(Path(__file__).parent.parent / "skills" / "observability-usage-collector" / "scripts"))
from collect_usage import (
    SkillOrAgent,
    SessionData,
    generate_analysis_json,
    SetupProfile,
)


@pytest.fixture
def skill():
    """A skill to track timestamps for."""
    return SkillOrAgent(
        name="debugging",
        type="skill",
        description="Debug code",
        triggers=["debug", "debugging"],
        source_path="/test/path",
        source_type="global",
    )


@pytest.fixture
def sessions_with_timestamps(skill):
    """Sessions with different timestamps."""
    # Session 1 - earliest (Jan 10)
    s1 = SessionData(session_id="session-1")
    s1.session_date = datetime(2026, 1, 10, 10, 0, 0)
    s1.prompts = ["debug this"]
    s1.skills_used = {"debugging"}

    # Session 2 - middle (Jan 15)
    s2 = SessionData(session_id="session-2")
    s2.session_date = datetime(2026, 1, 15, 14, 0, 0)
    s2.prompts = ["hello"]
    s2.skills_used = set()  # Not used

    # Session 3 - latest (Jan 20)
    s3 = SessionData(session_id="session-3")
    s3.session_date = datetime(2026, 1, 20, 16, 0, 0)
    s3.prompts = ["debug again"]
    s3.skills_used = {"debugging"}

    return [s1, s2, s3]


class TestFirstUsedTimestamp:
    """Test that first_used timestamp is tracked."""

    def test_skill_has_first_used_field(self, skill, sessions_with_timestamps):
        """discovery.skills should include first_used field."""
        output = generate_analysis_json(
            skills=[skill],
            agents=[],
            commands=[],
            hooks=[],
            sessions=sessions_with_timestamps,
            jsonl_stats={"total_sessions": 3, "total_prompts": 3, "skills_used": {"debugging": 2}, "agents_used": {}, "commands_used": {}, "missed_skills": {}, "missed_agents": {}, "missed_commands": {}, "total_success": 0, "total_failure": 0, "total_interrupted": 0, "total_compactions": 0},
            claude_md={"files_found": [], "content": {}},
            setup_profile=SetupProfile("low", "minimal", [], [], [], [], {}, {}, []),
            missed=[],
            feedback={},
        )

        skill_output = output["discovery"]["skills"][0]
        assert "first_used" in skill_output

    def test_first_used_is_earliest_session(self, skill, sessions_with_timestamps):
        """first_used should be the timestamp of earliest session where skill was used."""
        output = generate_analysis_json(
            skills=[skill],
            agents=[],
            commands=[],
            hooks=[],
            sessions=sessions_with_timestamps,
            jsonl_stats={"total_sessions": 3, "total_prompts": 3, "skills_used": {"debugging": 2}, "agents_used": {}, "commands_used": {}, "missed_skills": {}, "missed_agents": {}, "missed_commands": {}, "total_success": 0, "total_failure": 0, "total_interrupted": 0, "total_compactions": 0},
            claude_md={"files_found": [], "content": {}},
            setup_profile=SetupProfile("low", "minimal", [], [], [], [], {}, {}, []),
            missed=[],
            feedback={},
        )

        skill_output = output["discovery"]["skills"][0]
        # Should be Jan 10 (earliest usage)
        assert skill_output["first_used"] == "2026-01-10T10:00:00"

    def test_first_used_null_when_never_used(self, skill):
        """first_used should be null when skill was never used."""
        s1 = SessionData(session_id="session-1")
        s1.session_date = datetime(2026, 1, 10, 10, 0, 0)
        s1.prompts = ["hello"]
        s1.skills_used = set()

        output = generate_analysis_json(
            skills=[skill],
            agents=[],
            commands=[],
            hooks=[],
            sessions=[s1],
            jsonl_stats={"total_sessions": 1, "total_prompts": 1, "skills_used": {}, "agents_used": {}, "commands_used": {}, "missed_skills": {}, "missed_agents": {}, "missed_commands": {}, "total_success": 0, "total_failure": 0, "total_interrupted": 0, "total_compactions": 0},
            claude_md={"files_found": [], "content": {}},
            setup_profile=SetupProfile("low", "minimal", [], [], [], [], {}, {}, []),
            missed=[],
            feedback={},
        )

        skill_output = output["discovery"]["skills"][0]
        assert skill_output["first_used"] is None


class TestLastUsedTimestamp:
    """Test that last_used timestamp is tracked."""

    def test_skill_has_last_used_field(self, skill, sessions_with_timestamps):
        """discovery.skills should include last_used field."""
        output = generate_analysis_json(
            skills=[skill],
            agents=[],
            commands=[],
            hooks=[],
            sessions=sessions_with_timestamps,
            jsonl_stats={"total_sessions": 3, "total_prompts": 3, "skills_used": {"debugging": 2}, "agents_used": {}, "commands_used": {}, "missed_skills": {}, "missed_agents": {}, "missed_commands": {}, "total_success": 0, "total_failure": 0, "total_interrupted": 0, "total_compactions": 0},
            claude_md={"files_found": [], "content": {}},
            setup_profile=SetupProfile("low", "minimal", [], [], [], [], {}, {}, []),
            missed=[],
            feedback={},
        )

        skill_output = output["discovery"]["skills"][0]
        assert "last_used" in skill_output

    def test_last_used_is_most_recent_session(self, skill, sessions_with_timestamps):
        """last_used should be the timestamp of most recent session where skill was used."""
        output = generate_analysis_json(
            skills=[skill],
            agents=[],
            commands=[],
            hooks=[],
            sessions=sessions_with_timestamps,
            jsonl_stats={"total_sessions": 3, "total_prompts": 3, "skills_used": {"debugging": 2}, "agents_used": {}, "commands_used": {}, "missed_skills": {}, "missed_agents": {}, "missed_commands": {}, "total_success": 0, "total_failure": 0, "total_interrupted": 0, "total_compactions": 0},
            claude_md={"files_found": [], "content": {}},
            setup_profile=SetupProfile("low", "minimal", [], [], [], [], {}, {}, []),
            missed=[],
            feedback={},
        )

        skill_output = output["discovery"]["skills"][0]
        # Should be Jan 20 (most recent usage)
        assert skill_output["last_used"] == "2026-01-20T16:00:00"

    def test_last_used_null_when_never_used(self, skill):
        """last_used should be null when skill was never used."""
        s1 = SessionData(session_id="session-1")
        s1.session_date = datetime(2026, 1, 10, 10, 0, 0)
        s1.prompts = ["hello"]
        s1.skills_used = set()

        output = generate_analysis_json(
            skills=[skill],
            agents=[],
            commands=[],
            hooks=[],
            sessions=[s1],
            jsonl_stats={"total_sessions": 1, "total_prompts": 1, "skills_used": {}, "agents_used": {}, "commands_used": {}, "missed_skills": {}, "missed_agents": {}, "missed_commands": {}, "total_success": 0, "total_failure": 0, "total_interrupted": 0, "total_compactions": 0},
            claude_md={"files_found": [], "content": {}},
            setup_profile=SetupProfile("low", "minimal", [], [], [], [], {}, {}, []),
            missed=[],
            feedback={},
        )

        skill_output = output["discovery"]["skills"][0]
        assert skill_output["last_used"] is None


class TestAgentTimestamps:
    """Test that agents also have timestamp fields."""

    def test_agent_has_timestamp_fields(self):
        """Agents should also have first_used and last_used fields."""
        agent = SkillOrAgent(
            name="reviewer",
            type="agent",
            description="Review code",
            triggers=["review"],
            source_path="/test/path",
            source_type="global",
        )

        s1 = SessionData(session_id="session-1")
        s1.session_date = datetime(2026, 1, 10, 10, 0, 0)
        s1.prompts = ["review code"]
        s1.agents_used = {"reviewer"}

        s2 = SessionData(session_id="session-2")
        s2.session_date = datetime(2026, 1, 20, 16, 0, 0)
        s2.prompts = ["review again"]
        s2.agents_used = {"reviewer"}

        output = generate_analysis_json(
            skills=[],
            agents=[agent],
            commands=[],
            hooks=[],
            sessions=[s1, s2],
            jsonl_stats={"total_sessions": 2, "total_prompts": 2, "skills_used": {}, "agents_used": {"reviewer": 2}, "commands_used": {}, "missed_skills": {}, "missed_agents": {}, "missed_commands": {}, "total_success": 0, "total_failure": 0, "total_interrupted": 0, "total_compactions": 0},
            claude_md={"files_found": [], "content": {}},
            setup_profile=SetupProfile("low", "minimal", [], [], [], [], {}, {}, []),
            missed=[],
            feedback={},
        )

        agent_output = output["discovery"]["agents"][0]
        assert "first_used" in agent_output
        assert "last_used" in agent_output
        assert agent_output["first_used"] == "2026-01-10T10:00:00"
        assert agent_output["last_used"] == "2026-01-20T16:00:00"
