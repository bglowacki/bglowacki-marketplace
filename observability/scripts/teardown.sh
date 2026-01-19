#!/bin/bash

PLUGIN_ROOT="${CLAUDE_PLUGIN_ROOT:-$(dirname "$(dirname "$0")")}"
K8S_DIR="$PLUGIN_ROOT/k8s"

echo "=== Tearing Down Observability Stack ==="

# Delete resources
kubectl delete -f "$K8S_DIR/otel-collector.yaml" --ignore-not-found
kubectl delete -f "$K8S_DIR/prometheus-alerts.yaml" --ignore-not-found
kubectl delete -f "$K8S_DIR/alertmanager-config.yaml" --ignore-not-found

# Remove config
rm -f "$PLUGIN_ROOT/config/endpoint.env"

# Stop alert-notifier
pkill -f alert-notifier.py 2>/dev/null || true

echo "=== Teardown Complete ==="
