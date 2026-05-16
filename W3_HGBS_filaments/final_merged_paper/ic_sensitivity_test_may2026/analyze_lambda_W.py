#!/usr/bin/env python3
"""
Analyze Fragmentation Wavelength from HDF5 Snapshots

Measures λ/W (fragmentation wavelength / filament width) from
Athena++ HDF5 output files for the IC sensitivity test campaign.

Uses the same methodology as the 2193-simulation DTC analysis:
1. Load final HDF5 snapshot
2. Extract column density Σ(x,y) by integrating ρ along z-axis
3. Identify density maxima (cores) above threshold
4. Measure nearest-neighbor spacings
5. Compute median λ/W
"""

import h5py
import numpy as np
import json
import os
from pathlib import Path
from typing import Dict, List, Tuple
from scipy.ndimage import gaussian_filter, maximum_filter
from scipy.spatial import cKDTree

# Analysis parameters
DENSITY_THRESHOLD = 1.5  # Core identification threshold (× background)
CORE_SEPARATION_MIN = 8  # Minimum cell separation between cores
FILAMENT_WIDTH = 2.0     # Assumed filament width in code units (W = 2 × r_core)

def load_final_snapshot(run_dir: str, run_id: str) -> Tuple[np.ndarray, dict]:
    """Load the final HDF5 snapshot from a simulation directory."""
    # Find HDF5 files
    hdf5_files = list(Path(run_dir).glob("*.hdf5"))

    if not hdf5_files:
        raise FileNotFoundError(f"No HDF5 files found in {run_dir}")

    # Sort by filename and take the last one (final snapshot)
    hdf5_files.sort()
    final_file = hdf5_files[-1]

    print(f"Loading {final_file.name}")

    with h5py.File(final_file, 'r') as f:
        # Get density field
        density = f['dens'][:]

        # Get metadata
        metadata = {
            'time': f.attrs.get('Time', 0.0),
            'ncells': density.shape,
            'file': str(final_file)
        }

    return density, metadata

def compute_column_density(density: np.ndarray) -> np.ndarray:
    """Compute column density Σ(x,y) by integrating ρ along z-axis."""
    # density shape: (nx3, nx2, nx1) -> integrate over axis 0 (z)
    sigma = np.trapz(density, axis=0)
    return sigma

def identify_cores(sigma: np.ndarray, threshold: float = DENSITY_THRESHOLD) -> np.ndarray:
    """Identify density maxima (cores) in column density map."""
    # Smooth the column density map
    sigma_smooth = gaussian_filter(sigma, sigma=2)

    # Compute background level (median)
    background = np.median(sigma_smooth)

    # Find local maxima above threshold
    local_max = maximum_filter(sigma_smooth, size=20) == sigma_smooth
    cores = np.where(local_max & (sigma_smooth > threshold * background))

    return np.array(cores).T  # Return as (N_cores, 2) array

def measure_nearest_neighbor_spacings(core_positions: np.ndarray, domain_size: Tuple[float, float]) -> np.ndarray:
    """Measure nearest-neighbor spacings between cores using periodic boundary conditions."""
    if len(core_positions) < 2:
        return np.array([])

    # Build KD-tree for efficient nearest-neighbor search
    tree = cKDTree(core_positions, boxsize=domain_size)

    # Query nearest neighbor for each core (excluding self)
    distances, _ = tree.query(core_positions, k=2)  # k=2 because first neighbor is self

    # Return second column (nearest neighbor, not self)
    nn_distances = distances[:, 1]

    return nn_distances

def compute_lambda_over_W(sigma: np.ndarray, core_positions: np.ndarray, domain_size: Tuple[float, float]) -> Dict:
    """Compute λ/W from column density map and core positions."""
    if len(core_positions) < 2:
        return {
            'lambda_W': None,
            'n_cores': len(core_positions),
            'note': 'Insufficient cores for measurement'
        }

    # Measure nearest-neighbor spacings
    nn_spacings = measure_nearest_neighbor_spacings(core_positions, domain_size)

    # Compute median spacing
    lambda_median = np.median(nn_spacings)

    # Compute λ/W (assuming filament width W = 2.0 code units)
    lambda_over_W = lambda_median / FILAMENT_WIDTH

    return {
        'lambda_W': lambda_over_W,
        'lambda_median': lambda_median,
        'W': FILAMENT_WIDTH,
        'n_cores': len(core_positions),
        'nn_spacings': nn_spacings.tolist(),
        'note': 'Success'
    }

def analyze_single_simulation(run_dir: str, run_id: str) -> Dict:
    """Analyze a single simulation and return λ/W measurement."""
    print(f"\nAnalyzing {run_id}...")

    result = {
        'run_id': run_id,
        'status': 'FAILED',
        'lambda_W': None
    }

    try:
        # Load final snapshot
        density, metadata = load_final_snapshot(run_dir, run_id)

        # Compute column density
        sigma = compute_column_density(density)

        # Get domain size (assuming x1max - x1min, x2max - x2min)
        # For our setup: x1 ∈ [-4, 4], x2 ∈ [-1, 1]
        domain_size = (8.0, 2.0)

        # Identify cores
        core_positions = identify_cores(sigma)

        print(f"  Found {len(core_positions)} cores")

        # Compute λ/W
        lambda_result = compute_lambda_over_W(sigma, core_positions, domain_size)

        result.update({
            'status': 'SUCCESS',
            'lambda_W': lambda_result['lambda_W'],
            'n_cores': lambda_result['n_cores'],
            'lambda_median': lambda_result.get('lambda_median'),
            'time': metadata['time']
        })

        print(f"  λ/W = {lambda_result['lambda_W']:.3f}")

    except Exception as e:
        print(f"  Error: {e}")
        result['note'] = str(e)

    return result

def load_campaign_summary() -> Dict:
    """Load campaign summary to get list of all simulations."""
    summary_path = "output/campaign_summary.json"
    if not os.path.exists(summary_path):
        raise FileNotFoundError(f"Campaign summary not found at {summary_path}")

    with open(summary_path, 'r') as f:
        return json.load(f)

def main():
    import argparse

    parser = argparse.ArgumentParser(description="Analyze λ/W from HDF5 snapshots")
    parser.add_argument("--run-id", type=str, default=None,
                       help="Analyze specific run ID (default: analyze all)")
    parser.add_argument("--work-dir", type=str, default="output/simulations",
                       help="Working directory for simulations")
    parser.add_argument("--output", type=str, default="output/analysis/lambda_W_measurements.json",
                       help="Output JSON file")
    args = parser.parse_args()

    print("IC Sensitivity Test: λ/W Analysis")
    print("="*60)

    # Load campaign summary
    try:
        campaign = load_campaign_summary()
        all_results = campaign['results']
    except FileNotFoundError:
        print("Warning: Campaign summary not found. Using run_list.json instead")
        with open('run_list.json', 'r') as f:
            campaign = json.load(f)
            all_results = campaign['simulations']

    # Filter for specific run_id if requested
    if args.run_id:
        all_results = [r for r in all_results if r['run_id'] == args.run_id]
        print(f"Analyzing single run: {args.run_id}")
    else:
        print(f"Analyzing all {len(all_results)} simulations")

    # Analyze each simulation
    lambda_W_results = []

    for sim_result in all_results:
        run_id = sim_result['run_id']

        # Skip if simulation didn't fragment
        if sim_result.get('status') != 'FRAG':
            print(f"Skipping {run_id} (status: {sim_result.get('status')})")
            lambda_W_results.append({
                'run_id': run_id,
                'status': 'SKIPPED',
                'lambda_W': None,
                'note': f"Simulation did not fragment (status: {sim_result.get('status')})"
            })
            continue

        # Analyze simulation
        run_dir = os.path.join(args.work_dir, run_id)
        lambda_result = analyze_single_simulation(run_dir, run_id)

        # Add metadata from campaign summary
        lambda_result['f'] = sim_result['f']
        lambda_result['beta'] = sim_result['beta']
        lambda_result['mach'] = sim_result['mach']
        lambda_result['ic_type'] = sim_result.get('ic_type', 'king')
        lambda_result['seed'] = sim_result['seed']

        lambda_W_results.append(lambda_result)

    # Write results to JSON
    os.makedirs(os.path.dirname(args.output), exist_ok=True)
    with open(args.output, 'w') as f:
        json.dump(lambda_W_results, f, indent=2)

    print(f"\nResults written to {args.output}")

    # Print summary
    successful = [r for r in lambda_W_results if r['status'] == 'SUCCESS']
    print(f"\nSummary:")
    print(f"  Successfully analyzed: {len(successful)}/{len(lambda_W_results)}")

    if successful:
        king_results = [r for r in successful if r.get('ic_type') == 'king']
        unif_results = [r for r in successful if r.get('ic_type') == 'uniform']

        king_lambda_W = [r['lambda_W'] for r in king_results if r['lambda_W']]
        unif_lambda_W = [r['lambda_W'] for r in unif_results if r['lambda_W']]

        print(f"\nBy IC type:")
        if king_lambda_W:
            print(f"  King IC:    λ/W = {np.mean(king_lambda_W):.3f} ± {np.std(king_lambda_W):.3f} (N={len(king_lambda_W)})")
        if unif_lambda_W:
            print(f"  Uniform IC: λ/W = {np.mean(unif_lambda_W):.3f} ± {np.std(unif_lambda_W):.3f} (N={len(unif_lambda_W)})")

    print("\nNext step: Run python3 compare_ic_sensitivity.py")

if __name__ == "__main__":
    main()
