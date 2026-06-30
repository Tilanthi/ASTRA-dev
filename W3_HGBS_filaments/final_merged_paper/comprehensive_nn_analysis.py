#!/usr/bin/env python3
"""
Comprehensive Nearest-Neighbor Analysis for All 8 HGBS Regions

This script computes proper nearest-neighbor (adjacent-core) spacing statistics
for all 8 HGBS regions to address the L/3 convergence problem with pairwise median.

Author: Filament Spacing Paper - Referee Response
Date: June 2026
"""

import numpy as np
from astropy.io import fits
from astropy import units as u
from astropy.coordinates import SkyCoord
from scipy.spatial import cKDTree
from scipy import ndimage
from collections import defaultdict
import json
import os
import glob

class HGBSNearestNeighborAnalyzer:
    """Analyzer for computing nearest-neighbor spacing along filaments."""

    def __init__(self, region_name, skeleton_file, catalog_file, distance_pc):
        """
        Initialize analyzer for a specific region.

        Parameters:
        -----------
        region_name : str
            Name of the HGBS region
        skeleton_file : str
            Path to DisPerSE skeleton FITS file
        catalog_file : str
            Path to HGBS core catalog
        distance_pc : float
            Distance to region in parsecs (for converting angular to physical distances)
        """
        self.region_name = region_name
        self.skeleton_file = skeleton_file
        self.catalog_file = catalog_file
        self.distance_pc = distance_pc

        # Data containers
        self.skeleton_data = None
        self.skeleton_header = None
        self.cores = []
        self.filaments = []
        self.wcs = None

    def load_skeleton(self):
        """Load the DisPerSE skeleton map."""
        print(f"[{self.region_name}] Loading skeleton: {self.skeleton_file}")

        if not os.path.exists(self.skeleton_file):
            print(f"[{self.region_name}] WARNING: Skeleton file not found: {self.skeleton_file}")
            return False

        try:
            hdul = fits.open(self.skeleton_file)
            self.skeleton_data = hdul[0].data.astype(np.float64)
            self.skeleton_header = hdul[0].header
            print(f"[{self.region_name}] Skeleton shape: {self.skeleton_data.shape}")

            # Get WCS info
            try:
                from astropy.wcs import WCS
                self.wcs = WCS(self.skeleton_header)
            except Exception as e:
                print(f"[{self.region_name}] No WCS in header: {e}")

            hdul.close()
            return True
        except Exception as e:
            print(f"[{self.region_name}] ERROR loading skeleton: {e}")
            return False

    def load_catalog(self):
        """Load the HGBS core catalog."""
        print(f"[{self.region_name}] Loading catalog: {self.catalog_file}")

        if not os.path.exists(self.catalog_file):
            print(f"[{self.region_name}] WARNING: Catalog file not found: {self.catalog_file}")
            return False

        try:
            # Handle encoding - HGBS catalogs have special characters
            with open(self.catalog_file, 'r', encoding='latin-1', errors='ignore') as f:
                lines = f.readlines()

            # Skip header until we find the data
            data_start = 0
            for i, line in enumerate(lines):
                if line.strip().startswith('1 ') or line.strip().startswith('1	'):
                    data_start = i
                    break

            # Parse core data
            for line in lines[data_start:]:
                if not line.strip():
                    continue

                parts = line.split()
                if len(parts) < 5:
                    continue

                try:
                    core_id = int(parts[0])
                    # Parse RA/Dec from sexagesimal format
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

            print(f"[{self.region_name}] Loaded {len(self.cores)} cores from catalog")
            return len(self.cores) > 0
        except Exception as e:
            print(f"[{self.region_name}] ERROR loading catalog: {e}")
            return False

    def extract_filament_spines(self, threshold=0.1, min_length=30):
        """Extract filament spines from the skeleton map."""
        if self.skeleton_data is None:
            return False

        print(f"[{self.region_name}] Extracting filament spines...")

        # Threshold the skeleton
        skeleton_mask = self.skeleton_data > threshold

        # Label connected components
        labeled, num_features = ndimage.label(skeleton_mask)
        print(f"[{self.region_name}] Found {num_features} candidate filaments")

        # Extract each filament as an ordered set of pixels
        self.filaments = []

        for i in range(1, num_features + 1):
            filament_pixels = np.where(labeled == i)
            n_pixels = len(filament_pixels[0])

            if n_pixels < min_length:
                continue

            y_coords = filament_pixels[0]
            x_coords = filament_pixels[1]

            # Order the pixels along the filament
            skeleton_values = self.skeleton_data[y_coords, x_coords]
            order = np.lexsort((x_coords, y_coords))

            self.filaments.append({
                'id': i,
                'pixels_y': y_coords[order],
                'pixels_x': x_coords[order],
                'values': skeleton_values[order],
                'length': n_pixels
            })

        print(f"[{self.region_name}] Extracted {len(self.filaments)} filaments")
        return len(self.filaments) > 0

    def world_to_pixel(self, ra_deg, dec_deg):
        """Convert world coordinates to pixel coordinates."""
        if self.wcs is None:
            raise ValueError("No WCS available")

        from astropy.wcs import utils
        x, y = utils.skycoord_to_pixel(
            SkyCoord(ra_deg, dec_deg, unit='deg'),
            self.wcs
        )
        return x, y

    def associate_cores_with_filaments(self, max_distance_pixels=15):
        """Associate cores with filaments based on proximity."""
        if self.wcs is None or len(self.filaments) == 0:
            # Fallback: use simple spatial clustering
            return self._fallback_core_association()

        print(f"[{self.region_name}] Associating cores with filaments...")

        core_filament_assoc = {}
        core_positions = []

        for i, core in enumerate(self.cores):
            try:
                px, py = self.world_to_pixel(core['ra'], core['dec'])

                # Check if core is within skeleton map bounds
                if (px < 0 or px >= self.skeleton_data.shape[1] or
                    py < 0 or py >= self.skeleton_data.shape[0]):
                    continue

                # Find nearest filament
                min_dist = np.inf
                nearest_fil = None

                for fil in self.filaments:
                    dist_sq = (fil['pixels_x'] - px)**2 + (fil['pixels_y'] - py)**2
                    dist = np.sqrt(np.min(dist_sq))

                    if dist < min_dist and dist < max_distance_pixels:
                        min_dist = dist
                        nearest_fil = fil['id']

                if nearest_fil is not None:
                    core_filament_assoc[i] = nearest_fil
                    core_positions.append((i, nearest_fil, px, py))
            except Exception as e:
                continue

        n_associated = len(core_filament_assoc)
        print(f"[{self.region_name}] Associated {n_associated}/{len(self.cores)} cores with filaments")

        return core_filament_assoc

    def _fallback_core_association(self):
        """
        Fallback: Use spatial clustering when skeleton is not available.

        Groups cores by proximity to simulate filament associations.
        """
        print(f"[{self.region_name}] Using fallback spatial clustering...")

        if len(self.cores) < 2:
            return {}

        # Build KD-tree for spatial queries
        coords = np.array([[c['ra'], c['dec']] for c in self.cores])

        # Scale RA by cos(dec) for proper distance
        median_dec = np.median(coords[:, 1])
        coords[:, 0] *= np.cos(np.radians(median_dec))

        tree = cKDTree(coords)

        # Associate cores based on connectivity
        # Find neighbors within a threshold distance
        threshold_deg = 0.1  # degrees
        pairs = tree.query_pairs(threshold_deg)

        # Build connected components
        filament_groups = []
        core_to_group = {}

        for i, c1 in enumerate(self.cores):
            if i not in core_to_group:
                # Start new group
                group_id = len(filament_groups)
                group = [i]
                core_to_group[i] = group_id

                # BFS to find connected cores
                queue = [i]
                visited = {i}

                while queue:
                    current = queue.pop(0)
                    # Find neighbors
                    for j in range(len(self.cores)):
                        if j in visited:
                            continue

                        dist = np.sqrt(
                            (coords[current][0] - coords[j][0])**2 +
                            (coords[current][1] - coords[j][1])**2
                        )

                        if dist < threshold_deg:
                            visited.add(j)
                            queue.append(j)
                            group.append(j)
                            core_to_group[j] = group_id

                if len(group) >= 2:
                    filament_groups.append(group)

        print(f"[{self.region_name}] Fallback: Found {len(filament_groups)} filament-like groups")

        # Convert to core_filament_assoc format
        core_filament_assoc = {}
        for group_id, group in enumerate(filament_groups):
            for core_idx in group:
                core_filament_assoc[core_idx] = group_id

        return core_filament_assoc

    def order_cores_along_filaments(self, core_filament_assoc):
        """Order cores along each filament spine."""
        print(f"[{self.region_name}] Ordering cores along filaments...")

        filament_cores = defaultdict(list)

        # Group cores by filament
        for core_idx, fil_id in core_filament_assoc.items():
            filament_cores[fil_id].append(core_idx)

        # Order cores within each filament
        for fil_id, core_indices in filament_cores.items():
            if len(core_indices) < 2:
                continue

            # Get coordinates
            coords = []
            for idx in core_indices:
                core = self.cores[idx]
                coords.append([core['ra'], core['dec']])

            coords = np.array(coords)

            # Scale RA by cos(dec)
            median_dec = np.median(coords[:, 1])
            coords[:, 0] *= np.cos(np.radians(median_dec))

            # Use first principal component as filament axis
            if len(coords) >= 2:
                centered = coords - np.mean(coords, axis=0)
                cov = np.cov(centered.T)
                eigvals, eigvecs = np.linalg.eig(cov)

                # Project onto principal component
                pc1 = eigvecs[:, np.argmax(eigvals)]
                projections = centered @ pc1

                # Sort by projection
                order = np.argsort(projections)
                filament_cores[fil_id] = [core_indices[i] for i in order]

        return dict(filament_cores)

    def compute_nearest_neighbor_spacing(self, filament_cores):
        """Compute nearest-neighbor spacing for cores along filaments."""
        print(f"[{self.region_name}] Computing nearest-neighbor spacings...")

        all_spacings = []

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
                sep_pc = sep.radian * self.distance_pc
                all_spacings.append(sep_pc)

        all_spacings = np.array(all_spacings)
        print(f"[{self.region_name}] Computed {len(all_spacings)} nearest-neighbor spacings")

        return all_spacings

    def analyze_spacing(self, spacings):
        """Compute statistics on nearest-neighbor spacings."""
        if len(spacings) == 0:
            return {}

        stats = {
            'n_spacings': len(spacings),
            'min_pc': float(np.min(spacings)),
            'max_pc': float(np.max(spacings)),
            'mean_pc': float(np.mean(spacings)),
            'median_pc': float(np.median(spacings)),
            'std_pc': float(np.std(spacings)),
            'sem_pc': float(np.std(spacings) / np.sqrt(len(spacings))),
            'q25_pc': float(np.percentile(spacings, 25)),
            'q75_pc': float(np.percentile(spacings, 75)),
        }

        # Lambda/W ratio
        stats['lambda_by_W'] = stats['median_pc'] / 0.1  # Width = 0.1 pc

        return stats

    def run_analysis(self):
        """Run the full analysis pipeline."""
        print(f"\n{'='*70}")
        print(f"HGBS Nearest-Neighbor Analysis: {self.region_name}")
        print(f"{'='*70}")

        # Load data
        if not self.load_skeleton():
            print(f"[{self.region_name}] Cannot proceed without skeleton data")
            return None

        if not self.load_catalog():
            print(f"[{self.region_name}] Cannot proceed without catalog data")
            return None

        # Extract filaments
        if not self.extract_filament_spines():
            print(f"[{self.region_name}] Could not extract filaments")
            return None

        # Associate cores with filaments
        core_assoc = self.associate_cores_with_filaments()

        if len(core_assoc) < 2:
            print(f"[{self.region_name}] Not enough cores associated")
            return None

        # Order cores along filaments
        filament_cores = self.order_cores_along_filaments(core_assoc)

        # Compute nearest-neighbor spacings
        spacings = self.compute_nearest_neighbor_spacing(filament_cores)

        if len(spacings) == 0:
            print(f"[{self.region_name}] No spacings computed")
            return None

        # Analyze
        stats = self.analyze_spacing(spacings)

        print(f"\n{'='*70}")
        print(f"RESULTS: {self.region_name}")
        print(f"{'='*70}")
        print(f"Cores analyzed: {len(self.cores)}")
        print(f"Cores associated: {len(core_assoc)}")
        print(f"NN spacings: {stats['n_spacings']}")
        print(f"Median spacing: {stats['median_pc']:.4f} pc")
        print(f"Mean spacing: {stats['mean_pc']:.4f} pc")
        print(f"Std spacing: {stats['std_pc']:.4f} pc")
        print(f"SEM spacing: {stats['sem_pc']:.4f} pc")
        print(f"λ/W ratio: {stats['lambda_by_W']:.2f}")
        print(f"{'='*70}\n")

        return {
            'region': self.region_name,
            'distance_pc': self.distance_pc,
            'n_cores_total': len(self.cores),
            'n_cores_associated': len(core_assoc),
            'n_filaments': len(filament_cores),
            'nn_spacing_statistics': stats,
            'all_spacings_pc': spacings.tolist()
        }


# Define all 8 HGBS regions with their data paths and Gaia DR3 distances
HGBS_REGIONS = {
    'Orion B': {
        'skeleton': '/Users/gjw255/astrodata/SWARM/ASTRA/HGBS_ORIB/HGBS_orionB_skeleton_map_thresh50.fits',
        'catalog': '/Users/gjw255/astrodata/SWARM/ASTRA/HGBS_ORIB/HGBS_orionb_derived_core_catalog.txt',
        'distance_pc': 386
    },
    'Aquila': {
        'skeleton': '/Users/gjw255/astrodata/SWARM/ASTRA/HGBS_AQUILA/HGBS_AQUILA/HGBS_Aquila_python_skeleton.fits',
        'catalog': '/Users/gjw255/astrodata/SWARM/ASTRA/HGBS_AQUILA/HGBS_AQUILA/HGBS_aquilaM2_derived_core_catalog.txt',
        'distance_pc': 436
    },
    'Perseus': {
        'skeleton': '/Users/gjw255/astrodata/SWARM/ASTRA/HGBS_PERSEUS/HGBS_PERSEUS/HGBS_Perseus_python_skeleton.fits',
        'catalog': '/Users/gjw255/astrodata/SWARM/ASTRA/HGBS_PERSEUS/HGBS_PERSEUS/HGBS_perseus_derived_core_catalog.txt',
        'distance_pc': 296
    },
    'Taurus': {
        'skeleton': '/Users/gjw255/astrodata/SWARM/ASTRA/HGBS_TAURUS/HGBS_Taurus_python_skeleton.fits',
        'catalog': '/Users/gjw255/astrodata/SWARM/ASTRA/HGBS_TAURUS/HGBS_taurusL1495_derived_core_catalog.txt',
        'distance_pc': 135
    },
    'Ophiuchus': {
        'skeleton': '/Users/gjw255/astrodata/SWARM/ASTRA/HGBS_OPH/HGBS_Ophiuchus_python_skeleton.fits',
        'catalog': '/Users/gjw255/astrodata/SWARM/ASTRA/HGBS_OPH/HGBS_ophiuchus_derived_core_catalog.txt',
        'distance_pc': 137
    },
    'Serpens': {
        'skeleton': '/Users/gjw255/astrodata/SWARM/ASTRA/HGBS_SERPENS/HGBS_Serpens_python_skeleton.fits',
        'catalog': '/Users/gjw255/astrodata/SWARM/ASTRA/HGBS_SERPENS/HGBS_serpens_observed_core_catalog.txt',
        'distance_pc': 458
    },
    'TMC1': {
        'skeleton': '/Users/gjw255/astrodata/SWARM/ASTRA/HGBS_TMC1/HGBS_TMC1_python_skeleton.fits',
        'catalog': '/Users/gjw255/astrodata/SWARM/ASTRA/HGBS_TMC1/HGBS_taurusTMC1_derived_core_catalog.txt',
        'distance_pc': 135
    },
    'CRA': {
        'skeleton': '/Users/gjw255/astrodata/SWARM/ASTRA/HGBS_CRA/HGBS_CRA_python_skeleton.fits',
        'catalog': '/Users/gjw255/astrodata/SWARM/ASTRA/HGBS_CRA/HGBS_craNS_derived_core_catalog.txt',
        'distance_pc': 150
    },
}


def run_comprehensive_nn_analysis():
    """Run NN analysis for all 8 HGBS regions."""
    print("="*70)
    print("COMPREHENSIVE NEAREST-NEIGHBOR ANALYSIS FOR ALL 8 HGBS REGIONS")
    print("="*70)
    print()

    results = {}

    for region_name, region_data in HGBS_REGIONS.items():
        analyzer = HGBSNearestNeighborAnalyzer(
            region_name=region_name,
            skeleton_file=region_data['skeleton'],
            catalog_file=region_data['catalog'],
            distance_pc=region_data['distance_pc']
        )

        result = analyzer.run_analysis()
        if result is not None:
            results[region_name] = result

    # Compute summary statistics
    print("\n" + "="*70)
    print("SUMMARY: ALL REGIONS")
    print("="*70)

    # Prepare summary table
    table_lines = []
    table_lines.append("\n" + "="*100)
    table_lines.append(f"{'Region':<12} {'N cores':>8} {'N assoc':>8} {'N NN':>6} {'NN median (pc)':>15} {'SEM (pc)':>10} {'λ/W':>6}")
    table_lines.append("-"*100)

    for region in ['Orion B', 'Aquila', 'Perseus', 'Taurus', 'Ophiuchus', 'Serpens', 'TMC1', 'CRA']:
        if region in results:
            r = results[region]
            stats = r['nn_spacing_statistics']
            table_lines.append(
                f"{region:<12} {r['n_cores_total']:>8} {r['n_cores_associated']:>8} "
                f"{stats['n_spacings']:>6} {stats['median_pc']:>15.4f} {stats['sem_pc']:>10.4f} "
                f"{stats['lambda_by_W']:>6.2f}"
            )
        else:
            table_lines.append(f"{region:<12} {'NO DATA':>42}")

    table_lines.append("="*100)

    for line in table_lines:
        print(line)

    # Compute weighted mean across regions
    print("\n" + "="*70)
    print("WEIGHTED MEAN CALCULATION")
    print("="*70)

    # Use inverse variance weighting
    weighted_sum = 0
    weight_sum = 0

    for region, result in results.items():
        stats = result['nn_spacing_statistics']
        variance = stats['sem_pc']**2
        weight = 1.0 / variance if variance > 0 else 0

        weighted_sum += weight * stats['median_pc']
        weight_sum += weight

        print(f"{region}: λ_NN = {stats['median_pc']:.4f} ± {stats['sem_pc']:.4f} pc, weight = {weight:.2f}")

    if weight_sum > 0:
        weighted_mean = weighted_sum / weight_sum
        print(f"\nWeighted mean NN spacing: {weighted_mean:.4f} pc")
        print(f"λ_NN/W = {weighted_mean / 0.1:.2f}")

    # Save comprehensive results
    output_file = '/Users/gjw255/astrodata/SWARM/ASTRA-dev-main/W3_HGBS_filaments/final_merged_paper/nn_analysis_results.json'

    comprehensive_results = {
        'analysis_date': '2026-06-05',
        'method': 'nearest_neighbor_along_filaments',
        'description': 'Adjacent-core spacing computed along filament structures',
        'regions': results,
        'summary': {
            'weighted_mean_pc': weighted_mean if weight_sum > 0 else None,
            'lambda_by_W': weighted_mean / 0.1 if weight_sum > 0 else None,
        }
    }

    with open(output_file, 'w') as f:
        json.dump(comprehensive_results, f, indent=2)

    print(f"\nResults saved to: {output_file}")

    return comprehensive_results


if __name__ == '__main__':
    results = run_comprehensive_nn_analysis()

    print("\n" + "="*70)
    print("ANALYSIS COMPLETE")
    print("="*70)
