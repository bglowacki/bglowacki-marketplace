# Story 3.1: Empty State Handling

Status: done

## Story

**As a** Power Customizer,
**I want** clear guidance when no data or issues are found,
**So that** I'm not confused by empty results.

## Acceptance Criteria

1. **AC-1: No Session Data Message**
   - Given no session data exists for the time period
   - When the agent processes results
   - Then a helpful message explains why there's no data
   - And suggests adjusting the `--days` parameter

2. **AC-2: No Missed Opportunities Message**
   - Given sessions exist but no missed opportunities found
   - When the agent presents results
   - Then a positive message confirms the user is utilizing their skills well
   - And no empty tables or confusing blank sections appear

3. **AC-3: Graceful Degradation**
   - Given the collector returns valid but minimal data
   - When the agent renders output
   - Then all sections degrade gracefully without errors
   - And parsing errors (if any) are summarized

4. **AC-4: No Skills Installed Message**
   - Given no skills/agents are discovered
   - When the agent starts analysis
   - Then a helpful message explains no skills are installed
   - And provides link/guidance to documentation

## Tasks / Subtasks

- [x] Task 1: Add empty session handling (AC: 1)
  - [x] Check if `total_sessions == 0` in JSON input
  - [x] Display: "No sessions found in the last {N} days"
  - [x] Suggest: "Try extending the range with `--days 14` or `--days 30`"

- [x] Task 2: Add positive confirmation for healthy state (AC: 2)
  - [x] Check if `missed_opportunities` array is empty
  - [x] Display: "All systems healthy - no missed opportunities detected"
  - [x] Show brief usage stats as positive reinforcement

- [x] Task 3: Handle minimal data gracefully (AC: 3)
  - [x] Check for parsing errors in metadata
  - [x] If errors exist, show summary: "Note: {N} sessions had parsing issues"
  - [x] Ensure no empty tables/sections render (hide if no data)

- [x] Task 4: Add no-skills-installed handling (AC: 4)
  - [x] Check if `skills_discovered == 0` and `agents_discovered == 0`
  - [x] Display: "No skills or agents installed"
  - [x] Provide guidance: "Install skills from the marketplace or create custom ones"

- [x] Task 5: Test all empty states (AC: 1-4)
  - [x] Manually test with empty JSON input
  - [x] Test with zero sessions
  - [x] Test with sessions but no matches
  - [x] Test with parsing errors present

## Dev Notes

### File to Modify

```
observability/agents/usage-insights-agent.md
```

This is an **agent prompt file** (Markdown), not Python code. Changes involve adding conditional output sections.

### Empty State Messages

```markdown
## Empty State: No Sessions

**No sessions found in the last {days} days.**

This could mean:
- You haven't used Claude Code recently
- Session logs aren't being saved to `~/.claude/projects/`

**Try:** Extend the analysis range with `--days 14` or `--days 30`

---

## Empty State: All Healthy

**Great news! Your setup is working well.**

- Sessions analyzed: {count}
- Skills discovered: {count}
- No missed opportunities detected

Your skills and agents are being triggered appropriately. Keep up the good work!

---

## Empty State: No Skills

**No skills or agents found.**

The collector couldn't find any installed skills, agents, or commands.

**To get started:**
1. Install skills from the Claude Code marketplace
2. Create custom skills in `~/.claude/skills/`
3. See documentation: [Claude Code Skills Guide]
```

### Conditional Rendering Pattern

The agent should check JSON input fields before rendering sections:

```markdown
<!-- In agent prompt -->

**Analysis Instructions:**

1. First, check for empty states:
   - If `total_sessions == 0` → Show "No Sessions" message, STOP
   - If `skills_discovered == 0` → Show "No Skills" message, STOP
   - If `missed_opportunities` is empty → Show "All Healthy" message

2. Only proceed to detailed analysis if data exists
```

### Architecture Compliance

- **Agent-only changes**: No collector modifications
- **Graceful UX**: Empty states should feel helpful, not broken
- **No error states**: Empty data is valid, not an error

### Dependencies

**This story has NO blocking dependencies.** (Track B - Unblocked)

Can be implemented in parallel with Epic 1 and Epic 2.

**This story is a PREREQUISITE FOR:**
- Story 3.2: Summary Dashboard (handles non-empty case)

### References

- [Source: _bmad-output/planning-artifacts/epics.md#Story-3.1]
- [Source: _bmad-output/planning-artifacts/prd.md#US-3.0]
- [Source: observability/agents/usage-insights-agent.md] - File to modify

## Dev Agent Record

### Agent Model Used

Claude Opus 4.5 (claude-opus-4-5-20251101)

### Debug Log References

None - clean implementation with no issues.

### Completion Notes List

- Added "Empty State Handling" section to usage-insights-agent.md with 4 ordered checks: no sessions, no skills, no missed opportunities, and parsing errors
- Added "Pre-Phase: Empty State Checks" reference in Analysis Workflow to ensure checks run before any analysis
- Added "Graceful Section Rendering" rules to prevent empty tables/sections from rendering
- Check 1 (no sessions) and Check 2 (no skills) are STOP conditions — no further analysis proceeds
- Check 3 (healthy state) shows positive message and skips detailed findings
- Check 4 (parsing errors) is informational only — analysis continues
- All 306 existing tests pass with no regressions

### Change Log

| Date | Change | Author |
|------|--------|--------|
| 2026-01-29 | Added empty state handling (4 checks), graceful rendering rules, and pre-phase workflow step to usage-insights-agent.md | Claude Opus 4.5 |
| 2026-01-29 | Code review: fixed 4 issues — AC-4 condition now includes commands, resolved Check 3 vs Pre-Phase contradiction, removed conflicting "ALWAYS DO FIRST" on Phase 0, replaced hardcoded URL with generic doc reference | Claude Opus 4.5 (Review) |

### File List

- observability/agents/usage-insights-agent.md (modified)
