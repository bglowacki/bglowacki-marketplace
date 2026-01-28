# ADR-008: Overlapping Triggers Detection

**Status:** IMPLEMENTED
**Date:** 2026-01-27
**Category:** Methodology
**Decision:** Real problem confirmed; implement severity scoring (Option B)

## Context

The `compute_setup_profile()` function detects trigger overlaps (collect_usage.py:173-187):

```python
trigger_map: dict[str, list[str]] = defaultdict(list)
for item in skills + agents:
    for trigger in item.triggers:
        trigger_lower = trigger.lower()
        if len(trigger_lower) > 4:  # Skip short triggers
            trigger_map[trigger_lower].append(f"{item.type}:{item.name}")

overlapping = []
for trigger, items in trigger_map.items():
    if len(items) > 1:
        overlapping.append({"trigger": trigger, "items": items})
```

## Problems Identified

1. **Exact match only**: "debug" and "debugging" not considered overlapping
2. **Short trigger exclusion**: >4 char filter might miss meaningful short triggers
3. **No severity scoring**: "debug" overlap (common) vs "systematic-debugging" (specific)
4. **Intentional overlaps**: Some overlaps are intentional (multiple debugging tools)
5. **Source-blind**: Overlap between global and plugin is different from within plugin
6. **No resolution guidance**: Just flags overlap, doesn't suggest which to keep

## Decision Options

### Option A: Semantic Overlap Detection
Use stemming/lemmatization to find semantic overlaps.

### Option B: Severity Scoring
Score overlaps by trigger specificity and frequency of conflict.

### Option C: Source-Aware Classification
Classify overlaps as: intra-plugin, cross-plugin, global-plugin, etc.

### Option D: Conflict Resolution Suggestions
Suggest which component to keep based on usage patterns.

## Evidence Needed

- What % of detected overlaps cause actual confusion?
- Do users intentionally create overlapping triggers?
- Which source combinations cause most problems?

## Research Findings (2026-01-27)

**Critical Finding: Skill/Command Duplication is HIGH Severity**

Actual overlaps found in observability plugin:

| Trigger | Conflicts | Severity |
|---------|-----------|----------|
| `observability-usage-collector` | skill + command (same name) | HIGH |
| `observability-workflow-optimizer` | skill + command (same name) | HIGH |
| `usage data` | skill trigger overlaps agent trigger | MEDIUM |

**Root Cause:** Skills and commands share identical names, creating ambiguity when user invokes them.

**User Impact Scenario:**
```
User: "optimize my workflow"
Matches: Skill "optimize workflow" AND Command "optimize workflow"
Result: Claude picks arbitrarily → User gets unexpected behavior
```

**Substring Matching Reality:**
Word-boundary regex means "collect usage data" matches BOTH:
- `collect usage` trigger
- `usage data` trigger

## Final Decision

**ACCEPTED: Real problem requiring Option B (Severity Scoring)**

Implementation:
1. Classify overlaps by type:
   - Skill/Command same name: HIGH (structural issue)
   - Cross-plugin trigger: MEDIUM
   - Intra-plugin redundancy: LOW (often intentional)
2. Flag HIGH severity overlaps as red flags
3. Suggest resolution: rename command to avoid skill name collision

## Consequences

- Detects real conflicts, not just theoretical overlaps
- Guides users to resolve high-impact issues first
- Reduces false alarms from intentional redundancy
