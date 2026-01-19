---
name: observability-workflow-optimizer
description: Analyzes usage-analyzer output and suggests minimal improvements to skills, agents, and workflows. Triggers on "optimize workflow", "improve triggers", "fix missed opportunities", or after running usage-analyzer.
---

# Workflow Optimizer

Analyze missed opportunities and propose minimal, targeted improvements to skills, agents, and workflows.

## Principles

1. **Minimal Changes** - Smallest edit that solves the problem
2. **Progressive Discovery** - Improve triggers before restructuring
3. **Holistic Review** - Check surrounding context, not just the named item
4. **Avoid Proliferation** - Improve existing items before creating new ones

## Workflow

### Step 1: Get Usage Analysis

Run usage-analyzer first:

```bash
uv run ${CLAUDE_PLUGIN_ROOT}/skills/usage-analyzer/scripts/analyze_usage.py --sessions 20 --format json
```

### Step 2: Analyze Each Missed Opportunity

For each missed item, work through this checklist:

#### 2.1 Understand the Context
- [ ] Read the full prompt that triggered the miss
- [ ] Read the current skill/agent description
- [ ] Identify what the user was trying to accomplish
- [ ] Check if another item handled this instead (and if that was correct)

#### 2.2 Review the Item
- [ ] Is the description clear about when to use it?
- [ ] Are trigger phrases explicit and specific?
- [ ] Does it overlap with other items?
- [ ] Is it trying to do too many things?

#### 2.3 Review Surroundings
- [ ] Check similar skills/agents for conflicts
- [ ] Check CLAUDE.md for relevant workflow guidance
- [ ] Check if a guide or command would be more appropriate
- [ ] Verify the item is discoverable (listed in right location)

### Step 3: Categorize Root Cause

| Root Cause | Solution |
|------------|----------|
| Trigger too narrow | Add specific trigger phrases to description |
| Trigger too broad | Narrow triggers or add context |
| Wrong item triggered | Clarify descriptions to distinguish |
| Item too broad | Consider splitting (last resort) |
| Coverage gap | Extend existing item or document gap |
| Workflow issue | Update CLAUDE.md or guides |
| Discovery issue | Check file location and naming |

### Step 4: Apply Minimal Fix

**Order of preference:**
1. Add/refine trigger phrases in description
2. Clarify description language
3. Update CLAUDE.md workflow guidance
4. Split item (only if clearly doing multiple unrelated things)
5. Create new item (only if no existing item can cover it)

### Step 5: Verify

Re-run usage-analyzer to confirm:
- Fixed opportunities now detected
- No new false positives
- No regressions in other items

## Decision Tree

```
Missed opportunity
│
├─ Was item name in prompt?
│   YES → Intentional skip or analyzer bug
│
├─ Similar triggers exist?
│   NO → Add trigger phrases
│
├─ More specific item exists?
│   YES → Improve that item instead
│
├─ Item doing too much?
│   YES → Split (last resort)
│
└─ New use case?
    └─ Can existing item extend?
        YES → Extend it
        NO → Document gap
```

## Anti-Patterns

**DON'T:**
- Add generic triggers ("help", "fix", "create")
- Duplicate triggers across items
- Create new items when trigger refinement works
- Change one item without checking conflicts

**DO:**
- Use specific, distinctive triggers
- Check for conflicts with similar items
- Test with usage-analyzer after changes
- Prefer description changes over structural changes

## Output Format

For each improvement:

```markdown
### [skill/agent name]

**Root Cause:** [from Step 3]

**Change:**
- File: `path/to/file.md`
- Line: [if applicable]
- Before: `current text`
- After: `improved text`

**Rationale:** [why minimal]

**Conflicts Checked:** [items reviewed]
```
