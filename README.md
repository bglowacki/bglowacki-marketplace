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

After installing, run `/setup-observability` to deploy the K8s stack.

**Features:**
- Tracks tool outcomes (success/failure)
- Workflow stage inference (brainstorm -> plan -> implement -> test -> review -> commit)
- Context efficiency (compaction metrics)
- Session summaries with macOS notifications
- Prometheus alerts for workflow issues
