#!/bin/bash
set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SKILL_DIR="$(dirname "$SCRIPT_DIR")"

echo "=== Observability Full Setup ==="

echo ""
echo "=== Step 1: Switch to orbstack context ==="
kubectl config use-context orbstack
kubectl cluster-info

echo ""
echo "=== Step 2: Create namespace ==="
kubectl get namespace observability 2>/dev/null || kubectl create namespace observability

echo ""
echo "=== Step 3: Add Helm repos ==="
helm repo add prometheus-community https://prometheus-community.github.io/helm-charts 2>/dev/null || true
helm repo add open-telemetry https://open-telemetry.github.io/opentelemetry-helm-charts 2>/dev/null || true
helm repo update

echo ""
echo "=== Step 4: Install Prometheus Stack (Helm) ==="
if helm status kube-prometheus-stack -n observability &>/dev/null; then
    echo "Prometheus stack already installed"
else
    helm install kube-prometheus-stack prometheus-community/kube-prometheus-stack \
        --namespace observability \
        --set prometheus.prometheusSpec.enableRemoteWriteReceiver=true \
        --set grafana.enabled=true \
        --set alertmanager.alertmanagerSpec.alertmanagerConfigSelector.matchLabels.alertmanagerConfig=local-webhook \
        --set alertmanager.alertmanagerSpec.alertmanagerConfigNamespaceSelector.matchLabels.kubernetes\\.io/metadata\\.name=observability \
        --wait --timeout 5m
fi

echo ""
echo "=== Step 5: Install OTEL Collector (Helm) ==="
if helm status otel-collector -n observability &>/dev/null; then
    echo "OTEL Collector already installed"
else
    helm install otel-collector open-telemetry/opentelemetry-collector \
        --namespace observability \
        --set image.repository=otel/opentelemetry-collector-contrib \
        --set mode=deployment \
        --set replicaCount=1 \
        --set config.receivers.otlp.protocols.grpc.endpoint="0.0.0.0:4317" \
        --set config.receivers.otlp.protocols.http.endpoint="0.0.0.0:4318" \
        --set config.exporters.debug.verbosity=basic \
        --set config.exporters.prometheus.endpoint="0.0.0.0:8889" \
        --set config.service.pipelines.metrics.receivers="{otlp}" \
        --set config.service.pipelines.metrics.exporters="{prometheus,debug}" \
        --set ports.otlp.enabled=true \
        --set ports.otlp-http.enabled=true \
        --wait --timeout 2m
fi

echo ""
echo "=== Step 6: Create NodePort services for external access ==="
kubectl apply -f - <<EOF
apiVersion: v1
kind: Service
metadata:
  name: otel-collector-external
  namespace: observability
  labels:
    app: otel-collector-external
spec:
  type: NodePort
  selector:
    app.kubernetes.io/name: opentelemetry-collector
    app.kubernetes.io/instance: otel-collector
  ports:
    - name: otlp-grpc
      port: 4317
      targetPort: 4317
      nodePort: 30417
    - name: otlp-http
      port: 4318
      targetPort: 4318
      nodePort: 30418
    - name: prometheus
      port: 8889
      targetPort: 8889
      nodePort: 30889
---
apiVersion: v1
kind: Service
metadata:
  name: prometheus-external
  namespace: observability
spec:
  type: NodePort
  selector:
    app.kubernetes.io/name: prometheus
    prometheus: kube-prometheus-stack-prometheus
  ports:
    - name: http
      port: 9090
      targetPort: 9090
      nodePort: 30090
EOF

echo ""
echo "=== Step 7: Create ServiceMonitor for OTEL collector ==="
kubectl apply -f - <<EOF
apiVersion: monitoring.coreos.com/v1
kind: ServiceMonitor
metadata:
  name: otel-collector-metrics
  namespace: observability
  labels:
    release: kube-prometheus-stack
spec:
  selector:
    matchLabels:
      app: otel-collector-external
  namespaceSelector:
    matchNames:
      - observability
  endpoints:
    - port: prometheus
      interval: 5s
      path: /metrics
EOF

echo ""
echo "=== Step 8: Deploy Prometheus Alerts ==="
kubectl apply -f "$SKILL_DIR/k8s/prometheus-alerts.yaml"

echo ""
echo "=== Step 9: Configure endpoints ==="
# Write to global config (shared across all projects/versions)
GLOBAL_CONFIG_DIR="$HOME/.claude/observability"
mkdir -p "$GLOBAL_CONFIG_DIR"
cat > "$GLOBAL_CONFIG_DIR/endpoint.env" << 'EOF'
OTEL_ENDPOINT=http://localhost:30418
PROMETHEUS_ENDPOINT=http://localhost:30090
EOF
echo "Config written to: $GLOBAL_CONFIG_DIR/endpoint.env"
cat "$GLOBAL_CONFIG_DIR/endpoint.env"

echo ""
echo "=== Step 10: Verify deployment ==="
kubectl get pods -n observability
echo ""
kubectl get svc otel-collector-external prometheus-external -n observability
echo ""
kubectl get endpoints otel-collector-external prometheus-external -n observability

echo ""
echo "=== Setup Complete ==="
echo "OTEL HTTP: http://localhost:30418"
echo "OTEL gRPC: http://localhost:30417"
echo "Prometheus: http://localhost:30090"
echo "Grafana: kubectl port-forward svc/kube-prometheus-stack-grafana 3000:80 -n observability"
