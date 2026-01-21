---
name: observability-setup
description: Deploy full observability stack (Prometheus, Grafana, OTEL) to Kubernetes
allowed-tools: Bash
---

# Setup Observability

Run the setup script to deploy the full observability stack:

!`${CLAUDE_PLUGIN_ROOT}/skills/observability-setup/scripts/setup.sh`

## Summary for User

After the script completes, tell the user:

**Setup complete!** Full observability stack deployed:
- ✓ Prometheus (metrics storage)
- ✓ Grafana (dashboards)
- ✓ OTEL Operator
- ✓ OTEL Collector (receives telemetry from plugin)
- ✓ Alert rules configured

**No additional configuration needed** - plugin hooks automatically send telemetry.

Endpoints:
- OTEL: `http://localhost:30418`
- Prometheus: `http://localhost:30090`
- Grafana: `http://localhost:3000` (admin/prom-operator)

## Verify Setup

After deployment, run the test script to verify events flow correctly:

!`${CLAUDE_PLUGIN_ROOT}/skills/observability-setup/scripts/test-event.sh`

This sends a test event through the hook and verifies it appears in Prometheus.
