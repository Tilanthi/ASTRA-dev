#!/usr/bin/env python3
"""
Generate skeleton map for Taurus L1495 using FilFinder
"""

import numpy as np
from astropy.io import fits
from astropy.wcs import WCS
from astropy import units as u
import fil_finder
from fil_finder import FilFinder2D

# File paths
col_den_file = '/Users/gjw255/astrodata/SWARM/ASTRA/HGBS_TAURUS/HGBS_tauN3_hires_column_density_map.fits'
output_file = '/Users/gjw255/astrodata/SWARM/ASTRA/HGBS_TAURUS/HGBS_taurusL1495_skeleton_map_filfinder.fits'

print("="*70)
print("Generating Taurus Skeleton Map using FilFinder")
print("="*70)

# Load column density map
print(f"\nLoading column density map: {col_den_file}")
with fits.open(col_den_file) as hdul:
    data_nh2 = hdul[0].data
    header = hdul[0].header

print(f"  Data shape: {data_nh2.shape}")
print(f"  Data range: {np.min(data_nh2):.2f} - {np.max(data_nh2):.2f} × 10^21 cm^-2")

# Handle NaN and Inf values
print(f"  Cleaning data (replacing NaN/Inf)...")
data_nh2_clean = np.nan_to_num(data_nh2, posinf=0, neginf=0)
data_nh2_clean = np.clip(data_nh2_clean, 0, None)

# Convert from 10^21 cm^-2 to column density (H/cm^2)
# The data is already in units of 10^21 cm^-2
img = data_nh2_clean * 1e21  # Convert to H/cm^2

# Get beam size from header
beam_size = header.get('HPBW', 18.2)  # Default 18.2 arcsec
print(f"  Beam size: {beam_size} arcsec")

# Distance to Taurus (pc)
distance_pc = 140.0

# Expected filament width (pc)
expected_width = 0.1

# Create FilFinder object (with astropy units)
print(f"\nInitializing FilFinder...")
print(f"  Distance: {distance_pc} pc")
print(f"  Expected filament width: {expected_width} pc")

fil_finder = FilFinder2D(img, distance=distance_pc*u.pc,  # Distance with units
                       beamwidth=beam_size*u.arcsec)  # Beam size with angular units

# Preprocess the image
print(f"\nPreprocessing image...")
fil_finder.preprocess_image(flatten_frac=None,
                             normalize=False,
                             skeleton=False)

# Create mask for filamentary structures
print(f"Creating mask (threshold: 3×10^21 cm^-2)...")
fil_finder.create_mask(glob_thresh=3.0,  # Threshold in units of 10^21 cm^-2
                     adapt_thresh=0.1,
                     smooth_size=3,
                     size_cutoff=400)

# Analyze the skeleton
print(f"Analyzing skeleton...")
fil_finder.analyze_skeleton(branch_thresh=40*3.086e18,  # Convert 40 pc to cm
                        perc_keep=0.0,
                        relabel=True)

# Get the skeleton
skeleton = fil_finder.skeleton
print(f"  Skeleton pixels: {np.sum(skeleton > 0)}")

# Save the skeleton
print(f"\nSaving skeleton map to: {output_file}")
fits.writeto(output_file, skeleton.astype(float), header, overwrite=True)

import os
print(f"  File size: {os.path.getsize(output_file) / 1024 / 1024:.1f} MB")

print("\n" + "="*70)
print("Taurus skeleton map generated with FilFinder!")
print("="*70)
