# ADR-007: Description Quality Validation

**Status:** IMPLEMENTED
**Date:** 2026-01-27
**Category:** Methodology
**Decision:** Option B (Template Matching) with multi-dimensional quality framework

## Context

The usage-insights-agent validates descriptions (usage-insights-agent.md:315-320):

```markdown
| Check | Detection Logic | Context7 Query |
|-------|-----------------|----------------|
| Empty descriptions | Skill/agent description < 50 chars | "effective skill and agent descriptions" |
| Missing triggers | Description has no quoted phrases or "trigger" keyword | "skill trigger phrases best practices" |
```

## Problems Identified

1. **Char count is poor proxy**: "Use this for debugging" is 22 chars but clear
2. **Trigger phrase detection is naive**: Requires literal "trigger" keyword or quotes
3. **No semantic validation**: Description might have words but convey nothing useful
4. **No example detection**: Descriptions with usage examples are more discoverable
5. **Language quality ignored**: Grammar, clarity, specificity not checked
6. **Context7 dependency**: Falls back to generic advice if MCP unavailable

## Decision Options

### Option A: LLM-Based Quality Scoring
Use Claude to score description quality on discoverability, clarity, specificity.

### Option B: Template Matching
Define good description patterns and check compliance.

### Option C: Comparative Scoring
Score against known-good descriptions from popular plugins.

### Option D: User Feedback Loop
Track which skills get discovered and correlate with description quality.

## Evidence Needed

- Correlation between description length and actual usage
- What makes descriptions actually discoverable?
- User feedback on description recommendations

## Research Findings (2026-01-27)

**Description Usage Analysis:**

Descriptions serve dual purposes:
1. **Trigger extraction**: Parsed via regex for quoted phrases and "Triggers on" patterns
2. **Human discovery**: Read by users browsing available tools

**Quality Criteria Framework (Proposed):**

| Dimension | Min | Target | Max | Rationale |
|-----------|-----|--------|-----|-----------|
| Length (chars) | 30 | 80-120 | 200 | Room for purpose + context |
| Explicit triggers | 2 | 3-4 | 6+ | Balance discovery/spam |
| Quoted phrases | 2 | 3+ | N/A | Enables automated extraction |
| Semantic keywords | 3 | 4+ | N/A | Specificity for matching |
| Domain mention | 1 | 1+ | N/A | Clarity about when to use |
| Action verb | 1 | 1+ | N/A | Clarity about what it does |

**Example Good Description:**
```
Collects Claude Code session history for analysis. Triggers on "collect usage", "gather usage data", or "usage data".
```
- 112 chars ✓
- 3 quoted triggers ✓
- Domain: "Claude Code" ✓
- Action: "Collects" ✓

**Example Bad Description:**
```
Process and analyze data
```
- 24 chars ✗
- 0 triggers ✗
- Generic domain ✗

## Final Decision

**ACCEPTED: Option B (Template Matching) with multi-dimensional validation**

Implementation:
1. Replace 50-char minimum with multi-dimensional scoring
2. Check: length (30-200), trigger count (≥2), domain mention, action verb
3. Flag descriptions failing ≥2 dimensions as "needs improvement"
4. Provide specific fix suggestions per dimension

## Consequences

- More accurate quality detection
- Actionable improvement suggestions
- Reject LLM-based scoring (ADR-019 policy)
