# Story 4.3: Resolution Hints

Status: done

## Story

As a Power Customizer,
I want each overlap to include an actionable one-line hint,
so that I immediately know what to do about it without needing the walk-through.

## Acceptance Criteria

1. **AC-1: Hint Generation by Classification+Severity**
   - Given an overlap is detected and classified
   - When hint generation runs
   - Then a `hint` string is populated based on `(classification, severity)`:
     - COLLISION (skill+skill) HIGH: "`{a}` and `{b}` are both skills named `{name}` — rename the less specific one or merge into a single skill"
     - COLLISION (command+skill) HIGH: "`{a}` (command) and `{b}` (skill) share name `{name}` — if same-source, this is likely an intentional delegation pattern (will be auto-classified as PATTERN/INFO); if cross-source, rename the command or configure as intentional in v2's `intentional_overlaps`"
     - COLLISION (command+command) HIGH: "`{a}` and `{b}` are both commands named `{name}` — only one can be invoked; remove or rename the duplicate from the lower-priority plugin"
     - COLLISION (agent+other) HIGH: "Agent `{a}` collides with {type} `{b}` on name `{name}` — rename the non-agent component to avoid routing ambiguity"
     - SEMANTIC MEDIUM: "Triggers `{a}` and `{b}` overlap ({similarity:.0%}) — add distinct trigger prefixes, or consolidate into one component if they serve the same purpose"
     - SEMANTIC LOW: "Minor trigger similarity ({similarity:.0%}) between `{a}` and `{b}` — no action needed unless users report misfires"
     - PATTERN INFO: "Assumed delegation: `{command}` → `{skill}` ({source}) (v1 heuristic) — no action needed"

2. **AC-2: Actionable HIGH Hints**
   - Given a HIGH severity overlap
   - When the user reads the hint
   - Then the hint is actionable without needing the walk-through (self-contained)

3. **AC-3: Template Variable Interpolation**
   - Given the hint uses template variables ({a}, {b}, {name}, {similarity}, etc.)
   - When hints are generated
   - Then actual component names, types, and scores are interpolated into the hint text

4. **AC-4: Overlap Schema Compliance**
   - Given overlap dicts are produced
   - When they include hints
   - Then the schema matches: trigger, components/items, severity, classification, detection_method, similarity, intentional, hint

## Tasks / Subtasks

- [x] Task 1: Write tests first (TDD) (AC: 1-3)
  - [x] `test_hint_collision_skill_skill` — correct hint text for skill+skill HIGH
  - [x] `test_hint_collision_command_skill` — correct hint for command+skill HIGH
  - [x] `test_hint_collision_command_command` — correct hint for command+command HIGH
  - [x] `test_hint_collision_agent_other` — correct hint for agent+other HIGH
  - [x] `test_hint_semantic_medium` — correct hint with similarity percentage for MEDIUM
  - [x] `test_hint_semantic_low` — correct hint with similarity percentage for LOW
  - [x] `test_hint_pattern_info` — correct hint for PATTERN INFO
  - [x] `test_hint_interpolates_real_names` — actual component names in hint, not placeholders
  - [x] `test_hint_similarity_format` — similarity displayed as percentage (e.g., "67%")

- [x] Task 2: Implement `_generate_overlap_hint()` helper function (AC: 1, 3)
  - [x] Place near overlap detection code in `collect_usage.py`
  - [x] Accept overlap dict (with classification, severity, items/components, similarity)
  - [x] Determine component types from items list (e.g., "skill:foo" → type="skill", name="foo")
  - [x] Select hint template based on (classification, severity, component types)
  - [x] Interpolate actual names, types, sources, similarity scores
  - [x] Return hint string

- [x] Task 3: Wire hint generation into overlap detection (AC: 1, 4)
  - [x] Call `_generate_overlap_hint()` for each overlap dict in `compute_setup_profile()`
  - [x] Set `hint` field on all overlap dicts (exact-match, semantic, PATTERN)
  - [x] Replace `hint: None` defaults from Story 4.1 with actual hints

- [x] Task 4: Verify all existing tests pass
  - [x] Run `cd observability && uv run pytest tests/ -x`

## Dev Notes

### Hint Templates (from ADR-077)

The 7 hint templates are fully specified in ADR-077 Part 3. They must be implemented exactly as written — these are the user-facing strings.

### Component Type Detection

The `items` field in overlap dicts stores components as `"type:name"` strings (e.g., `"skill:brainstorming"`, `"command:commit"`). Parse these to determine component types for hint template selection:

```python
def _parse_component(item: str) -> tuple[str, str]:
    """Parse 'type:name' into (type, name)."""
    parts = item.split(":", 1)
    return (parts[0], parts[1]) if len(parts) == 2 else ("unknown", item)
```

### Similarity Formatting

For SEMANTIC hints, format Jaccard similarity as percentage: `f"{similarity:.0%}"` produces "67%" from 0.6667.

### Dependencies

**Upstream:** Story 4.1 (schema with new fields), Story 4.2 (PATTERN classification)
**Downstream:** Story 4.4 (walk-through uses hints in `rendered.problem`)

### All Code in `collect_usage.py`

Per ADR-042 — no separate files. Place `_generate_overlap_hint()` near the overlap detection block.

### References

- [Source: docs/adrs/ADR-077-semantic-overlap-detection-classification-resolution.md#Part 3]
- [Source: _bmad-output/planning-artifacts/epics.md#Story 4.3]
- [Source: collect_usage.py:791-845] — Overlap detection where hints are generated

## Dev Agent Record

### Agent Model Used
Claude Opus 4.5

### Debug Log References

### Completion Notes List
- Implemented `_parse_component()` and `_generate_overlap_hint()` helpers in collect_usage.py (placed before `compute_setup_profile()`)
- All 7 hint templates from ADR-077 Part 3 implemented: COLLISION (skill+skill, command+skill, command+command, agent+other), SEMANTIC (MEDIUM, LOW), PATTERN (INFO)
- Wired hint generation into all three overlap creation points: exact-match triggers, name collisions, and semantic overlaps
- Updated existing test `test_existing_overlaps_get_migration_defaults` to expect non-None hints (Story 4.3 replaces `hint: None` defaults)
- All 405 tests pass (0 failures, 2 skipped)

### Code Review Fixes (2026-01-30)
- Fixed PATTERN hint to include `{source}` per ADR-077 spec; added `source` field to PATTERN overlap entries
- Added early return guard for `items` lists with fewer than 2 elements (prevents IndexError)
- Clarified tuple unpacking — removed ambiguous ternary on unpacking lines
- Improved `next()` call readability for agent collision branch (named tuple destructure)
- Added 3 new tests: source in PATTERN hint, empty items, single item edge case
- All 408 tests pass (0 failures, 2 skipped)

### File List
- observability/skills/observability-usage-collector/scripts/collect_usage.py (modified — added `_parse_component`, `_generate_overlap_hint`, wired hints into overlap detection)
- observability/tests/test_resolution_hints.py (new — 9 TDD test cases for hint generation)
- observability/tests/test_semantic_detection.py (modified — updated migration defaults test for non-None hints)

## Change Log
- 2026-01-30: Implemented Story 4.3 — resolution hints for all overlap types with TDD tests
