# ADR-067: Implementation Priority Recommendation

## Status
PROPOSED

## Context
This review session generated 31 ADRs (ADR-046 to ADR-076) covering documentation, code quality, architecture, and feature improvements. This ADR provides a recommended implementation order.

## Prioritized Implementation Plan

### Phase 1: Quick Wins (Trivial Effort, High Impact)
| ADR | Title | Effort | Why First |
|-----|-------|--------|-----------|
| ADR-046 | Update Marketplace Description | 5 min | Single line, user-facing |
| ADR-052 | Hook Timeout Risk | 5 min | Single line, prevents silent failures |
| ADR-062 | Settings.local.json to .gitignore | 5 min | Security hygiene |

### Phase 2: Documentation Cleanup (Low Effort, Medium Impact)
| ADR | Title | Effort | Why |
|-----|-------|--------|-----|
| ADR-047 | Update Root README.md | 30 min | Critical mismatch with reality |
| ADR-057 | Plugin Version Mismatch (CHANGELOG) | 30 min | Version history needed |
| ADR-058 | Stale Design Documents | 15 min | Add superseded notes |
| ADR-063 | Add Project-Level CLAUDE.md | 20 min | Development context |
| ADR-053 | Schema Version Changelog | 15 min | API versioning |

### Phase 3: Code Quality (Medium Effort, Foundation for Future)
| ADR | Title | Effort | Why |
|-----|-------|--------|-----|
| ADR-051 | Add Tests | High | PREREQUISITE for Phase 4 |
| ADR-054 | Magic Numbers | Low | Readability |
| ADR-065 | Centralize Path.home() | Low | Maintainability |
| ADR-048 | Deduplicate detect_outcome | Medium | DRY principle |

### Phase 4: Architecture Improvements (Requires Tests First)
| ADR | Title | Effort | Depends On |
|-----|-------|--------|------------|
| ADR-049 | Split collect_usage.py | High | ADR-051 |
| ADR-056 | Workflow Stage Gaps | Medium | ADR-051 |
| ADR-060 | Reduce Agent Complexity | Medium | None |

### Phase 5: Feature Enhancements (Nice-to-Have)
| ADR | Title | Effort |
|-----|-------|--------|
| ADR-055 | Error Handling/Logging | Medium |
| ADR-061 | Cleanup Command | Medium |
| ADR-066 | Cross-Platform Notifications | Low |
| ADR-050 | Skill/Command Redundancy | Low (docs only) |

### Defer/Skip
| ADR | Title | Reason |
|-----|-------|--------|
| ADR-059 | Date Typos | Very low priority |
| ADR-064 | Notification Security | Low risk, accepted as-is |

## Recommended Implementation Order

1. **Day 1**: ADRs 046, 052, 062 (3 quick wins)
2. **Day 2**: ADRs 047, 057, 063 (documentation)
3. **Week 1**: ADR-051 (test foundation)
4. **Week 2**: ADRs 054, 065, 048 (code cleanup)
5. **Week 3+**: ADRs 049, 056 (major refactoring)

## Decision
This ADR is for reference only - implementation order can be adjusted based on priorities.
