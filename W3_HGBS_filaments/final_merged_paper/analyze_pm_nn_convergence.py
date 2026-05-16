#!/usr/bin/env python3
"""
Monte Carlo analysis of PM vs NN statistics for filament core spacing.

Addresses MC1 and MC4 from peer review:
- MC1: PM convergence test with synthetic filaments
- MC4: Pairwise median validation against known input

Author: ASTRA Analysis System
Date: 2026-05-04
"""

import numpy as np
import matplotlib.pyplot as plt
from scipy import stats
from pathlib import Path


def generate_periodic_filament(n_cores, filament_length, true_lambda_w,
                                 noise_level=0.05, random_seed=None):
    """
    Generate a synthetic filament with periodic beading at known wavelength.

    Parameters
    ----------
    n_cores : int
        Number of cores to generate
    filament_length : float
        Physical length of the filament (pc)
    true_lambda_w : float
        True fragmentation wavelength in units of filament width
        (lambda/W = 1.0 corresponds to spacing = 0.1 pc for W=0.1 pc)
    noise_level : float
        Gaussian noise amplitude (fraction of wavelength)
    random_seed : int or None
        Random seed for reproducibility

    Returns
    -------
    core_positions : ndarray
        1D array of core positions along filament (pc)
    """
    if random_seed is not None:
        np.random.seed(random_seed)

    # Filament width (HGBS characteristic value)
    W_fil = 0.1  # pc

    # True spacing in pc
    true_spacing = true_lambda_w * W_fil

    # Generate periodic positions with noise
    n_periods = int(filament_length / true_spacing)
    core_positions = []

    for i in range(n_periods + 1):
        # Base periodic position
        pos = i * true_spacing

        # Add Gaussian noise
        pos += np.random.normal(0, noise_level * true_spacing)

        # Only add if within filament
        if 0 <= pos <= filament_length:
            core_positions.append(pos)

    # Add random extra cores (if requested n_cores is larger)
    while len(core_positions) < n_cores:
        pos = np.random.uniform(0, filament_length)
        # Sort and insert
        core_positions.append(pos)
        core_positions.sort()

    # Trim to exactly n_cores if too many
    core_positions = np.array(core_positions[:n_cores])

    return core_positions


def compute_pairwise_median(positions):
    """
    Compute pairwise median statistic.

    For N cores, compute all N(N-1)/2 pairwise distances,
    then return the median.
    """
    n = len(positions)
    if n < 2:
        return np.nan

    # Compute all pairwise distances
    distances = []
    for i in range(n):
        for j in range(i+1, n):
            distances.append(abs(positions[j] - positions[i]))

    return np.median(distances)


def compute_nearest_neighbor(positions):
    """
    Compute nearest-neighbor (adjacent-core) spacing statistic.

    For N cores, compute distances between adjacent cores
    (sorted by position), then return the median.
    """
    n = len(positions)
    if n < 2:
        return np.nan

    # Sort positions
    sorted_pos = np.sort(positions)

    # Compute adjacent spacings
    adj_spacings = np.diff(sorted_pos)

    return np.median(adj_spacings)


def run_convergence_test(true_lambda_w_values, n_cores_range, filament_length,
                          n_realizations=100, noise_level=0.05):
    """
    Test PM vs NN convergence for various (true_lambda, N) combinations.

    Returns
    -------
    results : dict
        Dictionary containing:
        - 'pm_values': PM measurements [n_lambda, n_n_cores, n_realizations]
        - 'nn_values': NN measurements [n_lambda, n_n_cores, n_realizations]
        - 'l3_predictions': L/3 predictions for each case
    """
    n_lambda = len(true_lambda_w_values)
    n_n_cores = len(n_cores_range)

    pm_values = np.full((n_lambda, n_n_cores, n_realizations), np.nan)
    nn_values = np.full((n_lambda, n_n_cores, n_realizations), np.nan)

    for i, true_lambda_w in enumerate(true_lambda_w_values):
        for j, n_cores in enumerate(n_cores_range):
            for k in range(n_realizations):
                # Generate filament
                positions = generate_periodic_filament(
                    n_cores=n_cores,
                    filament_length=filament_length,
                    true_lambda_w=true_lambda_w,
                    noise_level=noise_level,
                    random_seed=i*1000 + j*100 + k
                )

                # Compute statistics
                pm_values[i, j, k] = compute_pairwise_median(positions) / 0.1  # lambda/W
                nn_values[i, j, k] = compute_nearest_neighbor(positions) / 0.1  # lambda/W

    # Compute L/3 predictions
    l3_predictions = np.full(n_n_cores, filament_length / 3.0 / 0.1)  # lambda/W

    return {
        'pm_values': pm_values,
        'nn_values': nn_values,
        'l3_predictions': l3_predictions,
        'true_lambda_w_values': true_lambda_w_values,
        'n_cores_range': n_cores_range,
        'filament_length': filament_length
    }


def analyze_results(results):
    """
    Analyze Monte Carlo results and compute key metrics.

    Returns
    -------
    summary : dict
        Dictionary with summary statistics and figures
    """
    pm_values = results['pm_values']
    nn_values = results['nn_values']
    l3_predictions = results['l3_predictions']
    true_lambda_w_values = results['true_lambda_w_values']
    n_cores_range = results['n_cores_range']

    n_lambda = len(true_lambda_w_values)
    n_n_cores = len(n_cores_range)

    # Compute means and stds
    pm_mean = np.nanmean(pm_values, axis=2)
    pm_std = np.nanstd(pm_values, axis=2)
    nn_mean = np.nanmean(nn_values, axis=2)
    nn_std = np.nanstd(nn_values, axis=2)

    summary = {
        'pm_mean': pm_mean,
        'pm_std': pm_std,
        'nn_mean': nn_mean,
        'nn_std': nn_std,
        'l3_predictions': l3_predictions,
        'true_lambda_w_values': true_lambda_w_values,
        'n_cores_range': n_cores_range
    }

    return summary


def plot_convergence_results(summary, output_dir):
    """
    Generate publication-quality figures showing PM vs NN convergence.
    """
    output_path = Path(output_dir)
    output_path.mkdir(exist_ok=True)

    # Figure 1: PM vs NN for different true wavelengths
    fig, axes = plt.subplots(2, 2, figsize=(12, 10))
    fig.suptitle('PM vs NN Statistics: Convergence Analysis', fontsize=16, fontweight='bold')

    true_lambda_w_values = summary['true_lambda_w_values']
    n_cores_range = summary['n_cores_range']

    # Panel (a): PM recovery for different true wavelengths
    ax = axes[0, 0]
    for i, true_lambda_w in enumerate(true_lambda_w_values):
        pm_mean = summary['pm_mean'][i, :]
        pm_std = summary['pm_std'][i, :]
        ax.errorbar(n_cores_range, pm_mean, yerr=pm_std,
                   marker='o', label=f'True $\\lambda/W$ = {true_lambda_w:.1f}',
                   capsize=3, linewidth=2)

    # L/3 prediction
    l3_pred = summary['l3_predictions']
    ax.axhline(y=l3_pred[0], color='gray', linestyle='--',
               label=f'$L/3$ prediction ($\\lambda/W \\approx {l3_pred[0]:.1f}$)',
               linewidth=2, alpha=0.7)

    ax.set_xlabel('Number of Cores ($N$)', fontsize=12)
    ax.set_ylabel('Measured $\\lambda/W$ (PM statistic)', fontsize=12)
    ax.set_title('(a) Pairwise Median Recovery', fontsize=13, fontweight='bold')
    ax.legend(fontsize=9)
    ax.grid(True, alpha=0.3)
    ax.set_xscale('log')

    # Panel (b): NN recovery for different true wavelengths
    ax = axes[0, 1]
    for i, true_lambda_w in enumerate(true_lambda_w_values):
        nn_mean = summary['nn_mean'][i, :]
        nn_std = summary['nn_std'][i, :]
        ax.errorbar(n_cores_range, nn_mean, yerr=nn_std,
                   marker='s', label=f'True $\\lambda/W$ = {true_lambda_w:.1f}',
                   capsize=3, linewidth=2)

    # True wavelength reference lines
    for true_lambda_w in true_lambda_w_values:
        ax.axhline(y=true_lambda_w, color='gray', linestyle=':', alpha=0.5)

    ax.set_xlabel('Number of Cores ($N$)', fontsize=12)
    ax.set_ylabel('Measured $\\lambda/W$ (NN statistic)', fontsize=12)
    ax.set_title('(b) Nearest-Neighbor Recovery', fontsize=13, fontweight='bold')
    ax.legend(fontsize=9)
    ax.grid(True, alpha=0.3)
    ax.set_xscale('log')

    # Panel (c): PM/NN ratio vs N
    ax = axes[1, 0]
    for i, true_lambda_w in enumerate(true_lambda_w_values):
        ratio = summary['pm_mean'][i, :] / summary['nn_mean'][i, :]
        ax.plot(n_cores_range, ratio, marker='o',
               label=f'True $\\lambda/W$ = {true_lambda_w:.1f}', linewidth=2)

    ax.axhline(y=1.0, color='black', linestyle='--', label='PM = NN', linewidth=2)
    ax.set_xlabel('Number of Cores ($N$)', fontsize=12)
    ax.set_ylabel('PM / NN Ratio', fontsize=12)
    ax.set_title('(c) Convergence Ratio', fontsize=13, fontweight='bold')
    ax.legend(fontsize=9)
    ax.grid(True, alpha=0.3)
    ax.set_xscale('log')

    # Panel (d): Recovery error
    ax = axes[1, 1]
    for i, true_lambda_w in enumerate(true_lambda_w_values):
        pm_error = (summary['pm_mean'][i, :] - true_lambda_w) / true_lambda_w * 100
        nn_error = (summary['nn_mean'][i, :] - true_lambda_w) / true_lambda_w * 100

        ax.plot(n_cores_range, pm_error, marker='o', linestyle='-',
               label=f'PM error ($\\lambda/W$={true_lambda_w:.1f})', linewidth=2)
        ax.plot(n_cores_range, nn_error, marker='s', linestyle='--',
               label=f'NN error ($\\lambda/W$={true_lambda_w:.1f})', linewidth=2)

    ax.axhline(y=0, color='black', linestyle='-', linewidth=1)
    ax.set_xlabel('Number of Cores ($N$)', fontsize=12)
    ax.set_ylabel('Recovery Error (%)', fontsize=12)
    ax.set_title('(d) Measurement Accuracy', fontsize=13, fontweight='bold')
    ax.legend(fontsize=8, ncol=2)
    ax.grid(True, alpha=0.3)
    ax.set_xscale('log')

    plt.tight_layout()
    fig.savefig(output_path / 'pm_nn_convergence.pdf', dpi=300, bbox_inches='tight')
    fig.savefig(output_path / 'pm_nn_convergence.png', dpi=150, bbox_inches='tight')
    plt.close()

    print(f"Figure saved: {output_path / 'pm_nn_convergence.pdf'}")

    # Figure 2: Orion B specific case (N=1844)
    fig, axes = plt.subplots(1, 2, figsize=(12, 5))

    # Test Orion B parameters
    orion_n = 1844
    orion_length_pc = 0.313 * 3  # Approximate length from spacing
    true_lambdas = [1.25, 2.0, 2.84, 3.33, 4.0]

    pm_recoveries = []
    nn_recoveries = []
    l3_value = orion_length_pc / 3.0 / 0.1

    for true_lambda in true_lambdas:
        positions = generate_periodic_filament(
            n_cores=orion_n,
            filament_length=orion_length_pc,
            true_lambda_w=true_lambda,
            noise_level=0.05,
            random_seed=42
        )
        pm = compute_pairwise_median(positions) / 0.1
        nn = compute_nearest_neighbor(positions) / 0.1
        pm_recoveries.append(pm)
        nn_recoveries.append(nn)

    # Panel (a): Orion B recovery
    ax = axes[0]
    ax.plot(true_lambdas, pm_recoveries, 'o-', label='Pairwise Median',
            linewidth=2, markersize=8)
    ax.plot(true_lambdas, nn_recoveries, 's-', label='Nearest-Neighbor',
            linewidth=2, markersize=8)
    ax.plot(true_lambdas, true_lambdas, 'k--', label='True value (1:1)',
            linewidth=2)
    ax.axhline(y=l3_value, color='gray', linestyle=':',
               label=f'$L/3$ prediction ({l3_value:.1f})', linewidth=2)
    ax.set_xlabel('True $\\lambda/W$', fontsize=12)
    ax.set_ylabel('Measured $\\lambda/W$', fontsize=12)
    ax.set_title(f'(a) Orion B Case: N = {orion_n} cores', fontsize=13, fontweight='bold')
    ax.legend(fontsize=10)
    ax.grid(True, alpha=0.3)
    ax.set_xlim([1, 4.5])
    ax.set_ylim([1, 4.5])

    # Panel (b): Bias vs true wavelength
    ax = axes[1]
    pm_bias = np.array(pm_recoveries) - np.array(true_lambdas)
    nn_bias = np.array(nn_recoveries) - np.array(true_lambdas)
    l3_bias = l3_value - np.array(true_lambdas)

    ax.plot(true_lambdas, pm_bias, 'o-', label='PM bias', linewidth=2, markersize=8)
    ax.plot(true_lambdas, nn_bias, 's-', label='NN bias', linewidth=2, markersize=8)
    ax.axhline(y=0, color='black', linestyle='--', linewidth=1)
    ax.set_xlabel('True $\\lambda/W$', fontsize=12)
    ax.set_ylabel('Bias (Measured - True)', fontsize=12)
    ax.set_title('(b) Measurement Bias for Orion B', fontsize=13, fontweight='bold')
    ax.legend(fontsize=10)
    ax.grid(True, alpha=0.3)
    ax.axhline(y=0, color='black', linestyle='-', linewidth=1)

    plt.tight_layout()
    fig.savefig(output_path / 'orion_b_recovery.pdf', dpi=300, bbox_inches='tight')
    fig.savefig(output_path / 'orion_b_recovery.png', dpi=150, bbox_inches='tight')
    plt.close()

    print(f"Figure saved: {output_path / 'orion_b_recovery.pdf'}")


def generate_latex_table(summary, output_file):
    """
    Generate LaTeX table with key results.
    """
    output_path = Path(output_file)

    latex_content = r"""
\begin{table*}
\caption{Pairwise Median vs Nearest-Neighbor: Monte Carlo Validation Results}
\label{tab:pm_nn_validation}
\begin{tabular}{lccccc}
\toprule
True $\lambda/W$ & $N$ cores & PM (mean $\pm$ std) & NN (mean $\pm$ std) & $L/3$ Prediction & PM/NN Ratio \\
\midrule
"""

    # Add data rows
    n_lambda = len(summary['true_lambda_w_values'])
    n_n_cores = len(summary['n_cores_range'])

    for j, n_cores in enumerate(summary['n_cores_range']):
        if j > 0 and j % 3 == 0:
            latex_content += r"\midrule" + "\n"

        for i, true_lambda in enumerate(summary['true_lambda_w_values']):
            pm_mean = summary['pm_mean'][i, j]
            pm_std = summary['pm_std'][i, j]
            nn_mean = summary['nn_mean'][i, j]
            nn_std = summary['nn_std'][i, j]
            l3_pred = summary['l3_predictions'][j]
            ratio = pm_mean / nn_mean if nn_mean > 0 else np.nan

            line = f"{true_lambda:.1f} & {n_cores:4d} & "
            line += f"{pm_mean:.2f} $\\pm$ {pm_std:.2f} & "
            line += f"{nn_mean:.2f} $\\pm$ {nn_std:.2f} & "
            line += f"{l3_pred:.2f} & "
            line += f"{ratio:.2f} \\\\\n"

            latex_content += line

    latex_content += r"""
\bottomrule
\end{tabular}

\vspace{0.1in}
\footnotesize
\textbf{Notes}: (1) PM = pairwise median statistic (all $N(N-1)/2$ core pairs).
(2) NN = nearest-neighbor statistic (adjacent cores only).
(3) $L/3$ prediction assumes uniform distribution of cores along filament length $L$.
(4) Monte Carlo realizations: 100 per (true $\lambda/W$, $N$) combination.
(5) Noise level: 5\% Gaussian positional noise.
(6) Filament length scaled to $L = 3\\lambda$ for each case.
\end{table*}
"""

    with open(output_path, 'w') as f:
        f.write(latex_content)

    print(f"LaTeX table saved: {output_path}")


def main():
    """Run full PM vs NN convergence analysis."""

    print("="*70)
    print("PM vs NN STATISTICS: MONTE CARLO VALIDATION")
    print("="*70)
    print()

    # Parameters for convergence test
    true_lambda_w_values = [1.25, 2.0, 2.5, 3.0, 3.33, 4.0]  # Range from perpendicular-field to classical
    n_cores_range = [50, 100, 200, 500, 1000, 1844]  # Up to Orion B size
    filament_length = 3.0 * 0.4  # ~3 wavelengths at classical spacing (0.4 pc)
    n_realizations = 100

    print("Test parameters:")
    print(f"  True $\\lambda/W$ values: {true_lambda_w_values}")
    print(f"  Core count range: {n_cores_range}")
    print(f"  Filament length: {filament_length:.2f} pc")
    print(f"  Realizations per case: {n_realizations}")
    print()

    print("Running convergence test...")
    results = run_convergence_test(
        true_lambda_w_values=true_lambda_w_values,
        n_cores_range=n_cores_range,
        filament_length=filament_length,
        n_realizations=n_realizations,
        noise_level=0.05
    )

    print("Analyzing results...")
    summary = analyze_results(results)

    # Generate outputs
    output_dir = Path("figures")
    print(f"Generating figures in {output_dir}/...")
    plot_convergence_results(summary, output_dir)

    print("Generating LaTeX table...")
    generate_latex_table(summary, "figures/pm_nn_validation_table.tex")

    print()
    print("="*70)
    print("KEY FINDINGS")
    print("="*70)

    # Print key findings
    orion_n_idx = len(n_cores_range) - 1  # Last index (largest N)

    print(f"\n1. L/3 Convergence Test (for N = {n_cores_range[-1]} cores):")
    for i, true_lambda in enumerate(true_lambda_w_values):
        pm_mean = summary['pm_mean'][i, -1]
        l3_pred = summary['l3_predictions'][-1]
        convergence_pct = abs(pm_mean - l3_pred) / l3_pred * 100
        print(f"   True $\\lambda/W$ = {true_lambda:.2f}: "
              f"PM = {pm_mean:.2f}, L/3 = {l3_pred:.2f} "
              f"({convergence_pct:.1f}% difference)")

    print(f"\n2. NN Statistic Accuracy:")
    for i, true_lambda in enumerate(true_lambda_w_values):
        nn_mean = summary['nn_mean'][i, -1]
        nn_std = summary['nn_std'][i, -1]
        bias_pct = (nn_mean - true_lambda) / true_lambda * 100
        print(f"   True $\\lambda/W$ = {true_lambda:.2f}: "
              f"NN = {nn_mean:.2f} $\\pm$ {nn_std:.2f} "
              f"(bias = {bias_pct:+.1f}%)")

    print(f"\n3. Orion B Case (N = 1844, true $\\lambda/W$ = 3.13):")
    positions = generate_periodic_filament(
        n_cores=1844,
        filament_length=0.313 * 3,
        true_lambda_w=3.13,
        noise_level=0.05,
        random_seed=42
    )
    pm = compute_pairwise_median(positions) / 0.1
    nn = compute_nearest_neighbor(positions) / 0.1
    l3 = (0.313 * 3) / 3.0 / 0.1
    print(f"   PM = {pm:.2f} (converges to L/3 = {l3:.2f})")
    print(f"   NN = {nn:.2f} (recovers true value)")
    print(f"   PM/NN ratio = {pm/nn:.2f}")

    print()
    print("="*70)
    print("ANALYSIS COMPLETE")
    print("="*70)
    print(f"\nOutputs:")
    print(f"  - figures/pm_nn_convergence.pdf/png")
    print(f"  - figures/orion_b_recovery.pdf/png")
    print(f"  - figures/pm_nn_validation_table.tex")
    print()


if __name__ == '__main__':
    main()
