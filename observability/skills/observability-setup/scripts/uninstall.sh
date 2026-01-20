#!/bin/bash
set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SKILL_DIR="$(dirname "$SCRIPT_DIR")"

echo "=== Observability Uninstall ==="

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
echo "=== Step 4: Delete namespace (optional) ==="
echo "Keeping observability namespace (may contain other resources)"
echo "To delete manually: kubectl delete namespace observability"

echo ""
echo "=== Step 5: Remove endpoint config ==="
rm -f "$SKILL_DIR/config/endpoint.env"
echo "Removed endpoint configuration"

echo ""
echo "=== Step 6: Verify teardown ==="
kubectl get pods -n observability -l app.kubernetes.io/name=claude-code-collector 2>/dev/null || echo "No collector pods found (good)"

echo ""
echo "=== Uninstall Complete ==="
echo "The observability stack has been removed."
echo "Plugin hooks will continue to run but will silently skip sending metrics."
