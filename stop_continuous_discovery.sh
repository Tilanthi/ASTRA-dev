#!/bin/bash
# ASTRA Continuous Discovery Stop Script
# This script stops the ASTRA discovery watchdog and continuous operation

echo "🛑 Stopping ASTRA Continuous Discovery System..."
echo "================================================"
echo "📅 Date: $(date)"
echo ""
echo "This will stop ASTRA continuous operation and:"
echo "  ✅ Stop the discovery process gracefully"
echo "  ✅ Stop the watchdog monitoring"
echo "  ✅ Mark ASTRA as inactive"
echo "  ✅ Prevent auto-restart"
echo ""
echo "To restart: ./start_continuous_discovery.sh"
echo "================================================"
echo ""

# Stop the watchdog
python3 astra_core/scientific_discovery/astra_watchdog.py stop

echo ""
echo "ASTRA Continuous Discovery has been stopped"
echo "💡 You can restart anytime with: ./start_continuous_discovery.sh"
