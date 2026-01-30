"""Tests for Story 4.1: Token-Set Semantic Detection (ADR-077)."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "skills" / "observability-usage-collector" / "scripts"))

import pytest
from collect_usage import (
    tokenize_and_stem,
    _jaccard_similarity,
    compute_setup_profile,
    SkillOrAgent,
    Hook,
    SEMANTIC_DETECTION_ENABLED,
    SEMANTIC_THRESHOLD,
)


# --- Helper ---

def _make_component(name: str, triggers: list[str], type_: str = "skill", source: str = "project") -> SkillOrAgent:
    return SkillOrAgent(name=name, type=type_, description="", triggers=triggers, source_path="", source_type=source)


def _setup_profile_with_overlaps(skills=None, agents=None, commands=None):
    """Run compute_setup_profile with minimal valid inputs and return the profile."""
    return compute_setup_profile(
        skills=skills or [],
        agents=agents or [],
        commands=commands or [],
        hooks=[],
        claude_md={"files_found": ["CLAUDE.md"]},
    )


# --- tokenize_and_stem tests (AC-1, AC-6) ---

class TestTokenizeAndStem:
    def test_basic(self):
        result = tokenize_and_stem("code review")
        assert isinstance(result, frozenset)
        assert len(result) == 2

    def test_hyphenated(self):
        result = tokenize_and_stem("test-driven")
        assert isinstance(result, frozenset)
        assert len(result) >= 1  # "test" and "driven" stemmed

    def test_underscore(self):
        result = tokenize_and_stem("code_review")
        assert isinstance(result, frozenset)
        assert len(result) == 2

    def test_strips_punctuation(self):
        result = tokenize_and_stem("code! review?")
        assert isinstance(result, frozenset)
        assert len(result) == 2

    def test_removes_blocklisted(self):
        # "the" and "for" are in COMMON_WORD_BLOCKLIST
        result = tokenize_and_stem("the code for review")
        # "the" and "for" removed, leaves "code" and "review" stems
        assert len(result) == 2

    def test_empty_result(self):
        # All tokens are blocklisted or too short
        result = tokenize_and_stem("the for and")
        assert result == frozenset()

    def test_unicode(self):
        result = tokenize_and_stem("código revisión")
        assert isinstance(result, frozenset)

    def test_empty_string(self):
        assert tokenize_and_stem("") == frozenset()

    def test_whitespace_only(self):
        assert tokenize_and_stem("   ") == frozenset()

    def test_morphological_consistency(self):
        # "debug" and "debugging" should produce the same stem
        result_a = tokenize_and_stem("debug")
        result_b = tokenize_and_stem("debugging")
        assert result_a == result_b

    def test_phrase_reordering_consistency(self):
        # "code review" and "review code" should produce the same token set
        result_a = tokenize_and_stem("code review")
        result_b = tokenize_and_stem("review code")
        assert result_a == result_b


# --- Jaccard similarity ---

class TestJaccardSimilarity:
    def test_identical_sets(self):
        s = frozenset({"a", "b"})
        assert _jaccard_similarity(s, s) == 1.0

    def test_disjoint_sets(self):
        assert _jaccard_similarity(frozenset({"a"}), frozenset({"b"})) == 0.0

    def test_empty_set(self):
        assert _jaccard_similarity(frozenset(), frozenset({"a"})) == 0.0

    def test_partial_overlap(self):
        a = frozenset({"a", "b", "c"})
        b = frozenset({"b", "c", "d"})
        assert _jaccard_similarity(a, b) == pytest.approx(0.5)


# --- Semantic detection integration tests (AC-2, AC-3, AC-4, AC-5, AC-7) ---

class TestSemanticDetection:
    def test_morphological_variants(self):
        """AC-2: 'debug' vs 'debugging' flagged as SEMANTIC."""
        skills = [
            _make_component("skill-a", ["debug"]),
            _make_component("skill-b", ["debugging"]),
        ]
        profile = _setup_profile_with_overlaps(skills=skills)
        semantic = [o for o in profile.overlapping_triggers if o.get("classification") == "SEMANTIC"]
        assert len(semantic) >= 1
        assert semantic[0]["detection_method"] == "stemmed"
        assert semantic[0]["similarity"] is not None

    def test_phrase_reordering(self):
        """AC-2: 'code review' vs 'review code' flagged as SEMANTIC."""
        skills = [
            _make_component("skill-a", ["code review"]),
            _make_component("skill-b", ["review code"]),
        ]
        profile = _setup_profile_with_overlaps(skills=skills)
        semantic = [o for o in profile.overlapping_triggers if o.get("classification") == "SEMANTIC"]
        assert len(semantic) >= 1
        assert semantic[0]["similarity"] == pytest.approx(1.0)

    def test_below_threshold(self):
        """AC-2: Below threshold not flagged. 'code review' vs 'review changes' — Jaccard ~0.33."""
        skills = [
            _make_component("skill-a", ["code review"]),
            _make_component("skill-b", ["review changes"]),
        ]
        profile = _setup_profile_with_overlaps(skills=skills)
        semantic = [o for o in profile.overlapping_triggers if o.get("classification") == "SEMANTIC"]
        assert len(semantic) == 0

    def test_severity_medium(self):
        """AC-2: Jaccard >= 0.8 gets MEDIUM severity."""
        skills = [
            _make_component("skill-a", ["debug"]),
            _make_component("skill-b", ["debugging"]),
        ]
        profile = _setup_profile_with_overlaps(skills=skills)
        semantic = [o for o in profile.overlapping_triggers if o.get("classification") == "SEMANTIC"]
        assert len(semantic) >= 1
        assert semantic[0]["severity"] == "MEDIUM"

    def test_severity_low(self):
        """AC-2: Jaccard >= 0.4 < 0.8 gets LOW severity."""
        # "systematic debugging" stems: {"systemat", "debug"}
        # "debug logging" stems: {"debug", "log"}
        # Jaccard = 1/3 ≈ 0.33 — too low. Need a better pair.
        # "code debug" stems: {"code", "debug"}
        # "debug trace" stems: {"debug", "trace"}
        # Jaccard = 1/3 ≈ 0.33 — still too low.
        # "code debug review" stems: {"code", "debug", "review"}
        # "debug review" stems: {"debug", "review"}
        # Jaccard = 2/3 ≈ 0.67 — LOW (>= 0.4, < 0.8)
        skills = [
            _make_component("skill-a", ["code debug review"]),
            _make_component("skill-b", ["debug review"]),
        ]
        profile = _setup_profile_with_overlaps(skills=skills)
        semantic = [o for o in profile.overlapping_triggers if o.get("classification") == "SEMANTIC"]
        assert len(semantic) >= 1
        assert semantic[0]["severity"] == "LOW"

    def test_skips_existing_collisions(self):
        """AC-3: Exact-match pairs not re-flagged by semantic detection."""
        # Two skills with the exact same trigger -> COLLISION, not also SEMANTIC
        skills = [
            _make_component("skill-a", ["debug mode"]),
            _make_component("skill-b", ["debug mode"]),
        ]
        profile = _setup_profile_with_overlaps(skills=skills)
        collisions = [o for o in profile.overlapping_triggers if o["classification"] == "COLLISION"]
        semantic = [o for o in profile.overlapping_triggers if o["classification"] == "SEMANTIC"]
        assert len(collisions) == 1
        assert len(semantic) == 0

    def test_disabled_flag(self, monkeypatch):
        """AC-4: No semantic results when SEMANTIC_DETECTION_ENABLED is False."""
        import collect_usage
        monkeypatch.setattr(collect_usage, "SEMANTIC_DETECTION_ENABLED", False)
        skills = [
            _make_component("skill-a", ["debug"]),
            _make_component("skill-b", ["debugging"]),
        ]
        profile = _setup_profile_with_overlaps(skills=skills)
        semantic = [o for o in profile.overlapping_triggers if o.get("classification") == "SEMANTIC"]
        assert len(semantic) == 0

    def test_overlap_dict_has_new_fields(self):
        """AC-7: All overlap dicts include new fields."""
        skills = [
            _make_component("skill-a", ["debug"]),
            _make_component("skill-b", ["debug"]),
        ]
        profile = _setup_profile_with_overlaps(skills=skills)
        for overlap in profile.overlapping_triggers:
            assert "classification" in overlap
            assert "detection_method" in overlap
            assert "similarity" in overlap
            assert "intentional" in overlap
            assert "hint" in overlap

    def test_existing_overlaps_get_migration_defaults(self):
        """AC-5: COLLISION defaults applied to exact-match overlaps."""
        skills = [
            _make_component("skill-a", ["run tests"]),
            _make_component("skill-b", ["run tests"]),
        ]
        profile = _setup_profile_with_overlaps(skills=skills)
        exact = [o for o in profile.overlapping_triggers if o["detection_method"] == "exact"]
        assert len(exact) >= 1
        assert exact[0]["classification"] == "COLLISION"
        assert exact[0]["similarity"] is None
        assert exact[0]["intentional"] is False
        assert exact[0]["hint"] is not None  # Story 4.3: hints now populated

    def test_empty_token_set_skipped(self):
        """AC-1: Empty token sets after processing don't cause comparison."""
        # Trigger with only blocklisted words -> empty token set -> no semantic match
        skills = [
            _make_component("skill-a", ["the for and"]),
            _make_component("skill-b", ["debug"]),
        ]
        profile = _setup_profile_with_overlaps(skills=skills)
        semantic = [o for o in profile.overlapping_triggers if o.get("classification") == "SEMANTIC"]
        assert len(semantic) == 0


# --- Story 4.2: PATTERN classification tests (AC-1 through AC-4) ---

class TestPatternClassification:
    def test_pattern_classification_same_source_command_skill(self):
        """AC-1: Same name + same source command+skill → PATTERN/INFO/intentional=True."""
        skills = [_make_component("deploy", ["deploy app"], type_="skill", source="plugin:ops")]
        commands = [_make_component("deploy", ["deploy cmd"], type_="command", source="plugin:ops")]
        profile = _setup_profile_with_overlaps(skills=skills, commands=commands)
        patterns = [o for o in profile.overlapping_triggers if o.get("classification") == "PATTERN"]
        assert len(patterns) == 1
        assert patterns[0]["severity"] == "INFO"
        assert patterns[0]["intentional"] is True

    def test_pattern_keeps_collision_cross_source(self):
        """AC-2: Same name + different source → stays COLLISION/HIGH."""
        skills = [_make_component("deploy", ["deploy app"], type_="skill", source="plugin:ops")]
        commands = [_make_component("deploy", ["deploy cmd"], type_="command", source="plugin:infra")]
        profile = _setup_profile_with_overlaps(skills=skills, commands=commands)
        collisions = [o for o in profile.overlapping_triggers
                      if o.get("trigger") == "[name collision: deploy]"]
        assert len(collisions) == 1
        assert collisions[0]["classification"] == "COLLISION"
        assert collisions[0]["severity"] == "HIGH"

    def test_pattern_only_command_skill_pairs(self):
        """AC-3: Two skills same name same source → stays COLLISION."""
        skills = [
            _make_component("deploy", ["deploy app"], type_="skill", source="plugin:ops"),
            _make_component("deploy", ["deploy app"], type_="skill", source="plugin:ops"),
        ]
        profile = _setup_profile_with_overlaps(skills=skills)
        # No name collision (no command involved), but trigger overlap exists
        patterns = [o for o in profile.overlapping_triggers if o.get("classification") == "PATTERN"]
        assert len(patterns) == 0

    def test_pattern_display_includes_v1_heuristic(self):
        """AC-4: Output contains '(v1 heuristic)'."""
        skills = [_make_component("deploy", ["deploy app"], type_="skill", source="plugin:ops")]
        commands = [_make_component("deploy", ["deploy cmd"], type_="command", source="plugin:ops")]
        profile = _setup_profile_with_overlaps(skills=skills, commands=commands)
        patterns = [o for o in profile.overlapping_triggers if o.get("classification") == "PATTERN"]
        assert len(patterns) == 1
        assert "(v1 heuristic)" in patterns[0]["hint"]

    def test_pattern_all_fields_correct(self):
        """PATTERN overlaps have intentional=True and severity=INFO."""
        skills = [_make_component("deploy", ["deploy app"], type_="skill", source="plugin:ops")]
        commands = [_make_component("deploy", ["deploy cmd"], type_="command", source="plugin:ops")]
        profile = _setup_profile_with_overlaps(skills=skills, commands=commands)
        patterns = [o for o in profile.overlapping_triggers if o.get("classification") == "PATTERN"]
        assert len(patterns) == 1
        assert patterns[0]["intentional"] is True
        assert patterns[0]["severity"] == "INFO"

    def test_non_pattern_intentional_field_false(self):
        """COLLISION overlaps have intentional=False."""
        skills = [_make_component("deploy", ["deploy app"], type_="skill", source="plugin:ops")]
        commands = [_make_component("deploy", ["deploy cmd"], type_="command", source="plugin:infra")]
        profile = _setup_profile_with_overlaps(skills=skills, commands=commands)
        collisions = [o for o in profile.overlapping_triggers if o.get("classification") == "COLLISION"]
        for c in collisions:
            assert c["intentional"] is False
