#!/usr/bin/env python3

# Copyright 2024-2026 Glenn J. White (The Open University / RAL Space)
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""
ASTRA Restart Script with State Persistence

This script:
1. Saves current ASTRA state (hypotheses, engine state, cognitive state)
2. Stops the running ASTRA server
3. Restarts with all new cognitive capabilities
4. Restores all previous state

Usage: python3 restart_astra.py
"""
import os
import sys
import time
import subprocess
import signal
from pathlib import Path

# Add parent to path
sys.path.insert(0, str(Path(__file__).resolve().parent))

from astra_live_backend.state_persistence import (
    save_engine_state, save_hypotheses, save_cognitive_state,
    get_state_summary, STATE_DIR
)


def save_current_state(engine):
    """Save current ASTRA state before restart."""
    print("=" * 70)
    print("SAVING ASTRA STATE BEFORE RESTART")
    print("=" * 70)

    # Save engine state
    engine_state = save_engine_state(engine)
    print(f"✓ Saved engine state: cycle {engine_state['cycle_count']}")

    # Save hypotheses
    hypotheses = save_hypotheses(engine.store)
    print(f"✓ Saved {hypotheses} hypotheses")

    # Save cognitive state
    if engine.cognitive_core:
        save_cognitive_state(engine.cognitive_core)
        print(f"✓ Saved cognitive state: {len(engine.cognitive_core.discoveries)} discoveries")

    # Show summary
    summary = get_state_summary()
    print(f"\nState saved to: {STATE_DIR}")
    print(f"  - Active hypotheses: {summary.get('active_hypotheses', 0)}")
    print(f"  - Total hypotheses: {summary.get('hypotheses_count', 0)}")
    print(f"  - Cycles completed: {summary.get('cycle_count', 0)}")

    print("\n✅ State saved successfully!")


def check_running_server():
    """Check if ASTRA server is running."""
    try:
        # Check if port 8787 is in use
        result = subprocess.run(
            ["lsof", "-i", ":8787"],
            capture_output=True,
            text=True
        )

        if result.returncode == 0:
            # Extract PID
            lines = result.stdout.split('\n')
            if len(lines) > 1:
                parts = lines[1].split()
                if parts:
                    return int(parts[1])  # PID is second column

        return None
    except Exception as e:
        print(f"Note: Could not check for running server: {e}")
        return None


def stop_server(pid):
    """Stop the running ASTRA server."""
    print(f"\nStopping ASTRA server (PID: {pid})...")

    try:
        # Try graceful shutdown first
        os.kill(pid, signal.SIGTERM)
        time.sleep(3)

        # Check if still running
        try:
            os.kill(pid, 0)  # Check if process exists
            # Still running, force kill
            print("Force killing...")
            os.kill(pid, signal.SIGKILL)
            time.sleep(1)
        except OSError:
            # Process is gone
            pass

        print("✓ Server stopped")
        return True
    except Exception as e:
        print(f"Error stopping server: {e}")
        return False


def start_server():
    """Start ASTRA server with new capabilities."""
    print("\n" + "=" * 70)
    print("STARTING ASTRA WITH COGNITIVE ARCHITECTURE")
    print("=" * 70)

    print("\n🚀 Starting ASTRA server...")
    print("   - Knowledge Graph: Semantic brain")
    print("   - Neuro-Symbolic Engine: Pattern discovery + symbolic reasoning")
    print("   - Meta-Cognition: Self-awareness and self-improvement")
    print("   - State Persistence: Automatic save/restore")
    print("\nNew API Endpoints:")
    print("   - /api/cognitive/status")
    print("   - /api/knowledge-graph/*")
    print("   - /api/metacognition/*")
    print("   - /api/cognitive/*")
    print("   - /api/state/*")

    print("\n🌐 Dashboard: http://localhost:8787")
    print("📚 API Docs:  http://localhost:8787/docs")
    print("\n" + "=" * 70)
    print("ASTRA is running with cognitive capabilities!")
    print("=" * 70)

    # Start server
    os.chdir(Path(__file__).parent)
    subprocess.run([sys.executable, "-m", "astra_live_backend.server"])


def main():
    """Main restart workflow."""
    print("\n" + "=" * 70)
    print("ASTRA RESTART WITH COGNITIVE ARCHITECTURE")
    print("=" * 70)
    print("\nThis will:")
    print("1. Save all current hypotheses and state")
    print("2. Stop the running server")
    print("3. Restart with new cognitive capabilities")
    print("4. Restore all saved state")

    # Import engine to save state
    try:
        from astra_live_backend.engine import DiscoveryEngine
        print("\nLoading ASTRA engine...")
        engine = DiscoveryEngine()

        # Save current state
        save_current_state(engine)

        # Check for running server
        print("\nChecking for running server...")
        pid = check_running_server()

        if pid:
            print(f"Found running server (PID: {pid})")

            # Ask if we should stop it
            response = input("\nStop the running server? (y/n): ").strip().lower()

            if response == 'y':
                stop_server(pid)
                time.sleep(2)
            else:
                print("\n⚠️  Please stop the server manually before restarting")
                print("   You can stop it with Ctrl+C in the server terminal")
                return

        # Start new server
        start_server()

    except ImportError as e:
        print(f"Error importing ASTRA: {e}")
        print("Make sure you're running from the ASTRA directory")
        return
    except Exception as e:
        print(f"Error: {e}")
        return


if __name__ == "__main__":
    main()
