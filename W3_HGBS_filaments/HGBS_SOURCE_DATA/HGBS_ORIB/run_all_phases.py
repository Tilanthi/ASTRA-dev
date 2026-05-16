#!/usr/bin/env python3
"""
HGBS Discovery Science - Run All Phases

This script runs all 5 phases of HGBS discovery analysis on a specified region.
It automatically updates paths in the phase scripts and runs them sequentially.

Usage:
    python run_all_phases.py <region_folder> <region_name>

Example:
    python run_all_phases.py /path/to/HGBS_ORION Orion

Author: ASTRA Discovery System
Date: 18 April 2026
"""

import os
import sys
import subprocess
import shutil
from pathlib import Path
import time


def print_banner(text):
    """Print a formatted banner."""
    print("\n" + "="*70)
    print(text.center(70))
    print("="*70 + "\n")


def print_phase(number, name):
    """Print phase header."""
    print("\n" + "-"*70)
    print(f"PHASE {number}: {name}")
    print("-"*70 + "\n")


def update_hgbs_dir_in_script(script_path, new_hgbs_dir):
    """Update the HGBS_DIR variable in a script."""
    with open(script_path, 'r') as f:
        content = f.read()

    # Replace HGBS_DIR line
    lines = content.split('\n')
    new_lines = []
    for line in lines:
        if line.strip().startswith("HGBS_DIR = "):
            indent = len(line) - len(line.lstrip())
            new_lines.append(" " * indent + f"HGBS_DIR = '{new_hgbs_dir}'")
        elif "results_file = " in line and "phase2_results.npz" in line:
            # Keep results in current directory
            indent = len(line) - len(line.lstrip())
            new_lines.append(" " * indent + "results_file = 'phase2_results.npz'")
        else:
            new_lines.append(line)

    with open(script_path, 'w') as f:
        f.write('\n'.join(new_lines))


def run_script(script_name, region_folder):
    """Run a phase script and return success status."""
    script_path = os.path.join(region_folder, script_name)

    if not os.path.exists(script_path):
        print(f"ERROR: {script_name} not found in {region_folder}")
        print(f"Please copy the script from the ASTRA/HGBS folder first.")
        return False

    print(f"Running {script_name}...")
    print(f"Working directory: {region_folder}")
    print(f"Script: {script_path}")
    print("-" * 40)

    try:
        result = subprocess.run(
            [sys.executable, script_path],
            cwd=region_folder,
            capture_output=False,
            text=True
        )

        if result.returncode == 0:
            print(f"✓ {script_name} completed successfully")
            return True
        else:
            print(f"✗ {script_name} failed with return code {result.returncode}")
            return False

    except Exception as e:
        print(f"✗ Error running {script_name}: {e}")
        return False


def check_required_files(region_folder, region_name):
    """Check if required FITS files exist in the region folder."""
    required_files = [
        f'{region_name}_column_density_map.fits',
        f'{region_name}_temperature_map.fits',
        f'{region_name}_skeleton_map.fits',
        f'{region_name}_derived_core_catalog.txt'
    ]

    print("Checking for required data files...")

    all_exist = True
    for filename in required_files:
        filepath = os.path.join(region_folder, filename)
        if os.path.exists(filepath):
            print(f"  ✓ {filename}")
        else:
            print(f"  ✗ {filename} NOT FOUND")
            all_exist = False

    if not all_exist:
        print("\nWARNING: Some required files are missing.")
        print("Please check your FITS file names - they may differ.")
        print("Common variations include 'HGBS_<region>_' prefix or no prefix.")
        print("\nFiles currently in directory:")
        try:
            for f in os.listdir(region_folder):
                if f.endswith(('.fits', '.txt')):
                    print(f"  - {f}")
        except:
            pass

    return all_exist


def main():
    """Main function to run all phases."""
    if len(sys.argv) < 3:
        print("Usage: python run_all_phases.py <region_folder> <region_name>")
        print("\nExample:")
        print("  python run_all_phases.py /data/HGBS_ORION Orion")
        print("\nWhere:")
        print("  region_folder = Path to the folder containing FITS files")
        print("  region_name   = Name used in FITS file names (e.g., 'Orion', 'Aquila')")
        sys.exit(1)

    region_folder = sys.argv[1]
    region_name = sys.argv[2]

    # Normalize paths
    region_folder = os.path.abspath(region_folder)

    print_banner("HGBS DISCOVERY SCIENCE - MULTI-PHASE ANALYSIS")

    print(f"Region Folder: {region_folder}")
    print(f"Region Name: {region_name}")

    # Check if region folder exists
    if not os.path.exists(region_folder):
        print(f"\nERROR: Region folder does not exist: {region_folder}")
        sys.exit(1)

    # Check for required files
    print()
    check_required_files(region_folder, region_name)

    response = input("\nContinue with analysis? (y/n): ")
    if response.lower() != 'y':
        print("Exiting.")
        sys.exit(0)

    # List of scripts to run in order
    phases = [
        (1, "Data Exploration", "hgbs_discovery_phase1_fixed.py"),
        (2, "Core-Filament Association", "hgbs_discovery_phase2.py"),
        (3, "Mass-per-Unit-Length Analysis", "hgbs_discovery_phase3.py"),
        (4, "Filament Junction Analysis", "hgbs_discovery_phase4.py"),
        (5, "Discovery Mode with ASTRA", "hgbs_discovery_phase5.py"),
    ]

    # Track results
    phase_results = {}
    start_time = time.time()

    # Run each phase
    for phase_num, phase_name, script_name in phases:
        print_phase(phase_num, phase_name)

        # Update HGBS_DIR in the script
        script_path = os.path.join(region_folder, script_name)
        if os.path.exists(script_path):
            update_hgbs_dir_in_script(script_path, region_folder)
        else:
            print(f"WARNING: {script_name} not found. Skipping this phase.")
            phase_results[phase_num] = False
            continue

        # Run the script
        success = run_script(script_name, region_folder)
        phase_results[phase_num] = success

        if not success:
            print(f"\nPhase {phase_num} failed. Continuing with next phase...")

    # Summary
    elapsed_time = time.time() - start_time

    print_banner("ANALYSIS COMPLETE")

    print(f"Total elapsed time: {elapsed_time:.1f} seconds ({elapsed_time/60:.1f} minutes)")
    print()
    print("Phase Results:")
    print("-" * 40)

    for phase_num, phase_name, _ in phases:
        status = "✓ COMPLETE" if phase_results.get(phase_num, False) else "✗ FAILED"
        print(f"  Phase {phase_num} ({phase_name}): {status}")

    print()
    print("Output Files Created:")
    print("-" * 40)

    # Check for output files
    output_files = [
        "phase2_results.npz",
        "PHASE1_RESULTS.md",
        "PHASE2_RESULTS.md",
        "PHASE3_RESULTS.md",
        "PHASE4_RESULTS.md",
        "PHASE5_RESULTS.md"
    ]

    for filename in output_files:
        filepath = os.path.join(region_folder, filename)
        if os.path.exists(filepath):
            size = os.path.getsize(filepath) / 1024  # KB
            print(f"  ✓ {filename} ({size:.1f} KB)")

    print()
    print("Next Steps:")
    print("-" * 40)
    print("1. Review the phase result markdown files")
    print("2. Create visualizations: python create_visualizations.py")
    print("3. Compile results into paper draft")
    print()
    print(f"All results saved in: {region_folder}")
    print()


if __name__ == '__main__':
    main()
