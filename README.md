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

- Kubernetes cluster (OrbStack recommended)
- `kubectl` configured
- `helm` installed
- `uv` package manager

#### Setup

1. **Deploy the observability stack:**

```
/observability-setup
```

This deploys and configures everything:
- OTEL Collector (receives metrics)
- Prometheus alerts (4 workflow alerts)
- Alertmanager config (routes to local webhook)
- Endpoint configuration (no manual env vars needed)

2. **Restart Claude Code** to load the plugin hooks.

> **Note:** `CLAUDE_CODE_ENABLE_TELEMETRY` is **not required** and can cause exit hangs. This plugin uses its own metrics pipeline.

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
- If `CLAUDE_CODE_ENABLE_TELEMETRY` is set to `"1"`, set it to `"0"` (not needed for this plugin)
- Ensure OTEL collector is running: `kubectl get pods -n observability`

**No metrics:**
- Verify `/setup-observability` was run
- Check endpoint config exists: `ls ~/.claude/plugins/cache/bglowacki-marketplace/observability/*/config/endpoint.env`

**No alerts:**
- Check alert-notifier is running: `pgrep -f alert-notifier`
- Check logs: `cat /tmp/alert-notifier.log`

#### Health Check

Run the health check to verify all components:

```bash
./observability/scripts/check-health.sh
```

#### Additional Skills

**Usage Analyzer** - Analyze session patterns and identify missed skill/agent opportunities:

```
/observability-usage-analyzer
```

Options: `--sessions N`, `--format table|dashboard|json`, `--quick-stats`

**Workflow Optimizer** - Suggests improvements to skills and workflows based on usage analysis:

```
/observability-workflow-optimizer
```

Run after usage-analyzer to get actionable improvement recommendations.

#### Uninstall

Remove the entire observability stack:

```
/observability-uninstall
```

This removes OTEL Collector, Prometheus, Grafana, cert-manager, and all related namespaces.
