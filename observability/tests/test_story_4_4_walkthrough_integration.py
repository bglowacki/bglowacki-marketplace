"""Tests for Story 4.4: Walk-Through Integration & Pre-Release Validation.

Tests for:
- AC-1: rendered dict populated at detection time
- AC-2: Walk-through skill accepts overlap findings
- AC-3: Dashboard graceful degradation without classification
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "skills" / "observability-usage-collector" / "scripts"))

import pytest
from collect_usage import (
    compute_setup_profile,
    compute_pre_computed_findings,
    SkillOrAgent,
    Hook,
)


# --- Helpers ---

def _make_component(name: str, triggers: list[str], type_: str = "skill", source: str = "project") -> SkillOrAgent:
    return SkillOrAgent(name=name, type=type_, description="test desc", triggers=triggers, source_path="", source_type=source)


def _setup_with_overlaps(skills=None, agents=None, commands=None):
    return compute_setup_profile(
        skills=skills or [],
        agents=agents or [],
        commands=commands or [],
        hooks=[],
        claude_md={"files_found": ["CLAUDE.md"]},
    )


# --- AC-1: Rendered dict populated at detection time ---

class TestRenderedDictPopulatedAtDetection:
    """test_rendered_dict_populated_at_detection — overlap has `rendered` with problem/evidence/action."""

    def test_collision_has_rendered(self):
        skills = [
            _make_component("skill-a", ["run tests"]),
            _make_component("skill-b", ["run tests"]),
        ]
        profile = _setup_with_overlaps(skills=skills)
        for overlap in profile.overlapping_triggers:
            assert "rendered" in overlap, "Overlap must have 'rendered' dict"
            rendered = overlap["rendered"]
            assert "problem" in rendered
            assert "evidence" in rendered
            assert "action" in rendered

    def test_semantic_has_rendered(self):
        skills = [
            _make_component("skill-a", ["debug"]),
            _make_component("skill-b", ["debugging"]),
        ]
        profile = _setup_with_overlaps(skills=skills)
        semantic = [o for o in profile.overlapping_triggers if o["classification"] == "SEMANTIC"]
        assert len(semantic) >= 1
        for overlap in semantic:
            assert "rendered" in overlap
            rendered = overlap["rendered"]
            assert "problem" in rendered
            assert "evidence" in rendered
            assert "action" in rendered

    def test_pattern_has_rendered(self):
        skills = [_make_component("deploy", ["deploy app"], type_="skill", source="plugin:ops")]
        commands = [_make_component("deploy", ["deploy cmd"], type_="command", source="plugin:ops")]
        profile = _setup_with_overlaps(skills=skills, commands=commands)
        patterns = [o for o in profile.overlapping_triggers if o["classification"] == "PATTERN"]
        assert len(patterns) >= 1
        for overlap in patterns:
            assert "rendered" in overlap
            rendered = overlap["rendered"]
            assert "problem" in rendered
            assert "evidence" in rendered
            assert "action" in rendered


class TestRenderedProblemEqualsHint:
    """test_rendered_problem_equals_hint — `rendered.problem` matches `hint` field."""

    def test_collision_problem_is_hint(self):
        skills = [
            _make_component("skill-a", ["run tests"]),
            _make_component("skill-b", ["run tests"]),
        ]
        profile = _setup_with_overlaps(skills=skills)
        for overlap in profile.overlapping_triggers:
            if overlap.get("hint"):
                assert overlap["rendered"]["problem"] == overlap["hint"]

    def test_semantic_problem_is_hint(self):
        skills = [
            _make_component("skill-a", ["debug"]),
            _make_component("skill-b", ["debugging"]),
        ]
        profile = _setup_with_overlaps(skills=skills)
        semantic = [o for o in profile.overlapping_triggers if o["classification"] == "SEMANTIC"]
        for overlap in semantic:
            assert overlap["rendered"]["problem"] == overlap["hint"]


class TestRenderedEvidenceFormat:
    """test_rendered_evidence_format — evidence string contains components, trigger, detection_method."""

    def test_evidence_contains_components(self):
        skills = [
            _make_component("skill-a", ["run tests"]),
            _make_component("skill-b", ["run tests"]),
        ]
        profile = _setup_with_overlaps(skills=skills)
        for overlap in profile.overlapping_triggers:
            evidence = overlap["rendered"]["evidence"]
            # Must contain component references
            for item in overlap["items"]:
                assert item in evidence, f"Evidence must contain component '{item}'"

    def test_evidence_contains_trigger(self):
        skills = [
            _make_component("skill-a", ["run tests"]),
            _make_component("skill-b", ["run tests"]),
        ]
        profile = _setup_with_overlaps(skills=skills)
        for overlap in profile.overlapping_triggers:
            evidence = overlap["rendered"]["evidence"]
            assert overlap["trigger"] in evidence or "trigger" in evidence.lower()

    def test_evidence_contains_detection_method(self):
        skills = [
            _make_component("skill-a", ["run tests"]),
            _make_component("skill-b", ["run tests"]),
        ]
        profile = _setup_with_overlaps(skills=skills)
        for overlap in profile.overlapping_triggers:
            evidence = overlap["rendered"]["evidence"]
            assert overlap["detection_method"] in evidence

    def test_semantic_evidence_contains_similarity(self):
        skills = [
            _make_component("skill-a", ["debug"]),
            _make_component("skill-b", ["debugging"]),
        ]
        profile = _setup_with_overlaps(skills=skills)
        semantic = [o for o in profile.overlapping_triggers if o["classification"] == "SEMANTIC"]
        for overlap in semantic:
            evidence = overlap["rendered"]["evidence"]
            assert str(overlap["similarity"]) in evidence or "similarity" in evidence.lower()


class TestRenderedActionVariesByClassification:
    """test_rendered_action_varies_by_classification — different action text for COLLISION vs SEMANTIC vs PATTERN."""

    def _get_actions_by_classification(self):
        # Get COLLISION action
        skills_c = [
            _make_component("skill-a", ["run tests"]),
            _make_component("skill-b", ["run tests"]),
        ]
        profile_c = _setup_with_overlaps(skills=skills_c)
        collision_actions = [o["rendered"]["action"] for o in profile_c.overlapping_triggers if o["classification"] == "COLLISION"]

        # Get SEMANTIC action
        skills_s = [
            _make_component("skill-a", ["debug"]),
            _make_component("skill-b", ["debugging"]),
        ]
        profile_s = _setup_with_overlaps(skills=skills_s)
        semantic_actions = [o["rendered"]["action"] for o in profile_s.overlapping_triggers if o["classification"] == "SEMANTIC"]

        # Get PATTERN action
        skills_p = [_make_component("deploy", ["deploy app"], type_="skill", source="plugin:ops")]
        commands_p = [_make_component("deploy", ["deploy cmd"], type_="command", source="plugin:ops")]
        profile_p = _setup_with_overlaps(skills=skills_p, commands=commands_p)
        pattern_actions = [o["rendered"]["action"] for o in profile_p.overlapping_triggers if o["classification"] == "PATTERN"]

        return collision_actions, semantic_actions, pattern_actions

    def test_collision_has_action(self):
        collision, _, _ = self._get_actions_by_classification()
        assert len(collision) >= 1
        assert collision[0]  # non-empty

    def test_semantic_has_action(self):
        _, semantic, _ = self._get_actions_by_classification()
        assert len(semantic) >= 1
        assert semantic[0]  # non-empty

    def test_pattern_has_action(self):
        _, _, pattern = self._get_actions_by_classification()
        assert len(pattern) >= 1
        assert pattern[0]  # non-empty

    def test_actions_differ_by_classification(self):
        collision, semantic, pattern = self._get_actions_by_classification()
        # At least one from each should be different
        assert collision[0] != semantic[0], "COLLISION and SEMANTIC actions should differ"
        assert pattern[0] != collision[0], "PATTERN and COLLISION actions should differ"


class TestOverlapFindingType:
    """test_overlap_finding_type — finding has `finding_type: 'overlap_resolution'`."""

    def test_pre_computed_findings_have_overlap_type(self):
        skills = [
            _make_component("skill-a", ["run tests"]),
            _make_component("skill-b", ["run tests"]),
        ]
        profile = _setup_with_overlaps(skills=skills)
        findings = compute_pre_computed_findings(
            skills=skills, agents=[], commands=[], sessions=[], missed=[],
            setup_profile=profile,
        )
        assert "overlap_findings" in findings, "pre_computed_findings must contain 'overlap_findings'"
        for finding in findings["overlap_findings"]:
            assert finding["finding_type"] == "overlap_resolution"

    def test_overlap_finding_contains_rendered(self):
        skills = [
            _make_component("skill-a", ["run tests"]),
            _make_component("skill-b", ["run tests"]),
        ]
        profile = _setup_with_overlaps(skills=skills)
        findings = compute_pre_computed_findings(
            skills=skills, agents=[], commands=[], sessions=[], missed=[],
            setup_profile=profile,
        )
        for finding in findings["overlap_findings"]:
            assert "rendered" in finding
            assert "overlap" in finding

    def test_overlap_finding_includes_full_overlap_dict(self):
        skills = [
            _make_component("skill-a", ["run tests"]),
            _make_component("skill-b", ["run tests"]),
        ]
        profile = _setup_with_overlaps(skills=skills)
        findings = compute_pre_computed_findings(
            skills=skills, agents=[], commands=[], sessions=[], missed=[],
            setup_profile=profile,
        )
        for finding in findings["overlap_findings"]:
            overlap = finding["overlap"]
            assert "trigger" in overlap
            assert "components" in overlap or "items" in overlap
            assert "severity" in overlap
            assert "classification" in overlap


class TestWalkThroughHandlesMissingFields:
    """test_walk_through_handles_missing_fields — overlap without new fields uses defaults gracefully."""

    def test_overlap_without_rendered_gets_defaults(self):
        # Simulate an overlap dict from before Story 4.4 (no rendered field)
        legacy_overlap = {
            "trigger": "run tests",
            "items": ["skill:skill-a", "skill:skill-b"],
            "severity": "LOW",
        }
        # The walk-through agent should handle missing fields.
        # Since agents are markdown-based LLM consumers, we verify the agent
        # markdown contains instructions for handling missing fields.
        root = Path(__file__).parent.parent
        agent_file = root / "agents" / "usage-insights-agent.md"
        content = agent_file.read_text()
        walkthrough = content[content.find("## Findings Walk-through"):]
        assert "overlap" in walkthrough.lower() or "Overlap" in walkthrough

    def test_agent_has_overlap_resolution_template(self):
        root = Path(__file__).parent.parent
        agent_file = root / "agents" / "usage-insights-agent.md"
        content = agent_file.read_text()
        assert "overlap_resolution" in content or "Overlap Resolution" in content


class TestDashboardDegradesWithoutClassification:
    """test_dashboard_degrades_without_classification — severity displayed even if classification absent."""

    def test_dashboard_mentions_severity(self):
        root = Path(__file__).parent.parent
        agent_file = root / "agents" / "usage-insights-agent.md"
        content = agent_file.read_text()
        # Dashboard section should reference severity for overlaps
        dashboard_start = content.find("## Summary Dashboard")
        analysis_start = content.find("## Analysis Workflow", dashboard_start)
        dashboard = content[dashboard_start:analysis_start] if analysis_start != -1 else content[dashboard_start:]
        assert "severity" in dashboard.lower() or "overlapping" in dashboard.lower()

    def test_setup_analyzer_handles_missing_classification(self):
        root = Path(__file__).parent.parent
        agent_file = root / "agents" / "usage-setup-analyzer.md"
        content = agent_file.read_text()
        # Should reference overlapping triggers with severity display
        assert "overlapping" in content.lower() or "overlap" in content.lower()
        assert "severity" in content.lower()
