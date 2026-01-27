# Architecture Decision Records - Observability Methodology Review

This directory contains ADRs generated during a 1-hour methodology review session on 2026-01-27.

**Note:** Files with `ADR-XXX-` prefix are from this session. Pre-existing ADRs (001-031 without prefix) are from previous work.

## Session Summary (Updated after Research Cycle)

| Status | Count | ADRs |
|--------|-------|------|
| **ACCEPTED** | 37 | ADR-001 to ADR-009, ADR-012 to ADR-016, ADR-018 to ADR-027, ADR-030, ADR-032 to ADR-041, ADR-043, ADR-044 |
| **REJECTED** | 5 | ADR-010, ADR-017, ADR-028, ADR-029, ADR-042 |
| **NEEDS_MORE_INFO** | 3 | ADR-011, ADR-031, ADR-045 |

**Total ADRs from this session: 45**

### Research Cycle Results (2026-01-27)

| ADR | Previous | New | Research Finding |
|-----|----------|-----|------------------|
| ADR-003 | NEEDS_MORE_INFO | ACCEPTED | Workflow stages not used by insights agent - keep as informational-only |
| ADR-004 | NEEDS_MORE_INFO | ACCEPTED | Coverage gaps are speculative - keep with user validation requirement |
| ADR-007 | NEEDS_MORE_INFO | ACCEPTED | Defined multi-dimensional quality criteria framework |
| ADR-008 | NEEDS_MORE_INFO | ACCEPTED | Skill/command duplication confirmed as real HIGH severity problem |
| ADR-017 | NEEDS_MORE_INFO | REJECTED | DDD scored 3/10 - procedural approach is adequate |
| ADR-022 | NEEDS_MORE_INFO | ACCEPTED | Performance 100-200ms (below 500ms threshold) - no optimization needed |
| ADR-023 | NEEDS_MORE_INFO | ACCEPTED | Output structure is well-designed - no changes needed |
| ADR-028 | NEEDS_MORE_INFO | REJECTED | Zero validated user demand - defer indefinitely |
| ADR-030 | NEEDS_MORE_INFO | ACCEPTED | 50+ threshold rare (~10-15%) - current design handles both cases |
| ADR-011 | NEEDS_MORE_INFO | NEEDS_MORE_INFO | Sources identified but false positive rate still unknown |

### Deep Research Cycle Results (2026-01-27)

Critical review of ACCEPTED ADRs revealed significant issues:

| ADR | Previous | Recommendation | Critical Finding |
|-----|----------|----------------|------------------|
| ADR-001 | ACCEPTED | **NEEDS_REVISION** | Threshold inconsistency (>4 vs >3), missing case sensitivity for 3-char acronyms, common word false positives |
| ADR-002 | ACCEPTED | **REJECT** | Tri-state already exists in output; simpler ADR-037 fix addresses actual problem |
| ADR-006 | ACCEPTED | **NEEDS_REVISION** | Classification heuristics have HIGH false positive risk ("thanks" ≠ satisfied); 30s timeout arbitrary |
| ADR-012 | ACCEPTED | **REJECT or SCOPE DOWN** | Building infrastructure for hypothetical problems; many proposed flags unfeasible |
| ADR-014 | ACCEPTED | **REJECT** | Weighted scoring doesn't work within LLM prompt constraints; simpler binary escalation better |
| ADR-018 | ACCEPTED | **REJECT** | Over-engineering; no user demand; current Python constants are sufficient |
| ADR-027 | ACCEPTED | **REJECT hybrid** | All-JSON approach better for AI agent consumer; hybrid adds complexity |
| ADR-033 | ACCEPTED | **NEEDS_REVISION** | May cause MORE problems - false negatives worse than false positives |
| ADR-035 | ACCEPTED | ✅ CONFIRMED | Zero test coverage verified; high ROI; should be first priority |
| ADR-043 | ACCEPTED | **MODIFY** | --no-prompts should be PRIMARY (default); regex sanitization SECONDARY |
| ADR-024 | ACCEPTED | **NEEDS_REVISION** | Tests DO exist (120+); ADR premise outdated; `find_matches()` is actual gap |
| ADR-026 | ACCEPTED | **STRENGTHEN** | Defensive parsing necessary but insufficient; need schema fingerprinting + degradation thresholds |
| ADR-032 | ACCEPTED | **DEPRIORITIZE** | Performance claim misleading (~1ms savings); DRY benefit marginal; low value |
| ADR-037 | ACCEPTED | **DEFER** | Trades false positives for false negatives; merge with ADR-002's tri-state approach |

**Summary**: Deep research of 14 ADRs revealed:
- 6 ADRs should be REJECTED outright
- 5 ADRs need significant REVISION
- 2 ADRs should be DEPRIORITIZED or DEFERRED
- 1 ADR confirmed correct (ADR-035)

## Priority Implementation Order (REVISED after Deep Research)

### High Priority (Core Methodology Fixes)

1. **ADR-035**: Add test coverage for `find_matches()` - MUST BE FIRST ✅ CONFIRMED
2. **ADR-001**: Fix trigger matching - **NEEDS REVISION** (threshold inconsistency >3 vs >4)
3. **ADR-036**: Fix silent error suppression - Straightforward quality fix
4. **ADR-013**: Add sync verification tests for duplicated code
5. **ADR-026**: JSONL schema stability - **STRENGTHEN** (add fingerprinting + degradation thresholds)

### Medium Priority (After Core Fixes)

6. **ADR-034**: Skill/command naming collision detection
7. **ADR-020**: Implement schema 3.2 with all additive changes
8. **ADR-006**: Interrupted tool duration tracking - **NEEDS REVISION** (simplify classification)
9. **ADR-043**: Prompt sanitization - **MODIFY** (--no-prompts as default)

### Defer/Reject Based on Deep Research

**REJECT - Not worth implementing:**
- ~~ADR-002~~: Tri-state already exists; simpler ADR-037 approach if needed
- ~~ADR-012~~: Building infrastructure for hypothetical problems
- ~~ADR-014~~: Weighted scoring doesn't work within LLM prompt constraints
- ~~ADR-018~~: Over-engineering; no user demand for configuration

**DEPRIORITIZE - Low value:**
- ~~ADR-032~~: Performance claim misleading (~1ms); marginal DRY benefit
- ~~ADR-024~~: Tests already exist; premise outdated

**DEFER - Needs more work:**
- ADR-033: May cause false negatives; needs careful design
- ADR-037: Trades false positives for false negatives; merge with ADR-002 concepts
- ADR-027: All-JSON approach better than hybrid; needs redesign

### Lower Priority (Future Enhancements)

10. **ADR-005**: Component-level plugin usage tracking
11. **ADR-009**: Incremental session analysis
12. **ADR-015**: Full analysis, truncated display
13. **ADR-021**: Hook validation warnings
14. **ADR-025**: Separate usage vs best practices analysis
15. **ADR-016**: User value validation process

### Blocked (Require Data/Research)

- **ADR-011**: False positive reduction - need to collect labeled validation data
- **ADR-031**: Version cleanup policy - need execution model decisions
- **ADR-045**: Agent prompt complexity - need interruption frequency and phase dependency data

### Rejected

- **ADR-010**: Compaction metrics - no validated user need
- **ADR-017**: Domain aggregates - DDD overkill for scripting tool (scored 3/10)
- **ADR-028**: Multi-project analysis - zero user demand, architectural anti-pattern
- **ADR-029**: Historical trend tracking - speculative, defer until user demand
- **ADR-042**: Shared logic module - contradicts ADR-013 (duplication with tests is preferred)

## Cross-Cutting Decisions

### ADR-019: No ML Dependencies (POLICY) ✅ CONFIRMED
All ML-based solutions explicitly rejected. Use rule-based approaches with confidence scoring.
- Review after 12 months if accuracy proves insufficient

### ADR-016: MVP + Validate (PROCESS) ✅ CONFIRMED
Ship fast, measure within 30 days, deprecate unused features ruthlessly.

### ADR-020: Schema Versioning (STANDARD) ✅ CONFIRMED
Semantic versioning for data schema. Batch additive changes into minor releases.
- All pending schema changes batch into v3.2

### ~~ADR-018: Configuration Externalization~~ ❌ REJECTED
~~Move hardcoded values to `.claude/observability-config.yaml` with JSON Schema validation.~~
**Deep research finding:** Over-engineering. No user demand. Current Python constants are sufficient.

### ~~ADR-027: Error Handling (Hybrid)~~ ❌ NEEDS REDESIGN
~~Hybrid approach: structured errors in JSON output, critical errors also to stderr.~~
**Deep research finding:** All-JSON approach is better for AI agent consumers. Hybrid adds unnecessary complexity.

## Key Insights from Review

### Methodology Problems Identified

1. **Trigger matching has arbitrary thresholds** (>3 char limit excludes TDD, DDD, API)
2. **Outcome detection defaults to success** (optimistic bias in metrics)
3. **No test coverage** for core detection logic
4. **Multiple hardcoded values** scattered across code
5. **Features built without validated user need** (compaction tracking)
6. **JSONL schema is fragile dependency** (internal Claude Code format)

### Patterns Rejected

- ML-based solutions (embeddings, NLP, classification)
- Cross-project data correlation (privacy concerns)
- Historical trend tracking (speculative)
- Full DDD aggregates (overkill for scripting tool)

### Patterns Accepted

- Rule-based with confidence scoring
- Defensive parsing with error logging
- Incremental testing (TDD)
- All-JSON error output (revised from hybrid)
- Simple priority thresholds (binary escalation, not weighted scoring)

## Review Agents Used

- **Backend Architect**: Technical feasibility, implementation complexity
- **System Architect**: Scalability, maintainability
- **DDD/DNA Architect**: Domain model alignment, bounded contexts

## Session Statistics

- **Duration**: ~1 hour
- **ADRs Generated**: 45
- **Review Cycles**: 8 (research + 3 new ADR batches)
- **Parallel Agent Reviews**: 24
- **Deep Research Agents**: 14 ADRs critically analyzed
- **Initial Acceptance**: 37 (82%)
- **After Deep Research**:
  - Still valid: 25 (56%)
  - Rejected: 11 (24%) - includes 6 new rejections
  - Needs revision: 6 (13%)
  - Needs more info: 3 (7%)

## ADR Index (This Session) - Post Deep Research

| ADR | Title | Initial | After Deep Research | Category |
|-----|-------|---------|---------------------|----------|
| ADR-001 | Trigger Matching Algorithm | ACCEPTED | **NEEDS_REVISION** | Methodology |
| ADR-002 | Outcome Detection Reliability | ACCEPTED | **REJECTED** | Methodology |
| ADR-003 | Workflow Stage Inference | ACCEPTED | ACCEPTED | Methodology |
| ADR-004 | Coverage Gap Detection | ACCEPTED | ACCEPTED | Methodology |
| ADR-005 | Plugin Usage Classification | ACCEPTED | ACCEPTED | Methodology |
| ADR-006 | Interrupted Tool Analysis | ACCEPTED | **NEEDS_REVISION** | Methodology |
| ADR-007 | Description Quality Validation | ACCEPTED | ACCEPTED | Methodology |
| ADR-008 | Overlapping Triggers Detection | ACCEPTED | ACCEPTED | Methodology |
| ADR-009 | Session Sampling Strategy | ACCEPTED | ACCEPTED | Methodology |
| ADR-010 | Compaction Metric Interpretation | REJECTED | REJECTED | Methodology |
| ADR-011 | Missed Opportunity False Positives | NEEDS_MORE_INFO | NEEDS_MORE_INFO | Methodology |
| ADR-012 | Red Flag Detection Completeness | ACCEPTED | **REJECTED** | Methodology |
| ADR-013 | Data Duplication Strategy | ACCEPTED | ACCEPTED | Architecture |
| ADR-014 | Category Priority Calculation | ACCEPTED | **REJECTED** | Methodology |
| ADR-015 | Prompt Length Truncation | ACCEPTED | ACCEPTED | Methodology |
| ADR-016 | User Value Validation Process | ACCEPTED | ACCEPTED | Process |
| ADR-017 | Domain Model Aggregates | REJECTED | REJECTED | Architecture |
| ADR-018 | Configuration Externalization | ACCEPTED | **REJECTED** | Architecture |
| ADR-019 | ML Dependency Policy | ACCEPTED | ACCEPTED | Policy |
| ADR-020 | Schema Versioning Strategy | ACCEPTED | ACCEPTED | Architecture |
| ADR-021 | Hook Discovery Validation | ACCEPTED | ACCEPTED | Methodology |
| ADR-022 | Discovery Performance | ACCEPTED | ACCEPTED | Performance |
| ADR-023 | Agent Output Structure | ACCEPTED | ACCEPTED | Methodology |
| ADR-024 | Test Coverage | ACCEPTED | **NEEDS_REVISION** | Quality |
| ADR-025 | Cross-Context Insights | ACCEPTED | ACCEPTED | Methodology |
| ADR-026 | JSONL Schema Stability | ACCEPTED | **STRENGTHEN** | Risk |
| ADR-027 | Error Handling Strategy | ACCEPTED | **NEEDS_REDESIGN** | Architecture |
| ADR-028 | Multi-Project Analysis | REJECTED | REJECTED | Feature |
| ADR-029 | Historical Trend Tracking | REJECTED | REJECTED | Feature |
| ADR-030 | Insights Agent Resumability | ACCEPTED | ACCEPTED | UX |
| ADR-031 | Version Cleanup Policy | NEEDS_MORE_INFO | NEEDS_MORE_INFO | Operations |
| ADR-032 | Duplicate Discovery Consolidation | ACCEPTED | **DEPRIORITIZE** | Architecture |
| ADR-033 | Negation Pattern Detection | ACCEPTED | **DEFER** | Methodology |
| ADR-034 | Skill/Command Naming Collision | ACCEPTED | ACCEPTED | Methodology |
| ADR-035 | find_matches() Test Coverage | ACCEPTED | ✅ **CONFIRMED** | Quality |
| ADR-036 | Silent Error Suppression | ACCEPTED | ACCEPTED | Quality |
| ADR-037 | Outcome False Positives | ACCEPTED | **DEFER** | Methodology |
| ADR-038 | Date Parsing Validation | ACCEPTED | ACCEPTED | Quality |
| ADR-039 | Truncation Metadata | ACCEPTED | ACCEPTED | UX |
| ADR-040 | Tool Input Validation | ACCEPTED | ACCEPTED | Quality |
| ADR-041 | Hook Input Validation | ACCEPTED | ACCEPTED | Quality |
| ADR-042 | Shared Logic Module | REJECTED | REJECTED | Architecture |
| ADR-043 | Prompt Sanitization | ACCEPTED | **MODIFY** | Security |
| ADR-044 | Hook Test Coverage | ACCEPTED | ACCEPTED | Quality |
| ADR-045 | Agent Prompt Complexity | NEEDS_MORE_INFO | NEEDS_MORE_INFO | UX |
