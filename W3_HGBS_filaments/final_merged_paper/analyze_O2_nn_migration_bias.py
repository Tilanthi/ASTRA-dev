#!/usr/bin/env python3
"""
O2: NN Migration Bias - Analytical Estimate

Models the effect of protostellar migration on NN spacing statistics.
Unlike PM (which averages over all pairwise distances), NN depends on
a single nearest neighbor and is therefore more sensitive to positional
perturbations.

Uses synthetic filament with known spacing to quantify NN bias under
different migration scenarios:
- Random migration: Δx uniformly distributed ±0.1 pc
- Inward migration: Protostars migrate toward fragment centers
- Outward migration: Protostars migrate away from fragment centers
"""

import numpy as np
import matplotlib.pyplot as plt
from scipy.spatial.distance import pdist, squareform

# Filament parameters
LAMBDA_TRUE = 0.4  # True fragmentation wavelength (pc)
WIDTH = 0.1  # Filament width (pc)
N_CORES = 50  # Number of cores in synthetic filament
F_PROTOSTELLAR = 0.3  # Fraction of protostellar cores (30%)
MIGRATION_AMPLITUDE = 0.1  # Typical migration distance (pc)
N_SIMULATIONS = 10000  # Monte Carlo iterations

# Generate synthetic filament with known spacing
def generate_synthetic_filament(n_cores, lambda_true, width):
    """
    Generate a synthetic filament with cores spaced by lambda_true.

    Returns: array of core positions (x, y)
    """
    # Place cores along x-axis with spacing lambda_true
    x_positions = np.arange(n_cores) * lambda_true

    # Add small random y-offsets (within filament width)
    y_positions = np.random.normal(0, width/4, n_cores)

    return np.column_stack([x_positions, y_positions])

# Calculate NN spacing statistic
def calculate_nn_spacing(positions):
    """
    Calculate nearest-neighbor spacing for a set of core positions.

    Returns: mean NN distance
    """
    # Calculate pairwise distances
    distances = squareform(pdist(positions))

    # For each core, find its nearest neighbor (exclude self)
    np.fill_diagonal(distances, np.inf)
    nn_distances = np.min(distances, axis=1)

    # Return mean NN distance
    return np.mean(nn_distances)

# Apply migration to protostellar cores
def apply_migration(positions, protostellar_mask, scenario, amplitude):
    """
    Apply positional migration to protostellar cores.

    Parameters:
    - positions: (n_cores, 2) array of core positions
    - protostellar_mask: boolean array indicating protostellar cores
    - scenario: 'random', 'inward', or 'outward'
    - amplitude: migration distance (pc)

    Returns: (n_cores, 2) array of migrated positions
    """
    migrated = positions.copy()

    if scenario == 'random':
        # Random migration in x-direction (along filament)
        delta_x = np.random.uniform(-amplitude, amplitude, size=np.sum(protostellar_mask))
        migrated[protostellar_mask, 0] += delta_x

    elif scenario == 'inward':
        # Inward migration: move toward nearest fragment center
        # Fragment centers are at multiples of lambda_true
        for i in np.where(protostellar_mask)[0]:
            x_pos = positions[i, 0]
            fragment_center = np.round(x_pos / LAMBDA_TRUE) * LAMBDA_TRUE
            direction = np.sign(fragment_center - x_pos)
            if direction == 0:
                direction = np.random.choice([-1, 1])
            migrated[i, 0] += direction * amplitude * np.random.uniform(0, 1)

    elif scenario == 'outward':
        # Outward migration: move away from nearest fragment center
        for i in np.where(protostellar_mask)[0]:
            x_pos = positions[i, 0]
            fragment_center = np.round(x_pos / LAMBDA_TRUE) * LAMBDA_TRUE
            direction = -np.sign(fragment_center - x_pos)
            if direction == 0:
                direction = np.random.choice([-1, 1])
            migrated[i, 0] += direction * amplitude * np.random.uniform(0, 1)

    return migrated

# Main analysis
def analyze_migration_bias():
    """
    Run Monte Carlo analysis of NN migration bias.
    """
    print("=" * 80)
    print("O2: NN Migration Bias Analysis")
    print("=" * 80)
    print()

    # Print parameters
    print("Parameters:")
    print(f"  True fragmentation wavelength: λ = {LAMBDA_TRUE} pc")
    print(f"  Filament width: W = {WIDTH} pc")
    print(f"  True λ/W ratio: {LAMBDA_TRUE/WIDTH:.2f}")
    print(f"  Number of cores: N = {N_CORES}")
    print(f"  Protostellar fraction: fₚ = {F_PROTOSTELLAR:.1%}")
    print(f"  Migration amplitude: Δx = {MIGRATION_AMPLITUDE} pc")
    print(f"  Monte Carlo iterations: {N_SIMULATIONS}")
    print()

    # Generate filament
    np.random.seed(42)
    positions = generate_synthetic_filament(N_CORES, LAMBDA_TRUE, WIDTH)

    # Calculate true NN spacing (no migration)
    nn_true = calculate_nn_spacing(positions)
    print(f"True NN spacing (no migration): {nn_true:.4f} pc")
    print()

    # Create protostellar mask
    protostellar_mask = np.random.rand(N_CORES) < F_PROTOSTELLAR
    n_protostellar = np.sum(protostellar_mask)
    print(f"Number of protostellar cores: {n_protostellar}/{N_CORES}")
    print()

    # Test scenarios
    scenarios = {
        'random': 'Random migration (Δx ~ ±0.1 pc)',
        'inward': 'Inward migration (toward fragment centers)',
        'outward': 'Outward migration (away from fragment centers)',
    }

    results = {}

    print("-" * 80)
    print("MONTE CARLO ANALYSIS")
    print("-" * 80)
    print()

    for scenario_key, scenario_name in scenarios.items():
        nn_biases = []
        nn_migrated_list = []

        for _ in range(N_SIMULATIONS):
            # Apply migration
            migrated = apply_migration(positions, protostellar_mask, scenario_key, MIGRATION_AMPLITUDE)

            # Calculate NN spacing after migration
            nn_migrated = calculate_nn_spacing(migrated)
            nn_migrated_list.append(nn_migrated)

            # Calculate bias
            bias = (nn_migrated - nn_true) / nn_true * 100  # Percentage
            nn_biases.append(bias)

        # Calculate statistics
        mean_bias = np.mean(nn_biases)
        std_bias = np.std(nn_biases)
        median_bias = np.median(nn_biases)
        p16 = np.percentile(nn_biases, 16)
        p84 = np.percentile(nn_biases, 84)

        mean_nn_migrated = np.mean(nn_migrated_list)

        print(f"{scenario_name}:")
        print(f"  Mean NN spacing after migration: {mean_nn_migrated:.4f} pc")
        print(f"  Mean bias: {mean_bias:+.2f}%")
        print(f"  Median bias: {median_bias:+.2f}%")
        print(f"  Std dev: {std_bias:.2f}%")
        print(f"  68% range: [{p16:+.1f}%, {p84:+.1f}%]")
        print()

        results[scenario_key] = {
            'mean_bias': mean_bias,
            'std_bias': std_bias,
            'median_bias': median_bias,
            'p16': p16,
            'p84': p84,
            'mean_nn_migrated': mean_nn_migrated,
        }

    # Compare to PM migration bias
    print("-" * 80)
    print("COMPARISON TO PM MIGRATION BIAS")
    print("-" * 80)
    print()

    pm_migration_bias = 7.5  # From paper: ~5-10% for PM
    print(f"PM migration bias (from paper): ~{pm_migration_bias:.1f}%")
    print()

    for scenario_key, scenario_name in scenarios.items():
        nn_bias = results[scenario_key]['mean_bias']
        ratio = nn_bias / pm_migration_bias if pm_migration_bias != 0 else 0
        print(f"{scenario_name}:")
        print(f"  NN bias: {nn_bias:+.2f}%")
        print(f"  NN/PM sensitivity ratio: {ratio:.1f}x")
        print()

    # Conservative systematic error
    print("=" * 80)
    print("SYSTEMATIC UNCERTAINTY RECOMMENDATION")
    print("=" * 80)
    print()

    # Find the scenario with the largest absolute bias
    max_bias_scenario = max(results.keys(), key=lambda k: abs(results[k]['mean_bias']))
    max_bias = results[max_bias_scenario]['mean_bias']
    max_abs_bias = max(results.keys(), key=lambda k: abs(results[k]['p84']))

    conservative_bias = results[max_abs_bias]['p84']
    conservative_bias_abs = abs(conservative_bias)

    print(f"Maximum mean bias: {max_bias:+.2f}% ({scenarios[max_bias_scenario]})")
    print(f"Conservative 84th percentile: {conservative_bias:+.2f}%")
    print()

    # Round to appropriate precision
    systematic_uncertainty = round(conservative_bias_abs)

    print(f"Recommended systematic uncertainty for NN migration bias:")
    print(f"  ±{systematic_uncertainty}%")
    print()

    print("Justification:")
    print(f"  - NN is {results[max_bias_scenario]['mean_bias']/pm_migration_bias:.1f}x more sensitive to")
    print(f"    migration than PM (which shows ~{pm_migration_bias:.0f}% bias)")
    print(f"  - Conservative estimate based on worst-case scenario")
    print(f"  - 84th percentile of Monte Carlo distribution")
    print()

    # Suggested text for paper
    print("=" * 80)
    print("SUGGESTED TEXT FOR PAPER")
    print("=" * 80)
    print()
    print("Section 3.2 (NN Methodology) - Add after current bias discussion:")
    print()
    print(r"\textbf{Protostellar migration bias in NN measurements.}")
    print()
    print("Unlike PM, which averages over all pairwise distances and shows only")
    print(f"~{pm_migration_bias:.0f}% sensitivity to protostellar migration (Section 3.3),")
    print("NN depends on a single nearest neighbor and is therefore more")
    print("vulnerable to positional perturbations. We estimate the NN migration")
    print("bias using synthetic filament models with known spacing")
    print(f"($\\lambda = {LAMBDA_TRUE}$ pc, $W = {WIDTH}$ pc), applying realistic")
    print(f"migration amplitudes ($\\Delta x = {MIGRATION_AMPLITUDE}$ pc) to the")
    print(f"protostellar fraction ($f_{{\\rm p}} = {F_PROTOSTELLAR:.0%}$).")
    print()

    # Find the scenario that produces bias closest to the conservative estimate
    bias_scenarios = []
    for scenario_key, scenario_name in scenarios.items():
        bias = results[scenario_key]['mean_bias']
        bias_scenarios.append((scenario_key, abs(bias)))

    bias_scenarios.sort(key=lambda x: x[1], reverse=True)

    print("For random migration, the NN spacing shows a systematic bias of")
    print(f"{results['random']['mean_bias']:+.1f}%, while inward migration toward fragment")
    print(f"centers produces {results['inward']['mean_bias']:+.1f}% bias. We conservatively")
    print(f"adopt a systematic uncertainty of $\\pm${systematic_uncertainty}% on the NN")
    print("spacing to account for migration effects, incorporated into the error")
    print("budget (Table 5).")
    print()

    # Save results to file
    print("Results saved to O2_nn_migration_bias_results.txt")
    with open('O2_nn_migration_bias_results.txt', 'w') as f:
        f.write("# O2: NN Migration Bias Analysis Results\n")
        f.write(f"\n")
        f.write(f"True NN spacing: {nn_true:.4f} pc\n")
        f.write(f"Protostellar fraction: {F_PROTOSTELLAR}\n")
        f.write(f"Migration amplitude: {MIGRATION_AMPLITUDE} pc\n")
        f.write(f"\n")

        for scenario_key, scenario_name in scenarios.items():
            f.write(f"{scenario_key}:\n")
            for stat, value in results[scenario_key].items():
                f.write(f"  {stat}: {value}\n")
            f.write(f"\n")

        f.write(f"Recommended systematic uncertainty: ±{systematic_uncertainty}%\n")

    return results, systematic_uncertainty

if __name__ == '__main__':
    results, systematic_uncertainty = analyze_migration_bias()
