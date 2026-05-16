#!/usr/bin/env python3
"""Fast filament-projected NN analysis - optimized version."""
import numpy as np
from astropy.io import fits
from astropy import units as u
from astropy.coordinates import SkyCoord
from scipy import ndimage
from astropy.wcs import WCS
from collections import defaultdict
import json

def analyze_region_fast(region_name, skeleton_path, catalog_path, distance_pc, width_pc=0.1):
    """Analyze a single region with optimized approach."""

    print(f"\n{'='*60}")
    print(f"{region_name.upper()}")
    print(f"{'='*60}")

    # Load skeleton (downsample for speed)
    print("Loading skeleton...")
    hdul = fits.open(skeleton_path)
    skeleton = hdul[0].data.astype(np.float64)
    wcs = WCS(hdul[0].header)
    hdul.close()

    # Downsample skeleton by factor of 2 for speed
    print(f"  Original shape: {skeleton.shape}")
    skeleton_small = skeleton[::2, ::2]
    print(f"  Downsampled shape: {skeleton_small.shape}")

    # Scale WCS for downsampled image
    wcs_small = wcs.deepcopy()
    wcs_small.wcs.ctype = wcs.wcs.ctype
    wcs_small.wcs.crval = wcs.wcs.crval
    wcs_small.wcs.crpix = np.array(wcs.wcs.crpix) / 2
    wcs_small.wcs.cdelt = wcs.wcs.cdelt * 2

    # Load catalog (limit to first N for speed)
    print(f"Loading catalog...")
    cores = []
    with open(catalog_path, 'r', encoding='latin-1', errors='ignore') as f:
        lines = f.readlines()

    for line in lines:
        parts = line.split()
        # Look for lines with at least 4 parts where first part is a number
        if len(parts) >= 4:
            try:
                # Try to parse first part as ID
                int(parts[0])
                # RA and Dec should be in sexagesimal format with colons
                # Find the RA and Dec fields
                ra_str, dec_str = None, None
                for i, part in enumerate(parts[1:], 1):
                    if ':' in part and i < len(parts) - 1:
                        # Check if this looks like RA/Dec
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

        if len(cores) >= 2000:  # Safety limit
            break

    print(f"  Loaded {len(cores)} cores")

    # Extract filaments from downsampled skeleton
    print("Extracting filaments...")
    # Use fixed low threshold instead of percentile
    threshold = 0.1  # Low threshold for skeleton data
    mask = skeleton_small > threshold
    labeled, n_features = ndimage.label(mask)
    print(f"  Found {n_features} features at threshold {threshold:.3f}")

    filaments = []
    for i in range(1, min(n_features + 1, 5000)):
        yp, xp = np.where(labeled == i)
        if len(yp) >= 20:  # Lower threshold for downsampled
            filaments.append({'id': i, 'y': yp, 'x': xp})

    print(f"  Extracted {len(filaments)} filaments")

    # Associate cores
    print("Associating cores...")
    from astropy.wcs import utils
    core_assoc = {}
    assoc_threshold_px = 15  # Adjusted for downsampling

    for i, core in enumerate(cores):
        try:
            px, py = utils.skycoord_to_pixel(wcs_small, SkyCoord(core['ra'], core['dec'], unit='deg'))
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

    # Order cores and compute spacings
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
                px, py = utils.skycoord_to_pixel(wcs_small, SkyCoord(cores[ci]['ra'], cores[ci]['dec'], unit='deg'))
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

    spacings = np.array(spacings)
    print(f"  Computed {len(spacings)} spacings")

    if len(spacings) > 0:
        print(f"\n  NN median: {np.median(spacings):.4f} pc")
        print(f"  λ/W: {np.median(spacings)/width_pc:.2f}")

        return {
            'region': region_name,
            'n_cores': len(cores),
            'n_associated': len(core_assoc),
            'n_spacings': len(spacings),
            'nn_median_pc': float(np.median(spacings)),
            'nn_mean_pc': float(np.mean(spacings)),
            'nn_std_pc': float(np.std(spacings)),
            'lambda_over_W': float(np.median(spacings) / width_pc),
        }
    else:
        return {'region': region_name, 'error': 'No spacings computed'}

# Analyze all regions
results = []
base = '/Users/gjw255/astrodata/SWARM/ASTRA-dev-main/W3_HGBS_filaments/HGBS_SOURCE_DATA'

regions = [
    ('Orion B', f'{base}/HGBS_ORIB/HGBS_orionB_skeleton_map_thresh50.fits',
               f'{base}/HGBS_ORIB/HGBS_orionB_observed_core_catalog.txt', 386),
    ('Aquila', f'{base}/HGBS_AQUILA/HGBS_AQUILA/HGBS_aquilaM2_skeleton_map.fits',
              f'{base}/HGBS_AQUILA/HGBS_AQUILA/HGBS_aquilaM2_derived_core_catalog.txt', 436),
    ('Perseus', f'{base}/HGBS_PERSEUS/HGBS_perseus_skeleton_map_thresh20.fits',
               f'{base}/HGBS_PERSEUS/HGBS_PERSEUS/HGBS_perseus_observed_core_catalog.txt', 296),
]

for name, skel, cat, dist in regions:
    try:
        result = analyze_region_fast(name, skel, cat, dist)
        results.append(result)
    except Exception as e:
        print(f"ERROR analyzing {name}: {e}")
        results.append({'region': name, 'error': str(e)})

# Compute weighted mean
valid = [r for r in results if 'error' not in r]
if valid:
    weights = np.array([r['n_spacings'] for r in valid])
    values = np.array([r['nn_median_pc'] for r in valid])
    weighted_mean = np.sum(weights * values) / np.sum(weights)
    lambda_W_mean = np.sum(weights * np.array([r['lambda_over_W'] for r in valid])) / np.sum(weights)

    print(f"\n{'='*60}")
    print("WEIGHTED MEAN RESULTS")
    print(f"{'='*60}")
    print(f"NN median: {weighted_mean:.4f} pc")
    print(f"λ/W: {lambda_W_mean:.2f}")

    results.append({'weighted_mean': {
        'nn_median_pc': float(weighted_mean),
        'lambda_over_W': float(lambda_W_mean),
    }})

# Save results
with open(f'{base}/filament_nn_results_fast.json', 'w') as f:
    json.dump(results, f, indent=2)

print(f"\nResults saved to filament_nn_results_fast.json")
