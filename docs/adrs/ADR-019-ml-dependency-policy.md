# ADR-019: ML Dependency Policy

**Status:** ACCEPTED
**Date:** 2026-01-27
**Category:** Policy
**Decision:** No ML dependencies for core analysis functionality

## Context

Multiple ADRs proposed ML-based solutions that were rejected:
- ADR-001 Option B: ML embeddings for trigger matching - REJECTED
- ADR-002 Option D: ML classification for outcome detection - REJECTED
- ADR-004 Option D: Dynamic domain discovery via NLP - REJECTED
- ADR-006 Option D: NLP for interruption intent extraction - REJECTED
- ADR-007 Option A: LLM-based description quality scoring - NEEDS_MORE_INFO

Pattern: ML solutions repeatedly proposed but rejected as over-engineering.

## Decision

**POLICY: No ML dependencies for core analysis functionality.**

### Rationale

1. **Dependency burden**: ML models require additional dependencies (torch, transformers, etc.)
2. **Reproducibility**: Rule-based analysis is deterministic and auditable
3. **Operational complexity**: Model versioning, updates, and inference latency
4. **Overkill for domain**: Text patterns in Claude sessions are structured enough for rules
5. **`uv run --script` compatibility**: ML dependencies break standalone operation

### Exceptions

ML may be considered only when:
1. Rule-based approach has proven insufficient (with data showing >30% improvement needed)
2. Sample validation: accuracy drops below 80% on 100+ session sample
3. User has explicitly opted in via configuration
4. Dependency is optional, not required for core functionality

### Approved Patterns Instead

| Instead of ML | Use This |
|--------------|----------|
| Embedding similarity | Keyword matching with stemming |
| Classification | Rule-based with confidence scores |
| NLP extraction | Regex patterns with fallback |
| Quality scoring | Template-based validation |

### Sunset Clause

Review this policy after 12 months of production usage data. If rule-based accuracy proves insufficient with documented evidence, revisit ML options.

## Review Summary

### DDD Architect Review
- **Verdict:** ACCEPT
- **Alignment:** DNA principles of deferred decisions and context-appropriate complexity
- **Praise:** Documents cross-ADR pattern, preventing repeated debates
- **Suggestion:** Add concrete threshold for "proven insufficient" (done: 80% accuracy)

### Cross-ADR Pattern
- Backend Architect: "ML overhead is not justified for this domain"
- System Architect: "NLP extraction introduces ML dependency, training data requirements"
- DDD Architect: "Introduces prohibitive temporal coupling"

## Consequences

- Simpler, more maintainable codebase
- Deterministic, reproducible analysis
- No model versioning or update concerns
- May sacrifice some accuracy in edge cases (acceptable tradeoff)
- Clear path to reconsider if data proves rules insufficient
