# Story 3.4: Safe Cleanup Mode

Status: ready-for-dev

## Story

**As a** Power Customizer,
**I want** deletion recommendations only when I explicitly enable cleanup mode,
**So that** I don't accidentally remove skills I might need.

## Acceptance Criteria

1. **AC-1: Default No Deletions**
   - Given cleanup mode is NOT enabled (default)
   - When unused skills are detected
   - Then NO deletion recommendations are made
   - And skills are shown as "Unused" for informational purposes only

2. **AC-2: Cleanup Mode Requirements**
   - Given cleanup mode IS enabled
   - When a skill has zero trigger matches
   - Then deletion is ONLY suggested if ALL conditions met:
     - Zero trigger matches in analysis period
     - No hard dependencies detected
     - >= 20 sessions analyzed (NFR-8)
     - Always flagged as "REVIEW CAREFULLY"

3. **AC-3: Rollback Guidance**
   - Given a deletion recommendation is made
   - When presented to user
   - Then rollback guidance is included (how to reinstall if needed)
   - And safety classification level is shown

4. **AC-4: Insufficient Data Warning**
   - Given < 20 sessions analyzed
   - When cleanup mode is enabled
   - Then show "INSUFFICIENT DATA" warning
   - And do not suggest any deletions

## Tasks / Subtasks

- [ ] Task 1: Add cleanup mode flag detection (AC: 1)
  - [ ] Check for `--cleanup` flag or config setting
  - [ ] Default to cleanup mode OFF
  - [ ] Show "Unused" category without deletion suggestions when OFF

- [ ] Task 2: Implement safety classification (AC: 2)
  - [ ] Check zero trigger matches condition
  - [ ] Check no hard dependencies condition
  - [ ] Check >= 20 sessions threshold (NFR-8)
  - [ ] Only proceed if ALL conditions met

- [ ] Task 3: Create cleanup finding template (AC: 2, 3)
  - [ ] Header: "REVIEW CAREFULLY"
  - [ ] Show safety classification level
  - [ ] Include rollback guidance
  - [ ] Never say "safe to delete"

- [ ] Task 4: Implement insufficient data handling (AC: 4)
  - [ ] Check session count against threshold (20)
  - [ ] If below: Show warning, block cleanup suggestions
  - [ ] Display: "Extend analysis period for cleanup recommendations"

- [ ] Task 5: Add rollback guidance templates (AC: 3)
  - [ ] For global skills: Reinstall from marketplace
  - [ ] For project skills: Restore from git history
  - [ ] For plugin skills: Reinstall plugin

## Dev Notes

### Safety Classification (Architecture Decision)

| Level | Criteria | User Sees |
|-------|----------|-----------|
| **NEVER SUGGEST** | Has trigger matches in period | Nothing (not mentioned for deletion) |
| **INSUFFICIENT DATA** | Cleanup mode ON but <20 sessions | Warning message, no suggestions |
| **REVIEW CAREFULLY** | Zero triggers + no deps + cleanup ON + >= 20 sessions | Careful deletion suggestion |

### Minimum Session Threshold

**20 sessions required** before any cleanup suggestions (NFR-8).

Rationale: Protects trust metric; prevents false positives from:
- Short analysis windows
- Holiday periods
- New projects

### Cleanup Finding Template

```markdown
---
### 🔴 REVIEW CAREFULLY: Potential Unused Skill

**Skill:** {skill_name}
**Source:** {source_type} ({path})

**Safety Check:**
- [x] Zero trigger matches in {N} days
- [x] No hard dependencies found
- [x] {session_count} sessions analyzed (threshold: 20)

**Assessment:** This skill has not been triggered in {N} days across {session_count} sessions. It MAY be unused.

**IMPORTANT:** This is NOT a "safe to delete" recommendation. Review carefully:
- Is this skill seasonal? (e.g., deployment skills used monthly)
- Is this skill project-specific? (might be needed in other projects)
- Is this a safety net? (e.g., rollback scripts rarely used but critical)

**If you decide to remove:**
```bash
# To remove:
rm -rf {skill_path}

# To restore (if needed):
# From marketplace: claude-code install {skill_name}
# From git: git checkout HEAD~1 -- {skill_path}
```

**Options:** [Skip] [More Detail]
```

### Cleanup Mode OFF (Default) Template

```markdown
### Unused Skills (Informational Only)

The following skills had no trigger matches in the analysis period:
- {skill_1} (last used: never/unknown)
- {skill_2} (last used: never/unknown)

**Note:** These are shown for information only. Enable cleanup mode (`--cleanup`) for removal suggestions.
```

### Insufficient Data Template

```markdown
### Cleanup Mode: Insufficient Data

You've enabled cleanup mode, but only {N} sessions were analyzed.

**Minimum required:** 20 sessions
**Current:** {N} sessions

To get cleanup recommendations:
- Extend analysis period: `--days 30` or `--days 60`
- Wait for more usage data to accumulate

**Why this threshold?** Short analysis periods can miss:
- Seasonal skills (monthly deployments, quarterly reports)
- Project-specific skills (dormant projects)
- Safety-net skills (rarely used but critical)
```

### File to Modify

```
observability/agents/usage-insights-agent.md
```

### Architecture Compliance

- **Opt-in cleanup**: Per FR-3.3.2, never default to deletion suggestions
- **Safety first**: Per Critical Trust Metric, zero tolerance for bad recommendations
- **Always flagged**: Per FR-3.3.1, never say "safe to delete"
- **Rollback guidance**: Per FR-3.3.3, always provide restoration path

### Dependencies

**This story DEPENDS ON:**
- Epic 2: Missed Opportunity Detection (provides trigger match data)
- Story 3.3: Findings Walk-through (provides finding format)

**This story has NO downstream dependencies.** (Final story in MVP)

### References

- [Source: _bmad-output/planning-artifacts/epics.md#Story-3.4]
- [Source: _bmad-output/planning-artifacts/architecture.md#Safety Classification]
- [Source: _bmad-output/planning-artifacts/prd.md#FR-3.3]
- [Source: _bmad-output/planning-artifacts/prd.md#Critical Trust Metric]

## Dev Agent Record

### Agent Model Used

{{agent_model_name_version}}

### Debug Log References

### Completion Notes List

### Change Log

| Date | Change | Author |
|------|--------|--------|

### File List
