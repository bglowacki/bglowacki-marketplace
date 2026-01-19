# Observability Plugin

Claude Code plugin for OTEL-based metrics, alerts, and session summaries.

## Features

- Tracks tool invocations, outcomes, and workflow stages
- Monitors skills, agents, and context efficiency
- Generates session summaries saved to `~/.claude/session-summaries/`
- Sends macOS notifications for alerts
- Integrates with Kubernetes observability stack (Prometheus, Alertmanager)

## Prerequisites

- Kubernetes cluster with:
  - OpenTelemetry Operator
  - Prometheus Operator
- `uv` package manager
- `kubectl` configured for your cluster

## Quick Start

Run the setup skill:

```
/observability:setup-observability
```

See [skills/setup-observability/SKILL.md](skills/setup-observability/SKILL.md) for detailed setup instructions.

## Environment Variables

- `CLAUDE_CODE_ENABLE_TELEMETRY=1` - Required for metrics collection
- `OTEL_EXPORTER_OTLP_ENDPOINT` - Set automatically during setup

## Architecture

```
SessionStart → start-services.sh → alert-notifier.py (background)
PostToolUse  → send_event_otel.py → OTEL Collector → Prometheus
PreCompact   → send_event_otel.py → OTEL Collector → Prometheus
Stop         → send_event_otel.py → Session summary + cleanup
```
