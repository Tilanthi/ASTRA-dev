#!/usr/bin/env python3
"""
HGBS Perseus Core Catalog Parser

Parses the Perseus core catalog which has a pipe-delimited format
with text core type descriptions.

Author: ASTRA Discovery System
Date: 19 April 2026
"""

import numpy as np

def parse_perseus_catalog(filename):
    """
    Parse the Perseus derived core catalog.

    Format: Pipe-delimited with 19 columns
    Core types: "starless", "prestellar", "protostellar"

    Returns:
        List of dictionaries containing core properties
    """
    cores = []

    with open(filename, 'r', encoding='latin-1') as f:
        for line in f:
            line = line.strip()

            # Skip header lines
            if not line or line.startswith('|') or line.startswith('-'):
                continue

            # Parse data line - split by pipe
            parts = line.split('|')
            if len(parts) < 15:
                continue

            # Extract data from the columns
            try:
                # Column 1: runNO
                run_no = parts[1].strip() if len(parts) > 1 else ''
                if not run_no.isdigit():
                    continue

                # Column 2: Core_name
                core_name = parts[2].strip() if len(parts) > 2 else ''

                # Column 3: RA_2000 (h:m:ss)
                ra = parts[3].strip() if len(parts) > 3 else ''
                # Convert to standard format with colons
                ra = ra.replace(' ', ':')

                # Column 4: Dec_2000 (d:m:s)
                dec = parts[4].strip() if len(parts) > 4 else ''

                # Column 5: R_core (deconvolved)
                r_deconv = parts[5].strip() if len(parts) > 5 else ''
                r_obs = parts[6].strip() if len(parts) > 6 else ''

                # Column 7: M_core
                mass_str = parts[7].strip() if len(parts) > 7 else ''
                mass = float(mass_str.split()[0]) if mass_str else 0.0

                # Column 9: T_dust
                temp_str = parts[9].strip() if len(parts) > 9 else ''
                temp = float(temp_str.split()[0]) if temp_str else 0.0

                # Column 11: Nh2_peak
                nh2_str = parts[11].strip() if len(parts) > 11 else ''
                nh2_peak = float(nh2_str) if nh2_str else 0.0

                # Column 17: alpha_BE
                alpha_str = parts[17].strip() if len(parts) > 17 else ''
                alpha_be = float(alpha_str) if alpha_str else None

                # Column 18: Core_type
                core_type = parts[18].strip() if len(parts) > 18 else 'unknown'

                # Clean up core type
                if 'prestellar' in core_type.lower():
                    core_type = 'prestellar'
                elif 'protostellar' in core_type.lower():
                    core_type = 'protostellar'
                elif 'starless' in core_type.lower():
                    core_type = 'starless'
                else:
                    core_type = 'unknown'

                core = {
                    'id': int(run_no),
                    'name': core_name,
                    'ra': ra,
                    'dec': dec,
                    'mass': mass,
                    'temp': temp,
                    'nh2_peak': nh2_peak,
                    'alpha_be': alpha_be,
                    'type': core_type
                }

                cores.append(core)

            except (ValueError, IndexError) as e:
                continue

    return cores

if __name__ == '__main__':
    # Test the parser
    catalog_file = '/Users/gjw255/astrodata/SWARM/ASTRA/HGBS_PERSEUS/HGBS_PERSEUS/HGBS_perseus_derived_core_catalog.txt'

    print("Parsing Perseus catalog...")
    cores = parse_perseus_catalog(catalog_file)

    print(f"\nParsed {len(cores)} cores")

    if cores:
        # Print first few cores
        print("\nFirst 5 cores:")
        for i, core in enumerate(cores[:5]):
            print(f"  {i+1}. {core['name']}: M={core['mass']:.3f} Msun, T={core['temp']:.1f} K, type={core['type']}")

        # Count core types
        type_counts = {}
        for core in cores:
            ctype = core['type']
            type_counts[ctype] = type_counts.get(ctype, 0) + 1

        print("\nCore type distribution:")
        for ctype, count in type_counts.items():
            print(f"  {ctype}: {count} ({100*count/len(cores):.1f}%)")

        # Mass statistics
        masses = [c['mass'] for c in cores if c['mass'] > 0]
        if masses:
            print(f"\nMass statistics:")
            print(f"  Range: {np.min(masses):.3f} - {np.max(masses):.3f} Msun")
            print(f"  Median: {np.median(masses):.3f} Msun")
