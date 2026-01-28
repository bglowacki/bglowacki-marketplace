# ADR-011: Workflow Stage Inference Gaps

## Status
PROPOSED

## Context
The `infer_workflow_stage` function attempts to detect workflow stages from tool usage. However, the logic has gaps and may produce inaccurate results.

## Finding
**File**: `generate_session_summary.py:78-112`, `collect_usage.py` (similar)

### Gaps Identified:

1. **No "research" stage**: Reading files, web searches, exploration aren't tracked
2. **Brainstorm only from skill**: Won't detect organic brainstorming without skill
3. **"unknown" default**: Sessions often stay "unknown" throughout
4. **No "debug" stage**: Debugging workflows aren't identified
5. **Git operations limited**: Only tracks commit/push, not branch/merge/rebase
6. **No stage transitions**: Doesn't track order/duration of stages

### Current Stage Detection:
| Detected | Source |
|----------|--------|
| brainstorm | Skill name contains "brainstorm" |
| plan | Skill name contains "plan" |
| implement | Edit or Write tool |
| test | pytest/test in Bash, or skill name |
| review | Skill or agent name contains "review" |
| commit | git commit in Bash |
| deploy | git push in Bash |

### Missing:
| Should Detect | Source |
|---------------|--------|
| research | Read, WebFetch, Grep, Glob usage |
| debug | Skill name or repeated failures |
| refactor | Edit patterns (moving code) |

## Decision
TBD - Needs review

## Recommendation
1. Add "research" stage for exploration-heavy sessions
2. Track stage transitions and durations
3. Add "debug" stage detection
4. Consider making stage inference configurable

## Impact
- More accurate workflow analysis
- Better insights into session patterns
- Useful for identifying stuck workflows

## Review Notes
- Severity: Medium (feature completeness)
- Effort: Medium
- Risk: Low (additive changes)
