#!/bin/bash
# Monitor discovery system after signal threading fix

echo "═══════════════════════════════════════════════════════════════"
echo "DISCOVERY SYSTEM MONITORING (Post-Fix)"
echo "═══════════════════════════════════════════════════════════════"
echo ""
echo "Expected Behavior:"
echo "  • Discovery cycles completing successfully"
echo "  • Genuine discoveries being produced (NOT zero)"
echo "  • No signal threading errors in logs"
echo "  • System running 24/7 without crashes"
echo ""
echo "═══════════════════════════════════════════════════════════════"

# Monitor for 5 minutes
echo "Monitoring for 5 minutes..."
echo ""

for i in {1..10}; do
    echo "Check $i/10:"

    # Check service status
    if launchctl list com.astra.discovery | grep -q "pid"; then
        echo "  ✅ Service running: $(launchctl list com.astra.discovery | awk '{print $1}')"
    else
        echo "  ❌ Service not running!"
    fi

    # Check for signal errors
    if tail -20 .astra_service.log | grep -q "signal only works in main thread"; then
        echo "  ❌ Signal threading error detected!"
    else
        echo "  ✅ No signal threading errors"
    fi

    # Check discovery count
    if [ -f ~/.astra_persistent/genuine_discoveries.json ]; then
        count=$(python3 -c "import json; print(len(json.load(open('$HOME/.astra_persistent/genuine_discoveries.json')).get('discoveries', [])))")
        echo "  📊 Discoveries: $count"
    else
        echo "  ⏳ Waiting for first discovery..."
    fi

    echo ""
    sleep 30
done

echo "═══════════════════════════════════════════════════════════════"
echo "Monitoring complete - Check discovery logs for detailed results"
echo "═══════════════════════════════════════════════════════════════"