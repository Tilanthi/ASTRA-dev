#!/usr/bin/env python3
"""Test script for filament-projected NN analysis - fixed."""

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

# Load skeleton
print("\n1. Loading skeleton...")
hdul = fits.open(skeleton_file)
skeleton_data = hdul[0].data.astype(np.float64)
header = hdul[0].header
hdul.close()

from astropy.wcs import WCS
wcs = WCS(header)

print(f"   Skeleton shape: {skeleton_data.shape}")

# Load catalog
print("\n2. Loading catalog...")
cores = []

with open(catalog_file, 'r', encoding='latin-1', errors='ignore') as f:
    lines = f.readlines()

# Find data start - look for line starting with "1"
for i, line in enumerate(lines):
    parts = line.split()
    if len(parts) >= 8 and parts[0].isdigit() and int(parts[0]) == 1:
        print(f"   Data starts at line {i}")
        # Parse from this line
        for j in range(i, min(i + 2000, len(lines))):  # Read first 2000 lines
            line = lines[j]
            if not line.strip() or line.startswith('|'):
                continue

            parts = line.split()
            if len(parts) < 8:
                continue

            try:
                core_id = int(parts[0])
                ra_str = f"{parts[2]}:{parts[3]}:{parts[4]}"
                dec_str = f"{parts[5]}:{parts[6]}:{parts[7]}"
                coord = SkyCoord(ra_str, dec_str, unit=(u.hourangle, u.deg))
                cores.append({'id': core_id, 'ra': coord.ra.deg, 'dec': coord.dec.deg})
            except Exception:
                pass
        break

print(f"   Loaded {len(cores)} cores")

# Extract filaments - use higher threshold to reduce noise
print("\n3. Extracting filaments...")
threshold = np.percentile(skeleton_data[skeleton_data > 0], 50)  # Use median of non-zero values
print(f"   Using threshold: {threshold:.3f}")

skeleton_mask = skeleton_data > threshold
labeled, num_features = ndimage.label(skeleton_mask)
print(f"   Found {num_features} features")

# Get filaments with >= 100 pixels
filaments = []
for i in range(1, num_features + 1):
    filament_pixels = np.where(labeled == i)
    n_pixels = len(filament_pixels[0])

    if n_pixels >= 100:
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

print(f"   Extracted {len(filaments)} filaments (>= 100 pixels)")

# Associate cores
print("\n4. Associating cores with filaments...")
from astropy.wcs import utils

core_assoc = {}
association_threshold_px = 30  # Approx 2W at Orion B distance

for i, core in enumerate(cores):
    try:
        px, py = utils.skycoord_to_pixel(wcs, SkyCoord(core['ra'], core['dec'], unit='deg'))
        min_dist = np.inf
        closest_fil = None

        for fil in filaments:
            # Find distance to filament
            dist_sq = (fil['pixels_x'] - px)**2 + (fil['pixels_y'] - py)**2
            dist = np.sqrt(np.min(dist_sq))

            if dist < min_dist:
                min_dist = dist
                closest_fil = fil['id']

        if min_dist < association_threshold_px:
            core_assoc[i] = closest_fil
    except Exception:
        pass

print(f"   Associated {len(core_assoc)}/{len(cores)} cores")

# Order cores along filaments
print("\n5. Ordering cores along filaments...")
from collections import defaultdict

filament_cores = defaultdict(list)
for core_idx, fil_id in core_assoc.items():
    filament_cores[fil_id].append(core_idx)

ordered_filament_cores = {}
for fil_id, core_indices in filament_cores.items():
    if len(core_indices) < 2:
        continue

    fil = next(f for f in filaments if f['id'] == fil_id)
    core_positions = []

    for core_idx in core_indices:
        core = cores[core_idx]
        try:
            px, py = utils.skycoord_to_pixel(wcs, SkyCoord(core['ra'], core['dec'], unit='deg'))
            dist_sq = (fil['pixels_x'] - px)**2 + (fil['pixels_y'] - py)**2
            closest_idx = np.argmin(dist_sq)
            position_along_spine = closest_idx / fil['length']
            core_positions.append((position_along_spine, core_idx))
        except Exception:
            pass

    core_positions.sort(key=lambda x: x[0])
    ordered_filament_cores[fil_id] = [c[1] for c in core_positions]

print(f"   Ordered cores in {len(ordered_filament_cores)} filaments")

# Compute NN spacings
print("\n6. Computing NN spacings...")
all_spacings = []

for fil_id, core_indices in ordered_filament_cores.items():
    if len(core_indices) < 2:
        continue

    coords = SkyCoord(
        ra=[cores[i]['ra'] for i in core_indices] * u.deg,
        dec=[cores[i]['dec'] for i in core_indices] * u.deg
    )

    for i in range(len(coords) - 1):
        sep = coords[i].separation(coords[i+1])
        sep_pc = sep.radian * distance_pc
        all_spacings.append(sep_pc)

all_spacings = np.array(all_spacings)

print(f"   Computed {len(all_spacings)} NN spacings")

if len(all_spacings) > 0:
    print(f"\n{'='*60}")
    print(f"RESULTS FOR {region}")
    print(f"{'='*60}")
    print(f"   N cores total: {len(cores)}")
    print(f"   N cores associated: {len(core_assoc)}")
    print(f"   N filaments with 2+ cores: {len(ordered_filament_cores)}")
    print(f"   N NN spacings: {len(all_spacings)}")
    print(f"   NN median: {np.median(all_spacings):.4f} pc")
    print(f"   NN mean: {np.mean(all_spacings):.4f} pc")
    print(f"   NN std: {np.std(all_spacings):.4f} pc")
    print(f"   λ/W (W=0.1 pc): {np.median(all_spacings) / 0.1:.2f}")
    print(f"{'='*60}")
else:
    print(f"\nERROR: No spacings computed for {region}")

print("\nTest complete!")
