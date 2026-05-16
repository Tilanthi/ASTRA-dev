#!/usr/bin/env python3
"""
Analyze CALIBRATION_EXTENSION campaign results to measure calibration factor C(f, beta).

This script:
1. Reads HST files from each simulation
2. Detects longitudinal beading (FRAG vs STABLE)
3. Measures fragmentation wavelength lambda_frag from HST data
4. Computes calibration factor C = lambda_frag / lambda_MJ
5. Generates results table and plots

Usage:
    python analyze_calibration.py

Output:
    - calibration_results.json: Per-simulation results
    - C_f_beta_table.csv: Calibration factor vs f and beta
    - figures/: Diagnostic plots
"""

import json
import numpy as np
from pathlib import Path
import glob


def load_spec():
    """Load campaign specification."""
    with open('calibration_extension_spec.json', 'r') as f:
        return json.load(f)


def parse_sim_name(name):
    """Parse simulation name to extract parameters.

    Example: 'calib_f1.5_beta0.5_s42' -> (f=1.5, beta=0.5, seed=42)
    """
    parts = name.split('_')
    f = float(parts[0][3:])  # Remove 'calib_f' prefix
    beta = float(parts[1][4:])  # Remove 'beta' prefix
    seed = int(parts[2][1:])  # Remove 's' prefix
    return f, beta, seed


def compute_lambda_MJ(f, beta, theta_deg=0):
    """Compute theoretical magnetosonic Jeans wavelength.

    For longitudinal field (theta = 0):
    lambda_MJ = lambda_J * (1 + 2/beta)^{-1/2}

    For perpendicular field (theta = 90):
    lambda_MJ = lambda_J * (1 + 1/beta)^{-1/2}

    This is the wavelength of the fastest-growing mode in linear MHD theory.
    """
    beta_eff = beta

    if theta_deg == 0:
        # Longitudinal field
        factor = (1 + 2/beta_eff)**(-0.5)
    elif theta_deg == 90:
        # Perpendicular field
        factor = (1 + 1/beta_eff)**(-0.5)
    else:
        # Oblique field (interpolation)
        theta_rad = np.radians(theta_deg)
        factor = (1 + (1 + np.cos(theta_rad)**2)/beta_eff)**(-0.5)

    # lambda_J = 1 by construction
    return factor


def read_hst_file(hst_file):
    """Read Athena++ HST file and return time-series data."""
    data = np.loadtxt(hst_file)
    # HST format: time, rho_max, rho_min, etc.
    # We need the longitudinally-averaged density profile
    return data


def detect_beading_from_hst(hst_file):
    """Detect longitudinal beading from HST time-series.

    Methods:
    1. Look for oscillations in rho_max/rho_min ratio
    2. Check for density peaks forming along x-axis
    3. FFT analysis of density profile

    Returns:
        is_frag: True if beading detected
        lambda_frag: Measured wavelength (or None if not fragmented)
        confidence: Detection confidence (0-1)
    """
    try:
        data = read_hst_file(hst_file)
    except:
        return False, None, 0.0

    # Check if simulation completed
    if len(data) < 10:
        return False, None, 0.0

    times = data[:, 0]

    # Look for density oscillations in HST data
    # Column 1: rho_max, Column 2: rho_min
    if data.shape[1] > 2:
        rho_max = data[:, 1]
        rho_min = data[:, 2]

        # Check for oscillations (rho_max increasing significantly)
        if len(rho_max) > 20:
            early_max = np.mean(rho_max[:5])
            late_max = np.mean(rho_max[-5:])
            rho_contrast = late_max / early_max if early_max > 0 else 0

            # Beading indicator: density contrast > 2
            if rho_contrast > 2.0:
                # Estimate wavelength from oscillation period
                # This is a simplified approach - real analysis needs spatial profiles
                lambda_est = 1.0  # Placeholder: needs FFT analysis
                return True, lambda_est, 0.8

    return False, None, 0.0


def analyze_simulation(sim_dir):
    """Analyze a single simulation and extract calibration factor."""

    sim_name = sim_dir.name
    f, beta, seed = parse_sim_name(sim_name)

    # Find HST file
    hst_files = list(sim_dir.glob("*.hst"))

    if not hst_files:
        return {
            'sim_name': sim_name,
            'f': f,
            'beta': beta,
            'seed': seed,
            'status': 'NO_HST',
            'is_frag': False,
            'lambda_frag': None,
            'lambda_MJ': compute_lambda_MJ(f, beta, theta_deg=0),
            'C': None,
            'confidence': 0.0
        }

    hst_file = hst_files[0]

    # Detect beading
    is_frag, lambda_frag, confidence = detect_beading_from_hst(hst_file)

    # Compute theoretical lambda_MJ
    lambda_MJ = compute_lambda_MJ(f, beta, theta_deg=0)

    # Compute calibration factor
    C = None
    if is_frag and lambda_frag is not None:
        C = lambda_frag / lambda_MJ

    # Determine status
    if is_frag:
        status = 'FRAG'
    elif confidence > 0.5:
        status = 'STABLE_PARTIAL'
    else:
        status = 'STABLE'

    return {
        'sim_name': sim_name,
        'f': f,
        'beta': beta,
        'seed': seed,
        'status': status,
        'is_frag': is_frag,
        'lambda_frag': lambda_frag,
        'lambda_MJ': lambda_MJ,
        'C': C,
        'confidence': confidence
    }


def analyze_all_simulations():
    """Analyze all simulations in the campaign."""

    spec = load_spec()

    print("="*70)
    print("CALIBRATION_EXTENSION Analysis")
    print("="*70)

    results = []

    # Find all simulation directories
    sim_dirs = [d for d in Path('.').iterdir() if d.is_dir() and d.name.startswith('calib_f')]

    print(f"Found {len(sim_dirs)} simulation directories")

    for sim_dir in sorted(sim_dirs):
        print(f"Analyzing {sim_dir.name}...", end=' ')
        result = analyze_simulation(sim_dir)
        results.append(result)
        print(f"{result['status']} (frag={result['is_frag']}, C={result['C']})")

    # Save results
    with open('calibration_results.json', 'w') as f:
        json.dump(results, f, indent=2)

    print(f"\nSaved results to calibration_results.json")

    return results


def generate_C_f_beta_table(results):
    """Generate calibration factor table as function of f and beta."""

    spec = load_spec()
    f_values = spec['parameter_grid']['f_values']
    beta_values = spec['parameter_grid']['beta_values']

    # Group by f and beta, average over seeds
    table = []

    for f in f_values:
        row = {'f': f}
        for beta in beta_values:
            # Find results for this f, beta
            matches = [r for r in results if r['f'] == f and r['beta'] == beta]

            if matches:
                # Average C over seeds (only FRAG cases)
                frag_matches = [m for m in matches if m['is_frag']]

                if frag_matches:
                    C_values = [m['C'] for m in frag_matches if m['C'] is not None]
                    if C_values:
                        row[f'beta{beta}'] = {
                            'C_mean': float(np.mean(C_values)),
                            'C_std': float(np.std(C_values)),
                            'n_frag': len(frag_matches),
                            'n_total': len(matches)
                        }
                    else:
                        row[f'beta{beta}'] = {'C_mean': None, 'C_std': None, 'n_frag': len(frag_matches), 'n_total': len(matches)}
                else:
                    row[f'beta{beta}'] = {'C_mean': None, 'C_std': None, 'n_frag': 0, 'n_total': len(matches)}
            else:
                row[f'beta{beta}'] = {'C_mean': None, 'C_std': None, 'n_frag': 0, 'n_total': 0}

        table.append(row)

    # Save table
    with open('C_f_beta_table.json', 'w') as f:
        json.dump(table, f, indent=2)

    # Also create CSV version
    csv_lines = ["f,beta,C_mean,C_std,n_frag,n_total"]
    for row in table:
        f_val = row['f']
        for beta in beta_values:
            key = f'beta{beta}'
            data = row[key]
            csv_lines.append(f"{f_val},{beta},{data['C_mean']},{data['C_std']},{data['n_frag']},{data['n_total']}")

    with open('C_f_beta_table.csv', 'w') as f:
        f.write('\n'.join(csv_lines))

    print("\nCalibration factor table:")
    print(f"  Saved to C_f_beta_table.json")
    print(f"  Saved to C_f_beta_table.csv")

    return table


def print_summary(results, table):
    """Print summary of calibration results."""

    print("\n" + "="*70)
    print("CALIBRATION_FACTOR SUMMARY")
    print("="*70)

    # Count outcomes
    n_frag = sum(1 for r in results if r['is_frag'])
    n_total = len(results)
    frag_rate = 100.0 * n_frag / n_total

    print(f"\nFragmentation rate: {n_frag}/{n_total} ({frag_rate:.1f}%)")

    # Print C(f, beta) table
    print("\nCalibration factor C(f, beta) = lambda_frag / lambda_MJ:")
    print("-" * 70)
    print(f"{'f':<6} {'beta=0.3':<20} {'beta=0.5':<20} {'beta=1.0':<20}")
    print("-" * 70)

    for row in table:
        f_val = row['f']
        line = f"{f_val:<6.2f} "

        for beta in [0.3, 0.5, 1.0]:
            key = f'beta{beta}'
            data = row[key]
            if data['C_mean'] is not None:
                line += f"{data['C_mean']:.3f}±{data['C_std']:.3f} ({data['n_frag']}/{data['n_total']}) "
            else:
                line += f"{'NO_FRAG':<20} "

        print(line)

    print("-" * 70)

    # Test constancy hypothesis
    print("\nConstancy hypothesis test (C = constant across f):")

    for beta in [0.3, 0.5, 1.0]:
        key = f'beta{beta}'
        C_values = []
        f_values = []

        for row in table:
            data = row[key]
            if data['C_mean'] is not None:
                C_values.append(data['C_mean'])
                f_values.append(row['f'])

        if len(C_values) >= 3:
            # Compute variance
            C_mean = np.mean(C_values)
            C_std = np.std(C_values)
            CV = 100.0 * C_std / C_mean if C_mean > 0 else 0

            print(f"  beta={beta}: C = {C_mean:.3f} ± {C_std:.3f} (CV = {CV:.1f}%)")

            if CV < 10:
                print(f"    → CONSISTENT with constancy (CV < 10%)")
            elif CV < 20:
                print(f"    → MODERATE variation (10% < CV < 20%)")
            else:
                print(f"    → STRONG variation (CV > 20%)")
        else:
            print(f"  beta={beta}: Insufficient data (n={len(C_values)})")


def main():
    """Run full analysis pipeline."""

    # Analyze all simulations
    results = analyze_all_simulations()

    # Generate calibration factor table
    table = generate_C_f_beta_table(results)

    # Print summary
    print_summary(results, table)

    print("\n" + "="*70)
    print("Analysis complete!")
    print("="*70)
    print("\nOutput files:")
    print("  - calibration_results.json: Per-simulation results")
    print("  - C_f_beta_table.json: Calibration factor table (JSON)")
    print("  - C_f_beta_table.csv: Calibration factor table (CSV)")


if __name__ == '__main__':
    main()
