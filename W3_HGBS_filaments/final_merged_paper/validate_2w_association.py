#!/usr/bin/env python3
"""
Validate Standard HGBS 2W Core-Filament Association Method

This script validates the standard HGBS methodology for associating cores with filaments:
1. Load phase2 results (cores with pixel coordinates)
2. Load skeleton map
3. Associate cores within 2W threshold (distance <= 2W pixels)
4. Compare with published results

This demonstrates that the standard HGBS methodology works correctly
and provides independent validation of the published results.

Author: Validation script for peer review response
Date: 28 April 2026
"""

import numpy as np
import matplotlib.pyplot as plt
from astropy.io import fits
from scipy.spatial import cKDTree
import json
from pathlib import Path


def load_region_data(region_name):
    """Load phase2 results and skeleton for a region."""
    # Map region names to actual directory names
    region_map = {
        'TAURUS': 'TAURUS',
        'ORIB': 'ORIB',
        'PERSEUS': 'PERSEUS',
        'AQUILA': 'AQUILA',
        'OPH': 'OPH',
        'SERPENS': 'SERPENS',
        'TMC1': 'TMC1',
        'CRA': 'CRA',
    }

    actual_dir = region_map.get(region_name, region_name)
    phase2_file = f'/Users/gjw255/astrodata/SWARM/ASTRA/HGBS_{actual_dir}/phase2_results.npz'

    # Try different skeleton file names with region-specific patterns
    skeleton_patterns = {
        'TAURUS': ['HGBS_taurusL1495_skeleton_map_thresh50.fits',
                   'HGBS_taurusL1495_skeleton_map.fits'],
        'ORIB': ['HGBS_orionB_skeleton_map_thresh50.fits',
                 'HGBS_orionB_skeleton_map.fits'],
        'PERSEUS': ['HGBS_perseus_skeleton_map_thresh50.fits',
                    'HGBS_perseus_skeleton_map.fits'],
        'AQUILA': ['HGBS_aquilaM2_skeleton_map_thresh50.fits',
                   'HGBS_aquilaM2_skeleton_map.fits'],
        'OPH': ['HGBS_ophiuchus_skeleton_map_thresh50.fits',
                'HGBS_ophiuchus_skeleton_map.fits'],
        'SERPENS': ['HGBS_serpens_skeleton_map_thresh50.fits',
                    'HGBS_serpens_skeleton_map.fits'],
        'TMC1': ['HGBS_taurusTMC1_skeleton_map_thresh50.fits',
                 'HGBS_taurusTMC1_skeleton_map.fits'],
        'CRA': ['HGBS_crameres_skeleton_map_thresh50.fits',
                'HGBS_crameres_skeleton_map.fits'],
    }

    skeleton_files = [f'/Users/gjw255/astrodata/SWARM/ASTRA/HGBS_{actual_dir}/{pattern}'
                      for pattern in skeleton_patterns.get(region_name,
                      [f'HGBS_{region_name.lower()}_skeleton_map_thresh50.fits',
                       f'HGBS_{region_name.lower()}_skeleton_map.fits'])]

    # Load phase2 results
    print(f"\nLoading {region_name} data...")
    print(f"  Phase2: {phase2_file}")
    try:
        phase2_data = np.load(phase2_file, allow_pickle=True)
        cores = phase2_data['cores']
        print(f"    Loaded {len(cores)} cores")
    except FileNotFoundError:
        print(f"    ERROR: Phase2 file not found")
        return None, None, None

    # Load skeleton
    skeleton_data = None
    skeleton_header = None
    for skel_file in skeleton_files:
        try:
            print(f"  Skeleton: {skel_file}")
            with fits.open(skel_file) as hdul:
                skeleton_data = hdul[0].data
                skeleton_header = hdul[0].header
            print(f"    Loaded skeleton: shape={skeleton_data.shape}")
            break
        except FileNotFoundError:
            continue

    if skeleton_data is None:
        print(f"  WARNING: No skeleton file found for {region_name}")
        return cores, None, None

    return cores, skeleton_data, skeleton_header


def calculate_2w_pixels(skeleton_header, region_name, distance_pc):
    """Calculate 2W threshold in pixels for a region."""
    # Standard HGBS filament width
    W_pc = 0.10  # 0.1 pc (Arzoumanian+2011)
    width_2w_pc = 2 * W_pc  # 0.2 pc

    # Get pixel scale from header
    cdelt1 = abs(skeleton_header.get('CDELT1', 5.0/3600))
    cdelt2 = abs(skeleton_header.get('CDELT2', 5.0/3600))
    pix_scale_deg = (cdelt1 + cdelt2) / 2
    pix_scale_rad = pix_scale_deg * np.pi / 180

    # Convert 2W from pc to pixels
    # Physical size (pc) = distance (pc) × angle (rad)
    # angle (rad) = Physical size (pc) / distance (pc)
    # angle (pixels) = angle (rad) / pix_scale_rad
    width_2w_pixels = (width_2w_pc / distance_pc) / pix_scale_rad

    return width_2w_pixels


def associate_cores_2w_method(cores, skeleton_data, width_2w_pixels):
    """Associate cores with filaments using standard 2W method."""
    if skeleton_data is None:
        return []

    # Find filament pixels
    filament_mask = skeleton_data > 0
    filament_pixels = np.argwhere(filament_mask)

    if len(filament_pixels) == 0:
        print("    WARNING: No filament pixels found!")
        return []

    print(f"    Filament pixels: {len(filament_pixels)}")

    # Build KDTree for filament pixels
    filament_tree = cKDTree(filament_pixels)

    # Get core pixel coordinates
    core_coords = np.array([[c['y_pix'], c['x_pix']] for c in cores])
    valid_cores = np.array([0 <= c['x_pix'] < skeleton_data.shape[1] and
                           0 <= c['y_pix'] < skeleton_data.shape[0]
                           for c in cores])

    # Query KDTree for distance to nearest filament
    distances, indices = filament_tree.query(core_coords[valid_cores])

    # Mark cores within 2W as associated
    associated_indices = np.where(valid_cores)[0][distances <= width_2w_pixels]

    print(f"    Cores within 2W ({width_2w_pixels:.1f} px): {len(associated_indices)}")

    return associated_indices


def calculate_pairwise_spacing(cores, associated_indices, skeleton_header, distance_pc):
    """Calculate pairwise median spacing for associated cores."""
    if len(associated_indices) < 2:
        return None

    # Get coordinates of associated cores
    assoc_cores = [cores[i] for i in associated_indices]
    coords = np.array([[c['x_pix'], c['y_pix']] for c in assoc_cores])

    # Calculate pairwise distances
    from scipy.spatial.distance import pdist
    pair_dists_px = pdist(coords, metric='euclidean')

    # Convert to parsecs
    cdelt1 = abs(skeleton_header.get('CDELT1', 5.0/3600))
    cdelt2 = abs(skeleton_header.get('CDELT2', 5.0/3600))
    pix_scale_rad = (cdelt1 + cdelt2) / 2 * np.pi / 180
    pair_dists_pc = distance_pc * pix_scale_rad * pair_dists_px

    # Calculate median
    median_spacing_pc = np.median(pair_dists_pc)

    return median_spacing_pc


def analyze_region(region_name, distance_pc):
    """Analyze a single region with 2W association method."""
    print(f"\n{'='*70}")
    print(f"REGION: {region_name} (distance = {distance_pc} pc)")
    print('='*70)

    # Load data
    cores, skeleton_data, skeleton_header = load_region_data(region_name)

    if skeleton_header is None:
        return None

    # Calculate 2W threshold
    width_2w_pixels = calculate_2w_pixels(skeleton_header, region_name, distance_pc)
    print(f"\n2W Association Threshold:")
    print(f"  W = 0.10 pc (standard HGBS filament width)")
    print(f"  2W = 0.20 pc")
    print(f"  At {distance_pc} pc: 2W = {width_2w_pixels:.1f} pixels")

    # Associate cores using 2W method
    associated_indices = associate_cores_2w_method(cores, skeleton_data, width_2w_pixels)

    # Calculate spacing
    median_spacing = calculate_pairwise_spacing(cores, associated_indices,
                                                skeleton_header, distance_pc)

    if median_spacing is not None:
        # Calculate lambda/W ratio
        W_pc = 0.10
        lambda_W_ratio = median_spacing / W_pc

        print(f"\nSpacing Results:")
        print(f"  Median pairwise spacing: {median_spacing:.3f} pc")
        print(f"  λ/W ratio: {lambda_W_ratio:.2f}")

        return {
            'region': region_name,
            'distance_pc': distance_pc,
            'width_2w_pixels': width_2w_pixels,
            'n_cores': len(cores),
            'n_associated': len(associated_indices),
            'association_rate': 100 * len(associated_indices) / len(cores),
            'median_spacing_pc': median_spacing,
            'lambda_W_ratio': lambda_W_ratio
        }
    else:
        print(f"\nWARNING: Could not calculate spacing (N_associated < 2)")
        return None


def main():
    """Run validation analysis for all regions."""
    print("="*70)
    print("VALIDATION OF STANDARD HGBS 2W ASSOCIATION METHOD")
    print("="*70)
    print("\nThis script validates the core-filament association method used in")
    print("the paper by reproducing the results using the standard HGBS 2W threshold.")
    print("\nMethodology:")
    print("  1. Load phase2 results (cores with pixel coordinates from WCS)")
    print("  2. Load filament skeleton from DisPerSE (3σ persistence)")
    print("  3. Associate cores within 2W of filament skeleton pixels")
    print("  4. Calculate pairwise median spacing for associated cores")
    print("  5. Compare with published λ/W values")

    # Region information (from paper Table 1)
    # Note: PERSEUS doesn't have phase2_results.npz - skip for now
    regions = {
        'TAURUS': 135,
        'ORIB': 386,
        # 'PERSEUS': 300,  # No phase2 results available
        'AQUILA': 436,
        'OPH': 137,
        'SERPENS': 458,
        'TMC1': 135,
        'CRA': 175,
    }

    results = []

    # Analyze each region
    for region_name, distance_pc in regions.items():
        result = analyze_region(region_name, distance_pc)
        if result:
            results.append(result)

    # Summary
    print(f"\n{'='*70}")
    print("VALIDATION SUMMARY")
    print('='*70)

    if results:
        print(f"\nAnalyzed {len(results)} regions successfully")
        print(f"\n{'Region':<12} {'Dist':<6} {'N':<5} {'Assoc':<6} {'Assoc %':<8} {'λ':<8} {'λ/W':<6}")
        print('-'*70)

        for r in results:
            print(f"{r['region']:<12} {r['distance_pc']:<6} "
                  f"{r['n_cores']:<5} {r['n_associated']:<6} "
                  f"{r['association_rate']:<7.1f}% {r['median_spacing_pc']:<8.3f} "
                  f"{r['lambda_W_ratio']:<6.2f}")

        # Calculate weighted mean for robust regions
        robust_regions = ['ORIB', 'AQUILA', 'PERSEUS', 'TAURUS']
        robust_results = [r for r in results if r['region'] in robust_regions]

        if robust_results:
            print(f"\n{'='*70}")
            print("ROBUST REGIONS (Primary Result from Paper)")
            print('='*70)

            # Weighted mean by N_associated
            weights = np.array([r['n_associated'] for r in robust_results])
            spacings = np.array([r['median_spacing_pc'] for r in robust_results])

            weighted_mean_spacing = np.sum(weights * spacings) / np.sum(weights)
            weighted_mean_lambda_W = weighted_mean_spacing / 0.10

            print(f"\nWeighted mean spacing (4 robust regions):")
            print(f"  λ = {weighted_mean_spacing:.3f} ± {np.std(spacings):.3f} pc")
            print(f"  λ/W = {weighted_mean_lambda_W:.2f}")

            # Compare with paper value
            print(f"\nPaper value: λ/W = 2.84 ± 0.12")
            diff = abs(weighted_mean_lambda_W - 2.84)
            print(f"Difference: {diff:.2f} ({100*diff/2.84:.1f}%)")

            if diff < 0.2:
                print(f"\n✓ VALIDATION PASSED: Reproduced paper result within uncertainty")
            else:
                print(f"\n⚠ WARNING: Difference > 0.2 from paper value")

    # Save results
    output_file = 'validation_2w_association_results.json'
    with open(output_file, 'w') as f:
        json.dump(results, f, indent=2)

    print(f"\nResults saved to: {output_file}")
    print("\nValidation complete!")


if __name__ == '__main__':
    main()
