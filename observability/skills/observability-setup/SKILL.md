---
name: observability-setup
description: Deploy OTEL observability stack to Kubernetes. Triggers on "setup observability", "install observability", "configure metrics".
---

# Setup Observability

Deploy the full observability stack for Claude Code metrics tracking.

## Prerequisites

- OrbStack or minikube running with Kubernetes
- kubectl configured and working
- Prometheus Operator installed (for alerts)
- OTEL Operator installed (for collector)

## Usage

Run this skill: `/setup`

## What This Deploys

1. **OTEL Collector** - Receives metrics via OTLP HTTP/gRPC
2. **Prometheus Rules** - 4 alerts for workflow issues
3. **Alertmanager Config** - Routes alerts to local webhook

## Setup Steps

Execute these steps in order:

### Step 1: Check Prerequisites

```bash
# Verify kubectl works
kubectl cluster-info

# Check for observability namespace
kubectl get namespace observability || kubectl create namespace observability

# Verify OTEL operator
kubectl get crd opentelemetrycollectors.opentelemetry.io

# Verify Prometheus operator
kubectl get crd prometheusrules.monitoring.coreos.com
```

### Step 2: Deploy OTEL Collector

```bash
kubectl apply -f ${CLAUDE_PLUGIN_ROOT}/k8s/otel-collector.yaml
```

Wait for collector to be ready:
```bash
kubectl wait --for=condition=available deployment/claude-code-collector-collector -n observability --timeout=60s
```

### Step 3: Deploy Prometheus Alerts

```bash
kubectl apply -f ${CLAUDE_PLUGIN_ROOT}/k8s/prometheus-alerts.yaml
```

### Step 4: Configure Alertmanager (Optional)

If you want macOS notifications for alerts:

```bash
kubectl apply -f ${CLAUDE_PLUGIN_ROOT}/k8s/alertmanager-config.yaml
```

### Step 5: Verify Deployment

```bash
# Check collector is running
kubectl get pods -n observability -l app.kubernetes.io/name=claude-code-collector

# Check service is exposed
kubectl get svc otel-collector-external -n observability

# Test connectivity (should return empty but no error)
curl -s http://localhost:30418/v1/metrics -X POST -d '{}' || echo "Connection OK"
```

### Step 6: Configure Endpoint (Auto)

The setup script will write the endpoint configuration:

```bash
mkdir -p ${CLAUDE_PLUGIN_ROOT}/config
echo "OTEL_ENDPOINT=http://localhost:30418" > ${CLAUDE_PLUGIN_ROOT}/config/endpoint.env
```

## Post-Setup

After setup, metrics are automatically collected:
- **PostToolUse** - Every tool invocation with outcome tracking
- **PreCompact** - Context compaction events
- **Stop** - Session summary with notification

Session summaries saved to: `~/.claude/session-summaries/`

## Troubleshooting

### Collector not receiving metrics

1. Check collector logs: `kubectl logs -n observability -l app.kubernetes.io/name=claude-code-collector`
2. Verify NodePort service: `kubectl get svc otel-collector-external -n observability`
3. Test endpoint: `curl http://localhost:30418/v1/metrics`

### Alerts not firing

1. Verify PrometheusRule: `kubectl get prometheusrule -n observability`
2. Check Prometheus targets: Port-forward to Prometheus UI and check targets

### No macOS notifications

1. Check alert-notifier running: `pgrep -f alert-notifier`
2. Check logs: `cat /tmp/alert-notifier.log`
3. Verify Alertmanager can reach host: Check `host.docker.internal` resolution

## Teardown

To remove everything:

```bash
kubectl delete -f ${CLAUDE_PLUGIN_ROOT}/k8s/otel-collector.yaml
kubectl delete -f ${CLAUDE_PLUGIN_ROOT}/k8s/prometheus-alerts.yaml
kubectl delete -f ${CLAUDE_PLUGIN_ROOT}/k8s/alertmanager-config.yaml
```
