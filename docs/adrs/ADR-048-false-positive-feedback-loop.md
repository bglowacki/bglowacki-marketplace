# ADR-048: False Positive Feedback Loop

**Status:** PROPOSED
**Date:** 2026-01-28
**Category:** Methodology
**Source:** Deep research on recommendation systems

## Context

Current analysis has no mechanism to learn from user feedback:
- False positives can't be marked/dismissed
- Same incorrect recommendations reappear
- No tracking of recommendation acceptance rate

## Research Findings

From [DevPro Journal DevSecOps](https://www.devprojournal.com/software-development-trends/devsecops/shape-the-future-devsecops-2024-trends-and-insights/):
> "Teams struggle with an excessive number of false positives and difficulties related to remediation."

From [Checkmarx DevOps Metrics](https://checkmarx.com/learn/appsec/devops-metrics-2025-the-complete-guide-to-successfully-measuring-dev-operations/):
> "Automate metrics tracking, collection and visualization. This will reduce friction and help focus on the productivity impact."

## Problem Statement

1. **No dismissal mechanism**: User can't mark "this is not useful"
2. **Recommendation fatigue**: Same false positives appear repeatedly
3. **No learning**: System can't improve from feedback
4. **No quality metrics**: Unknown what % of recommendations are accepted

## Proposed Solution

### 1. Feedback Storage

Store user responses to recommendations:

```python
# ~/.claude/observability-feedback.json
{
    "dismissed": [
        {
            "finding_hash": "abc123",
            "category": "skill_discovery",
            "reason": "intentional_skip",
            "timestamp": "2026-01-28T10:00:00Z"
        }
    ],
    "accepted": [
        {
            "finding_hash": "def456",
            "category": "configuration",
            "timestamp": "2026-01-28T09:00:00Z"
        }
    ]
}
```

### 2. Dismissal Reasons

Allow categorized dismissals:

| Reason | Meaning | Action |
|--------|---------|--------|
| `intentional_skip` | User knowingly doesn't use this | Suppress permanently |
| `not_applicable` | Wrong context detected | Reduce confidence for similar |
| `already_handled` | Fixed outside this session | Suppress for 7 days |
| `defer` | Will address later | Suppress for 24 hours |

### 3. Finding Deduplication

Hash findings to detect repeats:

```python
def hash_finding(category: str, component: str, trigger: str) -> str:
    """Generate stable hash for finding deduplication."""
    return hashlib.sha256(f"{category}:{component}:{trigger}".encode()).hexdigest()[:12]
```

### 4. Acceptance Rate Tracking

Track metrics over time:

```markdown
## Analysis Quality Metrics

**Recommendation Acceptance Rate:** 62% (improving from 45% last month)

| Category | Accepted | Dismissed | Rate |
|----------|----------|-----------|------|
| skill_discovery | 15 | 8 | 65% |
| configuration | 12 | 3 | 80% |
| cleanup | 5 | 12 | 29% ← Needs calibration |
```

### 5. Output Format Change

Add dismissal option to findings:

```markdown
### Missed Skill: systematic-debugging

**Prompt:** "help me debug this error"
**Recommendation:** Use /systematic-debugging next time

Actions:
- [Apply] Mark as accepted
- [Dismiss: Intentional] I don't want this skill for debugging
- [Dismiss: N/A] This wasn't actually a debugging task
- [Defer] Remind me later
```

## Consequences

- System learns from user feedback
- False positive rate decreases over time
- Quality metrics enable continuous improvement
- Users have agency over recommendations

## Implementation Notes

- Requires persistent storage outside session
- Hash-based dedup prevents repeat alerts
- Consider privacy: store locally only
- workflow-optimizer should check dismissed before suggesting
