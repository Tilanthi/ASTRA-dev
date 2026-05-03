#!/usr/bin/env python3
"""
Run script for Targeted Supercritical f=1.5 Campaign

Executes 5 Athena++ simulations with extended domains at f=1.5.

Author: ASTRA Agent System
Date: 2026-05-03
"""

import subprocess
import time
from pathlib import Path
import json

def run_simulation(config_file, exec_path="./athena++"):
    """
    Run a single Athena++ simulation.

    Parameters
    ----------
    config_file : str or Path
        Path to .athinput configuration file
    exec_path : str
        Path to Athena++ executable

    Returns
    -------
    success : bool
        True if simulation completed successfully
    """
    config_file = Path(config_file)

    print(f"Running simulation: {config_file.name}")
    print(f"Executable: {exec_path}")
    print(f"Started at: {time.strftime('%Y-%m-%d %H:%M:%S')}")

    # Start timer
    start_time = time.time()

    # Run simulation
    try:
        result = subprocess.run(
            [exec_path, "-i", str(config_file)],
            capture_output=True,
            text=True,
            timeout=21600  # 6 hour timeout
        )

        # End timer
        elapsed = time.time() - start_time

        if result.returncode == 0:
            print(f"✓ SUCCESS: Completed in {elapsed:.1f} seconds ({elapsed/3600:.2f} hours)")
            return True
        else:
            print(f"✗ FAILED: Return code {result.returncode}")
            print(f"STDERR: {result.stderr}")
            return False

    except subprocess.TimeoutExpired:
        print(f"✗ TIMEOUT: Exceeded 6 hour wall-clock limit")
        return False

    except Exception as e:
        print(f"✗ ERROR: {e}")
        return False


def main():
    """Run all simulations in the campaign."""

    # Configuration
    config_dir = Path("configs")
    exec_path = "./athena++"  # Adjust if needed
    max_concurrent = 2  # Run 2 simulations at a time

    # Find all config files
    config_files = sorted(config_dir.glob("targeted_f15_extended_*.athinput"))

    if len(config_files) == 0:
        print(f"ERROR: No config files found in {config_dir}")
        print("Run generate_configs.py first!")
        return

    print("="*70)
    print("TARGETED SUPERCRITICAL F=1.5 CAMPAIGN: Execution")
    print("="*70)
    print(f"Config directory: {config_dir.absolute()}")
    print(f"Number of simulations: {len(config_files)}")
    print(f"Max concurrent: {max_concurrent}")
    print(f"Executable: {exec_path}")
    print()

    # Check executable exists
    if not Path(exec_path).exists():
        print(f"ERROR: Athena++ executable not found: {exec_path}")
        print("Compile Athena++ first!")
        return

    # Track results
    results = {
        'campaign': 'targeted_supercritical_f15',
        'start_time': time.strftime('%Y-%m-%d %H:%M:%S'),
        'simulations': []
    }

    # Run simulations
    completed = 0
    failed = 0

    for i, config_file in enumerate(config_files, 1):
        print(f"\n[{i}/{len(config_files)}] Processing {config_file.name}")
        print("-" * 70)

        success = run_simulation(config_file, exec_path)

        sim_result = {
            'config_file': str(config_file),
            'success': success
        }

        results['simulations'].append(sim_result)

        if success:
            completed += 1
        else:
            failed += 1

    # Summary
    print()
    print("="*70)
    print("CAMPAIGN COMPLETE")
    print("="*70)
    print(f"Total simulations: {len(config_files)}")
    print(f"Successful: {completed}")
    print(f"Failed: {failed}")
    print()

    # Save results
    results['end_time'] = time.strftime('%Y-%m-%d %H:%M:%S')
    results['completed'] = completed
    results['failed'] = failed

    results_file = "campaign_results.json"
    with open(results_file, 'w') as f:
        json.dump(results, f, indent=2)

    print(f"Results saved to: {results_file}")
    print()
    print("Next steps:")
    print("1. Run analysis: python3 analyze_results.py")
    print("2. Review classification results")
    print()


if __name__ == '__main__':
    main()
