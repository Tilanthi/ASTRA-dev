#!/bin/bash
# ASTRA Auto-Start Script
# Ensures ASTRA server is running and opens the dashboard

ASTRA_DIR="/Users/gjw255/astrodata/SWARM/ASTRA-dev-main"
cd "$ASTRA_DIR" || exit 1

# Check if server is already running
if pgrep -f "astra_live_backend.server" > /dev/null; then
    echo "ASTRA server is already running"
else
    echo "Starting ASTRA server..."
    # Start server in background with logging
    nohup python3 -m astra_live_backend.server > /tmp/astra_server.log 2>&1 &

    # Wait for server to start
    echo "Waiting for server to initialize..."
    sleep 3

    # Check if server started successfully
    if pgrep -f "astra_live_backend.server" > /dev/null; then
        echo "ASTRA server started successfully"
    else
        echo "Failed to start ASTRA server. Check /tmp/astra_server.log"
        exit 1
    fi
fi

# Open dashboard in browser
echo "Opening ASTRA dashboard..."
open http://localhost:8787

echo "ASTRA is ready! Dashboard: http://localhost:8787"
