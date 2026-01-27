# ADR-023: Agent Output Structure Consistency

**Status:** ACCEPTED
**Date:** 2026-01-27
**Category:** Methodology
**Decision:** Current hybrid structure is well-designed; no changes needed

## Context

The usage-insights-agent produces output with multiple formats:
- Setup Summary (markdown table)
- Plugin Efficiency (markdown list)
- Category findings (Problem → Impact → Action)
- Category selection JSON (for complex setups)

## Problems Identified

1. **Format inconsistency**: Some sections use tables, others lists, others JSON
2. **Machine-readability**: Markdown output is hard to programmatically process
3. **Category selection JSON embedded in markdown**: Awkward parsing
4. **No structured output option**: Always markdown, no JSON alternative
5. **Finding format varies**: Different templates for different finding types

## Blocking Question

**Who/what parses agent output?**

This determines whether JSON mode is necessary or gold-plating:
- If only humans read it: Keep markdown, improve templates
- If tools parse it: JSON mode is essential
- If workflow-optimizer parses it: Need clear contract

## Proposed Options

### Option B: Additional JSON Mode (Recommended if consumers exist)

Keep markdown default, add JSON alternative with schema versioning:

```json
{
  "schema_version": "1.0",
  "setup_summary": {...},
  "plugin_efficiency": {...},
  "findings": [
    {
      "category": "skill_discovery",
      "type": "missed_opportunity",
      "severity": "major",
      "problem": "...",
      "impact": "...",
      "action": "..."
    }
  ]
}
```

### Option C: Structured Markdown

Keep markdown but with strict templates. Half-measure that solves neither problem fully.

## Review Summary

### System Architect Review
- **Verdict:** NEEDS_MORE_INFO
- **Critical Issue:** "Questions for Review" must be answered - they're design inputs, not follow-ups
- **Recommendation:** If JSON mode added, include schema versioning from day one
- **Note:** Define explicit contract via separate schema file

## Research Findings (2026-01-27)

**Consumers Identified:**

| Consumer | Format Needed | Current Support |
|----------|--------------|-----------------|
| User (via AskUserQuestion) | Markdown + JSON | ✓ Supported |
| Workflow Optimizer Skill | Markdown tables | ✓ Supported |
| Parent agent (category selection) | JSON block | ✓ Supported |

**Output Structure Analysis:**

- **Phase 1 (Setup Summary)**: Always markdown tables ✓
- **Phase 3 (Category Selection)**: JSON block with `awaiting_selection` flag ✓
- **Phase 4 (Detailed Findings)**: Markdown with Problem → Impact → Action ✓

**Critical Marker:** HTML comment `<!-- CATEGORY_SELECTION_REQUIRED -->` enables parent agent to detect JSON block.

**Assessment: WELL-DESIGNED**

The hybrid approach correctly serves:
1. Human readers (markdown tables, collapsible sections)
2. Machine consumers (JSON block for category selection)
3. Workflow optimizer (structured finding format)

## Final Decision

**ACCEPTED: Current structure is appropriate**

**Rationale:**
1. Progressive disclosure works (auto-expand for moderate, selection for complex)
2. JSON selection block exists but only activates when needed
3. Finding format (Problem → Impact → Action) is consumable by all consumers

**No Changes Required**

## Consequences

- Keep current hybrid markdown + JSON approach
- Document JSON schema version if consumers increase
- No additional JSON mode needed currently
