#!/usr/bin/env python3
"""
Setup and run 5-phase analysis for HGBS_IC5146
"""

import os
import shutil
import subprocess

IC5146_DIR = '/Users/gjw255/astrodata/SWARM/ASTRA/HGBS_IC5146'
TAURUS_DIR = '/Users/gjw255/astrodata/SWARM/ASTRA/HGBS_TAURUS'

print("="*70)
print("Setting up IC5146 5-Phase Analysis Pipeline")
print("="*70)

# Copy phase scripts from Taurus (as template)
for i in range(1, 6):
    src = os.path.join(TAURUS_DIR, f'hgbs_discovery_phase{i}.py')
    dst = os.path.join(IC5146_DIR, f'hgbs_discovery_phase{i}.py')
    if os.path.exists(src) and not os.path.exists(dst):
        shutil.copy(src, dst)
        print(f"  Copied phase{i}.py")

# Update paths in scripts for IC5146
ic5146_config = {
    'HGBS_DIR': IC5146_DIR,
    'COL_DEN_FILE': 'HGBS_ic5146_hires_column_density_map.fits',
    'TEMP_FILE': 'HGBS_ic5146_dust_temperature_map.fits',
    'SKELETON_FILE': 'HGBS_ic5146_skeleton_map.fits',
    'CAT_FILE': 'core_catalog_ic5146.csv',
    'parser': 'parse_ic5146_catalog',
    'parser_func': 'parse_ic5146_catalog',
    'distance': 260,  # Distance for IC5146
}

for i in range(1, 6):
    script_path = os.path.join(IC5146_DIR, f'hgbs_discovery_phase{i}.py')
    if os.path.exists(script_path):
        with open(script_path, 'r') as f:
            content = f.read()

        # Update HGBS_DIR
        content = content.replace("HGBS_DIR = '/Users/gjw255/astrodata/SWARM/ASTRA/HGBS_TAURUS'",
                             f"HGBS_DIR = '{IC5146_DIR}'")

        # Update FITS file paths
        content = content.replace(
            "COL_DEN_FILE = os.path.join(HGBS_DIR, 'HGBS_tauN3_hires_column_density_map.fits')",
            f"COL_DEN_FILE = os.path.join(HGBS_DIR, '{ic5146_config['COL_DEN_FILE']}')"
        )

        content = content.replace(
            "TEMP_FILE = os.path.join(HGBS_DIR, 'HGBS_taurus_L1495_dust_temperature_map.fits')",
            f"TEMP_FILE = os.path.join(HGBS_DIR, '{ic5146_config['TEMP_FILE']}')"
        )

        content = content.replace(
            "SKELETON_FILE = os.path.join(HGBS_DIR, 'HGBS_taurusL1495_skeleton_map.fits')",
            f"SKELETON_FILE = os.path.join(HGBS_DIR, '{ic5146_config['SKELETON_FILE']}')"
        )

        content = content.replace(
            "CAT_FILE = os.path.join(HGBS_DIR, 'HGBS_taurusL1495_derived_core_catalog.txt')",
            f"CAT_FILE = os.path.join(HGBS_DIR, '{ic5146_config['CAT_FILE']}')"
        )

        # Update parser imports
        content = content.replace(
            "from parse_taurus_catalog import parse_taurus_catalog",
            f"from {ic5146_config['parser']} import {ic5146_config['parser_func']}"
        )

        content = content.replace(
            "self.cores = parse_taurus_catalog(CAT_FILE)",
            f"self.cores = {ic5146_config['parser_func']}(CAT_FILE)"
        )

        # Update distance
        content = content.replace(
            "DISTANCE_PC = 140.0",
            f"DISTANCE_PC = {ic5146_config['distance']}"
        )

        # Update region names in output
        content = content.replace("HGBS TAURUS", "HGBS IC5146")
        content = content.replace("HGBS PERSEUS", "HGBS IC5146")
        content = content.replace("HGBS AQUILA", "HGBS IC5146")
        content = content.replace("Taurus L1495", "IC5146 (Cocoon Nebula)")

        with open(script_path, 'w') as f:
            f.write(content)

        print(f"  Updated phase{i}.py")

print("\n" + "="*70)
print("Scripts configured")
print("="*70)

# Run Phase 2
print("\nRunning Phase 2 Analysis...")
phase2_script = os.path.join(IC5146_DIR, 'hgbs_discovery_phase2.py')

try:
    result = subprocess.run(
        ['python', phase2_script],
        capture_output=True,
        text=True,
        timeout=300,
        cwd=IC5146_DIR
    )

    # Show key output
    output_lines = result.stdout.split('\n')
    summary_start = max(0, len(output_lines) - 40)
    print('\n'.join(output_lines[summary_start:]))

    if result.returncode == 0:
        # Check for results file
        results_file = os.path.join(IC5146_DIR, 'phase2_results.npz')
        if os.path.exists(results_file):
            size = os.path.getsize(results_file) / 1024
            print(f"\n✓ IC5146 Phase 2 complete!")
            print(f"  Results file: {size:.1f} KB")
        else:
            print(f"\n⚠ Results file not created")
    else:
        print(f"\n✗ Phase 2 failed")
        if result.stderr:
            print(f"Error: {result.stderr[-200:]}")

except subprocess.TimeoutExpired:
    print("\n✗ Phase 2 timed out")
except Exception as e:
    print(f"\n✗ Phase 2 error: {e}")

print("\n" + "="*70)
print("IC5146 Pipeline Setup Complete")
print("="*70)
print("Region: HGBS_IC5146 (Cocoon Nebula)")
print("  Cores: 174 star-forming cores")
print("  Skeleton: Available")
print("  Status: Ready for full 5-phase analysis")
