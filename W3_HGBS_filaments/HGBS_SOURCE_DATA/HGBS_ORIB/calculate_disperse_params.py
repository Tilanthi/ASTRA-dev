#!/usr/bin/env python3
"""
DisPerSE Parameter Calculator for HGBS Orion B
Following Arzoumanian+2019 Section 2.2
"""

import numpy as np
from astropy.io import fits
from pathlib import Path
import json

print("="*70)
print("DISPERSE PARAMETER CALCULATION: HGBS ORION B")
print("Arzoumanian+2019 Section 2.2")
print("="*70)

# Set paths
data_dir = Path("/Users/gjw255/astrodata/SWARM/ASTRA/HGBS_ORIB")
column_density_file = data_dir / "HGBS_orionB_column_density_map.fits"

# Load data
print("\nLoading column density map...")
hdul = fits.open(column_density_file)
column_density = hdul[0].data
header = hdul[0].header
hdul.close()

print(f"Shape: {column_density.shape}")
print(f"Dtype: {column_density.dtype}")

# Get pixel scale (CDELT is in degrees, convert to arcsec)
cdelt2_deg = header.get('CDELT2', 3.0/3600)  # Default 3 arcsec in degrees
cdelt2_arcsec = cdelt2_deg * 3600

print(f"\nImage parameters:")
print(f"  CDELT2: {cdelt2_deg:.10f} degrees = {cdelt2_arcsec:.3f} arcsec/pixel")

# HPBW for Herschel (typically 18 arcsec for SPIRE 250um)
hpbw_arcsec = header.get('HPBW', 18.0)
print(f"  HPBW: {hpbw_arcsec:.1f} arcsec")

# Calculate HPBW in pixels
hpbw_pixels = hpbw_arcsec / cdelt2_arcsec
print(f"  HPBW: {hpbw_pixels:.1f} pixels")

# Calculate background parameters following Arzoumanian+2019
print("\n" + "="*70)
print("BACKGROUND PARAMETER CALCULATION")
print("="*70)

# Get finite values
data_flat = column_density[np.isfinite(column_density)]
print(f"\nTotal finite pixels: {len(data_flat):,}")
print(f"Range: {np.min(data_flat):.2e} to {np.max(data_flat):.2e} H2/cm^2")

# Create histogram with bin size = 10^21 cm^-2
bin_size = 1e21  # cm^-2

# Determine appropriate range
min_val = 0  # Start from 0
max_val = np.min([np.max(data_flat), min_val + 200 * bin_size])  # Limit bins
bins = np.arange(min_val, max_val + bin_size, bin_size)

print(f"\nHistogram parameters:")
print(f"  Bin size: {bin_size:.2e} cm^-2")
print(f"  Number of bins: {len(bins)}")

# Calculate histogram
print("Calculating histogram...")
hist, bin_edges = np.histogram(data_flat, bins=bins)

# Get first bin statistics
first_bin_mask = (data_flat >= bins[0]) & (data_flat < bins[1])
first_bin_values = data_flat[first_bin_mask]

NH2_bg_min = np.median(first_bin_values)

# Use robust std estimate: IQR/1.349
q75, q25 = np.percentile(first_bin_values, [75, 25])
iqr = q75 - q25
rms_min_robust = iqr / 1.349

# Also try regular std
rms_min_std = np.std(first_bin_values)

print(f"\nFirst bin statistics (0 to {bin_size:.2e} cm^-2):")
print(f"  Number of pixels: {len(first_bin_values):,}")
print(f"  Median (NH2_bg,min): {NH2_bg_min:.4e} cm^-2")
print(f"  IQR: {iqr:.4e} cm^-2")
print(f"  rms_min (robust, IQR/1.349): {rms_min_robust:.4e} cm^-2")
print(f"  rms_min (std): {rms_min_std:.4e} cm^-2")

# Use robust estimate if std is unreliable
if np.isinf(rms_min_std) or np.isnan(rms_min_std):
    rms_min = rms_min_robust
    print(f"\nUsing robust rms estimate (std is unreliable)")
else:
    rms_min = rms_min_std
    print(f"\nUsing std for rms estimate")

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
print(f"  N_pix (smoothing) = 2 × HPBW/pix = {int(2 * hpbw_pixels)} pixels")
print(f"  Min feature length = 10 × HPBW = {int(10 * hpbw_pixels)} pixels")

# Physical scales (Orion B distance ~400 pc)
distance_pc = 400
pix_size_pc = (cdelt2_arcsec / 206265) * distance_pc
hpbw_pc = (hpbw_arcsec / 206265) * distance_pc

print(f"\nPhysical scales (at d = {distance_pc} pc):")
print(f"  Pixel size: {pix_size_pc:.5f} pc = {pix_size_pc * 3.086e18:.2e} cm")
print(f"  HPBW: {hpbw_pc:.3f} pc")
print(f"  Min feature length: {int(10 * hpbw_pixels) * pix_size_pc:.2f} pc")

# Save parameters
params = {
    'NH2_bg_min': float(NH2_bg_min),
    'rms_min': float(rms_min),
    'persistence_threshold': float(persistence_threshold),
    'robustness_threshold': float(robustness_threshold),
    'assembly_angle': 50.0,
    'n_pix_smoothing': int(2 * hpbw_pixels),
    'min_feature_length': int(10 * hpbw_pixels),
    'hpbw_pixels': float(hpbw_pixels),
    'pix_size_pc': float(pix_size_pc),
    'hpbw_pc': float(hpbw_pc)
}

output_file = data_dir / "disperse_params_final.json"
with open(output_file, 'w') as f:
    json.dump(params, f, indent=2)

print(f"\nParameters saved to: {output_file}")

print("\n" + "="*70)
print("PARAMETER CALCULATION COMPLETE")
print("="*70)
