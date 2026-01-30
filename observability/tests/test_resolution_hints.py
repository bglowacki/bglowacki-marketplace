"""Tests for Story 4.3: Resolution Hints (ADR-077 Part 3)."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "skills" / "observability-usage-collector" / "scripts"))

import pytest
from collect_usage import _generate_overlap_hint


class TestHintCollisionSkillSkill:
    """AC-1: COLLISION skill+skill HIGH hint."""

    def test_hint_collision_skill_skill(self):
        overlap = {
            "trigger": "deploy",
            "items": ["skill:deploy-a", "skill:deploy-b"],
            "severity": "HIGH",
            "classification": "COLLISION",
            "detection_method": "exact",
            "similarity": None,
            "intentional": False,
            "hint": None,
        }
        hint = _generate_overlap_hint(overlap)
        assert "`skill:deploy-a`" in hint
        assert "`skill:deploy-b`" in hint
        assert "rename the less specific one or merge into a single skill" in hint


class TestHintCollisionCommandSkill:
    """AC-1: COLLISION command+skill HIGH hint."""

    def test_hint_collision_command_skill(self):
        overlap = {
            "trigger": "deploy",
            "items": ["command:deploy", "skill:deploy"],
            "severity": "HIGH",
            "classification": "COLLISION",
            "detection_method": "exact",
            "similarity": None,
            "intentional": False,
            "hint": None,
        }
        hint = _generate_overlap_hint(overlap)
        assert "(command)" in hint
        assert "(skill)" in hint
        assert "deploy" in hint
        assert "intentional delegation pattern" in hint


class TestHintCollisionCommandCommand:
    """AC-1: COLLISION command+command HIGH hint."""

    def test_hint_collision_command_command(self):
        overlap = {
            "trigger": "deploy",
            "items": ["command:deploy-a", "command:deploy-b"],
            "severity": "HIGH",
            "classification": "COLLISION",
            "detection_method": "exact",
            "similarity": None,
            "intentional": False,
            "hint": None,
        }
        hint = _generate_overlap_hint(overlap)
        assert "`command:deploy-a`" in hint
        assert "`command:deploy-b`" in hint
        assert "only one can be invoked" in hint


class TestHintCollisionAgentOther:
    """AC-1: COLLISION agent+other HIGH hint."""

    def test_hint_collision_agent_other(self):
        overlap = {
            "trigger": "deploy",
            "items": ["agent:deploy-bot", "skill:deploy"],
            "severity": "HIGH",
            "classification": "COLLISION",
            "detection_method": "exact",
            "similarity": None,
            "intentional": False,
            "hint": None,
        }
        hint = _generate_overlap_hint(overlap)
        assert "Agent" in hint
        assert "`deploy-bot`" in hint
        assert "routing ambiguity" in hint


class TestHintSemanticMedium:
    """AC-1: SEMANTIC MEDIUM hint with similarity percentage."""

    def test_hint_semantic_medium(self):
        overlap = {
            "trigger": "debug ↔ debugging",
            "items": ["skill:debug-tool", "skill:debugger"],
            "severity": "MEDIUM",
            "classification": "SEMANTIC",
            "detection_method": "stemmed",
            "similarity": 1.0,
            "intentional": False,
            "hint": None,
        }
        hint = _generate_overlap_hint(overlap)
        assert "`skill:debug-tool`" in hint
        assert "`skill:debugger`" in hint
        assert "100%" in hint
        assert "add distinct trigger prefixes" in hint


class TestHintSemanticLow:
    """AC-1: SEMANTIC LOW hint with similarity percentage."""

    def test_hint_semantic_low(self):
        overlap = {
            "trigger": "code debug review ↔ debug review",
            "items": ["skill:analyzer", "skill:reviewer"],
            "severity": "LOW",
            "classification": "SEMANTIC",
            "detection_method": "stemmed",
            "similarity": 0.6667,
            "intentional": False,
            "hint": None,
        }
        hint = _generate_overlap_hint(overlap)
        assert "`skill:analyzer`" in hint
        assert "`skill:reviewer`" in hint
        assert "67%" in hint
        assert "no action needed unless users report misfires" in hint


class TestHintPatternInfo:
    """AC-1: PATTERN INFO hint."""

    def test_hint_pattern_info(self):
        overlap = {
            "trigger": "[name collision: deploy]",
            "items": ["skill:deploy", "command:deploy"],
            "severity": "INFO",
            "classification": "PATTERN",
            "detection_method": "exact",
            "similarity": None,
            "intentional": True,
            "hint": None,
            "source": "my-plugin",
        }
        hint = _generate_overlap_hint(overlap)
        assert "Assumed delegation" in hint
        assert "(v1 heuristic)" in hint
        assert "no action needed" in hint
        assert "(my-plugin)" in hint

    def test_hint_pattern_info_no_source(self):
        overlap = {
            "trigger": "[name collision: deploy]",
            "items": ["skill:deploy", "command:deploy"],
            "severity": "INFO",
            "classification": "PATTERN",
            "detection_method": "exact",
            "similarity": None,
            "intentional": True,
            "hint": None,
        }
        hint = _generate_overlap_hint(overlap)
        assert "Assumed delegation" in hint
        assert "(v1 heuristic)" in hint


class TestHintInterpolation:
    """AC-3: Template variable interpolation uses real names."""

    def test_hint_interpolates_real_names(self):
        overlap = {
            "trigger": "brainstorming",
            "items": ["skill:brainstorming", "command:brainstorming"],
            "severity": "HIGH",
            "classification": "COLLISION",
            "detection_method": "exact",
            "similarity": None,
            "intentional": False,
            "hint": None,
        }
        hint = _generate_overlap_hint(overlap)
        # Must contain actual names, not template placeholders
        assert "{a}" not in hint
        assert "{b}" not in hint
        assert "{name}" not in hint
        assert "brainstorming" in hint


class TestHintEdgeCases:
    """Edge case: empty items list returns empty hint."""

    def test_hint_empty_items(self):
        overlap = {
            "trigger": "x",
            "items": [],
            "severity": "HIGH",
            "classification": "COLLISION",
            "detection_method": "exact",
            "similarity": None,
            "intentional": False,
            "hint": None,
        }
        assert _generate_overlap_hint(overlap) == ""

    def test_hint_single_item(self):
        overlap = {
            "trigger": "x",
            "items": ["skill:foo"],
            "severity": "HIGH",
            "classification": "COLLISION",
            "detection_method": "exact",
            "similarity": None,
            "intentional": False,
            "hint": None,
        }
        assert _generate_overlap_hint(overlap) == ""


class TestHintSimilarityFormat:
    """AC-3: Similarity displayed as percentage."""

    def test_hint_similarity_format(self):
        overlap = {
            "trigger": "scan secrets ↔ secret scanner",
            "items": ["skill:scanner-a", "skill:scanner-b"],
            "severity": "MEDIUM",
            "classification": "SEMANTIC",
            "detection_method": "stemmed",
            "similarity": 0.6667,
            "intentional": False,
            "hint": None,
        }
        hint = _generate_overlap_hint(overlap)
        # Similarity should be formatted as percentage (e.g., "67%")
        assert "67%" in hint
        # Should NOT contain raw float
        assert "0.6667" not in hint
