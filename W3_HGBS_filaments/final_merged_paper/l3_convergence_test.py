#!/usr/bin/env python3
"""
Injection-Recovery Monte Carlo Test of L/3 Convergence Artifact

Tests whether the pairwise median (PM) statistic converges to L/3 for clustered
core distributions (like HGBS filaments) or only for uniform distributions.

Author: Referee Response Campaign
Date: 2026-05-08
"""

import numpy as np
from scipy.spatial import distance
from scipy.stats import poisson
import matplotlib.pyplot as plt
import json
from pathlib import Path
import warnings
warnings.filterwarnings('ignore')


def generate_uniform_cores(L, N):
    """
    Generate uniformly distributed cores along filament (baseline case).

    Parameters:
    -----------
    L : float - Filament length (pc)
    N : int - Number of cores

    Returns:
    --------
    positions : array - Core positions (pc)
    """
    return np.random.uniform(0, L, N)


def generate_beaded_filament(L, lambda_true, n_cores_per_bead=20, sigma_bead=0.05, seed=None):
    """
    Generate synthetic filament with periodic beading (clustered cores).

    This simulates a realistic HGBS filament with periodic fragmentation.

    Parameters:
    -----------
    L : float - Filament length (pc)
    lambda_true : float - True fragmentation wavelength (pc)
    n_cores_per_bead : int - Mean number of cores per bead
    sigma_bead : float - Core clustering scale within each bead (pc)
    seed : int - Random seed for reproducibility

    Returns:
    --------
    positions : array - Core positions along filament (pc)
    bead_centers : array - True bead centers (pc)
    """
    if seed is not None:
        np.random.seed(seed)

    n_beads = int(L / lambda_true)
    core_positions = []
    bead_centers = []

    for i in range(n_beads):
        bead_center = i * lambda_true
        bead_centers.append(bead_center)

        # Number of cores in this bead (Poisson variation)
        n_cores = np.random.poisson(n_cores_per_bead)

        for _ in range(n_cores):
            # Core position: bead center + Gaussian scatter
            offset = np.random.normal(0, sigma_bead)
            core_positions.append(bead_center + offset)

    return np.array(core_positions), np.array(bead_centers)


def compute_pairwise_median(positions):
    """
    Compute pairwise median (PM) statistic.

    For N cores, computes all N(N-1)/2 pairwise distances and takes median.

    Parameters:
    -----------
    positions : array - Core positions (pc)

    Returns:
    --------
    lambda_pm : float - PM-based spacing estimate (pc)
    """
    if len(positions) < 2:
        return np.nan

    pairwise_dists = distance.pdist(positions.reshape(-1, 1))
    return np.median(pairwise_dists)


def compute_nn_spacing(positions):
    """
    Compute nearest-neighbor (NN) spacing statistic.

    Sorts positions along filament and computes spacings between adjacent cores.

    Parameters:
    -----------
    positions : array - Core positions (pc)

    Returns:
    --------
    lambda_nn : float - NN-based spacing estimate (pc)
    """
    if len(positions) < 2:
        return np.nan

    sorted_pos = np.sort(positions)
    spacings = np.diff(sorted_pos)
    return np.median(spacings)


def run_single_realization(L, lambda_true, n_cores_per_bead, sigma_bead, seed=None):
    """
    Run one realization of the injection-recovery test.

    Generates a beaded filament with known lambda_true, then applies
    both PM and NN statistics to recover the spacing.

    Parameters:
    -----------
    L : float - Filament length (pc)
    lambda_true : float - True fragmentation wavelength (pc)
    n_cores_per_bead : int - Mean number of cores per bead
    sigma_bead : float - Core clustering scale (pc)
    seed : int - Random seed

    Returns:
    --------
    result : dict - Results including PM, NN, biases, and metadata
    """
    positions, bead_centers = generate_beaded_filament(
        L, lambda_true, n_cores_per_bead, sigma_bead, seed
    )

    if len(positions) < 2:
        return None

    lambda_pm = compute_pairwise_median(positions)
    lambda_nn = compute_nn_spacing(positions)

    return {
        'N': len(positions),
        'n_beads': len(bead_centers),
        'lambda_true': lambda_true,
        'L': L,
        'sigma_bead': sigma_bead,
        'lambda_pm': lambda_pm,
        'lambda_nn': lambda_nn,
        'bias_pm': (lambda_pm - lambda_true) / lambda_true,
        'bias_nn': (lambda_nn - lambda_true) / lambda_true,
        'L_over_3': L / 3.0,
        'pm_converges_to_L3': abs(lambda_pm - L/3.0) < abs(lambda_pm - lambda_true),
        'nn_converges_to_true': abs(lambda_nn - lambda_true) < abs(lambda_nn - L/3.0)
    }


def run_convergence_test(L=2.0, lambda_true=0.20, sigma_bead=0.05, n_realizations=200):
    """
    Test PM vs NN convergence as number of cores varies.

    Parameters:
    -----------
    L : float - Filament length (pc)
    lambda_true : float - True fragmentation wavelength (pc)
    sigma_bead : float - Core clustering scale (pc)
    n_realizations : int - Number of random realizations per parameter point

    Returns:
    --------
    results : list - Results for each n_cores_per_bead value
    """
    results = []

    # Vary number of cores per bead to test N dependence
    n_cores_values = [5, 10, 15, 20, 30, 50, 80, 120]

    for n_cores in n_cores_values:
        realization_results = []

        for i in range(n_realizations):
            result = run_single_realization(
                L, lambda_true, n_cores, sigma_bead, seed=i
            )

            if result is not None:
                realization_results.append(result)

        if not realization_results:
            continue

        # Aggregate statistics
        avg_N = np.mean([r['N'] for r in realization_results])
        avg_lambda_pm = np.mean([r['lambda_pm'] for r in realization_results])
        std_lambda_pm = np.std([r['lambda_pm'] for r in realization_results])
        avg_lambda_nn = np.mean([r['lambda_nn'] for r in realization_results])
        std_lambda_nn = np.std([r['lambda_nn'] for r in realization_results])
        avg_bias_pm = np.mean([r['bias_pm'] for r in realization_results])
        std_bias_pm = np.std([r['bias_pm'] for r in realization_results])
        avg_bias_nn = np.mean([r['bias_nn'] for r in realization_results])
        std_bias_nn = np.std([r['bias_nn'] for r in realization_results])

        # Test convergence
        pm_to_L3 = np.mean([r['pm_converges_to_L3'] for r in realization_results])
        nn_to_true = np.mean([r['nn_converges_to_true'] for r in realization_results])

        results.append({
            'n_cores_per_bead': n_cores,
            'avg_N': avg_N,
            'avg_lambda_pm': avg_lambda_pm,
            'std_lambda_pm': std_lambda_pm,
            'avg_lambda_nn': avg_lambda_nn,
            'std_lambda_nn': std_lambda_nn,
            'avg_bias_pm': avg_bias_pm,
            'std_bias_pm': std_bias_pm,
            'avg_bias_nn': avg_bias_nn,
            'std_bias_nn': std_bias_nn,
            'pm_converges_to_L3_fraction': pm_to_L3,
            'nn_converges_to_true_fraction': nn_to_true,
            'L_over_3': L / 3.0,
            'lambda_true': lambda_true
        })

    return results


def run_clustering_strength_test(L=2.0, lambda_true=0.20, n_cores_per_bead=20, n_realizations=200):
    """
    Test PM vs NN as clustering strength varies.

    Clustering strength is controlled by sigma_bead (smaller = stronger clustering).

    Parameters:
    -----------
    L : float - Filament length (pc)
    lambda_true : float - True fragmentation wavelength (pc)
    n_cores_per_bead : int - Mean number of cores per bead
    n_realizations : int - Number of random realizations per parameter point

    Returns:
    --------
    results : list - Results for each sigma_bead value
    """
    results = []

    # Vary clustering strength (sigma_bead)
    # sigma_bead = 0.01: very strong clustering (cores tightly grouped)
    # sigma_bead = 0.20: weak clustering (approaching uniform)
    sigma_values = [0.01, 0.02, 0.05, 0.08, 0.12, 0.15, 0.20, 0.30]

    for sigma in sigma_values:
        realization_results = []

        for i in range(n_realizations):
            result = run_single_realization(
                L, lambda_true, n_cores_per_bead, sigma, seed=i
            )

            if result is not None:
                realization_results.append(result)

        if not realization_results:
            continue

        avg_N = np.mean([r['N'] for r in realization_results])
        avg_lambda_pm = np.mean([r['lambda_pm'] for r in realization_results])
        std_lambda_pm = np.std([r['lambda_pm'] for r in realization_results])
        avg_lambda_nn = np.mean([r['lambda_nn'] for r in realization_results])
        std_lambda_nn = np.std([r['lambda_nn'] for r in realization_results])
        avg_bias_pm = np.mean([r['bias_pm'] for r in realization_results])
        std_bias_pm = np.std([r['bias_pm'] for r in realization_results])
        avg_bias_nn = np.mean([r['bias_nn'] for r in realization_results])
        std_bias_nn = np.std([r['bias_nn'] for r in realization_results])

        # Test convergence
        pm_to_L3 = np.mean([r['pm_converges_to_L3'] for r in realization_results])
        nn_to_true = np.mean([r['nn_converges_to_true'] for r in realization_results])

        results.append({
            'sigma_bead': sigma,
            'avg_N': avg_N,
            'avg_lambda_pm': avg_lambda_pm,
            'std_lambda_pm': std_lambda_pm,
            'avg_lambda_nn': avg_lambda_nn,
            'std_lambda_nn': std_lambda_nn,
            'avg_bias_pm': avg_bias_pm,
            'std_bias_pm': std_bias_pm,
            'avg_bias_nn': avg_bias_nn,
            'std_bias_nn': std_bias_nn,
            'pm_converges_to_L3_fraction': pm_to_L3,
            'nn_converges_to_true_fraction': nn_to_true,
            'clustering_ratio': lambda_true / sigma,  # Higher = stronger clustering
            'L_over_3': L / 3.0,
            'lambda_true': lambda_true
        })

    return results


def run_wavelength_test(L=2.0, sigma_bead=0.05, n_cores_per_bead=20, n_realizations=200):
    """
    Test PM vs NN across different true wavelengths.

    Parameters:
    -----------
    L : float - Filament length (pc)
    sigma_bead : float - Core clustering scale (pc)
    n_cores_per_bead : int - Mean number of cores per bead
    n_realizations : int - Number of random realizations per parameter point

    Returns:
    --------
    results : list - Results for each lambda_true value
    """
    results = []

    # Test different wavelengths (lambda/W from 1.0 to 4.0)
    # W = 0.1 pc, so lambda from 0.1 to 0.4 pc
    lambda_values = [0.10, 0.15, 0.20, 0.25, 0.30, 0.35, 0.40]

    for lam in lambda_values:
        realization_results = []

        for i in range(n_realizations):
            result = run_single_realization(
                L, lam, n_cores_per_bead, sigma_bead, seed=i
            )

            if result is not None:
                realization_results.append(result)

        if not realization_results:
            continue

        avg_N = np.mean([r['N'] for r in realization_results])
        avg_lambda_pm = np.mean([r['lambda_pm'] for r in realization_results])
        std_lambda_pm = np.std([r['lambda_pm'] for r in realization_results])
        avg_lambda_nn = np.mean([r['lambda_nn'] for r in realization_results])
        std_lambda_nn = np.std([r['lambda_nn'] for r in realization_results])
        avg_bias_pm = np.mean([r['bias_pm'] for r in realization_results])
        std_bias_pm = np.std([r['bias_pm'] for r in realization_results])
        avg_bias_nn = np.mean([r['bias_nn'] for r in realization_results])
        std_bias_nn = np.std([r['bias_nn'] for r in realization_results])

        # Test convergence
        pm_to_L3 = np.mean([r['pm_converges_to_L3'] for r in realization_results])
        nn_to_true = np.mean([r['nn_converges_to_true'] for r in realization_results])

        results.append({
            'lambda_true': lam,
            'lambda_over_W': lam / 0.1,  # W = 0.1 pc
            'avg_N': avg_N,
            'avg_lambda_pm': avg_lambda_pm,
            'std_lambda_pm': std_lambda_pm,
            'avg_lambda_nn': avg_lambda_nn,
            'std_lambda_nn': std_lambda_nn,
            'avg_bias_pm': avg_bias_pm,
            'std_bias_pm': std_bias_pm,
            'avg_bias_nn': avg_bias_nn,
            'std_bias_nn': std_bias_nn,
            'pm_converges_to_L3_fraction': pm_to_L3,
            'nn_converges_to_true_fraction': nn_to_true,
            'L_over_3': L / 3.0
        })

    return results


def run_uniform_baseline(L=2.0, n_realizations=200):
    """
    Run uniform distribution baseline case (where L/3 artifact is expected).

    Parameters:
    -----------
    L : float - Filament length (pc)
    n_realizations : int - Number of random realizations

    Returns:
    --------
    results : list - Results for different N values
    """
    results = []

    N_values = [50, 100, 200, 500, 1000]

    for N in N_values:
        lambda_pm_values = []

        for i in range(n_realizations):
            positions = generate_uniform_cores(L, N)
            lambda_pm = compute_pairwise_median(positions)
            lambda_pm_values.append(lambda_pm)

        avg_lambda_pm = np.mean(lambda_pm_values)
        std_lambda_pm = np.std(lambda_pm_values)

        results.append({
            'N': N,
            'avg_lambda_pm': avg_lambda_pm,
            'std_lambda_pm': std_lambda_pm,
            'L_over_3': L / 3.0,
            'bias_from_L3': (avg_lambda_pm - L/3.0) / (L/3.0)
        })

    return results


def create_convergence_figure(convergence_results, clustering_results, wavelength_results, uniform_results, output_dir):
    """
    Create comprehensive figure showing all test results.
    """
    fig, axes = plt.subplots(2, 2, figsize=(12, 10))
    fig.suptitle('L/3 Convergence Artifact Test: Injection-Recovery Monte Carlo', fontsize=14, fontweight='bold')

    # Panel A: Convergence vs N (number of cores)
    ax = axes[0, 0]
    N_vals = [r['avg_N'] for r in convergence_results]
    pm_vals = [r['avg_lambda_pm'] for r in convergence_results]
    pm_errs = [r['std_lambda_pm'] for r in convergence_results]
    nn_vals = [r['avg_lambda_nn'] for r in convergence_results]
    nn_errs = [r['std_lambda_nn'] for r in convergence_results]
    L3 = convergence_results[0]['L_over_3']
    true = convergence_results[0]['lambda_true']

    ax.errorbar(N_vals, pm_vals, yerr=pm_errs, fmt='o-', label='PM (pairwise median)', color='red', linewidth=2)
    ax.errorbar(N_vals, nn_vals, yerr=nn_errs, fmt='s-', label='NN (nearest neighbor)', color='blue', linewidth=2)
    ax.axhline(L3, color='gray', linestyle='--', label=f'L/3 = {L3:.3f} pc', alpha=0.7)
    ax.axhline(true, color='green', linestyle=':', label=f'λ_true = {true:.3f} pc', alpha=0.7)

    ax.set_xlabel('Number of cores (N)')
    ax.set_ylabel('Recovered wavelength λ (pc)')
    ax.set_title('Panel A: Convergence vs Sample Size')
    ax.legend()
    ax.grid(True, alpha=0.3)
    ax.set_xscale('log')

    # Panel B: Convergence vs clustering strength
    ax = axes[0, 1]
    sigma_vals = [r['sigma_bead'] for r in clustering_results]
    pm_vals = [r['avg_lambda_pm'] for r in clustering_results]
    pm_errs = [r['std_lambda_pm'] for r in clustering_results]
    nn_vals = [r['avg_lambda_nn'] for r in clustering_results]
    nn_errs = [r['std_lambda_nn'] for r in clustering_results]
    L3 = clustering_results[0]['L_over_3']
    true = clustering_results[0]['lambda_true']

    ax.errorbar(sigma_vals, pm_vals, yerr=pm_errs, fmt='o-', label='PM', color='red', linewidth=2)
    ax.errorbar(sigma_vals, nn_vals, yerr=nn_errs, fmt='s-', label='NN', color='blue', linewidth=2)
    ax.axhline(L3, color='gray', linestyle='--', label=f'L/3 = {L3:.3f} pc', alpha=0.7)
    ax.axhline(true, color='green', linestyle=':', label=f'λ_true = {true:.3f} pc', alpha=0.7)

    ax.set_xlabel('Clustering scale σ (pc) [smaller = stronger clustering]')
    ax.set_ylabel('Recovered wavelength λ (pc)')
    ax.set_title('Panel B: Convergence vs Clustering Strength')
    ax.legend()
    ax.grid(True, alpha=0.3)

    # Panel C: Convergence vs true wavelength
    ax = axes[1, 0]
    lam_true = [r['lambda_true'] for r in wavelength_results]
    pm_vals = [r['avg_lambda_pm'] for r in wavelength_results]
    pm_errs = [r['std_lambda_pm'] for r in wavelength_results]
    nn_vals = [r['avg_lambda_nn'] for r in wavelength_results]
    nn_errs = [r['std_lambda_nn'] for r in wavelength_results]

    ax.errorbar(lam_true, pm_vals, yerr=pm_errs, fmt='o-', label='PM', color='red', linewidth=2)
    ax.errorbar(lam_true, nn_vals, yerr=nn_errs, fmt='s-', label='NN', color='blue', linewidth=2)
    ax.plot(lam_true, lam_true, 'k:', label='Perfect recovery (λ = λ_true)', linewidth=2)

    ax.set_xlabel('True wavelength λ_true (pc)')
    ax.set_ylabel('Recovered wavelength λ (pc)')
    ax.set_title('Panel C: Recovery Accuracy vs True Wavelength')
    ax.legend()
    ax.grid(True, alpha=0.3)

    # Panel D: Uniform baseline (where L/3 is expected)
    ax = axes[1, 1]
    N_vals = [r['N'] for r in uniform_results]
    pm_vals = [r['avg_lambda_pm'] for r in uniform_results]
    pm_errs = [r['std_lambda_pm'] for r in uniform_results]
    L3 = uniform_results[0]['L_over_3']

    ax.errorbar(N_vals, pm_vals, yerr=pm_errs, fmt='o-', label='PM (uniform)', color='red', linewidth=2)
    ax.axhline(L3, color='gray', linestyle='--', label=f'L/3 = {L3:.3f} pc', alpha=0.7)

    ax.set_xlabel('Number of cores (N)')
    ax.set_ylabel('Recovered wavelength λ (pc)')
    ax.set_title('Panel D: Uniform Distribution (L/3 Expected)')
    ax.legend()
    ax.grid(True, alpha=0.3)
    ax.set_xscale('log')

    plt.tight_layout()

    output_path = output_dir / 'l3_convergence_test.png'
    plt.savefig(output_path, dpi=300, bbox_inches='tight')
    plt.savefig(output_dir / 'l3_convergence_test.pdf', bbox_inches='tight')

    print(f"Figure saved to {output_path}")
    plt.close()


def create_bias_figure(convergence_results, clustering_results, wavelength_results, output_dir):
    """
    Create figure showing bias vs N and clustering strength.
    """
    fig, axes = plt.subplots(1, 2, figsize=(12, 5))
    fig.suptitle('PM and NN Bias: Injection-Recovery Results', fontsize=14, fontweight='bold')

    # Panel A: Bias vs N
    ax = axes[0]
    N_vals = [r['avg_N'] for r in convergence_results]
    pm_bias = [r['avg_bias_pm'] * 100 for r in convergence_results]  # Convert to %
    pm_bias_err = [r['std_bias_pm'] * 100 for r in convergence_results]
    nn_bias = [r['avg_bias_nn'] * 100 for r in convergence_results]  # Convert to %
    nn_bias_err = [r['std_bias_nn'] * 100 for r in convergence_results]

    ax.errorbar(N_vals, pm_bias, yerr=pm_bias_err, fmt='o-', label='PM bias', color='red', linewidth=2)
    ax.errorbar(N_vals, nn_bias, yerr=nn_bias_err, fmt='s-', label='NN bias', color='blue', linewidth=2)
    ax.axhline(0, color='gray', linestyle='--', label='Unbiased', alpha=0.7)

    ax.set_xlabel('Number of cores (N)')
    ax.set_ylabel('Bias (%)')
    ax.set_title('Panel A: Bias vs Sample Size')
    ax.legend()
    ax.grid(True, alpha=0.3)
    ax.set_xscale('log')

    # Panel B: Bias vs clustering strength
    ax = axes[1]
    sigma_vals = [r['sigma_bead'] for r in clustering_results]
    pm_bias = [r['avg_bias_pm'] * 100 for r in clustering_results]
    pm_bias_err = [r['std_bias_pm'] * 100 for r in clustering_results]
    nn_bias = [r['avg_bias_nn'] * 100 for r in clustering_results]
    nn_bias_err = [r['std_bias_nn'] * 100 for r in clustering_results]

    ax.errorbar(sigma_vals, pm_bias, yerr=pm_bias_err, fmt='o-', label='PM bias', color='red', linewidth=2)
    ax.errorbar(sigma_vals, nn_bias, yerr=nn_bias_err, fmt='s-', label='NN bias', color='blue', linewidth=2)
    ax.axhline(0, color='gray', linestyle='--', label='Unbiased', alpha=0.7)

    ax.set_xlabel('Clustering scale σ (pc) [smaller = stronger clustering]')
    ax.set_ylabel('Bias (%)')
    ax.set_title('Panel B: Bias vs Clustering Strength')
    ax.legend()
    ax.grid(True, alpha=0.3)

    plt.tight_layout()

    output_path_png = output_dir / 'l3_bias_analysis.png'
    output_path_pdf = output_dir / 'l3_bias_analysis.pdf'
    plt.savefig(output_path_png, dpi=300, bbox_inches='tight')
    plt.savefig(output_path_pdf, bbox_inches='tight')

    print(f"Bias analysis figure saved to {output_path_png}")
    plt.close()


def print_summary_statistics(convergence_results, clustering_results, wavelength_results, uniform_results, L=2.0, lambda_true=0.20):
    """
    Print summary statistics to console.
    """
    print("\n" + "="*70)
    print("L/3 CONVERGENCE TEST: SUMMARY STATISTICS")
    print("="*70)

    # Test parameters passed as arguments

    print(f"\nFilament parameters:")
    print(f"  Length L = {L:.2f} pc")
    print(f"  True wavelength λ_true = {lambda_true:.3f} pc (λ/W = {lambda_true/0.1:.1f})")
    print(f"  L/3 = {L/3:.3f} pc")

    print(f"\n{'-'*70}")
    print("UNIFORM DISTRIBUTION BASELINE (L/3 artifact expected)")
    print(f"{'-'*70}")

    for r in uniform_results[-3:]:  # Show largest 3 N values
        bias_pct = r['bias_from_L3'] * 100
        print(f"  N = {r['N']:4d}: PM = {r['avg_lambda_pm']:.4f} ± {r['std_lambda_pm']:.4f} pc, "
              f"bias from L/3 = {bias_pct:+.2f}%")

    print(f"\n{'-'*70}")
    print("CLUSTERED (BEADED) FILAMENTS")
    print(f"{'-'*70}")

    # Key test: High-N limit
    high_N_result = convergence_results[-1]
    pm_bias_pct = high_N_result['avg_bias_pm'] * 100
    nn_bias_pct = high_N_result['avg_bias_nn'] * 100

    print(f"\nHigh-N limit (N ≈ {high_N_result['avg_N']:.0f} cores):")
    print(f"  PM: λ = {high_N_result['avg_lambda_pm']:.4f} ± {high_N_result['std_lambda_pm']:.4f} pc")
    print(f"      Bias = {pm_bias_pct:+.1f}% from λ_true = {lambda_true:.3f} pc")
    print(f"      PM {'CONVERGES TO L/3' if high_N_result['pm_converges_to_L3_fraction'] > 0.5 else 'CONVERGES TO λ_TRUE'} "
          f"({high_N_result['pm_converges_to_L3_fraction']*100:.1f}% of realizations)")

    print(f"\n  NN: λ = {high_N_result['avg_lambda_nn']:.4f} ± {high_N_result['std_lambda_nn']:.4f} pc")
    print(f"      Bias = {nn_bias_pct:+.1f}% from λ_true = {lambda_true:.3f} pc")
    print(f"      NN {'CONVERGES TO λ_TRUE' if high_N_result['nn_converges_to_true_fraction'] > 0.5 else 'DOES NOT CONVERGE TO λ_TRUE'} "
          f"({high_N_result['nn_converges_to_true_fraction']*100:.1f}% of realizations)")

    # Clustering strength test
    strong_clustering = clustering_results[0]  # Smallest sigma
    weak_clustering = clustering_results[-1]   # Largest sigma

    print(f"\n{'-'*70}")
    print("CLUSTERING STRENGTH DEPENDENCE")
    print(f"{'-'*70}")

    print(f"\nStrong clustering (σ = {strong_clustering['sigma_bead']:.2f} pc):")
    print(f"  PM bias = {strong_clustering['avg_bias_pm']*100:+.1f}%")
    print(f"  NN bias = {strong_clustering['avg_bias_nn']*100:+.1f}%")

    print(f"\nWeak clustering (σ = {weak_clustering['sigma_bead']:.2f} pc, approaching uniform):")
    print(f"  PM bias = {weak_clustering['avg_bias_pm']*100:+.1f}%")
    print(f"  NN bias = {weak_clustering['avg_bias_nn']*100:+.1f}%")

    # Wavelength dependence
    print(f"\n{'-'*70}")
    print("WAVELENGTH DEPENDENCE")
    print(f"{'-'*70}")

    for r in wavelength_results[::2]:  # Show every other result
        print(f"  λ_true = {r['lambda_true']:.2f} pc (λ/W = {r['lambda_over_W']:.1f}): "
              f"PM bias = {r['avg_bias_pm']*100:+.1f}%, "
              f"NN bias = {r['avg_bias_nn']*100:+.1f}%")

    print(f"\n{'-'*70}")
    print("KEY FINDING:")
    print(f"{'-'*70}")

    if abs(high_N_result['avg_bias_pm']) < 0.10:
        print("  PM is UNBIASED for clustered distributions (bias < 10%)")
        print("  The L/3 artifact DOES NOT apply to strongly clustered HGBS-like filaments")
    elif high_N_result['avg_bias_pm'] > 0.10:
        bias_pct = high_N_result['avg_bias_pm'] * 100
        print(f"  PM shows POSITIVE BIAS of {bias_pct:.1f}% for clustered distributions")
        print("  PM systematically OVERESTIMATES the true fragmentation wavelength")
        if high_N_result['pm_converges_to_L3_fraction'] > 0.5:
            print(f"  PM converges toward L/3 = {L/3:.3f} pc (NOT λ_true = {lambda_true:.3f} pc)")

    if abs(high_N_result['avg_bias_nn']) < 0.05:
        print("  NN is UNBIASED (bias < 5%) and accurately recovers λ_true")
    else:
        bias_pct = high_N_result['avg_bias_nn'] * 100
        print(f"  NN shows bias of {bias_pct:.1f}%")

    print("="*70 + "\n")


def main():
    """
    Run full L/3 convergence test suite.
    """
    print("\n" + "="*70)
    print("L/3 CONVERGENCE ARTIFACT TEST")
    print("Injection-Recovery Monte Carlo Simulation")
    print("="*70)

    # Create output directory
    output_dir = Path('/Users/gjw255/astrodata/SWARM/ASTRA-dev-main/W3_HGBS_filaments/final_merged_paper')
    output_dir.mkdir(parents=True, exist_ok=True)

    # Test parameters (fiducial HGBS-like values)
    L = 2.0  # pc (typical filament length)
    lambda_true = 0.20  # pc (λ/W = 2.0, sub-Jeans but plausible)
    sigma_bead = 0.05  # pc (clustering scale)
    n_cores_per_bead = 20  # (typical bead richness)
    n_realizations = 200  # (per parameter point)

    print(f"\nRunning tests with parameters:")
    print(f"  Filament length L = {L} pc")
    print(f"  True wavelength λ_true = {lambda_true} pc")
    print(f"  Clustering scale σ = {sigma_bead} pc")
    print(f"  {n_realizations} realizations per parameter point")

    # Test 1: Uniform baseline (where L/3 is expected)
    print("\n[1/4] Running uniform distribution baseline test...")
    uniform_results = run_uniform_baseline(L, n_realizations)

    # Test 2: Convergence vs N
    print("[2/4] Running convergence vs sample size test...")
    convergence_results = run_convergence_test(L, lambda_true, sigma_bead, n_realizations)

    # Test 3: Clustering strength dependence
    print("[3/4] Running clustering strength test...")
    clustering_results = run_clustering_strength_test(L, lambda_true, n_cores_per_bead, n_realizations)

    # Test 4: Wavelength dependence
    print("[4/4] Running wavelength dependence test...")
    wavelength_results = run_wavelength_test(L, sigma_bead, n_cores_per_bead, n_realizations)

    # Save results to JSON
    all_results = {
        'parameters': {
            'L_pc': L,
            'lambda_true_pc': lambda_true,
            'sigma_bead_pc': sigma_bead,
            'n_cores_per_bead': n_cores_per_bead,
            'n_realizations': n_realizations
        },
        'uniform_baseline': uniform_results,
        'convergence_vs_N': convergence_results,
        'clustering_strength': clustering_results,
        'wavelength_dependence': wavelength_results
    }

    output_json = output_dir / 'l3_convergence_test_results.json'
    with open(output_json, 'w') as f:
        json.dump(all_results, f, indent=2)
    print(f"\nResults saved to {output_json}")

    # Create figures
    print("\nGenerating figures...")
    create_convergence_figure(convergence_results, clustering_results, wavelength_results, uniform_results, output_dir)
    create_bias_figure(convergence_results, clustering_results, wavelength_results, output_dir)

    # Print summary
    print_summary_statistics(convergence_results, clustering_results, wavelength_results, uniform_results, L, lambda_true)

    print("\nAll tests complete!")
    print(f"Output directory: {output_dir}")
    print(f"  - l3_convergence_test_results.json")
    print(f"  - l3_convergence_test.png/pdf")
    print(f"  - l3_bias_analysis.png/pdf")


if __name__ == '__main__':
    main()
