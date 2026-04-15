#!/usr/bin/env python3

# Copyright 2024-2026 Glenn J. White (The Open University / RAL Space)
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""
Quick test of core spacing calculation for Orion B.
"""
import numpy as np
from scipy import ndimage
from astropy.io import fits

print("Loading Orion B data...")
skeleton_file = '/Users/gjw255/astrodata/SWARM/ASTRA/HGBS_ORIB/HGBS_orionB_skeleton_map_thresh50.fits'
results_file = '/Users/gjw255/astrodata/SWARM/ASTRA/HGBS_ORIB/phase2_results.npz'

# Load skeleton
with fits.open(skeleton_file) as hdul:
    skeleton = hdul[0].data
    header = hdul[0].header

# Load cores
data = np.load(results_file, allow_pickle=True)
cores = data['cores']
cores_on_filaments = [c for c in cores if c.get('on_filament', False)]

print(f"Total cores: {len(cores)}")
print(f"Cores on filaments: {len(cores_on_filaments)}")

# Simple test: calculate 2D nearest-neighbor distances (what was likely done before)
from scipy.spatial import cKDTree

coords = np.array([[c['x_pix'], c['y_pix']] for c in cores_on_filaments])
tree = cKDTree(coords)
nn_dists, _ = tree.query(coords, k=2)
nn_dists = nn_dists[:, 1]  # Nearest neighbor (excluding self)

# Convert to pc
pixel_size_pc = 0.00378
nn_dists_pc = nn_dists * pixel_size_pc

print(f"\n2D Nearest-Neighbor Distances (ORIGINAL METHOD):")
print(f"  Median: {np.median(nn_dists_pc):.3f} pc")
print(f"  Mean:   {np.mean(nn_dists_pc):.3f} pc")

# Now try proper filament-by-filament method
print(f"\nExtracting filaments...")
skeleton_binary = skeleton > 0
labeled, num_filaments = ndimage.label(skeleton_binary)

print(f"Found {num_filaments} filaments")

# Find filaments with cores
filament_stats = []
for i in range(1, min(num_filaments + 1, 1000)):  # Limit for speed
    filament_mask = labeled == i
    pixel_count = np.sum(filament_mask)

    if pixel_count < 50:  # Skip small filaments
        continue

    # Find cores on this filament
    cores_on_this = []
    for core in cores_on_filaments:
        x, y = int(core['x_pix']), int(core['y_pix'])
        if filament_mask[y, x]:
            cores_on_this.append(core)

    if len(cores_on_this) >= 2:
        # Get coordinates
        these_coords = np.array([[c['x_pix'], c['y_pix']] for c in cores_on_this])

        # Calculate nearest neighbor within this filament
        if len(these_coords) >= 2:
            tree_fil = cKDTree(these_coords)
            nn_fil, _ = tree_fil.query(these_coords, k=2)
            nn_fil = nn_fil[:, 1]
            nn_fil_pc = nn_fil * pixel_size_pc

            filament_stats.append({
                'id': i,
                'n_cores': len(cores_on_this),
                'median_spacing': np.median(nn_fil_pc),
                'spacings': nn_fil_pc
            })

print(f"\nFilaments with ≥2 cores: {len(filament_stats)}")

if filament_stats:
    # Collect all spacings
    all_spacings = []
    for fs in filament_stats:
        all_spacings.extend(fs['spacings'])

    all_spacings = np.array(all_spacings)

    print(f"\nPROPER Filament-by-Filament Method:")
    print(f"  Total measurements: {len(all_spacings)}")
    print(f"  Median: {np.median(all_spacings):.3f} pc")
    print(f"  Mean:   {np.mean(all_spacings):.3f} pc")

    # Filament-by-filament median
    filament_medians = [fs['median_spacing'] for fs in filament_stats]

    print(f"\n  Median of filament medians: {np.median(filament_medians):.3f} pc")
    print(f"  Mean of filament medians:   {np.mean(filament_medians):.3f} pc")

print(f"\nCOMPARISON:")
print(f"  2D NN method (original):  {np.median(nn_dists_pc):.3f} pc")
print(f"  Proper filament method:  {np.median(all_spacings) if filament_stats else 'N/A'} pc")
