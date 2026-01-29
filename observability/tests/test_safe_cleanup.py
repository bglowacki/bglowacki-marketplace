"""Tests for Safe Cleanup Mode (Story 3.4).

Requirements:
- AC-1: Default no deletions - cleanup mode OFF by default, unused shown informational only
- AC-2: Cleanup mode requirements - zero triggers + no deps + >=20 sessions + REVIEW CAREFULLY
- AC-3: Rollback guidance included with deletion recommendations
- AC-4: Insufficient data warning when <20 sessions analyzed
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


def _make_jsonl_stats(total_sessions=25, total_prompts=100):
    return {
        "total_sessions": total_sessions,
        "total_prompts": total_prompts,
        "skills_used": {},
        "agents_used": {},
        "commands_used": {},
        "missed_skills": {},
        "missed_agents": {},
        "missed_commands": {},
        "total_success": 0,
        "total_failure": 0,
        "total_interrupted": 0,
        "total_compactions": 0,
    }


def _make_sessions(count=25):
    sessions = []
    for i in range(count):
        s = SessionData(session_id=f"session-{i}")
        s.prompts = [f"prompt {i}"]
        s.skills_used = set()
        sessions.append(s)
    return sessions


@pytest.fixture
def unused_skill():
    return SkillOrAgent(
        name="unused-skill",
        type="skill",
        description="A skill nobody uses",
        triggers=["unused trigger"],
        source_path="/test/unused",
        source_type="global",
    )


@pytest.fixture
def setup_profile():
    return SetupProfile("low", "minimal", [], [], [], [], {}, {}, [])


class TestCleanupModeFlag:
    """AC-1: Cleanup mode detection in JSON output."""

    def test_cleanup_mode_default_off(self, unused_skill, setup_profile):
        """When cleanup_mode not specified, defaults to False in output."""
        output = generate_analysis_json(
            skills=[unused_skill],
            agents=[],
            commands=[],
            hooks=[],
            sessions=_make_sessions(1),
            jsonl_stats=_make_jsonl_stats(1, 1),
            claude_md={"files_found": [], "content": {}},
            setup_profile=setup_profile,
            missed=[],
            feedback={},
        )
        assert output["_schema"]["cleanup_mode"] is False

    def test_cleanup_mode_on(self, unused_skill, setup_profile):
        """When cleanup_mode=True, output reflects it."""
        output = generate_analysis_json(
            skills=[unused_skill],
            agents=[],
            commands=[],
            hooks=[],
            sessions=_make_sessions(1),
            jsonl_stats=_make_jsonl_stats(1, 1),
            claude_md={"files_found": [], "content": {}},
            setup_profile=setup_profile,
            missed=[],
            feedback={},
            cleanup_mode=True,
        )
        assert output["_schema"]["cleanup_mode"] is True


class TestSafetyClassification:
    """AC-2: Safety classification for cleanup suggestions."""

    def test_cleanup_candidates_only_with_cleanup_mode(self, unused_skill, setup_profile):
        """Cleanup candidates only appear when cleanup_mode=True."""
        output = generate_analysis_json(
            skills=[unused_skill],
            agents=[],
            commands=[],
            hooks=[],
            sessions=_make_sessions(25),
            jsonl_stats=_make_jsonl_stats(25, 100),
            claude_md={"files_found": [], "content": {}},
            setup_profile=setup_profile,
            missed=[],
            feedback={},
            cleanup_mode=False,
        )
        findings = output.get("pre_computed_findings", {})
        assert "cleanup_candidates" not in findings or len(findings.get("cleanup_candidates", [])) == 0

    def test_cleanup_candidates_with_cleanup_mode_and_sufficient_sessions(self, unused_skill, setup_profile):
        """When cleanup_mode=True and >=20 sessions, unused skills become cleanup candidates."""
        output = generate_analysis_json(
            skills=[unused_skill],
            agents=[],
            commands=[],
            hooks=[],
            sessions=_make_sessions(25),
            jsonl_stats=_make_jsonl_stats(25, 100),
            claude_md={"files_found": [], "content": {}},
            setup_profile=setup_profile,
            missed=[],
            feedback={},
            cleanup_mode=True,
        )
        findings = output.get("pre_computed_findings", {})
        assert "cleanup_candidates" in findings
        candidates = findings["cleanup_candidates"]
        assert len(candidates) >= 1
        assert candidates[0]["name"] == "unused-skill"
        assert candidates[0]["safety_level"] == "REVIEW CAREFULLY"

    def test_cleanup_candidate_has_required_fields(self, unused_skill, setup_profile):
        """Each cleanup candidate has name, type, source, safety_level, session_count, rollback_guidance."""
        output = generate_analysis_json(
            skills=[unused_skill],
            agents=[],
            commands=[],
            hooks=[],
            sessions=_make_sessions(25),
            jsonl_stats=_make_jsonl_stats(25, 100),
            claude_md={"files_found": [], "content": {}},
            setup_profile=setup_profile,
            missed=[],
            feedback={},
            cleanup_mode=True,
        )
        candidate = output["pre_computed_findings"]["cleanup_candidates"][0]
        assert "name" in candidate
        assert "type" in candidate
        assert "source" in candidate
        assert "safety_level" in candidate
        assert "session_count" in candidate
        assert "rollback_guidance" in candidate

    def test_no_cleanup_for_skills_with_trigger_matches(self, setup_profile):
        """Skills with trigger matches should NOT be cleanup candidates."""
        matched_skill = SkillOrAgent(
            name="matched-skill",
            type="skill",
            description="A skill with matches",
            triggers=["test trigger"],
            source_path="/test/matched",
            source_type="global",
        )
        stats = _make_jsonl_stats(25, 100)
        stats["missed_skills"] = {"matched-skill": 3}

        output = generate_analysis_json(
            skills=[matched_skill],
            agents=[],
            commands=[],
            hooks=[],
            sessions=_make_sessions(25),
            jsonl_stats=stats,
            claude_md={"files_found": [], "content": {}},
            setup_profile=setup_profile,
            missed=[],
            feedback={},
            cleanup_mode=True,
        )
        findings = output.get("pre_computed_findings", {})
        candidates = findings.get("cleanup_candidates", [])
        names = [c["name"] for c in candidates]
        assert "matched-skill" not in names


class TestInsufficientData:
    """AC-4: Insufficient data warning when <20 sessions."""

    def test_insufficient_data_flag_below_threshold(self, unused_skill, setup_profile):
        """When cleanup_mode=True but <20 sessions, insufficient_data is flagged."""
        output = generate_analysis_json(
            skills=[unused_skill],
            agents=[],
            commands=[],
            hooks=[],
            sessions=_make_sessions(10),
            jsonl_stats=_make_jsonl_stats(10, 50),
            claude_md={"files_found": [], "content": {}},
            setup_profile=setup_profile,
            missed=[],
            feedback={},
            cleanup_mode=True,
        )
        findings = output.get("pre_computed_findings", {})
        assert findings.get("cleanup_insufficient_data") is True
        assert len(findings.get("cleanup_candidates", [])) == 0

    def test_no_insufficient_data_flag_above_threshold(self, unused_skill, setup_profile):
        """When >=20 sessions, no insufficient data flag."""
        output = generate_analysis_json(
            skills=[unused_skill],
            agents=[],
            commands=[],
            hooks=[],
            sessions=_make_sessions(25),
            jsonl_stats=_make_jsonl_stats(25, 100),
            claude_md={"files_found": [], "content": {}},
            setup_profile=setup_profile,
            missed=[],
            feedback={},
            cleanup_mode=True,
        )
        findings = output.get("pre_computed_findings", {})
        assert findings.get("cleanup_insufficient_data") is not True

    def test_no_insufficient_data_when_cleanup_off(self, unused_skill, setup_profile):
        """When cleanup_mode=False, no insufficient data flag regardless of session count."""
        output = generate_analysis_json(
            skills=[unused_skill],
            agents=[],
            commands=[],
            hooks=[],
            sessions=_make_sessions(5),
            jsonl_stats=_make_jsonl_stats(5, 20),
            claude_md={"files_found": [], "content": {}},
            setup_profile=setup_profile,
            missed=[],
            feedback={},
        )
        findings = output.get("pre_computed_findings", {})
        assert findings.get("cleanup_insufficient_data") is not True


class TestRollbackGuidance:
    """AC-3: Rollback guidance included with cleanup candidates."""

    def test_global_skill_rollback_guidance(self, setup_profile):
        """Global skills get marketplace reinstall guidance."""
        skill = SkillOrAgent(
            name="global-skill",
            type="skill",
            description="A global skill",
            triggers=["global trigger"],
            source_path="/home/user/.claude/skills/global-skill",
            source_type="global",
        )
        output = generate_analysis_json(
            skills=[skill],
            agents=[],
            commands=[],
            hooks=[],
            sessions=_make_sessions(25),
            jsonl_stats=_make_jsonl_stats(25, 100),
            claude_md={"files_found": [], "content": {}},
            setup_profile=setup_profile,
            missed=[],
            feedback={},
            cleanup_mode=True,
        )
        candidate = output["pre_computed_findings"]["cleanup_candidates"][0]
        assert "marketplace" in candidate["rollback_guidance"].lower() or "reinstall" in candidate["rollback_guidance"].lower()

    def test_project_skill_rollback_guidance(self, setup_profile):
        """Project skills get git restore guidance."""
        skill = SkillOrAgent(
            name="project-skill",
            type="skill",
            description="A project skill",
            triggers=["project trigger"],
            source_path="/project/.claude/skills/project-skill",
            source_type="project",
        )
        output = generate_analysis_json(
            skills=[skill],
            agents=[],
            commands=[],
            hooks=[],
            sessions=_make_sessions(25),
            jsonl_stats=_make_jsonl_stats(25, 100),
            claude_md={"files_found": [], "content": {}},
            setup_profile=setup_profile,
            missed=[],
            feedback={},
            cleanup_mode=True,
        )
        candidate = output["pre_computed_findings"]["cleanup_candidates"][0]
        assert "git" in candidate["rollback_guidance"].lower()

    def test_plugin_skill_rollback_guidance(self, setup_profile):
        """Plugin skills get plugin reinstall guidance."""
        skill = SkillOrAgent(
            name="plugin-skill",
            type="skill",
            description="A plugin skill",
            triggers=["plugin trigger"],
            source_path="/project/.claude-plugins/my-plugin/skills/plugin-skill",
            source_type="plugin:my-plugin",
        )
        output = generate_analysis_json(
            skills=[skill],
            agents=[],
            commands=[],
            hooks=[],
            sessions=_make_sessions(25),
            jsonl_stats=_make_jsonl_stats(25, 100),
            claude_md={"files_found": [], "content": {}},
            setup_profile=setup_profile,
            missed=[],
            feedback={},
            cleanup_mode=True,
        )
        candidate = output["pre_computed_findings"]["cleanup_candidates"][0]
        assert "plugin" in candidate["rollback_guidance"].lower()
