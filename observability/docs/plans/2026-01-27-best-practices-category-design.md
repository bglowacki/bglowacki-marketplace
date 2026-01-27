# Design: Best Practices Category for Usage Insights Agent

## Overview

Add a "Best Practices" category that validates user's Claude Code setup against official documentation guidelines, using Context7 MCP for up-to-date recommendations with hardcoded fallback.

## Category Definition

| Category | ID | Findings Included |
|----------|-----|-------------------|
| **Best Practices** | `best_practices` | CLAUDE.md structure issues, description quality, hook patterns, settings organization |

## Detection Conditions

| Check | Detection Logic | Doc Query (if Context7 available) |
|-------|-----------------|-----------------------------------|
| CLAUDE.md missing | No project-level file in `claude_md.files_found` | "CLAUDE.md purpose and structure" |
| CLAUDE.md sparse | Content < 500 chars or < 3 sections | "CLAUDE.md recommended sections" |
| Empty descriptions | Skill/agent description < 50 chars | "effective skill descriptions" |
| Missing triggers | Description has no quoted phrases | "skill trigger phrases" |
| Hook no timeout | Hook definition missing `timeout` field | "hook timeout best practices" |
| Large timeout | Hook timeout > 30000ms | "hook performance guidelines" |

## Context7 Integration

Tools needed: `mcp__context7__resolve-library-id`, `mcp__context7__query-docs`

Workflow:
1. Resolve library ID: `resolve-library-id(libraryName="claude-code", query="CLI documentation")`
2. Query specific topic: `query-docs(libraryId="...", query="CLAUDE.md best practices")`

## Fallback Behavior

If Context7 unavailable:
- Use hardcoded essentials
- Note: "Install Context7 MCP for detailed best practices from official docs"

Hardcoded essentials:
| Check | Recommendation |
|-------|----------------|
| CLAUDE.md missing | Create with project context, code style, testing commands |
| CLAUDE.md < 3 sections | Add: Project Context, Code Style, Testing |
| Empty skill description | Add description with trigger phrases in quotes |
| Hook no timeout | Add timeout (5000-30000ms recommended) |

## Output Format

```markdown
### {Issue Type}

**Why this matters:** {explanation}

**From docs:** {Context7 quote, or "Using built-in guidelines" if fallback}

| Issue | Your Setup | Recommendation |
|-------|------------|----------------|
| ... | ... | ... |
```

## Files to Modify

- `agents/usage-insights-agent.md` - Add category, detection logic, Context7 instructions
- `plugin.json` - Bump to 2.2.0
