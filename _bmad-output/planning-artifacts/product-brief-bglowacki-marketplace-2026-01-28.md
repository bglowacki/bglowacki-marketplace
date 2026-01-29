---
stepsCompleted: [1, 2, 3, 4, 5]
inputDocuments:
  - docs/index.md
  - docs/project-overview.md
  - docs/architecture.md
  - docs/development-guide.md
date: 2026-01-28
author: Bartek
---

# Product Brief: bglowacki-marketplace

## Executive Summary

You've invested hours customizing Claude Code with skills, agents, and workflows. But how do you know it's paying off?

bglowacki-marketplace provides the **only observability layer for AI-assisted development**—giving you visibility into what's actually being used, what's being ignored, and what patterns should become your next skill. Stop flying blind. Start optimizing with data.

---

## Core Vision

### Problem Statement

Claude Code users invest significant effort customizing their environments. But there's no way to know if that investment pays off. You suspect Claude is missing opportunities to use your tools—but you can't prove it. The gap between what you've built and what actually gets used creates a frustrating question: *"Did I waste my time?"*

### Problem Impact

- **The "did it work?" anxiety**: You built custom skills but have no idea if they're ever triggered
- **Invisible inefficiency**: Same tasks done differently each session, no standardization
- **Reactive treadmill**: Adding instructions only when problems surface, never getting ahead
- **Instruction rot**: CLAUDE.md grows unwieldy while skills overlap or get ignored

### Why Existing Solutions Fall Short

There are none. GitHub has Insights. VS Code has telemetry. Claude Code? Users fly blind.

Today's workaround is ad-hoc fixes—adding instructions reactively when you notice Claude missing something. This fails because there's no cross-session visibility, no way to detect redundancy, and no systematic way to identify patterns worth standardizing.

### Proposed Solution

Analyze Claude Code session logs to provide data-driven insights:
- **Usage visibility**: See which skills, agents, and tools are actually being used
- **Missed opportunity detection**: Know when Claude could have used a skill but didn't
- **Pattern recommendations**: Surface repeated behaviors that should become skills
- **Redundancy alerts**: Flag overlapping or conflicting configurations

### Key Differentiators

1. **The only player**: No other observability layer exists for AI-assisted development
2. **Zero friction**: Leverages existing session logs—no instrumentation needed
3. **Actionable insights**: Not just data, but specific recommendations to improve your setup
4. **Rule-based transparency**: No ML black boxes—heuristics you can understand and trust

---

## Target Users

### Primary Users

#### The Power Customizer

**Profile:** An advanced Claude Code user who treats it as an all-day coding partner. They've invested significant time building custom skills, agents, and workflows. Comfortable with JSONL logs, YAML frontmatter, and writing scripts.

**Context:** They use Claude Code constantly throughout their workday—it's their primary development companion. They've built a sophisticated setup because they believe in the potential.

**Emotional Reality:** They experience cognitive dissonance. Proud of their setup, but secretly wondering if it's a house of cards. It's like going to the gym every day without a mirror or scale—effort without feedback. They alternate between confidence and self-doubt: *"Is my setup actually good, or am I just making things more complicated?"*

**Core Frustration:** Inconsistent behavior and **cleanup paralysis**. Their CLAUDE.md has grown into technical debt. They want to simplify but are afraid to delete anything—they don't know what's actually being used and what's load-bearing.

**Current Workaround:** Ad-hoc fixes. When they notice Claude not using a skill, they add more instructions. The file grows. Some instructions conflict. The problem gets worse. They never remove anything because they can't prove it's safe to delete.

**What Success Looks Like:**
- Actionable recommendations: "You should create a skill for X—you do this 12 times per week"
- Cleanup suggestions: "These 3 skills overlap, consolidate them" / "This skill hasn't been triggered in 30 days—safe to remove"
- Before/after proof: Evidence that their optimizations actually improved consistency

**The Triggering Event:** They open CLAUDE.md to add yet another instruction, see it's 500+ lines, and freeze. They want to clean it up but realize: *"I have no idea what's load-bearing here."* That's when they search for a solution.

**Discovery Path:** Searches "how to see Claude Code usage" or "Claude Code analytics" → finds observability plugin in marketplace

**Aha Moment:** Acts on first recommendation—consolidates overlapping skills or safely removes an unused one—and sees measurable improvement.

**Expanded Role:** Some Power Customizers also share their setup with teammates, wanting to ensure others benefit from their optimizations. They need visibility not just for themselves, but to prove and explain their setup choices to others.

### User Journey

**Trigger:** CLAUDE.md cleanup paralysis—wants to improve but afraid to break things

**Discovery:** Searches for Claude Code usage visibility → finds observability plugin

**Onboarding:** Installs plugin → runs first usage collection → sees report showing what's actually used vs. ignored

**Aha Moment:** Acts on first recommendation → sees improvement → gains confidence to make more changes

**Core Usage:** Periodically runs analysis after making changes → tracks improvement → builds confidence

**Long-term:** Plugin becomes part of their optimization loop—build → measure → improve → repeat. CLAUDE.md stays lean because they can prove what's working.

---

## Success Metrics

### User Success Indicators

**For the Power Customizer, success means:**

1. **Clarity Gained** — Understanding what's actually happening in sessions vs. assumptions
2. **Reduced Config Bloat** — CLAUDE.md gets leaner while functionality is maintained
3. **Acted on Recommendations** — Plugin provides specific suggestions that lead to real changes
4. **Consistency Improved** — Claude behaves more predictably after optimizations
5. **Hidden Patterns Discovered** — Surfaces repeated behaviors worth standardizing

### Business Objectives

**Primary Objective: Personal Tool Excellence**

Built for personal use first. Success hierarchy:

| Tier | Objective | Why It Matters |
|------|-----------|----------------|
| **Tier 1: Personal Value** | Tool is useful enough to use regularly | If I don't use it, nothing else matters |
| **Tier 2: Quality Gates** | Recommendations are trustworthy | One bad recommendation = trust lost forever |
| **Tier 3: Public Benefit** | Others can install and benefit | Nice to have, not required for success |

### Key Performance Indicators

**Tiered KPIs (in priority order):**

| Tier | KPI | Target | Measurement |
|------|-----|--------|-------------|
| **Must Pass** | Weekly personal usage | Yes | Did I run analysis this week? |
| **Must Pass** | Act on recommendations | ≥1 per run | Did I change something based on findings? |
| **Quality Gate** | Zero "broke my setup" incidents | 0 | No recommendation caused harm |
| **Quality Gate** | Recommendation accuracy | >80% | Suggestions feel correct and relevant |
| **Nice to Have** | Time-to-insight | <5 min | From running collector to understanding |

### Critical Trust Metric

**Zero tolerance for harmful recommendations.** If the plugin ever suggests deleting something that's actually important, trust is lost permanently. Safety > quantity of insights.

### Leading Indicators

- **Analysis completion**: Run full analysis without abandoning
- **Recommendation follow-through**: Act on at least one suggestion
- **Return usage**: Come back after making changes to verify improvement
- **Setup confidence**: Make CLAUDE.md changes without hesitation

---

## MVP Scope

### Current State

**Foundation exists (v2.4.6):**
- Session log parsing and data collection infrastructure
- Skill/agent/hook discovery mechanisms
- Basic session summary generation (Stop hook)
- Plugin architecture and marketplace integration

**Gap to close:** Core analysis intelligence—turning raw data into actionable insights.

**Technical debt note:** 76 ADRs document unresolved decisions. Foundation validation needed before adding features.

### Core Features (MVP)

**Lean MVP—the minimum that creates weekly check-in value:**

1. **Usage Visibility**
   - Show which skills, agents, and tools are actually being triggered
   - Frequency and context of usage
   - Clear report of "what's active vs. dormant"

2. **Missed Opportunity Detection**
   - Identify when Claude could have used a skill but didn't
   - Match user prompts against skill triggers
   - Confidence scoring to reduce false positives

3. **Actionable Output**
   - Clear instructions on what to fix (NOT auto-generated code yet)
   - Manual fix guidance that's specific enough to act on immediately
   - "Here's the problem, here's what to do about it"

### Post-MVP (v1.1)

**Add after lean MVP proves value:**

| Feature | Why Deferred |
|---------|--------------|
| **Redundancy detection** | Requires deeper pattern analysis; lean MVP validates approach first |
| **Pattern surfacing** | Useful but not essential for weekly check-ins |
| **Auto-fix generation** | High accuracy required; trust must be established first. Ship safe, add magic later. |

### Out of Scope (v2.0+)

**Explicitly deferred:**

| Feature | Rationale |
|---------|-----------|
| **Team features** | Multi-user adds complexity; personal tool first |
| **Historical trends** | Requires data persistence infrastructure |
| **Visual dashboard** | Text output is functional; pretty is nice-to-have |
| **Cross-project analysis** | Single-project optimization first |

### MVP Success Criteria

**The lean MVP is "done enough" when:**

1. **Trusted output** — Recommendations are accurate enough to act on
2. **Finds real issues** — Surfaces problems user didn't know about
3. **Actionable format** — Clear enough to act on immediately (manual fixes)

**Quality gate:** Zero harmful recommendations

### Feature Stack (Implementation Order)

```
Usage Visibility (foundation)
    ↓
Missed Opportunities (requires knowing what's available vs. used)
    ↓
[MVP BOUNDARY]
    ↓
Redundancy Detection (v1.1)
    ↓
Pattern Surfacing (v1.1)
    ↓
Auto-Fix Generation (v1.1 - after trust proven)
```

### Future Vision

**If wildly successful (v2.0+):**

- Historical trending and week-over-week comparisons
- Team standardization and shared configs
- Proactive alerts before user runs analysis
- Auto-apply mode with confirmation
- Community patterns from opt-in aggregate data
