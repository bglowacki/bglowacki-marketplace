"""Tests for JSON output metadata compliance (Story 1.2, AC-5).

Requirements:
- Schema version starts with "3." (v3.x compatible)
- Collection timestamp is included
- Total session count is included
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
def minimal_output():
    """Generate minimal output for metadata testing."""
    skill = SkillOrAgent(
        name="test",
        type="skill",
        description="Test skill",
        triggers=["test"],
        source_path="/test/path",
        source_type="global",
    )

    session = SessionData(session_id="test-1")
    session.prompts = ["hello"]
    session.skills_used = set()

    return generate_analysis_json(
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


class TestSchemaVersion:
    """Test that schema version is v3.x compliant."""

    def test_schema_has_version_field(self, minimal_output):
        """_schema should have version field."""
        assert "_schema" in minimal_output
        assert "version" in minimal_output["_schema"]

    def test_schema_version_is_3_x(self, minimal_output):
        """Schema version should be in v3.x series."""
        version = minimal_output["_schema"]["version"]
        assert version.startswith("3."), f"Expected version 3.x, got {version}"


class TestCollectionTimestamp:
    """Test that collection timestamp is included."""

    def test_schema_has_collection_timestamp(self, minimal_output):
        """_schema should include collection_timestamp."""
        assert "collection_timestamp" in minimal_output["_schema"]

    def test_collection_timestamp_is_iso_format(self, minimal_output):
        """collection_timestamp should be in ISO format."""
        timestamp = minimal_output["_schema"]["collection_timestamp"]
        # Should be parseable as ISO datetime
        try:
            datetime.fromisoformat(timestamp)
        except (ValueError, TypeError) as e:
            pytest.fail(f"collection_timestamp '{timestamp}' is not valid ISO format: {e}")

    def test_collection_timestamp_is_recent(self, minimal_output):
        """collection_timestamp should be approximately now."""
        timestamp = datetime.fromisoformat(minimal_output["_schema"]["collection_timestamp"])
        now = datetime.now()
        # Should be within last minute
        diff = abs((now - timestamp).total_seconds())
        assert diff < 60, f"Timestamp is {diff}s old, should be recent"


class TestTotalSessions:
    """Test that total_sessions count is included."""

    def test_stats_has_total_sessions(self, minimal_output):
        """stats should include total_sessions."""
        assert "stats" in minimal_output
        assert "total_sessions" in minimal_output["stats"]

    def test_total_sessions_matches_session_count(self):
        """total_sessions should match the number of sessions analyzed."""
        skill = SkillOrAgent(
            name="test",
            type="skill",
            description="Test skill",
            triggers=["test"],
            source_path="/test/path",
            source_type="global",
        )

        sessions = [
            SessionData(session_id="test-1"),
            SessionData(session_id="test-2"),
            SessionData(session_id="test-3"),
        ]
        for s in sessions:
            s.prompts = ["hello"]
            s.skills_used = set()

        output = generate_analysis_json(
            skills=[skill],
            agents=[],
            commands=[],
            hooks=[],
            sessions=sessions,
            jsonl_stats={"total_sessions": 3, "total_prompts": 3, "skills_used": {}, "agents_used": {}, "commands_used": {}, "missed_skills": {}, "missed_agents": {}, "missed_commands": {}, "total_success": 0, "total_failure": 0, "total_interrupted": 0, "total_compactions": 0},
            claude_md={"files_found": [], "content": {}},
            setup_profile=SetupProfile("low", "minimal", [], [], [], [], {}, {}, []),
            missed=[],
            feedback={},
        )

        assert output["stats"]["total_sessions"] == 3


class TestSchemaDescription:
    """Test that schema description mentions v3.0 compliance."""

    def test_schema_has_description(self, minimal_output):
        """_schema should have description field."""
        assert "description" in minimal_output["_schema"]
