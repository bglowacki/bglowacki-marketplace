# ADR-002: Outcome Detection Reliability

**Status:** ACCEPTED
**Date:** 2026-01-27
**Category:** Methodology
**Decision:** Options A + C (Tri-State + Tool-Specific Strategies)

## Context

The `detect_outcome()` function (collect_usage.py:777-805, generate_session_summary.py:52-80) classifies tool results as success/failure using keyword matching:

```python
def detect_outcome(tool_name: str, result: str) -> str:
    result_lower = result.lower()
    if tool_name == "Bash":
        if "exit code: 0" in result_lower or "succeeded" in result_lower:
            return "success"
        if "exit code:" in result_lower:
            return "failure"
        if any(kw in result_lower for kw in ["error:", "failed", "traceback", "permission denied"]):
            return "failure"
        return "success"  # Default to success
```

## Problems Identified

1. **Default success assumption**: If no keywords match, defaults to success - this is optimistic bias
2. **No confidence scoring**: Binary classification loses nuance (partial failure, warning, etc.)
3. **Keyword overlap**: "error handling" text gets flagged as error
4. **Tool-specific gaps**: Grep returning no results isn't "failure" but also isn't "success"
5. **Context-blind**: Same output might be success in one context, failure in another
6. **Exit code parsing fragility**: Relies on exact format "exit code: 0"

## Decision

**ACCEPTED: Options A + C combined**

Implement tool-specific detection strategies with tri-state (success/failure/unknown) for uncertain cases.

## Implementation Plan

```python
class OutcomeDetector(Protocol):
    def detect(self, result: str, context: dict) -> tuple[str, float]:
        """Returns (outcome, confidence) where outcome in {'success', 'failure', 'unknown'}"""

class BashOutcomeDetector:
    def detect(self, result: str, context: dict) -> tuple[str, float]:
        # Parse exit codes explicitly, handle edge cases
        ...
```

1. Create strategy pattern with tool-specific detectors
2. Add "unknown" state when confidence is low
3. Schema version bump for confidence scoring

## Review Summary

### Backend Architect Review
- **Recommendation:** ACCEPT (Options A + C)
- **Key Concern:** Default success assumption is dangerous for reliability metrics
- **Note:** Grep context-dependent (no results may be success or failure depending on intent)

### System Architect Review
- **Recommendation:** Consider adding "warning" as fourth state
- **Scalability:** No concerns - parsing is O(1) per result

## Consequences

- More accurate success rates in stats
- Breaking change requires schema version bump
- Tool-specific detectors are extensible without touching core logic
