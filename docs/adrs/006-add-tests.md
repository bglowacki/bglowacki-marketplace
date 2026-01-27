# ADR-006: Add Test Coverage

## Status
PROPOSED

## Context
The observability plugin has no visible test files. Key logic that should be tested:
- Outcome detection (`detect_outcome`)
- Workflow stage inference (`infer_workflow_stage`)
- JSONL parsing (`parse_session_file`)
- Trigger extraction (`extract_triggers_from_description`)
- Setup profile computation

## Finding
**Missing**: No `tests/` directory, no test files

**Risk**:
- Regressions can go unnoticed
- Refactoring (like ADR-003, ADR-004) is risky without tests
- Edge cases in JSONL parsing may cause silent failures

## Decision
TBD - Needs review

## Recommendation
Add pytest test suite covering:

1. **Unit tests**:
   - `test_outcome_detection.py` - Various tool result patterns
   - `test_workflow_stages.py` - Stage inference from tools
   - `test_trigger_extraction.py` - Parsing descriptions
   - `test_session_parsing.py` - JSONL edge cases

2. **Integration tests**:
   - `test_collect_usage.py` - Full pipeline with fixtures
   - `test_session_summary.py` - Hook output validation

3. **Fixtures**:
   - Sample JSONL files with various scenarios
   - Expected output fixtures

## Impact
- Enables safe refactoring
- Documents expected behavior
- Catches regressions early
- Required for ADR-003 and ADR-004 implementation

## Review Notes
- Severity: Medium (quality/safety concern)
- Effort: High (significant test writing)
- Risk: None (adding tests doesn't break existing code)
- Prerequisite for: ADR-003, ADR-004
