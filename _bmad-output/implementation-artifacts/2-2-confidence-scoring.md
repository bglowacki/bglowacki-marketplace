# Story 2.2: Confidence Scoring

Status: done

## Story

**As a** Power Customizer,
**I want** trigger matches to include a confidence score,
**So that** I only see high-confidence recommendations (>80%).

## Acceptance Criteria

1. **AC-1: Confidence Formula Implementation**
   - Given a trigger match is found
   - When confidence is calculated
   - Then the formula is applied:
     - `length_score = min(100, trigger_length * 10)`
     - `specificity_score = 50` (single word) or `100` (multi-word phrase)
     - `position_score = 100` at char 0, decays linearly to 0 at char 200
     - `confidence = (length_score + specificity_score + position_score) / 3`

2. **AC-2: Confidence Threshold Filtering**
   - Given matches are evaluated
   - When results are filtered
   - Then only matches with confidence > 80% are included in output

3. **AC-3: Confidence in JSON Output**
   - Given confidence scoring is added
   - When JSON output is generated
   - Then confidence score is included for each match (transparency)
   - And existing tests continue to pass
   - And new parameterized confidence tests pass

4. **AC-4: MatchResult Dataclass**
   - Given the architecture specifies MatchResult
   - When implementing confidence scoring
   - Then use the MatchResult dataclass:
     ```python
     @dataclass
     class MatchResult:
         skill: SkillOrAgent
         matched_triggers: list[str]
         confidence: float  # 0.0 - 1.0
     ```

## Tasks / Subtasks

- [x] Task 1: Add MatchResult dataclass (AC: 4)
  - [x] Add `@dataclass` definition at top of `collect_usage.py` (after imports)
  - [x] Include `skill`, `matched_triggers`, `confidence` fields
  - [x] Add `to_dict()` method for JSON output compatibility

- [x] Task 2: Implement confidence calculation functions (AC: 1)
  - [x] Add `calculate_length_score(trigger: str) -> float`
  - [x] Add `calculate_specificity_score(trigger: str) -> float`
  - [x] Add `calculate_position_score(match_position: int) -> float`
  - [x] Add `calculate_confidence(trigger: str, match_position: int) -> float`

- [x] Task 3: Integrate confidence into find_matches() (AC: 1, 2)
  - [x] Modify `find_matches()` to calculate confidence for each match
  - [x] Return `MatchResult` objects instead of plain strings
  - [x] Filter results to only include confidence > 0.80

- [x] Task 4: Update JSON output (AC: 3)
  - [x] Modify output structure to include confidence field
  - [x] Use `MatchResult.to_dict()` for serialization
  - [x] Ensure schema v3.1 compatibility

- [x] Task 5: Verify all tests pass (AC: 3)
  - [x] Run `uv run pytest tests/` to verify no regressions
  - [x] Confirm Story 2.1 test cases still pass
  - [x] Verify confidence calculation tests pass

## Dev Notes

### Confidence Scoring Formula (Architecture Decision)

| Factor | Score Range | Calculation |
|--------|-------------|-------------|
| `length_score` | 0-100 | `min(100, trigger_length * 10)` - 10+ char trigger = 100% |
| `specificity_score` | 0-100 | Single word = 50, multi-word phrase = 100 |
| `position_score` | 0-100 | Match in first 20 chars = 100, decays linearly to 0 at char 200 |

**Final formula:** `confidence = (length_score + specificity_score + position_score) / 3`

**Threshold:** Only surface matches with confidence > 80% (0.80)

### Implementation Code Pattern

```python
# Add at top of collect_usage.py, after imports

@dataclass
class MatchResult:
    skill: SkillOrAgent
    matched_triggers: list[str]
    confidence: float  # 0.0 - 1.0

    def to_dict(self) -> dict:
        """For JSON output compatibility with schema v3.1"""
        return {
            "skill_name": self.skill.name,
            "matched_triggers": self.matched_triggers,
            "confidence": self.confidence
        }

def calculate_length_score(trigger: str) -> float:
    """Longer triggers = more specific = higher confidence."""
    return min(100, len(trigger) * 10) / 100  # Normalize to 0.0-1.0

def calculate_specificity_score(trigger: str) -> float:
    """Multi-word phrases are more specific than single words."""
    return 1.0 if " " in trigger or "-" in trigger else 0.5

def calculate_position_score(match_position: int) -> float:
    """Earlier matches in prompt indicate higher intent."""
    if match_position <= 20:
        return 1.0
    elif match_position >= 200:
        return 0.0
    else:
        # Linear decay from 1.0 at char 20 to 0.0 at char 200
        return 1.0 - ((match_position - 20) / 180)

def calculate_confidence(trigger: str, match_position: int) -> float:
    """Calculate overall confidence score."""
    length = calculate_length_score(trigger)
    specificity = calculate_specificity_score(trigger)
    position = calculate_position_score(match_position)
    return (length + specificity + position) / 3
```

### Confidence Representation

| Context | Format | Example |
|---------|--------|---------|
| Internal (Python) | Float 0.0-1.0 | `0.85` |
| JSON output | Float 0.0-1.0 | `"confidence": 0.85` |
| Agent display | Percentage string | `"85%"` |

### Architecture Compliance

- **Single file**: All new functions go in `collect_usage.py`
- **Dataclasses at top**: `MatchResult` placed after imports
- **JSON output**: Use dicts via `to_dict()` for v3.1 compatibility
- **No new dependencies**: Only stdlib

### Testing Requirements

From Story 2.1, the following confidence tests should pass:
- `test_confidence_score_calculation` (parameterized)
- Verify 80% threshold filtering works correctly

### Dependencies

**This story DEPENDS ON:**
- Story 2.1: Test Suite for find_matches() (tests must exist first)

**This story is a PREREQUISITE FOR:**
- Story 2.3: Missed Opportunity Detection with Impact

### References

- [Source: _bmad-output/planning-artifacts/epics.md#Story-2.2]
- [Source: _bmad-output/planning-artifacts/architecture.md#Confidence Scoring Formula]
- [Source: _bmad-output/planning-artifacts/architecture.md#MatchResult Data Structure]
- [Source: docs/adrs/ADR-001] - Trigger matching algorithm

## Dev Agent Record

### Agent Model Used

Claude Opus 4.5 (claude-opus-4-5-20251101)

### Debug Log References

### Completion Notes List

- Added `MatchResult` dataclass after `SkillOrAgent` with `skill`, `matched_triggers`, `confidence` fields and `to_dict()` method
- Implemented 4 confidence calculation functions: `calculate_length_score`, `calculate_specificity_score`, `calculate_position_score`, `calculate_confidence`
- Modified `find_matches()` to return `MatchResult` objects with confidence scoring and configurable `min_confidence` threshold (default 0.80)
- Tracked earliest match position per skill for position-based scoring
- Updated internal callers (`_classify_component`, missed opportunity detection) to work with `MatchResult`
- Updated existing test_find_matches.py to use `min_confidence=0.0` for backward-compatible trigger matching tests
- Created comprehensive test_confidence_scoring.py with 26 tests covering dataclass, formula components, threshold filtering, and integration
- All 283 tests pass with 0 regressions

### Change Log

| Date | Change | Author |
|------|--------|--------|
| 2026-01-29 | Implemented confidence scoring (Story 2.2) | Claude Opus 4.5 |

### File List

- observability/skills/observability-usage-collector/scripts/collect_usage.py (modified)
- observability/tests/test_confidence_scoring.py (new)
- observability/tests/test_find_matches.py (modified)
