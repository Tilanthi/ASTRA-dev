#!/bin/bash
# Check REAL status of 24/7 autonomous discovery system from logs

echo "=== 24/7 AUTONOMOUS DISCOVERY STATUS ==="
echo ""

# Check if process is running
if pgrep -f "run_24_7_discovery.py" > /dev/null; then
    echo "✅ Discovery process: RUNNING"
    PID=$(pgrep -f 'run_24_7_discovery.py')
    echo "PID: $PID"
    echo "Uptime: $(ps -p $PID -o etime= | tr -d ' ')"
else
    echo "❌ Discovery process: NOT RUNNING"
    echo "Start with: ./start_discovery.sh"
    exit 1
fi

echo ""
echo "=== DISCOVERY ACTIVITY FROM LOGS ==="

# Parse the log file for discovery activity
LOG_FILE="$HOME/.astra_persistent/24_7_discovery.log"

if [ -f "$LOG_FILE" ]; then
    echo "Log file: $LOG_FILE"
    echo ""

    # Count completed cycles
    CYCLES=$(grep -c "Discovery cycle.*completed" "$LOG_FILE" 2>/dev/null || echo 0)
    echo "Discovery cycles completed: $CYCLES"

    # Count processed discoveries
    PROCESSED=$(grep -c "Discovery made:" "$LOG_FILE" 2>/dev/null || echo 0)
    echo "Discoveries processed: $PROCESSED"

    echo ""
    echo "=== RECENT DISCOVERIES ==="

    # Show recent discoveries
    grep "Discovery made:" "$LOG_FILE" | tail -3 | while read -r line; do
        echo "🔬 $(echo "$line" | sed -E 's/.*result.*: (.+)}/\1/' | cut -c1-100)..."
    done

    echo ""
    echo "=== PROCESS STATUS ==="

    # Show startup info
    grep "24/7 DISCOVERY SYSTEM NOW RUNNING" "$LOG_FILE" | tail -1

    echo ""
    echo "=== NEXT DISCOVERY CYCLE ==="
    LAST_CYCLE=$(grep "Discovery cycle.*completed" "$LOG_FILE" | tail -1)
    if [ -n "$LAST_CYCLE" ]; then
        echo "Last cycle: $(echo "$LAST_CYCLE" | cut -d' ' -f1-2)"
        echo "Next cycle: ~30 minutes after last cycle (1800s interval)"
    else
        echo "Waiting for first cycle to complete..."
    fi

else
    echo "❌ Log file not found: $LOG_FILE"
fi

echo ""
echo "=== MONITORING ==="
echo "Watch real-time: tail -f ~/.astra_persistent/24_7_discovery.log"
echo "Process monitor: ps aux | grep run_24_7_discovery"