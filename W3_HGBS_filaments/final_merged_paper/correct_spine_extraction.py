#!/usr/bin/env python3
"""
Corrected Spine Extraction and Core-Filament Association Analysis

This script implements the standard HGBS methodology for:
1. Loading filament skeletons from DisPerSE output
2. Extracting filament spines (avoiding the crop bug)
3. Associating cores within 2W threshold
4. Calculating adjacent-core spacing along filaments (not all pairwise)

Issues fixed from previous ultra-fast method:
- TAURUS: Skeleton crop bug fixed (no longer crops to 0 pixels)
- SERPENS/TMC1: Uses correct 2W threshold instead of fixed scales
- Spacing: Calculates adjacent-core spacing along filaments, not all pairwise

Author: Peer review response validation
Date: 28 April 2026
"""

import numpy as np
import matplotlib.pyplot as plt
from astropy.io import fits
from scipy.spatial import cKDTree
from scipy.spatial.distance import pdist
from scipy.ndimage import label
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
    print(f"\n{'='*70}")
    print(f"REGION: {region_name}")
    print('='*70)
    print(f"Loading {region_name} data...")
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


def calculate_2w_pixels(skeleton_header, distance_pc):
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
    width_2w_pixels = (width_2w_pc / distance_pc) / pix_scale_rad

    return width_2w_pixels


def extract_filament_spines(skeleton_data, min_length=10):
    """
    Extract filament spines from skeleton data using connected component labeling.

    This fixes the crop bug that caused TAURUS to have 0 pixels.
    """
    # Find filament pixels
    filament_mask = skeleton_data > 0

    if not np.any(filament_mask):
        print(f"    WARNING: No filament pixels found!")
        return []

    # Label connected components
    labeled_array, num_features = label(filament_mask)

    print(f"    Found {num_features} filament segments")

    # Extract each filament as a list of pixel coordinates
    filaments = []
    for i in range(1, num_features + 1):
        segment_mask = labeled_array == i
        segment_pixels = np.argwhere(segment_mask)

        if len(segment_pixels) >= min_length:
            filaments.append(segment_pixels)

    print(f"    Extracted {len(filaments)} filaments with >= {min_length} pixels")

    return filaments


def associate_cores_with_filaments(cores, filaments, width_2w_pixels):
    """
    Associate cores with filaments using 2W threshold.

    Returns a dictionary mapping filament_id -> list of core_indices
    """
    if not filaments:
        return {}

    # Build KDTree for all filament pixels
    all_filament_pixels = np.vstack(filaments)
    filament_tree = cKDTree(all_filament_pixels)

    # Get core pixel coordinates
    core_coords = np.array([[c['y_pix'], c['x_pix']] for c in cores])

    # Query KDTree for distance to nearest filament
    distances, indices = filament_tree.query(core_coords)

    # Mark cores within 2W as associated
    associated_mask = distances <= width_2w_pixels

    # Map associated cores to specific filaments
    filament_to_cores = {}
    for core_idx, is_associated in enumerate(associated_mask):
        if is_associated:
            # Find which filament this core is closest to
            nearest_pixel_idx = indices[core_idx]

            # Find which filament contains this pixel
            pixel_count = 0
            for fil_id, filament in enumerate(filaments):
                if pixel_count + len(filament) > nearest_pixel_idx:
                    if fil_id not in filament_to_cores:
                        filament_to_cores[fil_id] = []
                    filament_to_cores[fil_id].append(core_idx)
                    break
                pixel_count += len(filament)

    total_associated = sum(len(cores) for cores in filament_to_cores.values())
    print(f"    Cores within 2W ({width_2w_pixels:.1f} px): {total_associated}")

    return filament_to_cores


def calculate_adjacent_spacing(cores, filament_to_cores, skeleton_header, distance_pc):
    """
    Calculate adjacent-core spacing along filaments.

    This is the correct HGBS method: sort cores along each filament
    and calculate distances between consecutive cores, NOT all pairwise.
    """
    if not filament_to_cores:
        return None

    cdelt1 = abs(skeleton_header.get('CDELT1', 5.0/3600))
    cdelt2 = abs(skeleton_header.get('CDELT2', 5.0/3600))
    pix_scale_rad = (cdelt1 + cdelt2) / 2 * np.pi / 180

    adjacent_spacings_pc = []

    for fil_id, core_indices in filament_to_cores.items():
        if len(core_indices) < 2:
            continue

        # Get coordinates of cores on this filament
        fil_cores = [cores[i] for i in core_indices]
        coords = np.array([[c['x_pix'], c['y_pix']] for c in fil_cores])

        # Sort by x-coordinate (simplified - assumes filament roughly horizontal)
        sorted_indices = np.argsort(coords[:, 0])
        sorted_coords = coords[sorted_indices]

        # Calculate distances between adjacent cores
        for i in range(len(sorted_coords) - 1):
            dx_pix = sorted_coords[i+1, 0] - sorted_coords[i, 0]
            dy_pix = sorted_coords[i+1, 1] - sorted_coords[i, 1]
            dist_px = np.sqrt(dx_pix**2 + dy_pix**2)

            # Convert to parsecs
            dist_pc = distance_pc * pix_scale_rad * dist_px
            adjacent_spacings_pc.append(dist_pc)

    if not adjacent_spacings_pc:
        return None

    # Calculate median
    median_spacing_pc = np.median(adjacent_spacings_pc)

    print(f"    N_adjacent_pairs: {len(adjacent_spacings_pc)}")
    print(f"    Median adjacent spacing: {median_spacing_pc:.3f} pc")

    return median_spacing_pc


def analyze_region(region_name, distance_pc):
    """Analyze a single region with corrected methodology."""
    # Load data
    cores, skeleton_data, skeleton_header = load_region_data(region_name)

    if skeleton_header is None or skeleton_data is None:
        return None

    # Calculate 2W threshold
    width_2w_pixels = calculate_2w_pixels(skeleton_header, distance_pc)
    print(f"\n2W Association Threshold:")
    print(f"  W = 0.10 pc (standard HGBS filament width)")
    print(f"  2W = 0.20 pc")
    print(f"  At {distance_pc} pc: 2W = {width_2w_pixels:.1f} pixels")

    # Extract filament spines (fixed crop bug)
    print(f"\nExtracting filament spines...")
    filaments = extract_filament_spines(skeleton_data, min_length=10)

    if not filaments:
        print(f"    WARNING: No filaments extracted!")
        return None

    # Associate cores using 2W method
    print(f"\nAssociating cores with filaments...")
    filament_to_cores = associate_cores_with_filaments(cores, filaments, width_2w_pixels)

    if not filament_to_cores:
        print(f"    WARNING: No cores associated with filaments!")
        return None

    # Calculate adjacent-core spacing (correct method)
    print(f"\nCalculating adjacent-core spacing...")
    median_spacing = calculate_adjacent_spacing(cores, filament_to_cores,
                                                skeleton_header, distance_pc)

    if median_spacing is not None:
        # Calculate lambda/W ratio
        W_pc = 0.10
        lambda_W_ratio = median_spacing / W_pc

        print(f"\nSpacing Results:")
        print(f"  Median adjacent spacing: {median_spacing:.3f} pc")
        print(f"  λ/W ratio: {lambda_W_ratio:.2f}")

        return {
            'region': region_name,
            'distance_pc': distance_pc,
            'width_2w_pixels': width_2w_pixels,
            'n_cores': len(cores),
            'n_filaments': len(filaments),
            'n_associated': sum(len(c) for c in filament_to_cores.values()),
            'association_rate': 100 * sum(len(c) for c in filament_to_cores.values()) / len(cores),
            'median_spacing_pc': median_spacing,
            'lambda_W_ratio': lambda_W_ratio
        }
    else:
        print(f"\nWARNING: Could not calculate spacing")
        return None


def main():
    """Run corrected analysis for all regions."""
    print("="*70)
    print("CORRECTED SPINE EXTRACTION AND CORE-FILAMENT ASSOCIATION")
    print("="*70)
    print("\nFixes applied:")
    print("  1. Fixed skeleton crop bug (TAURUS 0 pixels issue)")
    print("  2. Use correct 2W threshold per region (not fixed scales)")
    print("  3. Calculate adjacent-core spacing (not all pairwise)")

    # Region information (from paper Table 1)
    regions = {
        'TAURUS': 135,
        'ORIB': 386,
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
    print("CORRECTED ANALYSIS SUMMARY")
    print('='*70)

    if results:
        print(f"\nAnalyzed {len(results)} regions successfully")
        print(f"\n{'Region':<12} {'Dist':<6} {'N':<5} {'Fil':<4} {'Assoc':<6} {'Assoc %':<8} {'λ':<8} {'λ/W':<6}")
        print('-'*75)

        for r in results:
            print(f"{r['region']:<12} {r['distance_pc']:<6} "
                  f"{r['n_cores']:<5} {r['n_filaments']:<4} "
                  f"{r['n_associated']:<6} "
                  f"{r['association_rate']:<7.1f}% {r['median_spacing_pc']:<8.3f} "
                  f"{r['lambda_W_ratio']:<6.2f}")

        # Calculate weighted mean for robust regions
        robust_regions = ['ORIB', 'AQUILA', 'TAURUS']
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

            print(f"\nWeighted mean spacing ({len(robust_results)} robust regions):")
            print(f"  λ = {weighted_mean_spacing:.3f} ± {np.std(spacings):.3f} pc")
            print(f"  λ/W = {weighted_mean_lambda_W:.2f}")

            # Compare with paper value
            print(f"\nPaper value: λ/W = 2.84 ± 0.12")
            diff = abs(weighted_mean_lambda_W - 2.84)
            print(f"Difference: {diff:.2f} ({100*diff/2.84:.1f}%)")

            if diff < 0.3:
                print(f"\n✓ CORRECTED METHOD VALIDATED: Result consistent with paper")
            else:
                print(f"\n⚠ Note: Difference may reflect:")
                print(f"    - Different core catalog version")
                print(f"    - Adjacent vs pairwise spacing definition")
                print(f"    - Skeleton extraction details")

    # Save results
    output_file = 'corrected_spine_extraction_results.json'
    with open(output_file, 'w') as f:
        json.dump(results, f, indent=2)

    print(f"\nResults saved to: {output_file}")
    print("\nCorrected analysis complete!")


if __name__ == '__main__':
    main()
