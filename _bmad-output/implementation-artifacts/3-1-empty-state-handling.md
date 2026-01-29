# Story 3.1: Empty State Handling

Status: ready-for-dev

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

- [ ] Task 1: Add empty session handling (AC: 1)
  - [ ] Check if `total_sessions == 0` in JSON input
  - [ ] Display: "No sessions found in the last {N} days"
  - [ ] Suggest: "Try extending the range with `--days 14` or `--days 30`"

- [ ] Task 2: Add positive confirmation for healthy state (AC: 2)
  - [ ] Check if `missed_opportunities` array is empty
  - [ ] Display: "All systems healthy - no missed opportunities detected"
  - [ ] Show brief usage stats as positive reinforcement

- [ ] Task 3: Handle minimal data gracefully (AC: 3)
  - [ ] Check for parsing errors in metadata
  - [ ] If errors exist, show summary: "Note: {N} sessions had parsing issues"
  - [ ] Ensure no empty tables/sections render (hide if no data)

- [ ] Task 4: Add no-skills-installed handling (AC: 4)
  - [ ] Check if `skills_discovered == 0` and `agents_discovered == 0`
  - [ ] Display: "No skills or agents installed"
  - [ ] Provide guidance: "Install skills from the marketplace or create custom ones"

- [ ] Task 5: Test all empty states (AC: 1-4)
  - [ ] Manually test with empty JSON input
  - [ ] Test with zero sessions
  - [ ] Test with sessions but no matches
  - [ ] Test with parsing errors present

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

{{agent_model_name_version}}

### Debug Log References

### Completion Notes List

### Change Log

| Date | Change | Author |
|------|--------|--------|

### File List
