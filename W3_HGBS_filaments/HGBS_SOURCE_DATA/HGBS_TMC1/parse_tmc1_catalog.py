#!/usr/bin/env python3
"""
HGBS TMC1 (Taurus Molecular Cloud 1) Core Catalog Parser

Format: Tab-separated with text-based core types
Uses colons for RA/Dec separation

Author: ASTRA Discovery System
Date: 22 April 2026
"""

import numpy as np

def parse_tmc1_catalog(filename):
    """Parse the TMC1 derived core catalog."""
    cores = []

    print(f"Opening catalog file: {filename}")
    with open(filename, 'r', encoding='latin-1') as f:
        lines = f.readlines()

    print(f"Total lines in file: {len(lines)}")

    # Find data start (skip header lines)
    data_start = None
    for i, line in enumerate(lines):
        if line.strip() and not line.startswith('!') and not line.startswith('|') and not line.startswith('#'):
            # Check if this looks like a data line
            parts = line.split()
            if len(parts) > 10 and parts[0].isdigit():
                data_start = i
                break

    if data_start is None:
        print("Could not find data start")
        return cores

    for line_num, line in enumerate(lines[data_start:], start=data_start):
        line = line.strip()

        # Skip empty lines or comment lines
        if not line or line.startswith('!') or line.startswith('|') or line.startswith('#'):
            continue

        # Parse data line (tab-separated or space-separated)
        parts = line.split()
        if len(parts) >= 12 and parts[0].replace('.', '').isdigit():
            core = parse_line(parts, line_num)
            if core:
                cores.append(core)

    return cores


def parse_line(parts, line_num):
    """Parse a single line from the TMC1 catalog."""
    try:
        # Core type mapping from text descriptions
        core_type_map = {
            'unbound starless': 'starless',
            'robust prestellar': 'prestellar',
            'protostellar': 'protostellar',
        }

        # Extract values
        # Format: [0]=ID, [1]=Name, [2]=RA, [3]=Dec, [4]=R_deconv, [5]=R_obs,
        # [6]=M_core, [7]=M_err, [8]=T_dust, [9]=T_err, [10]=Nh2_peak,
        # [11-16]=various densities, [17]=alpha_BE, [18]=core_type

        core_id = int(parts[0])
        core_name = parts[1]

        # RA and Dec are already in colon format: "04:33:03.26", "+26:01:50.7"
        ra_str = parts[2]
        dec_str = parts[3]

        # Convert to decimal degrees
        coord_parts = ra_str.split(':')
        ra_hours = float(coord_parts[0]) + float(coord_parts[1])/60.0 + float(coord_parts[2])/3600.0
        ra_deg = ra_hours * 15.0

        coord_parts = dec_str.split(':')
        dec_deg_val = abs(float(coord_parts[0])) + float(coord_parts[1])/60.0 + float(coord_parts[2])/3600.0
        if dec_str.startswith('-'):
            dec_deg_val = -dec_deg_val

        # Physical properties
        radius_deconv = float(parts[4]) if len(parts) > 4 else 0.0
        radius_obs = float(parts[5]) if len(parts) > 5 else 0.0
        mass = float(parts[6]) if len(parts) > 6 else 0.0
        mass_err = float(parts[7]) if len(parts) > 7 else 0.0
        temp = float(parts[8]) if len(parts) > 8 else 0.0
        temp_err = float(parts[9]) if len(parts) > 9 else 0.0
        nh2_peak = float(parts[10]) if len(parts) > 10 else 0.0

        # Find alpha_BE and core type at the end
        alpha_be = None
        core_type = 'unknown'

        for i in range(len(parts) - 1, -1, -1):
            part = parts[i].lower()
            if 'unbound starless' in part:
                core_type = 'starless'
            elif 'robust prestellar' in part:
                core_type = 'prestellar'
            elif 'protostellar' in part:
                core_type = 'protostellar'
            elif 'prestellar' in part and core_type == 'unknown':
                core_type = 'prestellar'

            # Try to parse as alpha_BE
            try:
                val = float(part)
                if 0 < val < 1000 and alpha_be is None:
                    alpha_be = val
            except:
                pass

        core = {
            'id': core_id,
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
            'alpha_be': alpha_be,
            'type': core_type
        }

        return core

    except (ValueError, IndexError) as e:
        print(f"Warning: Failed to parse line {line_num}: {e}")
        return None


if __name__ == '__main__':
    catalog_file = '/Users/gjw255/astrodata/SWARM/ASTRA/HGBS_TMC1/HGBS_taurusTMC1_derived_core_catalog.txt'

    print("="*70)
    print("Parsing TMC1 Core Catalog")
    print("="*70)

    cores = parse_tmc1_catalog(catalog_file)

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
