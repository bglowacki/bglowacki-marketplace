# ADR-077: Semantic Overlap Detection, Classification, and Resolution

**Status:** ACCEPTED
**Date:** 2026-01-30
**Category:** Methodology
**Relates To:** ADR-019 (no ML dependencies for core analysis)
## Context

The current overlap detection (collect_usage.py:793-845) uses exact string matching on lowercased triggers. This has gaps in two areas:

**Detection gaps:**

1. **Morphological variants** like "debug" vs "debugging" are not detected as overlapping
2. **Phrase-level overlap** like "code review" vs "review changes" is missed entirely
3. **Intentional overlaps** (e.g., command delegates to same-name skill) are flagged as problems, eroding trust in the analysis

**Output gaps:**

4. **No resolution guidance** — users see warnings but don't know what to do

## Data Model

Every overlap has two orthogonal dimensions:

| Dimension | Values | Purpose |
|-----------|--------|---------|
| **Severity** | HIGH, MEDIUM, LOW, INFO | How impactful is this overlap? |
| **Classification** | COLLISION, SEMANTIC, PATTERN | What kind of overlap is this? |

These are independent. A PATTERN overlap can have INFO severity (well-architected delegation). A SEMANTIC overlap can have MEDIUM severity (worth reviewing). A COLLISION is always HIGH.

#### Severity Assignment Rules

| Classification | Condition | Severity |
|---------------|-----------|----------|
| COLLISION | Always | HIGH |
| SEMANTIC | Jaccard ≥ 0.8 | MEDIUM |
| SEMANTIC | Jaccard ≥ 0.4 and < 0.8 | LOW |
| PATTERN | Always (v1 heuristic) | INFO |

### Overlap Schema

```python
{
    "trigger": str,              # original trigger text
    "components": list[str],     # involved component names
    "severity": str,             # HIGH | MEDIUM | LOW | INFO
    "classification": str,       # COLLISION | SEMANTIC | PATTERN
    "detection_method": str,     # "exact" | "stemmed"
    "similarity": float | None,  # Jaccard score for stemmed matches
    "intentional": bool,         # True for PATTERN overlaps
    "hint": str,                 # one-line resolution guidance
}
```

## Decision

### ADR-019 Compatibility

ADR-019 prohibits ML dependencies for core analysis — meaning no model inference, embedding generation, or statistical classifiers. The Porter Stemmer from `nltk` is a deterministic suffix-stripping algorithm (pure string manipulation, no trained models, no vector math). It produces identical output for identical input with no learning component. Using `nltk` solely for `nltk.stem.porter.PorterStemmer` does not conflict with the intent of ADR-019. The dependency is auto-installed via uv inline script metadata, keeping the main project dependency list unchanged.

### Part 1: Token-Set Detection with Stemming

**Token-set matching with suffix stripping and Jaccard similarity.**

#### Algorithm

1. **Tokenize** trigger into words (split on spaces, hyphens, underscores; strip punctuation)
2. **Stem** each token using the Porter Stemmer algorithm via `nltk.stem.porter` (installed automatically via uv inline script dependencies). Note: the `stemming` package is Python 2 only; use `nltk` instead.
3. **Remove blocklisted** common words (existing blocklist)
4. **Guard**: if either token set is empty after processing, skip comparison
5. **Compare** two triggers' stemmed token sets via Jaccard similarity: `|A ∩ B| / |A ∪ B|`
6. **Threshold:** Jaccard ≥ 0.4 → flag as `classification: SEMANTIC`

Severity for SEMANTIC overlaps is determined by Jaccard score:
- Jaccard ≥ 0.8 → MEDIUM
- Jaccard ≥ 0.4 → LOW

#### Detection Precedence

Exact-match detection runs first. If a trigger pair is already flagged as a COLLISION (exact match), skip semantic comparison for that pair. This avoids duplicate findings for the same pair and ensures COLLISION classification is never downgraded to SEMANTIC.

#### Why This Over Alternatives

| Option | Verdict |
|--------|---------|
| Suffix stripping on whole strings | Only handles single-word variants, misses phrase overlap |
| Ad-hoc suffix stripping | Zero deps but produces incorrect stems (e.g., "action"→"ac", "give"→"g"); no min-length guard fixes all cases |
| **Porter Stemmer (`nltk`)** | **Correct stemming, widely used, auto-installs via uv inline deps; `stemming` package is Python 2 only. Note: nltk is an NLP library but the Porter Stemmer is deterministic text processing (suffix stripping), not ML inference — this does not conflict with ADR-019's intent to avoid ML models in core analysis** |
| Levenshtein distance | False positives for short triggers, doesn't handle phrase reordering |
| Semantic embeddings | Blocked by ADR-019 (no ML dependencies for core analysis) |
| **Token-set with Porter stemming** | Handles both sub-problems, correct stemming, deterministic, minimal pure-Python dependency |

#### Examples

| Trigger A | Trigger B | Stemmed A | Stemmed B | Jaccard | Classification |
|-----------|-----------|-----------|-----------|---------|---------------|
| debug | debugging | {debug} | {debug} | 1.0 | SEMANTIC (MEDIUM) |
| code review | review changes | {code, review} | {review, chang} | 0.33 | — (below threshold) |
| code review | review code | {code, review} | {code, review} | 1.0 | SEMANTIC (MEDIUM) |
| test driven | write tests | {test, driven} | {write, test} | 0.33 | — (below threshold) |
| systematic debugging | debug systematically | {systemat, debug} | {debug, systemat} | 1.0 | SEMANTIC (MEDIUM) |

Note: The 0.4 threshold is a conservative starting point, not empirically derived. Near-threshold examples:

| Trigger A | Trigger B | Stemmed A | Stemmed B | Jaccard | Classification |
|-----------|-----------|-----------|-----------|---------|---------------|
| scan secrets | secret scanner | {scan, secret} | {secret, scan} | 1.0 | SEMANTIC (MEDIUM) |
| run test | test runner | {run, test} | {test, run} | 1.0 | SEMANTIC (MEDIUM) |
| analyze usage | usage analysis report | {analyz, usag} | {usag, analyz, report} | 0.67 | SEMANTIC (MEDIUM) |
| check code quality | quality review | {check, code, qual} | {qual, review} | 0.25 | — (below threshold) |
| optimize build | build cache setup | {optim, build} | {build, cach, setup} | 0.25 | — (below threshold) |
| deploy service | service deployment check | {deploy, servic} | {servic, deploy, check} | 0.67 | SEMANTIC (MEDIUM) |

#### Threshold Analysis

At the 0.4 threshold, the following below-threshold pairs are **acceptable misses** (not true overlaps):
- "code review" vs "review changes" (0.33) — different intent: one is a review action, the other is a change-tracking action. Sharing one word is insufficient.
- "test driven" vs "write tests" (0.33) — different workflows: TDD methodology vs test authoring.
- "check code quality" vs "quality review" (0.25) — loosely related but distinct scopes.
- "optimize build" vs "build cache setup" (0.25) — different concerns: optimization vs caching configuration.

**Known gap accepted at 0.4:** No below-threshold pairs in the current examples represent true overlaps that should be caught. If future real-world data reveals missed true overlaps in the 0.3–0.4 range, lower the threshold accordingly. The pre-release validation plan (below) is designed to surface such cases before shipping.

#### Pre-Release Validation Plan

Before merging, run the semantic detector against all triggers from installed plugins in this repository:
1. Collect all triggers via `collect_usage.py --quick-stats`
2. Run the new semantic detection on the full trigger set
3. Manually review every flagged pair — confirm true positives, record false positives
4. Adjust `SEMANTIC_THRESHOLD` if false-positive rate exceeds 20% of flagged pairs
5. Document the validation results (trigger count, pairs checked, FP rate) in the PR description

#### Runtime Feature Flag

Add a `SEMANTIC_DETECTION_ENABLED` boolean constant (default `True`). When `False`, skip all stemmed/Jaccard comparisons and only run exact-match detection. This allows disabling semantic detection without a code change if it produces excessive noise post-release.

#### Threshold Tuning

The 0.4 threshold is a starting point to be validated by the pre-release plan above. Post-release, tune based on production data — lowering catches more overlaps but risks noise; raising reduces false positives but misses real conflicts. The `SEMANTIC_THRESHOLD` constant allows easy adjustment.

### Part 2: Intentional Overlap Classification (PATTERN)

#### v1 (MVP): Same-Source Heuristic

If a skill and command share the same name AND the same source plugin → classify as PATTERN, severity INFO.

This is a **positive recognition** of a known design pattern, not a warning. Display as architecture insight:
> "Command `brainstorming` delegates to skill `brainstorming` (superpowers) — assumed delegation pattern (v1 heuristic)"

v1 output must include the "(v1 heuristic)" qualifier so users understand this is an assumption based on name + source matching, not verified delegation.

#### v2 (Future): Evidence-Based Detection + Override Config

Upgrade from heuristic to evidence-based detection:
- Check if command definition contains `disable_model_invocation: true`
- Check if command references a skill name in its definition
- Handle cross-source intentional delegation when explicitly configured
- Detect and flag broken patterns (dangling skill references) as config errors, not PATTERN
- Add `intentional_overlaps` list in plugin config to explicitly mark or suppress overlaps:
  ```yaml
  # in plugin.json or plugin config
  intentional_overlaps:
    - components: ["brainstorming-command", "brainstorming-skill"]
      reason: "Command delegates to skill"
  ```

#### Edge Cases

- Same source + same name but no actual delegation → still PATTERN in v1. This is accepted as low-risk: same-source same-name pairs without delegation are rare in practice (plugin authors typically use the naming convention intentionally). The v1 output includes the "(v1 heuristic)" qualifier to signal that delegation is assumed, not verified. Users who encounter a false positive here should add an explicit override in v2's `intentional_overlaps` config.
- Cross-source intentional delegation → remains HIGH in v1, addressed in v2
- Command references non-existent skill → not PATTERN; flag as configuration error

### Part 3: Resolution Guidance

#### Inline Hints (one sentence, in detector output)

Hints are keyed by `(classification, severity)`:

| Classification | Severity | Hint |
|---------------|----------|------|
| COLLISION (skill+skill) | HIGH | "`{a}` and `{b}` are both skills named `{name}` — rename the less specific one or merge into a single skill" |
| COLLISION (command+skill) | HIGH | "`{a}` (command) and `{b}` (skill) share name `{name}` — if same-source, this is likely an intentional delegation pattern (will be auto-classified as PATTERN/INFO); if cross-source, rename the command or configure as intentional in v2's `intentional_overlaps`" |
| COLLISION (command+command) | HIGH | "`{a}` and `{b}` are both commands named `{name}` — only one can be invoked; remove or rename the duplicate from the lower-priority plugin" |
| COLLISION (agent+other) | HIGH | "Agent `{a}` collides with {type} `{b}` on name `{name}` — rename the non-agent component to avoid routing ambiguity" |
| SEMANTIC | MEDIUM | "Triggers `{a}` and `{b}` overlap ({similarity:.0%}) — add distinct trigger prefixes, or consolidate into one component if they serve the same purpose" |
| SEMANTIC | LOW | "Minor trigger similarity ({similarity:.0%}) between `{a}` and `{b}` — no action needed unless users report misfires" |
| PATTERN | INFO | "Assumed delegation: `{command}` → `{skill}` ({source}) (v1 heuristic) — no action needed" |

#### Detailed Guidance (in walk-through skill, Story 3.3)

The walk-through skill provides interactive resolution exploration. Add an **Overlap Resolution** finding template:

```
**Problem**: {hint}
**Evidence**: Components {components} share trigger "{trigger}" (detection: {detection_method}, similarity: {similarity})
**Action**: [context-specific recommendation based on classification]
```

For HIGH severity overlaps, the hint itself must be actionable — users should not need the walk-through to understand what to do.

#### Walk-Through Interface Contract

The walk-through skill (Story 3.3) must accept overlap findings as a list of overlap dicts matching the schema defined in the Data Model section. The finding template contract:

```python
{
    "finding_type": "overlap_resolution",
    "overlap": {  # full overlap dict per schema above
        "trigger": str,
        "components": list[str],
        "severity": str,
        "classification": str,
        "detection_method": str,
        "similarity": float | None,
        "intentional": bool,
        "hint": str,
    },
    "rendered": {
        "problem": str,   # the hint text
        "evidence": str,   # "Components {components} share trigger '{trigger}' (detection: {detection_method}, similarity: {similarity})"
        "action": str,     # context-specific recommendation based on classification
    }
}
```

The detector is responsible for populating `rendered` at detection time. The walk-through skill is responsible for presentation and interactive exploration. Rendering details (formatting, ordering, grouping) are defined by Story 3.3.

## Implementation Notes

- Add `tokenize_and_stem(trigger) → frozenset` utility function near existing trigger matching code
- Apply during `compute_setup_profile()` trigger map construction
- Store both original trigger and stemmed token set — display original in output
- After detecting name collisions, check if both items share the same source plugin for PATTERN classification
- Add `classification`, `intentional`, `hint`, and `similarity` fields to overlap dict
- PATTERN overlaps: set `classification: "PATTERN"`, `severity: "INFO"`, `intentional: True`
- Walk-through skill (Story 3.3): add overlap finding template with Problem-Evidence-Action structure

## Performance

Token-set Jaccard comparison is O(n²) over all trigger pairs — n triggers produce n*(n-1)/2 comparisons, each involving tokenization, stemming, and set intersection.

**Benchmark results** (`uv run observability/scripts/benchmark_overlap_detection.py`):

The benchmark script must measure the **full detection pipeline**: tokenization, stemming, Jaccard comparison, classification, and hint generation — not just the Jaccard hot path. Results below are from the Jaccard-only benchmark and should be updated once the full pipeline benchmark is implemented:

| Triggers | Pairs | Total (ms) | Notes |
|----------|-------|------------|-------|
| 50 | 1,225 | ~1 | Jaccard only |
| 100 | 4,950 | ~3 | Jaccard only |
| 200 | 19,900 | ~8 | Jaccard only |
| 500 | 124,750 | ~40 | Jaccard only |
| 1,000 | 499,500 | ~147 | Jaccard only |

The "<200 unique triggers" estimate for real-world setups must be validated during the pre-release validation plan by reporting the actual trigger count from installed plugins. Update the benchmark script to:
1. Include tokenization + stemming + classification + hint generation in the timing
2. Accept a `--real-data` flag that runs against actual installed plugin triggers instead of synthetic data
3. Report both synthetic and real-data results in the PR description

**Mitigation (if needed):** If trigger counts grow beyond expectations, add an upper-bound guard that skips semantic detection when trigger count exceeds a configurable limit and emits a warning. Re-run the benchmark script to validate after implementation.

## Migration

The overlap schema adds new fields to an existing data structure. To maintain backward compatibility:

| New Field | Default for Existing Overlaps | Rationale |
|-----------|------------------------------|-----------|
| `classification` | `"COLLISION"` | Existing exact-match overlaps are collisions by definition |
| `intentional` | `false` | Existing overlaps were never classified as intentional |
| `hint` | `null` | Hints are generated at detection time; old data has none |
| `similarity` | `null` | Only populated for stemmed matches |
| `detection_method` | `"exact"` | Existing detection is exact string matching |

**Consumer updates required:**
- **Walk-through skill (Story 3.3):** Must handle overlaps with and without new fields during the transition. Use defaults above when fields are missing.
- **Summary dashboard (Story 3.2):** Display logic should gracefully degrade — show severity without classification if classification is absent.
- **JSON output consumers:** New fields are additive; existing fields unchanged. No breaking change for consumers that ignore unknown keys. **Implementation requirement:** audit all overlap data consumers (walk-through skill, summary dashboard, any scripts reading overlap JSON) to confirm they tolerate unknown keys before merging. Document audit results in the PR.

## Consequences

- Catches morphological and phrase-level false negatives via token-set matching
- Reduces false-positive HIGH warnings by reclassifying intentional overlaps as PATTERN
- Users get immediate actionable hints without dashboard clutter
- Detailed interactive guidance available via walk-through on demand
- Severity and classification are orthogonal — no conflation of "how bad" with "what kind"
- New test cases needed for: tokenization, stemming, Jaccard edge cases, PATTERN heuristic, hint generation
- Future: can upgrade stemming component and PATTERN detection independently
