#!/bin/bash
# Start the continuous discovery memory monitor

cd /Users/gjw255/astrodata/SWARM/ASTRA-dev-main

# Kill any existing monitor
pkill -f monitor_discoveries_continuous.py

# Start new monitor in background
nohup python3 monitor_discoveries_continuous.py > logs/monitor.log 2>&1 &
MONITOR_PID=$!
echo $MONITOR_PID > logs/monitor.pid

echo "Continuous discovery memory monitor started"
echo "PID: $MONITOR_PID"
echo "Log: logs/monitor.log"

# Wait a moment and check if it's running
sleep 3
if ps -p $MONITOR_PID > /dev/null; then
    echo "✓ Monitor is running"
    echo ""
    echo "To stop the monitor:"
    echo "  kill $MONITOR_PID"
    echo "  or: pkill -f monitor_discoveries_continuous.py"
else
    echo "✗ Monitor failed to start - check logs/monitor.log"
    exit 1
fi
