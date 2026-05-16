#!/usr/bin/env python3
"""
HGBS Serpens Core Catalog Parser

Note: Only observed catalog available, not derived catalog
Will have limited properties compared to other regions

Author: ASTRA Discovery System
Date: 22 April 2026
"""

import numpy as np

def parse_serpens_catalog(filename):
    """Parse the Serpens observed core catalog."""
    cores = []

    print(f"Opening catalog file: {filename}")
    with open(filename, 'r', encoding='latin-1') as f:
        lines = f.readlines()

    print(f"Total lines in file: {len(lines)}")

    # Find data start (skip header lines starting with !)
    data_start = None
    for i, line in enumerate(lines):
        if not line.startswith('!') and line.strip():
            # Check if this looks like a data line (starts with number)
            parts = line.split()
            if parts and parts[0].replace('.', '').replace('+', '').replace('-', '').isdigit():
                data_start = i
                break

    if data_start is None:
        print("Could not find data start")
        return cores

    for line_num, line in enumerate(lines[data_start:], start=data_start):
        line = line.strip()

        # Skip empty lines or comment lines
        if not line or line.startswith('!'):
            continue

        # Parse data line (space-separated)
        parts = line.split()
        if len(parts) >= 4 and parts[0].replace('.', '').replace('+', '').replace('-', '').isdigit():
            core = parse_line(parts, line_num)
            if core:
                cores.append(core)

    return cores


def parse_line(parts, line_num):
    """Parse a single line from the Serpens catalog."""
    try:
        # Serpens observed catalog has limited information
        # Format varies but includes: ID, Name, RA, Dec, and flux measurements

        core_id = int(parts[0]) if parts[0].replace('.', '').isdigit() else 0
        core_name = parts[1] if len(parts) > 1 else f"Serpens_{core_id}"

        # RA and Dec (various formats possible)
        ra_str = parts[2] if len(parts) > 2 else ""
        dec_str = parts[3] if len(parts) > 3 else ""

        # Convert to decimal degrees if format is recognizable
        ra_deg = np.nan
        dec_deg = np.nan

        if ':' in ra_str and ':' in dec_str:
            try:
                coord_parts = ra_str.split(':')
                ra_hours = float(coord_parts[0]) + float(coord_parts[1])/60.0 + float(coord_parts[2])/3600.0
                ra_deg = ra_hours * 15.0

                coord_parts = dec_str.split(':')
                dec_deg_val = abs(float(coord_parts[0])) + float(coord_parts[1])/60.0 + float(coord_parts[2])/3600.0
                if dec_str.startswith('-'):
                    dec_deg = -dec_deg_val
                else:
                    dec_deg = dec_deg_val
            except:
                pass

        # Serpens observed catalog doesn't have mass, temp, etc.
        # These will need to be estimated from column density maps
        core = {
            'id': core_id,
            'name': core_name,
            'ra': ra_str,
            'dec': dec_str,
            'ra_deg': ra_deg,
            'dec_deg': dec_deg,
            'mass': np.nan,  # Not available in observed catalog
            'temp': np.nan,  # Not available in observed catalog
            'nh2_peak': np.nan,  # Not available in observed catalog
            'type': 'unknown'  # Not classified in observed catalog
        }

        return core

    except (ValueError, IndexError) as e:
        print(f"Warning: Failed to parse line {line_num}: {e}")
        return None


if __name__ == '__main__':
    catalog_file = '/Users/gjw255/astrodata/SWARM/ASTRA/HGBS_SERPENS/HGBS_serpens_observed_core_catalog.txt'

    print("="*70)
    print("Parsing Serpens Core Catalog (OBSERVED ONLY)")
    print("="*70)

    cores = parse_serpens_catalog(catalog_file)

    print(f"\nSuccessfully parsed {len(cores)} cores")

    if cores:
        print("\n" + "="*70)
        print("First 5 cores:")
        print("="*70)
        for i, core in enumerate(cores[:5]):
            print(f"  {i+1}. {core['name']}: RA={core['ra']}, Dec={core['dec']}")

        print("\n" + "="*70)
        print("NOTE: Serpens catalog has limited properties")
        print("  - No derived mass values")
        print("  - No temperature measurements")
        print("  - No core type classification")
        print("  - Will need column density map for basic analysis")
        print("="*70)

    print("\n" + "="*70)
    print("Parsing complete!")
    print("="*70)
