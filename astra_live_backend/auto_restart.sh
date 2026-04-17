#!/bin/bash
# ASTRA Auto-Restart Script
# Ensures the ASTRA discovery engine keeps running continuously

LOG_DIR="/tmp"
LOG_FILE="${LOG_DIR}/astra_auto_restart.log"
ENGINE_PORT=8787
ENGINE_PID=""
MAX_RESTART_ATTEMPTS=100
RESTART_DELAY=5

log() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] $1" | tee -a "$LOG_FILE"
}

check_engine_running() {
    curl -s "http://localhost:${ENGINE_PORT}/api/state" > /dev/null 2>&1
    return $?
}

get_engine_pid() {
    ps aux | grep "python3 -m astra_live_backend.server" | grep -v grep | awk '{print $2}'
}

start_engine() {
    log "Starting ASTRA engine..."
    cd /Users/gjw255/astrodata/SWARM/ASTRA-dev-main

    # Start server in background
    nohup python3 -m astra_live_backend.server > "${LOG_DIR}/astra_server.log" 2>&1 &
    ENGINE_PID=$!

    # Wait for server to be ready
    local attempts=0
    local max_attempts=30

    while [ $attempts -lt $max_attempts ]; do
        if check_engine_running; then
            log "Engine started successfully (PID: $ENGINE_PID)"

            # Start the discovery engine
            sleep 3
            curl -s -X POST "http://localhost:${ENGINE_PORT}/api/engine/start" > /dev/null 2>&1
            log "Discovery engine started"

            return 0
        fi
        sleep 2
        attempts=$((attempts + 1))
    done

    log "ERROR: Failed to start engine after $max_attempts attempts"
    return 1
}

stop_engine() {
    local pid=$(get_engine_pid)
    if [ -n "$pid" ]; then
        log "Stopping engine (PID: $pid)..."
        kill $pid 2>/dev/null
        sleep 2

        # Force kill if still running
        if ps -p $pid > /dev/null 2>&1; then
            log "Force killing engine..."
            kill -9 $pid 2>/dev/null
        fi
    fi
}

restart_engine() {
    log "Restarting engine..."
    stop_engine
    sleep "$RESTART_DELAY"
    start_engine
}

monitor_engine() {
    local restart_count=0

    log "Starting ASTRA auto-restart monitor..."
    log "Monitoring engine on port ${ENGINE_PORT}"

    while [ $restart_count -lt $MAX_RESTART_ATTEMPTS ]; do
        # Check if engine is responding
        if ! check_engine_running; then
            log "WARNING: Engine not responding!"
            restart_engine
            restart_count=$((restart_count + 1))
            log "Restart count: $restart_count/$MAX_RESTART_ATTEMPTS"
        else
            # Engine is running - check cycle progress
            local cycle_info=$(curl -s "http://localhost:${ENGINE_PORT}/api/state" 2>/dev/null | python3 -c "import sys, json; data=json.load(sys.stdin); print(f\"Cycle: {data.get('cycle_count', 'N/A')}, Running: {data.get('running', False)}\")" 2>/dev/null)
            if [ -n "$cycle_info" ]; then
                log "Engine healthy - $cycle_info"
            fi
        fi

        # Sleep before next check (every 60 seconds)
        sleep 60
    done

    log "ERROR: Maximum restart attempts ($MAX_RESTART_ATTEMPTS) reached. Giving up."
    exit 1
}

# Main script
case "${1:-monitor}" in
    start)
        start_engine
        ;;
    stop)
        stop_engine
        ;;
    restart)
        restart_engine
        ;;
    monitor)
        monitor_engine
        ;;
    status)
        if check_engine_running; then
            echo "Engine is RUNNING on port ${ENGINE_PORT}"
            curl -s "http://localhost:${ENGINE_PORT}/api/state" 2>/dev/null | python3 -m json.tool 2>/dev/null || echo "State unavailable"
        else
            echo "Engine is NOT running"
            exit 1
        fi
        ;;
    *)
        echo "Usage: $0 {start|stop|restart|monitor|status}"
        exit 1
        ;;
esac
