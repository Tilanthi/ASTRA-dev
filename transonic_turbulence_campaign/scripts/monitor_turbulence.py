#!/usr/bin/env python3
"""
monitor_turbulence.py

Real-time turbulence monitoring for transonic campaign simulations.

Usage:
    python monitor_turbulence.py <run_directory>
    python monitor_turbulence.py <run_directory> --watch
"""

import sys
import os
import h5py
import numpy as np
import argparse
from pathlib import Path
from typing import Tuple, Dict

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))


def compute_mach_number(h5_file: h5py.File) -> Tuple[np.ndarray, np.ndarray]:
    """
    Compute turbulent Mach number from simulation snapshot.

    Parameters
    ----------
    h5_file : h5py.File
        Open HDF5 file object

    Returns
    -------
    time : float
        Simulation time in t_J
    M_turb : float
        Turbulent Mach number
    """
    try:
        # Try Athena++ v21.0 structure
        if 'Level0' in h5_file:
            # Get last time snapshot
            last_level = h5_file['Level0'][-1]

            if 'prim' in last_level:
                prim = last_level['prim']

                # Get velocity and density
                if 'vel' in prim and 'rho' in prim:
                    vel = prim['vel'][()]
                    rho = prim['rho'][()]

                    # Mass-weighted rms velocity
                    vel_rms = np.sqrt(np.sum(rho * vel**2) / np.sum(rho))

                    # Sound speed is 1.0 in normalized units
                    cs = 1.0
                    M_turb = vel_rms / cs

                    # Get time from attributes
                    time = last_level.attrs.get('Time', 0.0)

                    return time, M_turb

    except Exception as e:
        print(f"Warning: Error computing Mach number: {e}")
        return 0.0, 0.0

    return 0.0, 0.0


def find_hdf5_files(run_dir: str) -> list:
    """Find all HDF5 output files in run directory."""
    run_path = Path(run_dir)

    # Look for common patterns
    patterns = [
        "*.h5",
        "*.hdf5",
        "turb.*.h5",
        "*.athdf",
        "block*.h5"
    ]

    hdf5_files = []
    for pattern in patterns:
        hdf5_files.extend(run_path.glob(pattern))

    return sorted(hdf5_files)


def analyze_run_directory(run_dir: str) -> Dict:
    """
    Analyze turbulence in a simulation run directory.

    Parameters
    ----------
    run_dir : str
        Path to run directory

    Returns
    -------
    results : dict
        Dictionary with analysis results
    """
    run_path = Path(run_dir)

    if not run_path.exists():
        return {"error": f"Directory not found: {run_dir}"}

    # Find HDF5 files
    hdf5_files = find_hdf5_files(run_dir)

    if not hdf5_files:
        return {"error": f"No HDF5 files found in {run_dir}"}

    # Analyze evolution
    times = []
    mach_numbers = []

    for h5_file in hdf5_files:
        try:
            with h5py.File(h5_file, 'r') as f:
                time, M_turb = compute_mach_number(f)
                times.append(time)
                mach_numbers.append(M_turb)
        except Exception as e:
            print(f"Warning: Could not read {h5_file}: {e}")
            continue

    if not times:
        return {"error": "No valid snapshots found"}

    times = np.array(times)
    mach_numbers = np.array(mach_numbers)

    # Statistics
    results = {
        "run_directory": str(run_path),
        "n_snapshots": len(times),
        "time_final": times[-1],
        "M_turb_final": mach_numbers[-1],
        "M_turb_mean": np.mean(mach_numbers),
        "M_turb_std": np.std(mach_numbers),
        "M_turb_max": np.max(mach_numbers),
        "M_turb_min": np.min(mach_numbers),
        "times": times,
        "mach_numbers": mach_numbers,
        "transonic_achieved": np.any(mach_numbers >= 1.0),
        "supersonic_achieved": np.any(mach_numbers >= 2.0)
    }

    return results


def print_summary(results: Dict):
    """Print summary of turbulence analysis."""
    if "error" in results:
        print(f"ERROR: {results['error']}")
        return

    print("\n" + "="*60)
    print(f"Turbulence Analysis: {Path(results['run_directory']).name}")
    print("="*60)

    print(f"\nSnapshots analyzed: {results['n_snapshots']}")
    print(f"Final time: {results['time_final']:.3f} t_J")

    print(f"\nTurbulent Mach Number:")
    print(f"  Final:   {results['M_turb_final']:.3f}")
    print(f"  Mean:    {results['M_turb_mean']:.3f} ± {results['M_turb_std']:.3f}")
    print(f"  Range:   {results['M_turb_min']:.3f} - {results['M_turb_max']:.3f}")

    print(f"\nRegime Assessment:")
    if results['supersonic_achieved']:
        print("  ✓ SUPERSONIC (M >= 2) achieved")
    elif results['transonic_achieved']:
        print("  ✓ TRANSONIC (M >= 1) achieved")
    else:
        print("  ✗ Subsonic only (M < 1)")

    # Success criteria
    if results['M_turb_mean'] >= 1.0:
        print(f"\n✓ SUCCESS: Sustained transonic turbulence achieved")
    else:
        print(f"\n✗ FAILED: Mean M_turb < 1.0 (deeply subsonic)")

    print("="*60)


def watch_mode(run_dir: str, interval: int = 60):
    """
    Watch mode: Monitor turbulence at regular intervals.

    Parameters
    ----------
    run_dir : str
        Path to run directory
    interval : int
        Check interval in seconds
    """
    import time

    print(f"Watching {run_dir} (interval: {interval}s)")
    print("Press Ctrl+C to stop\n")

    try:
        while True:
            results = analyze_run_directory(run_dir)
            print_summary(results)

            if "error" in results:
                print("Waiting for simulation to start...")
            else:
                # Show progress if still running
                if results['time_final'] < 6.0:
                    progress = results['time_final'] / 6.0 * 100
                    print(f"\nSimulation progress: {progress:.1f}%")
                    print(f"Next check in {interval}s... (Ctrl+C to stop)")

            print("\n" + "-"*60 + "\n")
            time.sleep(interval)

    except KeyboardInterrupt:
        print("\nStopped watching.")


def main():
    parser = argparse.ArgumentParser(
        description="Monitor turbulence in Athena++ simulations"
    )
    parser.add_argument(
        "run_dir",
        help="Path to simulation run directory"
    )
    parser.add_argument(
        "--watch", "-w",
        action="store_true",
        help="Watch mode: monitor at regular intervals"
    )
    parser.add_argument(
        "--interval", "-i",
        type=int,
        default=60,
        help="Check interval for watch mode (seconds, default: 60)"
    )
    parser.add_argument(
        "--output", "-o",
        help="Save results to JSON file"
    )

    args = parser.parse_args()

    if args.watch:
        watch_mode(args.run_dir, args.interval)
    else:
        results = analyze_run_directory(args.run_dir)
        print_summary(results)

        if args.output:
            import json
            with open(args.output, 'w') as f:
                # Convert arrays to lists for JSON serialization
                output_data = {k: v.tolist() if isinstance(v, np.ndarray) else v
                              for k, v in results.items()}
                json.dump(output_data, f, indent=2)
            print(f"\nResults saved to: {args.output}")


if __name__ == "__main__":
    main()
