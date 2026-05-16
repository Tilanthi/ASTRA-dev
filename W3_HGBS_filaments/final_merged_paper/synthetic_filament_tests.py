#!/usr/bin/env python3
"""
Synthetic Filament Generator for PM vs NN Analysis

Generates synthetic core catalogs for single filaments and multi-fiber bundles
with known fragmentation wavelengths to test which statistic correctly recovers
the true fragmentation scale.
"""

import numpy as np
from typing import Tuple, List, Dict
from dataclasses import dataclass
import json


@dataclass
class FilamentConfig:
    """Configuration for a single filament"""
    filament_length: float  # pc
    fragmentation_wavelength: float  # pc (λ)
    phase_offset: float  # Starting position (0-1)
    n_cores: int  # Number of cores to generate
    label: str  # Identifier


@dataclass
class MultiFilamentConfig:
    """Configuration for multi-fiber bundle"""
    n_fibers: int
    filament_length: float  # pc
    fragmentation_wavelength: float  # pc (same for all fibers)
    phase_spread: float  # Random phase variation between fibers
    spacing_spread: float  # Random spacing variation between fibers
    n_cores_per_fiber: int  # Target cores per fiber (approximate)
    label: str


class SyntheticFilamentGenerator:
    """Generate synthetic core catalogs for testing PM vs NN statistics"""

    def __init__(self, seed=42):
        """Initialize with random seed for reproducibility"""
        self.rng = np.random.RandomState(seed)

    def generate_single_filament(self, config: FilamentConfig) -> np.ndarray:
        """
        Generate core positions along a single filament.

        Parameters
        ----------
        config : FilamentConfig
            Filament configuration

        Returns
        -------
        positions : ndarray
            Array of core positions along filament (pc)
        """
        # Generate regularly spaced cores starting from phase_offset
        positions = np.zeros(config.n_cores)
        positions[0] = config.phase_offset * config.fragmentation_wavelength

        for i in range(1, config.n_cores):
            positions[i] = positions[i-1] + config.fragmentation_wavelength

        # Only keep cores within filament length
        positions = positions[positions < config.filament_length]

        return positions

    def generate_multi_fiber_bundle(self, config: MultiFilamentConfig) -> np.ndarray:
        """
        Generate core positions for a bundle of interwoven fibers.

        Each fiber fragments independently at the same wavelength but with
        random phase offsets and small spacing variations.

        Parameters
        ----------
        config : MultiFilamentConfig
            Multi-fiber configuration

        Returns
        -------
        positions : ndarray
            Combined core positions from all fibers, sorted
        """
        all_positions = []

        for fiber_idx in range(config.n_fibers):
            # Random phase offset for this fiber
            phase_offset = self.rng.uniform(0, 1) * config.phase_spread

            # Random spacing variation for this fiber (±10%)
            wavelength_variation = self.rng.uniform(
                1.0 - config.spacing_spread,
                1.0 + config.spacing_spread
            )
            actual_wavelength = config.fragmentation_wavelength * wavelength_variation

            # Generate positions for this fiber
            positions = []
            pos = phase_offset * actual_wavelength
            while pos < config.filament_length:
                positions.append(pos)
                pos += actual_wavelength

            all_positions.extend(positions)

        # Combine and sort all positions
        all_positions = np.array(all_positions)
        all_positions = np.sort(all_positions)

        return all_positions

    def compute_pairwise_median(self, positions: np.ndarray) -> float:
        """
        Compute pairwise median spacing statistic.

        For N cores, computes all N(N-1)/2 pairwise distances and returns the median.

        Parameters
        ----------
        positions : ndarray
            Sorted core positions along filament

        Returns
        -------
        pm_spacing : float
            Pairwise median spacing
        """
        n = len(positions)
        if n < 2:
            return np.nan

        # Compute all pairwise distances
        distances = []
        for i in range(n):
            for j in range(i+1, n):
                distances.append(positions[j] - positions[i])

        return np.median(distances)

    def compute_nearest_neighbor(self, positions: np.ndarray) -> float:
        """
        Compute nearest-neighbor (adjacent-core) spacing statistic.

        Computes median of distances between immediately adjacent cores.

        Parameters
        ----------
        positions : ndarray
            Sorted core positions along filament

        Returns
        -------
        nn_spacing : float
            Median nearest-neighbor spacing
        """
        if len(positions) < 2:
            return np.nan

        # Compute adjacent-core spacings
        spacings = np.diff(positions)
        return np.median(spacings)

    def analyze_synthetic_catalog(
        self,
        positions: np.ndarray,
        true_wavelength: float,
        label: str
    ) -> Dict:
        """
        Analyze synthetic catalog with both PM and NN statistics.

        Parameters
        ----------
        positions : ndarray
            Core positions
        true_wavelength : float
            True fragmentation wavelength (for single filament case)
        label : str
            Identifier for this catalog

        Returns
        -------
        results : dict
            Analysis results including PM, NN, NN/PM ratio, recovery metrics
        """
        pm = self.compute_pairwise_median(positions)
        nn = self.compute_nearest_neighbor(positions)
        n_cores = len(positions)
        filament_length = positions[-1] - positions[0] if len(positions) > 1 else 0

        # Avoid division by zero
        nn_pm_ratio = nn / pm if pm > 0 else np.nan

        # Recovery metrics (for single-filament case)
        pm_recovery = pm / true_wavelength if true_wavelength > 0 else np.nan
        nn_recovery = nn / true_wavelength if true_wavelength > 0 else np.nan

        # For PM: check if it's close to L/3 (filament_length / 3) which is the
        # theoretical convergence for uniform sampling
        expected_L_over_3 = filament_length / 3.0 if filament_length > 0 else np.nan
        pm_vs_L3 = pm / expected_L_over_3 if expected_L_over_3 > 0 else np.nan

        return {
            'label': label,
            'n_cores': n_cores,
            'filament_length': filament_length,
            'true_wavelength': true_wavelength,
            'pm_spacing': pm,
            'nn_spacing': nn,
            'nn_pm_ratio': nn_pm_ratio,
            'pm_recovers_true': np.isclose(pm_recovery, 1.0, atol=0.2),
            'nn_recovers_true': np.isclose(nn_recovery, 1.0, atol=0.2),
            'pm_recovery_ratio': pm_recovery,
            'nn_recovery_ratio': nn_recovery,
            'expected_L_over_3': expected_L_over_3,
            'pm_vs_L3_ratio': pm_vs_L3
        }


def test_single_filament_baseline():
    """
    Test baseline case: Single filament with known fragmentation wavelength.

    Expected: PM ≈ NN ≈ true wavelength (both statistics should recover true value)
    """
    print("=" * 70)
    print("TEST 1: Single Filament Baseline")
    print("=" * 70)

    gen = SyntheticFilamentGenerator(seed=42)

    # Test with λ = 0.4 pc (classical 4× for W = 0.1 pc)
    config = FilamentConfig(
        filament_length=10.0,  # pc
        fragmentation_wavelength=0.4,  # pc
        phase_offset=0.0,
        n_cores=30,
        label="single_filament_lambda_0.4"
    )

    positions = gen.generate_single_filament(config)
    results = gen.analyze_synthetic_catalog(
        positions,
        config.fragmentation_wavelength,
        config.label
    )

    print(f"\nConfiguration: Single filament, λ = {config.fragmentation_wavelength} pc")
    print(f"Number of cores: {results['n_cores']}")
    print(f"Filament length: {results['filament_length']:.2f} pc")
    print(f"PM spacing: {results['pm_spacing']:.4f} pc (recovery: {results['pm_recovery_ratio']:.2f}×)")
    print(f"NN spacing: {results['nn_spacing']:.4f} pc (recovery: {results['nn_recovery_ratio']:.2f}×)")
    print(f"NN/PM ratio: {results['nn_pm_ratio']:.4f}")
    print(f"Expected L/3: {results['expected_L_over_3']:.4f} pc")
    print(f"PM / (L/3): {results['pm_vs_L3_ratio']:.4f}")

    if results['pm_recovers_true'] and results['nn_recovers_true']:
        print("\n✓ PASS: Both PM and NN correctly recover true wavelength")
    else:
        print("\n✗ FAIL: Statistics do not recover true wavelength")

    return results


def test_multi_fiber_bundle():
    """
    Test multi-fiber bundle: Multiple interwoven fibers fragmenting independently.

    Expected: PM recovers filament-scale wavelength, NN measures inter-fiber gaps
    """
    print("\n" + "=" * 70)
    print("TEST 2: Multi-Fiber Bundle")
    print("=" * 70)

    gen = SyntheticFilamentGenerator(seed=42)

    # Test with 5 fibers, each with λ = 0.4 pc
    config = MultiFilamentConfig(
        n_fibers=5,
        filament_length=10.0,  # pc
        fragmentation_wavelength=0.4,  # pc (true fiber-scale wavelength)
        phase_spread=1.0,  # Full random phase spread
        spacing_spread=0.1,  # 10% spacing variation
        n_cores_per_fiber=25,
        label="multi_fiber_5fibers"
    )

    positions = gen.generate_multi_fiber_bundle(config)
    results = gen.analyze_synthetic_catalog(
        positions,
        config.fragmentation_wavelength,  # True fiber-scale wavelength
        config.label
    )

    print(f"\nConfiguration: {config.n_fibers} interwoven fibers, λ = {config.fragmentation_wavelength} pc")
    print(f"Number of cores: {results['n_cores']}")
    print(f"PM spacing: {results['pm_spacing']:.4f} pc (recovery: {results['pm_recovery_ratio']:.2f}×)")
    print(f"NN spacing: {results['nn_spacing']:.4f} pc (recovery: {results['nn_recovery_ratio']:.2f}×)")
    print(f"NN/PM ratio: {results['nn_pm_ratio']:.4f}")

    # Check if NN/PM ratio is in observed range (0.31-0.73)
    if 0.3 <= results['nn_pm_ratio'] <= 0.8:
        print(f"\n✓ INTERESTING: NN/PM = {results['nn_pm_ratio']:.3f} is in observed HGBS range (0.31-0.73)")
        print("  This supports the multi-fiber interpretation!")
    else:
        print(f"\n✗ NN/PM = {results['nn_pm_ratio']:.3f} is outside observed range")

    # Check if PM recovers true wavelength
    if results['pm_recovers_true']:
        print(f"✓ PM correctly recovers true fiber-scale wavelength ({results['pm_recovery_ratio']:.2f}×)")
    else:
        print(f"✗ PM does NOT recover true wavelength ({results['pm_recovery_ratio']:.2f}×)")

    return results


def test_hgbs_like_conditions():
    """
    Test with parameters similar to actual HGBS conditions.

    HGBS: PM ≈ 0.28 pc, W = 0.1 pc, so λ ≈ 0.28 pc for PM measurement
    This corresponds to fragmentation wavelength ~0.28 pc.
    """
    print("\n" + "=" * 70)
    print("TEST 3: HGBS-Like Conditions")
    print("=" * 70)

    gen = SyntheticFilamentGenerator(seed=42)

    # Test with λ = 0.28 pc (similar to HGBS PM values)
    config = FilamentConfig(
        filament_length=10.0,  # pc
        fragmentation_wavelength=0.28,  # pc (HGBS-like)
        phase_offset=0.0,
        n_cores=40,  # More cores for longer filament
        label="hgbs_like_single"
    )

    positions = gen.generate_single_filament(config)
    results = gen.analyze_synthetic_catalog(
        positions,
        config.fragmentation_wavelength,
        config.label
    )

    print(f"\nConfiguration: Single filament, λ = {config.fragmentation_wavelength} pc (HGBS-like)")
    print(f"Number of cores: {results['n_cores']}")
    print(f"Filament length: {results['filament_length']:.2f} pc")
    print(f"PM spacing: {results['pm_spacing']:.4f} pc (recovery: {results['pm_recovery_ratio']:.2f}×)")
    print(f"NN spacing: {results['nn_spacing']:.4f} pc (recovery: {results['nn_recovery_ratio']:.2f}×)")
    print(f"NN/PM ratio: {results['nn_pm_ratio']:.4f}")
    print(f"Expected L/3: {results['expected_L_over_3']:.4f} pc")
    print(f"PM / (L/3): {results['pm_vs_L3_ratio']:.4f}")

    print("\nKey insight: For single filaments:")
    print(f"  - NN correctly recovers λ (ratio: {results['nn_recovery_ratio']:.2f}×)")
    print(f"  - PM overestimates by {results['pm_recovery_ratio']:.2f}×")
    print(f"  - PM converges toward L/3 (ratio to L/3: {results['pm_vs_L3_ratio']:.2f}×)")
    print("\nThis suggests: PM measures filament-scale extent (L/3), not fragmentation wavelength!")

    return results


def parameter_sweep_n_fibers():
    """
    Sweep number of fibers to see effect on NN/PM ratio.

    HGBS observed range: NN/PM = 0.31-0.73
    """
    print("\n" + "=" * 70)
    print("PARAMETER SWEEP: Number of Fibers")
    print("=" * 70)

    gen = SyntheticFilamentGenerator(seed=42)

    results = []
    for n_fibers in [1, 2, 3, 5, 7, 10, 15]:
        # Use consistent random seed for each run
        gen = SyntheticFilamentGenerator(seed=42 + n_fibers)

        config = MultiFilamentConfig(
            n_fibers=n_fibers,
            filament_length=10.0,
            fragmentation_wavelength=0.4,
            phase_spread=1.0,
            spacing_spread=0.1,
            n_cores_per_fiber=25,
            label=f"{n_fibers}_fibers"
        )

        positions = gen.generate_multi_fiber_bundle(config)
        result = gen.analyze_synthetic_catalog(
            positions,
            config.fragmentation_wavelength,
            config.label
        )
        results.append(result)

    print(f"\n{'Fibers':<10} {'N_cores':<10} {'PM (pc)':<12} {'NN (pc)':<12} {'NN/PM':<10} {'PM rec.':<10}")
    print("-" * 70)

    for r in results:
        print(f"{r['label']:<10} {r['n_cores']:<10} {r['pm_spacing']:<12.4f} "
              f"{r['nn_spacing']:<12.4f} {r['nn_pm_ratio']:<10.4f} {r['pm_recovery_ratio']:<10.2f}×")

    # Find which n_fibers gives NN/PM in HGBS observed range
    print("\nFiber counts producing NN/PM in HGBS range (0.31-0.73):")
    for r in results:
        if 0.31 <= r['nn_pm_ratio'] <= 0.73:
            print(f"  ✓ {r['label']}: NN/PM = {r['nn_pm_ratio']:.3f}")

    return results


def main():
    """Run all synthetic filament tests"""
    print("\n" + "=" * 70)
    print("SYNTHETIC FILAMENT TESTS: PM vs NN DISCREPANCY")
    print("=" * 70)
    print("\nGoal: Determine which statistic correctly measures fragmentation wavelength")
    print("       by testing on synthetic catalogs with known ground truth.\n")

    # Test 1: Single filament baseline (λ = 0.4 pc)
    single_result = test_single_filament_baseline()

    # Test 2: Multi-fiber bundle (λ = 0.4 pc)
    multi_result = test_multi_fiber_bundle()

    # Test 3: HGBS-like conditions (λ = 0.28 pc)
    hgbs_result = test_hgbs_like_conditions()

    # Test 4: Parameter sweep
    sweep_results = parameter_sweep_n_fibers()

    # Save results
    all_results = {
        'single_filament_lambda_0.4': single_result,
        'multi_fiber_5fibers_lambda_0.4': multi_result,
        'hgbs_like_single': hgbs_result,
        'n_fibers_sweep': sweep_results
    }

    # Save results (convert numpy types to native Python)
    def convert_types(obj):
        if isinstance(obj, np.floating):
            return float(obj)
        elif isinstance(obj, np.integer):
            return int(obj)
        elif isinstance(obj, dict):
            return {k: convert_types(v) for k, v in obj.items()}
        elif isinstance(obj, list):
            return [convert_types(item) for item in obj]
        elif isinstance(obj, (bool, np.bool_)):
            return bool(obj)
        elif isinstance(obj, (str,)) or obj is None:
            return obj
        else:
            return str(obj)  # Fallback

    output_file = '/Users/gjw255/astrodata/SWARM/ASTRA-dev-main/W3_HGBS_filaments/final_merged_paper/synthetic_test_results.json'
    with open(output_file, 'w') as f:
        json.dump(convert_types(all_results), f, indent=2)

    print(f"\n{'=' * 70}")
    print(f"Results saved to: {output_file}")
    print("=" * 70)

    return all_results


if __name__ == '__main__':
    main()
