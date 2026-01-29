---
stepsCompleted: [step-01-validate-prerequisites, step-02-design-epics, step-03-create-stories, step-04-final-validation]
workflowComplete: true
inputDocuments:
  - _bmad-output/planning-artifacts/prd.md
  - _bmad-output/planning-artifacts/architecture.md
---

# bglowacki-marketplace - Epic Breakdown

## Overview

This document provides the complete epic and story breakdown for bglowacki-marketplace, decomposing the requirements from the PRD, UX Design if it exists, and Architecture requirements into implementable stories.

## Requirements Inventory

### Functional Requirements

**FR-1: Usage Visibility**
- FR-1.1.1: Collect usage data from Claude Code session JSONL files
- FR-1.1.2: Support configurable time range via `--days N` parameter (default: 7)
- FR-1.1.3: Discover all installed skills, agents, commands, and hooks
- FR-1.1.4: Parse session logs to identify tool invocations and skill triggers
- FR-1.2.1: Generate per-skill usage counts with session context
- FR-1.2.2: Include per-project breakdown when multiple projects analyzed
- FR-1.2.3: Include timestamps for usage timeline
- FR-1.2.4: Classify each skill/agent as: Active (used), Dormant (triggers matched but not invoked), or Unused (no matching triggers)
- FR-1.3.1: Output structured JSON for agent consumption
- FR-1.3.2: Include metadata: schema version, collection timestamp, session count

**FR-2: Missed Opportunity Detection**
- FR-2.1.1: Match user prompts against skill/agent trigger phrases
- FR-2.1.2: Use unified threshold (≥3 characters) per ADR-001
- FR-2.1.3: Apply uppercase rule for 3-char acronyms (TDD, API, etc.)
- FR-2.1.4: Exclude common words via blocklist per ADR-001
- FR-2.2.1: Calculate match confidence using weighted factors (length_score + specificity_score + position_score) / 3
- FR-2.2.2: Only surface matches with >80% confidence (high confidence)
- FR-2.2.3: Include confidence score in output for transparency
- FR-2.2.4: PREREQUISITE: Implement tests for `find_matches()` before adding confidence logic (per ADR-035)
- FR-2.3.1: "Missed" = trigger matched but skill not invoked in that session
- FR-2.3.2: Group opportunities by skill/agent for consolidated recommendations
- FR-2.3.3: Include example prompts that triggered the match
- FR-2.4.1: Calculate impact score using formula: (confidence * 0.4) + (frequency * 0.4) + (recency * 0.2)
- FR-2.4.2: Pre-compute impact scores in collector for agent consumption
- FR-2.4.3: Include impact_score in JSON output for recommendation ranking

**FR-3: Actionable Output**
- FR-3.1.0: Present summary dashboard FIRST before detailed walk-through
- FR-3.1.1: Agent presents findings one-by-one within selected category
- FR-3.1.2: For each finding, provide: problem description, evidence, recommended action
- FR-3.1.3: User can accept, skip, or request more detail on each finding
- FR-3.2.1: Each recommendation includes specific action to take
- FR-3.2.2: Provide copy-paste-ready instructions where applicable
- FR-3.2.3: Explain WHY this is a recommendation (evidence-based)
- FR-3.3.1: Deletion/removal recommendations require ALL of: zero trigger matches, no hard dependencies, user opt-in to cleanup mode, always flagged as "REVIEW CAREFULLY"
- FR-3.3.2: Default behavior: Do NOT recommend deletions unless cleanup mode enabled
- FR-3.3.3: Provide rollback guidance for any recommended changes

### NonFunctional Requirements

| NFR | Requirement | Source | Validated In |
|-----|-------------|--------|--------------|
| NFR-1 | No ML dependencies - Rule-based matching only | ADR-019 | Code review (implicit) |
| NFR-2 | Test-first development - Tests before logic changes | ADR-035 | US-2.0 |
| NFR-3 | Hook timeout - 10 seconds max | Plugin manifest | US-1.1 AC |
| NFR-4 | Schema versioning - Semantic versioning | ADR-020 | US-2.0 AC |
| NFR-5 | Local-only - No external network calls | Architecture | Code review (implicit) |
| NFR-6 | uv run --script compatibility - Standalone scripts | ADR-042 | Code review (implicit) |
| NFR-7 | Collection performance - <2 min for 500 sessions | PRD | US-1.1 AC |
| NFR-8 | Safety threshold - 20 sessions minimum for cleanup | Architecture | US-3.3 AC |

### Additional Requirements

**From Architecture Document:**
- Use Python dataclasses for internal type safety (MatchResult dataclass)
- Keep JSON output as dicts for schema v3.0 compatibility
- Update schema to v3.1 with confidence field (no backward compatibility needed)
- Place new dataclasses at top of `collect_usage.py`, not in separate files
- All code in one file per ADR-042 (`uv run --script` compatibility)

**Testing Strategy (ADR-035):**
- 11 test cases for `find_matches()` required before any logic changes:
  1. test_exact_name_match
  2. test_minimum_trigger_length
  3. test_uppercase_3char_rule
  4. test_common_word_blocklist
  5. test_word_boundary_matching
  6. test_multiple_trigger_threshold
  7. test_case_insensitive
  8. test_confidence_score_calculation (parameterized)
  9. test_empty_prompt
  10. test_unicode_triggers
  11. test_very_long_prompt

**Confidence Scoring Formula:**
- length_score: min(100, trigger_length * 10)
- specificity_score: Single word = 50, multi-word phrase = 100
- position_score: Match in first 20 chars = 100, decays linearly to 0 at char 200
- Final: confidence = (length_score + specificity_score + position_score) / 3

**Impact Scoring Formula:**
- impact_score = (confidence * 0.4) + (frequency * 0.4) + (recency * 0.2)
- Pre-computed in collector, not re-computed in agent

**Safety Classification (Three-Level):**
| Level | Criteria |
|-------|----------|
| NEVER SUGGEST | Has trigger matches in period |
| INSUFFICIENT DATA | Cleanup mode ON but <20 sessions analyzed |
| REVIEW CAREFULLY | Zero triggers + no deps + cleanup mode ON + ≥20 sessions |

**Dependency Chain:**
- Tests (US-2.0) → Confidence (US-2.0) → Missed Detection (US-2.1) → Dashboard (US-3.1) → Walk-through (US-3.2)
- Parallel: US-1.x and US-3.0 can run independently

**Gap Analysis (Party Mode Review):**
The following items MUST be included in story acceptance criteria:

| Gap | Story | Required AC |
|-----|-------|-------------|
| Impact score calculation | US-2.1 | Implement FR-2.4.1-2.4.3 formula and include in output |
| Schema migration v3.0→v3.1 | US-2.0 | Acknowledge breaking change; no migration needed (personal tool) |
| Performance validation | US-1.1 | Validate <2 min for 500 sessions (NFR-7) |
| 11 test cases explicit | US-2.0 | List all 11 test cases as checkboxes in AC |
| Hook timeout validation | US-1.1 | Ensure collector respects 10s hook timeout (NFR-3) |

**Epic 3 Internal Dependencies:**
- US-3.0 (empty states): Can be implemented standalone
- US-3.1 (dashboard): REQUIRES Epic 2 completion (needs detection data + impact scores)
- US-3.2 (walk-through): REQUIRES US-3.1 (needs dashboard structure)
- US-3.3 (cleanup mode): REQUIRES Epic 2 completion (needs trigger match data)

### FR Coverage Map

| FR | Epic | Description |
|----|------|-------------|
| FR-1.1.1 | Epic 1 | Collect from JSONL files |
| FR-1.1.2 | Epic 1 | --days N parameter |
| FR-1.1.3 | Epic 1 | Discover installed components |
| FR-1.1.4 | Epic 1 | Parse session logs |
| FR-1.2.1 | Epic 1 | Per-skill usage counts |
| FR-1.2.2 | Epic 1 | Per-project breakdown |
| FR-1.2.3 | Epic 1 | Usage timestamps |
| FR-1.2.4 | Epic 1 | Active/Dormant/Unused classification |
| FR-1.3.1 | Epic 1 | JSON output format |
| FR-1.3.2 | Epic 1 | Metadata in output |
| FR-2.1.1 | Epic 2 | Trigger matching |
| FR-2.1.2 | Epic 2 | ≥3 char threshold |
| FR-2.1.3 | Epic 2 | Uppercase 3-char rule |
| FR-2.1.4 | Epic 2 | Common word blocklist |
| FR-2.2.1 | Epic 2 | Confidence scoring formula |
| FR-2.2.2 | Epic 2 | >80% confidence threshold |
| FR-2.2.3 | Epic 2 | Confidence in output |
| FR-2.2.4 | Epic 2 | Tests prerequisite (ADR-035) |
| FR-2.3.1 | Epic 2 | Missed = trigger matched, not invoked |
| FR-2.3.2 | Epic 2 | Group by skill |
| FR-2.3.3 | Epic 2 | Example prompts |
| FR-2.4.1 | Epic 2 | Impact score formula |
| FR-2.4.2 | Epic 2 | Pre-compute impact scores |
| FR-2.4.3 | Epic 2 | Impact score in output |
| FR-3.1.0 | Epic 3 | Summary dashboard first |
| FR-3.1.1 | Epic 3 | One-by-one findings |
| FR-3.1.2 | Epic 3 | Problem/evidence/action format |
| FR-3.1.3 | Epic 3 | Accept/skip/detail options |
| FR-3.2.1 | Epic 3 | Specific actions |
| FR-3.2.2 | Epic 3 | Copy-paste instructions |
| FR-3.2.3 | Epic 3 | Evidence-based why |
| FR-3.3.1 | Epic 3 | Deletion safety constraints |
| FR-3.3.2 | Epic 3 | Opt-in cleanup mode |
| FR-3.3.3 | Epic 3 | Rollback guidance |

## Epic List

### Epic 1: Usage Visibility
**User Outcome:** Users can see which skills/agents are Active (actually used), Dormant (triggers matched but not invoked), or Unused (no matching triggers) across their Claude Code sessions.

**FRs covered:** FR-1.1.1, FR-1.1.2, FR-1.1.3, FR-1.1.4, FR-1.2.1, FR-1.2.2, FR-1.2.3, FR-1.2.4, FR-1.3.1, FR-1.3.2

**Implementation notes:**
- Collector (Python) modifications
- Foundation for all other analysis
- Can start immediately (Track B - Unblocked)

---

### Epic 2: Missed Opportunity Detection
**User Outcome:** Users can identify when Claude could have used a skill but didn't, with confidence scoring that explains why each opportunity was flagged.

**FRs covered:** FR-2.1.1, FR-2.1.2, FR-2.1.3, FR-2.1.4, FR-2.2.1, FR-2.2.2, FR-2.2.3, FR-2.2.4, FR-2.3.1, FR-2.3.2, FR-2.3.3, FR-2.4.1, FR-2.4.2, FR-2.4.3

**Implementation notes:**
- Collector (Python) - confidence scoring in `find_matches()`
- **PREREQUISITE:** Tests for `find_matches()` must be implemented first (ADR-035)
- Blocked until Epic 2 Story 1 (tests) completes
- Schema update to v3.1 with confidence field

---

### Epic 3: Actionable Output
**User Outcome:** Users receive clear, prioritized recommendations with a summary dashboard, drill-down walkthrough, and safe cleanup mode for truly unused skills.

**FRs covered:** FR-3.1.0, FR-3.1.1, FR-3.1.2, FR-3.1.3, FR-3.2.1, FR-3.2.2, FR-3.2.3, FR-3.3.1, FR-3.3.2, FR-3.3.3

**Implementation notes:**
- Agent (Markdown) - `usage-insights-agent.md` modifications
- Three-tier dashboard: Stats → Top 3 → Drill-down
- Safety classification with 20-session minimum threshold
- US-3.0 (empty states) can start immediately (Track B - Unblocked)
- US-3.1+ REQUIRES Epic 2 completion

---

## Epic 1: Usage Visibility

Users can see which skills/agents are Active (actually used), Dormant (triggers matched but not invoked), or Unused (no matching triggers) across their Claude Code sessions.

### Story 1.1: Session Data Collection

**As a** Power Customizer,
**I want** to collect usage data from Claude Code session files with configurable time range,
**So that** I can analyze my actual tool usage patterns.

**FRs:** FR-1.1.1, FR-1.1.2, FR-1.1.3, FR-1.1.4

**Acceptance Criteria:**

**Given** a user with Claude Code sessions in `~/.claude/projects/`
**When** I run `collect_usage.py --days 7`
**Then** session JSONL files from the last 7 days are parsed
**And** tool invocations and skill triggers are extracted from each session
**And** all installed skills, agents, commands, and hooks are discovered via manifest files
**And** the `--days N` parameter is configurable (default: 7)

**Given** a large session history (up to 500 sessions)
**When** collection runs
**Then** it completes within 2 minutes (NFR-7)
**And** respects 10-second hook timeout constraint (NFR-3)

---

### Story 1.2: Usage Analysis Output

**As a** Power Customizer,
**I want** to see per-skill usage counts with Active/Dormant/Unused classification,
**So that** I understand which skills are providing value.

**FRs:** FR-1.2.1, FR-1.2.2, FR-1.2.3, FR-1.2.4, FR-1.3.1, FR-1.3.2

**Acceptance Criteria:**

**Given** session data has been collected
**When** the collector generates output
**Then** each skill/agent is classified as:
  - **Active**: Actually invoked in the period
  - **Dormant**: Triggers matched but not invoked
  - **Unused**: No matching triggers found

**Given** usage data exists
**When** output is generated
**Then** per-skill usage counts include session context
**And** per-project breakdown is included when multiple projects analyzed
**And** timestamps are included for usage timeline analysis

**Given** the collector completes
**When** JSON output is written
**Then** output includes schema version (v3.0)
**And** output includes collection timestamp
**And** output includes total session count analyzed

---

## Epic 2: Missed Opportunity Detection

Users can identify when Claude could have used a skill but didn't, with confidence scoring that explains why each opportunity was flagged.

**Dependency:** Stories must be completed in order (2.1 → 2.2 → 2.3)

### Story 2.1: Test Suite for find_matches()

**As a** Developer,
**I want** comprehensive tests for the current `find_matches()` behavior,
**So that** I can safely enhance matching logic without breaking existing functionality.

**FRs:** FR-2.2.4

**Acceptance Criteria:**

**Given** the existing `find_matches()` function in `collect_usage.py`
**When** the test suite is run
**Then** all 11 test cases pass:
- [ ] test_exact_name_match
- [ ] test_minimum_trigger_length
- [ ] test_uppercase_3char_rule
- [ ] test_common_word_blocklist
- [ ] test_word_boundary_matching
- [ ] test_multiple_trigger_threshold
- [ ] test_case_insensitive
- [ ] test_confidence_score_calculation (parameterized)
- [ ] test_empty_prompt
- [ ] test_unicode_triggers
- [ ] test_very_long_prompt

**Given** schema changes are planned (v3.0 → v3.1)
**When** tests are written
**Then** acknowledge breaking change is acceptable (personal tool, no migration needed)
**And** update schema version constant to v3.1

---

### Story 2.2: Confidence Scoring

**As a** Power Customizer,
**I want** trigger matches to include a confidence score,
**So that** I only see high-confidence recommendations (>80%).

**FRs:** FR-2.2.1, FR-2.2.2, FR-2.2.3

**Acceptance Criteria:**

**Given** a trigger match is found
**When** confidence is calculated
**Then** the formula is applied:
  - length_score = min(100, trigger_length × 10)
  - specificity_score = 50 (single word) or 100 (multi-word phrase)
  - position_score = 100 at char 0, decays linearly to 0 at char 200
  - confidence = (length_score + specificity_score + position_score) / 3

**Given** matches are evaluated
**When** results are filtered
**Then** only matches with confidence > 80% are included in output

**Given** confidence scoring is added
**When** JSON output is generated
**Then** confidence score is included for each match (transparency)
**And** existing tests continue to pass
**And** new parameterized confidence tests pass

---

### Story 2.3: Missed Opportunity Detection with Impact

**As a** Power Customizer,
**I want** to see missed opportunities grouped by skill with impact scores,
**So that** I can prioritize which skills to use more.

**FRs:** FR-2.1.1, FR-2.1.2, FR-2.1.3, FR-2.1.4, FR-2.3.1, FR-2.3.2, FR-2.3.3, FR-2.4.1, FR-2.4.2, FR-2.4.3

**Acceptance Criteria:**

**Given** user prompts in session history
**When** trigger matching runs
**Then** prompts are matched against skill/agent trigger phrases
**And** unified ≥3 character threshold is enforced
**And** 3-char uppercase acronyms (TDD, API, MCP) are permitted
**And** common words are excluded via blocklist per ADR-001

**Given** a trigger matched but skill was not invoked in that session
**When** results are compiled
**Then** this is classified as "Missed" opportunity
**And** opportunities are grouped by skill/agent for consolidated view
**And** example prompts that triggered the match are included

**Given** missed opportunities exist
**When** impact scores are calculated
**Then** formula is applied: impact = (confidence × 0.4) + (frequency × 0.4) + (recency × 0.2)
**And** impact scores are pre-computed in collector (not re-computed in agent)
**And** impact_score field is included in JSON output for each missed opportunity

---

## Epic 3: Actionable Output

Users receive clear, prioritized recommendations with a summary dashboard, drill-down walkthrough, and safe cleanup mode for truly unused skills.

**Dependencies:**
- Story 3.1: Can start immediately (parallel track)
- Stories 3.2, 3.4: Require Epic 2 completion
- Story 3.3: Requires Story 3.2

### Story 3.1: Empty State Handling

**As a** Power Customizer,
**I want** clear guidance when no data or issues are found,
**So that** I'm not confused by empty results.

**FRs:** Implicit (graceful agent behavior)

**Acceptance Criteria:**

**Given** no session data exists for the time period
**When** the agent processes results
**Then** a helpful message explains why there's no data
**And** suggests adjusting the `--days` parameter

**Given** sessions exist but no missed opportunities found
**When** the agent presents results
**Then** a positive message confirms the user is utilizing their skills well
**And** no empty tables or confusing blank sections appear

**Given** the collector returns valid but minimal data
**When** the agent renders output
**Then** all sections degrade gracefully without errors

---

### Story 3.2: Summary Dashboard

**As a** Power Customizer,
**I want** to see a summary dashboard before detailed findings,
**So that** I can quickly understand my usage patterns at a glance.

**FRs:** FR-3.1.0, FR-3.1.1, FR-3.1.2, FR-3.1.3

**Depends on:** Epic 2 completion

**Acceptance Criteria:**

**Given** collector output with usage and missed opportunity data
**When** the agent starts
**Then** summary dashboard is presented FIRST (before any drill-down)

**Given** the dashboard is displayed
**When** user views it
**Then** it shows three tiers:
  - **Stats**: Total sessions, skills analyzed, Active/Dormant/Unused counts
  - **Top 3**: Highest impact missed opportunities (sorted by impact_score)
  - **Categories**: Grouped findings with counts

**Given** findings exist in a category
**When** user selects a category
**Then** agent presents findings one-by-one within that category
**And** user can accept, skip, or request more detail on each finding

---

### Story 3.3: Findings Walk-through

**As a** Power Customizer,
**I want** each recommendation to include problem, evidence, and action,
**So that** I understand why it's recommended and how to act.

**FRs:** FR-3.2.1, FR-3.2.2, FR-3.2.3

**Depends on:** Story 3.2

**Acceptance Criteria:**

**Given** a finding is presented
**When** the agent displays it
**Then** it includes:
  - **Problem description**: What the issue is
  - **Evidence**: Data supporting the recommendation (sessions, frequency, confidence)
  - **Recommended action**: Specific action to take

**Given** an actionable recommendation
**When** presented to user
**Then** copy-paste-ready instructions are provided where applicable
**And** evidence-based explanation of WHY this is recommended

**Given** user reviews a finding
**When** they respond
**Then** they can accept (mark as actioned), skip (move to next), or request more detail

---

### Story 3.4: Safe Cleanup Mode

**As a** Power Customizer,
**I want** deletion recommendations only when I explicitly enable cleanup mode,
**So that** I don't accidentally remove skills I might need.

**FRs:** FR-3.3.1, FR-3.3.2, FR-3.3.3

**Depends on:** Epic 2 completion

**Acceptance Criteria:**

**Given** cleanup mode is NOT enabled (default)
**When** unused skills are detected
**Then** NO deletion recommendations are made
**And** skills are shown as "Unused" for informational purposes only

**Given** cleanup mode IS enabled
**When** a skill has zero trigger matches
**Then** deletion is ONLY suggested if ALL conditions met:
  - Zero trigger matches in analysis period
  - No hard dependencies detected
  - ≥20 sessions analyzed (NFR-8)
  - Always flagged as "REVIEW CAREFULLY"

**Given** a deletion recommendation is made
**When** presented to user
**Then** rollback guidance is included (how to reinstall if needed)
**And** safety classification level is shown:
  - INSUFFICIENT DATA: <20 sessions analyzed
  - REVIEW CAREFULLY: All conditions met

**Given** <20 sessions analyzed
**When** cleanup mode is enabled
**Then** show "INSUFFICIENT DATA" warning
**And** do not suggest any deletions
