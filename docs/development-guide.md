# Development Guide

## Prerequisites

- **Python 3.10+** - Required for type hints and modern syntax
- **uv** - Package manager ([install](https://docs.astral.sh/uv/getting-started/installation/))
- **Claude Code CLI** - For testing plugin integration

## Quick Start

```bash
# Clone the repository
git clone https://github.com/bglowacki/bglowacki-marketplace.git
cd bglowacki-marketplace

# Install development dependencies
cd observability
uv sync

# Run tests
uv run pytest tests/

# Test the hook manually
echo '{"session_id":"test123","cwd":"/tmp"}' | uv run hooks/generate_session_summary.py
```

## Project Structure

```
observability/
├── hooks/              # Event hooks (Stop hook)
├── skills/             # User-invocable skills
├── agents/             # AI agent definitions
├── commands/           # Shortcut commands
├── tests/              # pytest test suite
├── docs/plans/         # Design documents
├── pyproject.toml      # Python project config
└── .claude-plugin/     # Plugin manifest
```

## Development Workflow

### 1. Making Changes

1. Create a feature branch
2. Make changes to relevant files
3. Run tests: `uv run pytest tests/ -v`
4. Update version in `.claude-plugin/plugin.json` if needed
5. Update CHANGELOG.md

### 2. Testing Changes

```bash
# Run all tests
uv run pytest tests/

# Run specific test file
uv run pytest tests/test_outcome_detection.py -v

# Run with coverage
uv run pytest tests/ --cov=hooks --cov=skills

# Test hook manually
echo '{"session_id":"abc123","cwd":"/path/to/project"}' | uv run hooks/generate_session_summary.py

# Test collector script
uv run skills/observability-usage-collector/scripts/collect_usage.py --quick-stats --days 7
```

### 3. Version Management

**Always bump the version before pushing changes.**

Update version in `observability/.claude-plugin/plugin.json`:

```json
{
  "name": "observability",
  "version": "2.4.7",  // <-- Update this
  ...
}
```

Use semantic versioning:
- **PATCH** (x.x.X): Bug fixes, minor improvements
- **MINOR** (x.X.0): New features, new skills/agents
- **MAJOR** (X.0.0): Breaking changes

## Key Files

### hooks/generate_session_summary.py

The Stop hook that runs on session end. Key functions:

- `get_session_file()` - Locate session JSONL
- `detect_outcome()` - Classify tool outcomes
- `infer_workflow_stage()` - Track workflow stages
- `parse_session_file()` - Main parsing logic
- `generate_summary()` - Create output JSON

**Important**: This file uses `uv run --script` for standalone operation. Do not add external imports.

### skills/observability-usage-collector/scripts/collect_usage.py

The main data collection script (~800 LOC). Key classes:

- `SessionData` - Parsed session information
- `SkillOrAgent` - Component definitions
- `Hook` - Hook definitions
- `InterruptedTool` - Tool interruption tracking

Key functions:

- `discover_skills()` - Find all available skills
- `discover_agents()` - Find all available agents
- `discover_hooks()` - Find all configured hooks
- `parse_session()` - Parse JSONL session files
- `find_matches()` - Match prompts to components

### agents/usage-insights-agent.md

The main analysis agent. Uses YAML frontmatter:

```yaml
---
name: usage-insights-agent
description: Analyzes Claude Code usage data...
model: sonnet
tools: Read, Bash, Grep, mcp__context7__resolve-library-id, mcp__context7__query-docs
---
```

## Testing

### Test Files

| File | Tests |
|------|-------|
| `test_session_parsing.py` | JSONL parsing, entry extraction |
| `test_outcome_detection.py` | Tool outcome classification |
| `test_workflow_stages.py` | Workflow stage inference |
| `test_find_matches.py` | Trigger matching algorithm |
| `test_yaml_frontmatter.py` | Skill/agent YAML parsing |
| `test_code_sync.py` | Verifies duplicated functions stay in sync |

### Adding Tests

1. Add test file in `tests/test_*.py`
2. Import functions from source:
   ```python
   from generate_session_summary import detect_outcome
   from collect_usage import find_matches
   ```
3. Use pytest fixtures from `conftest.py`

## Common Tasks

### Adding a New Skill

1. Create directory: `skills/new-skill-name/`
2. Add `SKILL.md` with YAML frontmatter:
   ```yaml
   ---
   name: new-skill-name
   description: Description with trigger phrases
   allowed-tools:
     - Bash
     - Read
   ---
   ```
3. Add any scripts in `scripts/` subdirectory
4. Update CHANGELOG.md

### Adding a New Agent

1. Create `agents/new-agent.md` with YAML frontmatter:
   ```yaml
   ---
   name: new-agent
   description: What this agent does
   model: sonnet
   tools: Tool1, Tool2
   ---
   ```
2. Document agent behavior in markdown body
3. Update CHANGELOG.md

### Modifying the Hook

1. Edit `hooks/generate_session_summary.py`
2. Run tests: `uv run pytest tests/test_session_parsing.py tests/test_outcome_detection.py`
3. Test manually with sample input
4. **If changing `detect_outcome()` or similar**: Also update `collect_usage.py` to keep in sync (see ADR-013)
5. Run `uv run pytest tests/test_code_sync.py` to verify sync

## Architecture Decision Records

Design decisions are documented in `docs/adrs/`. Key ADRs:

| ADR | Topic |
|-----|-------|
| ADR-001 | Trigger matching algorithm |
| ADR-013 | Code duplication strategy (sync vs shared) |
| ADR-019 | No ML dependencies policy |
| ADR-020 | Schema versioning |
| ADR-026 | JSONL schema stability |

To add a new ADR:
1. Create `docs/adrs/ADR-NNN-topic-name.md`
2. Update `docs/adrs/README.md` index

## Troubleshooting

### Tests fail with import errors

```bash
# Ensure you're in the observability directory
cd observability

# Reinstall dependencies
uv sync

# Run tests
uv run pytest tests/
```

### Hook not running

1. Check plugin is installed: `claude plugins list`
2. Verify plugin.json hook configuration
3. Check hook timeout (default 10s)
4. Test hook manually with sample input

### Collector script errors

```bash
# Check for valid session files
ls -la ~/.claude/projects/

# Run with verbose output
uv run skills/observability-usage-collector/scripts/collect_usage.py --verbose --sessions 5
```

## CI/CD

Currently no CI/CD pipeline configured. Tests should be run manually before pushing.

Recommended pre-push checks:
```bash
cd observability
uv run pytest tests/ -v
```

---

*Generated by document-project workflow on 2026-01-28*
