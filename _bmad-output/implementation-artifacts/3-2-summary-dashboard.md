# Story 3.2: Summary Dashboard

Status: done

## Story

**As a** Power Customizer,
**I want** to see a summary dashboard before detailed findings,
**So that** I can quickly understand my usage patterns at a glance.

## Acceptance Criteria

1. **AC-1: Dashboard First**
   - Given collector output with usage and missed opportunity data
   - When the agent starts
   - Then summary dashboard is presented FIRST (before any drill-down)

2. **AC-2: Three-Tier Structure**
   - Given the dashboard is displayed
   - When user views it
   - Then it shows three tiers:
     - **Stats**: Total sessions, skills analyzed, Active/Dormant/Unused counts
     - **Top 3**: Highest impact missed opportunities (sorted by impact_score)
     - **Categories**: Grouped findings with counts

3. **AC-3: Category Selection**
   - Given findings exist in a category
   - When user selects a category
   - Then agent presents findings one-by-one within that category
   - And user can accept, skip, or request more detail on each finding

4. **AC-4: Impact Score Sorting**
   - Given missed opportunities exist
   - When Top 3 is displayed
   - Then items are sorted by `impact_score` descending
   - And impact score is visible for each item

## Tasks / Subtasks

- [x] Task 1: Design dashboard structure (AC: 1, 2)
  - [x] Define Stats tier content (sessions, skills, classification counts)
  - [x] Define Top 3 tier content (highest impact items)
  - [x] Define Categories tier content (grouped counts)

- [x] Task 2: Implement Stats tier (AC: 2)
  - [x] Extract `total_sessions` from JSON
  - [x] Count Active/Dormant/Unused skills from `skill_analysis`
  - [x] Calculate percentages for each category
  - [x] Display period analyzed (days)

- [x] Task 3: Implement Top 3 tier (AC: 2, 4)
  - [x] Sort `missed_opportunities` by `impact_score` descending
  - [x] Take top 3 items
  - [x] Display with emoji indicators (red/yellow/green)
  - [x] Show impact score and brief description

- [x] Task 4: Implement Categories tier (AC: 2)
  - [x] Group findings: Missed Opportunities, Dormant Skills, Unused Skills
  - [x] Show count per category
  - [x] Present as selectable options

- [x] Task 5: Implement category drill-down (AC: 3)
  - [x] When user selects category, list items one-by-one
  - [x] For each item, offer: Accept, Skip, More Detail
  - [x] Track which items have been reviewed

## Dev Notes

### Dashboard Template (Architecture Decision)

```markdown
## Usage Analysis Summary

**Period:** Last {N} days | **Sessions:** {count} | **Projects:** {count}

### Quick Stats
- Active skills: {X}/{Y} ({Z}%)
- Dormant skills: {X}/{Y} (triggers matched, never used)
- Unused skills: {X}/{Y} (no trigger matches)
- Missed opportunities: {X} (high confidence)

### Top 3 Recommendations (by impact score)
1. 🔴 **{highest_impact_item}** (impact: 0.92)
   {brief description}
2. 🟡 **{second_impact_item}** (impact: 0.78)
   {brief description}
3. 🟢 **{third_item_or_positive_note}** (impact: 0.65)
   {brief description}

### Categories
Select a category to explore:
[1] Missed Opportunities ({count})
[2] Dormant Skills ({count})
[3] Unused Skills ({count})
[4] Full Report
```

### Emoji Usage (Architecture Decision)

| Emoji | Meaning |
|-------|---------|
| 🔴 | High priority action needed |
| 🟡 | Medium priority / warning |
| 🟢 | Positive / working well |

### Impact Score Display

- Pre-computed in collector (Story 2.3)
- Display as decimal (0.92) not percentage
- Sort descending for Top 3

### Category Drill-Down Flow

```
User selects [1] Missed Opportunities
    ↓
Agent: "Missed Opportunity 1 of 5"
       Problem: TDD skill triggered 12 times, never used
       Evidence: Prompts included "write tests", "TDD approach"
       Action: Add explicit instruction to CLAUDE.md

       [Accept] [Skip] [More Detail]
    ↓
User: Accept
    ↓
Agent: "Missed Opportunity 2 of 5..."
```

### File to Modify

```
observability/agents/usage-insights-agent.md
```

### Architecture Compliance

- **Dashboard first**: Per FR-3.1.0, always show summary before detail
- **Agent-only changes**: No collector modifications
- **Use pre-computed scores**: Impact scores from collector, don't recalculate

### Dependencies

**This story DEPENDS ON:**
- Epic 2 completion (needs detection data + impact scores)
- Story 3.1: Empty State Handling (handles empty case)

**This story is a PREREQUISITE FOR:**
- Story 3.3: Findings Walk-through (uses category structure)

### References

- [Source: _bmad-output/planning-artifacts/epics.md#Story-3.2]
- [Source: _bmad-output/planning-artifacts/architecture.md#Agent Summary Dashboard Structure]
- [Source: _bmad-output/planning-artifacts/prd.md#FR-3.1]

## Dev Agent Record

### Agent Model Used

Claude Opus 4.5

### Debug Log References

### Completion Notes List

- Added "Summary Dashboard" section to usage-insights-agent.md before Analysis Workflow
- Dashboard defines three tiers: Quick Stats, Top 3 Recommendations, Categories
- Stats tier extracts total_sessions, classification counts (active/dormant/unused) with percentages
- Top 3 tier sorts missed_opportunities by impact_score descending, uses emoji indicators
- Categories tier groups findings into Missed Opportunities, Dormant Skills, Unused Skills
- Category drill-down presents findings one-by-one with Accept/Skip/More Detail options
- Added 20 structural tests in test_summary_dashboard.py validating all AC requirements
- All tests pass with no regressions
- Code review round 1: Fixed 5 issues (2 HIGH, 3 MEDIUM) — dashboard rendering order, category alignment, test precision, zero-count handling, period derivation
- Code review round 2: Fixed drill-down data extraction gap (H-2), period fallback precision (M-4), added tier ordering test (M-3)

### Change Log

| Date | Change | Author |
|------|--------|--------|
| 2026-01-29 | Implemented summary dashboard with 3-tier structure and category drill-down | Claude Opus 4.5 |
| 2026-01-29 | Code review: fixed dashboard rendering order, category alignment, test precision, zero-count handling, period derivation | Claude Opus 4.5 |
| 2026-01-29 | Code review round 2: added drill-down data extraction table (H-2), precise period fallback (M-4), tier ordering tests (M-3), cleaned completion notes (M-2) | Claude Opus 4.5 |

### File List

- observability/agents/usage-insights-agent.md (modified - added Summary Dashboard section with drill-down data extraction)
- observability/tests/test_summary_dashboard.py (new - 23 structural tests)
