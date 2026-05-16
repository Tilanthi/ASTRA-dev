#!/usr/bin/env python3
"""
Forward modelling of PM-NN discrepancy in multi-filament systems.

This script generates synthetic multi-filament systems with known
fragmentation wavelength and applies both PM and NN statistics to
quantitatively test whether geometric complexity can explain the
observed 40-50% PM-NN difference.

Author: ASTRA-dev
Date: 2026-05-08
"""

import numpy as np
from scipy.spatial import cKDTree
from scipy.cluster.hierarchy import linkage, fcluster
from scipy.spatial.distance import pdist, squareform
from sklearn.decomposition import PCA
import json
import matplotlib.pyplot as plt
from matplotlib import rcParams
import os
from datetime import datetime

# Set up matplotlib for publication-quality figures
rcParams.update({
    'font.size': 11,
    'font.family': 'serif',
    'axes.linewidth': 1.0,
    'xtick.major.width': 1.0,
    'ytick.major.width': 1.0,
    'figure.figsize': (8, 6),
    'figure.dpi': 150,
})

class MultiFilamentForwardModel:
    """
    Generate synthetic multi-filament systems and compute PM/NN ratios.
    """

    def __init__(self, L=5.0, W=0.1, lambda_true=0.20, n_filaments=3,
                 d_filament_ratio=1.0, phase_coherence='random',
                 sigma_scatter=0.05, seed=None):
        """
        Initialize forward model parameters.

        Parameters
        ----------
        L : float
            Filament length (pc)
        W : float
            Filament width (pc)
        lambda_true : float
            True fragmentation wavelength (pc)
        n_filaments : int
            Number of parallel filaments
        d_filament_ratio : float
            Inter-filament spacing as ratio to lambda_true
        phase_coherence : str
            'coherent', 'random', or 'semi-coherent'
        sigma_scatter : float
            Gaussian scatter around bead positions (pc)
        seed : int or None
            Random seed for reproducibility
        """
        self.L = L
        self.W = W
        self.lambda_true = lambda_true
        self.n_filaments = n_filaments
        self.d_filament = d_filament_ratio * lambda_true
        self.phase_coherence = phase_coherence
        self.sigma_scatter = sigma_scatter
        self.seed = seed

        if seed is not None:
            np.random.seed(seed)

        # Derived parameters
        self.n_beads_per_filament = int(L / lambda_true) + 1
        self.total_filament_width = (n_filaments - 1) * self.d_filament

        # Storage
        self.cores = None
        self.pm_spacing = None
        self.nn_spacing = None
        self.pm_nn_ratio = None

    def generate_filament_system(self):
        """
        Generate synthetic multi-filament system with beading.
        """
        cores = []

        # Generate each filament
        for i in range(self.n_filaments):
            # Filament center position (perpendicular to filament axis)
            y_center = (i - (self.n_filaments - 1) / 2) * self.d_filament

            # Phase offset for this filament
            if self.phase_coherence == 'coherent':
                phase_offset = 0.0
            elif self.phase_coherence == 'random':
                phase_offset = np.random.uniform(0, self.lambda_true)
            elif self.phase_coherence == 'semi-coherent':
                # Semi-coherent: partial phase alignment with some jitter
                phase_offset = np.random.normal(0, 0.2 * self.lambda_true)

            # Generate beads along this filament
            for j in range(self.n_beads_per_filament):
                # Position along filament (x-axis)
                x = j * self.lambda_true + phase_offset

                # Only include if within filament length
                if 0 <= x <= self.L:
                    # Add scatter
                    x_scatter = np.random.normal(0, self.sigma_scatter)
                    y_scatter = np.random.normal(0, self.sigma_scatter)

                    cores.append({
                        'x': x + x_scatter,
                        'y': y_center + y_scatter,
                        'filament_id': i,
                        'bead_id': j
                    })

        # Convert to numpy array
        self.cores = np.array([[c['x'], c['y']] for c in cores])
        return self.cores

    def compute_pm_spacing(self):
        """
        Compute pairwise median (PM) spacing.
        """
        if self.cores is None:
            self.generate_filament_system()

        n_cores = len(self.cores)

        # Compute all pairwise distances
        distances = []
        for i in range(n_cores):
            for j in range(i + 1, n_cores):
                dist = np.linalg.norm(self.cores[i] - self.cores[j])
                distances.append(dist)

        # PM is the median of all pairwise distances
        self.pm_spacing = np.median(distances)
        return self.pm_spacing

    def compute_nn_spacing_filament_projected(self):
        """
        Compute filament-projected nearest-neighbor (NN) spacing.

        This mimics the methodology used in the paper:
        1. Associate cores with filament skeletons
        2. Cluster into filament groups
        3. Project along filament axis using PCA
        4. Compute adjacent-core spacings
        """
        if self.cores is None:
            self.generate_filament_system()

        # For synthetic systems, we know the true filament assignment
        # But to mimic the paper's methodology, we use clustering

        # Step 1: Hierarchical clustering to identify filament groups
        # Use distance threshold based on inter-filament spacing
        clustering_threshold = self.d_filament * 0.6  # Slightly less than inter-filament spacing

        # Compute pairwise distances
        dist_matrix = squareform(pdist(self.cores))

        # Hierarchical clustering
        Z = linkage(dist_matrix, method='single')
        cluster_labels = fcluster(Z, t=clustering_threshold, criterion='distance')

        # Step 2: For each filament group, compute NN spacings
        nn_spacings = []

        for cluster_id in np.unique(cluster_labels):
            # Get cores in this cluster
            cluster_cores = self.cores[cluster_labels == cluster_id]

            if len(cluster_cores) < 2:
                continue

            # Step 3: Project along principal axis (filament direction)
            pca = PCA(n_components=2)
            pca.fit(cluster_cores)
            principal_axis = pca.components_[0]

            # Project cores onto principal axis
            projections = cluster_cores.dot(principal_axis)

            # Sort by projection
            projections_sorted = np.sort(projections)

            # Step 4: Compute adjacent-core spacings
            adjacent_spacings = np.diff(projections_sorted)
            nn_spacings.extend(adjacent_spacings.tolist())

        if len(nn_spacings) == 0:
            self.nn_spacing = np.nan
        else:
            self.nn_spacing = np.median(nn_spacings)

        return self.nn_spacing

    def compute_pm_nn_ratio(self):
        """
        Compute PM/NN ratio for this system.
        """
        if self.pm_spacing is None:
            self.compute_pm_spacing()
        if self.nn_spacing is None:
            self.compute_nn_spacing_filament_projected()

        if self.nn_spacing is None or np.isnan(self.nn_spacing):
            self.pm_nn_ratio = np.nan
        else:
            self.pm_nn_ratio = self.pm_spacing / self.nn_spacing

        return self.pm_nn_ratio


def run_parameter_sweep():
    """
    Run comprehensive parameter sweep across multi-filament space.

    Parameter space:
    - n_filaments: [1, 2, 3, 5, 7, 10]
    - d_filament_ratio: [0.5, 1.0, 2.0, 5.0]
    - sigma_scatter_ratio: [0.05, 0.1, 0.2, 0.3] (relative to lambda_true)
    - phase_coherence: ['coherent', 'random', 'semi-coherent']
    - n_realizations: 50 per parameter point (reduced from 100 for speed)

    Total: 6 * 4 * 4 * 3 * 50 = 14,400 realizations
    """
    print("=" * 80)
    print("FORWARD MODELLING: PM-NN DISCREPANCY IN MULTI-FILAMENT SYSTEMS")
    print("=" * 80)
    print(f"Start time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

    # Fixed HGBS-like parameters
    L = 5.0  # pc (typical HGBS filament length)
    W = 0.1  # pc (HGBS characteristic width)
    lambda_true = 0.20  # pc (true fragmentation wavelength)

    # Parameter ranges
    n_filaments_list = [1, 2, 3, 5, 7, 10]
    d_filament_ratio_list = [0.5, 1.0, 2.0, 5.0]
    sigma_scatter_ratio_list = [0.25, 0.5, 1.0, 1.5]  # relative to lambda_true
    phase_coherence_list = ['coherent', 'random', 'semi-coherent']
    n_realizations = 50

    # Results storage
    results = []
    total_sims = (len(n_filaments_list) * len(d_filament_ratio_list) *
                  len(sigma_scatter_ratio_list) * len(phase_coherence_list) *
                  n_realizations)

    sim_count = 0

    for n_filaments in n_filaments_list:
        for d_filament_ratio in d_filament_ratio_list:
            for sigma_scatter_ratio in sigma_scatter_ratio_list:
                for phase_coherence in phase_coherence_list:
                    for realization in range(n_realizations):
                        sim_count += 1

                        if sim_count % 1000 == 0:
                            print(f"Progress: {sim_count}/{total_sims} ({100*sim_count/total_sims:.1f}%)")

                        # Create model
                        sigma_scatter = sigma_scatter_ratio * lambda_true
                        seed = sim_count  # Unique seed for each realization

                        model = MultiFilamentForwardModel(
                            L=L, W=W, lambda_true=lambda_true,
                            n_filaments=n_filaments,
                            d_filament_ratio=d_filament_ratio,
                            phase_coherence=phase_coherence,
                            sigma_scatter=sigma_scatter,
                            seed=seed
                        )

                        # Generate system and compute statistics
                        model.generate_filament_system()
                        pm = model.compute_pm_spacing()
                        nn = model.compute_nn_spacing_filament_projected()

                        if nn is not None and not np.isnan(nn):
                            ratio = pm / nn
                        else:
                            ratio = np.nan

                        # Store result
                        results.append({
                            'n_filaments': n_filaments,
                            'd_filament_ratio': d_filament_ratio,
                            'sigma_scatter_ratio': sigma_scatter_ratio,
                            'phase_coherence': phase_coherence,
                            'realization': realization,
                            'pm_spacing': pm,
                            'nn_spacing': nn,
                            'pm_nn_ratio': ratio,
                            'pm_bias_pct': (pm - lambda_true) / lambda_true * 100,
                            'nn_bias_pct': (nn - lambda_true) / lambda_true * 100 if nn else np.nan,
                        })

    print(f"Completed {sim_count} simulations")

    # Save results
    results_file = 'forward_model_pm_nn_results.json'
    with open(results_file, 'w') as f:
        json.dump(results, f, indent=2)

    print(f"Results saved to {results_file}")

    return results


def analyze_results(results):
    """
    Analyze forward modelling results and generate figures.
    """
    print("\n" + "=" * 80)
    print("ANALYZING RESULTS")
    print("=" * 80)

    import pandas as pd

    df = pd.DataFrame(results)

    # Filter out NaN values
    df_valid = df.dropna(subset=['pm_nn_ratio'])

    print(f"\nValid simulations: {len(df_valid)} / {len(df)}")

    # Summary statistics
    print("\nPM/NN Ratio Statistics:")
    print(f"  Mean: {df_valid['pm_nn_ratio'].mean():.3f}")
    print(f"  Median: {df_valid['pm_nn_ratio'].median():.3f}")
    print(f"  Std: {df_valid['pm_nn_ratio'].std():.3f}")
    print(f"  Min: {df_valid['pm_nn_ratio'].min():.3f}")
    print(f"  Max: {df_valid['pm_nn_ratio'].max():.3f}")

    # Key question: What fraction of simulations produce PM/NN ≈ 1.4-1.5?
    target_range = (1.35, 1.55)
    in_range = df_valid[(df_valid['pm_nn_ratio'] >= target_range[0]) &
                        (df_valid['pm_nn_ratio'] <= target_range[1])]
    print(f"\nFraction with PM/NN in {target_range}: {len(in_range) / len(df_valid) * 100:.1f}%")

    # Analysis by number of filaments
    print("\nPM/NN Ratio by Number of Filaments:")
    for n_fil in sorted(df_valid['n_filaments'].unique()):
        subset = df_valid[df_valid['n_filaments'] == n_fil]
        print(f"  N={n_fil:2d}: mean={subset['pm_nn_ratio'].mean():.3f}, "
              f"median={subset['pm_nn_ratio'].median():.3f}, "
              f"std={subset['pm_nn_ratio'].std():.3f}, n={len(subset)}")

    # Single filament control case
    single_fil = df_valid[df_valid['n_filaments'] == 1]
    print(f"\nSingle-filament control: PM/NN = {single_fil['pm_nn_ratio'].mean():.3f} ± "
          f"{single_fil['pm_nn_ratio'].std():.3f}")

    # NN bias analysis
    print("\nNN Bias (should be ~0%):")
    print(f"  Mean: {df_valid['nn_bias_pct'].mean():.1f}%")
    print(f"  Median: {df_valid['nn_bias_pct'].median():.1f}%")

    # Create figures
    create_analysis_figures(df_valid)

    return df_valid


def create_analysis_figures(df):
    """
    Create publication-quality figures from forward modelling results.
    """
    output_dir = 'figures'
    os.makedirs(output_dir, exist_ok=True)

    # Figure 1: PM/NN ratio vs number of filaments
    fig, axes = plt.subplots(2, 2, figsize=(12, 10))

    # Panel A: PM/NN ratio vs n_filaments
    ax = axes[0, 0]
    n_fil_values = sorted(df['n_filaments'].unique())
    mean_ratios = [df[df['n_filaments'] == n]['pm_nn_ratio'].mean() for n in n_fil_values]
    std_ratios = [df[df['n_filaments'] == n]['pm_nn_ratio'].std() for n in n_fil_values]

    ax.errorbar(n_fil_values, mean_ratios, yerr=std_ratios,
                fmt='o-', capsize=5, linewidth=2, markersize=8, color='steelblue')
    ax.axhline(y=1.45, color='red', linestyle='--', linewidth=2,
               label='Observed (1.45)')
    ax.axhline(y=1.0, color='gray', linestyle=':', linewidth=1.5,
               label='Single filament (1.0)')
    ax.set_xlabel('Number of Filaments', fontsize=12)
    ax.set_ylabel('PM / NN Ratio', fontsize=12)
    ax.set_title('A. PM/NN Ratio vs. Number of Filaments', fontsize=13, fontweight='bold')
    ax.legend(fontsize=10)
    ax.grid(True, alpha=0.3)
    ax.set_ylim([0.8, 2.5])

    # Panel B: PM/NN ratio vs inter-filament spacing
    ax = axes[0, 1]
    d_values = sorted(df['d_filament_ratio'].unique())
    mean_ratios = [df[df['d_filament_ratio'] == d]['pm_nn_ratio'].mean() for d in d_values]
    std_ratios = [df[df['d_filament_ratio'] == d]['pm_nn_ratio'].std() for d in d_values]

    ax.errorbar(d_values, mean_ratios, yerr=std_ratios,
                fmt='s-', capsize=5, linewidth=2, markersize=8, color='forestgreen')
    ax.axhline(y=1.45, color='red', linestyle='--', linewidth=2, label='Observed (1.45)')
    ax.axhline(y=1.0, color='gray', linestyle=':', linewidth=1.5, label='Single filament (1.0)')
    ax.set_xlabel('Inter-Filament Spacing / $\lambda_{true}$', fontsize=12)
    ax.set_ylabel('PM / NN Ratio', fontsize=12)
    ax.set_title('B. PM/NN Ratio vs. Inter-Filament Spacing', fontsize=13, fontweight='bold')
    ax.legend(fontsize=10)
    ax.grid(True, alpha=0.3)
    ax.set_ylim([0.8, 2.5])
    ax.set_xscale('log')

    # Panel C: PM/NN ratio vs position scatter
    ax = axes[1, 0]
    sigma_values = sorted(df['sigma_scatter_ratio'].unique())
    mean_ratios = [df[df['sigma_scatter_ratio'] == s]['pm_nn_ratio'].mean() for s in sigma_values]
    std_ratios = [df[df['sigma_scatter_ratio'] == s]['pm_nn_ratio'].std() for s in sigma_values]

    ax.errorbar(sigma_values, mean_ratios, yerr=std_ratios,
                fmt='^-', capsize=5, linewidth=2, markersize=8, color='darkorange')
    ax.axhline(y=1.45, color='red', linestyle='--', linewidth=2, label='Observed (1.45)')
    ax.axhline(y=1.0, color='gray', linestyle=':', linewidth=1.5, label='Single filament (1.0)')
    ax.set_xlabel('Position Scatter / $\lambda_{true}$', fontsize=12)
    ax.set_ylabel('PM / NN Ratio', fontsize=12)
    ax.set_title('C. PM/NN Ratio vs. Position Scatter', fontsize=13, fontweight='bold')
    ax.legend(fontsize=10)
    ax.grid(True, alpha=0.3)
    ax.set_ylim([0.8, 2.5])

    # Panel D: 2D histogram of PM/NN ratio
    ax = axes[1, 1]
    # Create 2D histogram: n_filaments vs d_filament_ratio, color = pm_nn_ratio
    n_fil_vals = sorted(df['n_filaments'].unique())
    d_vals = sorted(df['d_filament_ratio'].unique())

    # Create a 2D array of mean PM/NN ratios
    ratio_grid = np.zeros((len(d_vals), len(n_fil_vals)))
    for i, d in enumerate(d_vals):
        for j, n in enumerate(n_fil_vals):
            subset = df[(df['d_filament_ratio'] == d) & (df['n_filaments'] == n)]
            if len(subset) > 0:
                ratio_grid[i, j] = subset['pm_nn_ratio'].mean()

    im = ax.imshow(ratio_grid, aspect='auto', origin='lower',
                   extent=[n_fil_vals[0]-0.5, n_fil_vals[-1]+0.5,
                           d_vals[0]*0.8, d_vals[-1]*1.2],
                   cmap='RdYlBu_r', vmin=0.9, vmax=2.0)
    ax.set_xlabel('Number of Filaments', fontsize=12)
    ax.set_ylabel('Inter-Filament Spacing / $\lambda_{true}$', fontsize=12)
    ax.set_title('D. PM/NN Ratio Phase Diagram', fontsize=13, fontweight='bold')
    ax.set_xticks(n_fil_vals)
    cbar = plt.colorbar(im, ax=ax)
    cbar.set_label('PM / NN Ratio', fontsize=11)

    # Add observed contour
    ax.contour(n_fil_vals, d_vals, ratio_grid, levels=[1.45], colors='red', linewidths=3)

    plt.tight_layout()
    plt.savefig(os.path.join(output_dir, 'forward_model_pm_nn_analysis.pdf'), dpi=300, bbox_inches='tight')
    plt.savefig(os.path.join(output_dir, 'forward_model_pm_nn_analysis.png'), dpi=300, bbox_inches='tight')
    print(f"\nFigure saved: {output_dir}/forward_model_pm_nn_analysis.pdf")

    # Figure 2: PM and NN bias comparison
    fig, axes = plt.subplots(1, 2, figsize=(12, 5))

    # Left: PM bias
    ax = axes[0]
    n_fil_values = sorted(df['n_filaments'].unique())
    pm_bias_means = [df[df['n_filaments'] == n]['pm_bias_pct'].mean() for n in n_fil_values]
    pm_bias_stds = [df[df['n_filaments'] == n]['pm_bias_pct'].std() for n in n_fil_values]

    ax.errorbar(n_fil_values, pm_bias_means, yerr=pm_bias_stds,
                fmt='o-', capsize=5, linewidth=2, markersize=8, color='crimson')
    ax.axhline(y=0, color='gray', linestyle='--', linewidth=1.5)
    ax.set_xlabel('Number of Filaments', fontsize=12)
    ax.set_ylabel('PM Bias (%)', fontsize=12)
    ax.set_title('PM Bias vs. Number of Filaments', fontsize=13, fontweight='bold')
    ax.grid(True, alpha=0.3)

    # Right: NN bias
    ax = axes[1]
    nn_bias_means = [df[df['n_filaments'] == n]['nn_bias_pct'].mean() for n in n_fil_values]
    nn_bias_stds = [df[df['n_filaments'] == n]['nn_bias_pct'].std() for n in n_fil_values]

    ax.errorbar(n_fil_values, nn_bias_means, yerr=nn_bias_stds,
                fmt='s-', capsize=5, linewidth=2, markersize=8, color='royalblue')
    ax.axhline(y=0, color='gray', linestyle='--', linewidth=1.5)
    ax.set_xlabel('Number of Filaments', fontsize=12)
    ax.set_ylabel('NN Bias (%)', fontsize=12)
    ax.set_title('NN Bias vs. Number of Filaments', fontsize=13, fontweight='bold')
    ax.grid(True, alpha=0.3)

    plt.tight_layout()
    plt.savefig(os.path.join(output_dir, 'forward_model_bias_analysis.pdf'), dpi=300, bbox_inches='tight')
    print(f"Figure saved: {output_dir}/forward_model_bias_analysis.pdf")


def generate_summary_report(df):
    """
    Generate a summary report of key findings.
    """
    report = []
    report.append("# Forward Modelling: PM-NN Discrepancy Analysis")
    report.append(f"\nGenerated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    report.append("\n## Summary Statistics")

    # Overall statistics
    report.append(f"\n**Total simulations**: {len(df)}")
    report.append(f"**PM/NN ratio**: {df['pm_nn_ratio'].mean():.3f} ± {df['pm_nn_ratio'].std():.3f} (mean ± std)")
    report.append(f"**PM/NN ratio**: {df['pm_nn_ratio'].median():.3f} (median)")
    report.append(f"**Range**: {df['pm_nn_ratio'].min():.3f} - {df['pm_nn_ratio'].max():.3f}")

    # Target range analysis
    target_range = (1.35, 1.55)
    in_range = df[(df['pm_nn_ratio'] >= target_range[0]) &
                  (df['pm_nn_ratio'] <= target_range[1])]
    report.append(f"\n**Fraction matching observed 40-50% discrepancy** (PM/NN = 1.35-1.55):")
    report.append(f"  {len(in_range)} / {len(df)} = {len(in_range)/len(df)*100:.1f}%")

    # Single filament control
    single_fil = df[df['n_filaments'] == 1]
    report.append(f"\n**Single-filament control** (should have PM/NN ≈ 1.0):")
    report.append(f"  PM/NN = {single_fil['pm_nn_ratio'].mean():.3f} ± {single_fil['pm_nn_ratio'].std():.3f}")

    # Multi-filament results
    report.append(f"\n**Multi-filament systems** (N ≥ 3):")
    multi_fil = df[df['n_filaments'] >= 3]
    report.append(f"  PM/NN = {multi_fil['pm_nn_ratio'].mean():.3f} ± {multi_fil['pm_nn_ratio'].std():.3f}")

    # NN bias
    report.append(f"\n**NN bias** (should be ≈ 0% if NN is unbiased):")
    report.append(f"  Mean bias: {df['nn_bias_pct'].mean():.1f}%")
    report.append(f"  Median bias: {df['nn_bias_pct'].median():.1f}%")

    # Key conclusion
    report.append(f"\n## Key Findings")

    if multi_fil['pm_nn_ratio'].mean() >= 1.35 and multi_fil['pm_nn_ratio'].mean() <= 1.55:
        report.append(f"\n✅ **Multi-filament systems produce PM/NN ratios consistent with the observed 40-50% discrepancy**.")
        report.append(f"   - Mean PM/NN for N ≥ 3: {multi_fil['pm_nn_ratio'].mean():.3f}")
        report.append(f"   - This matches the observed HGBS value of ~1.45")
    else:
        report.append(f"\n⚠️ **Multi-filament systems do NOT fully reproduce the observed discrepancy**.")
        report.append(f"   - Mean PM/NN for N ≥ 3: {multi_fil['pm_nn_ratio'].mean():.3f}")
        report.append(f"   - Observed HGBS value: ~1.45")
        report.append(f"   - Difference: {abs(multi_fil['pm_nn_ratio'].mean() - 1.45):.3f}")

    if abs(df['nn_bias_pct'].mean()) < 10:
        report.append(f"\n✅ **NN is statistically unbiased** (bias < 10%).")
    else:
        report.append(f"\n⚠️ **NN shows non-negligible bias** ({df['nn_bias_pct'].mean():.1f}%).")

    report_text = "\n".join(report)

    # Save report
    with open('FORWARD_MODEL_SUMMARY.md', 'w') as f:
        f.write(report_text)

    print(report_text)
    print(f"\nReport saved to: FORWARD_MODEL_SUMMARY.md")

    return report_text


if __name__ == "__main__":
    # Run parameter sweep
    results = run_parameter_sweep()

    # Analyze results
    df = analyze_results(results)

    # Generate summary report
    generate_summary_report(df)

    print("\n" + "=" * 80)
    print("FORWARD MODELLING COMPLETE")
    print("=" * 80)
    print(f"End time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
