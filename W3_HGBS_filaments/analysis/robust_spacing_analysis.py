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
Robust core spacing analysis using connected components directly.
"""
import numpy as np
from scipy import ndimage
from scipy.spatial import cKDTree
from astropy.io import fits

print("="*80)
print("CORE SPACING ANALYSIS - ORION B (Connected Components)")
print("="*80)

# Load data
skeleton_file = '/Users/gjw255/astrodata/SWARM/ASTRA/HGBS_ORIB/HGBS_orionB_skeleton_map_thresh50.fits'
results_file = '/Users/gjw255/astrodata/SWARM/ASTRA/HGBS_ORIB/phase2_results.npz'

with fits.open(skeleton_file) as hdul:
    skeleton = hdul[0].data

data = np.load(results_file, allow_pickle=True)
cores = data['cores']
cores_on_filaments = [c for c in cores if c.get('on_filament', False)]

pixel_size_pc = 0.00378

print(f"\nData: {len(cores_on_filaments)} cores on filaments")
print(f"Skeleton: {np.sum(skeleton > 0)} pixels")

# Method 1: Original 2D nearest neighbor
coords = np.array([[c['x_pix'], c['y_pix']] for c in cores_on_filaments])
tree = cKDTree(coords)
nn_dists, _ = tree.query(coords, k=2)
nn_2d_pc = nn_dists[:, 1] * pixel_size_pc

print(f"\nMethod 1 (2D NN): {np.median(nn_2d_pc):.3f} pc")

# Method 2: Pairwise distances
from scipy.spatial.distance import pdist
pair_dists = pdist(coords, metric='euclidean')
pair_dists_pc = pair_dists * pixel_size_pc

print(f"Method 2 (Pairwise): {np.median(pair_dists_pc):.3f} pc")

# Method 3: Connected component analysis
skeleton_binary = skeleton > 0

# Use a very conservative label structure
labeled, num_features = ndimage.label(skeleton_binary, structure=np.ones((3,3)))

print(f"\nConnected components: {num_features}")

# Find which component each core belongs to
core_components = []
for core in cores_on_filaments:
    x, y = int(core['x_pix']), int(core['y_pix'])
    if 0 <= y < labeled.shape[0] and 0 <= x < labeled.shape[1]:
        label = labeled[y, x]
        if label > 0:
            core_components.append((core, label))
        else:
            core_components.append((core, 0))
    else:
        core_components.append((core, 0))

# Group cores by component
from collections import defaultdict
components_dict = defaultdict(list)
for core, label in core_components:
    components_dict[label].append(core)

# Find components with multiple cores
multi_core_components = {k: v for k, v in components_dict.items() if len(v) >= 2}

print(f"Components with ≥2 cores: {len(multi_core_components)}")

# Calculate spacing for each component
component_spacings = []
for label, cores_list in multi_core_components.items():
    if len(cores_list) < 2:
        continue

    # Get coordinates
    these_coords = np.array([[c['x_pix'], c['y_pix']] for c in cores_list])

    # Calculate nearest neighbor within this component
    tree_comp = cKDTree(these_coords)
    nn_comp, _ = tree_comp.query(these_coords, k=2)
    nn_comp = nn_comp[:, 1]
    nn_comp_pc = nn_comp * pixel_size_pc

    component_spacings.extend(nn_comp_pc)

if component_spacings:
    component_spacings = np.array(component_spacings)

    print(f"\nMethod 3 (Connected Components):")
    print(f"  Total measurements: {len(component_spacings)}")
    print(f"  Median: {np.median(component_spacings):.3f} pc")
    print(f"  Mean: {np.mean(component_spacings):.3f} pc")

    # COMPARISON
    print(f"\n{'='*80}")
    print(f"COMPARISON")
    print(f"{'='*80}")
    print(f"  Method 1 (2D NN):            {np.median(nn_2d_pc):.3f} pc")
    print(f"  Method 2 (Pairwise):         {np.median(pair_dists_pc):.3f} pc")
    print(f"  Method 3 (Connected Comp):   {np.median(component_spacings):.3f} pc")

    # Theory comparison
    filament_width = 0.10
    predicted_4x = 4 * filament_width
    predicted_2x = 2 * filament_width

    observed = np.median(component_spacings)

    print(f"\n{'='*80}")
    print(f"THEORY COMPARISON")
    print(f"{'='*80}")
    print(f"  Filament width:        {filament_width} pc")
    print(f"  Predicted (4×):         {predicted_4x} pc")
    print(f"  Predicted (2×):         {predicted_2x} pc")
    print(f"  Observed:              {observed:.3f} pc")
    print(f"  Ratio to 4×:            {observed/predicted_4x:.2f}×")
    print(f"  Ratio to 2×:            {observed/predicted_2x:.2f}×")

    print(f"\n{'='*80}")
    print(f"CONCLUSION")
    print(f"{'='*80}")

    # Check which prediction is closer
    diff_4x = abs(observed - predicted_4x)
    diff_2x = abs(observed - predicted_2x)

    if diff_4x < diff_2x:
        print(f"  ✓ Observed spacing is closer to 4× prediction")
    elif diff_2x < diff_4x:
        print(f"  ⚠️  Observed spacing is closer to 2× prediction")
        print(f"     This suggests the original analysis was CORRECT")
        print(f"     but the theoretical prediction may need refinement")
    else:
        print(f"  Observed differs from both predictions")

    # Check robustness
    methods = [np.median(nn_2d_pc), np.median(pair_dists_pc), np.median(component_spacings)]
    method_range = max(methods) - min(methods)

    print(f"\n  Method range: {method_range:.3f} pc")
    if method_range < 0.02:
        print(f"  ✓ All methods agree: ~{np.mean(methods):.2f} pc (ROBUST)")
    else:
        print(f"  Methods vary by {method_range:.3f} pc")

else:
    print(f"\n✗ No component-based spacing calculated")

print(f"\n{'='*80}")
print(f"FINAL ANSWER")
print(f"{'='*80}")
print(f"\nThe observed core spacing in Orion B is ~{np.median(nn_2d_pc):.2f} pc")
print(f"This corresponds to {np.median(nn_2d_pc)/0.1:.1f}× the filament width")
print(f"\nClassical theory predicts 4× = 0.4 pc")
print(f"Our observation differs by {(np.median(nn_2d_pc) - 0.4):.3f} pc ({(np.median(nn_2d_pc)/0.4 - 1)*100:.1f}%)")
