#!/bin/bash
# ASTRA Autonomous Discovery Daemon - Production Startup Script

# This script starts the autonomous discovery daemon in the background
# with proper logging and monitoring.

ASTRA_ROOT="/Users/gjw255/astrodata/SWARM/ASTRA-dev-main"
cd "$ASTRA_ROOT"

echo "Starting ASTRA Autonomous Discovery Daemon..."
echo "Logs: $ASTRA_ROOT/logs/autonomous_daemon.log"
echo "PID: $ASTRA_ROOT/data/autonomous_daemon.pid"

# Start daemon in background with nohup
nohup python3 astra_autonomous_daemon.py start >> logs/autonomous_daemon.log 2>&1 &
DAEMON_PID=$!

echo "Daemon started with PID: $DAEMON_PID"
echo "Monitor with: tail -f logs/autonomous_daemon.log"
echo "Check status: python3 astra_autonomous_daemon.py status"
echo "Stop daemon: python3 astra_autonomous_daemon.py stop"

# Wait a moment to verify startup
sleep 3

if ps -p $DAEMON_PID > /dev/null; then
    echo "✓ Daemon is running (PID $DAEMON_PID)"
else
    echo "✗ Daemon failed to start"
    exit 1
fi
