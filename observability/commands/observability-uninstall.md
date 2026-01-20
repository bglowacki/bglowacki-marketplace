---
name: observability-uninstall
description: Remove entire observability stack from Kubernetes (OTEL, Prometheus, Grafana, cert-manager)
allowed-tools: Bash
---

# Uninstall Observability

Run the uninstall script to remove the entire observability stack:

!`${CLAUDE_PLUGIN_ROOT}/skills/observability-setup/scripts/uninstall.sh`

## Summary for User

After the script completes, tell the user:

**Full uninstall complete!** Everything removed:
- ✓ OTEL Collector and service
- ✓ Prometheus alert rules
- ✓ OpenTelemetry Operator
- ✓ cert-manager
- ✓ Prometheus/Grafana stack (Helm release)
- ✓ All namespaces (observability, cert-manager, opentelemetry-operator-system)
- ✓ Endpoint configuration

Namespace deletions may take a moment to fully terminate.

Plugin hooks will silently skip when no endpoint is configured.
