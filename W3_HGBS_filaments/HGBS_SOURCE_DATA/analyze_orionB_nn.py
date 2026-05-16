#!/usr/bin/env python3
"""
Focused NN analysis for Orion B only.
"""
import numpy as np
from astropy.io import fits
from astropy import units as u
from astropy.coordinates import SkyCoord
from astropy.wcs import WCS, utils
from scipy import ndimage
from collections import defaultdict
import json

def load_catalog(catalog_path):
    """Load core catalog."""
    print(f"Loading catalog from {catalog_path}...")
    cores = []
    with open(catalog_path, 'r', encoding='latin-1', errors='ignore') as f:
        lines = f.readlines()

    for line in lines:
        parts = line.split()
        if len(parts) >= 4:
            try:
                int(parts[0])  # First part should be ID
                ra_str, dec_str = None, None
                for i, part in enumerate(parts[1:], 1):
                    if ':' in part and i < len(parts) - 1:
                        if ra_str is None:
                            ra_str = part
                        elif dec_str is None:
                            dec_str = part
                            break

                if ra_str and dec_str:
                    coord = SkyCoord(ra_str, dec_str, unit=(u.hourangle, u.deg))
                    cores.append({'id': int(parts[0]), 'ra': coord.ra.deg, 'dec': coord.dec.deg})
            except:
                pass

    print(f"  Loaded {len(cores)} cores")
    return cores

def load_skeleton(skeleton_path, downsample=4):
    """Load and downsample skeleton."""
    print(f"Loading skeleton from {skeleton_path}...")
    with fits.open(skeleton_path) as hdul:
        skeleton = hdul[0].data.astype(np.float64)
        wcs = WCS(hdul[0].header)

    print(f"  Original shape: {skeleton.shape}")

    # Downsample
    skeleton_small = skeleton[::downsample, ::downsample]
    print(f"  Downsampled shape: {skeleton_small.shape}")

    # Scale WCS
    wcs_small = wcs.deepcopy()
    wcs_small.wcs.crpix = np.array(wcs.wcs.crpix) / downsample
    wcs_small.wcs.cdelt = wcs.wcs.cdelt * downsample

    return skeleton_small, wcs_small

def extract_filaments(skeleton, threshold=0.1, min_size=20):
    """Extract filaments from skeleton."""
    print("Extracting filaments...")
    mask = skeleton > threshold
    labeled, n_features = ndimage.label(mask)
    print(f"  Found {n_features} features at threshold {threshold}")

    filaments = []
    for i in range(1, n_features + 1):
        yp, xp = np.where(labeled == i)
        if len(yp) >= min_size:
            filaments.append({'id': i, 'y': yp, 'x': xp})

    print(f"  Extracted {len(filaments)} filaments (min_size={min_size})")
    return filaments

def associate_cores(cores, filaments, wcs, distance_pc, width_pc=0.1):
    """Associate cores with filaments using 2W threshold."""
    print("Associating cores with filaments...")

    # Convert 2W to pixels (assuming distance_pc and width_pc in pc)
    # For Orion B at 386 pc, 0.1 pc = 0.1/386 rad = 0.000259 rad
    # At typical pixel scale ~5 arcsec/pixel = 0.00145 rad/pixel
    # 0.1 pc ~ 18 pixels for downsampled by 4
    assoc_threshold_px = 20

    core_assoc = {}
    for i, core in enumerate(cores):
        try:
            px, py = utils.skycoord_to_pixel(wcs, SkyCoord(core['ra'], core['dec'], unit='deg'))
            min_dist = float('inf')
            closest = None
            for fil in filaments:
                d = np.sqrt(np.min((fil['x'] - px)**2 + (fil['y'] - py)**2))
                if d < min_dist:
                    min_dist = d
                    closest = fil['id']
            if min_dist < assoc_threshold_px:
                core_assoc[i] = closest
        except:
            pass

    print(f"  Associated {len(core_assoc)}/{len(cores)} cores")
    return core_assoc

def compute_spacings(cores, filaments, core_assoc, wcs, distance_pc):
    """Compute filament-projected NN spacings."""
    print("Computing NN spacings...")
    fil_cores = defaultdict(list)
    for ci, fi in core_assoc.items():
        fil_cores[fi].append(ci)

    spacings = []
    for fi, cis in fil_cores.items():
        if len(cis) < 2:
            continue
        fil = next(f for f in filaments if f['id'] == fi)

        # Order by position along filament
        positions = []
        for ci in cis:
            try:
                px, py = utils.skycoord_to_pixel(wcs, SkyCoord(cores[ci]['ra'], cores[ci]['dec'], unit='deg'))
                closest_idx = np.argmin((fil['x'] - px)**2 + (fil['y'] - py)**2)
                positions.append((closest_idx, ci))
            except:
                pass
        positions.sort()
        ordered_cis = [p[1] for p in positions]

        # Compute spacings
        coords = SkyCoord(ra=[cores[i]['ra'] for i in ordered_cis]*u.deg,
                         dec=[cores[i]['dec'] for i in ordered_cis]*u.deg)
        for j in range(len(coords)-1):
            sep_pc = coords[j].separation(coords[j+1]).radian * distance_pc
            spacings.append(sep_pc)

    print(f"  Computed {len(spacings)} spacings")
    return np.array(spacings)

def analyze_orionB():
    """Analyze Orion B."""
    base = '/Users/gjw255/astrodata/SWARM/ASTRA-dev-main/W3_HGBS_filaments/HGBS_SOURCE_DATA'

    print("\n" + "="*60)
    print("ORION B NN ANALYSIS")
    print("="*60)

    # Load data
    skeleton_path = f'{base}/HGBS_ORIB/HGBS_orionB_skeleton_map_thresh50.fits'
    catalog_path = f'{base}/HGBS_ORIB/HGBS_orionB_observed_core_catalog.txt'

    cores = load_catalog(catalog_path)
    skeleton, wcs = load_skeleton(skeleton_path, downsample=4)

    # Try different thresholds
    for threshold in [0.1, 0.5, 1.0, 2.0, 5.0, 10.0]:
        print(f"\n--- Threshold = {threshold} ---")
        filaments = extract_filaments(skeleton, threshold=threshold, min_size=20)

        if len(filaments) == 0:
            print("  No filaments found, skipping")
            continue

        core_assoc = associate_cores(cores, filaments, wcs, distance_pc=386)

        if len(core_assoc) < 10:
            print(f"  Too few associations ({len(core_assoc)}), skipping")
            continue

        spacings = compute_spacings(cores, filaments, core_assoc, wcs, distance_pc=386)

        if len(spacings) > 0:
            print(f"\n  RESULTS at threshold {threshold}:")
            print(f"    NN median: {np.median(spacings):.4f} pc")
            print(f"    NN mean:   {np.mean(spacings):.4f} pc")
            print(f"    NN std:    {np.std(spacings):.4f} pc")
            print(f"    λ/W:       {np.median(spacings)/0.1:.2f}")

            # Save result
            result = {
                'region': 'Orion B',
                'threshold': threshold,
                'n_cores': len(cores),
                'n_filaments': len(filaments),
                'n_associated': len(core_assoc),
                'n_spacings': len(spacings),
                'nn_median_pc': float(np.median(spacings)),
                'nn_mean_pc': float(np.mean(spacings)),
                'nn_std_pc': float(np.std(spacings)),
                'lambda_over_W': float(np.median(spacings) / 0.1),
            }

            with open(f'{base}/orionB_nn_result.json', 'w') as f:
                json.dump(result, f, indent=2)

            print(f"  Result saved to orionB_nn_result.json")
            break
    else:
        print("\nNo valid results obtained from any threshold")
        return {'error': 'No spacings computed'}

if __name__ == '__main__':
    analyze_orionB()
