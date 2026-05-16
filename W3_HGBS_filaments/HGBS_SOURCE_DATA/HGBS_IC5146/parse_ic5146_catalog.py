#!/usr/bin/env python3
"""
HGBS IC5146 Core Catalog Parser

The IC5146 catalog is in CSV format with columns:
obj_id, mass_Msun, peak_N_cm2, npix, ra_deg, dec_deg, Tdust_K, type

Author: ASTRA Discovery System
Date: 5 April 2026
"""

import numpy as np
import os

def parse_ic5146_catalog(filename):
    """Parse the IC5146 core catalog from CSV file."""
    cores = []

    print(f"Opening catalog file: {filename}")

    # Check file size
    file_size = os.path.getsize(filename)
    print(f"File size: {file_size/1024:.1f} KB")

    with open(filename, 'r') as f:
        lines = f.readlines()

    # Skip header lines (starting with #)
    data_lines = [line.strip() for line in lines if line.strip() and not line.startswith('#')]

    print(f"Total lines: {len(lines)}")
    print(f"Data lines: {len(data_lines)}")

    # Parse each data line
    for line_num, line in enumerate(data_lines, 1):
        parts = line.split(',')
        if len(parts) >= 7:
            try:
                core = parse_line(parts, line_num)
                if core:
                    cores.append(core)
            except Exception as e:
                print(f"Warning: Failed to parse line {line_num}: {e}")
                continue

    print(f"\nSuccessfully parsed {len(cores)} cores")
    return cores


def parse_line(parts, line_num):
    """Parse a single line from the IC5146 catalog."""
    try:
        # Extract values from CSV
        obj_id = int(parts[0])
        mass = float(parts[1])
        peak_nh2 = float(parts[2]) / 1e21  # Convert from cm^-2 to 10^21 cm^-2
        npix = int(parts[3])
        ra_deg = float(parts[4])
        dec_deg = float(parts[5])
        temp = float(parts[6])
        core_type = parts[7].strip() if len(parts) > 7 else 'unknown'

        # Create RA/Dec string representations
        # Convert degrees to HH:MM:SS format
        ra_hours = ra_deg / 15.0
        ra_h = int(ra_hours)
        ra_m = int((ra_hours - ra_h) * 60)
        ra_s = (ra_hours - ra_h - ra_m/60.0) * 3600
        ra_str = f"{ra_h:02d}:{ra_m:02d}:{ra_s:05.2f}"

        dec_str = f"{dec_deg:+.6f}"

        # Create name from object ID
        core_name = f'IC5146_{obj_id:04d}'

        core = {
            'id': obj_id,
            'name': core_name,
            'ra': ra_str,
            'dec': dec_str,
            'ra_deg': ra_deg,
            'dec_deg': dec_deg,
            'mass': mass,
            'temp': temp,
            'nh2_peak': peak_nh2,
            'npix': npix,
            'alpha_be': None,  # Not provided in catalog
            'type': core_type
        }

        return core

    except (ValueError, IndexError) as e:
        print(f"Warning: Failed to parse line {line_num}: {e}")
        return None


if __name__ == '__main__':
    catalog_file = '/Users/gjw255/astrodata/SWARM/ASTRA/HGBS_IC5146/core_catalog_ic5146.csv'

    print("="*70)
    print("Parsing IC5146 Core Catalog (CSV Format)")
    print("="*70)

    cores = parse_ic5146_catalog(catalog_file)

    if cores:
        print("\n" + "="*70)
        print("First 5 cores:")
        print("="*70)
        for i, core in enumerate(cores[:5]):
            print(f"\n  {i+1}. {core['name']}")
            print(f"     RA: {core['ra']} = {core['ra_deg']:.6f}°")
            print(f"     Dec: {core['dec']} = {core['dec_deg']:.6f}°")
            print(f"     Mass: {core['mass']:.4f} Msun, T: {core['temp']:.1f} K, Type: {core['type']}")

        # Count core types
        print("\n" + "="*70)
        print("Core type distribution:")
        print("="*70)
        type_counts = {}
        for core in cores:
            ctype = core['type']
            type_counts[ctype] = type_counts.get(ctype, 0) + 1

        for ctype, count in sorted(type_counts.items()):
            print(f"  {ctype}: {count} ({100*count/len(cores):.1f}%)")

        # Mass statistics
        masses = [c['mass'] for c in cores if c['mass'] > 0]
        if masses:
            print("\n" + "="*70)
            print("Mass statistics [Msun]:")
            print("="*70)
            print(f"  Range: {np.min(masses):.4f} - {np.max(masses):.4f}")
            print(f"  Median: {np.median(masses):.4f}")
            print(f"  Mean: {np.mean(masses):.4f}")

        # Temperature statistics
        temps = [c['temp'] for c in cores if c['temp'] > 0]
        if temps:
            print("\n" + "="*70)
            print("Temperature statistics [K]:")
            print("="*70)
            print(f"  Range: {np.min(temps):.2f} - {np.max(temps):.2f}")
            print(f"  Median: {np.median(temps):.2f}")

    print("\n" + "="*70)
    print("Parsing complete!")
    print("="*70)
