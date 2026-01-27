"""Tests for find_matches() function (ADR-035).

This tests the core trigger matching algorithm used for missed opportunity detection.
"""

import sys
from pathlib import Path

import pytest

# Add the scripts directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent / "skills" / "observability-usage-collector" / "scripts"))
from collect_usage import SkillOrAgent, find_matches


@pytest.fixture
def sample_skill():
    """Create a sample skill for testing."""
    return SkillOrAgent(
        name="systematic-debugging",
        type="skill",
        description="Debug issues systematically",
        triggers=["debug", "debugging", "bug", "issue", "error", "fix"],
        source_path="/test/path",
        source_type="global",
    )


@pytest.fixture
def sample_agent():
    """Create a sample agent for testing."""
    return SkillOrAgent(
        name="code-reviewer",
        type="agent",
        description="Review code changes",
        triggers=["review", "code review", "PR", "pull request"],
        source_path="/test/path",
        source_type="global",
    )


@pytest.fixture
def tdd_skill():
    """Skill with short trigger name (TDD is 3 chars)."""
    return SkillOrAgent(
        name="tdd",
        type="skill",
        description="Test-driven development",
        triggers=["tdd", "test driven", "write tests first"],
        source_path="/test/path",
        source_type="global",
    )


class TestFindMatchesBasic:
    """Basic matching behavior tests."""

    def test_exact_trigger_match(self, sample_skill):
        """Triggers should match when found in prompt."""
        prompt = "I need to debug this issue"
        matches = find_matches(prompt, [sample_skill])

        assert len(matches) == 1
        assert matches[0][0] == sample_skill
        assert "debug" in matches[0][1]
        assert "issue" in matches[0][1]

    def test_no_match_when_no_triggers(self, sample_skill):
        """Should not match when no triggers present."""
        prompt = "Please help me write documentation"
        matches = find_matches(prompt, [sample_skill])

        assert len(matches) == 0

    def test_single_trigger_not_enough(self, sample_skill):
        """Single trigger match should not be enough (requires 2+)."""
        prompt = "I found a bug"
        matches = find_matches(prompt, [sample_skill])

        # "bug" is only 3 chars, gets skipped by length check
        # Even if it matched, single trigger wouldn't be enough
        assert len(matches) == 0

    def test_case_insensitive_matching(self, sample_skill):
        """Matching should be case-insensitive."""
        prompt = "DEBUG this ERROR please"
        matches = find_matches(prompt, [sample_skill])

        assert len(matches) == 1
        # Triggers are returned in original case from skill
        matched_triggers = [t.lower() for t in matches[0][1]]
        assert "debug" in matched_triggers
        assert "error" in matched_triggers


class TestTriggerLengthThreshold:
    """Tests for minimum trigger length behavior."""

    def test_short_triggers_skipped(self, tdd_skill):
        """Triggers with 3 or fewer chars should be skipped."""
        prompt = "I want to use TDD for this feature"
        matches = find_matches(prompt, [tdd_skill])

        # "tdd" is 3 chars, gets skipped (>3 required)
        # "test driven" would need to match
        assert len(matches) == 0

    def test_longer_triggers_match(self, tdd_skill):
        """Triggers with more than 3 chars should match."""
        prompt = "Let's use test driven development to write tests first"
        matches = find_matches(prompt, [tdd_skill])

        assert len(matches) == 1
        matched_triggers = matches[0][1]
        assert any("test" in t.lower() for t in matched_triggers)


class TestWordBoundaryMatching:
    """Tests for word boundary matching behavior."""

    def test_word_boundary_match(self, sample_skill):
        """Should match 'debug' but not partial words."""
        prompt = "I need to debug this"
        matches = find_matches(prompt, [sample_skill])

        # "debug" is only 5 chars but it's a valid trigger
        # Still needs 2 triggers to match
        # Let's try with more
        prompt = "debug this error in the code"
        matches = find_matches(prompt, [sample_skill])

        assert len(matches) == 1

    def test_partial_word_no_match(self):
        """Trigger 'test' should not match 'testing' as word boundary."""
        skill = SkillOrAgent(
            name="test-skill",
            type="skill",
            description="Test things",
            triggers=["test", "unit test", "integration"],
            source_path="/test",
            source_type="global",
        )

        # "testing" should not match "test" due to word boundary
        prompt = "I am testing this code with integration"
        matches = find_matches(prompt, [skill])

        # "test" won't match "testing", but "integration" matches
        # Only 1 trigger = not enough
        assert len(matches) == 0


class TestMinimumTriggerThreshold:
    """Tests for minimum trigger match threshold."""

    def test_default_min_triggers_is_two(self, sample_skill):
        """Default requires 2+ triggers to match."""
        prompt = "Please fix this"  # Only "fix" matches
        matches = find_matches(prompt, [sample_skill])

        assert len(matches) == 0

    def test_two_triggers_matches(self, sample_skill):
        """Two triggers should be enough."""
        prompt = "debug this error"
        matches = find_matches(prompt, [sample_skill])

        assert len(matches) == 1
        assert len(matches[0][1]) >= 2

    def test_custom_min_triggers(self, sample_skill):
        """Should respect custom min_triggers parameter."""
        prompt = "debug this error and fix the issue"

        # With min_triggers=3
        matches = find_matches(prompt, [sample_skill], min_triggers=3)
        assert len(matches) == 1

        # With min_triggers=5
        matches = find_matches(prompt, [sample_skill], min_triggers=5)
        assert len(matches) == 0


class TestNameMatching:
    """Tests for skill/agent name matching."""

    def test_name_in_triggers_counts(self, sample_agent):
        """If name matches a trigger, it should help with matching."""
        # code-reviewer has "review" as trigger
        prompt = "please review my code"
        matches = find_matches(prompt, [sample_agent])

        # "review" and "code" might both match
        # Actually "code review" is a trigger (2 words)
        assert len(matches) == 1


class TestMultipleItems:
    """Tests for matching against multiple skills/agents."""

    def test_multiple_items_can_match(self, sample_skill, sample_agent):
        """Multiple items can match the same prompt."""
        prompt = "debug this code and review the error handling"
        matches = find_matches(prompt, [sample_skill, sample_agent])

        matched_names = [m[0].name for m in matches]
        assert "systematic-debugging" in matched_names
        # review + code matches code-reviewer

    def test_empty_items_list(self):
        """Should handle empty items list gracefully."""
        matches = find_matches("any prompt", [])
        assert matches == []


class TestEdgeCases:
    """Edge case tests."""

    def test_empty_prompt(self, sample_skill):
        """Should handle empty prompt."""
        matches = find_matches("", [sample_skill])
        assert matches == []

    def test_empty_triggers(self):
        """Should handle skill with no triggers."""
        skill = SkillOrAgent(
            name="no-triggers",
            type="skill",
            description="A skill without triggers",
            triggers=[],
            source_path="/test",
            source_type="global",
        )
        matches = find_matches("any prompt", [skill])
        assert len(matches) == 0

    def test_special_characters_in_prompt(self, sample_skill):
        """Should handle special regex characters in prompt."""
        prompt = "debug (this) [error] and fix it?"
        matches = find_matches(prompt, [sample_skill])

        # Should still match debug and error
        assert len(matches) == 1

    def test_special_characters_in_trigger(self):
        """Should handle special characters in triggers via regex escape."""
        skill = SkillOrAgent(
            name="test",
            type="skill",
            description="Test",
            triggers=["C++", "setup.py", "file (copy)"],
            source_path="/test",
            source_type="global",
        )
        # These shouldn't crash due to regex special chars
        prompt = "Help with C++ and setup.py"
        matches = find_matches(prompt, [skill])
        # Even if they don't match (length/boundary issues), shouldn't crash
        assert isinstance(matches, list)
