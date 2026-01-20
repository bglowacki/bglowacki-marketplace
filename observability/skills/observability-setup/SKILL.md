---
name: observability-setup
description: Deploy OTEL observability stack to Kubernetes. Triggers on "setup observability", "install observability", "configure metrics".
---

# Setup Observability

**CRITICAL: Execute these bash commands directly. Do NOT search for files - the manifests are at `$CLAUDE_PLUGIN_ROOT/k8s/`.**

## Step 1: Verify plugin path and prerequisites

Run these commands NOW:

```bash
# Show plugin path (where k8s manifests are)
echo "Plugin root: $CLAUDE_PLUGIN_ROOT"
ls $CLAUDE_PLUGIN_ROOT/k8s/

# Switch to orbstack context
kubectl config use-context orbstack

# Verify kubectl works
kubectl cluster-info

# Check/create observability namespace
kubectl get namespace observability || kubectl create namespace observability
```

## Step 2: Deploy OTEL Collector

```bash
kubectl apply -f $CLAUDE_PLUGIN_ROOT/k8s/otel-collector.yaml
kubectl wait --for=condition=available deployment/claude-code-collector-collector -n observability --timeout=60s
```

## Step 3: Deploy Prometheus Alerts

```bash
kubectl apply -f $CLAUDE_PLUGIN_ROOT/k8s/prometheus-alerts.yaml
```

## Step 4: Configure endpoints

```bash
mkdir -p $CLAUDE_PLUGIN_ROOT/config
cat > $CLAUDE_PLUGIN_ROOT/config/endpoint.env << 'EOF'
OTEL_ENDPOINT=http://localhost:30418
PROMETHEUS_ENDPOINT=http://prometheus-kube-prometheus-prometheus.observability.svc.cluster.local:9090
EOF
cat $CLAUDE_PLUGIN_ROOT/config/endpoint.env
```

## Step 5: Verify deployment

```bash
kubectl get pods -n observability -l app.kubernetes.io/name=claude-code-collector
kubectl get svc otel-collector-external -n observability
```

## Done

After setup:
- Metrics push to OTEL at `http://localhost:30418`
- Query Prometheus at `http://prometheus-kube-prometheus-prometheus.observability.svc.cluster.local:9090`
- Session summaries saved to `~/.claude/session-summaries/`
