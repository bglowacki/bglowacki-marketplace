# Story 4.2: Intentional Overlap Classification (PATTERN)

Status: done

## Story

As a Power Customizer,
I want intentional delegation patterns (command → same-name skill) recognized as harmless,
so that known patterns don't clutter my overlap warnings.

## Acceptance Criteria

1. **AC-1: Same-Source PATTERN Classification**
   - Given a skill and command share the same name AND the same source plugin
   - When overlap classification runs (after name collision detection)
   - Then the overlap is classified as `classification: "PATTERN"`, `severity: "INFO"`, `intentional: true`
   - And the output message includes "(v1 heuristic)" qualifier text

2. **AC-2: Cross-Source Remains COLLISION**
   - Given a skill and command share the same name but from DIFFERENT source plugins
   - When overlap classification runs
   - Then the overlap remains `classification: "COLLISION"`, `severity: "HIGH"`

3. **AC-3: Non-Command+Skill Pairs Stay COLLISION**
   - Given two skills (not a command+skill pair) share the same name from the same source
   - When overlap classification runs
   - Then the overlap remains COLLISION (PATTERN heuristic only applies to command+skill pairs in v1)

4. **AC-4: Display Format**
   - Given PATTERN overlaps are displayed
   - When the user views results
   - Then the display reads as architecture insight, not a warning:
     "Command `{name}` delegates to skill `{name}` ({source}) — assumed delegation pattern (v1 heuristic)"

## Tasks / Subtasks

- [x] Task 1: Write tests first (TDD) (AC: 1-4)
  - [x] `test_pattern_classification_same_source_command_skill` — same name + same source → PATTERN/INFO/intentional=True
  - [x] `test_pattern_keeps_collision_cross_source` — same name + different source → stays COLLISION/HIGH
  - [x] `test_pattern_only_command_skill_pairs` — two skills same name same source → stays COLLISION
  - [x] `test_pattern_display_includes_v1_heuristic` — output contains "(v1 heuristic)"
  - [x] `test_pattern_intentional_field_true` — `intentional: True` set for PATTERN
  - [x] `test_pattern_severity_is_info` — severity is "INFO" not "HIGH"
  - [x] `test_non_pattern_intentional_field_false` — COLLISION overlaps have `intentional: False`

- [x] Task 2: Implement PATTERN classification in `compute_setup_profile()` (AC: 1-3)
  - [x] After name collision detection (line ~840), before appending overlap dict
  - [x] For each name collision: check if one is a command and one is a skill
  - [x] If command+skill pair: compare `source_type` fields
  - [x] If same source: set `classification: "PATTERN"`, `severity: "INFO"`, `intentional: True`
  - [x] If different source: keep `classification: "COLLISION"`, `severity: "HIGH"`, `intentional: False`
  - [x] For non-command+skill pairs: always COLLISION

- [x] Task 3: Update display/hint text for PATTERN overlaps (AC: 4)
  - [x] Format: "Command `{name}` delegates to skill `{name}` ({source}) — assumed delegation pattern (v1 heuristic)"
  - [x] Store in overlap dict (hint field, prepared for Story 4.3)

- [x] Task 4: Verify all existing tests pass (regression check)
  - [x] Run `cd observability && uv run pytest tests/ -x`

## Dev Notes

### Where to Add Code

The PATTERN classification logic goes inside `compute_setup_profile()` in `collect_usage.py`, specifically in the name collision loop (around line 833-840). The current code:

```python
for name in name_collisions:
    overlapping.insert(0, {
        "trigger": f"[name collision: {name}]",
        "items": [f"skill:{name}", f"command:{name}"],
        "severity": "HIGH",
    })
    high_severity_count += 1
```

Must be modified to check source before assigning severity/classification.

### Source Information Access

The `source_type` field is available on each `SkillOrAgent` item. To compare sources for a name collision:
- Find the skill with `name.lower()` in the skills list
- Find the command with `name.lower()` in the commands list
- Compare their `source_type` values

### Key Constraint

PATTERN heuristic is **v1 only** — applies ONLY to command+skill pairs with same name AND same source. All other overlap types remain COLLISION. This is intentionally conservative.

### Dependencies

**Upstream:** Story 4.1 (overlap schema with new fields: classification, intentional, etc.)
**Downstream:** Stories 4.3 (hints use PATTERN classification), 4.4 (walk-through uses PATTERN)

### Test File

Add tests to `observability/tests/test_semantic_detection.py` (created in Story 4.1) or create `observability/tests/test_pattern_classification.py`.

### Previous Story Patterns

- Constants and helpers at module level
- Private helpers use `_function_name()` convention
- All code in single file `collect_usage.py` (ADR-042)

### References

- [Source: docs/adrs/ADR-077-semantic-overlap-detection-classification-resolution.md#Part 2]
- [Source: _bmad-output/planning-artifacts/epics.md#Story 4.2]
- [Source: collect_usage.py:833-840] — Name collision loop to modify

## Dev Agent Record

### Agent Model Used
Claude Opus 4.5

### Debug Log References
None needed — clean TDD cycle, all tests passed on first GREEN attempt.

### Completion Notes List
- Wrote 7 TDD tests covering all 4 ACs in `TestPatternClassification` class
- Modified name collision loop in `compute_setup_profile()` to classify same-source command+skill pairs as PATTERN (INFO/intentional) vs cross-source as COLLISION (HIGH)
- Hint text format: `Command \`{name}\` delegates to skill \`{name}\` ({source}) — assumed delegation pattern (v1 heuristic)`
- Full regression: 397 passed, 2 skipped, 0 failures

### File List
- observability/skills/observability-usage-collector/scripts/collect_usage.py (modified — PATTERN classification in name collision loop)
- observability/tests/test_semantic_detection.py (modified — added TestPatternClassification class with 7 tests)
