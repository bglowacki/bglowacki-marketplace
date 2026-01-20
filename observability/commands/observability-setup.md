---
name: observability-setup
description: Deploy OTEL observability stack to Kubernetes
allowed-tools: Bash
---

# Setup Observability

Run the setup script to deploy the observability stack:

!`${CLAUDE_PLUGIN_ROOT}/skills/observability-setup/scripts/setup.sh`

The script will:
1. Switch to orbstack Kubernetes context
2. Create observability namespace
3. Deploy OTEL Collector
4. Deploy Prometheus Alerts
5. Configure endpoints
6. Verify deployment

## After Setup

Endpoints:
- OTEL: `http://localhost:30418`
- Prometheus: `http://prometheus-kube-prometheus-prometheus.observability.svc.cluster.local:9090`
