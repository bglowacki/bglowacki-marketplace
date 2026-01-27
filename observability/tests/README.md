# Observability Plugin Tests

Test suite for the observability plugin.

## Running Tests

```bash
# Install pytest if needed
pip install pytest

# Run all tests
cd observability
pytest tests/ -v

# Run specific test file
pytest tests/test_outcome_detection.py -v

# Run with coverage
pip install pytest-cov
pytest tests/ --cov=hooks --cov=skills/observability-usage-collector/scripts
```

## Test Structure

- `test_outcome_detection.py` - Tests for `detect_outcome()` function
- `test_workflow_stages.py` - Tests for `infer_workflow_stage()` function
- `test_session_parsing.py` - Tests for `parse_session_file()` function

## Test Coverage

### Outcome Detection
- Bash command outcomes (exit codes, errors, timeouts)
- Edit/Write outcomes (permission errors, file not found)
- Generic tool outcomes
- Implementation parity between hook and collector scripts

### Workflow Stages
- Skill-based stage inference (brainstorm, plan, review, test, commit)
- Edit/Write → implement stage
- Bash command stage detection (test, commit, deploy)
- Task (agent) based stages
- Documents ADR-011 gaps (missing research stage)

### Session Parsing
- Tool counting and outcome tracking
- Compaction detection
- Interruption handling
- Skill and agent usage tracking
- Stage transition tracking
- Malformed input handling
