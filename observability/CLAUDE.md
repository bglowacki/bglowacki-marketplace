# Observability Plugin

Claude Code plugin for session analysis and usage insights.

## Project Context

This is an **observability plugin development project**. The plugin provides:
- **usage-collector**: Collects Claude Code session history (data gathering only)
- **usage-insights-agent**: Analyzes collected data to identify patterns and missed opportunities
- **workflow-optimizer**: Suggests improvements to skills, agents, and workflows based on analysis

Plugin source files are in this directory (`observability/`).

## Architecture

The plugin uses JSONL-only architecture - no external infrastructure required:
- **Stop hook**: `hooks/generate_session_summary.py` - parses session JSONL, writes summaries
- **Collector**: `skills/observability-usage-collector/scripts/collect_usage.py` - aggregates data
- **Agent**: `agents/usage-insights-agent.md` - interprets data and provides insights

## Version Management

**Always bump the version in `.claude-plugin/plugin.json` before pushing.**

Use semantic versioning:
- PATCH (x.x.X): Bug fixes, minor improvements
- MINOR (x.X.0): New features, new skills
- MAJOR (X.0.0): Breaking changes
