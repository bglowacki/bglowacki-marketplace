#!/bin/bash
set -e

PLUGIN_ROOT="${CLAUDE_PLUGIN_ROOT:-$(dirname "$(dirname "$0")")}"
K8S_DIR="$PLUGIN_ROOT/k8s"
CONFIG_DIR="$PLUGIN_ROOT/config"

echo "=== Claude Code Observability Setup ==="

# Check prerequisites
echo "Checking prerequisites..."
if ! command -v kubectl &> /dev/null; then
    echo "ERROR: kubectl not found. Install kubectl or OrbStack first."
    exit 1
fi

if ! kubectl cluster-info &> /dev/null; then
    echo "ERROR: Cannot connect to Kubernetes. Start OrbStack/minikube first."
    exit 1
fi

# Create namespace if needed
echo "Ensuring observability namespace..."
kubectl get namespace observability &> /dev/null || kubectl create namespace observability

# Check for OTEL operator
if ! kubectl get crd opentelemetrycollectors.opentelemetry.io &> /dev/null; then
    echo "WARNING: OTEL operator not found. Installing..."
    kubectl apply -f https://github.com/open-telemetry/opentelemetry-operator/releases/latest/download/opentelemetry-operator.yaml
    echo "Waiting for OTEL operator..."
    sleep 30
fi

# Deploy OTEL collector
echo "Deploying OTEL collector..."
kubectl apply -f "$K8S_DIR/otel-collector.yaml"

# Wait for collector
echo "Waiting for collector to be ready..."
kubectl wait --for=condition=available deployment/claude-code-collector-collector -n observability --timeout=120s || true

# Deploy Prometheus alerts (if Prometheus operator exists)
if kubectl get crd prometheusrules.monitoring.coreos.com &> /dev/null; then
    echo "Deploying Prometheus alerts..."
    kubectl apply -f "$K8S_DIR/prometheus-alerts.yaml"
else
    echo "WARNING: Prometheus operator not found. Skipping alert rules."
fi

# Deploy Alertmanager config
echo "Deploying Alertmanager config..."
kubectl apply -f "$K8S_DIR/alertmanager-config.yaml"

# Configure endpoint
echo "Configuring endpoint..."
mkdir -p "$CONFIG_DIR"
echo "OTEL_ENDPOINT=http://localhost:30418" > "$CONFIG_DIR/endpoint.env"

# Verify
echo ""
echo "=== Setup Complete ==="
echo "OTEL endpoint: http://localhost:30418"
echo "Prometheus metrics: http://localhost:30889/metrics"
echo ""
echo "Run /setup-observability check-health to verify connectivity."
