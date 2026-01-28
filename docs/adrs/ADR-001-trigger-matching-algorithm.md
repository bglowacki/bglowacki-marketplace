# ADR-001: Trigger Matching Algorithm Improvements

**Status:** IMPLEMENTED
**Date:** 2026-01-27
**Revised:** 2026-01-27
**Category:** Methodology
**Decision:** Fix threshold inconsistency, add case-sensitive short trigger handling, add common word blocklist

## Context

The current trigger matching algorithm in `find_matches()` (collect_usage.py:974-991) uses regex word boundary matching with a minimum of 2 triggers to match:

```python
def find_matches(prompt: str, items: list[SkillOrAgent], min_triggers: int = 2) -> list[tuple[SkillOrAgent, list[str]]]:
    for trigger in item.triggers:
        trigger_lower = trigger.lower()
        if len(trigger_lower) > 3:
            if re.search(r'\b' + re.escape(trigger_lower) + r'\b', prompt_lower):
                matched_triggers.append(trigger)
```

## Problems Identified

1. **Minimum trigger length of 3 chars is arbitrary**: Triggers like "TDD", "DDD", "API" are 3 chars and get excluded
2. **No weighting of triggers**: A specific trigger like "event-sourced aggregate" is treated the same as generic "help"
3. **No semantic matching**: "debugging" won't match "debug issue" despite clear intent
4. **No negation handling**: "don't use X" still matches X as a trigger
5. **Position-blind**: First word triggers are more likely intentional than mid-sentence

## Deep Research Findings (2026-01-27)

Critical issues discovered during deep code analysis:

### 1. DUAL THRESHOLD INCONSISTENCY (CRITICAL)

The codebase has two different thresholds:
- **Line 178** (`compute_setup_profile`): `if len(trigger_lower) > 4` - uses >4 for overlap detection
- **Line 983** (`find_matches`): `if len(trigger_lower) > 3` - uses >3 for matching

This inconsistency means:
- 4-char triggers like "test", "bash", "edit" are matched but excluded from overlap analysis
- Creates silent data quality issues

### 2. NO CASE SENSITIVITY FOR SHORT TRIGGERS

3-char acronyms like "TDD", "DDD", "API" are commonly UPPERCASE:
- Current code lowercases everything, losing this signal
- An uppercase-only rule for 3-char triggers would reduce false positives
- "API" should match, but "api" in prose ("the rapid expansion") should not

### 3. COMMON WORD FALSE POSITIVES

With `>=3` threshold, common English words would match:
- "the", "for", "add", "run", "fix", "use", "new", "old"
- These are unlikely to be intentional skill triggers
- Need a blocklist of common 3-4 char words

## Revised Decision

**ACCEPTED with modifications:**

1. **Fix threshold inconsistency**: Unify to single threshold value (recommend `>= 3`)
2. **Add uppercase rule for 3-char triggers**: Only match 3-char triggers if UPPERCASE in original
3. **Add common word blocklist**: Exclude common English words from short trigger matching
4. **Defer negation handling**: See ADR-033 (deferred due to false negative risk)

## Revised Implementation Plan

```python
COMMON_WORD_BLOCKLIST = {
    "the", "for", "and", "but", "add", "run", "fix", "use", "new", "old",
    "get", "set", "put", "can", "has", "was", "are", "not", "all", "any"
}

def find_matches(prompt: str, items: list[SkillOrAgent], min_triggers: int = 2):
    for trigger in item.triggers:
        trigger_lower = trigger.lower()

        # Unified threshold: >= 3 chars
        if len(trigger_lower) < 3:
            continue

        # 3-char triggers: require UPPERCASE in original (e.g., "TDD", "API")
        if len(trigger_lower) == 3:
            if not trigger.isupper():
                continue
            # Also skip if it's a common word
            if trigger_lower in COMMON_WORD_BLOCKLIST:
                continue

        # 4-char triggers: skip common words
        if len(trigger_lower) == 4 and trigger_lower in COMMON_WORD_BLOCKLIST:
            continue

        if re.search(r'\b' + re.escape(trigger_lower) + r'\b', prompt_lower):
            matched_triggers.append(trigger)
```

Also fix line 178 to use same threshold:
```python
# Line 178: Change from >4 to >=3 for consistency
if len(trigger_lower) >= 3:
```

## Dependencies

- **ADR-035** (tests): MUST implement tests FIRST before changing logic
- **ADR-033** (negation): DEFERRED - false negative risk outweighs benefit

## Review Summary

### Backend Architect Review
- **Recommendation:** ACCEPT (Option D then A)
- **Feasibility:** Option D is trivial (1-hour fix), Option A is medium complexity
- **Concerns:** Negation handling requires careful regex to avoid ReDoS

### Deep Research Review (2026-01-27)
- **Critical Finding:** Dual threshold inconsistency must be fixed
- **Added:** Uppercase rule for 3-char triggers
- **Added:** Common word blocklist
- **Deferred:** Negation handling (ADR-033) due to false negative risk

## Consequences

- Better matching reduces false positives in "missed opportunity" detection
- Consistent threshold across codebase prevents silent bugs
- Uppercase rule for acronyms is intuitive and accurate
- Common word blocklist prevents noise from prose matching
