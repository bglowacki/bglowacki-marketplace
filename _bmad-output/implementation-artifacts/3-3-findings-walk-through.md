# Story 3.3: Findings Walk-through

Status: done

## Story

**As a** Power Customizer,
**I want** each recommendation to include problem, evidence, and action,
**So that** I understand why it's recommended and how to act.

## Acceptance Criteria

1. **AC-1: Problem-Evidence-Action Format**
   - Given a finding is presented
   - When the agent displays it
   - Then it includes:
     - **Problem description**: What the issue is
     - **Evidence**: Data supporting the recommendation (sessions, frequency, confidence)
     - **Recommended action**: Specific action to take

2. **AC-2: Copy-Paste Instructions**
   - Given an actionable recommendation
   - When presented to user
   - Then copy-paste-ready instructions are provided where applicable
   - And evidence-based explanation of WHY this is recommended

3. **AC-3: User Response Options**
   - Given user reviews a finding
   - When they respond
   - Then they can:
     - **Accept**: Mark as actioned
     - **Skip**: Move to next finding
     - **More Detail**: Request additional context

4. **AC-4: Progress Tracking**
   - Given multiple findings in a category
   - When walking through
   - Then show progress (e.g., "Finding 2 of 5")
   - And track which findings have been reviewed

## Tasks / Subtasks

- [x] Task 1: Define finding template (AC: 1)
  - [x] Create Problem section format
  - [x] Create Evidence section format (with data points)
  - [x] Create Action section format (specific instructions)

- [x] Task 2: Implement copy-paste actions (AC: 2)
  - [x] For trigger improvements: Show example CLAUDE.md addition
  - [x] For skill usage: Show invocation command
  - [x] For configuration: Show config file snippet

- [x] Task 3: Implement response handling (AC: 3)
  - [x] Accept: Log as actioned, move to next
  - [x] Skip: Move to next without logging
  - [x] More Detail: Show additional context (example prompts, session IDs)

- [x] Task 4: Add progress indicator (AC: 4)
  - [x] Display "Finding {X} of {Y}" header
  - [x] Track reviewed items in session
  - [x] Show completion summary at end

- [x] Task 5: Create finding type templates (AC: 1, 2)
  - [x] Template for Missed Opportunity findings
  - [x] Template for Dormant Skill findings
  - [x] Template for Configuration Issue findings

## Dev Notes

### Finding Template Structure

```markdown
---
### Finding {X} of {Y}: {finding_type}

**Problem:** {skill_name} was triggered {count} times but never used.

**Evidence:**
- Confidence: {confidence}% match quality
- Frequency: Triggered in {session_count} sessions
- Example prompts:
  - "{prompt_1}"
  - "{prompt_2}"

**Recommended Action:** Add explicit instruction to CLAUDE.md

```markdown
# Copy-paste this to your CLAUDE.md:
When I mention "{trigger_phrase}", use the {skill_name} skill.
```

---

**Options:** [Accept] [Skip] [More Detail]
```

### Finding Types and Actions

| Finding Type | Problem Format | Action Format |
|--------------|----------------|---------------|
| Missed Opportunity | "{skill} triggered {N} times, never used" | Add CLAUDE.md instruction |
| Dormant Skill | "{skill} has matching triggers but low confidence" | Improve trigger phrases |
| Configuration Issue | "{skill} has conflicting triggers with {other}" | Resolve conflict |

### Copy-Paste Examples

**For Missed Opportunities:**
```markdown
# Add to CLAUDE.md:
When working on tests or TDD, always use the `test-driven-development` skill.
```

**For Trigger Improvements:**
```yaml
# Update skill triggers in SKILL.md:
triggers:
  - "TDD"
  - "test-driven"
  - "write tests first"  # Add this
  - "red green refactor" # Add this
```

### More Detail Response

When user requests more detail, show:
- All matching prompts (not just examples)
- Session IDs where matches occurred
- Confidence breakdown (length/specificity/position scores)
- Similar skills that might conflict

### File to Modify

```
observability/agents/usage-insights-agent.md
```

### Architecture Compliance

- **Evidence-based**: Per FR-3.2.3, always explain WHY
- **Copy-paste ready**: Per FR-3.2.2, actionable instructions
- **Interactive flow**: Agent guides through findings one-by-one

### Dependencies

**This story DEPENDS ON:**
- Story 3.2: Summary Dashboard (provides category structure)
- Epic 2: Missed Opportunity Detection (provides finding data)

**This story is a PREREQUISITE FOR:**
- Story 3.4: Safe Cleanup Mode (extends finding format)

### References

- [Source: _bmad-output/planning-artifacts/epics.md#Story-3.3]
- [Source: _bmad-output/planning-artifacts/prd.md#FR-3.2]
- [Source: _bmad-output/planning-artifacts/architecture.md#Agent Output Patterns]

## Dev Agent Record

### Agent Model Used

Claude Opus 4.5 (claude-opus-4-5-20251101)

### Debug Log References

### Completion Notes List

- Added "Findings Walk-through" section to usage-insights-agent.md with Problem-Evidence-Action template format
- Implemented copy-paste action blocks for CLAUDE.md additions, skill invocation commands, and configuration changes
- Added response handling table (Accept/Skip/More Detail) with detailed behavior descriptions
- Added progress tracking with "Finding X of Y" format and completion summary template
- Created three finding type templates: Missed Opportunity, Dormant Skill, Configuration Issue
- 22 new tests in test_findings_walkthrough.py, all passing
- Note: agent file changes were committed together with Story 3-2 (commit 06922dc) since both stories modify the same file
- Code review: Fixed confidence format (decimal not %), added template ordering test

### Change Log

| Date | Change | Author |
|------|--------|--------|
| 2026-01-29 | Added Findings Walk-through section with finding templates, copy-paste actions, response handling, progress tracking, and finding type templates | Dev Agent |
| 2026-01-29 | Code review: fixed confidence format (decimal not %), added template ordering tests, updated completion notes | Claude Opus 4.5 |

### File List

- observability/agents/usage-insights-agent.md (modified)
- observability/tests/test_findings_walkthrough.py (new)
