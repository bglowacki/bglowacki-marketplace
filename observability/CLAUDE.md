# Observability Plugin

Claude Code plugin for OTEL metrics, alerts, and session analysis.

## Project Context

This is an **observability plugin development project**. The plugin provides:
- **usage-collector**: Collects Claude Code session history and metrics (data gathering only)
- **usage-insights-agent**: Analyzes collected data to identify patterns and missed opportunities
- **workflow-optimizer**: Suggests improvements to skills, agents, and workflows based on analysis

Plugin source files are in this directory (`observability/`).

## Version Management

**Always bump the version in `.claude-plugin/plugin.json` before pushing.**

Use semantic versioning:
- PATCH (x.x.X): Bug fixes, minor improvements
- MINOR (x.X.0): New features, new skills
- MAJOR (X.0.0): Breaking changes
