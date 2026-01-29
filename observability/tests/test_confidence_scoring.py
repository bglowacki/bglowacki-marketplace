"""Tests for confidence scoring (Story 2.2).

Tests MatchResult dataclass and confidence calculation functions.
"""

import sys
from dataclasses import fields
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).parent.parent / "skills" / "observability-usage-collector" / "scripts"))
from collect_usage import (
    SkillOrAgent,
    MatchResult,
    calculate_length_score,
    calculate_specificity_score,
    calculate_position_score,
    calculate_confidence,
    find_matches,
)


@pytest.fixture
def sample_skill():
    return SkillOrAgent(
        name="systematic-debugging",
        type="skill",
        description="Debug issues systematically",
        triggers=["debug", "debugging", "bug", "issue", "error", "fix"],
        source_path="/test/path",
        source_type="global",
    )


class TestMatchResultDataclass:
    """AC-4: MatchResult dataclass."""

    def test_has_required_fields(self):
        skill = SkillOrAgent(
            name="test", type="skill", description="t",
            triggers=[], source_path="/t", source_type="global",
        )
        result = MatchResult(skill=skill, matched_triggers=["debug"], confidence=0.85)
        assert result.skill == skill
        assert result.matched_triggers == ["debug"]
        assert result.confidence == 0.85

    def test_to_dict(self):
        skill = SkillOrAgent(
            name="my-skill", type="skill", description="t",
            triggers=[], source_path="/t", source_type="global",
        )
        result = MatchResult(skill=skill, matched_triggers=["debug", "error"], confidence=0.92)
        d = result.to_dict()
        assert d["skill_name"] == "my-skill"
        assert d["matched_triggers"] == ["debug", "error"]
        assert d["confidence"] == 0.92

    def test_is_dataclass(self):
        field_names = {f.name for f in fields(MatchResult)}
        assert "skill" in field_names
        assert "matched_triggers" in field_names
        assert "confidence" in field_names


class TestLengthScore:
    """AC-1: length_score = min(100, trigger_length * 10) / 100."""

    @pytest.mark.parametrize("trigger,expected", [
        ("debug", 0.5),       # 5 * 10 = 50 / 100
        ("debugging", 0.9),   # 9 * 10 = 90 / 100
        ("test driven", 1.0), # 11 * 10 = 110 -> min(100,110) / 100
        ("a", 0.1),           # 1 * 10 = 10 / 100
        ("systematic-debugging", 1.0),  # 21 chars -> capped at 1.0
    ])
    def test_length_score(self, trigger, expected):
        assert calculate_length_score(trigger) == pytest.approx(expected)


class TestSpecificityScore:
    """AC-1: specificity_score = 1.0 (multi-word) or 0.5 (single word)."""

    @pytest.mark.parametrize("trigger,expected", [
        ("debug", 0.5),
        ("code review", 1.0),
        ("test-driven", 1.0),  # hyphen counts as multi-word
        ("TDD", 0.5),
    ])
    def test_specificity_score(self, trigger, expected):
        assert calculate_specificity_score(trigger) == expected


class TestPositionScore:
    """AC-1: position_score = 1.0 at 0-20, linear decay to 0.0 at 200."""

    @pytest.mark.parametrize("position,expected", [
        (0, 1.0),
        (10, 1.0),
        (20, 1.0),
        (110, 0.5),   # midpoint of 20-200 range
        (200, 0.0),
        (300, 0.0),   # beyond 200 still 0
    ])
    def test_position_score(self, position, expected):
        assert calculate_position_score(position) == pytest.approx(expected)


class TestCalculateConfidence:
    """AC-1: confidence = (length + specificity + position) / 3."""

    def test_high_confidence(self):
        # "code review" at position 0: length=1.0, specificity=1.0, position=1.0 => 1.0
        assert calculate_confidence("code review", 0) == pytest.approx(1.0)

    def test_medium_confidence(self):
        # "debug" at position 110: length=0.5, specificity=0.5, position=0.5 => 0.5
        assert calculate_confidence("debug", 110) == pytest.approx(0.5)

    def test_low_confidence(self):
        # "a" at position 200: length=0.1, specificity=0.5, position=0.0 => 0.2
        assert calculate_confidence("a", 200) == pytest.approx(0.2)


class TestFindMatchesConfidence:
    """AC-2: find_matches() returns MatchResult with confidence > 0.80 threshold."""

    @pytest.fixture
    def high_conf_skill(self):
        """Skill with multi-word triggers that produce >0.80 confidence."""
        return SkillOrAgent(
            name="code-reviewer", type="skill", description="Review code",
            triggers=["code review", "pull request", "review changes"],
            source_path="/t", source_type="global",
        )

    def test_returns_match_results(self, high_conf_skill):
        prompt = "please do a code review of my pull request"
        matches = find_matches(prompt, [high_conf_skill])
        assert len(matches) >= 1
        assert isinstance(matches[0], MatchResult)

    def test_match_result_has_confidence(self, high_conf_skill):
        prompt = "please do a code review of my pull request"
        matches = find_matches(prompt, [high_conf_skill])
        assert len(matches) >= 1
        assert hasattr(matches[0], 'confidence')
        assert 0.0 <= matches[0].confidence <= 1.0

    def test_threshold_filters_low_confidence(self):
        """Matches with confidence <= 0.80 should be filtered out."""
        skill = SkillOrAgent(
            name="test-skill", type="skill", description="t",
            triggers=["debug", "error", "issue", "fix"],
            source_path="/t", source_type="global",
        )
        # Place triggers far in prompt to get low position score
        long_prefix = "x " * 200  # ~400 chars
        prompt = long_prefix + "debug error"
        matches = find_matches(prompt, [skill])
        # Position score ~0, short triggers -> confidence below threshold
        assert len(matches) == 0

    def test_high_confidence_passes_threshold(self, high_conf_skill):
        """Multi-word triggers at start of prompt should pass threshold."""
        prompt = "code review my pull request please"
        matches = find_matches(prompt, [high_conf_skill])
        assert len(matches) >= 1
        assert matches[0].confidence > 0.80

    def test_low_confidence_without_threshold(self, sample_skill):
        """With min_confidence=0, all trigger-matched items are returned."""
        prompt = "debug this error"
        matches = find_matches(prompt, [sample_skill], min_confidence=0.0)
        assert len(matches) >= 1
        assert isinstance(matches[0], MatchResult)
        assert matches[0].skill == sample_skill

    def test_backward_compatible_access(self, high_conf_skill):
        """MatchResult should support skill and matched_triggers access."""
        prompt = "code review my pull request"
        matches = find_matches(prompt, [high_conf_skill])
        if matches:
            m = matches[0]
            assert m.skill == high_conf_skill
            assert isinstance(m.matched_triggers, list)
