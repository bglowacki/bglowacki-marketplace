"""Tests for missed opportunity detection with impact scoring (Story 2.3).

Tests detect_missed_opportunities, grouping by skill, impact score calculation,
and JSON output structure.
"""

import sys
from datetime import datetime, timedelta
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).parent.parent / "skills" / "observability-usage-collector" / "scripts"))
from collect_usage import (
    SkillOrAgent,
    SessionData,
    calculate_frequency_score,
    calculate_recency_score,
    calculate_impact_score,
    detect_missed_opportunities,
)


@pytest.fixture
def tdd_skill():
    return SkillOrAgent(
        name="test-driven-development",
        type="skill",
        description="Use TDD to write tests first",
        triggers=["TDD", "test driven", "write tests", "red green refactor"],
        source_path="/skills/tdd.md",
        source_type="global",
    )


@pytest.fixture
def debugging_skill():
    return SkillOrAgent(
        name="systematic-debugging",
        type="skill",
        description="Debug issues systematically",
        triggers=["systematic debugging", "root cause analysis", "investigate"],
        source_path="/skills/debug.md",
        source_type="global",
    )


# --- Task 3: Impact score calculation ---

class TestFrequencyScore:
    def test_zero_occurrences(self):
        assert calculate_frequency_score(0) == 0.0

    def test_one_occurrence(self):
        assert calculate_frequency_score(1) == pytest.approx(0.05)

    def test_ten_occurrences(self):
        assert calculate_frequency_score(10) == pytest.approx(0.5)

    def test_twenty_occurrences_caps_at_one(self):
        assert calculate_frequency_score(20) == 1.0

    def test_above_twenty_still_one(self):
        assert calculate_frequency_score(50) == 1.0


class TestRecencyScore:
    def test_today(self):
        assert calculate_recency_score(0, 7) == pytest.approx(1.0)

    def test_half_period(self):
        assert calculate_recency_score(3, 7) == pytest.approx(1.0 - 3/7)

    def test_full_period(self):
        assert calculate_recency_score(7, 7) == pytest.approx(0.0)

    def test_beyond_period_clamps(self):
        # Should not go negative
        result = calculate_recency_score(10, 7)
        assert result >= 0.0


class TestImpactScore:
    def test_formula(self):
        # impact = confidence*0.4 + frequency*0.4 + recency*0.2
        result = calculate_impact_score(0.85, 0.5, 0.7)
        expected = (0.85 * 0.4) + (0.5 * 0.4) + (0.7 * 0.2)
        assert result == pytest.approx(expected)

    def test_all_ones(self):
        assert calculate_impact_score(1.0, 1.0, 1.0) == pytest.approx(1.0)

    def test_all_zeros(self):
        assert calculate_impact_score(0.0, 0.0, 0.0) == pytest.approx(0.0)


# --- Tasks 1 & 2: Detection and grouping ---

class TestDetectMissedOpportunities:
    def test_no_sessions_returns_empty(self, tdd_skill):
        result = detect_missed_opportunities([], [tdd_skill])
        assert result == []

    def test_skill_invoked_not_missed(self, tdd_skill):
        session = SessionData(
            session_id="s1",
            prompts=["help me write tests using test driven development"],
            skills_used={"test-driven-development"},
        )
        result = detect_missed_opportunities([session], [tdd_skill])
        assert len(result) == 0

    def test_skill_matched_but_not_invoked_is_missed(self, tdd_skill):
        session = SessionData(
            session_id="s1",
            prompts=["help me write tests using test driven development"],
            skills_used=set(),
            session_date=datetime.now(),
        )
        result = detect_missed_opportunities([session], [tdd_skill])
        assert len(result) >= 1
        assert result[0]["skill_name"] == "test-driven-development"

    def test_grouped_by_skill(self, tdd_skill):
        sessions = [
            SessionData(
                session_id="s1",
                prompts=["help me write tests using test driven development"],
                skills_used=set(),
                session_date=datetime.now(),
            ),
            SessionData(
                session_id="s2",
                prompts=["I want to write tests using test driven approach"],
                skills_used=set(),
                session_date=datetime.now(),
            ),
        ]
        result = detect_missed_opportunities(sessions, [tdd_skill])
        # Should be one entry grouped by skill
        tdd_entries = [r for r in result if r["skill_name"] == "test-driven-development"]
        assert len(tdd_entries) == 1
        assert tdd_entries[0]["occurrence_count"] == 2

    def test_example_prompts_limited_to_three(self, tdd_skill):
        sessions = [
            SessionData(
                session_id=f"s{i}",
                prompts=["help me write tests using test driven development"],
                skills_used=set(),
                session_date=datetime.now(),
            )
            for i in range(5)
        ]
        result = detect_missed_opportunities(sessions, [tdd_skill])
        tdd = [r for r in result if r["skill_name"] == "test-driven-development"][0]
        assert len(tdd["example_prompts"]) <= 3

    def test_includes_impact_score(self, tdd_skill):
        session = SessionData(
            session_id="s1",
            prompts=["help me write tests using test driven development"],
            skills_used=set(),
            session_date=datetime.now(),
        )
        result = detect_missed_opportunities([session], [tdd_skill], analysis_period_days=7)
        assert len(result) >= 1
        assert "impact_score" in result[0]
        assert 0.0 <= result[0]["impact_score"] <= 1.0

    def test_includes_confidence(self, tdd_skill):
        session = SessionData(
            session_id="s1",
            prompts=["help me write tests using test driven development"],
            skills_used=set(),
            session_date=datetime.now(),
        )
        result = detect_missed_opportunities([session], [tdd_skill])
        assert len(result) >= 1
        assert "confidence" in result[0]

    def test_high_confidence_filtering(self, tdd_skill):
        session = SessionData(
            session_id="s1",
            prompts=["help me write tests using test driven development"],
            skills_used=set(),
            session_date=datetime.now(),
        )
        # Only matches > 80% confidence should be included
        result = detect_missed_opportunities([session], [tdd_skill])
        for r in result:
            assert r["confidence"] > 0.80

    def test_sorted_by_impact_descending(self, tdd_skill, debugging_skill):
        sessions = [
            SessionData(
                session_id=f"s{i}",
                prompts=["help me write tests using test driven development"],
                skills_used=set(),
                session_date=datetime.now(),
            )
            for i in range(5)
        ] + [
            SessionData(
                session_id="s_debug",
                prompts=["I need systematic debugging with root cause analysis"],
                skills_used=set(),
                session_date=datetime.now() - timedelta(days=5),
            ),
        ]
        result = detect_missed_opportunities(sessions, [tdd_skill, debugging_skill], analysis_period_days=7)
        if len(result) >= 2:
            scores = [r["impact_score"] for r in result]
            assert scores == sorted(scores, reverse=True)

    def test_multiple_skills_grouped_separately(self, tdd_skill, debugging_skill):
        session = SessionData(
            session_id="s1",
            prompts=[
                "help me write tests using test driven development",
                "I need systematic debugging with root cause analysis",
            ],
            skills_used=set(),
            session_date=datetime.now(),
        )
        result = detect_missed_opportunities([session], [tdd_skill, debugging_skill])
        skill_names = [r["skill_name"] for r in result]
        # Each skill should appear at most once (grouped)
        assert len(skill_names) == len(set(skill_names))

    def test_sessions_affected_tracked(self, tdd_skill):
        sessions = [
            SessionData(
                session_id="s1",
                prompts=["help me write tests using test driven development"],
                skills_used=set(),
                session_date=datetime.now(),
            ),
            SessionData(
                session_id="s2",
                prompts=["I want to write tests using test driven approach"],
                skills_used=set(),
                session_date=datetime.now(),
            ),
        ]
        result = detect_missed_opportunities(sessions, [tdd_skill])
        tdd = [r for r in result if r["skill_name"] == "test-driven-development"][0]
        assert "sessions_affected" in tdd
        assert set(tdd["sessions_affected"]) == {"s1", "s2"}
