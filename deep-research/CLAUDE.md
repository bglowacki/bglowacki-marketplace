# Deep Research Plugin

Multi-agent research system for Claude Code. Run `/research "your question"` to launch parallel research agents that search web, codebase, and MCP sources.

## Usage

```
/research "What are the trade-offs of event sourcing vs CRUD for a marketplace?"
/research "Compare Kubernetes vs ECS for our deployment"
/research "How does authentication work in our codebase?"
```

## Setup

For the best experience, allow `WebFetch` and `WebSearch` in your project or global settings so research agents can fetch any URL without permission prompts:

```json
// .claude/settings.json (project) or ~/.claude/settings.json (global)
{
  "permissions": {
    "allow": ["WebFetch", "WebSearch"]
  }
}
```

## Architecture

Based on Anthropic's multi-agent research system. The command acts as lead researcher, spawning parallel worker agents via Task tool. Workers search independently and return structured findings. Lead synthesizes into a report with citations.
