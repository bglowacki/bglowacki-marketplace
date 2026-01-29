"""Tests for skill classification logic (Story 1.2, AC-1).

Classification rules:
- ACTIVE: Skill was invoked in the period
- DORMANT: Triggers matched but skill not invoked
- UNUSED: No matching triggers found
"""

import sys
from pathlib import Path
from datetime import datetime

import pytest

sys.path.insert(0, str(Path(__file__).parent.parent / "skills" / "observability-usage-collector" / "scripts"))
from collect_usage import (
    SkillOrAgent,
    SessionData,
    SkillClassification,
    classify_skill,
    find_matches,
)


@pytest.fixture
def debugging_skill():
    """A skill that would match debugging-related prompts."""
    return SkillOrAgent(
        name="systematic-debugging",
        type="skill",
        description="Debug issues systematically",
        triggers=["debug", "debugging", "bug", "issue", "error", "fix"],
        source_path="/test/path",
        source_type="global",
    )


@pytest.fixture
def tdd_skill():
    """A skill for test-driven development."""
    return SkillOrAgent(
        name="test-driven-development",
        type="skill",
        description="TDD workflow",
        triggers=["test driven", "write tests first", "red green refactor"],
        source_path="/test/path",
        source_type="global",
    )


@pytest.fixture
def unused_skill():
    """A skill with triggers unlikely to match."""
    return SkillOrAgent(
        name="kubernetes-deployment",
        type="skill",
        description="Deploy to K8s",
        triggers=["kubernetes", "helm", "kubectl", "k8s deploy"],
        source_path="/test/path",
        source_type="global",
    )


@pytest.fixture
def session_with_debugging_invoked():
    """Session where debugging skill was actually invoked."""
    session = SessionData(session_id="test-1")
    session.prompts = ["Help me debug this error in the code"]
    session.skills_used = {"systematic-debugging"}
    return session


@pytest.fixture
def session_with_debugging_triggers_only():
    """Session where debugging triggers matched but skill wasn't invoked."""
    session = SessionData(session_id="test-2")
    session.prompts = ["Help me debug this error in the code"]
    session.skills_used = set()  # Skill not invoked
    return session


@pytest.fixture
def session_unrelated():
    """Session with no related prompts."""
    session = SessionData(session_id="test-3")
    session.prompts = ["Write a hello world function"]
    session.skills_used = set()
    return session


class TestSkillClassificationEnum:
    """Test SkillClassification enum/constants exist."""

    def test_active_constant_exists(self):
        """ACTIVE classification should exist."""
        assert SkillClassification.ACTIVE == "active"

    def test_dormant_constant_exists(self):
        """DORMANT classification should exist."""
        assert SkillClassification.DORMANT == "dormant"

    def test_unused_constant_exists(self):
        """UNUSED classification should exist."""
        assert SkillClassification.UNUSED == "unused"


class TestClassifySkillActive:
    """Test ACTIVE classification - skill was invoked."""

    def test_skill_invoked_returns_active(self, debugging_skill, session_with_debugging_invoked):
        """When skill was invoked in session, classification should be ACTIVE."""
        result = classify_skill(debugging_skill, [session_with_debugging_invoked])
        assert result == SkillClassification.ACTIVE

    def test_skill_invoked_multiple_sessions(self, debugging_skill, session_with_debugging_invoked, session_unrelated):
        """If invoked in ANY session, classification should be ACTIVE."""
        result = classify_skill(debugging_skill, [session_unrelated, session_with_debugging_invoked])
        assert result == SkillClassification.ACTIVE


class TestClassifySkillDormant:
    """Test DORMANT classification - triggers matched but not invoked."""

    def test_triggers_matched_not_invoked_returns_dormant(self, debugging_skill, session_with_debugging_triggers_only):
        """When triggers match but skill not invoked, should be DORMANT."""
        result = classify_skill(debugging_skill, [session_with_debugging_triggers_only])
        assert result == SkillClassification.DORMANT

    def test_triggers_matched_in_some_sessions_not_invoked(self, debugging_skill, session_with_debugging_triggers_only, session_unrelated):
        """If triggers match in ANY session but never invoked, should be DORMANT."""
        result = classify_skill(debugging_skill, [session_unrelated, session_with_debugging_triggers_only])
        assert result == SkillClassification.DORMANT


class TestClassifySkillUnused:
    """Test UNUSED classification - no matching triggers found."""

    def test_no_triggers_matched_returns_unused(self, unused_skill, session_unrelated):
        """When no triggers match in any session, should be UNUSED."""
        result = classify_skill(unused_skill, [session_unrelated])
        assert result == SkillClassification.UNUSED

    def test_empty_sessions_returns_unused(self, debugging_skill):
        """With no sessions, skill should be UNUSED."""
        result = classify_skill(debugging_skill, [])
        assert result == SkillClassification.UNUSED


class TestClassifySkillPriority:
    """Test classification priority: ACTIVE > DORMANT > UNUSED."""

    def test_active_takes_precedence_over_dormant(self, debugging_skill, session_with_debugging_invoked, session_with_debugging_triggers_only):
        """If invoked in ANY session, should be ACTIVE even if other sessions only had trigger matches."""
        result = classify_skill(debugging_skill, [session_with_debugging_triggers_only, session_with_debugging_invoked])
        assert result == SkillClassification.ACTIVE


class TestClassifyAgent:
    """Test that agents are also classified (same logic)."""

    def test_agent_classification_uses_agents_used(self):
        """Agent classification should check agents_used field."""
        from collect_usage import classify_agent

        agent = SkillOrAgent(
            name="code-reviewer",
            type="agent",
            description="Review code",
            triggers=["review", "code review", "pull request"],
            source_path="/test/path",
            source_type="global",
        )

        session = SessionData(session_id="test")
        session.prompts = ["please review my code"]
        session.agents_used = {"code-reviewer"}

        result = classify_agent(agent, [session])
        assert result == SkillClassification.ACTIVE

    def test_agent_dormant_when_triggers_match_not_invoked(self):
        """Agent should be DORMANT when triggers match but not invoked."""
        from collect_usage import classify_agent

        agent = SkillOrAgent(
            name="code-reviewer",
            type="agent",
            description="Review code",
            triggers=["review", "code review", "pull request"],
            source_path="/test/path",
            source_type="global",
        )

        session = SessionData(session_id="test")
        session.prompts = ["please review my code for the pull request"]
        session.agents_used = set()  # Not invoked

        result = classify_agent(agent, [session])
        assert result == SkillClassification.DORMANT


class TestOutputStructureClassification:
    """Test that classification field is added to output structure (AC-1 completion)."""

    def test_discovery_skills_have_classification_field(self):
        """discovery.skills should include classification field."""
        from collect_usage import generate_analysis_json, SetupProfile, classify_skill

        skill = SkillOrAgent(
            name="test-skill",
            type="skill",
            description="A test skill",
            triggers=["test", "testing"],
            source_path="/test/path",
            source_type="global",
        )

        session = SessionData(session_id="test")
        session.prompts = ["hello world"]
        session.skills_used = set()

        # Minimal mock setup
        output = generate_analysis_json(
            skills=[skill],
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

        assert "discovery" in output
        assert "skills" in output["discovery"]
        assert len(output["discovery"]["skills"]) == 1
        assert "classification" in output["discovery"]["skills"][0]
        assert output["discovery"]["skills"][0]["classification"] == SkillClassification.UNUSED

    def test_discovery_agents_have_classification_field(self):
        """discovery.agents should include classification field."""
        from collect_usage import generate_analysis_json, SetupProfile

        agent = SkillOrAgent(
            name="test-agent",
            type="agent",
            description="A test agent",
            triggers=["test", "testing"],
            source_path="/test/path",
            source_type="global",
        )

        session = SessionData(session_id="test")
        session.prompts = ["hello world"]
        session.agents_used = {"test-agent"}

        output = generate_analysis_json(
            skills=[],
            agents=[agent],
            commands=[],
            hooks=[],
            sessions=[session],
            jsonl_stats={"total_sessions": 1, "total_prompts": 1, "skills_used": {}, "agents_used": {"test-agent": 1}, "commands_used": {}, "missed_skills": {}, "missed_agents": {}, "missed_commands": {}, "total_success": 0, "total_failure": 0, "total_interrupted": 0, "total_compactions": 0},
            claude_md={"files_found": [], "content": {}},
            setup_profile=SetupProfile("low", "minimal", [], [], [], [], {}, {}, []),
            missed=[],
            feedback={},
        )

        assert "agents" in output["discovery"]
        assert len(output["discovery"]["agents"]) == 1
        assert "classification" in output["discovery"]["agents"][0]
        assert output["discovery"]["agents"][0]["classification"] == SkillClassification.ACTIVE
