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
echo "=== Step 5: Delete Prometheus Stack (Helm) ==="
helm uninstall prometheus -n observability 2>/dev/null || echo "Prometheus helm release not found"
helm uninstall prometheus-kube-prometheus -n observability 2>/dev/null || echo "kube-prometheus helm release not found"
helm uninstall kube-prometheus-stack -n observability 2>/dev/null || echo "kube-prometheus-stack helm release not found"

echo ""
echo "=== Step 6: Delete observability namespace ==="
kubectl delete namespace observability --ignore-not-found=true

echo ""
echo "=== Step 7: Remove endpoint config ==="
rm -f "$SKILL_DIR/config/endpoint.env"
echo "Removed endpoint configuration"

echo ""
echo "=== Step 8: Verify full teardown ==="
kubectl get namespace observability 2>/dev/null && echo "⚠ Namespace still exists (may take time to terminate)" || echo "✓ Namespace deleted"

echo ""
echo "=== Full Uninstall Complete ==="
