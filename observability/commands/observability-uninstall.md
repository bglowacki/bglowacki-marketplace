---
name: observability-uninstall
description: Remove OTEL observability stack from Kubernetes
allowed-tools: Bash
---

# Uninstall Observability

Run the uninstall script to remove the observability stack:

!`${CLAUDE_PLUGIN_ROOT}/skills/observability-setup/scripts/uninstall.sh`

## Summary for User

After the script completes, tell the user:

**Uninstall complete!** Claude Code observability resources removed:
- ✓ OTEL Collector (`claude-code-collector`)
- ✓ External service (`otel-collector-external`)
- ✓ Prometheus alert rules (`claude-code-alerts`)
- ✓ Service monitor
- ✓ Endpoint configuration

**Shared infrastructure NOT removed** (used by other services):
- Prometheus/Grafana stack
- Alertmanager
- OpenTelemetry Operator
- Base kube-prometheus rules

Plugin hooks will silently skip sending metrics when endpoint is unavailable.
