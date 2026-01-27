# ADR-022: Implementation Priority Recommendation

## Status
PROPOSED

## Context
This review session generated 21 ADRs covering documentation, code quality, architecture, and feature improvements. This ADR provides a recommended implementation order.

## Prioritized Implementation Plan

### Phase 1: Quick Wins (Trivial Effort, High Impact)
| ADR | Title | Effort | Why First |
|-----|-------|--------|-----------|
| 001 | Update Marketplace Description | 5 min | Single line, user-facing |
| 007 | Hook Timeout Risk | 5 min | Single line, prevents silent failures |
| 017 | Settings.local.json to .gitignore | 5 min | Security hygiene |

### Phase 2: Documentation Cleanup (Low Effort, Medium Impact)
| ADR | Title | Effort | Why |
|-----|-------|--------|-----|
| 002 | Update Root README.md | 30 min | Critical mismatch with reality |
| 012 | Plugin Version Mismatch (CHANGELOG) | 30 min | Version history needed |
| 013 | Stale Design Documents | 15 min | Add superseded notes |
| 018 | Add Project-Level CLAUDE.md | 20 min | Development context |
| 008 | Schema Version Changelog | 15 min | API versioning |

### Phase 3: Code Quality (Medium Effort, Foundation for Future)
| ADR | Title | Effort | Why |
|-----|-------|--------|-----|
| 006 | Add Tests | High | PREREQUISITE for Phase 4 |
| 009 | Magic Numbers | Low | Readability |
| 020 | Centralize Path.home() | Low | Maintainability |
| 003 | Deduplicate detect_outcome | Medium | DRY principle |

### Phase 4: Architecture Improvements (Requires Tests First)
| ADR | Title | Effort | Depends On |
|-----|-------|--------|------------|
| 004 | Split collect_usage.py | High | ADR-006 |
| 011 | Workflow Stage Gaps | Medium | ADR-006 |
| 015 | Reduce Agent Complexity | Medium | None |

### Phase 5: Feature Enhancements (Nice-to-Have)
| ADR | Title | Effort |
|-----|-------|--------|
| 010 | Error Handling/Logging | Medium |
| 016 | Cleanup Command | Medium |
| 021 | Cross-Platform Notifications | Low |
| 005 | Skill/Command Redundancy | Low (docs only) |

### Defer/Skip
| ADR | Title | Reason |
|-----|-------|--------|
| 014 | Date Typos | Very low priority |
| 019 | Notification Security | Low risk, accepted as-is |

## Recommended Implementation Order

1. **Day 1**: ADRs 001, 007, 017 (3 quick wins)
2. **Day 2**: ADRs 002, 012, 018 (documentation)
3. **Week 1**: ADR-006 (test foundation)
4. **Week 2**: ADRs 009, 020, 003 (code cleanup)
5. **Week 3+**: ADRs 004, 011 (major refactoring)

## Decision
This ADR is for reference only - implementation order can be adjusted based on priorities.
