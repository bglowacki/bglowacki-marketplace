"""Tests for per-project breakdown (Story 1.2, AC-3).

Requirements:
- Group session data by project path
- Generate per-project skill usage summaries
- Add per_project section to JSON output
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
def skill():
    """A skill used across projects."""
    return SkillOrAgent(
        name="debugging",
        type="skill",
        description="Debug code",
        triggers=["debug", "debugging"],
        source_path="/test/path",
        source_type="global",
    )


@pytest.fixture
def sessions_multiple_projects(skill):
    """Sessions from different projects."""
    # Project A - 2 sessions
    s1 = SessionData(session_id="session-1")
    s1.project_path = "/Users/foo/project-a"
    s1.prompts = ["debug this"]
    s1.skills_used = {"debugging"}

    s2 = SessionData(session_id="session-2")
    s2.project_path = "/Users/foo/project-a"
    s2.prompts = ["hello"]
    s2.skills_used = set()

    # Project B - 1 session
    s3 = SessionData(session_id="session-3")
    s3.project_path = "/Users/foo/project-b"
    s3.prompts = ["debug issue"]
    s3.skills_used = {"debugging"}

    return [s1, s2, s3]


class TestSessionProjectPath:
    """Test that SessionData has project_path field."""

    def test_session_has_project_path_field(self):
        """SessionData should have project_path field."""
        session = SessionData(session_id="test")
        assert hasattr(session, "project_path")

    def test_session_project_path_defaults_to_unknown(self):
        """SessionData.project_path should default to 'unknown'."""
        session = SessionData(session_id="test")
        assert session.project_path == "unknown"


class TestPerProjectSection:
    """Test that per_project section exists in output."""

    def test_output_has_per_project_section(self, skill, sessions_multiple_projects):
        """JSON output should include per_project section."""
        output = generate_analysis_json(
            skills=[skill],
            agents=[],
            commands=[],
            hooks=[],
            sessions=sessions_multiple_projects,
            jsonl_stats={"total_sessions": 3, "total_prompts": 3, "skills_used": {"debugging": 2}, "agents_used": {}, "commands_used": {}, "missed_skills": {}, "missed_agents": {}, "missed_commands": {}, "total_success": 0, "total_failure": 0, "total_interrupted": 0, "total_compactions": 0},
            claude_md={"files_found": [], "content": {}},
            setup_profile=SetupProfile("low", "minimal", [], [], [], [], {}, {}, []),
            missed=[],
            feedback={},
        )

        assert "per_project" in output

    def test_per_project_groups_by_project_path(self, skill, sessions_multiple_projects):
        """per_project should group sessions by project path."""
        output = generate_analysis_json(
            skills=[skill],
            agents=[],
            commands=[],
            hooks=[],
            sessions=sessions_multiple_projects,
            jsonl_stats={"total_sessions": 3, "total_prompts": 3, "skills_used": {"debugging": 2}, "agents_used": {}, "commands_used": {}, "missed_skills": {}, "missed_agents": {}, "missed_commands": {}, "total_success": 0, "total_failure": 0, "total_interrupted": 0, "total_compactions": 0},
            claude_md={"files_found": [], "content": {}},
            setup_profile=SetupProfile("low", "minimal", [], [], [], [], {}, {}, []),
            missed=[],
            feedback={},
        )

        per_project = output["per_project"]
        assert "/Users/foo/project-a" in per_project
        assert "/Users/foo/project-b" in per_project

    def test_per_project_shows_session_count(self, skill, sessions_multiple_projects):
        """Each project should show its session count."""
        output = generate_analysis_json(
            skills=[skill],
            agents=[],
            commands=[],
            hooks=[],
            sessions=sessions_multiple_projects,
            jsonl_stats={"total_sessions": 3, "total_prompts": 3, "skills_used": {"debugging": 2}, "agents_used": {}, "commands_used": {}, "missed_skills": {}, "missed_agents": {}, "missed_commands": {}, "total_success": 0, "total_failure": 0, "total_interrupted": 0, "total_compactions": 0},
            claude_md={"files_found": [], "content": {}},
            setup_profile=SetupProfile("low", "minimal", [], [], [], [], {}, {}, []),
            missed=[],
            feedback={},
        )

        per_project = output["per_project"]
        assert per_project["/Users/foo/project-a"]["sessions"] == 2
        assert per_project["/Users/foo/project-b"]["sessions"] == 1

    def test_per_project_shows_skill_usage(self, skill, sessions_multiple_projects):
        """Each project should show its skill usage."""
        output = generate_analysis_json(
            skills=[skill],
            agents=[],
            commands=[],
            hooks=[],
            sessions=sessions_multiple_projects,
            jsonl_stats={"total_sessions": 3, "total_prompts": 3, "skills_used": {"debugging": 2}, "agents_used": {}, "commands_used": {}, "missed_skills": {}, "missed_agents": {}, "missed_commands": {}, "total_success": 0, "total_failure": 0, "total_interrupted": 0, "total_compactions": 0},
            claude_md={"files_found": [], "content": {}},
            setup_profile=SetupProfile("low", "minimal", [], [], [], [], {}, {}, []),
            missed=[],
            feedback={},
        )

        per_project = output["per_project"]
        # Project A: debugging used in 1 of 2 sessions
        assert "skills_used" in per_project["/Users/foo/project-a"]
        assert per_project["/Users/foo/project-a"]["skills_used"]["debugging"] == 1
        # Project B: debugging used in 1 of 1 sessions
        assert per_project["/Users/foo/project-b"]["skills_used"]["debugging"] == 1


class TestPerProjectAgentUsage:
    """Test that per_project includes agent usage."""

    def test_per_project_shows_agent_usage(self):
        """Each project should show its agent usage."""
        agent = SkillOrAgent(
            name="reviewer",
            type="agent",
            description="Review code",
            triggers=["review"],
            source_path="/test/path",
            source_type="global",
        )

        s1 = SessionData(session_id="session-1")
        s1.project_path = "/Users/foo/project-a"
        s1.prompts = ["review code"]
        s1.agents_used = {"reviewer"}

        output = generate_analysis_json(
            skills=[],
            agents=[agent],
            commands=[],
            hooks=[],
            sessions=[s1],
            jsonl_stats={"total_sessions": 1, "total_prompts": 1, "skills_used": {}, "agents_used": {"reviewer": 1}, "commands_used": {}, "missed_skills": {}, "missed_agents": {}, "missed_commands": {}, "total_success": 0, "total_failure": 0, "total_interrupted": 0, "total_compactions": 0},
            claude_md={"files_found": [], "content": {}},
            setup_profile=SetupProfile("low", "minimal", [], [], [], [], {}, {}, []),
            missed=[],
            feedback={},
        )

        per_project = output["per_project"]
        assert "agents_used" in per_project["/Users/foo/project-a"]
        assert per_project["/Users/foo/project-a"]["agents_used"]["reviewer"] == 1


class TestProjectPathNotUnknown:
    """Regression: project_path must not default to 'unknown' when project is known."""

    def test_sessions_without_project_path_group_under_unknown(self):
        """Sessions with default project_path should group under 'unknown'."""
        from collect_usage import compute_per_project_breakdown

        s1 = SessionData(session_id="session-1")
        s1.prompts = ["hello"]
        s1.skills_used = set()
        # project_path NOT set - should default to "unknown"

        result = compute_per_project_breakdown([s1])
        assert "unknown" in result
        assert result["unknown"]["sessions"] == 1

    def test_sessions_with_project_path_group_correctly(self):
        """Sessions with explicit project_path should NOT group under 'unknown'."""
        from collect_usage import compute_per_project_breakdown

        s1 = SessionData(session_id="session-1")
        s1.project_path = "/Users/foo/my-project"
        s1.prompts = ["hello"]
        s1.skills_used = set()

        result = compute_per_project_breakdown([s1])
        assert "unknown" not in result
        assert "/Users/foo/my-project" in result
