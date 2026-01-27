# ADR-018: Add Project-Level CLAUDE.md

## Status
IMPLEMENTED (2026-01-27)

## Context
The project has `observability/CLAUDE.md` for the plugin subdirectory, but no root-level `CLAUDE.md` for the marketplace repository itself.

When working on the marketplace (not specifically on the observability plugin), there's no project-level configuration.

## Finding
**Missing**: `/Users/bartoszglowacki/Projects/bglowacki-marketplace/CLAUDE.md`

The `observability/CLAUDE.md` is specific to the observability plugin. The root directory needs its own configuration for:
- Overall project context (marketplace with multiple plugins)
- Coding standards for all plugins
- Common testing/build commands
- Plugin development patterns

## Decision
ACCEPTED - Created root `CLAUDE.md` with project structure, plugin development guidelines, code style, and common commands.

## Recommendation
Create root `CLAUDE.md` with:

```markdown
# bglowacki-marketplace

Personal Claude Code plugins marketplace.

## Project Structure
- `observability/` - Session analysis plugin
- Future plugins will be added as subdirectories

## Plugin Development
- Each plugin must have `.claude-plugin/plugin.json`
- Follow Claude Code plugin conventions
- Test hooks locally before committing

## Code Style
- Python: uv scripts, no external deps where possible
- Markdown: YAML frontmatter for skills/agents/commands
- Keep standalone scripts that work without package installs

## Common Commands
- Test hook: `echo '{"session_id":"test","cwd":"/tmp"}' | uv run observability/hooks/generate_session_summary.py`
- Run collector: `uv run observability/skills/observability-usage-collector/scripts/collect_usage.py --format json`
```

## Impact
- Claude Code has context when working at root level
- Consistent development patterns across plugins
- Documented testing approaches

## Review Notes
- Severity: Low (nice-to-have)
- Effort: Low
- Risk: None
