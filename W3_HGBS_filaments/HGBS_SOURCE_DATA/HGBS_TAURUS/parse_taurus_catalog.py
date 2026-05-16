#!/usr/bin/env python3
"""
HGBS Taurus (L1495) Core Catalog Parser - Fixed Coordinate Conversion

This parser correctly handles the Taurus catalog format where RA/Dec are
space-separated: "04 09 24.10" for RA and "+28 47 23" for Dec.

Column structure (when split by whitespace):
[0]=Source_number, [1]=Name_compact,
[2]=RA_hour, [3]=RA_min, [4]=RA_sec,
[5]=Dec_sign_deg (e.g. "+28"), [6]=Dec_min, [7]=Dec_sec,
[8]=R_obs, [9]=R_deconv,
[10]=Mass, [11]=Mass_err,
[12]=Temp, [13]=Temp_err,
[14]=Nh2_peak, [15]=Nh2_ave_obs, [16]=Nh2_ave_deconv,
[17]=nh2_peak_vol, [18]=nh2_ave_obs_vol, [19]=nh2_ave_deconv_vol,
[20]=alpha_BE, [21]=core_type

Author: ASTRA Discovery System
Date: 19 April 2026
"""

import numpy as np

def parse_taurus_catalog(filename):
    """Parse the Taurus L1495 derived core catalog."""
    cores = []

    print(f"Opening catalog file: {filename}")
    with open(filename, 'r', encoding='latin-1') as f:
        lines = f.readlines()

    print(f"Total lines in file: {len(lines)}")

    for line_num, line in enumerate(lines):
        line = line.strip()

        # Skip header lines (first 35 lines)
        if line_num < 35:
            continue

        # Skip empty lines or comment lines
        if not line or line.startswith('!') or line.startswith('|'):
            continue

        # Parse data line
        parts = line.split()
        if len(parts) >= 22 and parts[0].isdigit():
            core = parse_line(parts, line_num)
            if core:
                cores.append(core)

    return cores


def parse_line(parts, line_num):
    """Parse a single line from the Taurus catalog."""
    try:
        # Core type mapping
        core_type_map = {
            '1': 'starless',
            '2': 'prestellar',
            '3': 'prestellar_candidate',
            '4': 'protostellar'
        }

        # Basic identification
        core_id = int(parts[0])
        core_name = parts[1]

        # RA components: "04 09 24.10" -> indices 2, 3, 4
        ra_h = parts[2]
        ra_m = parts[3]
        ra_s = parts[4]

        # Dec components: "+28 47 23" -> indices 5, 6, 7
        # Note: Column 5 contains BOTH sign and degrees (e.g., "+28")
        dec_sign_deg = parts[5]  # e.g., "+28" or "-05"
        dec_m = parts[6]
        dec_s = parts[7]

        # Extract sign and degrees from column 5
        if dec_sign_deg.startswith('-'):
            dec_sign = '-'
            dec_d = dec_sign_deg[1:]  # Remove the minus sign
        else:
            dec_sign = '+'
            dec_d = dec_sign_deg[1:] if dec_sign_deg.startswith('+') else dec_sign_deg

        # Convert RA to decimal degrees manually
        # RA is in hours:minutes:seconds
        ra_hours = float(ra_h) + float(ra_m)/60.0 + float(ra_s)/3600.0
        ra_deg = ra_hours * 15.0  # 1 hour = 15 degrees

        # Convert Dec to decimal degrees manually
        # Dec is in degrees:arcminutes:arcseconds
        dec_deg_val = abs(float(dec_d)) + float(dec_m)/60.0 + float(dec_s)/3600.0
        if dec_sign == '-':
            dec_deg_val = -dec_deg_val

        # Create string representations for display
        ra_str = f"{ra_h}:{ra_m}:{ra_s}"
        dec_str = f"{dec_sign}{dec_d}:{dec_m}:{dec_s}"

        # Physical properties (corrected column indices)
        mass = float(parts[10]) if len(parts) > 10 else 0.0
        mass_err = float(parts[11]) if len(parts) > 11 else 0.0
        temp = float(parts[12]) if len(parts) > 12 else 0.0
        temp_err = float(parts[13]) if len(parts) > 13 else 0.0
        nh2_peak = float(parts[14]) if len(parts) > 14 else 0.0
        nh2_ave_obs = float(parts[15]) if len(parts) > 15 else 0.0
        alpha_be = float(parts[20]) if len(parts) > 20 else None

        # Core type
        core_type_code = parts[21] if len(parts) > 21 else '1'
        core_type = core_type_map.get(core_type_code.strip(), 'unknown')

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
        print(f"  Parts: {parts[:10]}")
        return None


if __name__ == '__main__':
    # Test the parser
    catalog_file = '/Users/gjw255/astrodata/SWARM/ASTRA/HGBS_TAURUS/HGBS_taurusL1495_derived_core_catalog.txt'

    print("="*70)
    print("Parsing Taurus L1495 Core Catalog")
    print("="*70)

    cores = parse_taurus_catalog(catalog_file)

    print(f"\nSuccessfully parsed {len(cores)} cores")

    if cores:
        print("\n" + "="*70)
        print("First 5 cores (verifying coordinate conversion):")
        print("="*70)
        for i, core in enumerate(cores[:5]):
            print(f"\n  {i+1}. {core['name']}")
            print(f"     RA: {core['ra']} = {core['ra_deg']:.6f}°")
            print(f"     Dec: {core['dec']} = {core['dec_deg']:.6f}°")
            print(f"     Mass: {core['mass']:.3f} Msun, Type: {core['type']}")

        # Coordinate validation
        print("\n" + "="*70)
        print("Coordinate validation:")
        print("="*70)
        ra_vals = [c['ra_deg'] for c in cores]
        dec_vals = [c['dec_deg'] for c in cores]
        print(f"  RA range: {np.min(ra_vals):.6f}° - {np.max(ra_vals):.6f}°")
        print(f"  Dec range: {np.min(dec_vals):.6f}° - {np.max(dec_vals):.6f}°")

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
