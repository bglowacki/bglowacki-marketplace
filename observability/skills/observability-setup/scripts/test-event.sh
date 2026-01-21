#!/bin/bash
# Test script that sends a test event through the hook and verifies it in Prometheus

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
# Navigate: scripts -> observability-setup -> skills -> observability -> hooks
PLUGIN_ROOT="$(dirname "$(dirname "$(dirname "$SCRIPT_DIR")")")"
HOOK_SCRIPT="$PLUGIN_ROOT/hooks/send_event_otel.py"

# Progress spinner
spin() {
    local pid=$1
    local delay=0.2
    local spinstr='⠋⠙⠹⠸⠼⠴⠦⠧⠇⠏'
    while kill -0 "$pid" 2>/dev/null; do
        for (( i=0; i<${#spinstr}; i++ )); do
            printf "\r  %s %s" "${spinstr:$i:1}" "$2"
            sleep $delay
        done
    done
    printf "\r  ✓ %s\n" "$2"
}

# Progress with countdown
wait_with_progress() {
    local seconds=$1
    local message=$2
    for ((i=seconds; i>0; i--)); do
        printf "\r  ⏳ %s (%ds remaining)  " "$message" "$i"
        sleep 1
    done
    printf "\r  ✓ %s                    \n" "$message"
}

echo ""
echo "╔══════════════════════════════════════════╗"
echo "║     Observability Setup Verification     ║"
echo "╚══════════════════════════════════════════╝"
echo ""

# Check if setup is complete
if [ ! -f "$HOME/.claude/observability/endpoint.env" ]; then
    echo "  ✗ ERROR: Observability not configured."
    echo "    Run /observability-setup first."
    exit 1
fi

source "$HOME/.claude/observability/endpoint.env"
echo "  ℹ OTEL Endpoint: $OTEL_ENDPOINT"
echo "  ℹ Prometheus Endpoint: $PROMETHEUS_ENDPOINT"
echo ""

# Step 1: Send test event
echo "━━━ Step 1/3: Send Test Event ━━━"
TEST_SESSION_ID="test-$(date +%s)"

echo '{
  "session_id": "'"$TEST_SESSION_ID"'",
  "tool_name": "Bash",
  "tool_input": {"command": "echo test"},
  "tool_result": "test\nExit code: 0",
  "cwd": "/tmp/test-project"
}' | "$HOOK_SCRIPT" --event-type PostToolUse --source-app test 2>/dev/null

echo "  ✓ Test event sent (session: ${TEST_SESSION_ID:0:12}...)"
echo ""

# Step 2: Wait for propagation
echo "━━━ Step 2/3: Wait for Metrics Propagation ━━━"
echo "  (OTEL exports every 5s, Prometheus scrapes every 5s)"
wait_with_progress 10 "Waiting for initial metrics export"
echo ""

# Step 3: Verify metrics with retries
echo "━━━ Step 3/3: Verify Metrics in Prometheus ━━━"

MAX_RETRIES=12
RETRY_DELAY=5
FOUND=false

for ((attempt=1; attempt<=MAX_RETRIES; attempt++)); do
    printf "  [%d/%d] Querying metrics..." "$attempt" "$MAX_RETRIES"

    RESULT=$(curl -s "${PROMETHEUS_ENDPOINT}/api/v1/query" \
      --data-urlencode 'query=claude_code_hook_tool_invocations_total{source_app="test"}' 2>/dev/null \
      | python3 -c "import sys,json; d=json.load(sys.stdin); r=d.get('data',{}).get('result',[]); print(len(r))" 2>/dev/null || echo "0")

    if [[ "$RESULT" -gt 0 ]]; then
        printf "\r  ✓ [%d/%d] Found %s test event(s) in Prometheus!     \n" "$attempt" "$MAX_RETRIES" "$RESULT"
        FOUND=true
        break
    else
        printf "\r  ⏳ [%d/%d] Not found yet" "$attempt" "$MAX_RETRIES"
        if [[ $attempt -lt $MAX_RETRIES ]]; then
            printf ", retrying in %ds...\n" "$RETRY_DELAY"
            sleep $RETRY_DELAY
        else
            printf "\n"
        fi
    fi
done

echo ""

# Show available metrics
echo "━━━ Available Claude Code Metrics ━━━"
METRICS=$(curl -s "${PROMETHEUS_ENDPOINT}/api/v1/label/__name__/values" 2>/dev/null \
  | python3 -c "import sys,json; names=[n for n in json.load(sys.stdin).get('data',[]) if 'claude_code' in n]; print('\n'.join(names))" 2>/dev/null)

if [[ -n "$METRICS" ]]; then
    echo "$METRICS" | while read -r metric; do
        echo "  • $metric"
    done
else
    echo "  (no claude_code metrics found yet)"
fi

echo ""
echo "╔══════════════════════════════════════════╗"
if $FOUND; then
    echo "║  ✓ VERIFICATION PASSED                   ║"
    echo "╠══════════════════════════════════════════╣"
    echo "║  Events flow: Hook → OTEL → Prometheus   ║"
else
    echo "║  ⚠ VERIFICATION PENDING                  ║"
    echo "╠══════════════════════════════════════════╣"
    echo "║  Metrics may still be propagating.       ║"
    echo "║  Check manually at:                      ║"
    echo "║  $PROMETHEUS_ENDPOINT"
fi
echo "╚══════════════════════════════════════════╝"
