# Story 2.3: Missed Opportunity Detection with Impact

Status: done

## Story

**As a** Power Customizer,
**I want** to see missed opportunities grouped by skill with impact scores,
**So that** I can prioritize which skills to use more.

## Acceptance Criteria

1. **AC-1: Trigger Matching with ADR-001 Rules**
   - Given user prompts in session history
   - When trigger matching runs
   - Then prompts are matched against skill/agent trigger phrases
   - And unified >= 3 character threshold is enforced
   - And 3-char uppercase acronyms (TDD, API, MCP) are permitted
   - And common words are excluded via blocklist per ADR-001

2. **AC-2: Missed Opportunity Classification**
   - Given a trigger matched but skill was not invoked in that session
   - When results are compiled
   - Then this is classified as "Missed" opportunity
   - And opportunities are grouped by skill/agent for consolidated view
   - And example prompts that triggered the match are included

3. **AC-3: Impact Score Calculation**
   - Given missed opportunities exist
   - When impact scores are calculated
   - Then formula is applied: `impact = (confidence * 0.4) + (frequency * 0.4) + (recency * 0.2)`
   - And impact scores are pre-computed in collector (not re-computed in agent)
   - And `impact_score` field is included in JSON output for each missed opportunity

4. **AC-4: High-Confidence Filtering**
   - Given matches are found
   - When results are returned
   - Then only matches with confidence > 80% are included
   - And confidence score is visible for transparency

## Tasks / Subtasks

- [x] Task 1: Implement missed opportunity detection logic (AC: 1, 2)
  - [x] For each session, compare trigger matches vs actual invocations
  - [x] Classify as "missed" when: trigger matched AND skill not invoked
  - [x] Store matched prompts as evidence

- [x] Task 2: Group opportunities by skill (AC: 2)
  - [x] Aggregate missed opportunities across sessions
  - [x] Group by skill name
  - [x] Include example prompts (up to 3 per skill)
  - [x] Count total occurrences per skill

- [x] Task 3: Implement impact score calculation (AC: 3)
  - [x] Add `calculate_frequency_score(occurrence_count: int) -> float`
    - Formula: `min(1.0, occurrence_count / 20)` (20+ = 1.0)
  - [x] Add `calculate_recency_score(days_since_last: int, analysis_period: int) -> float`
    - Formula: `1.0 - (days_since_last / analysis_period)`
  - [x] Add `calculate_impact_score(confidence: float, frequency: float, recency: float) -> float`
    - Formula: `(confidence * 0.4) + (frequency * 0.4) + (recency * 0.2)`

- [x] Task 4: Update JSON output structure (AC: 3, 4)
  - [x] Add `missed_opportunities` section to output
  - [x] Include per-skill: `skill_name`, `confidence`, `impact_score`, `occurrence_count`, `example_prompts`
  - [x] Sort by `impact_score` descending for agent consumption

- [x] Task 5: Integrate with existing collector flow (AC: 1-4)
  - [x] Call missed opportunity detection after session parsing
  - [x] Pre-compute all scores in collector
  - [x] Verify JSON output validates against schema v3.12

## Dev Notes

### Missed Opportunity Detection Algorithm

```python
def detect_missed_opportunities(
    sessions: list[SessionData],
    skills: list[SkillOrAgent]
) -> dict[str, MissedOpportunity]:
    """Identify skills that could have been used but weren't."""
    missed = {}

    for session in sessions:
        for skill in skills:
            # Get trigger matches with confidence
            matches = find_matches(skill, session.prompts)

            # Check if skill was actually invoked
            was_invoked = skill.name in session.skills_used

            # If matched but not invoked = missed opportunity
            if matches and not was_invoked:
                if skill.name not in missed:
                    missed[skill.name] = MissedOpportunity(
                        skill=skill,
                        occurrences=0,
                        example_prompts=[],
                        sessions=[],
                        avg_confidence=0.0
                    )

                missed[skill.name].occurrences += 1
                missed[skill.name].sessions.append(session.session_id)
                # Track example prompts (limit to 3)
                if len(missed[skill.name].example_prompts) < 3:
                    missed[skill.name].example_prompts.extend(
                        session.prompts[:1]  # First prompt of session
                    )

    return missed
```

### Impact Scoring Formula (Architecture Decision)

```python
def calculate_impact_score(
    confidence: float,      # From MatchResult, 0.0-1.0
    frequency: float,       # Normalized occurrence count
    recency: float          # How recently this occurred
) -> float:
    """
    Rank recommendations by weighted impact score.

    Factors:
    - confidence (40%): How sure are we this is a real issue?
    - frequency (40%): How often did this pattern occur?
    - recency (20%): Recent issues > old issues
    """
    return (confidence * 0.4) + (frequency * 0.4) + (recency * 0.2)

def calculate_frequency_score(occurrence_count: int) -> float:
    """Normalize occurrence count to 0.0-1.0 scale."""
    return min(1.0, occurrence_count / 20)  # 20+ occurrences = 1.0

def calculate_recency_score(days_since_last: int, analysis_period: int) -> float:
    """More recent = higher score."""
    return 1.0 - (days_since_last / analysis_period)
```

### JSON Output Structure

```json
{
  "_schema": {"version": "3.1"},
  "missed_opportunities": [
    {
      "skill_name": "tdd",
      "confidence": 0.85,
      "impact_score": 0.78,
      "occurrence_count": 12,
      "example_prompts": [
        "help me write tests for this function",
        "I need to add unit tests",
        "can you write TDD style"
      ],
      "sessions_affected": ["session-abc", "session-def"]
    }
  ],
  "potential_matches_detailed": [
    {
      "skill_name": "tdd",
      "matched_triggers": ["TDD", "write tests"],
      "confidence": 0.85,
      "impact_score": 0.78
    }
  ]
}
```

### Architecture Compliance

- **Pre-compute impact scores**: Calculate in collector, not agent
- **Single file**: All new functions in `collect_usage.py`
- **Schema v3.1**: Include `impact_score` field
- **Sort by impact**: Help agent prioritize recommendations

### ADR-001 Compliance Checklist

- [x] Unified >= 3 char threshold
- [x] Uppercase 3-char acronyms allowed (TDD, API, MCP)
- [x] Blocklist excludes common words
- [x] Word boundary matching enforced

### Dependencies

**This story DEPENDS ON:**
- Story 2.1: Test Suite for find_matches() (tests must exist)
- Story 2.2: Confidence Scoring (confidence must be calculated)

**This story is a PREREQUISITE FOR:**
- Story 3.2: Summary Dashboard (needs impact scores for ranking)
- Story 3.3: Findings Walk-through (needs missed opportunity data)

### References

- [Source: _bmad-output/planning-artifacts/epics.md#Story-2.3]
- [Source: _bmad-output/planning-artifacts/architecture.md#Impact Scoring Formula]
- [Source: _bmad-output/planning-artifacts/prd.md#FR-2.3]
- [Source: _bmad-output/planning-artifacts/prd.md#FR-2.4]
- [Source: docs/adrs/ADR-001] - Trigger matching algorithm

## Dev Agent Record

### Agent Model Used

Claude Opus 4.5 (claude-opus-4-5-20251101)

### Debug Log References

### Completion Notes List

- Implemented `detect_missed_opportunities()` function that iterates sessions, matches triggers via existing `find_matches()`, checks invocation status, and groups results by skill name
- Implemented three impact scoring functions: `calculate_frequency_score`, `calculate_recency_score`, `calculate_impact_score` with exact formulas from story spec
- `calculate_recency_score` clamps to 0.0 minimum to prevent negative scores for sessions beyond the analysis period
- Added `missed_opportunities` section to `generate_analysis_json` output, sorted by impact_score descending
- Added `impact_score` to each entry in `potential_matches_detailed.matches`
- Updated schema version from 3.11 to 3.12
- All functions added to `collect_usage.py` as required by architecture compliance (single file)
- Impact scores pre-computed in collector, not agent
- High-confidence filtering enforced: only matches with confidence > 0.80 included
- 23 new tests covering frequency scoring, recency scoring, impact scoring, detection logic, grouping, filtering, and sorting
- ADR-001 compliance inherited from existing `find_matches()` implementation (>= 3 char threshold, uppercase 3-char acronyms, blocklist, word boundaries)

### Change Log

| Date | Change | Author |
|------|--------|--------|
| 2026-01-29 | Story 2.3 implementation: missed opportunity detection with impact scoring | Claude Opus 4.5 |

### File List

- `observability/skills/observability-usage-collector/scripts/collect_usage.py` (modified)
- `observability/tests/test_missed_opportunities.py` (new)
