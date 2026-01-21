#!/bin/bash
# Test script that sends a test event through the hook and verifies it in Prometheus

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
# Navigate: scripts -> observability-setup -> skills -> observability -> hooks
PLUGIN_ROOT="$(dirname "$(dirname "$(dirname "$SCRIPT_DIR")")")"
HOOK_SCRIPT="$PLUGIN_ROOT/hooks/send_event_otel.py"

echo "=== Observability Test Event ==="
echo ""

# Check if setup is complete
if [ ! -f "$HOME/.claude/observability/endpoint.env" ]; then
    echo "ERROR: Observability not configured. Run /observability-setup first."
    exit 1
fi

source "$HOME/.claude/observability/endpoint.env"
echo "OTEL Endpoint: $OTEL_ENDPOINT"
echo "Prometheus Endpoint: $PROMETHEUS_ENDPOINT"

echo ""
echo "=== Step 1: Send test event via hook ==="
TEST_SESSION_ID="test-$(date +%s)"

# Send a PostToolUse event (simulates a Bash tool execution)
echo '{
  "session_id": "'"$TEST_SESSION_ID"'",
  "tool_name": "Bash",
  "tool_input": {"command": "echo test"},
  "tool_result": "test\nExit code: 0",
  "cwd": "/tmp/test-project"
}' | "$HOOK_SCRIPT" --event-type PostToolUse --source-app test

echo "Test event sent with session_id: $TEST_SESSION_ID"

echo ""
echo "=== Step 2: Wait for metrics export and scrape (15s) ==="
echo "(OTEL exports every 5s, Prometheus scrapes every 15s)"
sleep 15

echo ""
echo "=== Step 3: Query Prometheus for test metrics ==="

# Query for tool invocations with retry
for i in 1 2 3; do
    echo "Attempt $i: Querying claude_code_hook_tool_invocations_total{source_app=\"test\"}..."
    RESULT=$(curl -s "${PROMETHEUS_ENDPOINT}/api/v1/query" \
      --data-urlencode 'query=claude_code_hook_tool_invocations_total{source_app="test"}' \
      | python3 -c "import sys,json; d=json.load(sys.stdin); r=d.get('data',{}).get('result',[]); print(f'Found {len(r)} test event(s)!' if r else 'Not found yet')" 2>/dev/null || echo "Query failed")

    echo "Result: $RESULT"
    if [[ "$RESULT" == *"Found"* ]]; then
        break
    fi
    [ $i -lt 3 ] && echo "Waiting 5s before retry..." && sleep 5
done

echo ""
echo "=== Step 4: Show available Claude Code metrics ==="
curl -s "${PROMETHEUS_ENDPOINT}/api/v1/label/__name__/values" \
  | python3 -c "import sys,json; names=[n for n in json.load(sys.stdin).get('data',[]) if 'claude_code' in n]; print('\n'.join(names) if names else 'No claude_code metrics found yet')" 2>/dev/null || echo "Could not query metric names"

echo ""
echo "=== Test Complete ==="
echo ""
echo "If metrics show 'Not found yet', they may need more time to propagate."
echo "Check Prometheus UI: $PROMETHEUS_ENDPOINT"
echo "Query: claude_code_hook_tool_invocations_total"
