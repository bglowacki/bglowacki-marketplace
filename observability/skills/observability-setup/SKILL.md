---
name: observability-setup
description: Deploy OTEL observability stack to Kubernetes. Triggers on "setup observability", "install observability", "configure metrics".
---

# Setup Observability

You are deploying the Claude Code observability stack. The k8s manifests are already in this plugin at `$CLAUDE_PLUGIN_ROOT/k8s/`.

## Instructions

**DO NOT search for files. DO NOT use Glob or Grep. The paths are known.**

Execute these steps using the Bash tool:

### Step 1: Verify environment

Use the Bash tool to run:
- `echo "Plugin root: $CLAUDE_PLUGIN_ROOT"` - shows where manifests are
- `ls $CLAUDE_PLUGIN_ROOT/k8s/` - lists available manifests
- `kubectl config use-context orbstack` - switch to local k8s
- `kubectl cluster-info` - verify connection
- `kubectl get namespace observability || kubectl create namespace observability`

### Step 2: Deploy OTEL Collector

Use the Bash tool to run:
- `kubectl apply -f $CLAUDE_PLUGIN_ROOT/k8s/otel-collector.yaml`
- `kubectl wait --for=condition=available deployment/claude-code-collector-collector -n observability --timeout=60s`

### Step 3: Deploy Prometheus Alerts

Use the Bash tool to run:
- `kubectl apply -f $CLAUDE_PLUGIN_ROOT/k8s/prometheus-alerts.yaml`

### Step 4: Configure endpoints

Use the Bash tool to run:
- `mkdir -p $CLAUDE_PLUGIN_ROOT/config`
- Create endpoint.env with this content:
  ```
  OTEL_ENDPOINT=http://localhost:30418
  PROMETHEUS_ENDPOINT=http://prometheus-kube-prometheus-prometheus.observability.svc.cluster.local:9090
  ```
- `cat $CLAUDE_PLUGIN_ROOT/config/endpoint.env` to verify

### Step 5: Verify deployment

Use the Bash tool to run:
- `kubectl get pods -n observability -l app.kubernetes.io/name=claude-code-collector`
- `kubectl get svc otel-collector-external -n observability`

## After Setup

Report these endpoints to the user:
- OTEL: `http://localhost:30418`
- Prometheus: `http://prometheus-kube-prometheus-prometheus.observability.svc.cluster.local:9090`
- Session summaries: `~/.claude/session-summaries/`
