#!/usr/bin/env python3
"""
Parse HGBS OrionB Core Catalog

OrionB uses numeric core types (1=starless, 2=prestellar, 3=protostellar)
instead of text labels like Aquila.

Author: ASTRA Discovery System
Date: 19 April 2026
"""

import numpy as np


def parse_orionb_catalog(filename):
    """
    Parse the HGBS OrionB derived core catalog.

    Returns list of core dictionaries with properties.
    """
    cores = []

    with open(filename, 'r', encoding='latin-1') as f:
        lines = f.readlines()

    # Find the header line
    header_idx = None
    for i, line in enumerate(lines):
        if 'runNO' in line and 'Core_name' in line:
            header_idx = i
            break

    if header_idx is None:
        print("Could not find header line")
        return []

    # Data starts 2 lines after header (header + separator + data)
    data_start = header_idx + 2

    # Core type mapping for OrionB
    core_type_map = {
        '1': 'starless',
        '2': 'prestellar',
        '3': 'protostellar'
    }

    for line in lines[data_start:]:
        line = line.strip()
        if not line:
            continue

        # Split by whitespace and parse
        parts = line.split()

        # Skip lines that don't have enough data
        if len(parts) < 13:
            continue

        # First part should be a number (runNO)
        try:
            run_no = int(parts[0])
        except ValueError:
            continue

        # Parse the data based on OrionB format
        # Format: runNO Core_name RA Dec R_core_dec R_core_obs M_core M_err T_dust T_err N_h2_peak N_h2_ave_obs N_h2_ave_dec nh2_peak nh2_ave_obs nh2_ave_deconv alpha_BE Core_type Comments
        # Positions: 0      1         2   3   4           5           6       7      8       9      10          11              12              13        14            15              16       17
        try:
            # Get core type from numeric value (position 17)
            core_type_code = parts[17] if len(parts) > 17 else '1'
            core_type = core_type_map.get(core_type_code.strip(), 'unknown')

            # Get alpha_BE (position 16)
            alpha_be = None
            if len(parts) > 16:
                try:
                    alpha_val = float(parts[16])
                    if 0 < alpha_val < 1000:
                        alpha_be = alpha_val
                except ValueError:
                    pass

            core = {
                'run_number': int(parts[0]),
                'name': parts[1],
                'ra': parts[2],
                'dec': parts[3],
                'radius_deconv': float(parts[4]),
                'radius_obs': float(parts[5]),
                'mass': float(parts[6]),
                'mass_error': float(parts[7]),
                'temp': float(parts[8]),
                'temp_error': float(parts[9]),
                'nh2_peak': float(parts[10]),
                'nh2_ave': float(parts[11]),
                'nh2_ave_deconv': float(parts[12]) if len(parts) > 12 and is_float(parts[12]) else None,
                'alpha_be': alpha_be,
                'type': core_type
            }

        except (ValueError, IndexError) as e:
            # Skip lines with parsing errors
            continue

        cores.append(core)

    return cores


def is_float(s):
    """Check if string can be converted to float."""
    try:
        float(s)
        return True
    except ValueError:
        return False


def main():
    """Test the parser."""
    import sys
    if len(sys.argv) < 2:
        print("Usage: python parse_orionb_catalog.py <catalog_file>")
        sys.exit(1)

    filename = sys.argv[1]
    cores = parse_orionb_catalog(filename)

    print(f"Parsed {len(cores)} cores from {filename}")

    if len(cores) > 0:
        print("\nSample cores:")
        for core in cores[:5]:
            print(f"  {core['name']}: M={core['mass']:.3f} Msun, T={core['temp']:.1f} K, type={core['type']}")

        # Print statistics
        types = {}
        for core in cores:
            ctype = core.get('type', 'unknown')
            types[ctype] = types.get(ctype, 0) + 1

        print(f"\nCore type distribution:")
        for ctype, count in types.items():
            print(f"  {ctype}: {count}")


if __name__ == '__main__':
    main()
