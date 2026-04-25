#!/usr/bin/env python3
"""
Measure fragmentation time (t_frag) from Athena++ simulation output.

This script analyzes time-series data to measure both radial collapse time
and longitudinal beading time for regime boundary analysis.

Usage:
    python measure_tfrag.py --simulation_dir <path> --output <output.json>

Output:
    JSON file containing t_frag measurements and diagnostics
"""

import numpy as np
import h5py
import json
import argparse
from pathlib import Path


def measure_tfrag_radial(time_series):
    """
    Measure radial collapse time from time series data.

    Radial collapse is identified when the minimum radial distance
    drops below a threshold (typically 0.1 lambda_J).

    Parameters:
    -----------
    time_series : dict
        Dictionary containing time series data

    Returns:
    --------
    t_frag : float or None
        Radial collapse time in units of t_ff
    """
    if 'min_radial_distance' not in time_series:
        return None

    times = time_series['times']
    min_r = time_series['min_radial_distance']

    # Find when radial distance drops below threshold
    threshold = 0.1  # lambda_J
    collapse_idx = np.where(min_r < threshold)[0]

    if len(collapse_idx) == 0:
        return None  # No collapse

    t_frag = times[collapse_idx[0]]
    return t_frag


def measure_tfrag_longitudinal(time_series):
    """
    Measure longitudinal beading time from time series data.

    Longitudinal beading is identified when the amplitude of the
    dominant longitudinal mode exceeds a threshold.

    Parameters:
    -----------
    time_series : dict
        Dictionary containing time series data

    Returns:
    --------
    t_frag : float or None
        Longitudinal beading time in units of t_ff
    """
    if 'longitudinal_mode_amplitude' not in time_series:
        return None

    times = time_series['times']
    mode_amp = time_series['longitudinal_mode_amplitude']

    # Find when mode amplitude exceeds threshold
    threshold = 0.2  # Relative to mean density
    beading_idx = np.where(mode_amp > threshold)[0]

    if len(beading_idx) == 0:
        return None  # No beading

    t_frag = times[beading_idx[0]]
    return t_frag


def measure_tfrag_timestep(time_series):
    """
    Measure fragmentation time from timestep watchdog.

    The timestep watchdog identifies runaway collapse when
    dt < 1e-8 * t_ff.

    Parameters:
    -----------
    time_series : dict
        Dictionary containing time series data

    Returns:
    --------
    t_frag : float or None
        Fragmentation time in units of t_ff
    """
    if 'timestep' not in time_series:
        return None

    times = time_series['times']
    dt = time_series['timestep']

    # Find when timestep drops below threshold
    threshold = 1e-8
    watchdog_idx = np.where(dt < threshold)[0]

    if len(watchdog_idx) == 0:
        return None  # No fragmentation

    t_frag = times[watchdog_idx[0]]
    return t_frag


def read_time_series(simulation_dir):
    """
    Read time series data from simulation directory.

    Parameters:
    -----------
    simulation_dir : Path
        Directory containing simulation output

    Returns:
    --------
    time_series : dict or None
        Dictionary containing time series data
    """
    # Look for time series HDF5 file
    ts_file = Path(simulation_dir) / 'time_series.hdf5'

    if not ts_file.exists():
        return None

    with h5py.File(ts_file, 'r') as f:
        times = f['times'][:]

        time_series = {'times': times}

        # Read available datasets
        for key in f.keys():
            if key != 'times':
                time_series[key] = f[key][:]

    return time_series


def extract_simulation_parameters(simulation_dir):
    """
    Extract simulation parameters from directory.

    Parameters:
    -----------
    simulation_dir : Path
        Directory containing simulation output

    Returns:
    --------
    params : dict
        Dictionary of simulation parameters
    """
    # Try to read from parameter file
    param_file = Path(simulation_dir) / 'simulation_params.json'

    params = {}

    if param_file.exists():
        with open(param_file, 'r') as f:
            params = json.load(f)
    else:
        # Try to extract from final snapshot attributes
        snapshot_file = Path(simulation_dir) / 'final_snapshot.hdf5'
        if snapshot_file.exists():
            with h5py.File(snapshot_file, 'r') as f:
                params = {
                    'line_mass': f.attrs.get('line_mass', np.nan),
                    'plasma_beta': f.attrs.get('plasma_beta', np.nan),
                    'mach_number': f.attrs.get('mach_number', np.nan),
                    'gamma': f.attrs.get('gamma', 1.0),
                    'field_geometry': f.attrs.get('field_geometry', 'longitudinal')
                }

    return params


def analyze_regime_classification(simulation_dir, time_series):
    """
    Classify the fragmentation regime based on time series data.

    Parameters:
    -----------
    simulation_dir : Path
        Directory containing simulation output
    time_series : dict or None
        Time series data

    Returns:
    --------
    regime : str
        Fragmentation regime classification
    """
    params = extract_simulation_parameters(simulation_dir)
    f = params.get('line_mass', np.nan)

    if np.isnan(f):
        return 'unknown'

    # Classify based on line mass
    if f < 1.2:
        return 'near_critical'
    elif f > 1.5:
        return 'supercritical'
    else:
        return 'transition'


def main():
    parser = argparse.ArgumentParser(description='Measure t_frag from Athena++ simulations')
    parser.add_argument('--simulation_dir', type=str, required=True,
                        help='Directory containing simulation output')
    parser.add_argument('--output', type=str, required=True,
                        help='Output JSON file path')

    args = parser.parse_args()

    # Read time series
    time_series = read_time_series(args.simulation_dir)

    # Extract simulation parameters
    params = extract_simulation_parameters(args.simulation_dir)

    # Measure fragmentation times
    results = {
        'simulation_dir': str(args.simulation_dir),
        'parameters': params
    }

    if time_series is not None:
        # Measure using different methods
        t_frag_radial = measure_tfrag_radial(time_series)
        t_frag_longitudinal = measure_tfrag_longitudinal(time_series)
        t_frag_timestep = measure_tfrag_timestep(time_series)

        results['t_frag_radial'] = t_frag_radial
        results['t_frag_longitudinal'] = t_frag_longitudinal
        results['t_frag_timestep'] = t_frag_timestep

        # Classify regime
        regime = analyze_regime_classification(args.simulation_dir, time_series)
        results['regime_classification'] = regime

        # Determine which t_frag is primary
        if regime == 'near_critical':
            results['t_frag_primary'] = t_frag_longitudinal if t_frag_longitudinal is not None else t_frag_timestep
        elif regime == 'supercritical':
            results['t_frag_primary'] = t_frag_radial if t_frag_radial is not None else t_frag_timestep
        else:
            # Transition regime - use whichever is available
            results['t_frag_primary'] = t_frag_timestep
    else:
        results['error'] = 'No time series data found'

    # Write to JSON
    with open(args.output, 'w') as f:
        json.dump(results, f, indent=2)

    print(f"Results written to {args.output}")
    if 't_frag_primary' in results:
        print(f"t_frag (primary): {results['t_frag_primary']:.3f} t_ff")
    if 'regime_classification' in results:
        print(f"Regime: {results['regime_classification']}")


if __name__ == '__main__':
    main()
