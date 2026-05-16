#!/usr/bin/env python3
"""
HGBS Taurus (L1495) Core Catalog Parser - FIXED

Author: ASTRA Discovery System
Date: 19 April 2026
"""

import numpy as np

def parse_taurus_catalog(filename):
    """Parse the Taurus L1495 derived core catalog (FIXED)"""
    cores = []

    with open(filename, 'r', encoding='latin-1') as f:
        for line_num, line in enumerate(f):
            line = line.strip()

            # Skip header lines
            if line_num < 35:
                continue

            # Skip empty lines or comment lines
            if not line or line.startswith('!') or line.startswith('|'):
                continue

            # Parse data line - use regex to handle the space-separated RA/Dec
            import re
            # Pattern: matches lines starting with number, followed by name, then RA (HH MM SS.SS), then Dec
            # Format: "     1  040924.1+284723   04 09 24.10   +28 47 23 ..."
            match = re.match(r'\s*(\d+)\s+(\S+)\s+(\d+)\s+(\d+)\s+([\d\.]+)\s+([\+\-]?\d+)\s+(\d+)', line)
            if match:
                core = parse_line_fixed(line)
                if core:
                    cores.append(core)

    return cores

def parse_line_fixed(line):
    """Parse a single line from the catalog (FIXED for RA/Dec format)."""
    try:
        # Core type mapping
        core_type_map = {
            '1': 'starless',
            '2': 'prestellar',
            '3': 'prestellar_candidate',
            '4': 'protostellar'
        }

        # Split the line
        parts = line.split()

        # Extract core number
        core_id = int(parts[0])

        # Core name
        core_name = parts[1]

        # RA parsing - columns 3, 4, 5 (HH MM SS.SS)
        ra_h = parts[2]
        ra_m = parts[3]
        ra_s = parts[4]
        ra_str = f"{ra_h}:{ra_m}:{ra_s}"

        # Dec parsing - columns 6, 7, 8 (+/- DD MM SS)
        dec_sign = parts[5]
        dec_d = parts[6]
        dec_m = parts[7]
        dec_s = parts[8]
        dec_str = f"{dec_sign}{dec_d}:{dec_m}:{dec_s}"

        # Core properties - positions after splitting:
        # 9=R_obs, 10=R_deconv, 11=Mass, 12=Mass_err,
        # 13=Temp, 14=Temp_err, 15=Nh2_peak, 16=Nh2_ave_obs,
        # 17=Nh2_ave_deconv, 18=nh2_peak_vol, 19=nh2_ave_obs_vol,
        # 20=nh2_ave_deconv_vol, 21=alpha_BE, 22=core_type

        mass = float(parts[11]) if len(parts) > 11 else 0.0
        mass_err = float(parts[12]) if len(parts) > 12 else 0.0
        temp = float(parts[13]) if len(parts) > 13 else 0.0
        nh2_peak = float(parts[15]) if len(parts) > 15 else 0.0
        alpha_be = float(parts[21]) if len(parts) > 21 else None

        # Core type (column 22, last part)
        core_type_code = parts[22] if len(parts) > 22 else '1'
        core_type = core_type_map.get(core_type_code.strip(), 'unknown')

        core = {
            'id': core_id,
            'name': core_name,
            'ra': ra_str,
            'dec': dec_str,
            'mass': mass,
            'mass_err': mass_err,
            'temp': temp,
            'nh2_peak': nh2_peak,
            'alpha_be': alpha_be,
            'type': core_type
        }

        return core

    except (ValueError, IndexError) as e:
        print(f"Warning: Failed to parse line: {e}")
        return None

if __name__ == '__main__':
    # Test the parser
    catalog_file = '/Users/gjw255/astrodata/SWARM/ASTRA/HGBS_TAURUS/HGBS_taurusL1495_derived_core_catalog.txt'

    print("Parsing Taurus catalog (FIXED)...")
    cores = parse_taurus_catalog(catalog_file)

    print(f"\nParsed {len(cores)} cores")

    if cores:
        # Test coordinate conversion
        from astropy.coordinates import SkyCoord
        from astropy import units as u

        print("\nTesting coordinate conversion (first 3 cores)...")
        for i, core in enumerate(cores[:3]):
            try:
                coord = SkyCoord(ra=core['ra'], dec=core['dec'], unit=(u.hourangle, u.deg))
                print(f"  {i+1}. {core['name']}: RA={core['ra']}, Dec={core['dec']}, "
                     f"Coord=({coord.ra.deg:.6f}, {coord.dec.deg:.6f})")
            except Exception as e:
                print(f"  {i+1}. {core['name']}: ERROR - {e}")

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
            print(f"\nMass statistics [Msun] (N={len(masses)}):")
            print(f"  Range: {np.min(masses):.3f} - {np.max(masses):.3f}")
            print(f"  Median: {np.median(masses):.3f}")
