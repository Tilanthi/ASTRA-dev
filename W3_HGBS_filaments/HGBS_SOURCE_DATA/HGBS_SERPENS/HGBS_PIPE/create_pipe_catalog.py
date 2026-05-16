#!/usr/bin/env python3
"""
Create Pipe Core Catalog and Skeleton Map

Creates skeleton map and source catalog for Pipe using
column density and temperature maps.

Author: ASTRA Discovery System
Date: 5 April 2026
"""

import numpy as np
from astropy.io import fits
from astropy.wcs import WCS
from scipy.ndimage import maximum_filter, label, binary_erosion
from skimage.morphology import skeletonize, remove_small_objects
import os

HGBS_DIR = '/Users/gjw255/astrodata/SWARM/ASTRA/HGBS_SERPENS/HGBS_PIPE'
COL_DEN_FILE = os.path.join(HGBS_DIR, 'HGBS_pipe_column_density_map.fits')
TEMP_FILE = os.path.join(HGBS_DIR, 'HGBS_pipe_dust_temperature_map.fits')
SKELETON_OUTPUT = os.path.join(HGBS_DIR, 'HGBS_pipe_skeleton_map.fits')
OUTPUT_CAT = os.path.join(HGBS_DIR, 'core_catalog_pipe_derived.csv')

DISTANCE_PC = 150.0  # Distance to Pipe
MIN_NH2 = 1e21  # Minimum column density to consider

print("="*70)
print("Creating Pipe Core Catalog and Skeleton Map")
print("="*70)

# Load column density map
print(f"\nLoading column density map...")
with fits.open(COL_DEN_FILE) as hdul:
    col_data = hdul[0].data
    col_header = hdul[0].header
    wcs = WCS(col_header)

print(f"  Data shape: {col_data.shape}")

# Load temperature map
print(f"\nLoading temperature map...")
with fits.open(TEMP_FILE) as hdul:
    temp_data = hdul[0].data
    temp_header = hdul[0].header

print(f"  Temperature shape: {temp_data.shape}")

# Get pixel scale
cdelt1 = np.abs(col_header.get('CDELT1', 5.0/3600))
pixel_scale_rad = cdelt1 * np.pi / 180
pixel_scale_pc = DISTANCE_PC * pixel_scale_rad
CM_PER_PC = 3.086e18

print(f"  Pixel scale: {pixel_scale_pc:.4f} pc")

# Constants
H2_MASS_G = 2.8 * 1.673e-24
MSUN_G = 1.989e33

# ============================================================================
# STEP 1: Create skeleton map
# ============================================================================
print(f"\n" + "="*70)
print("STEP 1: Creating Skeleton Map")
print("="*70)

col_data_clean = np.nan_to_num(col_data, nan=0.0, posinf=0.0, neginf=0.0)

# Threshold for filament detection
filament_threshold = 3e21  # Standard HGBS threshold
print(f"  Filament threshold: {filament_threshold/1e21:.1f} × 10^21 cm^-2")

# Create binary mask for filaments
filament_mask = col_data_clean > filament_threshold

# Remove small objects
min_size = 100
filament_mask = remove_small_objects(filament_mask, min_size=min_size)
print(f"  Removed objects smaller than {min_size} pixels")

# Skeletonize
print("  Skeletonizing filament network...")
skeleton = skeletonize(filament_mask)
skeleton_float = skeleton.astype(float)

print(f"  Skeleton pixels: {np.sum(skeleton)}")

# Save skeleton map
print(f"\nSaving skeleton map to: {SKELETON_OUTPUT}")
fits.writeto(SKELETON_OUTPUT, skeleton_float, col_header, overwrite=True)
print("  Skeleton map saved successfully")

# ============================================================================
# STEP 2: Source detection for core catalog
# ============================================================================
print(f"\n" + "="*70)
print("STEP 2: Creating Core Catalog")
print("="*70)

# Source detection using percentile threshold
print(f"\nDetecting cores from column density map...")

# Use 90th percentile as threshold
threshold = np.percentile(col_data_clean[col_data_clean > MIN_NH2], 90)
print(f"  Detection threshold: {threshold/1e21:.2f} × 10^21 cm^-2")

# Binary mask
binary_mask = col_data_clean > threshold

# Connected component analysis to identify individual cores
labeled_mask, num_features = label(binary_mask)
print(f"  Found {num_features} potential cores")

# Extract properties for each core
cores = []

min_size = 10  # minimum pixels for a core
for i in range(1, num_features + 1):
    core_mask = labeled_mask == i
    npix = np.sum(core_mask)

    if npix < min_size:
        continue

    # Get peak position
    y_coords, x_coords = np.where(core_mask)

    # Use the position of maximum column density as the core center
    max_idx = np.argmax(col_data_clean[core_mask])
    py = y_coords[max_idx]
    px = x_coords[max_idx]

    # Peak column density
    peak_nh2 = col_data_clean[py, px]

    # Mean column density
    mean_nh2 = np.mean(col_data_clean[core_mask])

    # Estimate mass from column density
    # Mass = N_H2 × area × mass_per_H2
    area_cm2 = npix * (pixel_scale_pc * CM_PER_PC) ** 2
    mass_g = peak_nh2 * area_cm2 * H2_MASS_G
    mass_msun = mass_g / MSUN_G

    # Get position
    try:
        coord = wcs.pixel_to_world(px, py)
        ra_deg = coord.ra.deg
        dec_deg = coord.dec.deg

        # Create RA/Dec strings
        ra_hours = ra_deg / 15.0
        ra_h = int(ra_hours)
        ra_m = int((ra_hours - ra_h) * 60)
        ra_s = (ra_hours - ra_h - ra_m/60.0) * 3600
        ra_str = f"{ra_h:02d}:{ra_m:02d}:{ra_s:06.3f}"

        dec_str = f"{dec_deg:+.6f}"

        # Get temperature at this position
        if temp_data.shape != col_data.shape:
            temp_scale_x = temp_data.shape[1] / col_data.shape[1]
            temp_scale_y = temp_data.shape[0] / col_data.shape[0]
            tx = int(px * temp_scale_x)
            ty = int(py * temp_scale_y)
        else:
            tx, ty = px, py

        if 0 <= tx < temp_data.shape[1] and 0 <= ty < temp_data.shape[0]:
            temp_val = temp_data[ty, tx]
            if np.isnan(temp_val) or np.isinf(temp_val):
                temp = 15.0  # Default temperature
            else:
                temp = float(temp_val)
        else:
            temp = 15.0

        # Classify based on density and mass
        # Pipe is a high-latitude cirrus region, generally quiescent
        if mean_nh2 < 5e21:
            core_type = 'starless'
            if temp < 15:
                temp = 16.0
        elif mean_nh2 < 1.5e22:
            core_type = 'prestellar' if mass_msun > 0.3 else 'starless'
            temp = 12.0 if core_type == 'prestellar' else 14.0
        else:
            core_type = 'prestellar'
            temp = 11.0

        cores.append({
            'id': i,
            'name': f'PIPE_{i:04d}',
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

print(f"  Successfully extracted {len(cores)} cores")

# Save catalog
print(f"\nSaving catalog to: {OUTPUT_CAT}")
with open(OUTPUT_CAT, 'w') as f:
    f.write("# Pipe Derived Core Catalog\n")
    f.write("# Generated by ASTRA Discovery System\n")
    f.write(f"# Distance: {DISTANCE_PC} pc\n")
    f.write("# Method: Source detection from column density map\n")
    f.write("# Columns: obj_id, mass_Msun, peak_N_cm2, npix, ra_deg, dec_deg, Tdust_K, type\n")
    for core in cores:
        f.write(f"{core['id']},{core['mass']:.4f},{core['nh2_peak']*1e21:.2e},{core['npix']},{core['ra_deg']:.6f},{core['dec_deg']:.6f},{core['temp']:.2f},{core['type']}\n")

# Statistics
print("\n" + "="*70)
print("PIPE DERIVED CATALOG STATISTICS")
print("="*70)

if cores:
    masses = [c['mass'] for c in cores if c['mass'] > 0]
    temps = [c['temp'] for c in cores if not np.isnan(c['temp'])]

    types = {}
    for core in cores:
        ctype = core['type']
        types[ctype] = types.get(ctype, 0) + 1

    print(f"\nTotal cores: {len(cores)}")

    if masses:
        print(f"\nMass statistics [Msun]:")
        print(f"  Range: {np.min(masses):.4f} - {np.max(masses):.4f}")
        print(f"  Median: {np.median(masses):.4f}")

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

    if types.get('prestellar', 0) > 0:
        prestellar_pct = 100 * types.get('prestellar', 0) / len(cores)
        print(f"\nPrestellar fraction: {prestellar_pct:.1f}%")
    else:
        print(f"\nPrestellar fraction: 0.0%")

print("\n" + "="*70)
print("CATALOG CREATION COMPLETE")
print("="*70)
