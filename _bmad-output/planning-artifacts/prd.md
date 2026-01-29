---
stepsCompleted: [step-01-init, step-02-discovery, step-03-success, step-04-scope, step-05-requirements, step-06-stories, step-07-complete]
inputDocuments:
  - _bmad-output/planning-artifacts/product-brief-bglowacki-marketplace-2026-01-28.md
  - docs/index.md
  - docs/project-overview.md
  - docs/architecture.md
  - docs/adrs/README.md
  - docs/adrs/ADR-001-trigger-matching-algorithm.md
  - docs/adrs/ADR-067-implementation-priority.md
workflowType: 'prd'
documentCounts:
  brief: 1
  research: 0
  brainstorming: 0
  projectDocs: 3
  adrs: 3
classification:
  projectType: developer_tool
  domain: general
  complexity: low
  projectContext: brownfield
---

# Product Requirements Document - bglowacki-marketplace

**Author:** Bartek
**Date:** 2026-01-28
**Source:** Product Brief (2026-01-28)

---

## 1. Executive Summary

bglowacki-marketplace provides the **only observability layer for AI-assisted development**—giving Claude Code users visibility into what's actually being used, what's being ignored, and what patterns should become their next skill.

**The Problem:** Claude Code users invest significant effort customizing their environments with skills, agents, and workflows. But there's no way to know if that investment pays off. The gap between what's built and what's actually used creates cleanup paralysis and wasted effort.

**The Solution:** Analyze Claude Code session logs to provide data-driven insights with actionable recommendations.

---

## 2. Product Vision

### Problem Statement

Claude Code users invest significant effort customizing their environments. But there's no way to know if that investment pays off. You suspect Claude is missing opportunities to use your tools—but you can't prove it. The gap between what you've built and what actually gets used creates a frustrating question: *"Did I waste my time?"*

### Problem Impact

- **The "did it work?" anxiety**: Built custom skills but no idea if they're triggered
- **Invisible inefficiency**: Same tasks done differently each session
- **Reactive treadmill**: Adding instructions only when problems surface
- **Instruction rot**: CLAUDE.md grows unwieldy while skills overlap or get ignored

### Proposed Solution

Analyze Claude Code session logs to provide data-driven insights:
- **Usage visibility**: See which skills, agents, and tools are actually being used
- **Missed opportunity detection**: Know when Claude could have used a skill but didn't
- **Actionable output**: Clear instructions on what to fix

### Key Differentiators

1. **The only player**: No other observability layer exists for AI-assisted development
2. **Zero friction**: Leverages existing session logs—no instrumentation needed
3. **Actionable insights**: Not just data, but specific recommendations
4. **Rule-based transparency**: No ML black boxes—heuristics you can understand

---

## 3. Target Users

### Primary Persona: The Power Customizer

**Profile:** Advanced Claude Code user who treats it as an all-day coding partner. Invested significant time building custom skills, agents, and workflows. Comfortable with JSONL logs, YAML frontmatter, and writing scripts.

**Emotional Reality:** Cognitive dissonance—proud of their setup but secretly wondering if it's a house of cards. Like going to the gym every day without a mirror or scale.

**Core Frustration:** Inconsistent behavior and **cleanup paralysis**. CLAUDE.md has grown into technical debt. Want to simplify but afraid to delete anything—don't know what's load-bearing.

**Triggering Event:** Open CLAUDE.md to add yet another instruction, see it's 500+ lines, freeze. *"I have no idea what's load-bearing here."*

**Success Looks Like:**
- Actionable recommendations: "You should create a skill for X—you do this 12 times per week"
- Cleanup suggestions: "These 3 skills overlap, consolidate them"
- Before/after proof: Evidence that optimizations actually improved consistency

### User Journey

1. **Trigger:** CLAUDE.md cleanup paralysis
2. **Discovery:** Searches for Claude Code usage visibility → finds plugin
3. **Onboarding:** Installs → runs first collection → sees usage report
4. **Aha Moment:** Acts on first recommendation → sees improvement
5. **Core Usage:** Weekly analysis as part of optimization routine
6. **Long-term:** Build → measure → improve → repeat

---

## 4. Success Metrics

### Tiered KPIs

| Tier | KPI | Target | Measurement |
|------|-----|--------|-------------|
| **Must Pass** | Weekly personal usage | Yes | Run analysis this week? |
| **Must Pass** | Act on recommendations | ≥1 per run | Change something based on findings? |
| **Quality Gate** | Zero "broke my setup" incidents | 0 | No harmful recommendations |
| **Quality Gate** | Recommendation accuracy | >80% | Suggestions feel correct |
| **Nice to Have** | Time-to-insight | <5 min | From running collector to understanding |

### Critical Trust Metric

**Zero tolerance for harmful recommendations.** If the plugin ever suggests deleting something important, trust is lost permanently. Safety > quantity of insights.

---

## 5. MVP Scope

### Current State (v2.4.6)

**Foundation exists:**
- Session log parsing and data collection infrastructure
- Skill/agent/hook discovery mechanisms
- Basic session summary generation (Stop hook)
- Plugin architecture and marketplace integration

**Gap to close:** Core analysis intelligence—turning raw data into actionable insights.

### Lean MVP Features

**1. Usage Visibility**
- Show which skills, agents, and tools are actually being triggered
- Frequency and context of usage
- Clear report of "what's active vs. dormant"

**2. Missed Opportunity Detection**
- Identify when Claude could have used a skill but didn't
- Match user prompts against skill triggers
- Confidence scoring to reduce false positives

**3. Actionable Output**
- Clear instructions on what to fix (NOT auto-generated code yet)
- Manual fix guidance that's specific enough to act on immediately
- "Here's the problem, here's what to do about it"

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

### Out of Scope (Post-MVP)

| Feature | Version | Rationale |
|---------|---------|-----------|
| Redundancy detection | v1.1 | Requires deeper pattern analysis |
| Pattern surfacing | v1.1 | Useful but not essential for weekly check-ins |
| Auto-fix generation | v1.1 | High accuracy required; trust first |
| Team features | v2.0 | Multi-user adds complexity |
| Historical trends | v2.0 | Requires data persistence |
| Visual dashboard | v2.0 | Text output is functional |

---

## 6. Technical Constraints

### From ADR Decisions

| Constraint | Source | Impact |
|------------|--------|--------|
| No ML dependencies | ADR-019 | Rule-based matching only |
| Trigger matching needs revision | ADR-001 | Threshold inconsistency (>3 vs >4) must be fixed |
| Test coverage first | ADR-035 | Tests for `find_matches()` before logic changes |
| Schema versioning | ADR-020 | Semantic versioning for data schema |
| No external network calls | Architecture | JSONL-only, local file system |
| Hook timeout: 10 seconds | Plugin manifest | Keep processing fast |

### Technical Debt

- 76 ADRs document unresolved decisions
- Dual threshold inconsistency in trigger matching
- Zero test coverage for core `find_matches()` function
- Code duplication (by design per ADR-013, but requires sync tests)

---

## 7. Functional Requirements

### FR-1: Usage Visibility

#### FR-1.1: Data Collection
- **FR-1.1.1**: Collect usage data from Claude Code session JSONL files
- **FR-1.1.2**: Support configurable time range via `--days N` parameter (default: 7)
- **FR-1.1.3**: Discover all installed skills, agents, commands, and hooks
- **FR-1.1.4**: Parse session logs to identify tool invocations and skill triggers

#### FR-1.2: Usage Report
- **FR-1.2.1**: Generate per-skill usage counts with session context
- **FR-1.2.2**: Include per-project breakdown when multiple projects analyzed
- **FR-1.2.3**: Include timestamps for usage timeline
- **FR-1.2.4**: Classify each skill/agent as: Active (used), Dormant (triggers matched but not invoked), or Unused (no matching triggers)

#### FR-1.3: Output Format
- **FR-1.3.1**: Output structured JSON for agent consumption
- **FR-1.3.2**: Include metadata: schema version, collection timestamp, session count

### FR-2: Missed Opportunity Detection

#### FR-2.1: Trigger Matching
- **FR-2.1.1**: Match user prompts against skill/agent trigger phrases
- **FR-2.1.2**: Use unified threshold (≥3 characters) per ADR-001
- **FR-2.1.3**: Apply uppercase rule for 3-char acronyms (TDD, API, etc.)
- **FR-2.1.4**: Exclude common words via blocklist per ADR-001

#### FR-2.2: Confidence Scoring
- **FR-2.2.1**: Calculate match confidence using weighted factors:
  - Trigger length score (longer = more specific = higher confidence)
  - Trigger specificity (multi-word phrases > single words)
  - Match position (beginning of prompt = higher intent signal)
  - Formula: `confidence = (length_score + specificity_score + position_score) / 3`
- **FR-2.2.2**: Only surface matches with >80% confidence (high confidence)
- **FR-2.2.3**: Include confidence score in output for transparency
- **FR-2.2.4**: PREREQUISITE: Implement tests for `find_matches()` before adding confidence logic (per ADR-035)

#### FR-2.3: Opportunity Classification
- **FR-2.3.1**: "Missed" = trigger matched but skill not invoked in that session
- **FR-2.3.2**: Group opportunities by skill/agent for consolidated recommendations
- **FR-2.3.3**: Include example prompts that triggered the match

### FR-3: Actionable Output

#### FR-3.1: Interactive Agent Workflow
- **FR-3.1.0**: Present summary dashboard FIRST before detailed walk-through:
  - Total findings count by category
  - Top 3 highest-impact recommendations highlighted
  - User selects category to drill into
- **FR-3.1.1**: Agent presents findings one-by-one within selected category
- **FR-3.1.2**: For each finding, provide: problem description, evidence, recommended action
- **FR-3.1.3**: User can accept, skip, or request more detail on each finding

#### FR-3.2: Recommendation Format
- **FR-3.2.1**: Each recommendation includes specific action to take
- **FR-3.2.2**: Provide copy-paste-ready instructions where applicable
- **FR-3.2.3**: Explain WHY this is a recommendation (evidence-based)

#### FR-3.3: Safety Constraints
- **FR-3.3.1**: Deletion/removal recommendations require ALL of:
  - Zero trigger matches in analyzed period
  - Skill has no hard dependencies
  - User explicitly opts into "cleanup mode"
  - Always flag as "REVIEW CAREFULLY" (never "safe to delete")
- **FR-3.3.2**: Default behavior: Do NOT recommend deletions unless cleanup mode enabled
- **FR-3.3.3**: Provide rollback guidance for any recommended changes

---

## 8. User Stories

### Epic 1: Usage Collection (Collector - Python)

#### US-1.1: Run Usage Collection
**As a** Power Customizer
**I want to** run a usage collection on my Claude Code sessions
**So that** I can see what skills and agents are actually being used

**Acceptance Criteria:**
- [ ] Can invoke via `/observability-usage-collector` or trigger phrases
- [ ] Supports `--days N` parameter (default: 7)
- [ ] Discovers all installed skills, agents, commands, hooks
- [ ] Parses all session JSONL files in the time range
- [ ] Outputs structured JSON with schema version metadata
- [ ] Completes within 2 minutes for up to 500 sessions
- [ ] Provides progress indicator for long-running collections
- [ ] Gracefully handles malformed JSONL entries (skip + log, don't crash)
- [ ] Reports parsing errors in output metadata (per ADR-026)

#### US-1.2: View Usage Report
**As a** Power Customizer
**I want to** see a breakdown of which skills are active, dormant, or unused
**So that** I know what's actually working in my setup

**Acceptance Criteria:**
- [ ] Each skill/agent classified as: Active, Dormant, or Unused
- [ ] Active = invoked at least once in the period
- [ ] Dormant = triggers matched in prompts but never invoked
- [ ] Unused = no matching triggers found
- [ ] Per-project breakdown when multiple projects present
- [ ] Usage counts with session context (which sessions used it)

---

### Epic 2: Missed Opportunity Detection (Collector - Python)

#### US-2.0: Implement Confidence Scoring (PREREQUISITE)
**As a** developer
**I want to** add confidence scoring to find_matches()
**So that** missed opportunity detection can filter by confidence

**Acceptance Criteria:**
- [ ] Tests exist for current find_matches() behavior (ADR-035) - MUST BE FIRST
- [ ] Confidence formula implemented per FR-2.2.1
- [ ] Confidence returned in match results
- [ ] Threshold consistency fixed (≥3 chars unified)

#### US-2.1: Detect Missed Opportunities
**As a** Power Customizer
**I want to** know when Claude could have used a skill but didn't
**So that** I can improve my CLAUDE.md instructions or skill triggers

**Acceptance Criteria:**
- [ ] Matches user prompts against skill trigger phrases
- [ ] Uses ≥3 char threshold with uppercase rule for acronyms
- [ ] Excludes common words via blocklist
- [ ] Only surfaces matches with >80% confidence
- [ ] Groups opportunities by skill for consolidated view
- [ ] Includes example prompts that triggered the match

**Dependencies:** US-2.0 (confidence scoring)

#### US-2.2: Understand Match Confidence
**As a** Power Customizer
**I want to** see why a match was flagged as a missed opportunity
**So that** I can trust the recommendation

**Acceptance Criteria:**
- [ ] Confidence score visible for each match
- [ ] Factors explained: trigger length, specificity, position
- [ ] High confidence (>80%) clearly distinguished from lower

---

### Epic 3: Actionable Output (Agent - Markdown)

#### US-3.0: Handle Empty States
**As a** Power Customizer
**I want to** see helpful messages when there's nothing to report
**So that** I know the analysis worked even if there are no issues

**Acceptance Criteria:**
- [ ] "No sessions found in the last N days" with suggestion to extend range
- [ ] "No skills/agents installed" with link to documentation
- [ ] "All systems healthy - no missed opportunities detected" (positive confirmation)
- [ ] Parsing errors summarized if any occurred

#### US-3.1: Review Findings Summary
**As a** Power Customizer
**I want to** see a summary dashboard of all findings first
**So that** I can prioritize what to review during my weekly check-in

**Acceptance Criteria:**
- [ ] Shows total findings count by category
- [ ] Highlights top 3 highest-impact recommendations
- [ ] Lets me choose which category to drill into
- [ ] Doesn't overwhelm with 50-item linear lists

#### US-3.2: Walk Through Recommendations
**As a** Power Customizer
**I want to** review findings one-by-one with the agent
**So that** I can decide which actions to take

**Acceptance Criteria:**
- [ ] Each finding shows: problem, evidence, recommended action
- [ ] Can accept, skip, or request more detail
- [ ] Copy-paste-ready instructions where applicable
- [ ] Explains WHY this is recommended (evidence-based)

#### US-3.3: Safe Cleanup Mode
**As a** Power Customizer
**I want to** optionally enable cleanup suggestions
**So that** I can identify truly unused skills to remove

**Acceptance Criteria:**
- [ ] Cleanup mode is OPT-IN (not default)
- [ ] Deletion suggestions only when: zero triggers AND no dependencies
- [ ] Always flagged as "REVIEW CAREFULLY"
- [ ] Includes rollback guidance
- [ ] Never says "safe to delete"

---

## 9. Implementation Notes

### Work Stream Split

| Epic | Codebase | Type |
|------|----------|------|
| Epic 1 (Usage Collection) | `collect_usage.py` | Collector (Python) |
| Epic 2 (Missed Opportunities) | `collect_usage.py` | Collector (Python) |
| Epic 3 (Actionable Output) | `usage-insights-agent.md` | Agent (Markdown) |

### Dependency Chain

```
US-2.0 (tests + confidence)
    ↓
US-2.1 (missed opportunity detection)
    ↓
US-3.1 (summary dashboard)
    ↓
US-3.2 (walk-through)
```

**Parallelizable:** US-1.x and US-3.0 can be done independently.

### Priority Order (per ADR-067)

1. **ADR-035**: Tests for `find_matches()` - MUST BE FIRST
2. **US-2.0**: Confidence scoring (depends on tests)
3. **US-1.1/1.2**: Usage collection improvements
4. **US-2.1/2.2**: Missed opportunity detection
5. **US-3.x**: Agent improvements

---

## 10. Appendix

### Related Documents

| Document | Purpose |
|----------|---------|
| Product Brief | Vision, users, metrics, MVP scope |
| ADR-001 | Trigger matching algorithm |
| ADR-035 | Test coverage priority |
| ADR-067 | Implementation priority |
| docs/architecture.md | System design, data flow |

### Glossary

| Term | Definition |
|------|------------|
| **Active** | Skill/agent invoked at least once in analyzed period |
| **Dormant** | Skill with matching triggers in prompts but never invoked |
| **Unused** | Skill with no matching triggers in prompts |
| **Missed Opportunity** | Prompt that matched a skill's triggers but skill wasn't used |
| **Confidence Score** | 0-100% measure of match quality based on trigger specificity |
