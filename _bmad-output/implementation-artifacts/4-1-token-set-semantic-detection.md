# Story 4.1: Token-Set Semantic Detection

Status: done

<!-- Note: Validation is optional. Run validate-create-story for quality check before dev-story. -->

## Story

As a Power Customizer,
I want overlap detection to catch morphological variants and phrase reordering,
so that "debug" vs "debugging" and "code review" vs "review code" are flagged as overlapping.

## Acceptance Criteria

1. **AC-1: Tokenization and Stemming**
   - Given triggers exist in installed plugins
   - When `compute_setup_profile()` builds the trigger map
   - Then each trigger is tokenized (split on spaces, hyphens, underscores; strip punctuation)
   - And each token is stemmed via Porter Stemmer (`nltk.stem.porter`, auto-installed via uv inline script deps)
   - And blocklisted common words are removed
   - And empty token sets after processing are skipped (no comparison)

2. **AC-2: Jaccard Similarity and Classification**
   - Given two triggers with stemmed token sets A and B
   - When Jaccard similarity `|A ∩ B| / |A ∪ B|` is >= 0.4
   - Then the pair is flagged with `classification: "SEMANTIC"`, `detection_method: "stemmed"`
   - And severity is MEDIUM if Jaccard >= 0.8, LOW if Jaccard >= 0.4 and < 0.8
   - And `similarity` field stores the Jaccard score as a float

3. **AC-3: Detection Precedence**
   - Given a pair already flagged as COLLISION by exact-match detection
   - When semantic comparison runs
   - Then that pair is skipped (exact first, no duplicates)

4. **AC-4: Feature Flag**
   - Given the `SEMANTIC_DETECTION_ENABLED` constant is set to `False`
   - When overlap detection runs
   - Then only exact-match detection executes; no stemming or Jaccard comparisons occur

5. **AC-5: Migration Defaults**
   - Given existing overlaps produced before this feature
   - When the updated code processes them
   - Then defaults are applied: `classification: "COLLISION"`, `detection_method: "exact"`, `similarity: null`, `intentional: false`, `hint: null`

6. **AC-6: Utility Function**
   - Given a `tokenize_and_stem(trigger)` utility function
   - When called with a trigger string
   - Then it returns a `frozenset` of stemmed tokens
   - And it is placed near existing trigger matching code in `collect_usage.py`
   - And both original trigger and stemmed token set are stored (display original in output)

7. **AC-7: Overlap Schema Extension**
   - Given an overlap dict is produced
   - When it contains new fields
   - Then it includes: `classification`, `detection_method`, `similarity`, `intentional`, `hint`
   - And existing fields (`trigger`, `items`/`components`, `severity`) are preserved

## Tasks / Subtasks

- [x] Task 1: Add `nltk` dependency to uv inline script metadata (AC: 1)
  - [x] Add `nltk` to the inline `# /// script` dependencies block in `collect_usage.py`
  - [x] Verify `uv run` auto-installs `nltk` on first run

- [x] Task 2: Implement `tokenize_and_stem()` utility function (AC: 1, 6)
  - [x] Place near existing trigger matching code (around line 791)
  - [x] Split trigger on spaces, hyphens, underscores; strip punctuation
  - [x] Stem each token using `nltk.stem.porter.PorterStemmer`
  - [x] Remove blocklisted common words (use existing `COMMON_WORDS` blocklist)
  - [x] Return `frozenset` of stemmed tokens
  - [x] Handle edge cases: empty string, single character tokens, unicode

- [x] Task 3: Add `SEMANTIC_DETECTION_ENABLED` and `SEMANTIC_THRESHOLD` constants (AC: 4)
  - [x] `SEMANTIC_DETECTION_ENABLED: bool = True`
  - [x] `SEMANTIC_THRESHOLD: float = 0.4`
  - [x] Place near other constants (e.g., near `MIN_TRIGGER_LENGTH`)

- [x] Task 4: Extend overlap detection in `compute_setup_profile()` (AC: 2, 3, 5, 7)
  - [x] After existing exact-match detection (line ~840), add semantic detection block
  - [x] Build stemmed token sets for all triggers during trigger_map construction
  - [x] Track already-flagged pairs from exact-match to skip in semantic pass (AC-3)
  - [x] For each non-flagged trigger pair, compute Jaccard similarity
  - [x] If Jaccard >= SEMANTIC_THRESHOLD, create overlap dict with new fields
  - [x] Assign severity: MEDIUM if >= 0.8, LOW if >= 0.4 and < 0.8
  - [x] Guard: skip comparison if either token set is empty (AC-1)
  - [x] Wrap semantic block in `if SEMANTIC_DETECTION_ENABLED` check (AC-4)

- [x] Task 5: Add migration defaults to existing overlap dicts (AC: 5)
  - [x] Add `classification: "COLLISION"` to all existing exact-match overlaps
  - [x] Add `detection_method: "exact"` to existing overlaps
  - [x] Add `similarity: None` to existing overlaps
  - [x] Add `intentional: False` to existing overlaps
  - [x] Add `hint: None` to existing overlaps (hints come in Story 4.3)

- [x] Task 6: Write tests (TDD - write tests FIRST, then implement) (AC: 1-7)
  - [x] `test_tokenize_and_stem_basic` — "code review" -> frozenset of stemmed tokens
  - [x] `test_tokenize_and_stem_hyphenated` — "test-driven" splits on hyphen
  - [x] `test_tokenize_and_stem_underscore` — "code_review" splits on underscore
  - [x] `test_tokenize_and_stem_strips_punctuation` — removes punctuation
  - [x] `test_tokenize_and_stem_removes_blocklisted` — common words removed
  - [x] `test_tokenize_and_stem_empty_result` — returns empty frozenset for all-blocklist input
  - [x] `test_tokenize_and_stem_unicode` — handles non-ASCII triggers
  - [x] `test_semantic_detection_morphological_variants` — "debug" vs "debugging" flagged
  - [x] `test_semantic_detection_phrase_reordering` — "code review" vs "review code" flagged
  - [x] `test_semantic_detection_below_threshold` — "code review" vs "review changes" NOT flagged (Jaccard 0.33)
  - [x] `test_semantic_detection_severity_medium` — Jaccard >= 0.8 gets MEDIUM
  - [x] `test_semantic_detection_severity_low` — Jaccard >= 0.4 < 0.8 gets LOW
  - [x] `test_semantic_detection_skips_existing_collisions` — exact-match pairs not re-flagged
  - [x] `test_semantic_detection_disabled_flag` — no semantic results when flag is False
  - [x] `test_overlap_dict_has_new_fields` — classification, detection_method, similarity, intentional, hint present
  - [x] `test_existing_overlaps_get_migration_defaults` — COLLISION defaults applied to exact-match overlaps
  - [x] `test_empty_token_set_skipped` — empty token sets don't cause comparison

- [x] Task 7: Verify all 367+ existing tests still pass (regression check)
  - [x] Run `cd observability && uv run pytest tests/ -x`
  - [x] Zero regressions (390 passed, 2 skipped)

## Dev Notes

### Critical Architecture Constraints

- **Single file**: ALL code stays in `collect_usage.py` per ADR-042 (`uv run --script` compatibility). No separate `models.py` or `utils.py`.
- **No ML**: Porter Stemmer is deterministic suffix-stripping, not ML inference. ADR-019 compatible per ADR-077.
- **`nltk` package**: Use `nltk.stem.porter.PorterStemmer`. The `stemming` package is Python 2 only — do NOT use it.
- **Inline deps**: Add `nltk` to the `# /// script` inline dependencies block at the top of `collect_usage.py`, NOT to `pyproject.toml` main deps.

### Existing Overlap Detection Code

The current overlap detection is at `collect_usage.py:791-845`:
- Builds `trigger_map: dict[str, list[tuple[str, str, str]]]` mapping lowercased triggers to `(type, name, source)` tuples
- Checks `skill_names & command_names` for name collisions
- Produces overlap dicts with `trigger`, `items`, `severity` fields
- Limits output to top 10 overlaps (line 885)
- Stored in `SetupProfile.overlapping_triggers: list[dict]` (line 723)

### Where to Add New Code

1. **Constants**: Near `MIN_TRIGGER_LENGTH` (around line 40-60 area with other constants)
2. **`tokenize_and_stem()`**: Near line 791, before the overlap detection block
3. **Semantic detection**: After the existing exact-match loop (after line 840), before the `high_severity_count` red_flags check
4. **Migration defaults**: Modify existing overlap dict creation (lines 827-831 and 835-839) to include new fields

### Overlap Schema (New Fields)

```python
{
    "trigger": str,              # original trigger text (EXISTING)
    "items": list[str],          # involved components as "type:name" (EXISTING, renamed to "components" in ADR-077 but keep backward compat)
    "severity": str,             # HIGH | MEDIUM | LOW | INFO (EXISTING, extended)
    "classification": str,       # NEW: COLLISION | SEMANTIC | PATTERN
    "detection_method": str,     # NEW: "exact" | "stemmed"
    "similarity": float | None,  # NEW: Jaccard score for stemmed matches
    "intentional": bool,         # NEW: True for PATTERN overlaps (Story 4.2)
    "hint": str | None,          # NEW: one-line resolution guidance (Story 4.3)
}
```

### Jaccard Similarity Formula

```python
def jaccard_similarity(set_a: frozenset, set_b: frozenset) -> float:
    if not set_a or not set_b:
        return 0.0
    intersection = set_a & set_b
    union = set_a | set_b
    return len(intersection) / len(union)
```

### Detection Precedence Logic

```python
# 1. Run exact-match detection FIRST (existing code)
# 2. Track flagged pairs: exact_pairs = set of frozenset({comp_a, comp_b})
# 3. Run semantic detection ONLY for pairs NOT in exact_pairs
# 4. COLLISION classification never downgraded to SEMANTIC
```

### Example Token Sets (from ADR-077)

| Trigger | Tokens | Stemmed |
|---------|--------|---------|
| "debug" | ["debug"] | {"debug"} |
| "debugging" | ["debugging"] | {"debug"} |
| "code review" | ["code", "review"] | {"code", "review"} |
| "review code" | ["review", "code"] | {"code", "review"} |
| "systematic debugging" | ["systematic", "debugging"] | {"systemat", "debug"} |

### TDD Workflow

Per project config (CLAUDE.md): Use TDD — write tests first, expect failures, then implement code to make tests pass.

1. Write test file `observability/tests/test_semantic_detection.py`
2. Run tests — expect all new tests to FAIL
3. Implement `tokenize_and_stem()` — some tests pass
4. Implement semantic detection in `compute_setup_profile()` — more tests pass
5. Add migration defaults — remaining tests pass
6. Run full suite — 0 regressions

### Previous Story Learnings (from Story 3.4)

- 12 new tests were typical for a story of this scope
- Story 3.4 added constants at module level (e.g., `CLEANUP_MIN_SESSIONS = 20`)
- Helper functions follow `_function_name()` convention for private helpers
- All 365 tests passed after Story 3.4 (now 367 after retro cleanup)
- Agent model: Claude Opus 4.5 (claude-opus-4-5-20251101)

### Git Intelligence

Recent commits show consistent patterns:
- Commit format: `feat(observability): Story X.Y - description`
- Tests added alongside implementation
- Code review fixes applied in same commit
- Version bumped in `.claude-plugin/plugin.json` per CLAUDE.md

### Dependencies

**This story has NO upstream dependencies** (first story in Epic 4).

**Downstream:** Stories 4.2, 4.3, and 4.4 depend on this story's output (overlap schema with new fields).

### Project Structure Notes

- Main file: `observability/skills/observability-usage-collector/scripts/collect_usage.py`
- Tests: `observability/tests/test_semantic_detection.py` (NEW)
- Benchmark: `observability/scripts/benchmark_overlap_detection.py` (exists, may need updates in Story 4.4)
- No new directories needed

### References

- [Source: docs/adrs/ADR-077-semantic-overlap-detection-classification-resolution.md] — Full algorithm spec
- [Source: docs/adrs/ADR-019-ml-dependency-policy.md] — No ML deps; Porter Stemmer is compatible
- [Source: docs/adrs/ADR-001-trigger-matching-algorithm.md] — Existing blocklist and threshold
- [Source: _bmad-output/planning-artifacts/architecture.md#Implementation Patterns] — Code placement rules
- [Source: _bmad-output/planning-artifacts/epics.md#Story 4.1] — Full acceptance criteria
- [Source: collect_usage.py:791-845] — Existing overlap detection code to extend

## Dev Agent Record

### Agent Model Used

Claude Opus 4.5 (claude-opus-4-5-20251101)

### Debug Log References

None — clean implementation with no blocking issues.

### Completion Notes List

- Added `nltk` to inline script deps and dev-dependencies for test env
- Implemented `tokenize_and_stem()` with lazy-initialized PorterStemmer, splitting on spaces/hyphens/underscores, stripping punctuation, removing blocklisted words, returning frozenset
- Added `_jaccard_similarity()` helper for set comparison
- Added `SEMANTIC_DETECTION_ENABLED` and `SEMANTIC_THRESHOLD` constants
- Extended exact-match overlap dicts with migration defaults (classification, detection_method, similarity, intentional, hint)
- Added semantic detection block after exact-match: builds stemmed token sets, skips already-flagged pairs (AC-3), computes Jaccard similarity, assigns MEDIUM/LOW severity
- 25 new tests covering all 7 ACs; 390 total tests pass (0 regressions)

### File List

- `observability/skills/observability-usage-collector/scripts/collect_usage.py` — Modified: added nltk dep, import string, tokenize_and_stem(), _jaccard_similarity(), constants, semantic detection block, migration defaults
- `observability/tests/test_semantic_detection.py` — New: 25 tests for tokenization, Jaccard similarity, and semantic overlap detection
- `observability/pyproject.toml` — Modified: added nltk to dev-dependencies
- `observability/uv.lock` — Modified: updated lockfile with nltk dependency resolution

## Change Log

- 2026-01-30: Story 4.1 implemented — token-set semantic detection with Porter Stemmer, Jaccard similarity, feature flag, migration defaults, and 25 tests
