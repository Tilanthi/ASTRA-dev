#!/usr/bin/env python3
"""
Run all 5 phases for a region
"""

import subprocess
import sys

def run_phase(script_name):
    """Run a single phase script"""
    print(f"\nRunning {script_name}...")
    try:
        result = subprocess.run([sys.executable, script_name],
                              capture_output=True, text=True,
                              timeout=600)  # 10 min timeout
        print(result.stdout[-500:] if len(result.stdout) > 500 else result.stdout)
        if result.returncode != 0:
            print(f"ERROR in {script_name}:")
            print(result.stderr[-500:] if len(result.stderr) > 500 else result.stderr)
            return False
        return True
    except subprocess.TimeoutExpired:
        print(f"TIMEOUT: {script_name} took too long")
        return False
    except Exception as e:
        print(f"ERROR in {script_name}: {e}")
        return False

print("="*70)
print("AUTOMATED 5-PHASE ANALYSIS")
print("="*70)

phases = [
    'hgbs_discovery_phase1_fixed.py',
    'hgbs_discovery_phase2.py',
    'hgbs_discovery_phase3.py',
    'hgbs_discovery_phase4.py',
    'hgbs_discovery_phase5.py'
]

success_count = 0
for i, phase in enumerate(phases, 1):
    print(f"\n{'='*70}")
    print(f"PHASE {i}/5")
    print(f"{'='*70}")

    if run_phase(phase):
        success_count += 1
    else:
        print(f"Phase {i} failed - stopping")
        break

print("\n" + "="*70)
print(f"ANALYSIS COMPLETE: {success_count}/5 phases successful")
print("="*70)
