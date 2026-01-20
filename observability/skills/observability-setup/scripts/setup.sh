#!/bin/bash
set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SKILL_DIR="$(dirname "$SCRIPT_DIR")"

echo "=== Observability Full Setup ==="
echo "Skill directory: $SKILL_DIR"

# Verify manifests exist
if [ ! -d "$SKILL_DIR/k8s" ]; then
    echo "ERROR: k8s directory not found at $SKILL_DIR/k8s"
    exit 1
fi

echo ""
echo "=== Step 1: Switch to orbstack context ==="
kubectl config use-context orbstack
kubectl cluster-info

echo ""
echo "=== Step 2: Create namespace ==="
kubectl get namespace observability || kubectl create namespace observability

echo ""
echo "=== Step 3: Install Prometheus Stack (Helm) ==="
if helm status kube-prometheus-stack -n observability &>/dev/null; then
    echo "Prometheus stack already installed"
else
    helm repo add prometheus-community https://prometheus-community.github.io/helm-charts 2>/dev/null || true
    helm repo update
    helm install kube-prometheus-stack prometheus-community/kube-prometheus-stack \
        --namespace observability \
        --set prometheus.prometheusSpec.enableRemoteWriteReceiver=true \
        --set grafana.enabled=true \
        --wait --timeout 5m
fi

echo ""
echo "=== Step 4: Install cert-manager (required for OTEL Operator) ==="
if kubectl get namespace cert-manager &>/dev/null; then
    echo "cert-manager already installed"
else
    kubectl apply -f https://github.com/cert-manager/cert-manager/releases/download/v1.14.4/cert-manager.yaml
    echo "Waiting for cert-manager to be ready..."
    kubectl wait --for=condition=available deployment/cert-manager -n cert-manager --timeout=120s
    kubectl wait --for=condition=available deployment/cert-manager-webhook -n cert-manager --timeout=120s
    kubectl wait --for=condition=available deployment/cert-manager-cainjector -n cert-manager --timeout=120s
fi

echo ""
echo "=== Step 5: Install OTEL Operator ==="
if kubectl get crd opentelemetrycollectors.opentelemetry.io &>/dev/null; then
    echo "OTEL Operator already installed"
else
    kubectl apply -f https://github.com/open-telemetry/opentelemetry-operator/releases/latest/download/opentelemetry-operator.yaml
    echo "Waiting for OTEL operator to be ready..."
    kubectl wait --for=condition=available deployment/opentelemetry-operator-controller-manager -n opentelemetry-operator-system --timeout=120s 2>/dev/null || sleep 30
fi

echo ""
echo "=== Step 6: Deploy OTEL Collector ==="
kubectl apply -f "$SKILL_DIR/k8s/otel-collector.yaml"
echo "Waiting for collector..."
sleep 10
kubectl wait --for=condition=available deployment/claude-code-collector-collector -n observability --timeout=60s || echo "Collector may still be starting..."

echo ""
echo "=== Step 7: Deploy Prometheus Alerts ==="
kubectl apply -f "$SKILL_DIR/k8s/prometheus-alerts.yaml"

echo ""
echo "=== Step 8: Configure endpoints ==="
mkdir -p "$SKILL_DIR/config"
cat > "$SKILL_DIR/config/endpoint.env" << 'EOF'
OTEL_ENDPOINT=http://localhost:30418
PROMETHEUS_ENDPOINT=http://prometheus-kube-prometheus-prometheus.observability.svc.cluster.local:9090
EOF
cat "$SKILL_DIR/config/endpoint.env"

echo ""
echo "=== Step 9: Verify deployment ==="
kubectl get pods -n observability | head -20
kubectl get svc otel-collector-external -n observability

echo ""
echo "=== Setup Complete ==="
echo "OTEL endpoint: http://localhost:30418"
echo "Prometheus: http://prometheus-kube-prometheus-prometheus.observability.svc.cluster.local:9090"
echo "Grafana: http://localhost:3000 (admin/prom-operator)"
