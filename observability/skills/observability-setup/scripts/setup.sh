#!/bin/bash
set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SKILL_DIR="$(dirname "$SCRIPT_DIR")"

echo "=== Observability Setup ==="
echo "Skill directory: $SKILL_DIR"
echo "K8s manifests: $SKILL_DIR/k8s/"

# Verify manifests exist
if [ ! -d "$SKILL_DIR/k8s" ]; then
    echo "ERROR: k8s directory not found at $SKILL_DIR/k8s"
    exit 1
fi

echo ""
echo "=== Step 1: Listing manifests ==="
ls -la "$SKILL_DIR/k8s/"

echo ""
echo "=== Step 2: Switch to orbstack context ==="
kubectl config use-context orbstack

echo ""
echo "=== Step 3: Verify cluster ==="
kubectl cluster-info

echo ""
echo "=== Step 4: Create namespace ==="
kubectl get namespace observability || kubectl create namespace observability

echo ""
echo "=== Step 5: Deploy OTEL Collector ==="
kubectl apply -f "$SKILL_DIR/k8s/otel-collector.yaml"
kubectl wait --for=condition=available deployment/claude-code-collector-collector -n observability --timeout=60s

echo ""
echo "=== Step 6: Deploy Prometheus Alerts ==="
kubectl apply -f "$SKILL_DIR/k8s/prometheus-alerts.yaml"

echo ""
echo "=== Step 7: Configure endpoints ==="
mkdir -p "$SKILL_DIR/config"
cat > "$SKILL_DIR/config/endpoint.env" << 'EOF'
OTEL_ENDPOINT=http://localhost:30418
PROMETHEUS_ENDPOINT=http://prometheus-kube-prometheus-prometheus.observability.svc.cluster.local:9090
EOF
cat "$SKILL_DIR/config/endpoint.env"

echo ""
echo "=== Step 8: Verify deployment ==="
kubectl get pods -n observability -l app.kubernetes.io/name=claude-code-collector
kubectl get svc otel-collector-external -n observability

echo ""
echo "=== Setup Complete ==="
echo "OTEL endpoint: http://localhost:30418"
echo "Prometheus: http://prometheus-kube-prometheus-prometheus.observability.svc.cluster.local:9090"
