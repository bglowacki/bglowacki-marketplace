#!/bin/bash
set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SKILL_DIR="$(dirname "$SCRIPT_DIR")"

echo "=== Observability Full Uninstall ==="

echo ""
echo "=== Step 1: Switch to orbstack context ==="
kubectl config use-context orbstack

echo ""
echo "=== Step 2: Delete OTEL Collector ==="
kubectl delete -f "$SKILL_DIR/k8s/otel-collector.yaml" --ignore-not-found=true

echo ""
echo "=== Step 3: Delete Prometheus Alerts ==="
kubectl delete -f "$SKILL_DIR/k8s/prometheus-alerts.yaml" --ignore-not-found=true

echo ""
echo "=== Step 4: Delete OTEL Operator ==="
kubectl delete -f https://github.com/open-telemetry/opentelemetry-operator/releases/latest/download/opentelemetry-operator.yaml --ignore-not-found=true 2>/dev/null || echo "OTEL Operator removal attempted"

echo ""
echo "=== Step 5: Delete cert-manager ==="
kubectl delete -f https://github.com/cert-manager/cert-manager/releases/download/v1.14.4/cert-manager.yaml --ignore-not-found=true 2>/dev/null || echo "cert-manager removal attempted"

echo ""
echo "=== Step 6: Delete Prometheus Stack (Helm) ==="
helm uninstall kube-prometheus-stack -n observability 2>/dev/null || echo "kube-prometheus-stack helm release not found"

echo ""
echo "=== Step 7: Delete namespaces ==="
kubectl delete namespace observability --ignore-not-found=true
kubectl delete namespace cert-manager --ignore-not-found=true
kubectl delete namespace opentelemetry-operator-system --ignore-not-found=true

echo ""
echo "=== Step 8: Remove endpoint config ==="
rm -f "$SKILL_DIR/config/endpoint.env"
echo "Removed endpoint configuration"

echo ""
echo "=== Step 9: Verify full teardown ==="
kubectl get namespace observability 2>/dev/null && echo "⚠ observability namespace still terminating" || echo "✓ observability deleted"
kubectl get namespace cert-manager 2>/dev/null && echo "⚠ cert-manager namespace still terminating" || echo "✓ cert-manager deleted"

echo ""
echo "=== Full Uninstall Complete ==="
