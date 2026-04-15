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
Athena++ 3D Filament Analysis Script

Analyzes HDF5 output from filament fragmentation simulation
to extract core properties and compare to observations.

Author: ASTRA System
Date: 2026-04-09
"""

import h5py
import numpy as np
import matplotlib.pyplot as plt
from scipy.ndimage import maximum_filter
from scipy.spatial.distance import pdist
from pathlib import Path

# ============================================================
# CONFIGURATION
# ============================================================

# Input/output paths
INPUT_DIR = Path("./output")
OUTPUT_DIR = Path("./analysis_results")
OUTPUT_DIR.mkdir(exist_ok=True)

# Physical constants
PC_TO_CM = 3.086e18
KM_S_TO_CM_S = 1.0e5
MH = 1.67e-24  # Proton mass (g)

# Simulation parameters
DOMAIN_LENGTH_PC = 0.8  # Length in parsecs
DOMAIN_WIDTH_PC = 0.4   # Width in parsecs
N_CELLS_Z = 128         # Grid cells in z
N_CELLS_X = 64          # Grid cells in x

# Derived quantities
DZ_PC = DOMAIN_LENGTH_PC / N_CELLS_Z
DX_PC = DOMAIN_WIDTH_PC / N_CELLS_X

# Core detection parameters
DENSITY_THRESHOLD = 2.0  # Mean density enhancement factor
MIN_SEPARATION_PC = 0.05  # Minimum core separation (pc)
PEAK_NEIGHBORHOOD = 3     # For maximum filter

# ============================================================
# DATA LOADING
# ============================================================

def load_hdf5_snapshot(filepath):
    """
    Load data from a single HDF5 snapshot.

    Returns:
        dict: Contains density, velocity, coordinates
    """
    with h5py.File(filepath, 'r') as f:
        # Load density
        rho = f['/dens'][:]

        # Load velocity (if available)
        vel = {}
        for coord in ['1', '2', '3']:
            try:
                vel[coord] = f[f'/vel{coord}'][:]
            except KeyError:
                pass

        # Get grid info
        time_code = f.attrs.get('Time', 0.0)

        return {
            'density': rho,
            'velocity': vel,
            'time_code': time_code,
            'shape': rho.shape
        }


def load_all_snapshots(input_dir):
    """
    Load all HDF5 snapshots from input directory.

    Returns:
        list: Sorted list of (time, data) tuples
    """
    snapshots = []

    for filepath in sorted(input_dir.glob("blocs*.hdf5")):
        try:
            data = load_hdf5_snapshot(filepath)
            snapshots.append(data)
        except Exception as e:
            print(f"Warning: Could not load {filepath}: {e}")

    print(f"Loaded {len(snapshots)} snapshots")
    return snapshots


# ============================================================
# CORE DETECTION
# ============================================================

def detect_cores_3d(density, threshold=DENSITY_THRESHOLD, min_sep=MIN_SEPARATION_PC):
    """
    Detect density peaks (cores) in 3D density field.

    Args:
        density: 3D density array [z, y, x] in code units
        threshold: Minimum density threshold (relative to mean)
        min_sep: Minimum separation between peaks (pc)

    Returns:
        list: List of (z_idx, y_idx, x_idx) peak positions
    """
    # Normalize density
    mean_rho = np.mean(density)
    norm_density = density / mean_rho

    # Apply threshold
    masked = np.where(norm_density > threshold, norm_density, 0)

    # Find local maxima
    local_max = maximum_filter(masked, size=PEAK_NEIGHBORHOOD)
    peaks = (local_max == masked) & (masked > 0)

    # Get peak indices
    peak_indices = np.argwhere(peaks)

    # Filter peaks by minimum separation
    if len(peak_indices) > 1:
        # Convert to physical coordinates (pc)
        coords = peak_indices * np.array([DZ_PC, DX_PC, DX_PC])

        # Calculate pairwise distances
        distances = pdist(coords)

        # Filter out peaks that are too close
        keep = [True] * len(peak_indices)
        for i in range(len(peak_indices)):
            for j in range(i + 1, len(peak_indices)):
                dist = np.linalg.norm(coords[i] - coords[j])
                if dist < min_sep:
                    # Keep the brighter peak
                    if norm_density[tuple(peak_indices[i])] < norm_density[tuple(peak_indices[j])]:
                        keep[i] = False
                    else:
                        keep[j] = False

        peak_indices = peak_indices[keep]

    return peak_indices


def measure_core_spacing(peak_indices):
    """
    Measure spacings between detected cores.

    Args:
        peak_indices: Array of peak positions [N, 3]

    Returns:
        dict: Spacing statistics
    """
    if len(peak_indices) < 2:
        return {'n_cores': len(peak_indices), 'spacings': []}

    # Convert to physical coordinates (pc)
    coords = peak_indices * np.array([DZ_PC, DX_PC, DX_PC])

    # Project onto filament axis (z)
    z_coords = coords[:, 0]
    z_coords = np.sort(z_coords)

    # Calculate spacings
    spacings = np.diff(z_coords)

    return {
        'n_cores': len(peak_indices),
        'spacings': spacings,
        'mean_spacing': np.mean(spacings) if len(spacings) > 0 else 0,
        'std_spacing': np.std(spacings) if len(spacings) > 0 else 0,
        'all_coords': coords
    }


# ============================================================
# ANALYSIS FUNCTIONS
# ============================================================

def analyze_snapshot(data, snapshot_idx):
    """
    Analyze a single snapshot for core properties.

    Args:
        data: Snapshot data dictionary
        snapshot_idx: Index of snapshot

    Returns:
        dict: Analysis results
    """
    density = data['density']

    # Detect cores
    peaks = detect_cores_3d(density)

    # Measure spacings
    spacing_stats = measure_core_spacing(peaks)

    # Calculate density statistics
    mean_rho = np.mean(density)
    max_rho = np.max(density)
    min_rho = np.min(density)

    # Calculate time (code units to Myr)
    # Assuming 1 code time unit ≈ 0.318 Myr for our parameters
    time_myr = data['time_code'] * 0.318

    return {
        'snapshot_idx': snapshot_idx,
        'time_myr': time_myr,
        'n_cores': spacing_stats['n_cores'],
        'spacings': spacing_stats['spacings'],
        'mean_spacing': spacing_stats['mean_spacing'],
        'std_spacing': spacing_stats['std_spacing'],
        'mean_density': mean_rho,
        'max_density': max_rho,
        'peak_indices': peaks
    }


def analyze_time_evolution(snapshots):
    """
    Analyze evolution of core properties over time.

    Args:
        snapshots: List of snapshot data

    Returns:
        list: Analysis results for each snapshot
    """
    results = []

    for i, data in enumerate(snapshots):
        result = analyze_snapshot(data, i)
        results.append(result)
        print(f"Snapshot {i}: t={result['time_myr']:.2f} Myr, "
              f"N_cores={result['n_cores']}, "
              f"<spacing>={result['mean_spacing']:.3f} pc")

    return results


# ============================================================
# VISUALIZATION
# ============================================================

def plot_filament_evolution(density, time_myr, output_path):
    """
    Create visualization of filament structure.

    Args:
        density: 3D density array
        time_myr: Simulation time in Myr
        output_path: Path to save figure
    """
    fig, axes = plt.subplots(2, 2, figsize=(12, 10))

    # 1. Mid-plane slice (x-z plane)
    mid_y = density.shape[1] // 2
    slice_xz = density[:, mid_y, :].T

    im0 = axes[0, 0].imshow(slice_xz, aspect='auto', origin='lower',
                            extent=[-DOMAIN_LENGTH_PC/2, DOMAIN_LENGTH_PC/2,
                                   -DOMAIN_WIDTH_PC/2, DOMAIN_WIDTH_PC/2])
    axes[0, 0].set_xlabel('z (pc)')
    axes[0, 0].set_ylabel('x (pc)')
    axes[0, 0].set_title(f'X-Z Slice (t={time_myr:.2f} Myr)')
    plt.colorbar(im0, ax=axes[0, 0], label='Density')

    # 2. Longitudinal profile (along filament axis)
    mid_x = density.shape[2] // 2
    mid_y = density.shape[1] // 2
    profile_z = density[:, mid_y, mid_x]

    z_coords = np.linspace(-DOMAIN_LENGTH_PC/2, DOMAIN_LENGTH_PC/2, len(profile_z))
    axes[0, 1].plot(z_coords, profile_z, 'b-', linewidth=2)
    axes[0, 1].set_xlabel('z (pc)')
    axes[0, 1].set_ylabel('Density')
    axes[0, 1].set_title('Longitudinal Density Profile')
    axes[0, 1].grid(True, alpha=0.3)

    # 3. Density histogram
    axes[1, 0].hist(density.flatten(), bins=50, log=True, alpha=0.7)
    axes[1, 0].set_xlabel('Density')
    axes[1, 0].set_ylabel('Count (log)')
    axes[1, 0].set_title('Density Distribution')

    # 4. Cross-sectional profile
    mid_z = density.shape[0] // 2
    slice_xy = density[mid_z, :, :]

    # Radial profile
    center_x = slice_xy.shape[1] // 2
    center_y = slice_xy.shape[0] // 2
    y_idx, x_idx = np.ogrid[:slice_xy.shape[0], :slice_xy.shape[1]]
    r = np.sqrt((x_idx - center_x)**2 + (y_idx - center_y)**2)
    r = r * DX_PC

    from scipy.stats import binned_statistic
    bin_edges = np.linspace(0, DOMAIN_WIDTH_PC/2, 20)
    bin_centers = 0.5 * (bin_edges[:-1] + bin_edges[1:])
    radial_profile, _, _ = binned_statistic(r.flatten(), slice_xy.flatten(),
                                             statistic='mean', bins=bin_edges)

    axes[1, 1].plot(bin_centers, radial_profile, 'r-', linewidth=2)
    axes[1, 1].set_xlabel('Radius (pc)')
    axes[1, 1].set_ylabel('Mean Density')
    axes[1, 1].set_title('Radial Profile')
    axes[1, 1].grid(True, alpha=0.3)

    plt.tight_layout()
    plt.savefig(output_path, dpi=150, bbox_inches='tight')
    plt.close()

    print(f"Saved: {output_path}")


def plot_spacing_evolution(results, output_path):
    """
    Plot evolution of core spacing over time.

    Args:
        results: List of analysis results
        output_path: Path to save figure
    """
    times = [r['time_myr'] for r in results if r['n_cores'] >= 2]
    spacings = [r['mean_spacing'] for r in results if r['n_cores'] >= 2]
    stds = [r['std_spacing'] for r in results if r['n_cores'] >= 2]

    fig, ax = plt.subplots(figsize=(10, 6))

    if len(spacings) > 0:
        ax.errorbar(times, spacings, yerr=stds, fmt='o-', capsize=3, linewidth=2)
        ax.axhline(y=0.213, color='r', linestyle='--', linewidth=2,
                   label='Observed (0.213 pc)')
        ax.axhspan(0.206, 0.220, alpha=0.2, color='r',
                   label='Observed range (±0.007 pc)')

    ax.set_xlabel('Time (Myr)', fontsize=12)
    ax.set_ylabel('Core Spacing (pc)', fontsize=12)
    ax.set_title('Evolution of Core-to-Core Spacing', fontsize=14)
    ax.legend()
    ax.grid(True, alpha=0.3)
    ax.set_xlim(0, max(times) * 1.1)

    plt.tight_layout()
    plt.savefig(output_path, dpi=150, bbox_inches='tight')
    plt.close()

    print(f"Saved: {output_path}")


# ============================================================
# MAIN ANALYSIS
# ============================================================

def main():
    """Main analysis function."""

    print("=" * 60)
    print("ATHENA++ 3D FILAMENT ANALYSIS")
    print("=" * 60)

    # Load all snapshots
    print("\nLoading snapshots...")
    snapshots = load_all_snapshots(INPUT_DIR)

    if len(snapshots) == 0:
        print(f"ERROR: No snapshots found in {INPUT_DIR}")
        print(f"Please ensure output directory exists and contains HDF5 files.")
        return

    # Analyze evolution
    print("\nAnalyzing time evolution...")
    results = analyze_time_evolution(snapshots)

    # Save results
    results_file = OUTPUT_DIR / "analysis_results.npz"
    np.savez(results_file,
             times=[r['time_myr'] for r in results],
             n_cores=[r['n_cores'] for r in results],
             spacings=[r['spacings'] for r in results],
             mean_spacings=[r['mean_spacing'] for r in results])
    print(f"\nSaved: {results_file}")

    # Generate figures for final snapshot
    print("\nGenerating figures...")
    final_data = snapshots[-1]
    final_time = final_data['time_code'] * 0.318

    plot_filament_evolution(
        final_data['density'],
        final_time,
        OUTPUT_DIR / f"filament_t{final_time:.1f}myr.png"
    )

    # Plot spacing evolution
    plot_spacing_evolution(
        results,
        OUTPUT_DIR / "spacing_evolution.png"
    )

    # Summary statistics
    print("\n" + "=" * 60)
    print("FINAL RESULTS")
    print("=" * 60)

    final_result = results[-1]
    print(f"\nFinal time: {final_result['time_myr']:.2f} Myr")
    print(f"Number of cores: {final_result['n_cores']}")

    if final_result['n_cores'] >= 2:
        print(f"Mean spacing: {final_result['mean_spacing']:.3f} ± "
              f"{final_result['std_spacing']:.3f} pc")

        # Compare to observed
        observed = 0.213
        error_pct = abs(final_result['mean_spacing'] - observed) / observed * 100
        print(f"\nComparison to observed (0.213 pc):")
        print(f"  Difference: {error_pct:.1f}%")

        if error_pct < 10:
            print("  ✓ GOOD AGREEMENT with observations!")
        elif error_pct < 20:
            print("  ~ MODERATE AGREEMENT with observations")
        else:
            print("  ✗ POOR AGREEMENT - may need parameter adjustment")

    print("\n" + "=" * 60)
    print("Analysis complete!")
    print(f"Results saved to: {OUTPUT_DIR}")
    print("=" * 60)


if __name__ == "__main__":
    main()
