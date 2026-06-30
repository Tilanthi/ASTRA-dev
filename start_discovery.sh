#!/bin/bash
# Start 24/7 autonomous discovery system

echo "🚀 Starting 24/7 Autonomous Discovery System..."
echo ""

# Change to ASTRA directory
cd /Users/gjw255/astrodata/SWARM/ASTRA-dev-main

# Check if already running
if pgrep -f "run_24_7_discovery.py" > /dev/null; then
    echo "⚠️  Discovery system is already running!"
    echo "PID: $(pgrep -f 'run_24_7_discovery.py')"
    echo ""
    echo "To check status, run: ./check_discovery_status.sh"
    exit 1
fi

# Start discovery in background
nohup python3 run_24_7_discovery.py > /dev/null 2>&1 &
DISCOVERY_PID=$!

echo "✅ Discovery system started!"
echo "PID: $DISCOVERY_PID"
echo ""
echo "The system will now run continuous autonomous discovery 24/7."
echo ""
echo "To check status:"
echo "  ./check_discovery_status.sh"
echo ""
echo "To view logs:"
echo "  tail -f ~/.astra_persistent/24_7_discovery.log"
echo ""
echo "To stop:"
echo "  kill $DISCOVERY_PID"
echo "  or: pkill -f run_24_7_discovery.py"