#!/usr/bin/env python3
"""
Analyze STV (Supercritical Transition Validation) campaign results.

This script processes simulation outputs to:
1. Extract λ/W measurements at f ≥ 1.5
2. Compute statistical uncertainties from multiple seeds
3. Test the extrapolation from near-critical calibration
4. Fit λ/W(f) relationships
"""

import json
import glob
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from pathlib import Path
from scipy import stats
from scipy.optimize import curve_fit

from analysis_utils.extract_beading import extract_beading_pattern


OUTPUTS_DIR = Path("outputs/STV")
RESULTS_DIR = Path("results")
RESULTS_DIR.mkdir(exist_ok=True)


def load_simulation_results():
    """Load all STV simulation results."""
    results = []

    for sim_dir in OUTPUTS_DIR.glob("STV_*/"):
        # Load status file
        status_file = sim_dir / "status.json"
        if not status_file.exists():
            continue

        with open(status_file) as f:
            status = json.load(f)

        # Load metadata
        metadata = status.get('metadata', {})

        # Extract λ/W from final snapshot if available
        snapshot_files = list(sim_dir.glob("*final*.h5"))
        if snapshot_files:
            try:
                beading = extract_beading_pattern(
                    snapshot_files[0],
                    Lx_lambdaJ=metadata.get('Lx_lambdaJ', 24.0)
                )
                lambda_W = beading.get('lambda_measured') / beading.get('W', 1.0)
                status['lambda_W'] = lambda_W
                status['n_peaks'] = beading.get('n_peaks', 0)
            except Exception as e:
                status['lambda_W'] = None
                status['error'] = str(e)

        results.append({
            'sim_id': sim_dir.name,
            'f': metadata.get('f'),
            'beta': metadata.get('beta'),
            'theta': metadata.get('theta'),
            'seed': metadata.get('seed'),
            'Lx': metadata.get('Lx_lambdaJ'),
            'classification': status.get('classification'),
            'lambda_W': status.get('lambda_W'),
            'n_peaks': status.get('n_peaks', 0),
            'wall_time': status.get('wall_time_seconds')
        })

    return pd.DataFrame(results)


def compute_statistics_by_parameter(df):
    """Compute mean and uncertainty for each (f, β) parameter point."""
    stats = []

    for f in df['f'].unique():
        for beta in df['beta'].unique():
            subset = df[(df['f'] == f) & (df['beta'] == beta)]
            valid = subset[subset['lambda_W'].notna()]

            if len(valid) > 0:
                stats.append({
                    'f': f,
                    'beta': beta,
                    'n': len(valid),
                    'lambda_W_mean': valid['lambda_W'].mean(),
                    'lambda_W_std': valid['lambda_W'].std(),
                    'lambda_W_sem': valid['lambda_W'].std() / np.sqrt(len(valid)),
                    'lambda_W_values': valid['lambda_W'].tolist()
                })

    return pd.DataFrame(stats)


def test_extrapolation(stats_df):
    """Test whether near-critical calibration extrapolation is valid."""
    # Near-critical reference (from existing campaigns)
    near_critical_ref = {
        'f_range': (1.0, 1.2),
        'lambda_W_mean': 1.11,
        'lambda_W_std': 0.12
    }

    results = {
        'extrapolation_valid': True,
        'chi_squared': None,
        'p_value': None,
        'conclusion': ''
    }

    # Compute expected values using extrapolation
    # For each (f, β), compare measured vs. extrapolated
    comparisons = []
    for _, row in stats_df.iterrows():
        f = row['f']
        measured = row['lambda_W_mean']
        uncertainty = row['lambda_W_sem']

        # Simple linear extrapolation from near-critical
        # Assuming λ/W scales roughly linearly with f in this range
        f_ref = 1.1  # Midpoint of near-critical range
        extrapolated = near_critical_ref['lambda_W_mean'] * (f / f_ref)

        # Compute χ² contribution
        residual = (measured - extrapolated) / np.sqrt(uncertainty**2 + near_critical_ref['lambda_W_std']**2)
        comparisons.append({
            'f': f,
            'measured': measured,
            'extrapolated': extrapolated,
            'residual': residual
        })

    # Overall χ² test
    chi2 = sum(c['residual']**2 for c in comparisons)
    dof = len(comparisons) - 1
    p_value = 1 - stats.chi2.cdf(chi2, dof)

    results['chi_squared'] = chi2
    results['p_value'] = p_value

    # Interpretation
    if p_value < 0.01:
        results['extrapolation_valid'] = False
        results['conclusion'] = f"Extrapolation INVALID: χ² = {chi2:.2f}, p = {p_value:.4f} < 0.01"
    elif p_value < 0.05:
        results['conclusion'] = f"Extrapolation MARGINAL: χ² = {chi2:.2f}, p = {p_value:.4f}"
    else:
        results['conclusion'] = f"Extrapolation VALID: χ² = {chi2:.2f}, p = {p_value:.4f} > 0.05"

    return results, comparisons


def fit_lambda_W_models(stats_df):
    """Fit various models to λ/W(f) relationship."""
    fits = {}

    # Power law: λ/W = A * f^α
    def power_law(f, A, alpha):
        return A * f**alpha

    # Exponential: λ/W = A * exp(B * f)
    def exponential(f, A, B):
        return A * np.exp(B * f)

    # Linear: λ/W = A + B * f
    def linear(f, A, B):
        return A + B * f

    f_data = stats_df['f'].values
    y_data = stats_df['lambda_W_mean'].values
    y_err = stats_df['lambda_W_sem'].values

    # Power law fit
    try:
        popt_power, pcov_power = curve_fit(power_law, f_data, y_data, sigma=y_err, absolute_sigma=True)
        fits['power_law'] = {
            'A': popt_power[0],
            'alpha': popt_power[1],
            'A_err': np.sqrt(pcov_power[0, 0]),
            'alpha_err': np.sqrt(pcov_power[1, 1]),
            'chi2': np.sum(((y_data - power_law(f_data, *popt_power)) / y_err)**2)
        }
    except:
        fits['power_law'] = None

    # Exponential fit
    try:
        popt_exp, pcov_exp = curve_fit(exponential, f_data, y_data, sigma=y_err, absolute_sigma=True)
        fits['exponential'] = {
            'A': popt_exp[0],
            'B': popt_exp[1],
            'A_err': np.sqrt(pcov_exp[0, 0]),
            'B_err': np.sqrt(pcov_exp[1, 1]),
            'chi2': np.sum(((y_data - exponential(f_data, *popt_exp)) / y_err)**2)
        }
    except:
        fits['exponential'] = None

    # Linear fit
    try:
        popt_lin, pcov_lin = curve_fit(linear, f_data, y_data, sigma=y_err, absolute_sigma=True)
        fits['linear'] = {
            'A': popt_lin[0],
            'B': popt_lin[1],
            'A_err': np.sqrt(pcov_lin[0, 0]),
            'B_err': np.sqrt(pcov_lin[1, 1]),
            'chi2': np.sum(((y_data - linear(f_data, *popt_lin)) / y_err)**2)
        }
    except:
        fits['linear'] = None

    return fits


def create_figures(df, stats_df, extrapolation_result, comparisons, fits):
    """Create analysis figures."""
    # Figure 1: λ/W vs f for all β values
    fig1, ax1 = plt.subplots(figsize=(10, 6))

    for beta in sorted(stats_df['beta'].unique()):
        subset = stats_df[stats_df['beta'] == beta]
        ax1.errorbar(subset['f'], subset['lambda_W_mean'],
                    yerr=subset['lambda_W_sem'],
                    fmt='o-', label=f'β = {beta}',
                    capsize=5, markersize=8)

    ax1.set_xlabel('Line mass ratio f', fontsize=14)
    ax1.set_ylabel('λ/W', fontsize=14)
    ax1.set_title('Fragmentation Wavelength vs Line Mass (STV Campaign)', fontsize=16)
    ax1.legend(fontsize=12)
    ax1.grid(True, alpha=0.3)
    ax1.set_xlim(1.4, 3.1)

    fig1.tight_layout()
    fig1.savefig(RESULTS_DIR / 'lambda_vs_f.pdf', dpi=300)
    print(f"✓ Saved: lambda_vs_f.pdf")

    # Figure 2: Extrapolation test
    fig2, ax2 = plt.subplots(figsize=(10, 6))

    f_vals = [c['f'] for c in comparisons]
    measured = [c['measured'] for c in comparisons]
    extrapolated = [c['extrapolated'] for c in comparisons]

    ax2.plot(f_vals, measured, 'bo-', label='Measured (STV)', markersize=10)
    ax2.plot(f_vals, extrapolated, 'r--', label='Extrapolated from near-critical', linewidth=2)
    ax2.fill_between(f_vals,
                     np.array(measured) - np.array([c.get('uncertainty', 0.2) for c in comparisons]),
                     np.array(measured) + np.array([c.get('uncertainty', 0.2) for c in comparisons]),
                     alpha=0.2, color='blue')

    ax2.set_xlabel('Line mass ratio f', fontsize=14)
    ax2.set_ylabel('λ/W', fontsize=14)
    ax2.set_title(f'Calibration Extrapolation Test: {extrapolation_result["conclusion"]}', fontsize=16)
    ax2.legend(fontsize=12)
    ax2.grid(True, alpha=0.3)

    fig2.tight_layout()
    fig2.savefig(RESULTS_DIR / 'extrapolation_test.pdf', dpi=300)
    print(f"✓ Saved: extrapolation_test.pdf")

    # Figure 3: Model fits
    fig3, ax3 = plt.subplots(figsize=(10, 6))

    # Plot data
    for beta in sorted(stats_df['beta'].unique()):
        subset = stats_df[stats_df['beta'] == beta]
        ax3.errorbar(subset['f'], subset['lambda_W_mean'],
                    yerr=subset['lambda_W_sem'],
                    fmt='o', label=f'β = {beta} data',
                    capsize=5, markersize=6, alpha=0.7)

    # Plot best-fit models
    f_fine = np.linspace(1.4, 3.2, 100)
    if fits['power_law']:
        power_fit = power_law(f_fine, fits['power_law']['A'], fits['power_law']['alpha'])
        ax3.plot(f_fine, power_fit, 'b-', linewidth=2, label=f'Power law (χ²={fits["power_law"]["chi2"]:.1f})')
    if fits['exponential']:
        exp_fit = exponential(f_fine, fits['exponential']['A'], fits['exponential']['B'])
        ax3.plot(f_fine, exp_fit, 'g-', linewidth=2, label=f'Exponential (χ²={fits["exponential"]["chi2"]:.1f})')
    if fits['linear']:
        lin_fit = linear(f_fine, fits['linear']['A'], fits['linear']['B'])
        ax3.plot(f_fine, lin_fit, 'r-', linewidth=2, label=f'Linear (χ²={fits["linear"]["chi2"]:.1f})')

    ax3.set_xlabel('Line mass ratio f', fontsize=14)
    ax3.set_ylabel('λ/W', fontsize=14)
    ax3.set_title('λ/W(f) Model Fits', fontsize=16)
    ax3.legend(fontsize=10)
    ax3.grid(True, alpha=0.3)

    fig3.tight_layout()
    fig3.savefig(RESULTS_DIR / 'model_fits.pdf', dpi=300)
    print(f"✓ Saved: model_fits.pdf")


def write_summary_report(df, stats_df, extrapolation_result, fits):
    """Write comprehensive summary report."""
    report = []
    report.append("# STV Campaign Analysis Summary")
    report.append(f"\nGenerated: {pd.Timestamp.now().isoformat()}")
    report.append("\n## Overview")
    report.append(f"\nTotal simulations analyzed: {len(df)}")
    report.append(f"Successful λ/W extractions: {df['lambda_W'].notna().sum()}")
    report.append(f"Parameter points: {len(stats_df)}")

    report.append("\n## Extrapolation Test")
    report.append(f"\n{extrapolation_result['conclusion']}")
    report.append(f"χ² = {extrapolation_result['chi_squared']:.2f}")
    report.append(f"p = {extrapolation_result['p_value']:.4f}")

    if extrapolation_result['extrapolation_valid']:
        report.append("\n**Conclusion**: The λ_frag = 1.11 λ_MJ calibration extrapolation is VALIDATED by direct measurements at f ≥ 1.5.")
    else:
        report.append("\n**Conclusion**: The λ_frag = 1.11 λ_MJ calibration extrapolation is NOT supported by direct measurements. A revised calibration is needed.")

    report.append("\n## Model Fits")
    if fits['power_law']:
        report.append(f"\nPower law: λ/W = {fits['power_law']['A']:.2f} × f^{fits['power_law']['alpha']:.2f}")
        report.append(f"  χ² = {fits['power_law']['chi2']:.1f}")
    if fits['exponential']:
        report.append(f"\nExponential: λ/W = {fits['exponential']['A']:.2f} × exp({fits['exponential']['B']:.2f} × f)")
        report.append(f"  χ² = {fits['exponential']['chi2']:.1f}")
    if fits['linear']:
        report.append(f"\nLinear: λ/W = {fits['linear']['A']:.2f} + {fits['linear']['B']:.2f} × f")
        report.append(f"  χ² = {fits['linear']['chi2']:.1f}")

    report.append("\n## Recommendations")
    if extrapolation_result['extrapolation_valid']:
        report.append("\n1. The near-critical calibration extrapolation is validated")
        report.append("2. Paper can cite λ_frag = 1.11 λ_MJ as applicable to supercritical regime")
    else:
        report.append("\n1. A revised calibration factor is needed for f ≥ 1.5")
        report.append("2. Recommend using direct measurements from this campaign")
        report.append("3. Paper should be revised with new calibration")

    report_text = '\n'.join(report)

    with open(RESULTS_DIR / 'STV_SUMMARY.md', 'w') as f:
        f.write(report_text)

    print(report_text)
    print(f"\n✓ Saved: STV_SUMMARY.md")


def main():
    """Main analysis function."""
    print("=" * 60)
    print("STV Campaign Analysis")
    print("=" * 60)
    print()

    # Load results
    print("Loading simulation results...")
    df = load_simulation_results()
    print(f"Loaded {len(df)} simulation results")
    print()

    # Compute statistics
    print("Computing statistics by parameter point...")
    stats_df = compute_statistics_by_parameter(df)
    print(f"Found {len(stats_df)} parameter points")
    print()

    # Print statistics table
    print("λ/W measurements:")
    print(stats_df[['f', 'beta', 'n', 'lambda_W_mean', 'lambda_W_sem']].to_string(index=False))
    print()

    # Test extrapolation
    print("Testing calibration extrapolation...")
    extrapolation_result, comparisons = test_extrapolation(stats_df)
    print(extrapolation_result['conclusion'])
    print()

    # Fit models
    print("Fitting λ/W(f) models...")
    fits = fit_lambda_W_models(stats_df)
    print()

    # Create figures
    print("Creating figures...")
    create_figures(df, stats_df, extrapolation_result, comparisons, fits)
    print()

    # Write summary
    print("Writing summary report...")
    write_summary_report(df, stats_df, extrapolation_result, fits)
    print()

    # Save data tables
    stats_df.to_csv(RESULTS_DIR / 'lambda_measurements.csv', index=False)
    print(f"✓ Saved: lambda_measurements.csv")

    print()
    print("=" * 60)
    print("Analysis complete!")
    print(f"Results saved to: {RESULTS_DIR}/")
    print("=" * 60)


if __name__ == '__main__':
    main()
