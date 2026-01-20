---
name: observability-setup
description: Deploy OTEL observability stack to Kubernetes
allowed-tools: Bash
---

# Setup Observability

Run the setup script to deploy the observability stack:

!`${CLAUDE_PLUGIN_ROOT}/skills/observability-setup/scripts/setup.sh`

## Summary for User

After the script completes, tell the user:

**Setup complete!** The observability stack is now running.

**No additional configuration needed** - this plugin automatically sends telemetry via hooks:
- `PostToolUse` → sends tool metrics after each tool call
- `PreCompact` → sends context metrics before compaction
- `Stop` → generates session summary

Endpoints (for reference only):
- OTEL: `http://localhost:30418`
- Prometheus: `http://prometheus-kube-prometheus-prometheus.observability.svc.cluster.local:9090`
