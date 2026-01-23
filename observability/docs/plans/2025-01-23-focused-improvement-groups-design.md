# Focused Improvement Groups Design

## Problem

With complex setups (50+ components), the workflow-optimizer analyzes everything and produces overwhelming output. Users can't easily focus on what matters most.

## Solution

Add category-based filtering to the insights-agent workflow. Users select which improvement categories to focus on before seeing detailed findings.

```
┌─────────────────────────────────────────────────────────────────┐
│                    UPDATED PIPELINE                              │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  collect_usage.py (unchanged)                                    │
│  └── Output: JSON with setup_profile                             │
│                         ↓                                        │
│  usage-insights-agent (UPDATED)                                  │
│  ├── Phase 1: Setup Summary (unchanged)                          │
│  ├── Phase 2: Analyze ALL categories internally                  │
│  ├── Phase 3: Present category summary with counts               │
│  ├── [AskUserQuestion: multi-select categories]                  │
│  └── Phase 4: Expand only selected categories                    │
│                         ↓                                        │
│  workflow-optimizer (unchanged)                                  │
│  └── Generate fixes (now scoped to selected categories)          │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

## Category Definitions

| Category | ID | Findings Included |
|----------|-----|-------------------|
| **Skill Discovery** | `skill_discovery` | Missed skill opportunities, trigger overlaps (skills), empty skill descriptions |
| **Agent Delegation** | `agent_delegation` | Missed agent opportunities, trigger overlaps (agents), underused agents |
| **Hook Automation** | `hook_automation` | Missing project hooks, global→project hook moves, automation gaps |
| **Configuration** | `configuration` | Missing project CLAUDE.md, stale references, workflow contradictions |
| **Cleanup** | `cleanup` | Never-used components, redundant items, disabled-but-present items |

### Priority Calculation

- **High**: Category has 5+ issues OR contains a red flag from setup_profile
- **Medium**: Category has 2-4 issues
- **Low**: Category has 1 issue

### Mapping Rules

- Each finding goes to exactly one category (no duplicates)
- Overlapping triggers → `skill_discovery` or `agent_delegation` based on item type
- Empty descriptions → same category as the item type
- Red flags from setup_profile pre-populate categories

## Insights-Agent Workflow Changes

### Phase 3: Category Summary (NEW)

After Phase 2 analysis, agent outputs:

```markdown
## Improvement Categories

1. **Skill Discovery** (8 issues, High) - 5 missed opportunities, 3 trigger overlaps
2. **Agent Delegation** (3 issues, Medium) - 2 underused agents, 1 overlap
3. **Hook Automation** (5 issues, High) - No project hooks, 3 automation gaps
4. **Configuration** (2 issues, Low) - Missing project CLAUDE.md
5. **Cleanup** (12 issues, Medium) - 8 never-used, 4 redundant
```

Then calls `AskUserQuestion` with:
```
question: "Which categories would you like me to expand?"
header: "Focus areas"
multiSelect: true
options:
  - label: "Skill Discovery (8 issues)"
  - label: "Agent Delegation (3 issues)"
  - label: "Hook Automation (5 issues)"
  - label: "Configuration (2 issues)"
  - label: "Cleanup (12 issues)"
```

### Phase 4: Expand Selected (NEW)

For each selected category, output detailed findings:

```markdown
## Skill Discovery (Detailed)

### Missed Opportunities
- Prompt "help me debug this error" could have used systematic-debugging
- ...

### Trigger Overlaps
- "debug": matched by systematic-debugging, debugger, root-cause-analyst
- ...
```

## Implementation Scope

### Files to Modify

| File | Change |
|------|--------|
| `observability/agents/usage-insights-agent.md` | Add Phase 3 (category summary) and Phase 4 (expand selected) workflow |

### No Changes Needed

- `collect_usage.py` - Already provides all data needed
- `workflow-optimizer SKILL.md` - Works with whatever findings it receives

## Edge Cases

| Scenario | Behavior |
|----------|----------|
| All categories have 0 issues | Skip Phase 3/4, output "No issues found" |
| User selects no categories | Output "No categories selected" and end |
| Minimal/Moderate complexity | Still show categories but auto-expand all (skip selection) |
| Complex complexity | Show categories with selection (as designed) |

## Complexity-Based Behavior

- **Minimal/Moderate (<50 components)**: Skip AskUserQuestion, auto-expand all categories
- **Complex (50+)**: Use AskUserQuestion for selection

This keeps the focused grouping for large setups while not adding friction for smaller ones.
