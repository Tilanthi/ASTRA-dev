#!/usr/bin/env python3
"""
HGBS CRA (Corona Australis) Core Catalog Parser

Format: Space-separated with numeric core type codes
Similar to Taurus format

Author: ASTRA Discovery System
Date: 22 April 2026
"""

import numpy as np

def parse_cra_catalog(filename):
    """Parse the CRA derived core catalog."""
    cores = []

    print(f"Opening catalog file: {filename}")
    with open(filename, 'r', encoding='latin-1') as f:
        lines = f.readlines()

    print(f"Total lines in file: {len(lines)}")

    # Find data start (after header with column descriptions)
    data_start = None
    for i, line in enumerate(lines):
        if line.strip().startswith('   (1)'):
            data_start = i + 2  # Skip the separator line too
            break

    if data_start is None:
        # Alternative: look for lines starting with spaces and then a number
        for i, line in enumerate(lines):
            stripped = line.lstrip()
            if stripped and stripped[0].isdigit() and len(line.split()) >= 15:
                data_start = i
                break

    if data_start is None:
        print("Could not find data start")
        return cores

    for line_num, line in enumerate(lines[data_start:], start=data_start):
        line = line.strip()

        # Skip empty lines or comment lines
        if not line or line.startswith('!') or line.startswith('|'):
            continue

        # Parse data line
        parts = line.split()
        if len(parts) >= 18 and parts[0].isdigit():
            core = parse_line(parts, line_num)
            if core:
                cores.append(core)

    return cores


def parse_line(parts, line_num):
    """Parse a single line from the CRA catalog."""
    try:
        # Core type mapping for CRA
        # -1=tentative additional candidate, 1=unbound starless, 2=prestellar,
        # 3=candidate prestellar, 4=dense core with embedded protostar
        core_type_map = {
            '-1': 'starless',
            '1': 'starless',
            '2': 'prestellar',
            '3': 'prestellar_candidate',
            '4': 'protostellar'
        }

        # Extract values
        core_id = int(parts[0])
        core_name = parts[1]

        # RA: columns 2, 3, 4 -> "18 57 52.59"
        ra_h = parts[2]
        ra_m = parts[3]
        ra_s = parts[4]

        # Dec: columns 5, 6, 7 -> "-37 14 41.2"
        dec_sign_deg = parts[5]
        dec_m = parts[6]
        dec_s = parts[7]

        # Extract sign and degrees from column 5
        if dec_sign_deg.startswith('-'):
            dec_sign = '-'
            dec_d = dec_sign_deg[1:]
        else:
            dec_sign = '+'
            dec_d = dec_sign_deg[1:] if dec_sign_deg.startswith('+') else dec_sign_deg

        # Convert to decimal degrees
        ra_hours = float(ra_h) + float(ra_m)/60.0 + float(ra_s)/3600.0
        ra_deg = ra_hours * 15.0

        dec_deg_val = abs(float(dec_d)) + float(dec_m)/60.0 + float(dec_s)/3600.0
        if dec_sign == '-':
            dec_deg_val = -dec_deg_val

        # Create string representations
        ra_str = f"{ra_h}:{ra_m}:{ra_s}"
        dec_str = f"{dec_sign}{dec_d}:{dec_m}:{dec_s}"

        # Physical properties (adjust positions based on CRA format)
        # R_deconv, R_obs, M_core, M_err, T_dust, T_err,
        # Nh2_peak, Nh2_ave_obs, Nh2_ave_deconv, nh2_peak_vol, nh2_ave_obs_vol, nh2_ave_deconv_vol, alpha_BE, core_type
        mass = float(parts[9]) if len(parts) > 9 else 0.0
        mass_err = float(parts[10]) if len(parts) > 10 else 0.0
        temp = float(parts[11]) if len(parts) > 11 else 0.0
        temp_err = float(parts[12]) if len(parts) > 12 else 0.0
        nh2_peak = float(parts[13]) if len(parts) > 13 else 0.0
        nh2_ave_obs = float(parts[14]) if len(parts) > 14 else 0.0
        alpha_be = float(parts[17]) if len(parts) > 17 else None

        # Core type (column 19, index 21) - can be -1, 1, 2, 3, 4
        core_type_code = str(parts[21]).strip() if len(parts) > 21 else '1'
        if core_type_code in core_type_map:
            core_type = core_type_map[core_type_code]
        else:
            # Try extracting just the numeric part
            numeric_part = ''.join(c for c in core_type_code if c.isdigit() or c == '-')
            if numeric_part in core_type_map:
                core_type = core_type_map[numeric_part]
            else:
                core_type = 'unknown'

        core = {
            'id': core_id,
            'name': core_name,
            'ra': ra_str,
            'dec': dec_str,
            'ra_deg': ra_deg,
            'dec_deg': dec_deg_val,
            'mass': mass,
            'mass_err': mass_err,
            'temp': temp,
            'temp_err': temp_err,
            'nh2_peak': nh2_peak,
            'nh2_ave_obs': nh2_ave_obs,
            'alpha_be': alpha_be,
            'type': core_type
        }

        return core

    except (ValueError, IndexError) as e:
        print(f"Warning: Failed to parse line {line_num}: {e}")
        return None


if __name__ == '__main__':
    catalog_file = '/Users/gjw255/astrodata/SWARM/ASTRA/HGBS_CRA/HGBS_craNS_derived_core_catalog.txt'

    print("="*70)
    print("Parsing CRA Core Catalog")
    print("="*70)

    cores = parse_cra_catalog(catalog_file)

    print(f"\nSuccessfully parsed {len(cores)} cores")

    if cores:
        print("\n" + "="*70)
        print("First 5 cores:")
        print("="*70)
        for i, core in enumerate(cores[:5]):
            print(f"\n  {i+1}. {core['name']}")
            print(f"     RA: {core['ra']} = {core['ra_deg']:.6f}°")
            print(f"     Dec: {core['dec']} = {core['dec_deg']:.6f}°")
            print(f"     Mass: {core['mass']:.3f} Msun, Type: {core['type']}")

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
            print(f"  Range: {np.min(masses):.3f} - {np.max(masses):.3f}")
            print(f"  Median: {np.median(masses):.3f}")
            print(f"  Mean: {np.mean(masses):.3f}")

    print("\n" + "="*70)
    print("Parsing complete!")
    print("="*70)
