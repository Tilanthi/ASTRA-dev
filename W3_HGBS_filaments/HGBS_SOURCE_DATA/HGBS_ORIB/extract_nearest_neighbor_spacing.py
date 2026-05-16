#!/usr/bin/env python3
"""
Extract nearest-neighbor spacing from HGBS skeleton and catalog data.

This script:
1. Loads the HGBS skeleton map (DisPerSE output)
2. Extracts filament spine structures
3. Loads core catalog with positions
4. Associates cores with filaments
5. Orders cores along each filament spine
6. Computes nearest-neighbor distances
7. Reports statistics
"""

import numpy as np
from astropy.io import fits
from astropy import units as u
from astropy.coordinates import SkyCoord
from scipy.spatial import cKDTree
from scipy import ndimage
from collections import defaultdict
import json

class HGBSNearestNeighborAnalyzer:
    def __init__(self, skeleton_file, catalog_file, distance_pc=None):
        """
        Initialize analyzer with skeleton and catalog data.

        Parameters:
        -----------
        skeleton_file : str
            Path to DisPerSE skeleton FITS file
        catalog_file : str
            Path to HGBS core catalog
        distance_pc : float
            Distance to region in parsecs (for converting angular to physical distances)
        """
        self.skeleton_file = skeleton_file
        self.catalog_file = catalog_file
        self.distance_pc = distance_pc

        # Load data
        self.skeleton_data = None
        self.skeleton_header = None
        self.cores = []
        self.filaments = []  # List of filament spines (ordered arrays of pixel coordinates)

        self.load_skeleton()
        self.load_catalog()

    def load_skeleton(self):
        """Load the DisPerSE skeleton map."""
        print(f"Loading skeleton: {self.skeleton_file}")
        hdul = fits.open(self.skeleton_file)
        self.skeleton_data = hdul[0].data.astype(np.float64)
        self.skeleton_header = hdul[0].header

        print(f"Skeleton shape: {self.skeleton_data.shape}")
        print(f"Skeleton dtype: {self.skeleton_data.dtype}")

        # Get WCS info if available
        try:
            from astropy.wcs import WCS
            self.wcs = WCS(self.skeleton_header)
            print(f"WCS: {self.wcs}")
        except Exception as e:
            print(f"No WCS in header: {e}")
            self.wcs = None

        hdul.close()

    def load_catalog(self):
        """Load the HGBS core catalog."""
        print(f"Loading catalog: {self.catalog_file}")

        # Handle encoding - HGBS catalogs have special characters
        with open(self.catalog_file, 'r', encoding='latin-1') as f:
            lines = f.readlines()

        # Skip header until we find the data
        data_start = 0
        for i, line in enumerate(lines):
            if line.startswith('   1 ') or line.startswith(' 1 '):
                data_start = i
                break

        print(f"Found data starting at line {data_start}")

        # Parse core data
        for line in lines[data_start:]:
            if not line.strip():
                continue

            parts = line.split()
            if len(parts) < 5:
                continue

            try:
                core_id = int(parts[0])
                # Parse RA/Dec from sexagesimal format (05:39:54.92, -02:46:34.6)
                ra_str = parts[2]
                dec_str = parts[3]

                # Convert to degrees
                coord = SkyCoord(ra_str, dec_str, unit=(u.hourangle, u.deg))

                self.cores.append({
                    'id': core_id,
                    'ra': coord.ra.deg,
                    'dec': coord.dec.deg,
                    'coord': coord
                })
            except (ValueError, IndexError) as e:
                continue

        print(f"Loaded {len(self.cores)} cores from catalog")

    def extract_filament_spines(self, threshold=0.1, min_length=50):
        """
        Extract filament spines from the skeleton map.

        Parameters:
        -----------
        threshold : float
            Minimum skeleton value to consider
        min_length : int
            Minimum number of pixels for a filament
        """
        print("Extracting filament spines from skeleton map...")

        # Threshold the skeleton
        skeleton_mask = self.skeleton_data > threshold

        # Label connected components
        labeled, num_features = ndimage.label(skeleton_mask)

        print(f"Found {num_features} candidate filaments")

        # Extract each filament as an ordered set of pixels
        self.filaments = []

        for i in range(1, num_features + 1):
            filament_pixels = np.where(labeled == i)
            n_pixels = len(filament_pixels[0])

            if n_pixels < min_length:
                continue

            # Get the pixel coordinates
            y_coords = filament_pixels[0]
            x_coords = filament_pixels[1]

            # Order the pixels along the filament
            # This is a simplified approach - we'll use the skeleton values as weights
            skeleton_values = self.skeleton_data[y_coords, x_coords]

            # Sort by position (y, x) as a rough ordering
            # A more sophisticated approach would skeletonize further
            order = np.lexsort((x_coords, y_coords))
            ordered_y = y_coords[order]
            ordered_x = x_coords[order]
            ordered_values = skeleton_values[order]

            self.filaments.append({
                'id': i,
                'pixels_y': ordered_y,
                'pixels_x': ordered_x,
                'values': ordered_values,
                'length': n_pixels
            })

        print(f"Extracted {len(self.filaments)} filaments with >= {min_length} pixels")

        # Sort filaments by length (descending)
        self.filaments.sort(key=lambda f: f['length'], reverse=True)

    def world_to_pixel(self, ra_deg, dec_deg):
        """Convert world coordinates to pixel coordinates."""
        if self.wcs is None:
            raise ValueError("No WCS available")

        from astropy.wcs import utils
        x, y = utils.skycoord_to_pixel(self.wcs, SkyCoord(ra_deg, dec_deg, unit='deg'))
        return x, y

    def pixel_to_world(self, x, y):
        """Convert pixel coordinates to world coordinates."""
        if self.wcs is None:
            raise ValueError("No WCS available")

        from astropy.wcs import utils
        coord = utils.pixel_to_skycoord(self.wcs, x, y)
        return coord.ra.deg, coord.dec.deg

    def associate_cores_with_filaments(self, max_distance_pixels=10):
        """
        Associate cores with filaments based on proximity.

        Parameters:
        -----------
        max_distance_pixels : float
            Maximum distance (in pixels) for core-filament association
        """
        print(f"Associating cores with filaments (max distance: {max_distance_pixels} pixels)...")

        core_filament_assoc = {i: None for i in range(len(self.cores))}
        core_filament_distances = {i: np.inf for i in range(len(self.cores))}

        for i, core in enumerate(self.cores):
            try:
                # Convert core position to pixel coordinates
                px, py = self.world_to_pixel(core['ra'], core['dec'])

                # Find nearest filament
                for fil in self.filaments:
                    # Calculate minimum distance from core to any pixel in this filament
                    dist_sq = (fil['pixels_x'] - px)**2 + (fil['pixels_y'] - py)**2
                    min_dist = np.sqrt(np.min(dist_sq))

                    if min_dist < core_filament_distances[i] and min_dist < max_distance_pixels:
                        core_filament_distances[i] = min_dist
                        core_filament_assoc[i] = fil['id']
            except Exception as e:
                # Core outside skeleton map
                pass

        # Count associations
        n_associated = sum(1 for f in core_filament_assoc.values() if f is not None)
        print(f"Associated {n_associated}/{len(self.cores)} cores with filaments")

        return core_filament_assoc, core_filament_distances

    def order_cores_along_filaments(self, core_filament_assoc):
        """
        Order cores along each filament spine.

        This is a simplified approach - we project each core onto the filament
        and order by its position along the spine.
        """
        print("Ordering cores along filaments...")

        filament_cores = defaultdict(list)

        # For each filament, collect associated cores
        for i, core in enumerate(self.cores):
            fil_id = core_filament_assoc[i]
            if fil_id is not None:
                filament_cores[fil_id].append(i)

        # Order cores along each filament
        for fil_id, core_indices in filament_cores.items():
            if len(core_indices) < 2:
                continue

            # Get the filament data
            fil = next(f for f in self.filaments if f['id'] == fil_id)

            # Project each core onto the filament and get position along spine
            core_positions = []

            for core_idx in core_indices:
                core = self.cores[core_idx]
                try:
                    px, py = self.world_to_pixel(core['ra'], core['dec'])

                    # Find closest point on filament spine
                    dist_sq = (fil['pixels_x'] - px)**2 + (fil['pixels_y'] - py)**2
                    closest_idx = np.argmin(dist_sq)

                    # Use the index in the ordered filament as position along spine
                    position_along_spine = closest_idx

                    core_positions.append((position_along_spine, core_idx))
                except Exception as e:
                    # Core outside map
                    continue

            # Sort by position along spine
            core_positions.sort(key=lambda x: x[0])

            # Store ordered list of core indices for this filament
            filament_cores[fil_id] = [c[1] for c in core_positions]

        return filament_cores

    def compute_nearest_neighbor_spacing(self, filament_cores):
        """
        Compute nearest-neighbor spacing for cores along filaments.

        Returns arrays of spacings in physical units (pc).
        """
        print("Computing nearest-neighbor spacings...")

        all_spacings = []

        # Conversion factor from angular separation to physical distance
        if self.distance_pc is not None:
            # Angular scale: 1 radian at distance d corresponds to d * 1 radian
            # For small angles, separation in pc ≈ distance * angular_separation_radians
            # We'll compute angular separations and convert
            pass

        for fil_id, core_indices in filament_cores.items():
            if len(core_indices) < 2:
                continue

            # Get ordered core coordinates
            coords = SkyCoord(
                ra=[self.cores[i]['ra'] for i in core_indices] * u.deg,
                dec=[self.cores[i]['dec'] for i in core_indices] * u.deg
            )

            # Compute separations between adjacent cores
            for i in range(len(coords) - 1):
                sep = coords[i].separation(coords[i+1])

                # Convert to physical distance
                if self.distance_pc is not None:
                    # Small angle approximation: distance ≈ distance * angle
                    sep_pc = sep.radian * self.distance_pc
                else:
                    # Just use angular separation (convert to "pseudo-pc" assuming 1 degree at some distance)
                    sep_pc = sep.arcsec / 206265  # Convert arcsec to radians, then assume some scale

                all_spacings.append(sep_pc)

        all_spacings = np.array(all_spacings)

        print(f"Computed {len(all_spacings)} nearest-neighbor spacings")

        return all_spacings

    def analyze_spacing(self, spacings):
        """Compute statistics on nearest-neighbor spacings."""
        if len(spacings) == 0:
            print("No spacings computed!")
            return {}

        stats = {
            'n_spacings': len(spacings),
            'min_pc': np.min(spacings),
            'max_pc': np.max(spacings),
            'mean_pc': np.mean(spacings),
            'median_pc': np.median(spacings),
            'std_pc': np.std(spacings),
            'sem_pc': np.std(spacings) / np.sqrt(len(spacings)),
            'q25_pc': np.percentile(spacings, 25),
            'q75_pc': np.percentile(spacings, 75),
        }

        return stats

    def run_analysis(self):
        """Run the full analysis pipeline."""
        print("=" * 70)
        print("HGBS Nearest-Neighbor Spacing Analysis")
        print("=" * 70)

        # Step 1: Extract filament spines
        self.extract_filament_spines(threshold=0.1, min_length=50)

        # Step 2: Associate cores with filaments
        core_assoc, core_dists = self.associate_cores_with_filaments(max_distance_pixels=15)

        # Step 3: Order cores along filaments
        filament_cores = self.order_cores_along_filaments(core_assoc)

        # Step 4: Compute nearest-neighbor spacings
        spacings = self.compute_nearest_neighbor_spacing(filament_cores)

        # Step 5: Analyze
        stats = self.analyze_spacing(spacings)

        print("\n" + "=" * 70)
        print("NEAREST-NEIGHBOR SPACING STATISTICS")
        print("=" * 70)
        for key, value in stats.items():
            if isinstance(value, float):
                print(f"{key}: {value:.4f}")
            else:
                print(f"{key}: {value}")

        print("=" * 70)

        # Calculate lambda/W if width is known
        if self.distance_pc is not None and stats['median_pc']:
            # Characteristic width ~0.1 pc
            width_pc = 0.1
            lambda_by_W = stats['median_pc'] / width_pc
            print(f"\nMedian spacing: {stats['median_pc']:.4f} pc")
            print(f"λ/W ratio: {lambda_by_W:.2f}")

        return stats, spacings


def analyze_orion_b():
    """Analyze Orion B region."""

    skeleton_file = '/Users/gjw255/astrodata/SWARM/ASTRA/HGBS_ORIB/HGBS_orionB_skeleton_map_thresh50.fits'
    catalog_file = '/Users/gjw255/astrodata/SWARM/ASTRA/HGBS_ORIB/HGBS_orionB_derived_core_catalog.txt'
    distance_pc = 386  # Gaia DR3 distance for Orion B

    analyzer = HGBSNearestNeighborAnalyzer(
        skeleton_file=skeleton_file,
        catalog_file=catalog_file,
        distance_pc=distance_pc
    )

    stats, spacings = analyzer.run_analysis()

    # Save results
    results = {
        'region': 'Orion B',
        'distance_pc': distance_pc,
        'n_cores_analyzed': stats['n_spacings'] + 1,  # n_spacings = n_cores - 1
        'nearest_neighbor_spacing_pc': stats,
        'all_spacings_pc': spacings.tolist()
    }

    output_file = '/Users/gjw255/astrodata/SWARM/ASTRA/HGBS_ORIB/nearest_neighbor_results.json'
    with open(output_file, 'w') as f:
        json.dump(results, f, indent=2)

    print(f"\nResults saved to: {output_file}")

    return results


if __name__ == '__main__':
    import sys
    sys.path.append('/Users/gjw255/astrodata/SWARM/ASTRA-dev-main')

    results = analyze_orion_b()
