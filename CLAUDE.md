# bglowacki-marketplace

Personal Claude Code plugins marketplace.

## Project Structure

```
.
├── observability/          # Session analysis plugin (v2.3.0)
├── .claude-plugin/         # Marketplace manifest
└── docs/adrs/              # Architecture Decision Records
```

## Plugin Development

Each plugin must have:
- `.claude-plugin/plugin.json` - Plugin manifest
- `CLAUDE.md` - Plugin-specific context
- Skills, agents, commands, hooks as needed

## Code Style

- Python: Use `uv run` for scripts, minimize external dependencies
- Markdown: YAML frontmatter for skills/agents/commands
- Keep scripts standalone (work without package installs)

## Common Commands

```bash
# Run tests
cd observability && uv run pytest tests/

# Test hook manually
echo '{"session_id":"test","cwd":"/tmp"}' | uv run observability/hooks/generate_session_summary.py

# Run collector
uv run observability/skills/observability-usage-collector/scripts/collect_usage.py --quick-stats --days 7
```

## ADR Status

See `docs/adrs/` for Architecture Decision Records. Use `docs/adrs/ADR-067-implementation-priority.md` for implementation order.
