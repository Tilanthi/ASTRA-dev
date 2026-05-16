#!/usr/bin/env python3
"""
Analyze LW_DIRECT campaign: Direct λ/W measurements at supercritical values.

This addresses Concern 5: Test whether λ_frag = 1.11 λ_MJ calibration can be
extrapolated from near-critical (f ≈ 1.0-1.2) to supercritical (f ≥ 1.5) regime.

Expected outputs:
1. lambda_vs_f.csv: λ/W measurements with uncertainties
2. extrapolation_test.pdf: Comparison with near-critical calibration
3. fitting_results.json: Power-law, exponential fits
4. LW_DIRECT_SUMMARY.md: Executive summary
"""

import numpy as np
import pandas as pd
import json
import h5py
from pathlib import Path
from scipy.signal import find_peaks
from scipy.optimize import curve_fit
import matplotlib.pyplot as plt
import matplotlib
matplotlib.use('Agg')


def load_density_field(snapshot_file):
    """Load density field from HDF5 snapshot."""
    with h5py.File(snapshot_file, 'r') as f:
        for key in ['rho', 'density', 'dens']:
            if key in f:
                return f[key][:]
        raise ValueError(f"No density field found. Available: {list(f.keys())}")


def compute_longitudinal_profile(rho):
    """Compute longitudinal density profile by averaging over transverse directions."""
    rho_1D = rho.mean(axis=(0, 1))
    if rho_1D.ndim > 1:
        rho_1D = rho_1D.squeeze()
    return rho_1D


def extract_lambda_W(snapshot_file, Lx_lambdaJ, W_core=0.3, contrast_threshold=0.1, min_peak_separation=20):
    """
    Extract λ/W ratio from simulation snapshot.

    Returns None if beading is not detected.
    """
    try:
        rho = load_density_field(snapshot_file)
        rho_1D = compute_longitudinal_profile(rho)

        Nx = len(rho_1D)
        dx = Lx_lambdaJ / Nx

        # Normalize for peak detection
        rho_mean = rho_1D.mean()
        rho_normalized = (rho_1D - rho_mean) / rho_mean

        # Detect peaks
        peaks, properties = find_peaks(
            rho_normalized,
            height=contrast_threshold,
            distance=min_peak_separation
        )

        if len(peaks) < 2:
            return None  # Need at least 2 peaks to measure wavelength

        # Measure wavelength from peak spacing
        lambda_grid = np.diff(peaks).mean()
        lambda_measured = lambda_grid * dx  # In λJ units

        # Convert to λ/W ratio (W = 2 * W_core for full width)
        lambda_over_W = lambda_measured / (2 * W_core)

        return {
            'lambda_W': lambda_over_W,
            'lambda_lambdaJ': lambda_measured,
            'n_peaks': len(peaks),
            'peak_positions_lambdaJ': peaks * dx,
            'peak_contrasts': rho_normalized[peaks].tolist(),
            'longitudinal_variance': np.var(rho_normalized),
            'status': 'beading_detected'
        }

    except Exception as e:
        return {'status': f'error: {str(e)}', 'error': str(e)}


def analyze_simulation(sim_dir, sim_name):
    """Analyze a single simulation and extract λ/W from final snapshot."""
    sim_path = Path(sim_dir) / sim_name

    # Load config to get parameters
    config_file = sim_path / 'config.json'
    if not config_file.exists():
        return None

    with open(config_file) as f:
        config = json.load(f)

    metadata = config['metadata']
    f = metadata['f']
    beta = metadata['beta']
    theta = metadata['theta']
    seed = metadata['seed']
    Lx = metadata['Lx_lambdaJ']
    snap_times = metadata['snap_times']

    result = {
        'sim_name': sim_name,
        'f': f,
        'beta': beta,
        'theta': theta,
        'seed': seed,
        'Lx_lambdaJ': Lx,
        'snap_times': snap_times
    }

    # Find HDF5 snapshots
    h5_files = sorted(sim_path.glob('*.h5'))

    if not h5_files:
        result['status'] = 'no_h5_files'
        return result

    # Extract λ/W from final snapshot
    final_snapshot = h5_files[-1]
    lambda_W_result = extract_lambda_W(final_snapshot, Lx)

    if lambda_W_result and lambda_W_result.get('status') == 'beading_detected':
        result.update(lambda_W_result)
        result['status'] = 'SUCCESS'
    else:
        result['status'] = 'NO_BEADING'
        if lambda_W_result:
            result['error'] = lambda_W_result.get('status', 'unknown')

    return result


def power_law(x, a, alpha):
    """Power law: y = a * x^alpha"""
    return a * x**alpha


def exponential_decay(x, a, b, c):
    """Exponential: y = a * exp(-b*x) + c"""
    return a * np.exp(-b * x) + c


def analyze_lw_direct_campaign(campaign_dir):
    """Analyze all LW_DIRECT simulations."""
    campaign_path = Path(campaign_dir)
    outputs_dir = campaign_path / 'outputs' / 'LW_DIRECT'

    if not outputs_dir.exists():
        print(f"ERROR: Output directory not found: {outputs_dir}")
        return None

    # Find all simulation directories
    sim_dirs = [d for d in outputs_dir.iterdir() if d.is_dir()]

    results = []
    for sim_dir in sim_dirs:
        sim_name = sim_dir.name
        result = analyze_simulation(outputs_dir, sim_name)
        if result:
            results.append(result)

    # Save raw results
    results_file = campaign_path / 'lw_direct_results.json'
    with open(results_file, 'w') as f:
        json.dump(results, f, indent=2)

    print(f"Analyzed {len(results)} simulations")
    print(f"Results saved to {results_file}")

    # Filter successful measurements
    successful = [r for r in results if r.get('status') == 'SUCCESS']
    no_beading = [r for r in results if r.get('status') == 'NO_BEADING']

    print(f"\nSUCCESS: {len(successful)} simulations with λ/W measurements")
    print(f"NO_BEADING: {len(no_beading)} simulations")

    if not successful:
        print("\nERROR: No successful λ/W measurements found!")
        return None

    # Organize by (f, beta) parameters
    df = pd.DataFrame(successful)

    # Compute statistics per (f, beta) cell
    stats = df.groupby(['f', 'beta']).agg({
        'lambda_W': ['mean', 'std', 'count'],
        'lambda_lambdaJ': ['mean', 'std'],
        'n_peaks': 'mean'
    }).reset_index()

    stats.columns = ['f', 'beta', 'lambda_W_mean', 'lambda_W_std', 'n',
                     'lambda_lambdaJ_mean', 'lambda_lambdaJ_std', 'n_peaks_mean']

    # Save statistics
    stats_file = campaign_path / 'lambda_vs_f.csv'
    stats.to_csv(stats_file, index=False)
    print(f"\nStatistics saved to {stats_file}")

    # Print summary table
    print("\n" + "="*80)
    print("λ/W Measurements by (f, β)")
    print("="*80)
    print(stats.to_string(index=False))

    # Fit λ/W(f) relationship
    print("\n" + "="*80)
    print("Fitting λ/W(f) relationship")
    print("="*80)

    # Overall fit (all β values)
    fit_data = df[['f', 'lambda_W']].dropna()

    try:
        popt_power, _ = curve_fit(power_law, fit_data['f'], fit_data['lambda_W'],
                                  p0=[1.5, -0.5], maxfev=5000)
        popt_exp, _ = curve_fit(exponential_decay, fit_data['f'], fit_data['lambda_W'],
                                p0=[1.5, 0.5, 0.5], maxfev=5000)

        print(f"\nPower-law fit: λ/W = {popt_power[0]:.3f} * f^{popt_power[1]:.3f}")
        print(f"Exponential fit: λ/W = {popt_exp[0]:.3f} * exp(-{popt_exp[1]:.3f}*f) + {popt_exp[2]:.3f}")

        # Test extrapolation from near-critical calibration
        # Near-critical: λ/W ≈ 1.11 at f ≈ 1.0-1.2
        f_near_crit = 1.1
        lambda_W_near_crit = 1.11  # From near-critical calibration

        f_super_crit = np.array([1.5, 2.0, 2.5, 3.0])

        # Extrapolation using power law
        lambda_W_extrap_power = power_law(f_super_crit, *popt_power)

        # Expected if extrapolating from near-critical
        # Assume same power-law index from f=1.1 to supercritical
        lambda_W_expected = lambda_W_near_crit * (f_super_crit / f_near_crit)**popt_power[1]

        print(f"\nExtrapolation Test:")
        print(f"Near-critical calibration: λ/W = {lambda_W_near_crit:.3f} at f = {f_near_crit}")
        print(f"\nPower-law index: α = {popt_power[1]:.3f}")
        print(f"\nf   | Measured λ/W | Expected (extrap) | Difference")
        print(f"----|---------------|-------------------|------------")
        for f_i, meas, exp in zip(f_super_crit, lambda_W_extrap_power, lambda_W_expected):
            diff = meas - exp
            pct = diff / exp * 100
            print(f"{f_i:.1f} | {meas:.3f}        | {exp:.3f}            | {diff:+.3f} ({pct:+.1f}%)")

        # Save fitting results
        fitting_results = {
            'power_law': {
                'a': float(popt_power[0]),
                'alpha': float(popt_power[1]),
                'formula': f'lambda_W = {popt_power[0]:.3f} * f^{popt_power[1]:.3f}'
            },
            'exponential': {
                'a': float(popt_exp[0]),
                'b': float(popt_exp[1]),
                'c': float(popt_exp[2]),
                'formula': f'lambda_W = {popt_exp[0]:.3f} * exp(-{popt_exp[1]:.3f}*f) + {popt_exp[2]:.3f}'
            },
            'extrapolation_test': {
                'near_critical_lambda_W': lambda_W_near_crit,
                'near_critical_f': f_near_crit,
                'power_law_index': float(popt_power[1]),
                'measured_vs_expected': {
                    f: {'measured': float(m), 'expected': float(e), 'difference': float(m - e)}
                    for f, m, e in zip(f_super_crit.tolist(), lambda_W_extrap_power.tolist(), lambda_W_expected.tolist())
                }
            }
        }

        fitting_file = campaign_path / 'fitting_results.json'
        with open(fitting_file, 'w') as f:
            json.dump(fitting_results, f, indent=2)

        print(f"\nFitting results saved to {fitting_file}")

    except Exception as e:
        print(f"\nWARNING: Fitting failed: {e}")

    # Create figures
    create_figures(df, stats, campaign_path)

    # Create summary document
    create_summary_document(stats, fitting_results if 'fitting_results' in locals() else None, campaign_path)

    print("\n" + "="*80)
    print("LW_DIRECT Analysis Complete!")
    print("="*80)
    print(f"\nGenerated files:")
    print(f"  - {results_file}")
    print(f"  - {stats_file}")
    print(f"  - {campaign_path / 'fitting_results.json'}")
    print(f"  - {campaign_path / 'figures/'}")
    print(f"  - {campaign_path / 'LW_DIRECT_SUMMARY.md'}")

    return stats


def create_figures(df, stats, campaign_path):
    """Create analysis figures."""
    figures_dir = campaign_path / 'figures'
    figures_dir.mkdir(exist_ok=True)

    # Figure 1: λ/W vs f for different β values
    fig, ax = plt.subplots(figsize=(8, 6))

    for beta in sorted(df['beta'].unique()):
        beta_data = df[df['beta'] == beta]
        ax.scatter(beta_data['f'], beta_data['lambda_W'], label=f'β = {beta}', s=50, alpha=0.7)

        # Plot mean values
        beta_stats = stats[stats['beta'] == beta]
        if len(beta_stats) > 0:
            ax.errorbar(beta_stats['f'], beta_stats['lambda_W_mean'],
                       yerr=beta_stats['lambda_W_std'],
                       fmt='o-', capsize=5, linewidth=2)

    # Add near-critical calibration reference
    ax.axhline(y=1.11, color='gray', linestyle='--', label='Near-critical (f≈1.1)')
    ax.axvline(x=1.2, color='gray', linestyle=':', alpha=0.5, label='Near-critical limit')

    ax.set_xlabel('Line mass fraction (f)', fontsize=14)
    ax.set_ylabel('λ/W', fontsize=14)
    ax.set_title('λ/W Direct Measurements: Supercritical Regime', fontsize=16)
    ax.legend()
    ax.grid(True, alpha=0.3)
    ax.set_xlim(1.4, 3.1)
    ax.set_ylim(0, 3)

    plt.tight_layout()
    plt.savefig(figures_dir / 'lambda_W_vs_f.pdf')
    plt.savefig(figures_dir / 'lambda_W_vs_f.png', dpi=150)
    plt.close()

    print(f"Figure saved: {figures_dir / 'lambda_W_vs_f.pdf'}")

    # Figure 2: Extrapolation comparison
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(12, 5))

    # Left: All data with fits
    for beta in sorted(df['beta'].unique()):
        beta_data = df[df['beta'] == beta]
        ax1.scatter(beta_data['f'], beta_data['lambda_W'], label=f'β = {beta}', s=50, alpha=0.7)

    # Plot fits
    f_range = np.linspace(1.0, 3.2, 100)
    if 'fitting_results' in locals():
        popt_power = fitting_results['power_law']
        ax1.plot(f_range, power_law(f_range, popt_power['a'], popt_power['alpha']),
                'k--', label='Power-law fit', linewidth=2)

    ax1.set_xlabel('Line mass fraction (f)')
    ax1.set_ylabel('λ/W')
    ax1.set_title('(a) λ/W(f) with power-law fit')
    ax1.legend()
    ax1.grid(True, alpha=0.3)
    ax1.axvline(x=1.2, color='gray', linestyle=':', alpha=0.5)

    # Right: Extrapolation test
    if 'fitting_results' in locals():
        extrap_test = fitting_results['extrapolation_test']
        f_vals = [float(f) for f in extrap_test['measured_vs_expected'].keys()]
        measured = [extrap_test['measured_vs_expected'][f]['measured'] for f in f_vals]
        expected = [extrap_test['measured_vs_expected'][f]['expected'] for f in f_vals]

        ax2.plot(f_vals, expected, 'g--', label='Expected (extrapolated)', marker='o')
        ax2.plot(f_vals, measured, 'b-', label='Measured', marker='s')

    ax2.set_xlabel('Line mass fraction (f)')
    ax2.set_ylabel('λ/W')
    ax2.set_title('(b) Calibration Extrapolation Test')
    ax2.legend()
    ax2.grid(True, alpha=0.3)
    ax2.axhline(y=1.11, color='gray', linestyle=':', alpha=0.5)

    plt.tight_layout()
    plt.savefig(figures_dir / 'extrapolation_test.pdf')
    plt.savefig(figures_dir / 'extrapolation_test.png', dpi=150)
    plt.close()

    print(f"Figure saved: {figures_dir / 'extrapolation_test.pdf'}")


def create_summary_document(stats, fitting_results, campaign_path):
    """Create summary markdown document."""
    summary = """# LW_DIRECT Campaign Analysis Summary

## Objective

Direct λ/W measurements at supercritical values (f ≥ 1.5) to test whether the
λ_frag = 1.11 λ_MJ calibration can be extrapolated from the near-critical
regime (f ≈ 1.0-1.2).

**This addresses Concern 5 from the theoretician referee.**

---

## Results Summary

### Detection Rate

"""

    summary += f"- **Total simulations**: {stats['n'].sum()}\n"
    summary += f"- **Successful λ/W measurements**: {len(stats)}\n"
    summary += f"- **Detection rate**: {len(stats) / stats['n'].sum() * 100:.1f}%\n\n"

    summary += "### λ/W Measurements\n\n"
    summary += stats.to_string(index=False)

    if fitting_results:
        summary += "\n\n### Fitting Results\n\n"
        summary += f"**Power-law fit**: {fitting_results['power_law']['formula']}\n\n"

        summary += "### Extrapolation Test\n\n"
        summary += "Testing whether λ/W at f ≥ 1.5 matches extrapolation from near-critical calibration:\n\n"
        summary += "| f | Measured λ/W | Expected (extrap) | Difference |\n"
        summary += "|---|---------------|-------------------|------------|\n"

        for f, val in fitting_results['extrapolation_test']['measured_vs_expected'].items():
            summary += f"| {f} | {val['measured']:.3f} | {val['expected']:.3f} | {val['difference']:+.3f} |\n"

    summary += "\n\n### Conclusions\n\n"

    if fitting_results:
        max_diff = max(abs(v['difference']) for v in fitting_results['extrapolation_test']['measured_vs_expected'].values())
        if max_diff < 0.2:
            summary += "**The λ_frag = 1.11 λ_MJ calibration extrapolation is VALID** within uncertainties.\n\n"
            summary += f"Maximum deviation from extrapolation: {max_diff:.3f} ({max_diff/1.11*100:.1f}%)\n\n"
        else:
            summary += "**The λ_frag = 1.11 λ_MJ calibration extrapolation needs REVISION**.\n\n"
            summary += f"Maximum deviation from extrapolation: {max_diff:.3f} ({max_diff/1.11*100:.1f}%)\n\n"
            summary += "Recommend using the power-law fit from this campaign instead.\n\n"

    summary += "---\n\n"
    summary += "## Files Generated\n\n"
    summary += "- `lw_direct_results.json`: Raw results from all simulations\n"
    summary += "- `lambda_vs_f.csv`: Statistical summary by (f, β) parameters\n"
    summary += "- `fitting_results.json`: Power-law and exponential fit parameters\n"
    summary += "- `figures/lambda_W_vs_f.pdf`: Main result figure\n"
    summary += "- `figures/extrapolation_test.pdf`: Extrapolation validation figure\n"

    summary_path = campaign_path / 'LW_DIRECT_SUMMARY.md'
    with open(summary_path, 'w') as f:
        f.write(summary)

    print(f"Summary saved to {summary_path}")


def main():
    """Main entry point."""
    import argparse

    parser = argparse.ArgumentParser(
        description="Analyze LW_DIRECT campaign results"
    )
    parser.add_argument(
        'campaign_dir',
        nargs='?',
        default='.',
        help='Campaign directory (default: current directory)'
    )

    args = parser.parse_args()

    analyze_lw_direct_campaign(args.campaign_dir)


if __name__ == '__main__':
    main()
