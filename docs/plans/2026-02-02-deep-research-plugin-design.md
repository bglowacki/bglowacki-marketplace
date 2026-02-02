# Deep Research Plugin Design

## Overview

Claude Code plugin that replicates Anthropic's multi-agent research system. Provides a `/research` command that orchestrates parallel subagents for web, codebase, and MCP-based research, then synthesizes findings with citations.

Based on: https://www.anthropic.com/engineering/multi-agent-research-system

## Architecture

The `/research "query"` command transforms the current session into a lead researcher.

### Flow

1. **Analysis** — Lead classifies query complexity (simple/comparative/deep)
2. **Planning** — Decomposes into non-overlapping research angles
3. **Parallel research** — Spawns N subagents via Task tool in single message
4. **Synthesis** — Merges findings, identifies gaps, optional second wave
5. **Citation** — Haiku agent verifies sources and formats references

### Scaling Rules

| Query Type | Subagents | Tool Calls Each |
|---|---|---|
| Simple fact | 0 (lead handles) | 3-10 |
| Comparison | 2-4 | 10-15 |
| Deep research | 5-10 | 15+ |

### Components

| Component | Model | Role |
|---|---|---|
| `commands/research.md` | Inherits (opus) | Lead researcher |
| `agents/research-worker.md` | sonnet | Parallel searcher |
| `agents/citation-verifier.md` | haiku | Source checker |

### Research Sources

Workers access: WebSearch, WebFetch, Read, Grep, Glob, and any inherited MCP tools.

## Heuristics

### Lead Researcher
- Decompose before searching
- Assess complexity honestly — don't over-invest
- Assign distinct, non-overlapping angles
- Evaluate gaps after first wave

### Workers
- Start broad, narrow progressively
- Prefer authoritative sources over SEO content
- Multiple searches per angle (3-5 with different phrasings)
- Return structured findings: claim, source URL, confidence, caveats
- Use codebase and MCP tools when relevant

## Error Handling

| Failure | Response |
|---|---|
| No search results | Retry with rephrased query (3x), then report gap |
| WebFetch blocked | Skip URL, move to next |
| Empty subagent result | Note gap, targeted follow-up if critical |
| All agents fail | Lead researches directly (graceful degradation) |
| MCP unavailable | Skip silently, use web + codebase |

## Constraints

- Max 10 subagents per wave
- Max 2 waves (initial + follow-up)
- No persistent state
- No file writes — inline output only
- No scripts, no dependencies — pure prompt engineering
