# bglowacki-marketplace

Personal Claude Code plugins.

## Installation

```bash
# Add marketplace
claude plugins add-marketplace github:bglowacki/bglowacki-marketplace

# Install observability plugin
claude plugins install observability@bglowacki-marketplace
```

## Plugins

### observability

OTEL metrics, alerts, and session summaries for Claude Code.

**Features:**
- Tracks tool outcomes (success/failure)
- Workflow stage inference (brainstorm → plan → implement → test → review → commit)
- Context efficiency (compaction metrics)
- Session summaries with macOS notifications
- Prometheus alerts for workflow issues

#### Prerequisites

- OrbStack or minikube with Kubernetes
- kubectl configured
- OTEL Operator installed
- Prometheus Operator installed (for alerts)

#### Setup

1. **Add OTEL settings to `~/.claude/settings.json`:**

```json
{
  "env": {
    "CLAUDE_CODE_ENABLE_TELEMETRY": "1",
    "OTEL_METRICS_EXPORTER": "otlp",
    "OTEL_LOGS_EXPORTER": "otlp",
    "OTEL_EXPORTER_OTLP_PROTOCOL": "grpc",
    "OTEL_EXPORTER_OTLP_ENDPOINT": "http://otel-collector-external.observability.svc.cluster.local:4317",
    "OTEL_EXPORTER_OTLP_HTTP_ENDPOINT": "http://otel-collector-external.observability.svc.cluster.local:4318",
    "OTEL_METRIC_EXPORT_INTERVAL": "30000",
    "OTEL_METRICS_INCLUDE_SESSION_ID": "true",
    "OTEL_RESOURCE_ATTRIBUTES": "team.name=your-team,engineer.name=your-name"
  }
}
```

> **Note:** `CLAUDE_CODE_ENABLE_TELEMETRY` enables Claude Code's built-in telemetry via gRPC. Ensure your K8s OTEL collector is running before enabling, otherwise exit may hang while trying to flush metrics.

2. **Deploy the K8s observability stack:**

```
/observability:setup-observability
```

This deploys:
- OTEL Collector (receives metrics)
- Prometheus alerts (4 workflow alerts)
- Alertmanager config (routes to local webhook)

3. **Restart Claude Code** to load the plugin hooks.

#### How It Works

The plugin is inactive until you run `/setup-observability`. This creates a config file that enables the hooks.

**Hooks:**
- `PostToolUse` - Tracks every tool invocation with outcome detection
- `PreCompact` - Tracks context compaction events
- `Stop` - Generates session summary with macOS notification
- `SessionStart` - Starts alert webhook server

**Session summaries** are saved to `~/.claude/session-summaries/`

#### Alerts

| Alert | Trigger |
|-------|---------|
| ClaudeCodeRepeatedFailures | 3+ failures in 5 minutes |
| ClaudeCodeStuckInImplementation | 10+ implement stages without test/commit |
| ClaudeCodeContextChurn | 5+ compactions in 1 hour |
| ClaudeCodeEditFailures | 2+ Edit failures in 10 minutes |

#### Troubleshooting

**Exit hangs:**
- Ensure OTEL collector is running: `kubectl get pods -n observability`
- If K8s is down, temporarily set `CLAUDE_CODE_ENABLE_TELEMETRY` to `"0"`

**No metrics:**
- Verify `/setup-observability` was run
- Check endpoint config exists: `ls ~/.claude/plugins/cache/bglowacki-marketplace/observability/*/config/endpoint.env`

**No alerts:**
- Check alert-notifier is running: `pgrep -f alert-notifier`
- Check logs: `cat /tmp/alert-notifier.log`
