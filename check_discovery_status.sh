#!/bin/bash
# Check status of 24/7 autonomous discovery system

echo "=== 24/7 AUTONOMOUS DISCOVERY STATUS ==="
echo ""

# Check if process is running
if pgrep -f "run_24_7_discovery.py" > /dev/null; then
    echo "✅ Discovery process: RUNNING"
    echo "PID: $(pgrep -f 'run_24_7_discovery.py')"
else
    echo "❌ Discovery process: NOT RUNNING"
fi

echo ""
echo "=== DISCOVERY STATE ==="

python3 -c "
from astra_core.autonomous_startup_discovery import get_autonomous_startup_discovery
import json
from pathlib import Path

try:
    discovery = get_autonomous_startup_discovery()

    print(f'State: {discovery.state.value}')
    print(f'Mode: {discovery.config.mode.value}')
    print(f'Thread alive: {discovery.discovery_thread.is_alive() if discovery.discovery_thread else False}')
    print(f'ASTRA connected: {discovery.astra_system is not None}')
    print(f'Cycles completed: {discovery.discovery_cycles_completed}')
    print(f'Discoveries made: {len(discovery.discoveries_made)}')

    if discovery.discoveries_made:
        print(f'Latest discovery: {discovery.discoveries_made[-1].get(\"status\", \"unknown\")}')
        print(f'Total processed: {sum(1 for d in discovery.discoveries_made if d.get(\"status\") == \"processed\")}')

    # Show recent discoveries
    state_file = Path.home() / '.astra_persistent/startup_discovery_state.json'
    if state_file.exists():
        with open(state_file) as f:
            state = json.load(f)
            print(f'Persistent state: {len(state.get(\"discoveries\", []))} discoveries')

except Exception as e:
    print(f'Error checking status: {e}')
"

echo ""
echo "=== LOG FILES ==="
echo "Main log: ~/.astra_persistent/24_7_discovery.log"
echo "State file: ~/.astra_persistent/startup_discovery_state.json"