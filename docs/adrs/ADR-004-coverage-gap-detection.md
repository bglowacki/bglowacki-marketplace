# ADR-004: Coverage Gap Detection Methodology

**Status:** ACCEPTED (with validation requirement)
**Date:** 2026-01-27
**Category:** Methodology
**Decision:** Keep as infrastructure; validate user value per ADR-016 process

## Context

The `compute_setup_profile()` function (collect_usage.py:190-206) detects coverage gaps by string matching:

```python
coverage = {
    "git_commit": any(kw in all_names_desc for kw in ["commit", "pre-commit"]),
    "code_review": any(kw in all_names_desc for kw in ["review", "pr review"]),
    "testing": any(kw in all_names_desc for kw in ["test", "tdd", "spec"]),
    "debugging": any(kw in all_names_desc for kw in ["debug", "troubleshoot"]),
    "planning": any(kw in all_names_desc for kw in ["plan", "design", "architect"]),
    "event_sourcing": any(kw in all_names_desc for kw in ["aggregate", "event sourc", "projection", "cqrs"]),
    "documentation": any(kw in all_names_desc for kw in ["documentation", "readme", "guide"]),
    "security": any(kw in all_names_desc for kw in ["vulnerab", "secret", "security"]),
}
```

## Problems Identified

1. **Hardcoded domains**: 8 fixed categories don't adapt to project type
2. **Keyword matching is shallow**: "react testing library" has "testing" but isn't a testing framework
3. **No usage correlation**: A skill covering "testing" might never be used - is it really coverage?
4. **Domain-blind**: A Python project doesn't need "jest" coverage
5. **Binary coverage**: Either covered or not - no partial/good/excellent ratings
6. **Static analysis only**: Doesn't consider if user actually needs that coverage

## Decision Options

### Option A: Project-Type Aware Coverage
Detect project type (Python/JS/Go) and adjust expected coverage accordingly.

### Option B: Usage-Based Coverage Scoring
Track actual tool usage against potential coverage to score effectiveness.

### Option C: User-Defined Coverage Goals
Let users specify what coverage they care about in CLAUDE.md.

### Option D: Dynamic Domain Discovery
Extract domains from actual session prompts instead of predefined list.

## Evidence Needed

- What % of coverage gaps are actually relevant to users?
- Do users even look at coverage gaps?
- What domains are most commonly needed but missing?

## Research Findings (2026-01-27)

**User-Facing Visibility Analysis:**

| Surface | Visible? | Notes |
|---------|----------|-------|
| Default table output | NO | Not included in print_table() |
| Dashboard output | NO | Not included in print_dashboard() |
| JSON output | YES | Buried at setup_profile.coverage_gaps |
| usage-insights-agent Phase 1 | YES | Single-line: "Missing tooling for: {gaps}" |
| workflow-optimizer | Partial | One pattern among many |

**Assessment: SPECULATIVE INFRASTRUCTURE FEATURE**

Evidence:
1. Not in default user journey (requires --format json)
2. Shallow detection logic (keyword matching only)
3. No user validation ever conducted
4. Risk of false direction (detecting gaps user doesn't need)

## Final Decision

**ACCEPTED with validation requirement:**

1. Keep current implementation (low maintenance cost)
2. Apply ADR-016 process: validate with real users within 30 days
3. If <20% of users find gaps valuable: deprecate feature
4. If valuable: enhance detection per proposed options

## Consequences

- Feature remains but flagged for validation
- No enhancements until user value proven
- Will be deprecated if validation fails
