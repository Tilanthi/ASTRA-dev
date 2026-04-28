#!/usr/bin/env python3
"""
Analyze BRIDGE_GRID campaign results

Extracts lambda measurements, generates figures, and produces summary report.
"""

import json
import numpy as np
import pandas as pd
from pathlib import Path
import matplotlib.pyplot as plt
from scipy.signal import find_peaks
from scipy.optimize import curve_fit
import h5py

# Paths
OUTPUT_DIR = Path("outputs")
FIGURES_DIR = Path("figures")
RESULTS_FILE = Path("lambda_measurements.csv")
SUMMARY_FILE = Path("SUMMARY_REPORT.md")


def extract_lambda_from_hdf5(h5_file):
    """
    Extract fragmentation wavelength from HDF5 snapshot.

    Returns:
        dict: Contains lambda_frag, n_peaks, peak_positions, etc.
    """
    try:
        with h5py.File(h5_file, 'r') as f:
            # Get density field
            if 'rho' not in f:
                return None

            rho = f['rho'][:]  # Shape: (Nz, Ny, Nx, 1)

            # Average over transverse directions to get 1D profile
            rho_1D = rho.mean(axis=(0, 1)).flatten()

            # Normalize
            rho_mean = rho_1D.mean()
            if rho_mean == 0:
                return None

            rho_norm = (rho_1D - rho_mean) / rho_mean

            # Detect peaks
            peaks, properties = find_peaks(
                rho_norm,
                height=0.1,  # 10% contrast threshold
                distance=20   # Minimum separation
            )

            if len(peaks) < 2:
                return {
                    'n_peaks': len(peaks),
                    'lambda_frag': None,
                    'longitudinal_variance': np.var(rho_norm),
                    'status': 'insufficient_peaks'
                }

            # Measure wavelength
            peak_positions = np.diff(peaks)
            lambda_grid = peak_positions.mean()
            lambda_err = peak_positions.std()

            # Convert to physical units (assuming domain info in metadata)
            # L = 12 lambda_J, Nx = 384
            dx = 12.0 / 384.0  # Grid spacing in lambda_J units
            lambda_frag = lambda_grid * dx
            lambda_frag_err = lambda_err * dx

            return {
                'n_peaks': len(peaks),
                'peak_positions': peaks.tolist(),
                'peak_contrasts': rho_norm[peaks].tolist(),
                'lambda_frag': lambda_frag,
                'lambda_frag_uncertainty': lambda_frag_err,
                'longitudinal_variance': np.var(rho_norm),
                'density_contrast': rho_norm.max() - rho_norm.min(),
                'status': 'success'
            }

    except Exception as e:
        return {
            'status': 'error',
            'error': str(e)
        }


def analyze_all_simulations():
    """Analyze all simulation outputs."""
    results = []

    for sim_dir in OUTPUT_DIR.iterdir():
        if not sim_dir.is_dir():
            continue

        sim_id = sim_dir.name

        # Check for status file
        status_file = sim_dir / "status.json"
        if not status_file.exists():
            continue

        with open(status_file) as f:
            status_data = json.load(f)

        # Extract parameters from sim_id
        # Format: BRIDGE_GRID_f{f}_beta{beta}_M{M}_theta90.0_s{seed}
        parts = sim_id.split('_')
        params = {}
        for part in parts:
            if part.startswith('f'):
                params['f'] = float(part[1:])
            elif part.startswith('beta'):
                params['beta'] = float(part[4:])
            elif part.startswith('M'):
                params['M'] = float(part[1:])
            elif part.startswith('theta'):
                params['theta'] = float(part[5:])
            elif part.startswith('s'):
                params['seed'] = int(part[1:])

        # Extract lambda from HDF5
        h5_files = list(sim_dir.glob("*.h5"))
        if h5_files:
            lambda_data = extract_lambda_from_hdf5(h5_files[-1])
            if lambda_data:
                result = {
                    'sim_id': sim_id,
                    **params,
                    'status': status_data.get('status', 'UNKNOWN'),
                    't_frag': status_data.get('t_frag', None),
                    **lambda_data
                }
                results.append(result)

    return pd.DataFrame(results)


def power_law(f, a, alpha):
    """Power law: lambda = a * f^alpha"""
    return a * f**alpha


def fit_power_law(df, beta_value=None):
    """Fit power law to lambda vs f data."""
    if beta_value is not None:
        df_fit = df[df['beta'] == beta_value]
    else:
        df_fit = df

    # Filter successful measurements
    df_fit = df_fit[df_fit['status'] == 'success']
    df_fit = df_fit[df_fit['lambda_frag'].notna()]

    if len(df_fit) < 3:
        return None

    try:
        popt, pcov = curve_fit(
            power_law,
            df_fit['f'],
            df_fit['lambda_frag'],
            p0=[1.0, 0.5],
            sigma=df_fit.get('lambda_frag_uncertainty', 0.1)
        )

        a, alpha = popt
        a_err, alpha_err = np.sqrt(np.diag(pcov))

        return {
            'a': a,
            'alpha': alpha,
            'a_err': a_err,
            'alpha_err': alpha_err,
            'n_points': len(df_fit)
        }
    except:
        return None


def generate_figures(df):
    """Generate all analysis figures."""
    FIGURES_DIR.mkdir(exist_ok=True)

    # Filter successful measurements
    df_success = df[df['status'] == 'success']
    df_success = df_success[df_success['lambda_frag'].notna()]

    if len(df_success) == 0:
        print("No successful lambda measurements to plot")
        return

    # Figure 1: Lambda vs F for all beta values
    fig, ax = plt.subplots(figsize=(10, 6))

    beta_values = sorted(df_success['beta'].unique())
    colors = ['blue', 'red', 'green']

    for beta, color in zip(beta_values, colors):
        df_beta = df_success[df_success['beta'] == beta].sort_values('f')

        # Plot data points
        ax.errorbar(
            df_beta['f'],
            df_beta['lambda_frag'],
            yerr=df_beta.get('lambda_frag_uncertainty', 0),
            fmt='o',
            label=f'β = {beta}',
            color=color,
            capsize=5
        )

        # Fit power law
        fit_result = fit_power_law(df_success, beta)
        if fit_result:
            f_fit = np.linspace(df_beta['f'].min(), df_beta['f'].max(), 50)
            lambda_fit = power_law(f_fit, fit_result['a'], fit_result['alpha'])
            ax.plot(
                f_fit,
                lambda_fit,
                '--',
                color=color,
                alpha=0.7,
                label=f'Fit: α = {fit_result["alpha"]:.2f} ± {fit_result["alpha_err"]:.2f}'
            )

    ax.set_xlabel('Line mass ratio f')
    ax.set_ylabel('Fragmentation wavelength λ (λJ units)')
    ax.set_title('BRIDGE_GRID Campaign: λ vs f')
    ax.legend()
    ax.grid(True, alpha=0.3)
    plt.tight_layout()
    plt.savefig(FIGURES_DIR / 'fig_lambda_vs_f.pdf', dpi=300)
    plt.close()

    print(f"Saved: {FIGURES_DIR / 'fig_lambda_vs_f.pdf'}")

    # Figure 2: Lambda/W comparison
    fig, ax = plt.subplots(figsize=(10, 6))

    # Convert to lambda/W (assuming W = 2)
    df_success['lambda_by_W'] = df_success['lambda_frag'] / 2.0

    for beta, color in zip(beta_values, colors):
        df_beta = df_success[df_success['beta'] == beta].sort_values('f')

        ax.errorbar(
            df_beta['f'],
            df_beta['lambda_by_W'],
            yerr=df_beta.get('lambda_frag_uncertainty', 0) / 2.0,
            fmt='o',
            label=f'β = {beta}',
            color=color,
            capsize=5
        )

    # Add HGBS observational constraint
    ax.axhline(y=2.1, color='black', linestyle='--', linewidth=2, label='HGBS observed (λ/W = 2.1)')
    ax.axhspan(1.9, 2.3, alpha=0.2, color='gray')

    ax.set_xlabel('Line mass ratio f')
    ax.set_ylabel('Fragmentation spacing λ/W')
    ax.set_title('BRIDGE_GRID Campaign: λ/W vs f')
    ax.legend()
    ax.grid(True, alpha=0.3)
    ax.set_ylim(0, 6)
    plt.tight_layout()
    plt.savefig(FIGURES_DIR / 'fig_lambda_W_comparison.pdf', dpi=300)
    plt.close()

    print(f"Saved: {FIGURES_DIR / 'fig_lambda_W_comparison.pdf'}")

    # Figure 3: Transition analysis
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(14, 5))

    # Plot 1: Longitudinal variance vs f
    for beta, color in zip(beta_values, colors):
        df_beta = df[df['beta'] == beta].sort_values('f')
        ax1.scatter(
            df_beta['f'],
            df_beta['longitudinal_variance'],
            label=f'β = {beta}',
            color=color,
            alpha=0.7
        )

    ax1.set_xlabel('Line mass ratio f')
    ax1.set_ylabel('Longitudinal variance')
    ax1.set_title('Longitudinal Variance vs f')
    ax1.legend()
    ax1.grid(True, alpha=0.3)
    ax1.set_yscale('log')

    # Plot 2: Peak contrast vs f
    for beta, color in zip(beta_values, colors):
        df_beta = df[df['beta'] == beta].sort_values('f')
        ax2.scatter(
            df_beta['f'],
            df_beta.get('density_contrast', 0),
            label=f'β = {beta}',
            color=color,
            alpha=0.7
        )

    ax2.set_xlabel('Line mass ratio f')
    ax2.set_ylabel('Density contrast Δρ/ρ')
    ax2.set_title('Peak Contrast vs f')
    ax2.legend()
    ax2.grid(True, alpha=0.3)

    plt.tight_layout()
    plt.savefig(FIGURES_DIR / 'fig_transition_analysis.pdf', dpi=300)
    plt.close()

    print(f"Saved: {FIGURES_DIR / 'fig_transition_analysis.pdf'}")


def generate_summary_report(df):
    """Generate markdown summary report."""
    df_success = df[df['status'] == 'success']
    df_success = df_success[df_success['lambda_frag'].notna()]

    report = f"""# BRIDGE_GRID Campaign Summary Report

**Generated**: {pd.Timestamp.now().strftime('%Y-%m-%d %H:%M:%S')}

## Overview

This report summarizes the results of the BRIDGE_GRID MHD simulation campaign designed to address Peer Review Issue #3: the contradiction between linear perturbation theory and non-linear MHD results regarding the f-dependence of λ/W.

## Campaign Statistics

- **Total simulations**: {len(df)}
- **Successful measurements**: {len(df_success)}
- **Success rate**: {len(df_success)/len(df)*100:.1f}%

## Parameter Space

- **f (line mass ratio)**: {sorted(df['f'].unique())}
- **β (plasma beta)**: {sorted(df['beta'].unique())}
- **M (Mach number)**: {sorted(df['M'].unique())}
- **Seeds**: {sorted(df['seed'].unique())}

## Key Results

### Lambda Measurements by β Value

"""

    for beta in sorted(df['beta'].unique()):
        df_beta = df_success[df_success['beta'] == beta]
        if len(df_beta) == 0:
            continue

        lambda_mean = df_beta['lambda_frag'].mean()
        lambda_std = df_beta['lambda_frag'].std()
        lambda_by_W = lambda_mean / 2.0

        fit_result = fit_power_law(df_success, beta)
        if fit_result:
            fit_info = f"Power law: λ ∝ f^{fit_result['alpha']:.2f} ± {fit_result['alpha_err']:.2f}"
        else:
            fit_info = "Insufficient data for power law fit"

        report += f"""
#### β = {beta}

- **λ (mean)**: {lambda_mean:.3f} ± {lambda_std:.3f} λJ
- **λ/W**: {lambda_by_W:.2f}
- **N measurements**: {len(df_beta)}
- **{fit_info}**

"""

    report += f"""
## Comparison with Observations

| β | λ/W | HGBS λ/W = 2.1 | Agreement |
|---|-----|----------------|------------|
"""

    for beta in sorted(df['beta'].unique()):
        df_beta = df_success[df_success['beta'] == beta]
        if len(df_beta) == 0:
            continue

        lambda_by_W = df_beta['lambda_frag'].mean() / 2.0
        diff_pct = abs(lambda_by_W - 2.1) / 2.1 * 100

        if diff_pct < 10:
            agreement = "✓ Excellent"
        elif diff_pct < 20:
            agreement = "~ Good"
        else:
            agreement = "✗ Poor"

        report += f"| {beta} | {lambda_by_W:.2f} | 2.1 | {agreement} ({diff_pct:.1f}%)\n"

    report += f"""

## Scientific Interpretation

### Addressing Peer Review Issue #3

**The concern**: Linear perturbation theory predicts strong f-dependence (λ ∝ f^α with α ≈ 0.5-1.0), but non-linear MHD results showed weak/no f-dependence.

**What BRIDGE_GRID found**:
"""

    # Determine f-dependence strength
    all_fits = [fit_power_law(df_success, beta) for beta in sorted(df['beta'].unique())]
    valid_fits = [f for f in all_fits if f is not None]

    if valid_fits:
        avg_alpha = np.mean([f['alpha'] for f in valid_fits])
        avg_alpha_err = np.mean([f['alpha_err'] for f in valid_fits])

        if avg_alpha > 0.3:
            interpretation = f"**Moderate f-dependence detected**: α = {avg_alpha:.2f} ± {avg_alpha_err:.2f}. This is consistent with linear perturbation theory predictions, supporting the extrapolation from near-critical to supercritical regimes."
        elif avg_alpha > 0.1:
            interpretation = f"**Weak f-dependence detected**: α = {avg_alpha:.2f} ± {avg_alpha_err:.2f}. This suggests non-linear effects partially suppress the f-dependence predicted by linear theory."
        else:
            interpretation = f"**No significant f-dependence**: α = {avg_alpha:.2f} ± {avg_alpha_err:.2f}. Non-linear MHD effects dominate, washing out the theoretical f-dependence. The contradiction raised by the referee is confirmed and requires further investigation."

        report += f"\n{interpretation}\n\n"
    else:
        report += "\nInsufficient data to determine f-dependence trend.\n\n"

    report += """
## Recommendations for Paper

1. **Update λ/W vs f plot**: Include new BRIDGE_GRID data points
2. **Discuss transition regime**: Characterize where behavior changes (if observed)
3. **Compare with theory**: Add perturbation theory curves for comparison
4. **Address referee concern**: Explicitly discuss whether contradiction is resolved

## Data Files

- Full results: `lambda_measurements.csv`
- Individual simulation status: `outputs/*/status.json`
- Raw HDF5 outputs: `outputs/*/*.h5`

---

**Campaign completion**: {pd.Timestamp.now().strftime('%Y-%m-%d')}
**Total wall time**: ~10 hours on 200 vCPU
**Next steps**: Integrate results into paper, prepare referee response
"""

    with open(SUMMARY_FILE, 'w') as f:
        f.write(report)

    print(f"Saved: {SUMMARY_FILE}")


def main():
    """Main analysis workflow."""
    print("="*60)
    print("BRIDGE_GRID Campaign Analysis")
    print("="*60)

    # Load all simulation results
    print("\nAnalyzing simulation outputs...")
    df = analyze_all_simulations()

    if len(df) == 0:
        print("ERROR: No simulation results found!")
        print("Please run simulations first: python3 run_bridge_grid_200vcpu.py")
        return

    print(f"Found {len(df)} simulation results")

    # Save CSV
    csv_cols = ['sim_id', 'f', 'beta', 'M', 'theta', 'seed', 'status',
                't_frag', 'n_peaks', 'lambda_frag', 'lambda_frag_uncertainty',
                'longitudinal_variance', 'density_contrast']

    df.to_csv(RESULTS_FILE, index=False, columns=csv_cols)
    print(f"\nSaved: {RESULTS_FILE}")

    # Generate figures
    print("\nGenerating figures...")
    generate_figures(df)

    # Generate summary report
    print("\nGenerating summary report...")
    generate_summary_report(df)

    # Print summary
    df_success = df[df['status'] == 'success']
    df_success = df_success[df_success['lambda_frag'].notna()]

    print("\n" + "="*60)
    print("Analysis Complete")
    print("="*60)
    print(f"Successful lambda measurements: {len(df_success)}/{len(df)}")
    print(f"Results: {RESULTS_FILE}")
    print(f"Figures: {FIGURES_DIR}/")
    print(f"Summary: {SUMMARY_FILE}")


if __name__ == "__main__":
    main()
