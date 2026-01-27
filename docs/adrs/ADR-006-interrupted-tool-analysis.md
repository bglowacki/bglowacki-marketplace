# ADR-006: Interrupted Tool Context Analysis

**Status:** ACCEPTED (REVISED after Deep Research)
**Date:** 2026-01-27
**Revised:** 2026-01-27
**Category:** Methodology
**Decision:** Implement duration tracking only; REMOVE keyword-based classification; improve data model

## Context

The system tracks interrupted tools (collect_usage.py:66-69, 86, 914-925):

```python
@dataclass
class InterruptedTool:
    tool_name: str
    tool_input: dict
    followup_message: str  # What user said after interrupting

# Captures pending tools when "[Request interrupted by user]" appears
# Then captures user's followup message
```

## Problems Identified

1. **Lost context**: Only captures followup message, not WHY user interrupted
2. **No classification**: Interruption reasons vary (too slow, wrong direction, question answered, etc.)
3. **No pattern detection**: Repeated interruptions of same tool type isn't surfaced
4. **Input truncation**: `_summarize_tool_input` truncates to 100 chars, losing context
5. **Session-end interruptions**: Tools pending at session end get "[session ended]" - not useful
6. **No duration tracking**: How long tool ran before interruption is unknown

## Deep Research Findings (2026-01-27)

Critical issues with original proposal:

### 1. KEYWORD CLASSIFICATION HAS HIGH FALSE POSITIVE RISK (CRITICAL)

Original proposal:
```python
if any(kw in followup.lower() for kw in ["thanks", "got it", "nevermind"]):
    return "question_answered"
```

**Problems:**
| Keyword | False Positive Example | Actual Meaning |
|---------|------------------------|----------------|
| "thanks" | "thanks for trying, but this is wrong" | User is frustrated |
| "got it" | "I got it wrong, let me clarify" | User correcting themselves |
| "nevermind" | "nevermind what I said before, continue" | User changed mind |
| "wrong" | "that's the wrong approach" | Mid-conversation, not abort |
| "stop" | "stop at step 3" | Instruction, not abort |

**Recommendation:** REMOVE keyword-based classification entirely. Keep only:
- `duration_based` (timeout detection)
- `user_initiated` (everything else)

### 2. 30-SECOND TIMEOUT THRESHOLD IS ARBITRARY

30s timeout doesn't account for tool-type variability:

| Tool Type | Reasonable Duration | 30s is... |
|-----------|--------------------|----|
| Read/Edit/Write | < 10s | Too long |
| Bash (short cmd) | < 15s | Reasonable |
| Task (subagent) | 30-180s | Too short |
| WebFetch | 10-60s | Reasonable |

**Recommendation:** Either make timeout tool-aware OR remove timeout classification.

### 3. MULTIPLE PENDING TOOLS UNADDRESSED

When 3 tools are pending and user interrupts:
- Current: ALL 3 get same followup message
- Problem: Only one caused the interruption
- Missing: `interruption_position` (primary vs collateral)

### 4. SESSION-END DISMISSAL IS PREMATURE

The ADR called "[session ended]" "not useful" but it is valuable:
- User closed terminal mid-Task = strong dissatisfaction signal
- Pattern: User always closes during specific tool types = friction indicator
- Keep as separate `session_abandon` category, don't discard

### 5. TRUNCATION DOESN'T ADDRESS ROOT CAUSE

`_summarize_tool_input` loses critical context for Edit/Write:
- Doesn't capture `old_string`/`new_string` for Edit
- Doesn't capture `content` for Write
- Knowing WHAT was being edited matters more than just the file path

## Revised Decision

**ACCEPTED with significant modifications:**

1. **KEEP duration tracking** - straightforward value
2. **REMOVE keyword-based classification** - too error-prone
3. **ADD tool-type-aware timeout thresholds** - more accurate
4. **ADD interruption position** - primary vs collateral
5. **KEEP session-end interruptions** - valuable signal
6. **ENHANCE tool input capture** - include Edit old/new strings

## Revised Implementation Plan

### Data Model Changes

```python
@dataclass
class InterruptedTool:
    tool_name: str
    tool_input: dict
    followup_message: str
    duration_ms: int | None  # Time from tool start to interruption
    position: str  # "primary" (first pending) or "collateral"
    category: str  # "timeout" | "user_initiated" | "session_abandon"
```

### Timeout Thresholds (Tool-Aware)

```python
TIMEOUT_THRESHOLDS_MS = {
    "Bash": 30000,      # 30s
    "Task": 120000,     # 2 min - subagents take longer
    "WebFetch": 45000,  # 45s
    "Read": 10000,      # 10s
    "Edit": 10000,      # 10s
    "Write": 10000,     # 10s
    "default": 30000,   # 30s fallback
}

def classify_interruption(tool_name: str, duration_ms: int | None, followup: str) -> str:
    if followup == "[session ended]":
        return "session_abandon"

    if duration_ms is not None:
        threshold = TIMEOUT_THRESHOLDS_MS.get(tool_name, TIMEOUT_THRESHOLDS_MS["default"])
        if duration_ms > threshold:
            return "timeout"

    return "user_initiated"  # Don't guess from keywords
```

### Enhanced Tool Input Capture

```python
def _summarize_tool_input(tool_name: str, tool_input: dict, max_len: int = 200) -> str:
    if tool_name == "Edit":
        file_path = tool_input.get("file_path", "")
        old_str = tool_input.get("old_string", "")[:50]
        new_str = tool_input.get("new_string", "")[:50]
        return f"{file_path} | old: {old_str}... | new: {new_str}..."[:max_len]
    # ... rest of function
```

### Timestamp Storage

Modify pending_tools to store start timestamp:
```python
# Line 940-941: Change from
pending_tools[tool_use_id] = (tool_name, tool_input)
# To:
pending_tools[tool_use_id] = (tool_name, tool_input, entry_timestamp)
```

## Dependencies

None - can be implemented independently.

## Review Summary

### System Architect Review (Original)
- **Recommendation:** ACCEPT with modifications
- **Key Point:** NLP extraction is over-engineering for observability tooling
- **Duration Tracking:** Low-cost addition with clear utility

### Deep Research Review (2026-01-27)
- **REMOVED:** Keyword-based classification (high false positive risk)
- **ADDED:** Tool-type-aware timeout thresholds
- **ADDED:** Interruption position (primary vs collateral)
- **KEPT:** Session-end interruptions (valuable signal)
- **ENHANCED:** Tool input capture for Edit/Write

## Consequences

- Duration tracking enables timeout pattern detection
- Simple binary classification (timeout vs user_initiated) is more accurate than keyword guessing
- Primary/collateral distinction helps identify actual cause
- Session abandonment is tracked as a distinct signal
- Better Edit/Write context improves debugging value
