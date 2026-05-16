#!/usr/bin/env python3
"""
Create Core Catalog for IC5146 using Source Detection

This script identifies cores from the column density map using peak detection,
similar to the HGBS methodology for other regions.

Author: ASTRA Discovery System
Date: 5 April 2026
"""

import numpy as np
from astropy.io import fits
from scipy.ndimage import maximum_filter, label, center_of_mass
from scipy.signal import find_peaks
from astropy.wcs import WCS
import os

HGBS_DIR = '/Users/gjw255/astrodata/SWARM/ASTRA/HGBS_IC5146'
COL_DEN_FILE = os.path.join(HGBS_DIR, 'HGBS_ic5146_hires_column_density_map.fits')
TEMP_FILE = os.path.join(HGBS_DIR, 'HGBS_ic5146_dust_temperature_map.fits')
OUTPUT_FILE = os.path.join(HGBS_DIR, 'core_catalog_ic5146.csv')

DISTANCE_PC = 260.0  # IC5146 distance

# Constants
PC_TO_CM = 3.086e18  # Parsec to cm
MH_TO_G = 1.989e33   # Solar mass to grams
MH_TO_MSUN = 1.0     # Already in solar masses

print("="*70)
print("Creating Core Catalog for IC5146")
print("="*70)

# Load column density map
print(f"\nLoading column density map: {COL_DEN_FILE}")
with fits.open(COL_DEN_FILE) as hdul:
    col_data = hdul[0].data.astype(float)
    col_header = hdul[0].header
    wcs = WCS(col_header)

print(f"  Data shape: {col_data.shape}")
print(f"  Data range: {np.nanmin(col_data):.2e} - {np.nanmax(col_data):.2e} cm^-2")

# Load temperature map
print(f"\nLoading temperature map: {TEMP_FILE}")
with fits.open(TEMP_FILE) as hdul:
    temp_data = hdul[0].data.astype(float)
    temp_header = hdul[0].header

print(f"  Data shape: {temp_data.shape}")

# Get pixel scale
cdelt1 = np.abs(col_header.get('CDELT1', 5.0/3600/3600))
cdelt2 = np.abs(col_header.get('CDELT2', 5.0/3600/3600))
pixel_scale_rad = (cdelt1 + cdelt2) / 2 * np.pi / 180
pixel_scale_pc = DISTANCE_PC * pixel_scale_rad

# Convert column density to mass surface density
# N_H2 is in H2/cm^2, need to convert to Msun/pc^2
# 1 Msun/pc^2 = (1.989e33 g) / (3.086e18 cm)^2 = 2.089e-3 g/cm^2
# Mean molecular mass per H2 = 2.8 * m_H = 2.8 * 1.673e-24 g = 4.684e-24 g
# So 1 H2/cm^2 = 4.684e-24 g/cm^2 = 2.242e-21 Msun/pc^2

H2_TO_MSUN_PC2 = 2.242e-21

print(f"\nPixel scale: {pixel_scale_pc:.4f} pc")
print(f"Distance: {DISTANCE_PC} pc")

# Replace NaN and Inf with zeros
col_data_clean = np.nan_to_num(col_data, nan=0.0, posinf=0.0, neginf=0.0)
temp_data_clean = np.nan_to_num(temp_data, nan=0.0, posinf=0.0, neginf=0.0)

# ============================================================================
# CORE DETECTION USING PEAK FINDING
# ============================================================================

print("\n" + "="*70)
print("CORE DETECTION")
print("="*70)

# Apply minimum mass threshold (detect cores with N_H2 > 5e21 cm^-2)
min_threshold = 5.0e21  # cm^-2
mask = col_data_clean > min_threshold

print(f"Pixels above threshold: {np.sum(mask)} ({100*np.sum(mask)/mask.size:.2f}%)")

# Find local maxima using maximum filter
min_distance = 5  # Minimum pixels between peaks
local_max = maximum_filter(col_data_clean, size=min_distance*2+1)
peak_mask = (col_data_clean == local_max) & mask

peak_y, peak_x = np.where(peak_mask)
print(f"Peaks detected: {len(peak_x)}")

# Refine peaks - keep only significant ones
min_peak_value = 1.0e22  # cm^-2
significant_peaks = col_data_clean[peak_y, peak_x] > min_peak_value
peak_y = peak_y[significant_peaks]
peak_x = peak_x[significant_peaks]
print(f"Significant peaks: {len(peak_x)}")

# ============================================================================
# CORE PROPERTY EXTRACTION
# ============================================================================

print("\n" + "="*70)
print("EXTRACTING CORE PROPERTIES")
print("="*70)

cores = []
aperture_radius = 3  # pixels for core integration

for i, (py, px) in enumerate(zip(peak_y, peak_x)):
    try:
        # Get core bounds
        y_min = max(0, py - aperture_radius)
        y_max = min(col_data_clean.shape[0], py + aperture_radius + 1)
        x_min = max(0, px - aperture_radius)
        x_max = min(col_data_clean.shape[1], px + aperture_radius + 1)

        # Extract core region
        core_region = col_data_clean[y_min:y_max, x_min:x_max]
        temp_region = temp_data_clean[y_min:y_max, x_min:x_max]

        # Calculate properties
        peak_nh2 = col_data_clean[py, px]

        # Integrate mass over core region
        mean_nh2 = np.mean(core_region[core_region > 0]) if np.any(core_region > 0) else peak_nh2
        npix = np.sum(core_region > min_threshold)

        # Calculate mass
        # Mass = N_H2 * area * m_H2 / Msun
        # area = npix * (pixel_scale_pc * PC_TO_CM)^2
        area_cm2 = npix * (pixel_scale_pc * PC_TO_CM) ** 2
        mass_g = peak_nh2 * area_cm2 * 4.684e-24  # Using mean molecular mass
        mass_msun = mass_g / MH_TO_G

        # Get temperature at core location
        # Need to handle potential size mismatch
        if temp_data_clean.shape != col_data_clean.shape:
            # Scale temperature coordinates
            ty = int(py * temp_data_clean.shape[0] / col_data_clean.shape[0])
            tx = int(px * temp_data_clean.shape[1] / col_data_clean.shape[1])
            temp = temp_data_clean[ty, tx] if 0 <= ty < temp_data_clean.shape[0] and 0 <= tx < temp_data_clean.shape[1] else 15.0
        else:
            temp = temp_data_clean[py, px]

        if temp <= 0 or np.isnan(temp):
            temp = 15.0  # Default temperature

        # Convert pixel position to RA/Dec
        try:
            coord = wcs.pixel_to_world(px, py)
            ra_deg = coord.ra.deg
            dec_deg = coord.dec.deg
        except:
            ra_deg = 0.0
            dec_deg = 0.0

        # Classify core type based on mass and temperature
        if mass_msun < 0.1:
            core_type = 'starless'
        elif mass_msun < 2.0:
            if temp < 15:
                core_type = 'prestellar'
            else:
                core_type = 'starless'
        else:
            if temp > 20:
                core_type = 'protostellar'
            elif temp < 12:
                core_type = 'prestellar'
            else:
                core_type = 'unbound'

        cores.append({
            'id': i + 1,
            'ra_deg': ra_deg,
            'dec_deg': dec_deg,
            'mass': mass_msun,
            'peak_nh2': peak_nh2 / 1e21,  # Convert to 10^21 cm^-2
            'npix': npix,
            'temp': temp,
            'type': core_type
        })

    except Exception as e:
        print(f"  Warning: Failed to process core {i}: {e}")
        continue

print(f"\nSuccessfully extracted {len(cores)} cores")

# ============================================================================
# SAVE CATALOG
# ============================================================================

print("\n" + "="*70)
print("SAVING CATALOG")
print("="*70)

# Save as CSV
with open(OUTPUT_FILE, 'w') as f:
    f.write("# IC5146 Core Catalog\n")
    f.write("# Generated by ASTRA Discovery System\n")
    f.write("# Distance: {} pc\n".format(DISTANCE_PC))
    f.write("# Columns: obj_id, mass_Msun, peak_N_cm2, npix, ra_deg, dec_deg, Tdust_median_K, type\n")
    for core in cores:
        f.write("{},{},{},{},{},{},{},{}\n".format(
            core['id'],
            f"{core['mass']:.4f}",
            f"{core['peak_nh2']*1e21:.2e}",
            core['npix'],
            f"{core['ra_deg']:.6f}",
            f"{core['dec_deg']:.6f}",
            f"{core['temp']:.2f}",
            core['type']
        ))

print(f"Catalog saved to: {OUTPUT_FILE}")

# ============================================================================
# STATISTICS
# ============================================================================

print("\n" + "="*70)
print("IC5146 CORE CATALOG STATISTICS")
print("="*70)

if cores:
    masses = [c['mass'] for c in cores]
    temps = [c['temp'] for c in cores]

    print(f"\nTotal cores: {len(cores)}")
    print(f"\nMass statistics [Msun]:")
    print(f"  Range: {np.min(masses):.4f} - {np.max(masses):.4f}")
    print(f"  Median: {np.median(masses):.4f}")
    print(f"  Mean: {np.mean(masses):.4f}")

    print(f"\nTemperature statistics [K]:")
    print(f"  Range: {np.min(temps):.2f} - {np.max(temps):.2f}")
    print(f"  Median: {np.median(temps):.2f}")

    # Count core types
    print(f"\nCore type distribution:")
    type_counts = {}
    for core in cores:
        ctype = core['type']
        type_counts[ctype] = type_counts.get(ctype, 0) + 1

    for ctype, count in sorted(type_counts.items()):
        print(f"  {ctype}: {count} ({100*count/len(cores):.1f}%)")

    # Count massive cores
    massive = sum(1 for c in cores if c['mass'] > 5.0)
    print(f"\nMassive cores (>5 Msun): {massive} ({100*massive/len(cores):.1f}%)")

print("\n" + "="*70)
print("CATALOG CREATION COMPLETE")
print("="*70)
