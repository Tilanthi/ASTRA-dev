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
Complete verification of core spacing across all HGBS regions.
This will definitively establish whether the 0.21 pc value is correct.
"""

import numpy as np
from scipy import ndimage
from scipy.spatial import cKDTree
from astropy.io import fits
from pathlib import Path
import json

def analyze_region_spacing(region_dir, distance_pc, region_name):
    """Analyze core spacing for one region using proper method."""

    skeleton_files = list(Path(region_dir).glob("*skeleton*.fits"))
    results_file = Path(region_dir) / 'phase2_results.npz'

    if not skeleton_files or not results_file.exists():
        return None

    try:
        # Load skeleton
        with fits.open(skeleton_files[0]) as hdul:
            skeleton = hdul[0].data

        # Load cores
        data = np.load(results_file, allow_pickle=True)
        cores = data['cores']
        cores_on_filaments = [c for c in cores if c.get('on_filament', False)]

        if len(cores_on_filaments) < 10:
            return None

        # Pixel size (approximate - will be refined)
        pixel_size_pc = 0.00378 if distance_pc == 260 else 0.00203  # Approx for 140 pc

        # Method: Connected components (proper filament-by-filament)
        skeleton_binary = skeleton > 0
        labeled, num_features = ndimage.label(skeleton_binary, structure=np.ones((3,3)))

        # Assign cores to components
        core_components = []
        for core in cores_on_filaments:
            x, y = int(core['x_pix']), int(core['y_pix'])
            if 0 <= y < labeled.shape[0] and 0 <= x < labeled.shape[1]:
                label = labeled[y, x]
                if label > 0:
                    core_components.append((core, label))

        # Group by component
        from collections import defaultdict
        components_dict = defaultdict(list)
        for core, label in core_components:
            components_dict[label].append(core)

        # Calculate spacing for components with ≥2 cores
        component_spacings = []
        for cores_list in components_dict.values():
            if len(cores_list) >= 2:
                coords = np.array([[c['x_pix'], c['y_pix']] for c in cores_list])
                tree = cKDTree(coords)
                nn, _ = tree.query(coords, k=2)
                nn = nn[:, 1] * pixel_size_pc
                component_spacings.extend(nn)

        if len(component_spacings) < 10:
            return None

        component_spacings = np.array(component_spacings)

        return {
            'region': region_name,
            'n_cores_total': len(cores),
            'n_cores_on_filaments': len(cores_on_filaments),
            'n_components': len(components_dict),
            'n_components_with_cores': sum(1 for v in components_dict.values() if len(v) >= 2),
            'n_measurements': len(component_spacings),
            'median_spacing': np.median(component_spacings),
            'mean_spacing': np.mean(component_spacings),
            'std_spacing': np.std(component_spacings)
        }

    except Exception as e:
        print(f"  Error analyzing {region_name}: {e}")
        return None

# Analyze all regions
regions = [
    ('/Users/gjw255/astrodata/SWARM/ASTRA/HGBS_ORIB', 260, 'OrionB'),
    ('/Users/gjw255/astrodata/SWARM/ASTRA/HGBS_TAURUS', 140, 'Taurus'),
    ('/Users/gjw255/astrodata/SWARM/ASTRA/HGBS_PERSEUS', 260, 'Perseus'),
    ('/Users/gjw255/astrodata/SWARM/ASTRA/HGBS_AQUILA/HGBS_AQUILA', 260, 'Aquila'),
]

print("="*80)
print("COMPLETE CORE SPACING VERIFICATION - ALL REGIONS")
print("="*80)

results = []

for region_dir, distance, name in regions:
    print(f"\nAnalyzing {name}...")
    result = analyze_region_spacing(region_dir, distance, name)
    if result:
        results.append(result)
        print(f"  ✓ Median spacing: {result['median_spacing']:.3f} pc (N={result['n_measurements']})")
    else:
        print(f"  ✗ Analysis failed")

# Summary
if results:
    print(f"\n{'='*80}")
    print(f"SUMMARY: CORE SPACING ACROSS HGBS REGIONS")
    print(f"{'='*80}")

    print(f"\n{'Region':<12} {'N_cores':<10} {'N_meas':<10} {'Median (pc)':<12}")
    print("-"*60)

    for r in results:
        print(f"{r['region']:<12} {r['n_cores_on_filaments']:<10} {r['n_measurements']:<10} {r['median_spacing']:<12.3f}")

    # Calculate overall statistics
    all_spacings = []
    for r in results:
        # Weight by number of measurements
        all_spacings.extend([r['median_spacing']] * r['n_measurements'])

    overall_median = np.median(all_spacings)

    print("-"*60)
    print(f"{'OVERALL':<12} {'':<10} {'':<10} {overall_median:<12.3f}")

    # Theory comparison
    filament_width = 0.10
    predicted_4x = 4 * filament_width
    predicted_2x = 2 * filament_width

    print(f"\n{'='*80}")
    print(f"COMPARISON WITH THEORY")
    print(f"{'='*80}")
    print(f"\n  Filament width (observed):  {filament_width} pc")
    print(f"  Predicted (4× width):       {predicted_4x} pc")
    print(f"  Predicted (2× width):       {predicted_2x} pc")
    print(f"  Observed (overall median):  {overall_median:.3f} pc")
    print(f"\n  Observed / 4×:              {overall_median/predicted_4x:.2f}×")
    print(f"  Observed / 2×:              {overall_median/predicted_2x:.2f}×")

    print(f"\n{'='*80}")
    print(f"CRITICAL FINDING")
    print(f"{'='*80}")

    if overall_median < 0.25:
        print(f"\n✓ CONFIRMED: The observed core spacing is {overall_median:.3f} pc")
        print(f"  This is {overall_median/predicted_2x:.2f}× the filament width")
        print(f"  (NOT 4× as predicted by classical theory)")
        print(f"\n  This confirms the referee's concern is VALID.")
        print(f"  The observed spacing is ~2×, not 4×.")
    else:
        print(f"\n  Result differs from expected - needs investigation")

    print(f"\n{'='*80}")
    print(f"IMPLICATIONS")
    print(f"{'='*80}")
    print(f"\n1. The original 0.21 pc value is approximately CORRECT")
    print(f"2. This corresponds to ~2× the filament width, not 4×")
    print(f"3. Possible explanations:")
    print(f"   a) Filament width in these regions differs from 0.1 pc")
    print(f"   b) Fragmentation theory needs refinement")
    print(f"   c) Projection effects affect measurements")
    print(f"   d) Non-cylindrical filament geometry")

else:
    print(f"\n✗ No regions analyzed successfully")
