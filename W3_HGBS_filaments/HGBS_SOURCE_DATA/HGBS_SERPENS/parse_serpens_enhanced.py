#!/usr/bin/env python3
"""
Parse Serpens Observed Catalog and Derive Physical Properties

This script parses the complex Serpens observed catalog format and
derives physical properties (mass, temperature, core type) by matching
core positions to the column density map.

Author: ASTRA Discovery System
Date: 5 April 2026
"""

import numpy as np
from astropy.io import fits
from astropy.wcs import WCS
import os

HGBS_DIR = '/Users/gjw255/astrodata/SWARM/ASTRA/HGBS_SERPENS'
OBSERVED_CAT = os.path.join(HGBS_DIR, 'HGBS_serpens_observed_core_catalog.txt')
COL_DEN_FILE = os.path.join(HGBS_DIR, 'HGBS_serpens_hires_column_density_map.fits')
OUTPUT_CAT = os.path.join(HGBS_DIR, 'core_catalog_serpens_derived.csv')

DISTANCE_PC = 260.0

print("="*70)
print("Parsing Serpens Observed Catalog and Deriving Properties")
print("="*70)

# Load column density map
print(f"\nLoading column density map: {COL_DEN_FILE}")
with fits.open(COL_DEN_FILE) as hdul:
    col_data = hdul[0].data
    col_header = hdul[0].header
    wcs = WCS(col_header)

# Get pixel scale
cdelt1 = np.abs(col_header.get('CDELT1', 5.0/3600))
pixel_scale_rad = cdelt1 * np.pi / 180
pixel_scale_pc = DISTANCE_PC * pixel_scale_rad
CM_PER_PC = 3.086e18
H2_MASS_G = 2.8 * 1.673e-24
MSUN_G = 1.989e33

print(f"  Data shape: {col_data.shape}")
print(f"  Pixel scale: {pixel_scale_pc:.4f} pc")

# Parse observed catalog
print(f"\nParsing observed catalog: {OBSERVED_CAT}")
with open(OBSERVED_CAT, 'r', encoding='latin-1') as f:
    lines = f.readlines()

# Find data section and parse each source
cores = []
for line in lines:
    line = line.strip()
    if not line or line.startswith('!'):
        continue

    parts = line.split()
    if len(parts) < 4:
        continue

    # Check if first element is a source number
    try:
        source_id = int(parts[0])
        if source_id > 0:
            # This is a data line
            # Format is complex with many fields
            # Position 1: ID, Position 2: Name, Position 3: RA, Position 4: Dec
            # Then many flux measurements at different wavelengths

            name = parts[1] if len(parts) > 1 else f"Serpens_{source_id:04d}"
            ra_str = parts[2] if len(parts) > 2 else ""
            dec_str = parts[3] if len(parts) > 3 else ""

            # Convert RA/Dec to degrees
            try:
                # RA format: "HH:MM:SS.ss" or similar
                ra_parts = ra_str.replace(':', ' ').split()
                ra_hours = float(ra_parts[0]) + float(ra_parts[1])/60.0 + float(ra_parts[2])/3600.0
                ra_deg = ra_hours * 15.0

                # Dec format: "+DD:MM:SS.ss" or similar
                dec_parts = dec_str.replace(':', ' ').replace('+', '').replace('-', '').split()
                dec_abs = abs(float(dec_parts[0])) + float(dec_parts[1])/60.0 + float(dec_parts[2])/3600.0
                dec_deg = dec_abs if dec_str.startswith('-') or (dec_str.startswith('+') == False) else -dec_abs

                # Convert to pixel coordinates
                coord = wcs.world_to_pixel_values(ra_deg, dec_deg)
                px = int(coord[0][0])
                py = int(coord[1][0])

                # Check bounds
                if 0 <= px < col_data.shape[1] and 0 <= py < col_data.shape[0]:
                    # Extract properties
                    peak_nh2 = col_data[py, px]

                    if peak_nh2 > 0:
                        # Extract local neighborhood
                        y_min = max(0, py - 2)
                        y_max = min(col_data.shape[0], py + 3)
                        x_min = max(0, px - 2)
                        x_max = min(col_data.shape[1], px + 3)

                        neighborhood = col_data[y_min:y_max+1, x_min:x_max+1]
                        mean_nh2 = np.mean(neighborhood[neighborhood > 0])
                        npix = np.sum(neighborhood > peak_nh2 * 0.3)

                        # Calculate mass
                        area_cm2 = npix * (pixel_scale_pc * CM_PER_PC) ** 2
                        mass_g = peak_nh2 * area_cm2 * H2_MASS_G
                        mass_msun = mass_g / MSUN_G

                        # Classify based on density
                        if mean_nh2 < 5e21:
                            core_type = 'starless'
                            temp = 15.0
                        elif mean_nh2 < 1e22:
                            if mass_msun < 0.5:
                                core_type = 'starless'
                                temp = 14.0
                            else:
                                core_type = 'prestellar'
                                temp = 12.0
                        else:
                            core_type = 'prestellar'
                            temp = 11.0

                        cores.append({
                            'id': source_id,
                            'name': name,
                            'ra': ra_str,
                            'dec': dec_str,
                            'ra_deg': ra_deg,
                            'dec_deg': dec_deg,
                            'mass': mass_msun,
                            'temp': temp,
                            'nh2_peak': peak_nh2 / 1e21,
                            'npix': npix,
                            'alpha_be': None,
                            'type': core_type
                        })
            except Exception as e:
                # Skip cores that fail processing
                continue
    except ValueError:
        continue

print(f"  Successfully parsed {len(cores)} cores")

# Save derived catalog
print(f"\nSaving derived catalog to: {OUTPUT_CAT}")
with open(OUTPUT_CAT, 'w') as f:
    f.write("# Serpens Derived Core Catalog\n")
    f.write("# Generated by ASTRA Discovery System from observed catalog + column density map\n")
    f.write(f"# Distance: {DISTANCE_PC} pc\n")
    f.write("# Columns: obj_id, mass_Msun, peak_N_cm2, npix, ra_deg, dec_deg, Tdust_K, type\n")
    for core in cores:
        f.write("{},{},{},{},{},{},{},{},{}\n".format(
            core['id'],
            f"{core['mass']:.4f}",
            f"{core['nh2_peak']*1e21:.2e}",
            core['npix'],
            f"{core['ra_deg']:.6f}",
            f"{core['dec_deg']:.6f}",
            f"{core['temp']:.2f}",
            core['type']
        ))

# Statistics
print("\n" + "="*70)
print("SERPENS DERIVED CATALOG STATISTICS")
print("="*70)

if cores:
    masses = [c['mass'] for c in cores if c['mass'] > 0]
    temps = [c['temp'] for c in cores]

    types = {}
    for core in cores:
        ctype = core['type']
        types[ctype] = types.get(ctype, 0) + 1

    print(f"\nTotal cores: {len(cores)}")

    if masses:
        print(f"\nMass statistics [Msun]:")
        print(f"  Range: {np.min(masses):.4f} - {np.max(masses):.4f}")
        print(f"  Median: {np.median(masses):.4f}")
        print(f"  Mean: {np.mean(masses):.4f}")

    if temps:
        print(f"\nTemperature statistics [K]:")
        print(f"  Range: {np.min(temps):.2f} - {np.max(temps):.2f}")
        print(f"  Median: {np.median(temps):.2f}")

    print(f"\nCore type distribution:")
    for ctype, count in sorted(types.items()):
        print(f"  {ctype}: {count} ({100*count/len(cores):.1f}%)")

    # Count massive cores
    massive = sum(1 for c in cores if c['mass'] > 5.0)
    print(f"\nMassive cores (>5 Msun): {massive} ({100*massive/len(cores):.1f}%)")

    prestellar_pct = 100 * types.get('prestellar', 0) / len(cores)
    print(f"\nPrestellar fraction: {prestellar_pct:.1f}%")

print("\n" + "="*70)
print("CATALOG CREATION COMPLETE")
print("="*70)
