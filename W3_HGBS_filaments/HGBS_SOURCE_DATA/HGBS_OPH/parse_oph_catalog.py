#!/usr/bin/env python3
"""
HGBS Ophiuchus Core Catalog Parser

Parses the Ophiuchus core catalog which has a pipe-delimited format
with text core type descriptions.

Author: ASTRA Discovery System
Date: 19 April 2026
"""

import numpy as np
import re

def parse_oph_catalog(filename):
    """
    Parse the Ophiuchus derived core catalog.

    Format: Pipe-delimited (|)
    Core types: "starless", "prestellar", "protostellar"
    Some entries have additional notes like "prestellar tentative bound"

    Returns:
        List of dictionaries containing core properties
    """
    cores = []

    with open(filename, 'r', encoding='latin-1') as f:
        for line in f:
            line = line.strip()

            # Skip empty lines or comment lines
            if not line or line.startswith('|') and 'runNO' in line:
                continue
            if line.startswith('|'):
                continue
            if not line or line[0].isdigit() == False:
                # Check if it's a data line
                if '   ' in line and ':' in line:
                    pass  # Might be data
                else:
                    continue

            # Parse data line (space-separated, but need to handle RA/Dec)
            core = parse_oph_line(line)
            if core:
                cores.append(core)

    return cores

def parse_oph_line(line):
    """Parse a single line from the catalog."""
    try:
        # The format is irregular - need to parse carefully
        # Pattern: runNO  Core_name  RA(h:m:s)  Dec(d:m:s)  R_deconv  R_obs  M  M_err  T  T_err  Nh2_peak  Nh2_ave_obs  Nh2_ave_deconv  alpha_BE  core_type

        # Split by whitespace but preserve quoted strings
        parts = line.split()

        if len(parts) < 10:
            return None

        # Extract values
        run_no = parts[0]
        core_name = parts[1]

        # RA and Dec are in format like "16:20:35.20" and "-23:17:21.4"
        ra = parts[2] if len(parts) > 2 else '00:00:00'
        dec = parts[3] if len(parts) > 3 else '+00:00:00'

        # Sizes (deconvolved and observed)
        r_deconv = float(parts[4]) if len(parts) > 4 else 0.0
        r_obs = float(parts[5]) if len(parts) > 5 else 0.0

        # Mass and error
        mass = float(parts[6]) if len(parts) > 6 else 0.0
        mass_err = float(parts[7]) if len(parts) > 7 else 0.0

        # Temperature and error
        temp = float(parts[8]) if len(parts) > 8 else 0.0
        temp_err = float(parts[9]) if len(parts) > 9 else 0.0

        # Column densities
        nh2_peak = float(parts[10]) if len(parts) > 10 else 0.0
        nh2_ave_obs = float(parts[11]) if len(parts) > 11 else 0.0
        nh2_ave_deconv = float(parts[12]) if len(parts) > 12 else 0.0

        # Bonnor-Ebert ratio
        alpha_be = float(parts[13]) if len(parts) > 13 else None

        # Core type - last part, may have spaces
        # Need to find where the type starts (after alpha_BE)
        if len(parts) > 14:
            # Join remaining parts as core type
            core_type_parts = []
            for i in range(14, len(parts)):
                part = parts[i]
                # Skip numeric values that might be extra columns
                if part.replace('.', '').replace('+', '').replace('-', '').replace('e', '').replace('E', '').isdigit():
                    continue
                core_type_parts.append(part)

            core_type = ' '.join(core_type_parts).strip()
        else:
            core_type = 'unknown'

        # Clean up core type
        if 'starless' in core_type.lower():
            core_type = 'starless'
        elif 'prestellar' in core_type.lower():
            core_type = 'prestellar'
        elif 'protostellar' in core_type.lower():
            core_type = 'protostellar'
        else:
            core_type = 'unknown'

        core = {
            'id': int(run_no),
            'name': core_name,
            'ra': ra,
            'dec': dec,
            'mass': mass,
            'mass_err': mass_err,
            'temp': temp,
            'nh2_peak': nh2_peak,
            'alpha_be': alpha_be,
            'type': core_type
        }

        return core

    except (ValueError, IndexError) as e:
        # print(f"Warning: Failed to parse line: {e}")
        return None

if __name__ == '__main__':
    # Test the parser
    catalog_file = '/Users/gjw255/astrodata/SWARM/ASTRA/HGBS_OPH/HGBS_ophiuchus_derived_core_catalog.txt'

    print("Parsing Ophiuchus catalog...")
    cores = parse_oph_catalog(catalog_file)

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
