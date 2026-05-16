#!/usr/bin/env python3
"""
Multi-Filament PM Convergence Test

Tests what PM (pairwise median) converges to for realistic multi-filament regions,
as opposed to the single-filament case where PM converges to L/3.

Author: ASTRA Agent System
Date: 2026-05-03
"""

import numpy as np
from scipy import stats
import matplotlib.pyplot as plt
from typing import Dict, List, Tuple
import json
from pathlib import Path


class MultiFilamentRegionGenerator:
    """Generate synthetic multi-filament regions for PM convergence testing."""

    def __init__(self, n_filaments_range=(50, 200), length_range=(1.0, 15.0),
                 width_pc=0.1, lambda_true_range=(0.2, 0.4)):
        """
        Initialize generator.

        Parameters
        ----------
        n_filaments_range : tuple
            Range of number of filaments (min, max)
        length_range : tuple
            Range of filament lengths in pc (min, max)
        width_pc : float
            Filament width in pc
        lambda_true_range : tuple
            Range of true fragmentation wavelengths in pc (min, max)
        """
        self.n_filaments_range = n_filaments_range
        self.length_range = length_range
        self.width_pc = width_pc
        self.lambda_true_range = lambda_true_range

    def generate_region(self, n_filaments: int, length_dist: str = 'lognormal',
                        seed: int = None) -> Dict:
        """
        Generate a synthetic multi-filament region.

        Parameters
        ----------
        n_filaments : int
            Number of filaments to generate
        length_dist : str
            Distribution of filament lengths ('lognormal' or 'uniform')
        seed : int, optional
            Random seed

        Returns
        -------
        region : dict
            Dictionary containing:
            - filaments: list of filament data
            - all_cores: all core positions (pooled)
            - pm: pairwise median for the region
            - pm_theoretical: various theoretical predictions
        """
        if seed is not None:
            np.random.seed(seed)

        filaments = []
        all_coords = []

        # Generate filaments
        for i in range(n_filaments):
            # Draw filament length
            if length_dist == 'lognormal':
                # Log-normal with mean ~5 pc, sigma ~2 pc
                length_pc = np.random.lognormal(mean=np.log(5), sigma=0.5)
                length_pc = np.clip(length_pc, *self.length_range)
            else:
                length_pc = np.random.uniform(*self.length_range)

            # Draw true fragmentation wavelength
            lambda_true = np.random.uniform(*self.lambda_true_range)

            # Number of cores (Poisson with mean proportional to length)
            mean_cores = int(length_pc / lambda_true * 4)  # ~4 cores per wavelength
            n_cores = np.random.poisson(mean_cores)
            n_cores = max(n_cores, 2)  # At least 2 cores

            # Generate core positions along filament
            # Start position at x=0
            # Cores at positions: lambda_true, 2*lambda_true, 3*lambda_true, ...
            core_positions = np.arange(1, n_cores + 1) * lambda_true

            # Clip to filament length (cores near end may be cut off)
            core_positions = core_positions[core_positions < length_pc]

            if len(core_positions) < 2:
                continue  # Skip filaments with <2 cores

            filaments.append({
                'length_pc': length_pc,
                'lambda_true': lambda_true,
                'n_cores': len(core_positions),
                'positions': core_positions,
                'pm_filament': np.median([abs(i - j) for i in core_positions
                                               for j in core_positions])
            })

            all_coords.extend(core_positions.tolist())

        # Pool all cores and compute PM for region
        all_coords = np.array(all_coords)

        if len(all_coords) < 2:
            return None

        # Compute PM (pairwise median)
        all_distances = []
        for i in range(len(all_coords)):
            for j in range(i + 1, len(all_coords)):
                all_distances.append(abs(all_coords[i] - all_coords[j]))

        pm_region = np.median(all_distances)

        # Compute theoretical predictions
        lengths = np.array([f['length_pc'] for f in filaments])
        core_counts = np.array([f['n_cores'] for f in filaments])

        # Various possible "L/3" predictions:
        mean_L_over_3 = np.mean(lengths) / 3
        weighted_mean_L_over_3 = np.average(lengths, weights=core_counts) / 3
        median_L_over_3 = np.median(lengths) / 3

        # True fragmentation wavelength (should be recovered by NN, not PM)
        mean_lambda_true = np.mean([f['lambda_true'] for f in filaments])

        return {
            'n_filaments': len(filaments),
            'filaments': filaments,
            'n_cores_total': len(all_coords),
            'pm_region': pm_region,
            'pm_theoretical': {
                'mean_L_over_3': mean_L_over_3,
                'weighted_mean_L_over_3': weighted_mean_L_over_3,
                'median_L_over_3': median_L_over_3,
                'mean_lambda_true': mean_lambda_true
            }
        }


def run_convergence_test(n_realizations=100, n_filaments_list=None,
                          output_file='multifilament_pm_convergence_results.json'):
    """
    Run PM convergence test for multiple realizations.

    Parameters
    ----------
    n_realizations : int
        Number of synthetic region realizations
    n_filaments_list : list, optional
        List of filament counts to test (default: range 50-200)
    output_file : str
        Output file for results
    """
    if n_filaments_list is None:
        n_filaments_list = [50, 100, 150, 200]

    generator = MultiFilamentRegionGenerator()

    results = {
        'realizations': [],
        'summary_by_n_filaments': {}
    }

    print("="*70)
    print("MULTI-FILAMENT PM CONVERGENCE TEST")
    print("="*70)

    for n_fil in n_filaments_list:
        print(f"\nTesting {n_fil} filaments ({n_realizations} realizations)...")

        pm_ratios = []
        pm_biases = []

        for real_id in range(n_realizations):
            region = generator.generate_region(n_filaments=n_fil, seed=real_id)

            if region is None:
                continue

            pm = region['pm_region']
            mean_L3 = region['pm_theoretical']['mean_L_over_3']
            weighted_L3 = region['pm_theoretical']['weighted_mean_L_over_3']
            mean_lambda = region['pm_theoretical']['mean_lambda_true']

            # Compute ratios
            ratio_mean_L3 = pm / mean_L3 if mean_L3 > 0 else np.nan
            ratio_weighted_L3 = pm / weighted_L3 if weighted_L3 > 0 else np.nan
            bias_vs_lambda = pm / mean_lambda if mean_lambda > 0 else np.nan

            pm_ratios.append({
                'ratio_mean_L3': ratio_mean_L3,
                'ratio_weighted_L3': ratio_weighted_L3,
                'bias_vs_lambda': bias_vs_lambda,
                'pm': pm,
                'mean_L3': mean_L3,
                'weighted_L3': weighted_L3,
                'mean_lambda': mean_lambda
            })

            pm_biases.append(bias_vs_lambda)

        # Summary statistics for this n_filaments
        summary = {
            'n_filaments': n_fil,
            'mean_ratio_mean_L3': float(np.mean([r['ratio_mean_L3'] for r in pm_ratios])),
            'std_ratio_mean_L3': float(np.std([r['ratio_mean_L3'] for r in pm_ratios])),
            'mean_ratio_weighted_L3': float(np.mean([r['ratio_weighted_L3'] for r in pm_ratios])),
            'std_ratio_weighted_L3': float(np.std([r['ratio_weighted_L3'] for r in pm_ratios])),
            'mean_bias_vs_lambda': float(np.mean([r['bias_vs_lambda'] for r in pm_ratios])),
            'std_bias_vs_lambda': float(np.std([r['bias_vs_lambda'] for r in pm_ratios])),
            'median_pm': float(np.median([r['pm'] for r in pm_ratios])),
        }

        results['summary_by_n_filaments'][n_fil] = summary

        print(f"  PM / mean(L/3): {summary['mean_ratio_mean_L3']:.3f} ± {summary['std_ratio_mean_L3']:.3f}")
        print(f"  PM / weighted_mean(L/3): {summary['mean_ratio_weighted_L3']:.3f} ± {summary['std_ratio_weighted_L3']:.3f}")
        print(f"  PM / λ_true: {summary['mean_bias_vs_lambda']:.3f} ± {summary['std_bias_vs_lambda']:.3f}")

    results['realizations'] = pm_ratios

    # Save results
    with open(output_file, 'w') as f:
        json.dump(results, f, indent=2)

    print(f"\nResults saved to {output_file}")

    return results


def analyze_results(results_file='multifilament_pm_convergence_results.json'):
    """Analyze and plot results from convergence test."""
    with open(results_file, 'r') as f:
        results = json.load(f)

    print("\n" + "="*70)
    print("ANALYSIS OF RESULTS")
    print("="*70)

    print("\nKey findings:")
    print("-"*70)

    for n_fil, summary in results['summary_by_n_filaments'].items():
        print(f"\n{n_fil} filaments:")
        print(f"  PM / mean(L/3) = {summary['mean_ratio_mean_L3']:.3f} ± {summary['std_ratio_mean_L3']:.3f}")
        print(f"  PM / weighted_mean(L/3) = {summary['mean_ratio_weighted_L3']:.3f} ± {summary['std_ratio_weighted_L3']:.3f}")

        # Test if PM ≈ mean(L/3) (ratio close to 1)
        if abs(summary['mean_ratio_mean_L3'] - 1.0) < 0.1:
            print(f"  ✓ PM ≈ mean(L/3) (ratio within 10% of 1)")
        else:
            print(f"  ✗ PM ≠ mean(L/3) (ratio deviates from 1 by {abs(summary['mean_ratio_mean_L3'] - 1.0)*100:.1f}%)")

    # Interpretation
    print("\n" + "="*70)
    print("INTERPRETATION")
    print("="*70)

    all_ratios_mean_L3 = [s['mean_ratio_mean_L3'] for s in results['summary_by_n_filaments'].values()]
    all_ratios_weighted_L3 = [s['mean_ratio_weighted_L3'] for s in results['summary_by_n_filaments'].values()]

    mean_ratio = np.mean(all_ratios_mean_L3)
    std_ratio = np.std(all_ratios_mean_L3)

    print(f"\nAcross all filament counts tested:")
    print(f"  Mean PM / mean(L/3) = {mean_ratio:.3f} ± {std_ratio:.3f}")

    if abs(mean_ratio - 1.0) < 0.2:
        print(f"\n  ✓ PM approximately equals mean(L/3) for multi-filament regions")
        print(f"    This supports the L/3 interpretation for HGBS-like regions")
    elif abs(mean_ratio - 1.0) < 0.5:
        print(f"\n  ~ PM roughly equals mean(L/3) but with significant scatter")
        print(f"    This partially supports the L/3 interpretation but with caveats")
    else:
        print(f"\n  ✗ PM does NOT equal mean(L/3) for multi-filament regions")
        print(f"    The L/3 interpretation from single-filament tests does NOT generalize")
        print(f"    The paper must be revised to reflect this fundamental limitation")


if __name__ == '__main__':
    import sys

    # Run test
    n_realizations = int(sys.argv[1]) if len(sys.argv) > 1 else 50
    print(f"Running {n_realizations} realizations per filament count...")

    results = run_convergence_test(n_realizations=n_realizations)

    # Analyze results
    analyze_results()
