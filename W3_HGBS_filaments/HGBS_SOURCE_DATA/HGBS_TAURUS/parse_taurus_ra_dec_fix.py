#!/usr/bin/env python3
"""
HGBS Taurus (L1495) Core Catalog Parser - Corrected for RA/Dec

Author: ASTRA Discovery System
Date: 19 April 2026
"""

import numpy as np
from astropy.coordinates import SkyCoord
from astropy import units as u

def parse_taurus_catalog(filename):
    """Parse the Taurus L1495 derived core catalog with correct RA/Dec handling"""
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

            # Parse using whitespace
            parts = line.split()
            if len(parts) >= 22 and parts[0].isdigit():
                core = parse_line_corrected(parts)
                if core:
                    cores.append(core)

    return cores

def parse_line_corrected(parts):
    """Parse a line with correct RA/Dec format handling."""
    try:
        core_type_map = {
            '1': 'starless',
            '2': 'prestellar',
            '3': 'prestellar_candidate',
            '4': 'protostellar'
        }

        # Extract values
        core_id = int(parts[0])
        core_name = parts[1]

        # RA: columns 2, 3, 4 -> "04 09 24.10" -> "04:09:24.10"
        ra_h = parts[2]
        ra_m = parts[3]
        ra_s = parts[4]
        ra_str = f"{ra_h}:{ra_m}:{ra_s}"

        # Dec: columns 5, 6, 7, 8 -> "+28 47 23" -> "+28:47:23"
        dec_sign = parts[5]
        dec_deg = parts[6]  # This is degrees, not hours!
        dec_min = parts[7]
        dec_sec = parts[8]
        dec_str = f"{dec_sign}{dec_deg}:{dec_min}:{dec_sec}"

        # Try to parse with skycoord - treating Dec as degrees
        try:
            coord = SkyCoord(ra=ra_str, dec=dec_str, unit=(u.hourangle, u.deg))
            ra_deg = coord.ra.deg
            dec_deg = coord.dec.deg
        except Exception as e:
            # If that fails, try alternative format
            try:
                coord = SkyCoord(ra=ra_str, dec=dec_str, unit=(u.deg, u.deg))
                ra_deg = coord.ra.deg
                dec_deg = coord.dec.deg
            except:
                ra_deg = np.nan
                dec_deg = np.nan

        # Core properties
        mass = float(parts[11]) if len(parts) > 11 else 0.0
        temp = float(parts[13]) if len(parts) > 13 else 0.0
        nh2_peak = float(parts[15]) if len(parts) > 15 else 0.0
        alpha_be = float(parts[21]) if len(parts) > 21 else None

        # Core type (column 22)
        core_type_code = parts[22] if len(parts) > 22 else '1'
        core_type = core_type_map.get(core_type_code.strip(), 'unknown')

        core = {
            'id': core_id,
            'name': core_name,
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

    except Exception as e:
        print(f"Parse error (line {parts[0] if parts else '?'}): {e}")
        return None

if __name__ == '__main__':
    catalog_file = '/Users/gjw255/astrodata/SWARM/ASTRA/HGBS_TAURUS/HGBS_taurusL1495_derived_core_catalog.txt'

    print("Parsing Taurus catalog (corrected RA/Dec)...")
    cores = parse_taurus_catalog(catalog_file)

    print(f"\nParsed {len(cores)} cores")

    if cores:
        print("\nFirst 5 cores (RA, Dec in deg):")
        for i, core in enumerate(cores[:5]):
            print(f"  {i+1}. {core['name']}: M={core['mass']:.3f} Msun, "
                 f"RA={core['ra_deg']:.6f}°, Dec={core['dec_deg']:.6f}°")

        # Count core types
        type_counts = {}
        for core in cores:
            ctype = core['type']
            type_counts[ctype] = type_counts.get(ctype, 0) + 1

        print("\nCore type distribution:")
        for ctype, count in type_counts.items():
            print(f"  {ctype}: {count} ({100*count/len(cores):.1f}%)")
