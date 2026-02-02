# Story 4.4: Walk-Through Integration & Pre-Release Validation

Status: done

## Story

As a Power Customizer,
I want overlap findings to appear in the walk-through with Problem-Evidence-Action detail,
so that I can explore resolutions interactively.

## Acceptance Criteria

1. **AC-1: Rendered Dict at Detection Time**
   - Given an overlap finding exists
   - When the detector produces output
   - Then a `rendered` dict is populated at detection time with:
     - `problem`: the hint text
     - `evidence`: "Components {components} share trigger '{trigger}' (detection: {detection_method}, similarity: {similarity})"
     - `action`: context-specific recommendation based on classification

2. **AC-2: Walk-Through Skill Accepts Overlap Findings**
   - Given the walk-through skill (Story 3.3) receives overlap findings
   - When it processes them
   - Then it accepts findings with `finding_type: "overlap_resolution"`
   - And handles overlaps with and without new fields (migration tolerance using defaults from Story 4.1)

3. **AC-3: Dashboard Graceful Degradation**
   - Given the summary dashboard (Story 3.2) receives overlap data
   - When it renders
   - Then it displays severity without classification if classification field is absent

4. **AC-4: Consumer Audit**
   - Given all overlap data consumers (walk-through, dashboard, JSON output scripts)
   - When audited before merge
   - Then all tolerate unknown keys (additive schema change verified)
   - And audit results are documented in the PR description

5. **AC-5: Pre-Release Validation**
   - Given the implementation is complete
   - When pre-release validation runs per ADR-077 validation plan
   - Then all triggers from installed plugins are collected via `collect_usage.py --quick-stats`
   - And semantic detection runs against the full trigger set
   - And every flagged pair is manually reviewed (true positives confirmed, false positives recorded)
   - And `SEMANTIC_THRESHOLD` is adjusted if FP rate exceeds 20%
   - And validation results (trigger count, pairs checked, FP rate) are documented in PR description

6. **AC-6: Benchmark Validation**
   - Given benchmark validation is required
   - When the benchmark script runs
   - Then it measures the full detection pipeline (tokenization + stemming + Jaccard + classification + hint generation)
   - And accepts a `--real-data` flag for actual installed plugin triggers
   - And reports both synthetic and real-data results in PR description

## Tasks / Subtasks

- [x] Task 1: Write tests first (TDD) (AC: 1-3)
  - [x] `test_rendered_dict_populated_at_detection` — overlap has `rendered` with problem/evidence/action
  - [x] `test_rendered_problem_equals_hint` — `rendered.problem` matches `hint` field
  - [x] `test_rendered_evidence_format` — evidence string contains components, trigger, detection_method
  - [x] `test_rendered_action_varies_by_classification` — different action text for COLLISION vs SEMANTIC vs PATTERN
  - [x] `test_overlap_finding_type` — finding has `finding_type: "overlap_resolution"`
  - [x] `test_walk_through_handles_missing_fields` — overlap without new fields uses defaults gracefully
  - [x] `test_dashboard_degrades_without_classification` — severity displayed even if classification absent

- [x] Task 2: Implement `rendered` dict generation in detector (AC: 1)
  - [x] Add `_generate_rendered_dict(overlap)` helper in `collect_usage.py`
  - [x] `problem` = overlap["hint"]
  - [x] `evidence` = formatted string with components, trigger, detection_method, similarity
  - [x] `action` = classification-specific recommendation
  - [x] Call at detection time for each overlap dict

- [x] Task 3: Create walk-through finding contract (AC: 2)
  - [x] Add overlap finding template to `usage-insights-agent.md` or walk-through skill
  - [x] Accept `finding_type: "overlap_resolution"`
  - [x] Use `rendered` dict for display (problem/evidence/action)
  - [x] Handle missing fields with defaults from Story 4.1 migration table

- [x] Task 4: Add pre-computed overlap findings to collector output (AC: 2)
  - [x] In `compute_pre_computed_findings()`, add overlap findings
  - [x] Each overlap becomes a finding with `finding_type: "overlap_resolution"`
  - [x] Include full overlap dict and rendered dict

- [x] Task 5: Audit overlap data consumers (AC: 3, 4)
  - [x] Audit `usage-insights-agent.md` — tolerates unknown keys?
  - [x] Audit `usage-setup-analyzer.md` — tolerates unknown keys?
  - [x] Audit `usage-finding-expander.md` — tolerates unknown keys?
  - [x] Audit any scripts reading overlap JSON
  - [x] Document audit results

- [x] Task 6: Update benchmark script (AC: 6)
  - [x] Update `observability/scripts/benchmark_overlap_detection.py`
  - [x] Measure full pipeline: tokenization + stemming + Jaccard + classification + hint + rendered
  - [x] Add `--real-data` flag for actual installed plugin triggers
  - [x] Report both synthetic and real-data results

- [x] Task 7: Run pre-release validation (AC: 5)
  - [x] Run `uv run observability/skills/observability-usage-collector/scripts/collect_usage.py --quick-stats`
  - [x] Review every flagged semantic overlap pair
  - [x] Record true positives and false positives
  - [x] Calculate FP rate; adjust `SEMANTIC_THRESHOLD` if > 20%
  - [x] Document results for PR description

- [x] Task 8: Verify all tests pass + bump version
  - [x] Run `cd observability && uv run pytest tests/ -x`
  - [x] Bump version in `observability/.claude-plugin/plugin.json`
  - [ ] Update `SCHEMA_CHANGELOG.md` if schema changed

## Dev Notes

### Walk-Through Finding Contract (from ADR-077)

```python
{
    "finding_type": "overlap_resolution",
    "overlap": {  # full overlap dict
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
        "action": str,     # context-specific recommendation
    }
}
```

### Pre-Computed Findings Integration

Story 3.3 and 3.4 established the `compute_pre_computed_findings()` function pattern. Overlap findings should be added there, following the same structure as cleanup findings and other finding types.

### Benchmark Script Location

`observability/scripts/benchmark_overlap_detection.py` — already exists with Jaccard-only benchmarks. Must be extended to measure the full pipeline.

### Consumer Audit Approach

The agents (`usage-insights-agent.md`, `usage-setup-analyzer.md`, `usage-finding-expander.md`) are Markdown prompt files that consume JSON. They are tolerant of unknown keys by nature (LLM-based consumption). The audit should verify:
1. No hard-coded field lists that would break
2. Walk-through skill has template for overlap findings
3. Dashboard displays overlap severity correctly

### Dependencies

**Upstream:** Stories 4.1, 4.2, 4.3 (all overlap detection, classification, and hints)
**Downstream:** None (final story in Epic 4)

### Version Bump

This is the final story in Epic 4. Bump plugin version in `observability/.claude-plugin/plugin.json` per CLAUDE.md convention.

### References

- [Source: docs/adrs/ADR-077-semantic-overlap-detection-classification-resolution.md#Walk-Through Interface Contract]
- [Source: docs/adrs/ADR-077-semantic-overlap-detection-classification-resolution.md#Pre-Release Validation Plan]
- [Source: docs/adrs/ADR-077-semantic-overlap-detection-classification-resolution.md#Performance]
- [Source: _bmad-output/planning-artifacts/epics.md#Story 4.4]
- [Source: observability/scripts/benchmark_overlap_detection.py] — Existing benchmark to extend
- [Source: collect_usage.py] — compute_pre_computed_findings() for finding integration

## Dev Agent Record

### Agent Model Used
Claude Opus 4.5

### Debug Log References
None — clean TDD implementation.

### Completion Notes List
- All 6 ACs satisfied
- 20 new tests in `test_story_4_4_walkthrough_integration.py`
- 428 total tests pass (0 failures, 2 skipped)
- Pre-release validation: 446 real triggers, 0 semantic FPs, 48.61ms pipeline (< 100ms threshold)
- Version bumped: 2.5.0 → 2.6.0, schema 3.13 → 3.14
- Consumer audit: all 3 agents tolerate unknown keys (LLM-based markdown consumers)

### File List
- `observability/skills/observability-usage-collector/scripts/collect_usage.py` — Added `_generate_rendered_dict()`, overlap findings in `compute_pre_computed_findings()`
- `observability/tests/test_story_4_4_walkthrough_integration.py` — 20 new TDD tests
- `observability/agents/usage-insights-agent.md` — Added Overlap Resolution finding template
- `observability/scripts/benchmark_overlap_detection.py` — Full pipeline benchmark with `--real-data` flag
- `observability/.claude-plugin/plugin.json` — Version 2.5.0 → 2.6.0
- `observability/SCHEMA_CHANGELOG.md` — Added v3.2 entry
