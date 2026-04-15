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
Analyze filament fragmentation from Athena++ output files

Quick analysis script to measure core spacing from simulation outputs.
Designed to run on the server where the simulations are executed.
"""

import numpy as np
from pathlib import Path
import json
from scipy.signal import find_peaks
import warnings
warnings.filterwarnings('ignore')


def read_athena_tab(filename):
    """Read Athena++ .tab file (output at specific time step)"""
    # Athena++ tab files are simple ASCII with metadata header
    # We need to skip the header and read the data

    with open(filename, 'r') as f:
        lines = f.readlines()

    # Find where data starts (after '#')
    data_start = 0
    for i, line in enumerate(lines):
        if not line.strip().startswith('#'):
            data_start = i
            break

    # Read data (assume space-separated)
    data = np.loadtxt(lines[data_start:])

    return data


def extract_axial_density(output_dir, step=-1):
    """
    Extract mean axial density profile from Athena++ output.

    Parameters:
    -----------
    output_dir : Path
        Directory containing simulation output files
    step : int
        Time step to analyze (default: last step)

    Returns:
    --------
    x : array
        Axial positions
    rho_mean : array
        Mean density in cylindrical slices
    """
    output_dir = Path(output_dir)

    # Find output files
    tab_files = sorted(output_dir.glob('*.tab'))

    if len(tab_files) == 0:
        raise FileNotFoundError(f"No .tab files found in {output_dir}")

    # Use specified step or last available
    if step == -1:
        step = len(tab_files) - 1

    data_file = tab_files[step]

    try:
        data = read_athena_tab(data_file)
    except Exception as e:
        raise RuntimeError(f"Failed to read {data_file}: {e}")

    # Extract coordinates (assuming x is axial direction, index 0)
    # Density is typically index 4 or 5 (depending on output variables)
    x = data[:, 0]

    # For a 3D simulation, we need to average over y-z to get axial profile
    # This is a simplified version - actual implementation depends on grid structure

    # Assuming data format: x, y, z, rho, ...
    # We'll bin in x and average

    nbins = 200
    x_bins = np.linspace(x.min(), x.max(), nbins + 1)
    x_centers = 0.5 * (x_bins[1:] + x_bins[:-1])

    # Simple mean density per x-slice
    rho_mean = np.zeros(nbins)

    # For tab file output, we need to handle the data structure
    # This is simplified - adjust based on actual output format
    try:
        rho = data[:, 4]  # Density column
        for i in range(nbins):
            mask = (x >= x_bins[i]) & (x < x_bins[i+1])
            if mask.sum() > 0:
                rho_mean[i] = rho[mask].mean()
    except IndexError:
        # Fallback: use all values
        rho_mean = data[:, 4]

    return x_centers, rho_mean


def measure_spacing(x, rho, prominence_factor=0.3):
    """
    Measure core spacing from axial density profile.

    Parameters:
    -----------
    x : array
        Axial positions
    rho : array
        Density values
    prominence_factor : float
        Peak prominence as fraction of (max - min)

    Returns:
    --------
    results : dict
        Dictionary with spacing measurements
    """
    # Use log density for peak finding (more robust)
    log_rho = np.log10(rho + 1e-10)

    # Calculate prominence threshold
    prominence = prominence_factor * (log_rho.max() - log_rho.min())

    # Find peaks
    peaks, properties = find_peaks(
        log_rho,
        prominence=prominence,
        distance=5  # Minimum spacing between peaks
    )

    if len(peaks) < 2:
        return {
            'n_cores': len(peaks),
            'peak_positions': x[peaks].tolist() if len(peaks) > 0 else [],
            'spacings': [],
            'spacing_mean': None,
            'spacing_std': None,
            'lambda_W': None,
        }

    # Calculate spacings
    peak_x = x[peaks]
    spacings = np.diff(peak_x)

    # Remove outliers (spacings that are too large/small)
    median_spacing = np.median(spacings)
    iqr = np.percentile(spacings, 75) - np.percentile(spacings, 25)
    valid = (spacings > median_spacing - 1.5*iqr) & (spacings < median_spacing + 1.5*iqr)

    robust_spacings = spacings[valid]

    if len(robust_spacings) > 0:
        spacing_mean = robust_spacings.mean()
        spacing_std = robust_spacings.std()
    else:
        spacing_mean = spacings.mean()
        spacing_std = spacings.std()

    # Convert to λ/W (where W = 2 code units)
    W_fil = 2.0
    lambda_W = spacing_mean / W_fil

    return {
        'n_cores': len(peaks),
        'peak_positions': peak_x.tolist(),
        'spacings': spacings.tolist(),
        'robust_spacings': robust_spacings.tolist(),
        'spacing_mean': float(spacing_mean),
        'spacing_std': float(spacing_std),
        'lambda_W': float(lambda_W),
    }


def analyze_simulation(sim_name, output_base='outputs'):
    """Analyze one simulation and return results"""

    output_dir = Path(output_base) / sim_name

    if not output_dir.exists():
        return {
            'sim_name': sim_name,
            'error': f'Output directory not found: {output_dir}'
        }

    try:
        # Extract axial density profile
        x, rho = extract_axial_density(output_dir)

        # Measure spacing
        results = measure_spacing(x, rho)
        results['sim_name'] = sim_name

        return results

    except Exception as e:
        return {
            'sim_name': sim_name,
            'error': str(e)
        }


def main():
    """Analyze all simulations and generate summary"""

    # Load simulation design
    design_file = Path(__file__).parent / 'moderate_supercriticality_design.json'
    if not design_file.exists():
        print(f"Design file not found: {design_file}")
        print("Run moderate_supercriticality_test.py first to generate design.")
        return

    with open(design_file) as f:
        design = json.load(f)

    print("=" * 70)
    print("FILAMENT FRAGMENTATION ANALYSIS")
    print("=" * 70)

    # Analyze all simulations
    results = []
    for sim in design['simulations']:
        sim_name = sim['name']
        print(f"\nAnalyzing: {sim_name}...")

        result = analyze_simulation(sim_name)
        results.append(result)

        if 'error' in result:
            print(f"  ERROR: {result['error']}")
        else:
            print(f"  Cores: {result['n_cores']}")
            if result['lambda_W'] is not None:
                print(f"  λ/W: {result['lambda_W']:.3f} ± {result['spacing_std']/2.0:.3f}")

    # Save results
    output_file = Path(__file__).parent / 'fragmentation_results.json'
    with open(output_file, 'w') as f:
        json.dump({
            'analysis': 'moderate_supercriticality_test',
            'results': results,
        }, f, indent=2)

    print(f"\nResults saved to: {output_file}")

    # Generate summary table
    print("\n" + "=" * 70)
    print("SUMMARY TABLE")
    print("=" * 70)
    print(f"{'Sim':<25} {'ρ_c':<6} {'β':<6} {'f':<6} {'N':<4} {'λ/W':<8}")
    print("-" * 70)

    successful = [r for r in results if 'error' not in r]

    for r, sim in zip(results, design['simulations']):
        if 'error' in r:
            print(f"{sim['name']:<25} {sim['rho_center']:<6.1f} {sim['beta']:<6.1f} "
                  f"{sim['supercriticality']:<6.2f} {'ERR':<4} {'N/A':<8}")
        else:
            print(f"{sim['name']:<25} {sim['rho_center']:<6.1f} {sim['beta']:<6.1f} "
                  f"{sim['supercriticality']:<6.2f} {r['n_cores']:<4} "
                  f"{r['lambda_W']:.3f}" if r['lambda_W'] else "N/A")

    if successful:
        # Aggregate by (rho_c, beta)
        from collections import defaultdict
        aggregates = defaultdict(list)

        for r, sim in zip(results, design['simulations']):
            if 'error' not in r and r['lambda_W'] is not None:
                key = (sim['rho_center'], sim['beta'])
                aggregates[key].append(r['lambda_W'])

        print("\n" + "=" * 70)
        print("AGGREGATE RESULTS")
        print("=" * 70)
        print(f"{'ρ_c':<6} {'β':<6} {'λ/W (mean)':<12} {'λ/W (std)':<12} {'N':<4}")
        print("-" * 70)

        for (rho_c, beta), values in sorted(aggregates.items()):
            mean = np.mean(values)
            std = np.std(values)
            print(f"{rho_c:<6.1f} {beta:<6.1f} {mean:<12.3f} {std:<12.3f} {len(values):<4}")


if __name__ == '__main__':
    main()
