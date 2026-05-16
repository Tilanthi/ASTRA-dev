#!/usr/bin/env python3
"""
Simplified nearest-neighbor spacing analysis for HGBS Orion B.

This uses existing core-filament association data and computes
nearest-neighbor spacing more efficiently.
"""

import numpy as np
from astropy.coordinates import SkyCoord
from astropy import units as u
from scipy.spatial import cKDTree
import json

# Load existing core data with filament associations
data = np.load('/Users/gjw255/astrodata/SWARM/ASTRA/HGBS_ORIB/phase2_results.npz', allow_pickle=True)
cores = data['cores']

print(f"Total cores: {len(cores)}")

# Filter to cores on filaments
on_filament = [c for c in cores if c['on_filament']]
print(f"Cores on filaments: {len(on_filament)}")

# This seems too small - the paper reports 1844 cores for Orion B
# The issue is that 'on_filament' might mean directly on skeleton pixels
# Let's use a distance-based approach instead

# Convert cores to SkyCoord for distance calculations
all_coords = SkyCoord(
    ra=[c['ra_deg'] for c in cores] * u.deg,
    dec=[c['dec_deg'] for c in cores] * u.deg
)

# Gaia DR3 distance for Orion B
distance_pc = 386

# Convert angular resolution to physical resolution
# At 386 pc, 1 arcsec = 386 * (1/206265) pc ≈ 0.0019 pc
arcsec_to_pc = distance_pc / 206265

print(f"Distance: {distance_pc} pc")
print(f"1 arcsec = {arcsec_to_pc:.6f} pc")

# For nearest-neighbor spacing, we need to:
# 1. For each core, find its nearest neighbor
# 2. Compute the distance

print("\nComputing nearest-neighbor distances...")
nn_distances = []

for i, coord in enumerate(all_coords):
    # Compute separation to all other cores
    separations = coord.separation(all_coords)

    # Find nearest neighbor (excluding self)
    separations_array = separations.arcsec  # in arcseconds
    # Set self-distance to infinity
    separations_array[i] = np.inf
    nn_sep_arcsec = np.min(separations_array)

    # Convert to physical distance
    nn_sep_pc = nn_sep_arcsec * arcsec_to_pc
    nn_distances.append(nn_sep_pc)

nn_distances = np.array(nn_distances)

print(f"Computed {len(nn_distances)} nearest-neighbor distances")

# Statistics
stats = {
    'n_cores': len(cores),
    'mean_pc': np.mean(nn_distances),
    'median_pc': np.median(nn_distances),
    'std_pc': np.std(nn_distances),
    'min_pc': np.min(nn_distances),
    'max_pc': np.max(nn_distances),
    'q25_pc': np.percentile(nn_distances, 25),
    'q75_pc': np.percentile(nn_distances, 75),
}

print("\n" + "="*70)
print("NEAREST-NEIGHBOR SPACING STATISTICS (Orion B)")
print("="*70)
for key, value in stats.items():
    print(f"{key}: {value:.4f}")

# Calculate lambda/W
width_pc = 0.1  # characteristic filament width
lambda_by_W = stats['median_pc'] / width_pc
print(f"\nMedian nearest-neighbor spacing: {stats['median_pc']:.4f} pc")
print(f"λ/W ratio: {lambda_by_W:.2f}")

print("\n" + "="*70)
print("COMPARISON WITH PAIRWISE MEDIAN")
print("="*70)
print(f"Pairwise median (paper): 0.313 pc")
print(f"Nearest-neighbor (this analysis): {stats['median_pc']:.4f} pc")
print(f"Ratio NN/PM: {stats['median_pc']/0.313:.2f}")
print("="*70)

# Save results
results = {
    'region': 'Orion B',
    'distance_pc': distance_pc,
    'n_cores': len(cores),
    'method': 'nearest_neighbor_all_pairs',
    'statistics': stats,
    'all_spacings_pc': nn_distances.tolist()
}

output_file = '/Users/gjw255/astrodata/SWARM/ASTRA/HGBS_ORIB/nearest_neighbor_simple_results.json'
with open(output_file, 'w') as f:
    json.dump(results, f, indent=2)

print(f"\nResults saved to: {output_file}")
