#!/bin/bash

PLUGIN_ROOT="${CLAUDE_PLUGIN_ROOT:-$(dirname "$(dirname "$0")")}"

echo "=== Observability Health Check ==="

# Check collector pod
echo "Checking collector pod..."
kubectl get pods -n observability -l app.kubernetes.io/name=claude-code-collector

# Check service
echo ""
echo "Checking service..."
kubectl get svc otel-collector-external -n observability

# Test OTLP endpoint
echo ""
echo "Testing OTLP endpoint..."
if curl -s -o /dev/null -w "%{http_code}" http://localhost:30418/v1/metrics -X POST -H "Content-Type: application/json" -d '{}' | grep -q "200\|204"; then
    echo "✓ OTLP endpoint responding"
else
    echo "✗ OTLP endpoint not responding"
fi

# Check alert-notifier
echo ""
echo "Checking alert-notifier..."
if pgrep -f alert-notifier.py > /dev/null; then
    echo "✓ Alert notifier running"
else
    echo "✗ Alert notifier not running (will start on next session)"
fi

# Check endpoint config
echo ""
echo "Checking endpoint config..."
if [ -f "$PLUGIN_ROOT/config/endpoint.env" ]; then
    echo "✓ Endpoint configured: $(cat "$PLUGIN_ROOT/config/endpoint.env")"
else
    echo "✗ Endpoint not configured"
fi

echo ""
echo "=== Health Check Complete ==="
