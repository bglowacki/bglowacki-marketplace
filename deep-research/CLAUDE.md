# Deep Research Plugin

Multi-agent research system for Claude Code. Run `/research "your question"` to launch parallel research agents that search web, codebase, and MCP sources.

## Usage

```
/research "What are the trade-offs of event sourcing vs CRUD for a marketplace?"
/research "Compare Kubernetes vs ECS for our deployment"
/research "How does authentication work in our codebase?"
```

## Architecture

Based on Anthropic's multi-agent research system. The command acts as lead researcher, spawning parallel worker agents via Task tool. Workers search independently and return structured findings. Lead synthesizes into a report with citations.
