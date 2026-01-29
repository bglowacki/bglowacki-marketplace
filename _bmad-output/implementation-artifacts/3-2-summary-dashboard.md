# Story 3.2: Summary Dashboard

Status: ready-for-dev

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

- [ ] Task 1: Design dashboard structure (AC: 1, 2)
  - [ ] Define Stats tier content (sessions, skills, classification counts)
  - [ ] Define Top 3 tier content (highest impact items)
  - [ ] Define Categories tier content (grouped counts)

- [ ] Task 2: Implement Stats tier (AC: 2)
  - [ ] Extract `total_sessions` from JSON
  - [ ] Count Active/Dormant/Unused skills from `skill_analysis`
  - [ ] Calculate percentages for each category
  - [ ] Display period analyzed (days)

- [ ] Task 3: Implement Top 3 tier (AC: 2, 4)
  - [ ] Sort `missed_opportunities` by `impact_score` descending
  - [ ] Take top 3 items
  - [ ] Display with emoji indicators (red/yellow/green)
  - [ ] Show impact score and brief description

- [ ] Task 4: Implement Categories tier (AC: 2)
  - [ ] Group findings: Missed Opportunities, Dormant Skills, Unused Skills
  - [ ] Show count per category
  - [ ] Present as selectable options

- [ ] Task 5: Implement category drill-down (AC: 3)
  - [ ] When user selects category, list items one-by-one
  - [ ] For each item, offer: Accept, Skip, More Detail
  - [ ] Track which items have been reviewed

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

{{agent_model_name_version}}

### Debug Log References

### Completion Notes List

### Change Log

| Date | Change | Author |
|------|--------|--------|

### File List
