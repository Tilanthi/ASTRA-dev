#!/usr/bin/env python3
"""
HGBS IC5146 Discovery Science - Filament Analysis (Simplified)

Author: ASTRA Discovery System
Date: 19 April 2026
"""

import numpy as np
import matplotlib.pyplot as plt
from astropy.io import fits
from scipy.signal import convolve2d
import os

# ============================================================================
# DATA PATHS
# ============================================================================
HGBS_DIR = '/Users/gj255/astrodata/SWARM/ASTRA/HGBS_IC5146'

COL_DEN_FILE = os.path.join(HGBS_DIR, 'HGBS_ic5146_column_density_map.fits')
TEMP_FILE = os.path.join(HGBS_DIR, 'HGBS_ic5146_dust_temperature_map.fits')
SKELETON_FILE = os.path.join(HGBS_DIR, 'HGBS_ic5146_skeleton_map.fits')

DISTANCE_PC = 260.0
M_LINE_CRIT = 16.0  # Msun/pc

print("="*70)
print("HGBS IC5146 - FILAMENT ANALYSIS")
print("="*70)

# Load data
print("\nLoading FITS maps...")
with fits.open(COL_DEN_FILE) as hdul:
    col_data = hdul[0].data
    col_header = hdul[0].header

with fits.open(SKELETON_FILE) as hdul:
    skel_data = hdul[0].data

with fits.open(TEMP_FILE) as hdul:
    temp_data = hdul[0].data

print("Data loaded successfully")

# Calculate pixel size
cdelt1 = np.abs(col_header.get('CDELT1', 5.0/3600/3600))
cdelt2 = np.abs(col_header.get('CDELT2', 5.0/3600/3600))
pix_size_rad = (cdelt1 + cdelt2) / 2 * np.pi / 180
pixel_size_pc = DISTANCE_PC * pix_size_rad

print(f"Pixel size: {pixel_size_pc:.6f} pc")

# ============================================================================
# COLUMN DENSITY ANALYSIS
# ============================================================================
print("\n" + "="*70)
print("COLUMN DENSITY ANALYSIS")
print("="*70)

valid_col = col_data[np.isfinite(col_data)]
print(f"Median N_H2: {np.median(valid_col)/1e21:.2f}e21 cm^-2")
print(f"Range: {np.min(valid_col)/1e21:.2f} - {np.max(valid_col)/1e21:.2f} e21 cm^-2")

# ============================================================================
# SKELETON ANALYSIS
# ============================================================================
print("\n" + "="*70)
print("FILAMENT SKELETON ANALYSIS")
print("="*70)

filament_mask = skel_data > 0
filament_pixels = np.sum(filament_mask)
filament_length_pc = filament_pixels * pixel_size_pc

print(f"Filament pixels: {filament_pixels}")
print(f"Total filament length: {filament_length_pc:.1f} pc")

skel_values = skel_data[filament_mask]
print(f"Skeleton value range: {np.min(skel_values):.1f} - {np.max(skel_values):.1f}")
print(f"Median skeleton value: {np.median(skel_values):.2f}")

# ============================================================================
# JUNCTION ANALYSIS
# ============================================================================
print("\n" + "="*70)
print("JUNCTION ANALYSIS")
print("="*70)

kernel = np.array([[0, 1, 0], [1, 0, 1], [0, 1, 0]])
skeleton_binary = filament_mask.astype(np.uint8)
neighbor_count = convolve2d(skeleton_binary, kernel, mode='same')
junction_mask = (neighbor_count >= 3) & filament_mask

junction_y, junction_x = np.where(junction_mask)
junctions = list(zip(junction_y, junction_x))

print(f"Junctions identified: {len(junctions)}")

if len(junctions) > 0:
    junction_nh2 = col_data[junction_y, junction_x]
    print(f"Junction N_H2: median = {np.median(junction_nh2)/1e21:.2f}e21 cm^-2")

# High-density zones
high_skel_threshold = np.percentile(skel_values, 90)
high_skel_mask = (skel_data >= high_skel_threshold) & filament_mask
high_skel_y, high_skel_x = np.where(high_skel_mask)

print(f"High-density zones: {len(high_skel_y)}")

# ============================================================================
# M_LINE ANALYSIS (Simplified)
# ============================================================================
print("\n" + "="*70)
print("M_LINE ANALYSIS")
print("="*70)

filament_densities = col_data[filament_mask]
filament_densities = filament_densities[np.isfinite(filament_densities)]
filament_densities = filament_densities[filament_densities > 0]

print(f"Filament N_H2: median = {np.median(filament_densities)/1e21:.2f}e21 cm^-2")

# Simplified M_line calculation
# For N_H2 in 10^21 cm^-2, multiply by ~2.5 to get approximate Msun/pc
m_line_approx = filament_densities / 1e21 * 2.5

print(f"\nApproximate M_line statistics:")
print(f"  Median M_line: {np.median(m_line_approx):.2f} Msun/pc")
print(f"  Range: {np.min(m_line_approx):.2f} - {np.max(m_line_approx):.2f} Msun/pc")

above_crit = np.sum(m_line_approx > M_LINE_CRIT)
fraction = 100 * above_crit / len(m_line_approx)
print(f"\nAbove critical threshold ({M_LINE_CRIT} Msun/pc):")
print(f"  {above_crit} / {len(m_line_approx)} ({fraction:.1f}%)")

# ============================================================================
# SUMMARY
# ============================================================================
print("\n" + "="*70)
print("IC5146 FILAMENT ANALYSIS - SUMMARY")
print("="*70)

results = {
    'distance_pc': DISTANCE_PC,
    'median_nh2': float(np.median(valid_col)),
    'filament_length_pc': float(filament_length_pc),
    'junctions': len(junctions),
    'high_density_zones': len(high_skel_y),
    'median_m_line': float(np.median(m_line_approx)),
    'fraction_above_critical': float(fraction)
}

print(f"\nIC5146 Region Properties:")
print(f"  Median N_H2: {results['median_nh2']/1e21:.2f}e21 cm^-2")
print(f"  Filament length: {results['filament_length_pc']:.1f} pc")
print(f"  Junctions: {results['junctions']}")
print(f"  High-density zones: {results['high_density_zones']}")
print(f"  Median M_line: {results['median_m_line']:.2f} Msun/pc")
print(f"  Above critical threshold: {results['fraction_above_critical']:.1f}%")

# Save results
np.savez('ic5146_results.npz', **results)
print(f"\nResults saved to: ic5146_results.npz")

print("\n" + "="*70)
print("ANALYSIS COMPLETE")
print("="*70)
print("\nNote: IC5146 lacks the standard HGBS core catalog.")
print("This analysis focused on filament and skeleton properties only.")
print(f"Key Findings:")
print(f"  • {results['junctions']} filament junctions")
print(f"  • {results['high_density_zones']} high-density zones")
print(f"  • {results['filament_length_pc']:.1f} pc total filament length")
print(f"  • Median M_line: {results['median_m_line']:.2f} Msun/pc")
