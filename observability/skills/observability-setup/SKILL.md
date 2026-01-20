---
name: observability-setup
description: Deploy OTEL observability stack to Kubernetes. Triggers on "setup observability", "install observability", "configure metrics".
allowed-tools: Bash
---

# Setup Observability

Run the setup script from this skill's directory:

```bash
{base_directory}/scripts/setup.sh
```

Replace `{base_directory}` with the path shown in "Base directory for this skill:" above.

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
- Prometheus: `http://localhost:30090`
