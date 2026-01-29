# Source Tree Analysis

## Directory Structure

```
bglowacki-marketplace/
├── .claude-plugin/                    # Marketplace registration
│   └── marketplace.json               # Plugin registry manifest
│
├── .claude/                           # Claude Code configuration
│   └── commands/                      # Project-level commands
│
├── docs/                              # Project documentation
│   ├── adrs/                          # Architecture Decision Records (76 ADRs)
│   │   ├── README.md                  # ADR index with status tracking
│   │   ├── ADR-001-*.md through ADR-076-*.md
│   │   └── REVIEW_NOTES.md            # Review session notes
│   ├── project-overview.md            # This project overview
│   ├── architecture.md                # System architecture
│   ├── source-tree-analysis.md        # This file
│   ├── development-guide.md           # Development setup
│   └── index.md                       # Master documentation index
│
├── observability/                     # Main plugin directory (v2.4.6)
│   ├── .claude-plugin/
│   │   └── plugin.json                # Plugin manifest (name, version, hooks)
│   │
│   ├── hooks/                         # Event-driven hooks
│   │   └── generate_session_summary.py  # ★ Stop hook - session parsing
│   │
│   ├── skills/                        # User-invocable skills
│   │   ├── observability-usage-collector/
│   │   │   ├── SKILL.md               # Skill definition
│   │   │   └── scripts/
│   │   │       └── collect_usage.py   # ★ Main data collection script (~800 LOC)
│   │   │
│   │   └── observability-workflow-optimizer/
│   │       └── SKILL.md               # Optimization skill definition
│   │
│   ├── agents/                        # AI agent definitions
│   │   ├── usage-insights-agent.md    # ★ Main analysis agent (~400 lines)
│   │   ├── usage-setup-analyzer.md    # Setup summary agent
│   │   ├── usage-pattern-detector.md  # Pattern detection agent
│   │   └── usage-finding-expander.md  # Finding expansion agent
│   │
│   ├── commands/                      # Shortcut commands
│   │   ├── collect-usage.md           # Data collection command
│   │   └── optimize-workflow.md       # Pipeline orchestration command
│   │
│   ├── tests/                         # pytest test suite
│   │   ├── conftest.py                # Fixtures and path setup
│   │   ├── test_session_parsing.py    # Session JSONL parsing tests
│   │   ├── test_outcome_detection.py  # Outcome classification tests
│   │   ├── test_workflow_stages.py    # Workflow stage inference tests
│   │   ├── test_find_matches.py       # Trigger matching tests
│   │   ├── test_yaml_frontmatter.py   # YAML parsing tests
│   │   └── test_code_sync.py          # Duplicated code sync tests
│   │
│   ├── docs/                          # Plugin-specific docs
│   │   └── plans/                     # Design documents (7 files)
│   │
│   ├── README.md                      # Plugin documentation
│   ├── CLAUDE.md                      # AI context for plugin
│   ├── CHANGELOG.md                   # Plugin version history
│   ├── SCHEMA_CHANGELOG.md            # Data schema versions
│   └── pyproject.toml                 # Python project config
│
├── _bmad/                             # BMAD workflow framework (external)
├── _bmad-output/                      # BMAD workflow outputs
│
├── README.md                          # Root project readme
├── CLAUDE.md                          # Root AI context
├── CHANGELOG.md                       # Root changelog
└── .gitignore                         # Git ignore rules
```

## Key Entry Points

| File | Purpose | Trigger |
|------|---------|---------|
| `observability/hooks/generate_session_summary.py` | Session parsing | Stop hook (automatic) |
| `observability/skills/observability-usage-collector/scripts/collect_usage.py` | Data collection | User invocation |
| `observability/agents/usage-insights-agent.md` | Data analysis | Agent spawn |

## Critical Directories

### `observability/hooks/`
Contains the Stop hook that runs automatically when Claude Code sessions end. Parses JSONL session files and generates summary JSON files.

### `observability/skills/`
User-invokable skills accessible via `/observability-usage-collector` and `/observability-workflow-optimizer`. Contains the main data collection script.

### `observability/agents/`
AI agent definitions in markdown format with YAML frontmatter. The `usage-insights-agent` is the primary analysis component.

### `docs/adrs/`
76 Architecture Decision Records documenting design decisions, methodologies, and rationale. Organized by category (methodology ADR-001-045, project ADR-046-076).

## Data Flow Paths

```
1. Session End:
   Claude Code → Stop hook → generate_session_summary.py → ~/.claude/session-summaries/

2. Analysis Pipeline:
   ~/.claude/projects/*.jsonl → collect_usage.py → JSON → usage-insights-agent → insights

3. Optimization:
   insights → workflow-optimizer skill → fix recommendations
```

## File Naming Conventions

| Pattern | Usage |
|---------|-------|
| `*.py` | Python scripts (hooks, collectors) |
| `SKILL.md` | Skill definitions |
| `*-agent.md` | Agent definitions |
| `ADR-NNN-*.md` | Architecture Decision Records |
| `test_*.py` | pytest test files |

## External Dependencies

- **Claude Code JSONL files**: `~/.claude/projects/{project}/*.jsonl`
- **Session summaries output**: `~/.claude/session-summaries/`
- **Plugin cache**: `~/.claude/plugins/cache/`

---

*Generated by document-project workflow on 2026-01-28*
