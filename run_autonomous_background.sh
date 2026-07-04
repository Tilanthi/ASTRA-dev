#!/bin/bash
###############################################################################
# ASTRA Autonomous Discovery Background Runner
#
# This script starts the ASTRA discovery system in the background with
# automatic restart on failure and comprehensive logging.
#
# Usage:
#   ./run_autonomous_background.sh [start|stop|restart|status]
#
# Features:
# - Automatic background execution
# - Process management (start/stop/restart/status)
# - Automatic restart on failure
# - Comprehensive logging
# - PID file management
#
# Version: 2.0.0-Genuine
# Date: 2026-07-01
###############################################################################

# Configuration
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PYTHON_SCRIPT="$SCRIPT_DIR/start_autonomous_discovery.py"
LOG_FILE="$SCRIPT_DIR/.astra_autonomous.log"
PID_FILE="$SCRIPT_DIR/.astra_autonomous.pid"
AUTO_RESTART=true
RESTART_DELAY=10

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

###############################################################################
# Helper Functions
###############################################################################

log() {
    echo -e "${BLUE}[$(date '+%Y-%m-%d %H:%M:%S')]${NC} $1"
}

log_success() {
    echo -e "${GREEN}[$(date '+%Y-%m-%d %H:%M:%S')]${NC} ✅ $1"
}

log_warning() {
    echo -e "${YELLOW}[$(date '+%Y-%m-%d %H:%M:%S')]${NC} ⚠️  $1"
}

log_error() {
    echo -e "${RED}[$(date '+%Y-%m-%d %H:%M:%S')]${NC} ❌ $1"
}

###############################################################################
# Process Management Functions
###############################################################################

check_running() {
    if [ -f "$PID_FILE" ]; then
        PID=$(cat "$PID_FILE")
        if ps -p "$PID" > /dev/null 2>&1; then
            return 0  # Running
        else
            rm -f "$PID_FILE"
            return 1  # Not running (stale PID file)
        fi
    fi
    return 1  # Not running
}

start_system() {
    log "Starting ASTRA Autonomous Discovery System..."

    if check_running; then
        log_warning "System is already running (PID: $(cat $PID_FILE))"
        return 1
    fi

    # Check if Python script exists
    if [ ! -f "$PYTHON_SCRIPT" ]; then
        log_error "Python script not found: $PYTHON_SCRIPT"
        return 1
    fi

    # Start the system in background
    log "Launching discovery system..."
    nohup python3 "$PYTHON_SCRIPT" >> "$LOG_FILE" 2>&1 &
    PID=$!

    # Save PID
    echo $PID > "$PID_FILE"

    # Wait a moment to check if it started successfully
    sleep 3

    if ps -p $PID > /dev/null 2>&1; then
        log_success "ASTRA Discovery System started successfully (PID: $PID)"
        log "Log file: $LOG_FILE"
        log "Monitor with: tail -f $LOG_FILE"
        return 0
    else
        log_error "Failed to start discovery system"
        rm -f "$PID_FILE"
        return 1
    fi
}

stop_system() {
    log "Stopping ASTRA Autonomous Discovery System..."

    if ! check_running; then
        log_warning "System is not running"
        rm -f "$PID_FILE"
        return 0
    fi

    PID=$(cat "$PID_FILE")
    log "Stopping process $PID..."

    # Send SIGTERM for graceful shutdown
    kill -TERM $PID 2>/dev/null

    # Wait for graceful shutdown
    for i in {1..30}; do
        if ! ps -p $PID > /dev/null 2>&1; then
            log_success "System stopped gracefully"
            rm -f "$PID_FILE"
            return 0
        fi
        sleep 1
    done

    # Force kill if still running
    log_warning "System did not stop gracefully - forcing shutdown"
    kill -KILL $PID 2>/dev/null
    rm -f "$PID_FILE"
    log_success "System stopped"
    return 0
}

restart_system() {
    log "Restarting ASTRA Autonomous Discovery System..."
    stop_system
    sleep 2
    start_system
}

status_system() {
    echo ""
    echo "=========================================="
    echo "ASTRA Autonomous Discovery System Status"
    echo "=========================================="

    if check_running; then
        PID=$(cat "$PID_FILE")
        echo "Status: ${GREEN}RUNNING${NC}"
        echo "PID: $PID"
        echo "Log File: $LOG_FILE"

        # Show recent log entries
        if [ -f "$LOG_FILE" ]; then
            echo ""
            echo "Recent Activity:"
            tail -10 "$LOG_FILE"
        fi
    else
        echo "Status: ${RED}NOT RUNNING${NC}"
        rm -f "$PID_FILE"
    fi

    echo "=========================================="
    echo ""
}

###############################################################################
# Background Loop with Auto-Restart
###############################################################################

background_loop() {
    log "Starting ASTRA with auto-restart enabled..."

    while true; do
        # Start the system
        if ! check_running; then
            log "Starting discovery system..."
            python3 "$PYTHON_SCRIPT"
            EXIT_CODE=$?

            log "Discovery system exited with code: $EXIT_CODE"

            if [ "$AUTO_RESTART" = true ] && [ $EXIT_CODE -ne 0 ]; then
                log "System will restart in ${RESTART_DELAY} seconds..."
                sleep $RESTART_DELAY
            else
                log "System exited normally - not restarting"
                break
            fi
        else
            log "System already running - waiting..."
            sleep 60
        fi
    done
}

###############################################################################
# Command Line Interface
###############################################################################

case "${1:-start}" in
    start)
        start_system
        ;;

    stop)
        stop_system
        ;;

    restart)
        restart_system
        ;;

    status)
        status_system
        ;;

    background)
        background_loop
        ;;

    *)
        echo "Usage: $0 {start|stop|restart|status|background}"
        echo ""
        echo "Commands:"
        echo "  start      - Start the discovery system in background"
        echo "  stop       - Stop the discovery system"
        echo "  restart    - Restart the discovery system"
        echo "  status     - Show system status and recent logs"
        echo "  background - Run with auto-restart on failure"
        echo ""
        echo "Examples:"
        echo "  $0 start          # Start the system"
        echo "  $0 status         # Check status"
        echo "  $0 stop           # Stop the system"
        echo "  $0 background      # Run with auto-restart"
        exit 1
        ;;
esac

exit $?