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

## Testing the Setup

After deployment completes, run the test script to verify events flow correctly:

```bash
{base_directory}/scripts/test-event.sh
```

This script:
1. Sends a test event through the actual hook (`send_event_otel.py`)
2. Waits for metrics to propagate
3. Queries Prometheus to verify the event was received
4. Lists all available `claude_code_*` metrics

Expected output should show:
- "Found!" for the test metric query
- List of `claude_code_*` metrics in Prometheus
