#!/usr/bin/env python3
"""
Compute nearest-neighbor spacing statistics from HGBS core and skeleton data.

This script addresses the L/3 convergence problem by computing proper
nearest-neighbor (adjacent-core) spacing along filaments, rather than
the problematic pairwise median statistic.

For each HGBS region:
1. Load the skeleton map (FITS file)
2. Load the core catalog (RA/Dec positions)
3. For each core, find the nearest point on the skeleton
4. Associate cores with filaments
5. Compute position along filament skeleton
6. Sort cores by position and compute nearest-neighbor distances
7. Calculate median NN spacing per filament and for the region
"""

import numpy as np
from astropy.io import fits
from astropy.coordinates import SkyCoord
import astropy.units as u
from scipy.spatial import cKDTree
from scipy import ndimage
from collections import defaultdict
import os
import warnings
warnings.filterwarnings('ignore')

try:
    from sklearn.decomposition import PCA
    HAS_SKLEARN = True
except ImportError:
    HAS_SKLEARN = False
    print("Warning: sklearn not available, using fallback method for filament ordering")

# HGBS regions with Gaia DR3 distances (pc)
HGBS_REGIONS = {
    'Taurus': {
        'path': '/Users/gjw255/astrodata/SWARM/ASTRA/HGBS_TAURUS',
        'distance': 135,
        'skeleton_file': 'HGBS_taurusL1495_skeleton_map.fits',
        'core_catalog': 'HGBS_taurusL1495_derived_core_catalog.txt',
    },
    'OrionB': {
        'path': '/Users/gjw255/astrodata/SWARM/ASTRA/HGBS_ORIB',
        'distance': 386,
        'skeleton_file': None,  # Will search for it
        'core_catalog': None,
    },
    'Aquila': {
        'path': '/Users/gjw255/astrodata/SWARM/ASTRA/HGBS_AQUILA',
        'distance': 436,
        'skeleton_file': None,
        'core_catalog': None,
    },
    'Perseus': {
        'path': '/Users/gjw255/astrodata/SWARM/ASTRA/HGBS_PERSEUS',
        'distance': 296,
        'skeleton_file': None,
        'core_catalog': None,
    },
    'Ophiuchus': {
        'path': '/Users/gjw255/astrodata/SWARM/ASTRA/HGBS_OPH',
        'distance': 137,
        'skeleton_file': None,
        'core_catalog': None,
    },
    'Serpens': {
        'path': '/Users/gjw255/astrodata/SWARM/ASTRA/HGBS_SERPENS',
        'distance': 458,
        'skeleton_file': None,
        'core_catalog': None,
    },
    'TMC1': {
        'path': '/Users/gjw255/astrodata/SWARM/ASTRA/HGBS_TMC1',
        'distance': 135,
        'skeleton_file': None,
        'core_catalog': None,
    },
    'CRA': {
        'path': '/Users/gjw255/astrodata/SWARM/ASTRA/HGBS_CRA',
        'distance': 150,
        'skeleton_file': None,
        'core_catalog': None,
    },
}

def find_data_files(region_path, region_name):
    """Find skeleton and catalog files in a region directory."""
    import os
    import glob

    # Find skeleton files
    skeleton_files = glob.glob(os.path.join(region_path, '*skeleton*.fits'))
    if skeleton_files:
        # Prefer the standard skeleton file without threshold suffix
        standard_file = os.path.join(region_path, f'HGBS_{region_name.lower()}*_skeleton_map.fits')
        matches = glob.glob(standard_file)
        if matches:
            skeleton_file = matches[0]
        else:
            skeleton_file = skeleton_files[0]
    else:
        skeleton_file = None

    # Find core catalog files
    catalog_files = glob.glob(os.path.join(region_path, '*core*.txt'))
    catalog_files += glob.glob(os.path.join(region_path, '*catalog*.txt'))

    # Prefer derived_core_catalog if available
    for catalog_file in catalog_files:
        if 'derived' in catalog_file.lower():
            return skeleton_file, catalog_file

    if catalog_files:
        return skeleton_file, catalog_files[0]

    return skeleton_file, None

def load_skeleton(skeleton_file):
    """Load skeleton map from FITS file and extract skeleton pixels."""
    print(f"  Loading skeleton: {skeleton_file}")

    with fits.open(skeleton_file) as hdul:
        data = hdul[0].data
        header = hdul[0]. header

    # Get WCS for coordinate conversion
    from astropy.wcs import WCS
    wcs = WCS(header)

    # Find skeleton pixels (non-zero values)
    skeleton_mask = data > 0
    skeleton_y, skeleton_x = np.where(skeleton_mask)

    print(f"    Found {len(skeleton_x)} skeleton pixels")

    # Convert pixel coordinates to world coordinates (RA/Dec)
    world_coords = wcs.pixel_to_world(skeleton_x, skeleton_y)
    ra_skel = world_coords.ra.deg
    dec_skel = world_coords.dec.deg

    # Also store pixel coordinates for distance calculations
    skeleton_pixels = np.column_stack([skeleton_y, skeleton_x])

    return {
        'ra': ra_skel,
        'dec': dec_skel,
        'pixels': skeleton_pixels,
        'wcs': wcs,
        'data': data,
    }

def load_core_catalog(catalog_file, distance_pc):
    """Load core catalog from text file."""
    print(f"  Loading catalog: {catalog_file}")

    cores = []
    with open(catalog_file, 'r') as f:
        # Skip header lines (start with !)
        for line in f:
            if line.startswith('!'):
                continue
            if not line.strip():
                continue

            # Parse the data line
            parts = line.split()
            if len(parts) < 5:
                continue

            # Extract RA/Dec from source name (column 2, format: HHMMSS.s+DDMMSS)
            source_name = parts[1]

            try:
                if '+' in source_name:
                    # Split on the + sign
                    ra_part, dec_part = source_name.split('+')

                    # RA: HHMMSS.s -> hours:minutes:seconds
                    ra_h = float(ra_part[:2])
                    ra_m = float(ra_part[2:4])
                    ra_s = float(ra_part[4:])
                    ra_deg = 15 * (ra_h + ra_m/60 + ra_s/3600)

                    # Dec: DDMMSS -> degrees:minutes:seconds
                    dec_d = float(dec_part[:2])
                    dec_m = float(dec_part[2:4])
                    dec_s = float(dec_part[4:] if len(dec_part) > 4 else 0)
                    dec_deg = dec_d + dec_m/60 + dec_s/3600

                    cores.append({
                        'ra': ra_deg,
                        'dec': dec_deg,
                        'id': source_name,
                    })
            except Exception as e:
                # Skip problematic entries
                continue

    print(f"    Found {len(cores)} cores")
    return cores


def associate_cores_with_skeleton(cores, skeleton):
    """Associate each core with its nearest point on the skeleton."""
    print(f"  Associating cores with skeleton...")

    # Build KD-tree from skeleton pixels (using pixel coordinates)
    tree = cKDTree(skeleton['pixels'])

    core_associations = []
    for core in cores:
        # Convert core RA/Dec to pixel coordinates
        from astropy.wcs import WCS
        wcs = skeleton['wcs']

        world_coord = SkyCoord(core['ra']*u.deg, core['dec']*u.deg)
        pixel_coord = wcs.world_to_pixel(world_coord)

        # Find nearest skeleton pixel
        dist, idx = tree.query([pixel_coord[1], pixel_coord[0]], k=1)

        if dist < 50:  # Within 50 pixels of skeleton (increased from 10)
            # Get the RA/Dec of the nearest skeleton point
            nearest_skeleton_idx = idx
            skeleton_ra = skeleton['ra'][nearest_skeleton_idx]
            skeleton_dec = skeleton['dec'][nearest_skeleton_idx]

            core_associations.append({
                'core': core,
                'skeleton_ra': skeleton_ra,
                'skeleton_dec': skeleton_dec,
                'skeleton_pixel_idx': nearest_skeleton_idx,
                'distance_to_skeleton': dist,
            })

    print(f"    Associated {len(core_associations)} cores with skeleton")
    return core_associations

def extract_filament_paths(skeleton):
    """Extract individual filament paths from the skeleton mask."""
    print(f"  Extracting filament paths...")

    from scipy import ndimage

    # Label connected components in the skeleton
    labeled_skeleton, num_filaments = ndimage.label(skeleton['data'] > 0, structure=np.ones((3,3)))

    print(f"    Found {num_filaments} filament segments")

    filaments = []
    for i in range(1, num_filaments + 1):
        filament_mask = labeled_skeleton == i
        filament_y, filament_x = np.where(filament_mask)

        if len(filament_x) > 10:  # Only keep filaments with >10 pixels
            # Get RA/Dec for this filament
            indices = np.arange(len(filament_x))
            ra_vals = skeleton['ra'][indices]
            dec_vals = skeleton['dec'][indices]

            filaments.append({
                'id': i,
                'pixels': np.column_stack([filament_y, filament_x]),
                'ra': ra_vals,
                'dec': dec_vals,
                'length': len(filament_x),
            })

    print(f"    Extracted {len(filaments)} filaments (>10 pixels)")
    return filaments

def associate_cores_with_filaments(core_associations, filaments):
    """Associate each core with a specific filament."""
    print(f"  Associating cores with filaments...")

    filament_associations = defaultdict(list)

    for assoc in core_associations:
        core_ra = assoc['core']['ra']
        core_dec = assoc['core']['dec']

        # Find nearest filament
        min_dist = float('inf')
        nearest_filament = None

        for filament in filaments:
            # Calculate minimum distance to this filament
            dists = np.sqrt((filament['ra'] - core_ra)**2 +
                           (filament['dec'] - core_dec)**2 * np.cos(np.radians(core_ra))**2)
            min_d = dists.min()

            if min_d < min_dist:
                min_dist = min_d
                nearest_filament = filament

        if nearest_filament is not None and min_dist < 0.5:  # Within 0.5 degree (increased from 0.1)
            filament_associations[nearest_filament['id']].append({
                'core': assoc['core'],
                'ra': core_ra,
                'dec': core_dec,
            })

    # Filter filaments with at least 2 cores
    valid_filaments = {fid: cores for fid, cores in filament_associations.items()
                      if len(cores) >= 2}

    print(f"    Associated {sum(len(c) for c in valid_filaments.values())} cores "
          f"with {len(valid_filaments)} filaments (≥2 cores each)")

    return valid_filaments

def compute_position_along_filament(core_list, filament):
    """Compute position of each core along the filament path."""
    # This is a simplified approach - project cores onto the filament's
    # principal axis to get an ordering

    coords = np.column_stack([filament['ra'], filament['dec']])

    # Use PCA to find the primary axis of the filament
    from sklearn.decomposition import PCA
    pca = PCA(n_components=1)
    projected = pca.fit_transform(coords)

    # Project each core onto this axis
    core_coords = np.array([[c['ra'], c['dec']] for c in core_list])
    core_positions = pca.transform(core_coords).flatten()

    # Sort cores by position along filament
    sorted_indices = np.argsort(core_positions)

    sorted_cores = [core_list[i] for i in sorted_indices]
    sorted_positions = core_positions[sorted_indices]

    return sorted_cores, sorted_positions

def compute_nearest_neighbor_spacing(sorted_cores, sorted_positions, distance_pc):
    """Compute nearest-neighbor (adjacent-core) spacings along a filament."""
    if len(sorted_cores) < 2:
        return []

    # Convert angular separations to physical distances (pc)
    spacings = []
    for i in range(len(sorted_positions) - 1):
        # Angular separation between adjacent cores
        ra1, dec1 = sorted_cores[i]['ra'], sorted_cores[i]['dec']
        ra2, dec2 = sorted_cores[i+1]['ra'], sorted_cores[i+1]['dec']

        coord1 = SkyCoord(ra1*u.deg, dec1*u.deg)
        coord2 = SkyCoord(ra2*u.deg, dec2*u.deg)

        # Separation in degrees
        sep_deg = coord1.separation(coord2).deg

        # Convert to physical distance at the region's distance
        # 1 degree at distance D pc = D * π/180 pc
        sep_pc = sep_deg * (np.pi / 180) * distance_pc

        spacings.append(sep_pc)

    return spacings

def analyze_region(region_name, region_info):
    """Analyze a single HGBS region."""
    print(f"\n{'='*70}")
    print(f"ANALYZING {region_name.upper()}")
    print(f"{'='*70}")

    # Find data files
    skeleton_file, catalog_file = find_data_files(region_info['path'], region_name)

    if skeleton_file is None:
        print(f"  ERROR: No skeleton file found")
        return None

    if catalog_file is None:
        print(f"  ERROR: No catalog file found")
        return None

    # Load data
    skeleton = load_skeleton(skeleton_file)
    cores = load_core_catalog(catalog_file, region_info['distance'])

    if len(cores) < 2:
        print(f"  ERROR: Not enough cores ({len(cores)})")
        return None

    # Extract filaments
    filaments = extract_filament_paths(skeleton)

    # Associate cores with skeleton first
    core_associations = associate_cores_with_skeleton(cores, skeleton)

    # Associate cores with specific filaments
    filament_cores = associate_cores_with_filaments(core_associations, filaments)

    if len(filament_cores) == 0:
        print(f"  ERROR: No filaments with ≥2 cores")
        return None

    # Compute spacings for each filament
    all_spacings = []
    filament_results = []

    for filament_id, core_list in filament_cores.items():
        # Find the filament object
        filament = next(f for f in filaments if f['id'] == filament_id)

        # Sort cores by position along filament
        sorted_cores, sorted_positions = compute_position_along_filament(
            core_list, filament)

        # Compute nearest-neighbor spacings
        spacings = compute_nearest_neighbor_spacing(
            sorted_cores, sorted_positions, region_info['distance'])

        if spacings:
            median_spacing = np.median(spacings)
            filament_results.append({
                'id': filament_id,
                'n_cores': len(sorted_cores),
                'spacings': spacings,
                'median_spacing': median_spacing,
            })
            all_spacings.extend(spacings)

    # Compute region-level statistics
    if all_spacings:
        region_median = np.median(all_spacings)
        region_std = np.std(all_spacings)
        region_sem = region_std / np.sqrt(len(all_spacings))

        # Compute lambda/W ratio (assuming W = 0.1 pc)
        lambda_over_W = region_median / 0.1

        result = {
            'region': region_name,
            'distance': region_info['distance'],
            'n_filaments': len(filament_results),
            'n_cores_total': sum(len(f['spacings']) + 1 for f in filament_results),
            'n_spacings': len(all_spacings),
            'median_spacing': region_median,
            'std_spacing': region_std,
            'sem_spacing': region_sem,
            'lambda_over_W': lambda_over_W,
            'filament_results': filament_results,
        }

        print(f"\n  RESULTS:")
        print(f"    Distance: {region_info['distance']} pc")
        print(f"    Filaments with ≥2 cores: {len(filament_results)}")
        print(f"    Total spacings measured: {len(all_spacings)}")
        print(f"    Median NN spacing: {region_median:.4f} ± {region_sem:.4f} pc")
        print(f"    λ/W ratio: {lambda_over_W:.2f}")

        return result
    else:
        print(f"  ERROR: No spacings computed")
        return None

# Main analysis
if __name__ == '__main__':
    print("=" * 70)
    print("NEAREST-NEIGHBOR SPACING ANALYSIS FOR HGBS REGIONS")
    print("=" * 70)
    print()
    print("This analysis addresses the L/3 convergence problem by computing")
    print("proper nearest-neighbor (adjacent-core) spacing along filaments.")
    print()

    # Start with Taurus as a test
    region_name = 'Taurus'
    region_info = HGBS_REGIONS[region_name]

    try:
        result = analyze_region(region_name, region_info)

        if result:
            print(f"\n{'='*70}")
            print(f"SUMMARY FOR {region_name.upper()}")
            print(f"{'='*70}")
            print(f"Nearest-neighbor median spacing: {result['median_spacing']:.4f} ± {result['sem_spacing']:.4f} pc")
            print(f"λ/W ratio: {result['lambda_over_W']:.2f}")
            print(f"This should be compared with the pairwise median value of ~0.198 pc")
            print(f"to assess the L/3 convergence bias.")
            print()
    except Exception as e:
        print(f"\nERROR during analysis: {e}")
        import traceback
        traceback.print_exc()
