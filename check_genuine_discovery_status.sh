#!/bin/bash
# Check status of 24/7 genuine autonomous discovery system

echo "=== 24/7 GENUINE AUTONOMOUS DISCOVERY STATUS ==="
echo ""

# Check if process is running
if pgrep -f "run_24_7_genuine_discovery.py" > /dev/null; then
    echo "✅ Genuine discovery process: RUNNING"
    PID=$(pgrep -f 'run_24_7_genuine_discovery.py')
    echo "PID: $PID"
    echo "Uptime: $(ps -p $PID -o etime= | tr -d ' ')"
else
    echo "❌ Genuine discovery process: NOT RUNNING"
    echo "Start with: ./start_genuine_discovery.sh"
    exit 1
fi

echo ""
echo "=== GENUINE DISCOVERY ACTIVITY ==="

# Parse the discovery store
DISCOVERY_STORE="$HOME/.astra_persistent/genuine_discoveries.json"

if [ -f "$DISCOVERY_STORE" ]; then
    echo "Discovery store: $DISCOVERY_STORE"
    echo ""

    # Parse JSON with Python
    python3 - <<EOF
import json
from pathlib import Path

store_path = Path.home() / '.astra_persistent/genuine_discoveries.json'

try:
    with open(store_path) as f:
        store = json.load(f)

    stats = store.get('statistics', {})
    discoveries = store.get('discoveries', [])

    print(f"Discovery cycles completed: {stats.get('total_cycles', 0)}")
    print(f"✅ Genuine discoveries: {stats.get('total_discoveries', 0)}")
    print(f"Discovery success rate: {stats.get('discovery_rate', 0):.3f}")
    print(f"Failed attempts: {len(store.get('failed_attempts', []))}")

    if discoveries:
        print("")
        print("=== RECENT GENUINE DISCOVERIES ===")
        for d in discoveries[-3:]:
            print(f"🔬 {d.get('title', 'Untitled')}")
            print(f"   Type: {d.get('type', 'unknown')}")
            print(f"   Novelty: {d.get('novelty_level', 'unknown')}")
            print(f"   Probability: {d['validation']['probability_correct']:.2f}")
            print(f"   Novelty score: {d['validation']['novelty_score']:.2f}")
            print(f"   Domains: {', '.join(d.get('domains', []))}")
            print("")

except Exception as e:
    print(f"Error reading discovery store: {e}")
EOF

else
    echo "❌ Discovery store not found. System may not have completed first cycle yet."
fi

echo ""
echo "=== VALIDATION STANDARDS ==="
echo "All discoveries must meet:"
echo "  - Novelty score ≥ 0.3 (genuine novelty)"
echo "  - Probability correct ≥ 0.4 (reasonable confidence)"
echo "  - Testability requirement"
echo "  - Literature consistency check"
echo ""
echo "=== LOG FILES ==="
echo "Main log: ~/.astra_persistent/24_7_genuine_discovery.log"
echo "Discovery store: ~/.astra_persistent/genuine_discoveries.json"
echo ""
echo "View real-time: tail -f ~/.astra_persistent/24_7_genuine_discovery.log"