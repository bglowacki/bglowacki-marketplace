# ADR-033: Negation Pattern Detection in Trigger Matching

**Status:** DEFERRED (after Deep Research)
**Date:** 2026-01-27
**Revised:** 2026-01-27
**Category:** Methodology
**Decision:** DEFER implementation - false negative risk outweighs benefit; alternative approach proposed

## Context

During ADR-011 research, identified that trigger matching doesn't handle negation:

**Current behavior:**
- Prompt: "don't use the debug skill"
- Matches: "debug" trigger
- Result: Flags as missed opportunity (FALSE POSITIVE)

## Problem Statement

Word-boundary matching (`\b`) doesn't detect when triggers appear in negated context.

Common negation patterns:
- "don't debug"
- "do not use testing"
- "avoid the planning skill"
- "skip debugging"
- "without testing"

## Original Proposed Solution

```python
NEGATION_PATTERNS = [
    r"(?:don't|do not|don't|avoid|skip|without)\s+(?:\w+\s+)*?",
]

def is_negated_context(prompt: str, trigger: str, match_pos: int) -> bool:
    """Check if trigger appears in negated context."""
    # Look back 30 chars for negation words
    context_start = max(0, match_pos - 30)
    context = prompt[context_start:match_pos].lower()
    return any(re.search(pattern, context) for pattern in NEGATION_PATTERNS)
```

## Deep Research Findings (2026-01-27)

**Critical concerns with the original proposal:**

### 1. FALSE NEGATIVES ARE WORSE THAN FALSE POSITIVES

| Error Type | User Experience | Detectability |
|------------|-----------------|---------------|
| False Positive | User sees suggestion for skill they explicitly rejected | User can ignore/dismiss |
| False Negative | User never sees suggestion for relevant skill | **Invisible** |

A false positive is annoying but visible. A false negative means the user never knows they could have used a skill. This is fundamentally worse.

### 2. CHARACTER-BASED LOOKBACK IS CRUDE

The 30-50 char lookback window is arbitrary:
- Too short: Misses "I think we should probably not use debugging here" (negation is 40+ chars away)
- Too long: Catches unrelated negations

### 3. COMPLEX SENTENCES DEFEAT REGEX

| Sentence | Negation Detection Result | Correct? |
|----------|--------------------------|----------|
| "I don't want to debug this manually, let's use the debug skill" | Triggers negation! | WRONG |
| "Skip the setup and use the debug skill directly" | Triggers negation! | WRONG |
| "The debugging skill is not what I meant by 'not debugging'" | Confusing | WRONG |

### 4. SCOPE AMBIGUITY

"Don't use testing without proper debugging" - is "debugging" negated?
- Grammatically: No
- By lookback: Maybe (depends on window size)

## Revised Decision

**DEFERRED - Do not implement the original regex-based approach.**

The false negative risk is too high for the modest reduction in false positives. Users are better served by occasionally dismissing irrelevant suggestions than by never seeing relevant ones.

## Alternative Approach (If Needed in Future)

Instead of excluding negated matches, use **phrase removal** to clean the prompt:

```python
NEGATION_PHRASES = [
    "don't use", "do not use", "avoid using", "skip the", "without the",
    "don't want", "do not want", "not the", "no need for"
]

def clean_prompt_for_matching(prompt: str) -> str:
    """Remove explicit negation phrases before matching."""
    result = prompt.lower()
    for phrase in NEGATION_PHRASES:
        # Remove the phrase AND the next word (the thing being negated)
        result = re.sub(rf'{phrase}\s+\w+', '', result)
    return result
```

**Benefits of phrase removal:**
- Explicit list of known patterns (not arbitrary lookback)
- Only removes clearly negated terms
- Falls back to over-matching (false positives) rather than under-matching
- Easier to test and maintain

**Still has issues:**
- Phrase list needs maintenance
- Complex sentences still problematic
- May remove too much from prompts

## Recommendation

1. **Do not implement negation detection** until we have data on actual false positive rates
2. **Collect validation data** per ADR-011
3. **If false positives are problematic**, try the phrase removal approach
4. **Never implement lookback-based negation** - too error-prone

## Dependencies

- **ADR-035** (tests): Would need tests before any implementation
- **ADR-011** (validation data): Need to know if false positives are actually a problem

## Review Summary

### Backend Architect Review (Original)
- **Verdict:** ACCEPT with recommendations
- **Recommendation:** Increase lookback to 50 chars; add positive affirmation detection

### System Architect Review (Original)
- **Verdict:** ACCEPT with conditions
- **Concern:** Only checks context before trigger, misses "X is not needed" pattern
- **Dependency:** Requires ADR-035 (tests) first

### Deep Research Review (2026-01-27)
- **Finding:** False negatives worse than false positives
- **Finding:** Regex-based negation is fundamentally unreliable
- **Decision:** DEFER implementation
- **Alternative:** Phrase removal approach if needed

## Consequences

- False positives remain in missed opportunity detection
- Users may see suggestions for skills they rejected
- BUT: Users will always see relevant suggestions (no false negatives)
- Simpler codebase without complex negation logic
- Can revisit with validation data from ADR-011
