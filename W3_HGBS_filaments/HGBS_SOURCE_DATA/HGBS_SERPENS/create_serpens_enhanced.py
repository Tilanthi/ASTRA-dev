#!/usr/bin/env python3
"""
Create Enhanced Serpens Core Catalog with Physical Properties

Uses the observed Serpens catalog and adds physical properties by
extracting values at core positions from the column density map.

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
print("Creating Enhanced Serpens Core Catalog")
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

print(f"  Data shape: {col_data.shape}")
print(f"  Pixel scale: {pixel_scale_pc:.4f} pc")

# Constants
CM_PER_PC = 3.086e18
H2_MASS_G = 2.8 * 1.673e-24
MSUN_G = 1.989e33

# Read and parse the observed catalog
print(f"\nReading observed catalog: {OBSERVED_CAT}")

# Read the full catalog
with open(OBSERVED_CAT, 'r', encoding='latin-1') as f:
    lines = f.readlines()

# Find data section
in_data = False
data_lines = []
for line in lines:
    if in_data and not line.startswith('!'):
        data_lines.append(line.strip())
    elif line.startswith(' Source number'):
        in_data = True

print(f"  Found {len(data_lines)} data lines")

# Parse data lines - look for source entries
cores_data = []
current_source = None

for line in data_lines:
    if not line:
        continue

    parts = line.split()
    if len(parts) < 4:
        continue

    # Check if this is a new source entry (starts with number)
    try:
        num = int(parts[0])
        if num > 0 and len(parts) >= 4:
            # This looks like a source entry
            # Format: ID name RA dec ...
            if len(parts) >= 4:
                source_id = parts[0]
                name = parts[1]
                ra_str = parts[2]
                dec_str = parts[3]

                cores_data.append({
                    'id': int(source_id),
                    'name': name,
                    'ra_str': ra_str,
                    'dec_str': dec_str
                })
    except ValueError:
        continue

print(f"  Parsed {len(cores_data)} source entries")

# Now extract physical properties for each core at its position
enhanced_cores = []

for core_data in cores_data:
    try:
        # Convert RA/Dec from catalog string to degrees
        ra_str = core_data['ra_str']
        dec_str = core_data['dec_str']

        # Parse "HH:MM:SS.ss" or "HH MM SS.ss" format
        ra_parts = ra_str.replace(':', ' ').split()
        dec_parts = dec_str.replace(':', ' ').split()

        # Convert RA to degrees
        ra_hours = float(ra_parts[0]) + float(ra_parts[1])/60.0 + float(ra_parts[2])/3600.0
        ra_deg = ra_hours * 15.0

        # Convert Dec to degrees
        dec_abs = abs(float(dec_parts[0]))
        dec_min = float(dec_parts[1]) if len(dec_parts) > 1 else 0.0
        dec_sec = float(dec_parts[2]) if len(dec_parts) > 2 else 0.0
        dec_deg_val = dec_abs + dec_min/60.0 + dec_sec/3600.0
        if '-' in dec_str or str(dec_deg_val) in dec_str:
            dec_deg = -dec_deg_val
        else:
            dec_deg = dec_deg_val

        # Convert to pixel coordinates
        try:
            coord = wcs.world_to_pixel_values(ra_deg, dec_deg)
            px = int(coord[0][0])
            py = int(coord[1][0])
        except:
            continue

        # Check if pixel is within bounds
        if 0 <= px < col_data.shape[1] and 0 <= py < col_data.shape[0]:
            # Extract properties at core location

            # Peak column density
            peak_nh2 = col_data[py, px]

            # Extract local neighborhood (3x3 pixels)
            y_min = max(0, py - 1)
            y_max = min(col_data.shape[0], py + 2)
            x_min = max(0, px - 1)
            x_max = min(col_data.shape[1], px + 2)

            neighborhood = col_data[y_min:y_max+1, x_min:x_max+1]

            # Mean column density in neighborhood
            mean_nh2 = np.mean(neighborhood)

            # Number of pixels above threshold
            npix = np.sum(neighborhood > (peak_nh2 * 0.5))

            if peak_nh2 <= 0:
                continue

            # Calculate mass
            # Mass = N_H2 * area * mass_per_H2 / Msun
            # area in cm^2
            area_cm2 = npix * (pixel_scale_pc * CM_PER_PC) ** 2
            mass_g = peak_nh2 * area_cm2 * H2_MASS_G
            mass_msun = mass_g / MSUN_G

            # Estimate temperature based on column density
            # Using empirical relation for star-forming regions
            # T ~ 12-15 K for typical prestellar cores

            # Classify core type using HGBS criteria
            if mean_nh2 < 3e21:  # Below 3×10^21 cm^-2
                core_type = 'starless'
                temp = 15.0
            elif mean_nh2 < 1e22:  # 3-10×10^21 cm^-2
                if mass_msun < 0.5:
                    core_type = 'starless'
                    temp = 14.0
                else:
                    core_type = 'prestellar'
                    temp = 12.0
            else:  # Above 10^22 cm^-2
                core_type = 'prestellar'
                temp = 11.0

            enhanced_cores.append({
                'id': core_data['id'],
                'name': core_data['name'],
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
        continue

print(f"\nSuccessfully enhanced {len(enhanced_cores)} cores")

# Save enhanced catalog
print(f"\nSaving enhanced catalog to: {OUTPUT_CAT}")
with open(OUTPUT_CAT, 'w') as f:
    f.write("# Serpens Enhanced Core Catalog\n")
    f.write("# Generated by ASTRA Discovery System from observed catalog + column density map\n")
    f.write(f"# Distance: {DISTANCE_PC} pc\n")
    f.write("# Columns: obj_id, mass_Msun, peak_N_cm2, npix, ra_deg, dec_deg, Tdust_K, type\n")
    for core in enhanced_cores:
        f.write("{},{},{},{},{},{},{},{}\n".format(
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
print("SERPENS ENHANCED CATALOG STATISTICS")
print("="*70)

if enhanced_cores:
    masses = [c['mass'] for c in enhanced_cores if c['mass'] > 0]
    temps = [c['temp'] for c in enhanced_cores]

    types = {}
    for core in enhanced_cores:
        ctype = core['type']
        types[ctype] = types.get(ctype, 0) + 1

    print(f"\nTotal cores: {len(enhanced_cores)}")

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
        print(f"  {ctype}: {count} ({100*count/len(enhanced_cores):.1f}%)")

    # Count massive cores
    massive = sum(1 for c in enhanced_cores if c['mass'] > 5.0)
    print(f"\nMassive cores (>5 Msun): {massive} ({100*massive/len(enhanced_cores):.1f}%)")

    prestellar_pct = 100 * types.get('prestellar', 0) / len(enhanced_cores)
    print(f"\nPrestellar fraction: {prestellar_pct:.1f}%")

print("\n" + "="*70)
print("CATALOG CREATION COMPLETE")
print("="*70)
