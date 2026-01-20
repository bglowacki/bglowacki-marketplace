#!/bin/bash
set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SKILL_DIR="$(dirname "$SCRIPT_DIR")"

echo "=== Observability Full Uninstall ==="

echo ""
echo "=== Step 1: Switch to orbstack context ==="
kubectl config use-context orbstack

echo ""
echo "=== Step 2: Delete NodePort services ==="
kubectl delete svc otel-collector-external prometheus-external -n observability --ignore-not-found=true

echo ""
echo "=== Step 3: Delete Prometheus Alerts ==="
kubectl delete -f "$SKILL_DIR/k8s/prometheus-alerts.yaml" --ignore-not-found=true 2>/dev/null || echo "Alert rules already removed"

echo ""
echo "=== Step 4: Uninstall OTEL Collector (Helm) ==="
helm uninstall otel-collector -n observability 2>/dev/null || echo "OTEL Collector helm release not found"

echo ""
echo "=== Step 5: Uninstall Prometheus Stack (Helm) ==="
helm uninstall kube-prometheus-stack -n observability 2>/dev/null || echo "Prometheus stack helm release not found"

echo ""
echo "=== Step 6: Delete observability namespace ==="
kubectl delete namespace observability --ignore-not-found=true

echo ""
echo "=== Step 7: Cleanup leftovers from previous versions ==="
# cert-manager (from v1.7.x)
kubectl delete -f https://github.com/cert-manager/cert-manager/releases/download/v1.14.4/cert-manager.yaml --ignore-not-found=true 2>/dev/null || true
kubectl delete namespace cert-manager --ignore-not-found=true 2>/dev/null || true
# OTEL Operator (from v1.7.x)
kubectl delete -f https://github.com/open-telemetry/opentelemetry-operator/releases/latest/download/opentelemetry-operator.yaml --ignore-not-found=true 2>/dev/null || true
kubectl delete namespace opentelemetry-operator-system --ignore-not-found=true 2>/dev/null || true
echo "Cleaned up any leftovers from previous versions"

echo ""
echo "=== Step 8: Remove endpoint config ==="
rm -f "$HOME/.claude/observability/endpoint.env"
echo "Removed endpoint configuration"

echo ""
echo "=== Step 9: Verify teardown ==="
kubectl get namespace observability 2>/dev/null && echo "⚠ observability still terminating..." || echo "✓ observability deleted"
kubectl get namespace cert-manager 2>/dev/null && echo "⚠ cert-manager still terminating..." || echo "✓ cert-manager deleted"

echo ""
echo "=== Full Uninstall Complete ==="
