---
stepsCompleted: [1, 2, 3, 4, 5, 6, 7, 8]
status: 'complete'
completedAt: '2026-01-28'
inputDocuments:
  - _bmad-output/planning-artifacts/prd.md
  - _bmad-output/planning-artifacts/product-brief-bglowacki-marketplace-2026-01-28.md
  - _bmad-output/planning-artifacts/research/market-claude-code-plugin-ecosystem-research-2026-01-28.md
  - docs/architecture.md
  - docs/index.md
  - docs/adrs/ADR-001-trigger-matching-algorithm.md
  - docs/adrs/ADR-019-ml-dependency-policy.md
  - docs/adrs/ADR-035-find-matches-test-coverage.md
  - docs/adrs/ADR-067-implementation-priority.md
workflowType: 'architecture'
project_name: 'bglowacki-marketplace'
user_name: 'Bartek'
date: '2026-01-28'
classification:
  projectType: developer_tool
  projectContext: brownfield
  complexity: low
---

# Architecture Decision Document

_This document builds collaboratively through step-by-step discovery. Sections are appended as we work through each architectural decision together._

## Project Context Analysis

### Requirements Overview

**Functional Requirements:**

| ID | Requirement | Architectural Impact |
|----|-------------|---------------------|
| FR-1 | Usage Visibility | Collector outputs structured JSON; classify skills as Active/Dormant/Unused |
| FR-2 | Missed Opportunity Detection | Confidence scoring in `find_matches()`; threshold unification |
| FR-3 | Actionable Output | Agent presents summary dashboard → drill-down; safety constraints on deletions |

**Non-Functional Requirements:**

| NFR | Constraint | Source |
|-----|-----------|--------|
| No ML dependencies | Rule-based matching only | ADR-019 |
| Test-first development | Tests for `find_matches()` before logic changes | ADR-035 |
| Hook timeout | 10 seconds max | Plugin manifest |
| Schema versioning | Semantic versioning for data schema | ADR-020 |
| Local-only | No external network calls | Architecture doc |
| Internal data structures | Use Python dataclasses for type safety | Party Mode |
| JSON output | Keep as dicts for schema v3.0 compatibility | Party Mode |

**Scale & Complexity:**

- **Primary domain:** Python CLI scripts + Markdown agent prompts
- **Complexity level:** Low (brownfield enhancement)
- **Estimated components:** 2 (Collector modifications, Agent improvements)

### Technical Constraints & Dependencies

| Constraint | Impact |
|------------|--------|
| `uv run --script` compatibility | Scripts must be standalone; no complex package deps |
| Existing schema v3.0 | New output fields must extend, not break |
| 76 existing ADRs | Many decisions already made; follow established patterns |
| Dual codebase | Collector = Python, Agent = Markdown (different implementation approaches) |
| Python 3.10+ | Built-in `@dataclass` available for internal types |

### Cross-Cutting Concerns Identified

1. **Confidence Scoring Formula** - Affects FR-2.2.1; must be defined before implementation
2. **Threshold Unification** - `≥3 chars` unified across `find_matches()` and `compute_setup_profile()`
3. **Test Coverage** - Prerequisite for all algorithm changes (ADR-035)
4. **Safety Constraints** - Opt-in cleanup mode affects agent output design
5. **MatchResult Dataclass** - New return type for `find_matches()` (internal use, dict for JSON output)

### Confidence Scoring Formula (Architecture Decision)

| Factor | Score Range | Calculation |
|--------|-------------|-------------|
| `length_score` | 0-100 | `min(100, trigger_length * 10)` — 10+ char trigger = 100% |
| `specificity_score` | 0-100 | Single word = 50, multi-word phrase = 100 |
| `position_score` | 0-100 | Match in first 20 chars = 100, decays linearly to 0 at char 200 |

**Final formula:** `confidence = (length_score + specificity_score + position_score) / 3`

**Threshold:** Only surface matches with confidence > 80%

### MatchResult Data Structure (Architecture Decision)

```python
@dataclass
class MatchResult:
    skill: SkillOrAgent
    matched_triggers: list[str]
    confidence: float  # 0.0 - 1.0

    def to_dict(self) -> dict:
        """For JSON output compatibility with schema v3.0"""
        return {
            "skill_name": self.skill.name,
            "matched_triggers": self.matched_triggers,
            "confidence": self.confidence
        }
```

### Parallel Work Tracks

| Track | Status | Work Items |
|-------|--------|------------|
| **Track A (Blocked)** | Waiting on ADR-035 | Tests → US-2.0 (confidence) → US-2.1 (detection) |
| **Track B (Unblocked)** | Can start now | US-1.1/1.2 (usage collection), US-3.0 (empty states) |

**Dependency Chain (Track A):**
```
US-2.0 (tests + confidence) → US-2.1 (missed detection) → US-3.1 (dashboard) → US-3.2 (walk-through)
```

## Technology Stack (Existing)

### Brownfield Context

This is a **brownfield enhancement project** (v2.4.6). All major technology decisions are established:

### Collector (Python)

| Component | Technology | Notes |
|-----------|------------|-------|
| Runtime | Python 3.10+ | Required for `@dataclass` |
| Package manager | uv | `uv run --script` for standalone operation |
| Dependencies | pyyaml | Minimal by design (ADR-019) |
| Testing | pytest | `uv run pytest tests/` |
| Style | PEP 8 | No external formatter required |

### Agent Prompts (Markdown)

| Component | Technology | Notes |
|-----------|------------|-------|
| Format | Markdown + YAML frontmatter | Standard Claude Code skill/agent format |
| Triggers | YAML `triggers:` array | Matched by Claude Code |
| Tools | Claude Code built-in | Read, Edit, Bash, etc. |

### Data Flow

```
Session JSONL → collect_usage.py → JSON output → usage-insights-agent → recommendations
```

### No New Stack Decisions Required

All technology choices are locked by existing codebase. Architectural decisions focus on:
1. Algorithm design (confidence scoring formula)
2. Data structures (MatchResult dataclass)
3. Test coverage strategy
4. Agent prompt improvements

## Core Architectural Decisions

### Decision Priority Analysis

**Critical Decisions (Block Implementation):**
1. Testing strategy for `find_matches()` - prerequisite per ADR-035
2. Schema evolution approach - affects all downstream consumers

**Important Decisions (Shape Architecture):**
1. Agent summary dashboard structure
2. Safety classification levels
3. Impact scoring formula for recommendations

**Deferred Decisions (Post-MVP):**
- Redundancy detection algorithm (v1.1)
- Pattern surfacing heuristics (v1.1)
- Auto-fix generation approach (v1.1)

### Testing Strategy

**Decision:** Implement 11 test cases for `find_matches()` before any logic changes.

| Test | Assertion |
|------|-----------|
| `test_exact_name_match` | Skill name always matches regardless of triggers |
| `test_minimum_trigger_length` | Triggers < 3 chars are skipped |
| `test_uppercase_3char_rule` | "TDD" matches, "tdd" in prose doesn't |
| `test_common_word_blocklist` | "the", "add", "run", "fix" excluded |
| `test_word_boundary_matching` | "debug" matches "debug this", not "debugging" |
| `test_multiple_trigger_threshold` | Requires 2+ trigger matches OR exact name match |
| `test_case_insensitive` | Matching is case-insensitive (except 3-char uppercase rule) |
| `test_confidence_score_calculation` | Formula: `(length + specificity + position) / 3` (parameterized) |
| `test_empty_prompt` | Empty string returns no matches, doesn't crash |
| `test_unicode_triggers` | Handles non-ASCII triggers (café, émoji, etc.) |
| `test_very_long_prompt` | Position score behaves correctly for 2000+ char prompts |

**Note:** Use `@pytest.mark.parametrize` for confidence calculation tests to cover multiple input combinations.

**Rationale:** Matches ADR-035 requirements; edge cases prevent production surprises; enables safe refactoring.

### Agent Summary Dashboard Structure

**Decision:** Three-tier presentation - Stats → Top 3 → Drill-down

```
## Usage Analysis Summary

**Period:** Last {N} days | **Sessions:** {count} | **Projects:** {count}

### Quick Stats
- Active skills: X/Y (Z%)
- Dormant skills: X/Y (triggers matched, never used)
- Unused skills: X/Y (no trigger matches)
- Missed opportunities: X (high confidence)

### Top 3 Recommendations (by impact score)
1. 🔴 {highest_impact_item} (impact: 0.92)
2. 🟡 {second_impact_item} (impact: 0.78)
3. 🟢 {third_item_or_positive_note} (impact: 0.65)

Select category: [1] Missed Opportunities [2] Dormant Skills [3] Full Report
```

**Rationale:** Prevents information overload; lets user choose depth; aligns with FR-3.1.0.

### Impact Scoring Formula

**Decision:** Rank recommendations by weighted impact score.

```python
impact_score = (
    confidence * 0.4 +    # How sure are we this is a real issue?
    frequency * 0.4 +     # How often did this pattern occur?
    recency * 0.2         # Recent issues > old issues
)
```

| Factor | Range | Calculation |
|--------|-------|-------------|
| `confidence` | 0.0-1.0 | From MatchResult.confidence |
| `frequency` | 0.0-1.0 | `min(1.0, occurrence_count / 20)` — 20+ occurrences = 1.0 |
| `recency` | 0.0-1.0 | `1.0 - (days_since_last / analysis_period)` |

**Rationale:** Balances certainty, frequency, and freshness; prevents old low-confidence matches from ranking high.

### Safety Classification

**Decision:** Three-level safety system with minimum data threshold.

| Level | Criteria | User Sees |
|-------|----------|-----------|
| **NEVER SUGGEST** | Has trigger matches in period | Nothing (not mentioned) |
| **INSUFFICIENT DATA** | Cleanup mode ON but <20 sessions analyzed | "Insufficient data for cleanup recommendations. Extend analysis period or analyze more sessions." |
| **REVIEW CAREFULLY** | Zero triggers + no deps + cleanup mode ON + **≥20 sessions** | "Consider reviewing: {skill} - no matches in {N} days. REVIEW CAREFULLY before removing." |
| **DORMANT** | Triggers match but skill never invoked | "Improve triggers for: {skill} - matched {N} times but never used" |

**Minimum Session Threshold:** 20 sessions required before any cleanup suggestions.

**Rationale:** Protects trust metric; prevents false positives from short analysis windows (holidays, new projects); deletion is opt-in and always flagged.

### Schema Evolution

**Decision:** Update schema to v3.1 with confidence field. No backward compatibility needed.

**Schema v3.1:**
```json
{
  "_schema": {"version": "3.1"},
  "potential_matches_detailed": [
    {"skill_name": "tdd", "matched_triggers": ["TDD", "test-driven"], "confidence": 0.85}
  ]
}
```

**Rationale:** Personal tool; no external consumers to support; clean break simplifies code.

### Decision Impact Analysis

**Implementation Sequence:**
1. Add tests for `find_matches()` (11 tests, unblocks everything)
2. Fix threshold inconsistency (≥3 unified)
3. Add MatchResult dataclass + confidence calculation
4. Add impact scoring calculation
5. Update JSON output to include confidence (v3.1)
6. Update agent prompt for new dashboard format + impact scores
7. Add safety classification with session threshold to agent logic

**Cross-Component Dependencies:**
- Collector changes (1-5) must complete before agent changes (6-7)
- Schema bump (5) affects both collector output and agent consumption
- Impact scoring (4) used by both collector (pre-compute) and agent (display)

## Implementation Patterns & Consistency Rules

### Conflict Points Addressed

5 potential AI agent conflict points identified and resolved for new code.

### Python Code Patterns

**Dataclass Placement:**
```python
# At TOP of collect_usage.py, after imports, before other classes
@dataclass
class MatchResult:
    skill: SkillOrAgent
    matched_triggers: list[str]
    confidence: float  # 0.0 - 1.0
```
**Rationale:** Keep all code in one file per ADR-042 (`uv run --script` compatibility)

**Function Organization:**
- Helper functions near the functions that use them
- Public functions at module level
- No separate `models.py` or `utils.py` - everything in `collect_usage.py`

### Test Patterns

**Test File Naming:**
```
observability/tests/test_find_matches.py
```

**Test Function Naming:** Verbose, describes what's being tested
```python
# Good
def test_find_matches_with_empty_prompt_returns_empty_list():
def test_find_matches_with_uppercase_3char_trigger_matches():
def test_confidence_score_with_multiword_trigger_returns_100():

# Bad
def test_empty():
def test_uppercase():
def test_multiword():
```

**Parameterized Tests:**
```python
@pytest.mark.parametrize("trigger,expected", [
    ("TDD", 0.3),
    ("debugging", 0.9),
    ("test-driven development", 1.0),
])
def test_length_score_calculation(trigger, expected):
    assert calculate_length_score(trigger) == expected
```

### Data Format Patterns

**Confidence Representation:**
| Context | Format | Example |
|---------|--------|---------|
| Internal (Python) | Float 0.0-1.0 | `0.85` |
| JSON output | Float 0.0-1.0 | `"confidence": 0.85` |
| Agent display | Percentage string | `"85%"` |

**Conversion:**
```python
# In collector (internal)
match.confidence = 0.85

# In JSON output
{"confidence": 0.85}

# In agent prompt (display)
f"Confidence: {confidence * 100:.0f}%"  # "Confidence: 85%"
```

**Impact Score:**
- Pre-computed in collector
- Stored in JSON output as float 0.0-1.0
- Agent displays as-is (no re-computation)

```json
{
  "potential_matches_detailed": [
    {
      "skill_name": "tdd",
      "matched_triggers": ["TDD"],
      "confidence": 0.85,
      "impact_score": 0.78
    }
  ]
}
```

### Agent Output Patterns

**Dashboard Format:** Plain markdown with emoji indicators

```markdown
## Usage Analysis Summary

**Period:** Last 7 days | **Sessions:** 42 | **Projects:** 3

### Quick Stats
- Active skills: 8/12 (67%)
- Dormant skills: 3/12 (triggers matched, never used)
- Missed opportunities: 15 (high confidence)

### Top 3 Recommendations
1. 🔴 **TDD skill** - Triggered 12 times, never used (85% confidence)
2. 🟡 **debug** - Similar to systematic-debugging (72% confidence)
3. 🟢 **commit** - Working well, 23 uses
```

**Emoji Usage:**
| Emoji | Meaning |
|-------|---------|
| 🔴 | High priority action needed |
| 🟡 | Medium priority / warning |
| 🟢 | Positive / working well |

### Enforcement Guidelines

**All AI Agents MUST:**
1. Place new dataclasses at top of `collect_usage.py`, not in separate files
2. Use verbose test function names describing the test case
3. Store confidence as float 0.0-1.0 internally and in JSON
4. Pre-compute impact scores in collector, not in agent
5. Use plain markdown with emoji in agent output (no code blocks for data)

**Pattern Verification:**
- Run `uv run pytest tests/` - tests must pass
- Check JSON output validates against schema
- Agent output should be readable without tooling

### Anti-Patterns to Avoid

```python
# BAD: Separate models file
from observability.models import MatchResult  # Breaks uv run --script

# BAD: Short test names
def test_empty():  # What's being tested?

# BAD: Inconsistent confidence representation
{"confidence": 85}  # Is this 85% or 0.85?

# BAD: Computing impact in agent
impact = compute_impact(match)  # Should be pre-computed
```

## Project Structure & Boundaries

### Complete Project Directory Structure

```
bglowacki-marketplace/
├── .claude-plugin/
│   └── marketplace.json              # Marketplace manifest
├── observability/                    # Main plugin directory
│   ├── .claude-plugin/
│   │   └── plugin.json               # Plugin manifest (v2.4.6 → v3.0)
│   ├── pyproject.toml                # uv dependencies (pyyaml, pytest)
│   ├── README.md
│   ├── CHANGELOG.md
│   ├── SCHEMA_CHANGELOG.md           # Schema version history (update for v3.1)
│   │
│   ├── hooks/
│   │   └── generate_session_summary.py   # Stop hook (no changes needed)
│   │
│   ├── skills/
│   │   ├── observability-usage-collector/
│   │   │   ├── SKILL.md              # Skill definition
│   │   │   └── scripts/
│   │   │       └── collect_usage.py  # 📍 MAIN CHANGES HERE
│   │   │
│   │   └── observability-workflow-optimizer/
│   │       └── SKILL.md
│   │
│   ├── agents/
│   │   ├── usage-insights-agent.md   # 📍 Dashboard + safety updates
│   │   ├── usage-setup-analyzer.md
│   │   ├── usage-pattern-detector.md
│   │   └── usage-finding-expander.md
│   │
│   ├── commands/
│   │   ├── collect-usage.md
│   │   └── optimize-workflow.md
│   │
│   ├── tests/
│   │   ├── __init__.py
│   │   ├── conftest.py               # Shared fixtures
│   │   ├── test_find_matches.py      # 📍 NEW: 11 tests (ADR-035)
│   │   ├── test_confidence_scoring.py # 📍 NEW: parameterized tests
│   │   ├── test_session_parsing.py
│   │   ├── test_outcome_detection.py
│   │   ├── test_workflow_stages.py
│   │   ├── test_yaml_frontmatter.py
│   │   └── test_code_sync.py
│   │
│   └── docs/
│       └── plans/                    # Historical design docs
│
└── docs/
    ├── index.md
    ├── architecture.md
    ├── project-overview.md
    └── adrs/                         # 76 ADRs
```

### Requirements to Structure Mapping

**Epic 1: Usage Collection (Collector - Python)**

| Story | File | Changes |
|-------|------|---------|
| US-1.1 | `collect_usage.py` | Improve session parsing, add progress indicator |
| US-1.2 | `collect_usage.py` | Add Active/Dormant/Unused classification logic |

**Epic 2: Missed Opportunity Detection (Collector - Python)**

| Story | File | Changes |
|-------|------|---------|
| US-2.0 | `test_find_matches.py` | NEW FILE: 11 tests for `find_matches()` |
| US-2.0 | `test_confidence_scoring.py` | NEW FILE: parameterized confidence tests |
| US-2.0 | `collect_usage.py:L1-50` | Add `MatchResult` dataclass |
| US-2.0 | `collect_usage.py:L974-1052` | Add confidence scoring to `find_matches()` |
| US-2.1 | `collect_usage.py` | Implement missed opportunity detection |
| US-2.2 | `collect_usage.py` | Add confidence explanations to output |

**Epic 3: Actionable Output (Agent - Markdown)**

| Story | File | Changes |
|-------|------|---------|
| US-3.0 | `usage-insights-agent.md` | Add empty state handling |
| US-3.1 | `usage-insights-agent.md` | Add summary dashboard format |
| US-3.2 | `usage-insights-agent.md` | Add drill-down walkthrough |
| US-3.3 | `usage-insights-agent.md` | Add safety classification + cleanup mode |

### Architectural Boundaries

**Data Flow Boundary:**
```
┌─────────────────┐     JSON      ┌───────────────────┐
│  collect_usage  │ ───────────▶  │ usage-insights    │
│     .py         │    output     │     -agent.md     │
└─────────────────┘               └───────────────────┘
        │                                 │
        ▼                                 ▼
  Session JSONL                    User recommendations
  (~/.claude/projects/)            (conversational)
```

**Boundary Contract:** JSON output schema v3.1
- Collector produces JSON with `confidence` and `impact_score` fields
- Agent consumes JSON, displays percentages and recommendations
- No direct function calls between collector and agent

**Test Boundary:**
```
observability/tests/
├── test_find_matches.py        # Unit tests for matching logic
├── test_confidence_scoring.py  # Unit tests for confidence formula
├── test_session_parsing.py     # Unit tests for JSONL parsing
└── ...
```
- All tests run via `uv run pytest tests/`
- Tests must pass before any PR

### File Change Summary

**Files to CREATE:**
1. `observability/tests/test_find_matches.py` - 11 test cases
2. `observability/tests/test_confidence_scoring.py` - parameterized tests

**Files to MODIFY:**
1. `collect_usage.py` - Add MatchResult dataclass, confidence scoring, impact calculation
2. `usage-insights-agent.md` - Add dashboard, safety classification, walkthrough
3. `SCHEMA_CHANGELOG.md` - Document v3.1 changes
4. `plugin.json` - Bump version to 3.0

**Files UNCHANGED:**
- `generate_session_summary.py` (Stop hook)
- Other agents, commands, skills

## Architecture Validation Results

### Coherence Validation ✅

**Decision Compatibility:** All 4 key decision pairs validated compatible
**Pattern Consistency:** Naming, tests, data formats aligned
**Structure Alignment:** Changes map to existing structure

### Requirements Coverage ✅

| Category | Items | Covered |
|----------|-------|---------|
| Functional Requirements | 7 FRs | 7/7 ✅ |
| Non-Functional Requirements | 4 NFRs | 4/4 ✅ |
| User Stories | 8 stories | 8/8 ✅ |

### Implementation Readiness ✅

**AI Agent Can:**
- Follow confidence formula exactly
- Implement MatchResult dataclass as specified
- Create dashboard with provided template
- Apply safety classification rules

### Architecture Completeness Checklist

- [x] Project context analyzed (brownfield v2.4.6)
- [x] Technical constraints identified (ADR-019, ADR-035, 10s timeout)
- [x] Critical decisions documented (confidence, impact, safety)
- [x] Implementation patterns defined (naming, testing, data formats)
- [x] Project structure mapped (files to create/modify)
- [x] Requirements to code mapping complete

### Architecture Readiness Assessment

**Overall Status:** READY FOR IMPLEMENTATION

**Confidence Level:** High

**Key Strengths:**
1. Brownfield enhancement - minimal risk
2. Clear dependency chain (tests → confidence → detection)
3. Parallel tracks identified (Track A blocked, Track B unblocked)
4. Concrete code examples provided

**First Implementation Priority:**
```bash
cd observability && uv run pytest tests/  # Verify existing tests pass
# Then create test_find_matches.py per US-2.0
```

