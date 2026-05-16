#!/usr/bin/env python3
"""
HGBS Discovery Science - Setup New Region

This script copies all necessary analysis scripts to a new HGBS region folder
so you can run the complete analysis without manual file copying.

Usage:
    python setup_region.py <target_region_folder>

Example:
    python setup_region.py /data/HGBS_ORION

Author: ASTRA Discovery System
Date: 18 April 2026
"""

import os
import sys
import shutil
from pathlib import Path


def print_banner(text):
    """Print a formatted banner."""
    print("\n" + "="*70)
    print(text.center(70))
    print("="*70 + "\n")


def copy_scripts(source_dir, target_dir):
    """Copy analysis scripts to target directory."""
    scripts_to_copy = [
        'parse_catalog.py',
        'hgbs_discovery_phase1_fixed.py',
        'hgbs_discovery_phase2.py',
        'hgbs_discovery_phase3.py',
        'hgbs_discovery_phase4.py',
        'hgbs_discovery_phase5.py',
        'catalog_analysis.py',
        'create_visualizations.py',
        'run_all_phases.py',
    ]

    print("Copying analysis scripts...")
    print("-" * 40)

    copied = []
    not_found = []

    for script in scripts_to_copy:
        source_path = os.path.join(source_dir, script)
        target_path = os.path.join(target_dir, script)

        if os.path.exists(source_path):
            shutil.copy2(source_path, target_path)
            size = os.path.getsize(target_path) / 1024  # KB
            print(f"  ✓ {script} ({size:.1f} KB)")
            copied.append(script)
        else:
            print(f"  ✗ {script} NOT FOUND in source")
            not_found.append(script)

    return copied, not_found


def check_data_files(target_dir):
    """Check what data files exist in target directory."""
    print("\nChecking data files in target folder...")
    print("-" * 40)

    fits_files = []
    catalog_files = []

    try:
        for item in os.listdir(target_dir):
            item_path = os.path.join(target_dir, item)
            if os.path.isfile(item_path):
                if item.endswith('.fits'):
                    fits_files.append(item)
                elif 'catalog' in item.lower() and item.endswith('.txt'):
                    catalog_files.append(item)
    except Exception as e:
        print(f"  Error listing directory: {e}")
        return [], []

    if fits_files:
        print(f"\n  FITS files found ({len(fits_files)}):")
        for f in sorted(fits_files):
            size = os.path.getsize(os.path.join(target_dir, f)) / (1024*1024)  # MB
            print(f"    - {f} ({size:.1f} MB)")
    else:
        print("\n  ⚠ No FITS files found!")

    if catalog_files:
        print(f"\n  Catalog files found ({len(catalog_files)}):")
        for f in sorted(catalog_files):
            print(f"    - {f}")
    else:
        print("\n  ⚠ No catalog files found!")

    return fits_files, catalog_files


def print_usage_instructions(target_dir, fits_files):
    """Print instructions for running the analysis."""
    print("\n" + "="*70)
    print("SETUP COMPLETE - READY TO RUN ANALYSIS")
    print("="*70 + "\n")

    print("To run the complete 5-phase analysis, use:")
    print("-" * 40)

    # Try to guess the region name from FITS files
    region_name = "REGION_NAME"
    if fits_files:
        # Extract region name from first FITS file
        first_fits = fits_files[0]
        # Common patterns: HGBS_aquilaM2_* or aquila_*
        if first_fits.startswith('HGBS_'):
            parts = first_fits.replace('HGBS_', '').split('_')
            if parts:
                region_name = parts[0].upper()
        elif '_' in first_fits:
            region_name = first_fits.split('_')[0].upper()

    print(f"  cd {target_dir}")
    print(f"  python run_all_phases.py {target_dir} {region_name}")
    print()

    print("Or run phases individually:")
    print("-" * 40)
    print("  python hgbs_discovery_phase1_fixed.py")
    print("  python hgbs_discovery_phase2.py")
    print("  python hgbs_discovery_phase3.py")
    print("  python hgbs_discovery_phase4.py")
    print("  python hgbs_discovery_phase5.py")
    print()

    print("After analysis completes, create visualizations:")
    print("-" * 40)
    print("  python create_visualizations.py")
    print()


def main():
    """Main function."""
    if len(sys.argv) < 2:
        print("Usage: python setup_region.py <target_region_folder>")
        print("\nExample:")
        print("  python setup_region.py /data/HGBS_ORION")
        print("\nThis will copy all necessary analysis scripts to the target folder.")
        sys.exit(1)

    target_dir = sys.argv[1]
    target_dir = os.path.abspath(target_dir)

    # Get the source directory (where this script is located)
    source_dir = os.path.dirname(os.path.abspath(__file__))

    print_banner("HGBS DISCOVERY SCIENCE - SETUP NEW REGION")

    print(f"Source directory: {source_dir}")
    print(f"Target directory: {target_dir}")

    # Check if target directory exists
    if not os.path.exists(target_dir):
        print(f"\nERROR: Target directory does not exist: {target_dir}")
        print("Please create it first and add your FITS files.")
        sys.exit(1)

    # Copy scripts
    copied, not_found = copy_scripts(source_dir, target_dir)

    if not_found:
        print(f"\n⚠ Warning: {len(not_found)} script(s) not found in source directory")

    # Check data files
    fits_files, catalog_files = check_data_files(target_dir)

    # Print usage instructions
    print_usage_instructions(target_dir, fits_files)


if __name__ == '__main__':
    main()
