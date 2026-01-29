# Story 1.2: Usage Analysis Output

Status: done

## Story

**As a** Power Customizer,
**I want to** see per-skill usage counts with Active/Dormant/Unused classification,
**So that** I understand which skills are providing value.

## Acceptance Criteria

1. **AC-1: Skill Classification**
   - Given session data has been collected
   - When the collector generates output
   - Then each skill/agent is classified as:
     - **Active**: Actually invoked in the period
     - **Dormant**: Triggers matched but not invoked
     - **Unused**: No matching triggers found

2. **AC-2: Per-Skill Usage Counts**
   - Given usage data exists
   - When output is generated
   - Then per-skill usage counts include session context
   - And counts show how many times each skill was used

3. **AC-3: Per-Project Breakdown**
   - Given multiple projects have been analyzed
   - When output is generated
   - Then per-project breakdown is included
   - And each project shows its own skill usage

4. **AC-4: Usage Timestamps**
   - Given usage data exists
   - When output is generated
   - Then timestamps are included for usage timeline analysis
   - And both first and last usage times are recorded

5. **AC-5: JSON Output Metadata**
   - Given the collector completes
   - When JSON output is written
   - Then output includes schema version (v3.0)
   - And output includes collection timestamp
   - And output includes total session count analyzed

## Tasks / Subtasks

- [x] Task 1: Implement skill classification logic (AC: 1)
  - [x] Add `SkillClassification` enum or constants: `ACTIVE`, `DORMANT`, `UNUSED`
  - [x] Implement classification function that checks:
    - Active: skill invocation found in session data
    - Dormant: `find_matches()` returns match but no invocation
    - Unused: `find_matches()` returns no match
  - [x] Add classification field to output structure

- [x] Task 2: Add per-skill usage counts (AC: 2)
  - [x] Count invocations per skill across all sessions
  - [x] Track which sessions used each skill (session context)
  - [x] Add `usage_count` and `sessions_used` fields to output

- [x] Task 3: Implement per-project breakdown (AC: 3)
  - [x] Group session data by project path
  - [x] Generate per-project skill usage summaries
  - [x] Add `per_project` section to JSON output

- [x] Task 4: Add usage timestamps (AC: 4)
  - [x] Track `first_used` timestamp for each skill
  - [x] Track `last_used` timestamp for each skill
  - [x] Add timestamp fields to skill output

- [x] Task 5: Ensure JSON metadata compliance (AC: 5)
  - [x] Verify `_schema.version` is set to "3.0" (now 3.11 - schema evolution)
  - [x] Verify `collection_timestamp` is included
  - [x] Verify `total_sessions` count is included
  - [x] Run existing tests to ensure no regressions

## Dev Notes

### Current State Analysis

The collector at `collect_usage.py` already outputs JSON with session data. The key enhancement is adding **classification logic** and **structured usage reporting**.

**Key Existing Data Structures:**

```python
# SessionData (already tracks usage)
@dataclass
class SessionData:
    session_id: str
    timestamp: datetime
    prompts: list[str]
    tools_used: list[str]
    skills_used: list[str]  # Skills actually invoked
    agents_used: list[str]
    hooks_triggered: list[str]
    # ...

# SkillOrAgent (component definition)
@dataclass
class SkillOrAgent:
    name: str
    source: str  # global, project, plugin
    triggers: list[str]
    # ...
```

**Current Output Structure:**
The collector outputs JSON with `skill_usage`, `agent_usage`, but doesn't classify as Active/Dormant/Unused.

**What NEEDS TO BE ADDED:**

1. Classification logic comparing:
   - `skills_used` from SessionData (actual invocations)
   - `find_matches()` results (trigger matches in prompts)
   - Skill inventory from `discover_all_skills()`

2. New output fields:
   ```json
   {
     "skill_analysis": {
       "tdd": {
         "classification": "dormant",
         "usage_count": 0,
         "trigger_matches": 5,
         "sessions_used": [],
         "first_used": null,
         "last_used": null
       }
     }
   }
   ```

### Classification Algorithm

```python
def classify_skill(skill: SkillOrAgent, sessions: list[SessionData]) -> str:
    was_invoked = any(skill.name in s.skills_used for s in sessions)
    had_trigger_match = any(find_matches(skill, s.prompts) for s in sessions)

    if was_invoked:
        return "active"
    elif had_trigger_match:
        return "dormant"
    else:
        return "unused"
```

### Project Structure Notes

**File to modify:**
```
observability/skills/observability-usage-collector/scripts/collect_usage.py
```

**Alignment with architecture:**
- Keep all code in single file (ADR-042)
- Use dataclasses for new types (Architecture doc)
- JSON output maintains dict format for v3.0 compatibility

### Architecture Compliance

Per Architecture document:
- **Single file**: All additions go in `collect_usage.py`
- **Dataclasses**: Add new classification types using `@dataclass` at file top
- **JSON format**: Use dicts for output (schema v3.0)
- **No new dependencies**: Only stdlib + pyyaml

### Testing Standards

Run tests: `cd observability && uv run pytest tests/`

**Existing relevant tests:**
- `test_session_parsing.py` - verifies session data extraction
- `test_yaml_frontmatter.py` - verifies skill discovery

**New tests to consider:**
- Test classification logic (active/dormant/unused scenarios)
- Test per-project grouping
- Test timestamp tracking

### Previous Story Intelligence (1.1)

From Story 1.1 analysis:
- `SessionData` dataclass already tracks `skills_used`, `agents_used`
- `find_matches()` exists at L1754-1794 for trigger matching
- Error handling follows ADR-026 patterns
- Recent fixes improved YAML parsing reliability (v2.4.5, v2.4.6)

### Git Intelligence

Recent commits show:
- **v2.4.6**: Regex fallback for YAML parsing
- **v2.4.5**: SKILL.md/skill.md case handling
- Pattern: Bug fixes focus on robustness

### Dependencies

**This story DEPENDS ON:**
- Story 1.1: Session Data Collection (provides session data)

**This story is a PREREQUISITE FOR:**
- Epic 2: Missed Opportunity Detection (uses classification data)
- Story 3.2: Summary Dashboard (displays classification)

### References

- [Source: _bmad-output/planning-artifacts/prd.md#FR-1.2]
- [Source: _bmad-output/planning-artifacts/epics.md#Story-1.2]
- [Source: _bmad-output/planning-artifacts/architecture.md#Data Flow Boundary]
- [Source: docs/adrs/ADR-042] - uv run --script pattern
- [Source: docs/adrs/ADR-020] - Schema versioning

## Dev Agent Record

### Agent Model Used

Claude Opus 4.5 (claude-opus-4-5-20251101)

### Debug Log References

None - implementation proceeded smoothly with TDD approach.

### Completion Notes List

- Implemented `SkillClassification` class with ACTIVE, DORMANT, UNUSED constants
- Added `classify_skill()` and `classify_agent()` functions for classification logic
- Added `get_skill_usage_stats()` and `get_agent_usage_stats()` functions returning usage counts, sessions_used list, first_used and last_used timestamps
- Added `compute_per_project_breakdown()` function for per-project usage analysis
- Added `project_path` field to `SessionData` dataclass with "unknown" default
- Updated `generate_analysis_json()` to include new fields in discovery section
- Added `collection_timestamp` to schema metadata
- Bumped schema version to 3.11 (from 3.10)
- Created 4 new test files with 38 new tests covering all acceptance criteria

### Change Log

| Date | Change | Author |
|------|--------|--------|
| 2026-01-28 | Implemented skill classification (AC-1) | Claude Opus 4.5 |
| 2026-01-28 | Added per-skill usage counts and sessions_used (AC-2) | Claude Opus 4.5 |
| 2026-01-28 | Added per-project breakdown (AC-3) | Claude Opus 4.5 |
| 2026-01-28 | Added first_used and last_used timestamps (AC-4) | Claude Opus 4.5 |
| 2026-01-28 | Added collection_timestamp to schema (AC-5) | Claude Opus 4.5 |
| 2026-01-29 | [Review Fix] CRITICAL: Fixed project_path not populated on SessionData in main() | Code Review |
| 2026-01-29 | [Review Fix] MEDIUM: Refactored duplicated classify/stats functions into generic _classify_component/_get_component_usage_stats | Code Review |
| 2026-01-29 | [Review Fix] Added 2 regression tests for project_path population | Code Review |

### File List

**Modified:**
- observability/skills/observability-usage-collector/scripts/collect_usage.py

**New Test Files:**
- observability/tests/test_skill_classification.py
- observability/tests/test_usage_counts.py
- observability/tests/test_per_project.py
- observability/tests/test_usage_timestamps.py
- observability/tests/test_json_metadata.py
