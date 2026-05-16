#!/usr/bin/env python3
"""Test script for filament-projected NN analysis."""

import sys
sys.path.insert(0, '/Users/gjw255/astrodata/SWARM/ASTRA-dev-main/W3_HGBS_filaments/HGBS_SOURCE_DATA')

import numpy as np
from astropy.io import fits
from astropy import units as u
from astropy.coordinates import SkyCoord
from scipy import ndimage
from collections import defaultdict
from pathlib import Path

# Test just one region first
region = 'Orion B'
base_path = Path('/Users/gjw255/astrodata/SWARM/ASTRA-dev-main/W3_HGBS_filaments/HGBS_SOURCE_DATA')

skeleton_file = base_path / 'HGBS_ORIB/HGBS_orionB_skeleton_map_thresh50.fits'
catalog_file = base_path / 'HGBS_ORIB/HGBS_orionB_observed_core_catalog.txt'
distance_pc = 386

print(f"Testing {region}")
print(f"Skeleton: {skeleton_file}")
print(f"Catalog: {catalog_file}")

# Load skeleton
print("\n1. Loading skeleton...")
hdul = fits.open(skeleton_file)
skeleton_data = hdul[0].data.astype(np.float64)
header = hdul[0].header
hdul.close()

from astropy.wcs import WCS
wcs = WCS(header)

print(f"   Skeleton shape: {skeleton_data.shape}")
print(f"   Non-zero pixels: {np.sum(skeleton_data > 0)}")

# Load catalog
print("\n2. Loading catalog...")
cores = []

with open(catalog_file, 'r', encoding='latin-1', errors='ignore') as f:
    lines = f.readlines()

data_start = None
for i, line in enumerate(lines):
    if '   1 ' in line or ' 1 ' in line:
        data_start = i
        break

print(f"   Data starts at line {data_start}")

count = 0
for line in lines[data_start:data_start+20]:
    parts = line.split()
    if len(parts) >= 8:
        try:
            ra_str = f"{parts[2]}:{parts[3]}:{parts[4]}"
            dec_str = f"{parts[5]}:{parts[6]}:{parts[7]}"
            coord = SkyCoord(ra_str, dec_str, unit=(u.hourangle, u.deg))
            cores.append({'id': int(parts[0]), 'ra': coord.ra.deg, 'dec': coord.dec.deg})
            count += 1
        except Exception as e:
            pass

print(f"   Loaded {len(cores)} cores (first {count} for testing)")

# Extract filaments
print("\n3. Extracting filaments...")
skeleton_mask = skeleton_data > 0.1
labeled, num_features = ndimage.label(skeleton_mask)
print(f"   Found {num_features} features")

# Get filaments with >= 50 pixels
filaments = []
for i in range(1, min(num_features + 1, 200)):  # Limit for speed
    filament_pixels = np.where(labeled == i)
    n_pixels = len(filament_pixels[0])

    if n_pixels >= 50:
        y_coords = filament_pixels[0]
        x_coords = filament_pixels[1]
        skeleton_values = skeleton_data[y_coords, x_coords]
        order = np.argsort(-skeleton_values)

        filaments.append({
            'id': i,
            'pixels_y': y_coords[order],
            'pixels_x': x_coords[order],
            'length': n_pixels
        })

print(f"   Extracted {len(filaments)} filaments (>= 50 pixels)")

# Associate cores (simplified)
print("\n4. Testing core association...")
from astropy.wcs import utils

associated = 0
for i, core in enumerate(cores[:100]):  # Test first 100 cores
    try:
        px, py = utils.skycoord_to_pixel(wcs, SkyCoord(core['ra'], core['dec'], unit='deg'))
        min_dist = np.inf

        for fil in filaments[:10]:  # Test first 10 filaments
            dist_sq = (fil['pixels_x'] - px)**2 + (fil['pixels_y'] - py)**2
            dist = np.sqrt(np.min(dist_sq))
            if dist < min_dist:
                min_dist = dist

        if min_dist < 100:  # 100 pixel threshold
            associated += 1
    except Exception as e:
        pass

print(f"   Associated {associated}/100 cores with 10 filaments")

print("\nTest complete!")
