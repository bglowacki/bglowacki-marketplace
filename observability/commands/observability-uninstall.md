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

**Uninstall complete!** The observability stack has been removed.

What was removed:
- OTEL Collector deployment and service
- Prometheus alert rules
- Endpoint configuration

What remains:
- The `observability` namespace (may contain other resources)
- Plugin hooks (will silently skip sending metrics when endpoint is unavailable)

To fully clean up: `kubectl delete namespace observability`
