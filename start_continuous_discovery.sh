#!/bin/bash
# ASTRA Continuous Discovery Startup Script
# This script starts the ASTRA discovery watchdog for continuous operation

echo "🚀 Starting ASTRA Continuous Discovery System..."
echo "================================================"
echo "📅 Date: $(date)"
echo ""
echo "This will start ASTRA in continuous operation mode:"
echo "  ✅ Auto-restart if discovery process crashes"
echo "  ✅ Continuous monitoring and health checks"
echo "  ✅ Proper pause/resume for user tasks"
echo "  ✅ Graceful shutdown handling"
echo ""
echo "To stop: ./stop_continuous_discovery.sh"
echo "================================================"
echo ""

# Start the watchdog
python3 astra_core/scientific_discovery/astra_watchdog.py start

echo ""
echo "ASTRA Continuous Discovery has stopped"
