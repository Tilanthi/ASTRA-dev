#!/bin/bash
# View genuine discoveries from 24/7 autonomous discovery

echo "=== GENUINE ASTROPHYSICS DISCOVERIES ==="
echo ""

DISCOVERY_STORE="$HOME/.astra_persistent/genuine_discoveries.json"

if [ ! -f "$DISCOVERY_STORE" ]; then
    echo "❌ Discovery store not found. Start genuine discovery first:"
    echo "   ./start_genuine_discovery.sh"
    echo ""
    echo "The system needs time to complete discovery cycles."
    echo "Each cycle takes ~30 minutes and generates 1-3 candidate discoveries."
    exit 1
fi

python3 - <<EOF
import json
from pathlib import Path
from datetime import datetime

store_path = Path.home() / '.astra_persistent/genuine_discoveries.json'

try:
    with open(store_path) as f:
        store = json.load(f)

    discoveries = store.get('discoveries', [])
    stats = store.get('statistics', {})

    if not discoveries:
        print("No genuine discoveries yet. The system is still running...")
        print("Discovery cycles completed:", stats.get('total_cycles', 0))
        print("Failed attempts:", len(store.get('failed_attempts', [])))
        print("")
        print("The system applies rigorous standards - genuine discoveries take time!")
        exit(0)

    print(f"Total genuine discoveries: {len(discoveries)}")
    print(f"Discovery cycles completed: {stats.get('total_cycles', 0)}")
    print(f"Success rate: {stats.get('discovery_rate', 0):.3f}")
    print("")

    print("=" * 80)
    print("GENUINE DISCOVERIES")
    print("=" * 80)

    for i, d in enumerate(discoveries, 1):
        print(f"\n🔬 DISCOVERY #{i} (Cycle {d.get('cycle', '?')})")
        print("=" * 80)

        print(f"Title: {d.get('title', 'Untitled')}")
        print(f"Type: {d.get('type', 'unknown')}")
        print(f"Novelty Level: {d.get('novelty_level', 'unknown')}")
        print(f"Timestamp: {d.get('timestamp', 'unknown')}")

        validation = d.get('validation', {})

        print(f"\n✅ VALIDATION METRICS:")
        print(f"   Novelty Score: {validation.get('novelty_score', 0):.3f} / 1.000")
        print(f"   Probability Correct: {validation.get('probability_correct', 0):.3f} / 1.000")
        print(f"   Testability: {validation.get('testability', 'unknown')}")

        print(f"\n📝 ABSTRACT:")
        abstract = d.get('abstract', 'No abstract')
        print(abstract[:500] + ("..." if len(abstract) > 500 else ""))

        print(f"\n🔬 METHODOLOGY:")
        print(f"   {d.get('methodology', 'unknown')}")

        print(f"\n📊 DOMAINS INVOLVED:")
        domains = d.get('domains', [])
        if domains:
            print(f"   {', '.join(domains)}")

        print(f"\n🎯 NEXT STEPS:")
        steps = d.get('next_steps', [])
        for step in steps[:3]:
            print(f"   • {step}")

        print(f"\n💡 POTENTIAL IMPACT:")
        impact = validation.get('potential_impact', 'unknown')
        print(f"   {impact}")

        print("\n" + "-" * 80)

except Exception as e:
    print(f"Error reading discovery store: {e}")
    import traceback
    traceback.print_exc()
EOF

echo ""
echo "=== FULL DETAILS ==="
echo "Discovery store: $DISCOVERY_STORE"
echo ""
echo "To monitor discovery process in real-time:"
echo "  tail -f ~/.astra_persistent/24_7_genuine_discovery.log"