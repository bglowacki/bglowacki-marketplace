---
name: observability-setup
description: Deploy OTEL observability stack to Kubernetes. Triggers on "setup observability", "install observability", "configure metrics".
---

# Setup Observability

Deploy the Claude Code observability stack to Kubernetes.

## How to Use This Skill

When this skill is loaded, you receive a **"Base directory for this skill:"** header above. Use that path to access the k8s manifests.

**Example:** If the header shows `Base directory for this skill: /path/to/skill`, then:
- Manifests are at `/path/to/skill/k8s/`
- Config will be at `/path/to/skill/config/`

## Steps

### 1. Verify the manifests exist

Substitute the base directory path into this command:
```bash
ls {base_directory}/k8s/
```

### 2. Setup Kubernetes context

```bash
kubectl config use-context orbstack
kubectl cluster-info
kubectl get namespace observability || kubectl create namespace observability
```

### 3. Deploy OTEL Collector

```bash
kubectl apply -f {base_directory}/k8s/otel-collector.yaml
kubectl wait --for=condition=available deployment/claude-code-collector-collector -n observability --timeout=60s
```

### 4. Deploy Prometheus Alerts

```bash
kubectl apply -f {base_directory}/k8s/prometheus-alerts.yaml
```

### 5. Configure endpoints

```bash
mkdir -p {base_directory}/config
cat > {base_directory}/config/endpoint.env << 'EOF'
OTEL_ENDPOINT=http://localhost:30418
PROMETHEUS_ENDPOINT=http://prometheus-kube-prometheus-prometheus.observability.svc.cluster.local:9090
EOF
```

### 6. Verify deployment

```bash
kubectl get pods -n observability -l app.kubernetes.io/name=claude-code-collector
kubectl get svc otel-collector-external -n observability
```

## After Setup

Tell the user:
- OTEL: `http://localhost:30418`
- Prometheus: `http://prometheus-kube-prometheus-prometheus.observability.svc.cluster.local:9090`
