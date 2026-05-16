#!/bin/bash
# ASTRA Autonomous Discovery - Continuous Startup Script
# This script ensures ASTRA discovery daemon starts on boot and restarts if it crashes

ASTRA_DIR="/Users/gjw255/astrodata/SWARM/ASTRA-dev-main"
PYTHON="/Library/Frameworks/Python.framework/Versions/3.14/bin/python3.14"
PID_FILE="$ASTRA_DIR/.astra_server.pid"
LOG_FILE="$ASTRA_DIR/logs/autonomous_daemon.log"

echo "=== ASTRA Autonomous Discovery Startup ==="
echo "Starting at $(date)"

# Kill any existing daemon
if [ -f "$PID_FILE" ]; then
    OLD_PID=$(cat "$PID_FILE")
    if ps -p $OLD_PID > /dev/null 2>&1; then
        echo "Killing existing daemon (PID: $OLD_PID)"
        kill $OLD_PID
        sleep 2
    fi
fi

# Wait for port to be free
sleep 1

# Start the daemon in background
cd "$ASTRA_DIR"
nohup $PYTHON astra_autonomous_daemon.py start >> "$LOG_FILE" 2>&1 &
NEW_PID=$!

# Save PID
echo $NEW_PID > "$PID_FILE"

echo "ASTRA daemon started with PID: $NEW_PID"
echo "Logs: $LOG_FILE"
echo "Monitor: tail -f $LOG_FILE"

# Verify it's running
sleep 3
if ps -p $NEW_PID > /dev/null 2>&1; then
    echo "✓ ASTRA is running autonomously"
    echo ""
    echo "Discovery cycles will run every 5 minutes"
    echo "Statistics will sync every 1 minute"
    echo "Full statistics every 1 hour"
else
    echo "✗ Failed to start ASTRA"
    exit 1
fi

exit 0
