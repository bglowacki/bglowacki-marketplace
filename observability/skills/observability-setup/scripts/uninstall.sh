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
echo "=== Step 4: Remove endpoint config ==="
rm -f "$SKILL_DIR/config/endpoint.env"
echo "Removed endpoint configuration"

echo ""
echo "=== Step 5: Verify teardown ==="
echo "Checking for remaining Claude Code resources..."
kubectl get opentelemetrycollector -n observability 2>/dev/null | grep -i claude || echo "✓ No Claude Code collectors"
kubectl get svc -n observability 2>/dev/null | grep -i otel-collector-external || echo "✓ No OTEL external service"
kubectl get prometheusrule -n observability 2>/dev/null | grep -i claude-code || echo "✓ No Claude Code alert rules"
kubectl get servicemonitor -n observability 2>/dev/null | grep -i otel-collector || echo "✓ No OTEL service monitor"

echo ""
echo "=== Uninstall Complete ==="
