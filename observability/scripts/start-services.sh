#!/bin/bash
# Start observability services on session start

PLUGIN_ROOT="${CLAUDE_PLUGIN_ROOT:-$(dirname "$(dirname "$0")")}"

# Kill any existing alert-notifier
pkill -f alert-notifier.py 2>/dev/null

# Start alert-notifier in background
nohup uv run "$PLUGIN_ROOT/scripts/alert-notifier.py" > /tmp/alert-notifier.log 2>&1 &

exit 0
