#!/usr/bin/env python3
"""
Parse HGBS Perseus Core Catalog

The Perseus catalog has a pipe-delimited format with specific columns.

Author: ASTRA Discovery System
Date: 22 April 2026
"""

import numpy as np
import re


def parse_perseus_catalog(filename):
    """
    Parse the HGBS Perseus derived core catalog.

    Returns list of core dictionaries with properties.
    """
    cores = []

    with open(filename, 'r', encoding='latin-1') as f:
        lines = f.readlines()

    # Find the data start (after the separator line of dashes)
    data_start = None
    for i, line in enumerate(lines):
        if '|---' in line and i > 30:
            data_start = i + 1
            break

    if data_start is None:
        print("Could not find data start line")
        return cores

    for line in lines[data_start:]:
        line = line.strip()

        # Skip empty lines or lines that are clearly not data
        if not line or line.startswith('!'):
            continue

        # Parse pipe-delimited line
        # Data lines may or may not start with |
        if '|' in line:
            parts = [p.strip() for p in line.split('|')]
            parts = [p for p in parts if p]  # Remove empty parts
        else:
            # Fallback: split by whitespace
            parts = line.split()

        # Skip header lines or lines without enough data
        if len(parts) < 12:
            continue

        # First part should be a number (runNO)
        try:
            run_no = int(parts[0])
        except ValueError:
            continue

        # Parse based on column positions
        # [0]=runNO, [1]=Core_name, [2]=RA, [3]=Dec,
        # [4]=R_deconv, [5]=R_obs, [6]=M_core, [7]=M_err,
        # [8]=T_dust, [9]=T_err, [10]=Nh2_peak,
        # [11]=Nh2_ave_obs, [12]=Nh2_ave_deconv,
        # [13]=nh2_peak_vol, [14]=nh2_ave_obs_vol,
        # [15]=nh2_ave_deconv_vol, [16]=alpha_BE,
        # [17]=Core_type, [18]=Comments

        try:
            core_name = parts[1]
            ra_str = parts[2]
            dec_str = parts[3]

            # Convert RA/Dec to decimal degrees for consistency with Taurus parser
            coord_parts = ra_str.split(':')
            ra_hours = float(coord_parts[0]) + float(coord_parts[1])/60.0 + float(coord_parts[2])/3600.0
            ra_deg = ra_hours * 15.0

            coord_parts = dec_str.split(':')
            dec_deg_val = abs(float(coord_parts[0])) + float(coord_parts[1])/60.0 + float(coord_parts[2])/3600.0
            if dec_str.startswith('-'):
                dec_deg_val = -dec_deg_val

            radius_deconv = float(parts[4]) if is_float(parts[4]) else 0.0
            radius_obs = float(parts[5]) if is_float(parts[5]) else 0.0
            mass = float(parts[6]) if is_float(parts[6]) else 0.0
            mass_err = float(parts[7]) if is_float(parts[7]) else 0.0
            temp = float(parts[8]) if is_float(parts[8]) else 0.0
            temp_err = float(parts[9]) if is_float(parts[9]) else 0.0
            nh2_peak = float(parts[10]) if is_float(parts[10]) else 0.0
            nh2_ave_obs = float(parts[11]) if is_float(parts[11]) else 0.0
            nh2_ave_deconv = float(parts[12]) if len(parts) > 12 and is_float(parts[12]) else 0.0
            alpha_be = float(parts[16]) if len(parts) > 16 and is_float(parts[16]) else None

            # Core type
            core_type = 'unknown'
            if len(parts) > 17:
                ctype_str = parts[17].lower()
                if 'starless' in ctype_str:
                    core_type = 'starless'
                elif 'prestellar' in ctype_str:
                    core_type = 'prestellar'
                elif 'protostellar' in ctype_str:
                    core_type = 'protostellar'

            core = {
                'run_number': run_no,
                'name': core_name,
                'ra': ra_str,
                'dec': dec_str,
                'ra_deg': ra_deg,
                'dec_deg': dec_deg_val,
                'radius_deconv': radius_deconv,
                'radius_obs': radius_obs,
                'mass': mass,
                'mass_err': mass_err,
                'temp': temp,
                'temp_err': temp_err,
                'nh2_peak': nh2_peak,
                'nh2_ave_obs': nh2_ave_obs,
                'nh2_ave_deconv': nh2_ave_deconv,
                'alpha_be': alpha_be,
                'type': core_type
            }

            cores.append(core)

        except (ValueError, IndexError) as e:
            # Skip lines with parsing errors
            continue

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
        print("Usage: python parse_perseus_catalog.py <catalog_file>")
        sys.exit(1)

    filename = sys.argv[1]
    cores = parse_perseus_catalog(filename)

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
