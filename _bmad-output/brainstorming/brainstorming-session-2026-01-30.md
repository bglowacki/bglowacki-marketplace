---
stepsCompleted: [1, 2, 3, 4]
inputDocuments: ['docs/adrs/ADR-077-semantic-stemming-overlap-detection.md', 'docs/adrs/ADR-078-overlap-resolution-guidance.md', 'docs/adrs/ADR-079-intentional-overlap-classification.md']
session_topic: 'Overlap detection improvements for observability plugin (ADR-077, 078, 079)'
session_goals: 'Finalize ADR decisions, stress-test proposed approaches, surface missed alternatives or edge cases'
selected_approach: 'Progressive Technique Flow'
techniques_used: ['Assumption Reversal', 'Morphological Analysis', 'Six Thinking Hats', 'Decision Tree Mapping']
ideas_generated: [9]
context_file: ''
---

# Brainstorming Session Results

**Facilitator:** Bartek
**Date:** 2026-01-30

## Session Overview

**Topic:** Overlap detection improvements for the observability plugin — stemming (ADR-077), resolution guidance (ADR-078), and intentional overlap classification (ADR-079)
**Goals:** Finalize ADR decisions, stress-test proposed approaches, surface missed alternatives or edge cases

### Key Discoveries

1. **The problem is two problems:** Morphological variants (debug/debugging) AND semantic phrase overlap (code review/review changes). Original ADR-077 only addressed the first.
2. **Token-set matching** solves both sub-problems in one mechanism — tokenize, stem each word, compare sets via Jaccard similarity.
3. **grepai is design-time, not runtime** — ADR-019 blocks ML dependencies for core analysis.
4. **Resolution guidance belongs in the walk-through skill**, not as static templates in detector output.
5. **Intent detection needs positive signals** for v2, but same-source heuristic is good enough for MVP.
6. **PATTERN classification** turns false-positive warnings into positive architecture insights.

### Technique Execution

**Phase 1 — Assumption Reversal:** Challenged all 10 assumptions across three ADRs. Key finding: suffix stripping is insufficient because triggers include multi-word phrases.

**Phase 2 — Morphological Analysis:** Mapped 5 parameters × 3-4 options each. Identified MVP combination: token-set matching + brief inline hints + same-source heuristic + PATTERN category.

**Phase 3 — Six Thinking Hats:** Stress-tested MVP through facts, benefits, risks, gut feel, alternatives, and process. Confirmed token-set with Jaccard similarity as the approach.

**Phase 4 — Decision Tree Mapping:** Produced final ADR decisions and implementation order.

### Final Decisions

- **ADR-077:** Rewrite — token-set matching with suffix stripping and Jaccard similarity (threshold ≥ 0.5)
- **ADR-078:** Shrink — brief inline hints only, detailed guidance deferred to walk-through skill
- **ADR-079:** Keep + add PATTERN classification alongside severity levels
