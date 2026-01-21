# Observability Plugin

Claude Code plugin for OTEL-based metrics, alerts, and session summaries.

## Features

- Tracks tool invocations, outcomes, and workflow stages
- Monitors skills, agents, and context efficiency
- Generates session summaries saved to `~/.claude/session-summaries/`
- Sends macOS notifications for alerts
- Integrates with Kubernetes observability stack (Prometheus, Alertmanager)

## Prerequisites

- Kubernetes cluster (OrbStack recommended)
- `kubectl` configured
- `helm` installed
- `uv` package manager

## Quick Start

Run the setup skill:

```
/observability-setup
```

See [skills/observability-setup/SKILL.md](skills/observability-setup/SKILL.md) for detailed setup instructions.

## Available Skills

| Skill | Description |
|-------|-------------|
| `/observability-setup` | Deploy full observability stack to Kubernetes |
| `/observability-uninstall` | Remove entire stack (OTEL, Prometheus, Grafana, cert-manager) |
| `/observability-usage-collector` | Collect session data and metrics for analysis |
| `/observability-workflow-optimizer` | Suggest improvements based on usage analysis |

## Configuration

All configuration is handled automatically by `/observability-setup`. No manual environment variables needed.

> **Note:** `CLAUDE_CODE_ENABLE_TELEMETRY` is **not required** and can cause exit hangs. This plugin uses its own metrics pipeline.

## Utility Scripts

| Script | Description |
|--------|-------------|
| `scripts/check-health.sh` | Verify all components are running |
| `scripts/teardown.sh` | Stop local services |

## Architecture

```
SessionStart → start-services.sh → alert-notifier.py (background)
PostToolUse  → send_event_otel.py → OTEL Collector → Prometheus
PreCompact   → send_event_otel.py → OTEL Collector → Prometheus
Stop         → send_event_otel.py → Session summary + cleanup
```
