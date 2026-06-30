#!/bin/bash
# Start 24/7 genuine autonomous discovery system v2.0

echo "🚀 Starting 24/7 GENUINE Autonomous Discovery System v2.0..."
echo ""

# Change to ASTRA directory
cd /Users/gjw255/astrodata/SWARM/ASTRA-dev-main

# Check if already running
if pgrep -f "run_24_7_genuine_discovery.py" > /dev/null; then
    echo "⚠️  Genuine discovery system is already running!"
    echo "PID: $(pgrep -f 'run_24_7_genuine_discovery.py')"
    echo ""
    echo "To check status, run: ./check_genuine_discovery_status.sh"
    exit 1
fi

# Stop any old discovery process
if pgrep -f "run_24_7_discovery.py" > /dev/null; then
    echo "Stopping old discovery system..."
    pkill -f run_24_7_discovery.py
    sleep 2
fi

# Start genuine discovery in background
nohup python3 run_24_7_genuine_discovery.py > /dev/null 2>&1 &
DISCOVERY_PID=$!

echo "✅ Genuine discovery system started!"
echo "PID: $DISCOVERY_PID"
echo ""
echo "🔬 The system will now conduct GENUINE scientific discovery 24/7."
echo "   Focus: Novel patterns, theoretical synthesis, testable hypotheses"
echo "   Validation: Rigorous novelty assessment, probability estimation"
echo "   Storage: Only discoveries meeting genuine research standards"
echo ""
echo "To check status:"
echo "  ./check_genuine_discovery_status.sh"
echo ""
echo "To view genuine discoveries:"
echo "  ./view_genuine_discoveries.sh"
echo ""
echo "To view logs:"
echo "  tail -f ~/.astra_persistent/24_7_genuine_discovery.log"
echo ""
echo "To stop:"
echo "  kill $DISCOVERY_PID"
echo "  or: pkill -f run_24_7_genuine_discovery.py"