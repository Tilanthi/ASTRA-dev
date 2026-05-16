#!/usr/bin/env python3
"""
HGBS Taurus (L1495) Core Catalog Parser - Final Fixed Version

Author: ASTRA Discovery System
Date: 19 April 2026
"""

import numpy as np
from astropy.coordinates import SkyCoord
from astropy import units as u

def parse_taurus_catalog(filename):
    """Parse the Taurus L1495 derived core catalog (FINAL FIXED)"""
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

            # Parse data line
            # Format: "     1  040924.1+284723   04 09 24.10   +28 47 23 ..."
            parts = line.split()
            if len(parts) >= 22 and parts[0].isdigit():
                core = parse_line_final(parts, line_num, filename)
                if core:
                    cores.append(core)

    return cores

def parse_line_final(parts, line_num, filename):
    """Parse a single line from the catalog (FINAL FIXED for RA/Dec)."""
    try:
        # Core type mapping
        core_type_map = {
            '1': 'starless',
            '2': 'prestellar',
            '3': 'prestellar_candidate',
            '4': 'protostellar'
        }

        # Extract values by position
        # [0]=Source_number, [1]=Name,
        # [2]=RA_hour, [3]=RA_min, [4]=RA_sec,
        # [5]=Dec_sign, [6]=Dec_deg, [7]=Dec_min, [8]=Dec_sec
        # ... and so on

        # Fix RA format: "04 09 24.10" -> "04:09:24.10"
        ra_h = parts[2]
        ra_m = parts[3]
        ra_s = parts[4]
        ra_str = f"{ra_h}:{ra_m}:{ra_s}"

        # Fix Dec format: "+28 47 23" -> "+28:47:23"
        dec_sign = parts[5]
        dec_deg = parts[6]
        dec_min = parts[7]
        dec_sec = parts[8]
        dec_str = f"{dec_sign}{dec_deg}:{dec_min}:{dec_sec}"

        # Test coordinate conversion
        try:
            coord = SkyCoord(ra=ra_str, dec=dec_str, unit=(u.hourangle, u.deg))
            ra_deg = coord.ra.deg
            dec_deg = coord.dec.deg
        except Exception as e:
            print(f"Line {line_num}: Coordinate conversion failed: {e}")
            print(f"  RA: '{ra_str}', Dec: '{dec_str}'")
            return None

        # Core properties (adjusted positions):
        # 11=Mass, 13=Temp, 15=Nh2_peak, 21=alpha_BE, 22=core_type
        mass = float(parts[11]) if len(parts) > 11 else 0.0
        temp = float(parts[13]) if len(parts) > 13 else 0.0
        nh2_peak = float(parts[15]) if len(parts) > 15 else 0.0
        alpha_be = float(parts[21]) if len(parts) > 21 else None

        # Core type (column 22)
        core_type_code = parts[22] if len(parts) > 22 else '1'
        core_type = core_type_map.get(core_type_code.strip(), 'unknown')

        core = {
            'id': int(parts[0]),
            'name': parts[1],
            'ra': ra_str,
            'dec': dec_str,
            'ra_deg': ra_deg,
            'dec_deg': dec_deg,
            'mass': mass,
            'temp': temp,
            'nh2_peak': nh2_peak,
            'alpha_be': alpha_be,
            'type': core_type
        }

        return core

    except (ValueError, IndexError) as e:
        print(f"Warning: Failed to parse line {line_num}: {e}")
        return None

if __name__ == '__main__':
    # Test the parser
    catalog_file = '/Users/gjw255/astrodata/SWARM/ASTRA/HGBS_TAURUS/HGBS_taurusL1495_derived_core_catalog.txt'

    print("Parsing Taurus catalog (FINAL FIXED)...")
    cores = parse_taurus_catalog(catalog_file)

    print(f"\nParsed {len(cores)} cores")

    if cores:
        print("\nFirst 5 cores:")
        for i, core in enumerate(cores[:5]):
            print(f"  {i+1}. {core['name']}: M={core['mass']:.3f} Msun, T={core['temp']:.1f} K, "
                 f"RA={core['ra']}, Dec={core['dec']}")

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
