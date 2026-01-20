---
name: observability-setup
description: Deploy OTEL observability stack to Kubernetes. Triggers on "setup observability", "install observability", "configure metrics".
---

# Setup Observability

## CRITICAL: READ THIS FIRST

**The k8s manifests are in the PLUGIN directory, NOT the user's project.**

- Plugin location: `~/.claude/plugins/` (specifically `$CLAUDE_PLUGIN_ROOT/k8s/`)
- Do NOT search the current working directory
- Do NOT use Glob, Grep, or Search tools
- The files you need are NOT in the user's project

**Your FIRST action must be:** `echo $CLAUDE_PLUGIN_ROOT && ls $CLAUDE_PLUGIN_ROOT/k8s/`

## Step 1: Verify plugin path

Run this Bash command IMMEDIATELY (do not search first):

```
echo "Plugin root: $CLAUDE_PLUGIN_ROOT" && ls $CLAUDE_PLUGIN_ROOT/k8s/
```

This will show you the manifests: `otel-collector.yaml` and `prometheus-alerts.yaml`

## Step 2: Setup Kubernetes

```
kubectl config use-context orbstack
kubectl cluster-info
kubectl get namespace observability || kubectl create namespace observability
```

## Step 3: Deploy OTEL Collector

```
kubectl apply -f $CLAUDE_PLUGIN_ROOT/k8s/otel-collector.yaml
kubectl wait --for=condition=available deployment/claude-code-collector-collector -n observability --timeout=60s
```

## Step 4: Deploy Prometheus Alerts

```
kubectl apply -f $CLAUDE_PLUGIN_ROOT/k8s/prometheus-alerts.yaml
```

## Step 5: Configure endpoints

```
mkdir -p $CLAUDE_PLUGIN_ROOT/config
cat > $CLAUDE_PLUGIN_ROOT/config/endpoint.env << 'EOF'
OTEL_ENDPOINT=http://localhost:30418
PROMETHEUS_ENDPOINT=http://prometheus-kube-prometheus-prometheus.observability.svc.cluster.local:9090
EOF
cat $CLAUDE_PLUGIN_ROOT/config/endpoint.env
```

## Step 6: Verify

```
kubectl get pods -n observability -l app.kubernetes.io/name=claude-code-collector
kubectl get svc otel-collector-external -n observability
```

## Done

Report to user:
- OTEL endpoint: `http://localhost:30418`
- Prometheus: `http://prometheus-kube-prometheus-prometheus.observability.svc.cluster.local:9090`
