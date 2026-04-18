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
Run the automatic discovery verification workflow.

This script:
1. Verifies pending high-strength discoveries
2. Promotes those that pass verification criteria to "Verified" status
3. Updates the dashboard HTML with new verified discoveries

Usage:
    python3 run_verification_workflow.py
"""
import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from astra_live_backend.engine import DiscoveryEngine
from astra_live_backend.verification_auto import get_verified_manager
from astra_live_backend.update_verified_dashboard import update_dashboard


def run_verification_workflow():
    """Run the complete verification workflow."""
    print("=" * 70)
    print("ASTRA DISCOVERY VERIFICATION WORKFLOW")
    print("=" * 70)
    print()

    # Get the verified discovery manager
    print("Step 1: Running verification workflow...")
    manager = get_verified_manager()

    # Run verification
    new_verified = manager.update_verified_discoveries()

    if new_verified:
        print(f"  ✓ Verified {len(new_verified)} new discoveries")
    else:
        print("  → No new discoveries met verification criteria this run")

    print()

    # Get all verified discoveries
    print("Step 2: Fetching all verified discoveries...")
    all_verified = manager.get_all_verified_discoveries()
    print(f"  → Total verified discoveries: {len(all_verified)}")

    print()

    # Show summary
    if new_verified:
        print("Newly Verified Discoveries:")
        for v in new_verified:
            strength = v.get('score', 0.0)
            print(f"  • {v['hypothesis_id']} (verification score: {strength:.3f})")

    print()

    # Update dashboard
    print("Step 3: Updating dashboard HTML...")
    try:
        from astra_live_backend.update_verified_dashboard import update_dashboard
        update_dashboard()
        print("  ✓ Dashboard updated successfully")
    except Exception as e:
        print(f"  ✗ Dashboard update failed: {e}")

    print()
    print("=" * 70)
    print("VERIFICATION COMPLETE")
    print("=" * 70)

    return len(new_verified)


def main():
    """Main entry point."""
    # Check if engine is running
    try:
        import requests
        response = requests.get('http://localhost:8787/api/status', timeout=2)
        if response.status_code == 200:
            engine_running = True
        else:
            engine_running = False
    except:
        engine_running = False

    if engine_running:
        print("Note: ASTRA engine is running. New discoveries will be")
        print("      automatically verified during the UPDATE phase.")
        print()

    # Run verification workflow
    verified_count = run_verification_workflow()

    if verified_count > 0:
        print()
        print(f"SUCCESS: {verified_count} discoveries promoted to Verified status")
    else:
        print("INFO: No discoveries met verification criteria this run.")
        print()
        print("Verification criteria:")
        print("  - Strength ≥ 0.80")
        print("  - Effect size ≥ 0.3")
        print("  - Sample size ≥ 50")
        print("  - Physical validity check")
        print("  - Novelty check")
        print()
        print("Discoveries are evaluated every 5 cycles automatically.")
        print("To manually trigger verification:")
        print("  POST http://localhost:8787/api/verification/run")


if __name__ == '__main__':
    main()
