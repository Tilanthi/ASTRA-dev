#!/usr/bin/env python3
"""
Simple DisPerSE testing script for HGBS Orion B
Following Arzoumanian+2019 Section 2.2 parameter calculations
"""

import numpy as np
from astropy.io import fits
from pathlib import Path
import json

print("="*70)
print("DISPERSE PARAMETER CALCULATION: HGBS ORION B")
print("="*70)

# Set paths
data_dir = Path("/Users/gjw255/astrodata/SWARM/ASTRA/HGBS_ORIB")
column_density_file = data_dir / "HGBS_orionB_column_density_map.fits"
skeleton_file = data_dir / "HGBS_orionB_skeleton_map.fits"

# Load data
print("\nLoading column density map...")
with fits.open(column_density_file) as hdul:
    column_density = hdul[0].data
    header = hdul[0].header

print(f"Shape: {column_density.shape}")
print(f"Range: {np.nanmin(column_density):.2e} to {np.nanmax(column_density):.2e} H2/cm^2")

# Load existing skeleton
print("\nLoading existing skeleton map...")
with fits.open(skeleton_file) as hdul:
    existing_skeleton = hdul[0].data

print(f"Existing skeleton non-zero pixels: {np.count_nonzero(existing_skeleton):,}")

# Get pixel information
pix_scale = header.get('CDELT2', 3.0)  # arcsec/pixel
hpbw = header.get('HPBW', 18.0)  # arcsec

print(f"\nImage parameters:")
print(f"  Pixel scale: {pix_scale} arcsec/pixel")
print(f"  HPBW: {hpbw} arcsec")

# Calculate background parameters following Arzoumanian+2019 Section 2.2
print("\n" + "="*70)
print("BACKGROUND PARAMETER CALCULATION")
print("="*70)

# Create histogram with bin size = 10^21 cm^-2
bin_size = 1e21  # cm^-2
data_flat = column_density[np.isfinite(column_density)]

min_val = np.floor(np.min(data_flat) / bin_size) * bin_size
max_val = np.min([np.ceil(np.max(data_flat) / bin_size) * bin_size, min_val + 200 * bin_size])  # Limit bins for memory
bins = np.arange(min_val, max_val + bin_size, bin_size)

print(f"\nHistogram parameters:")
print(f"  Bin size: {bin_size:.2e} cm^-2")
print(f"  Number of bins: {len(bins)}")
print(f"  Range: {min_val:.2e} to {max_val:.2e} cm^-2")

# Calculate histogram
print("\nCalculating histogram...")
hist, bin_edges = np.histogram(data_flat, bins=bins)

# Get first bin statistics
first_bin_mask = (data_flat >= bins[0]) & (data_flat < bins[1])
first_bin_values = data_flat[first_bin_mask]

NH2_bg_min = np.median(first_bin_values)
rms_min = np.std(first_bin_values)

print(f"\nFirst bin statistics (0 to {bin_size:.2e} cm^-2):")
print(f"  Number of pixels: {len(first_bin_values):,}")
print(f"  Median (NH2_bg,min): {NH2_bg_min:.4e} cm^-2")
print(f"  Std (rms_min): {rms_min:.4e} cm^-2")

# Calculate DisPerSE thresholds
persistence_threshold = rms_min
robustness_threshold = 1.5 * NH2_bg_min

print(f"\n" + "="*70)
print("DISPERSE PARAMETERS (Arzoumanian+2019 Section 2.2)")
print("="*70)

print(f"\nThresholds:")
print(f"  PT (persistence) = rms_min = {persistence_threshold:.4e} cm^-2")
print(f"  RT (robustness) = 1.5 × NH2_bg,min = {robustness_threshold:.4e} cm^-2")

print(f"\nOther parameters:")
print(f"  AA (assembly angle) = 50°")
print(f"  N_pix (smoothing) = 2 × HPBW / pix = {int(2 * hpbw / pix_scale)} pixels")
print(f"  Min feature length = 10 × HPBW = {int(10 * hpbw / pix_scale)} pixels")

# Save parameters to file
params = {
    'NH2_bg_min': float(NH2_bg_min),
    'rms_min': float(rms_min),
    'persistence_threshold': float(persistence_threshold),
    'robustness_threshold': float(robustness_threshold),
    'assembly_angle': 50.0,
    'n_pix_smoothing': int(2 * hpbw / pix_scale),
    'min_feature_length': int(10 * hpbw / pix_scale),
    'bin_size': float(bin_size)
}

output_file = data_dir / "disperse_params.json"
with open(output_file, 'w') as f:
    json.dump(params, f, indent=2)

print(f"\nParameters saved to: {output_file}")

# Calculate approximate pixel scale in pc at Orion B distance
# Orion B distance ~400 pc
distance_pc = 400
pix_size_pc = (pix_scale / 206265) * distance_pc  # Convert arcsec to pc

print(f"\nPhysical scales (at {distance_pc} pc):")
print(f"  Pixel size: {pix_size_pc:.4f} pc")
print(f"  HPBW: {(hpbw / 206265) * distance_pc:.3f} pc")
print(f"  Min feature length: {params['min_feature_length'] * pix_size_pc:.2f} pc")

print("\n" + "="*70)
print("PARAMETER CALCULATION COMPLETE")
print("="*70)
