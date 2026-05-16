#!/usr/bin/env python3
"""
Compute corrected nearest-neighbor spacing using L-dependent bias factors.

Campaign 10 showed that the pairwise median bias depends strongly on filament
length L. This script uses the empirically measured bias factors from periodic
beading tests to correct each HGBS region individually.
"""

import numpy as np
import json

# HGBS regions with Gaia DR3 distances and estimated filament lengths
HGBS_REGIONS = {
    'Taurus': {
        'distance': 135,
        'n_cores': 536,
        'pairwise_median_pc': 0.198,
        'filament_length_L': 8.5,  # pc, typical for Taurus filaments
        'robust': True,
    },
    'OrionB': {
        'distance': 386,
        'n_cores': 1844,
        'pairwise_median_pc': 0.313,
        'filament_length_L': 12.0,  # pc, Orion B has long filaments
        'robust': True,
    },
    'Aquila': {
        'distance': 436,
        'n_cores': 749,
        'pairwise_median_pc': 0.346,
        'filament_length_L': 10.0,  # pc
        'robust': True,
    },
    'Perseus': {
        'distance': 296,
        'n_cores': 816,
        'pairwise_median_pc': 0.248,
        'filament_length_L': 9.0,  # pc
        'robust': True,
    },
    'Ophiuchus': {
        'distance': 137,
        'n_cores': 513,
        'pairwise_median_pc': 0.206,
        'filament_length_L': 7.0,  # pc, smaller region
        'robust': False,
    },
    'Serpens': {
        'distance': 458,
        'n_cores': 194,
        'pairwise_median_pc': 0.308,
        'filament_length_L': 6.0,  # pc, compact region
        'robust': False,
    },
    'TMC1': {
        'distance': 135,
        'n_cores': 178,
        'pairwise_median_pc': 0.233,
        'filament_length_L': 5.0,  # pc, small filament
        'robust': False,
    },
    'CRA': {
        'distance': 150,
        'n_cores': 239,
        'pairwise_median_pc': 0.204,
        'filament_length_L': 6.0,  # pc
        'robust': False,
    },
}

# L-dependent bias factors from Campaign 10 periodic beading tests
# Format: L_pc: bias_factor
L_DEPENDENT_BIAS = {
    5.0: 4.00,
    6.0: 5.01,
    7.0: 6.01,
    8.5: 7.93,
    9.0: 8.02,
    10.0: 9.00,
    12.0: 11.01,
}

def get_bias_factor(L):
    """Get bias factor for a given filament length L."""
    if L in L_DEPENDENT_BIAS:
        return L_DEPENDENT_BIAS[L]
    # Linear interpolation for intermediate values
    L_values = sorted(L_DEPENDENT_BIAS.keys())
    for i in range(len(L_values) - 1):
        if L_values[i] <= L <= L_values[i+1]:
            L1, L2 = L_values[i], L_values[i+1]
            b1, b2 = L_DEPENDENT_BIAS[L1], L_DEPENDENT_BIAS[L2]
            # Interpolate
            frac = (L - L1) / (L2 - L1)
            return b1 + frac * (b2 - b1)
    # Extrapolation for out-of-range values
    if L < L_values[0]:
        return L_DEPENDENT_BIAS[L_values[0]] * (L / L_values[0])
    if L > L_values[-1]:
        return L_DEPENDENT_BIAS[L_values[-1]] * (L / L_values[-1])
    return 7.0  # Default fallback

def compute_ldependent_nn_spacing():
    """Compute NN spacing using L-dependent bias correction."""

    print("="*70)
    print("L-DEPENDENT NEAREST-NEIGHBOR SPACING ANALYSIS")
    print("="*70)
    print()
    print("Using Campaign 10 L-dependent bias factors from periodic beading tests.")
    print("The bias factor scales with filament length L: longer filaments have")
    print("larger pairwise median bias.")
    print()

    results = []

    for region_name, data in HGBS_REGIONS.items():
        pairwise = data['pairwise_median_pc']
        L = data['filament_length_L']
        bias_factor = get_bias_factor(L)

        # Apply L-dependent correction
        nn_corrected = pairwise / bias_factor
        nn_lambda_W = nn_corrected / 0.1

        # Estimate uncertainty (20% due to bias factor uncertainty)
        nn_uncertainty = nn_corrected * 0.20
        nn_lambda_W_uncertainty = nn_uncertainty / 0.1

        result = {
            'region': region_name,
            'n_cores': data['n_cores'],
            'L': L,
            'bias_factor': bias_factor,
            'pairwise_median': pairwise,
            'nn_corrected': nn_corrected,
            'nn_uncertainty': nn_uncertainty,
            'nn_lambda_W': nn_lambda_W,
            'nn_lambda_W_uncertainty': nn_lambda_W_uncertainty,
            'robust': data['robust'],
        }
        results.append(result)

    # Print table
    print(f"{'Region':<12} {'L (pc)':<8} {'Bias':<8} {'Pairwise':<10} {'NN_corrected':<14} {'NN_λ/W':<10} {'Status':<8}")
    print("-"*75)

    for r in results:
        status = "Robust" if r['robust'] else "Limited"
        print(f"{r['region']:<12} {r['L']:<8.1f} {r['bias_factor']:<8.2f}× "
              f"{r['pairwise_median']:.3f}     "
              f"{r['nn_corrected']:.4f} ± {r['nn_uncertainty']:.4f} "
              f"{r['nn_lambda_W']:.2f} ± {r['nn_lambda_W_uncertainty']:.2f} "
              f"{status:<8}")

    print()
    print("COMBINED STATISTICS:")
    print("-"*40)

    # Separate robust and limited regions
    robust_results = [r for r in results if r['robust']]
    all_results = results

    if robust_results:
        # Compute weighted mean for robust regions
        weights = np.array([r['n_cores'] for r in robust_results], dtype=float)
        weights = weights / np.sum(weights)

        weighted_nn = np.sum([w * r['nn_corrected'] for w, r in zip(weights, robust_results)])
        weighted_lambda_W = np.sum([w * r['nn_lambda_W'] for w, r in zip(weights, robust_results)])

        # Compute uncertainty using error propagation
        weighted_uncertainty = np.sqrt(np.sum([w**2 * r['nn_uncertainty']**2
                                                 for w, r in zip(weights, robust_results)]))
        weighted_lambda_W_uncertainty = weighted_uncertainty / 0.1

        print(f"Robust regions (N=4):")
        print(f"  N_cores: {sum(r['n_cores'] for r in robust_results)}")
        print(f"  Weighted NN spacing: {weighted_nn:.4f} ± {weighted_uncertainty:.4f} pc")
        print(f"  Weighted NN λ/W: {weighted_lambda_W:.2f} ± {weighted_lambda_W_uncertainty:.2f}")
        print()

    if all_results:
        weights_all = np.array([r['n_cores'] for r in all_results], dtype=float)
        weights_all = weights_all / np.sum(weights_all)

        all_weighted_nn = np.sum([w * r['nn_corrected'] for w, r in zip(weights_all, all_results)])
        all_weighted_lambda_W = np.sum([w * r['nn_lambda_W'] for w, r in zip(weights_all, all_results)])

        all_weighted_uncertainty = np.sqrt(np.sum([w**2 * r['nn_uncertainty']**2
                                                    for w, r in zip(weights_all, all_results)]))
        all_lambda_W_uncertainty = all_weighted_uncertainty / 0.1

        print(f"Full sample (N={len(all_results)}):")
        print(f"  N_cores: {sum(r['n_cores'] for r in all_results)}")
        print(f"  Weighted NN spacing: {all_weighted_nn:.4f} ± {all_weighted_uncertainty:.4f} pc")
        print(f"  Weighted NN λ/W: {all_weighted_lambda_W:.2f} ± {all_lambda_W_uncertainty:.2f}")

    print()
    print("COMPARISON WITH CLASSICAL THEORY:")
    print("-"*40)
    print(f"Classical IM92 prediction: λ ≈ 4 × W = 0.4 pc (λ/W = 4.0)")
    print(f"Original pairwise (biased): λ = 0.28 pc (λ/W = 2.84)")
    print(f"L-dependent corrected NN: λ = {weighted_nn:.4f} pc (λ/W = {weighted_lambda_W:.2f})")
    print()
    ratio = weighted_nn / 0.4
    print(f"Ratio to classical prediction: {ratio:.1%}")
    print()

    if ratio > 0.5:
        print("The corrected NN spacing is SUBSTANTIALLY SMALLER than classical theory")
        print("by a factor of ~2-3. This suggests either:")
        print("  1. Real filaments fragment more finely than idealized theory predicts")
        print("  2. HGBS 'cores' include sub-fragments not predicted by classical theory")
        print("  3. The L-dependent bias correction may not apply to complex real filaments")
    elif ratio > 0.2:
        print("The corrected NN spacing is MUCH SMALLER than classical theory")
        print("by a factor of ~5. Possible interpretations:")
        print("  1. HGBS cores are hierarchical: what we measure as 'cores' may be")
        print("     smaller density fluctuations within larger Jeans fragments")
        print("  2. The bias correction may be overcorrecting")
        print("  3. Real filaments have much finer fragmentation than theory predicts")
    else:
        print("The corrected NN spacing is AN ORDER OF MAGNITUDE smaller than")
        print("classical theory. This strongly suggests that the pairwise median")
        print("statistic is NOT measuring the fragmentation wavelength at all.")

    print()
    print("RECOMMENDATION:")
    print("  The L-dependent bias correction gives λ/W ≈ {:.2f}, which is".format(weighted_lambda_W))
    print("  {:.1%} of the classical prediction. This differs from the".format(ratio))
    print("  original paper's claim (λ/W ≈ 2.8) by a factor of {:.1f}×.".format(2.84/weighted_lambda_W))
    print()
    print("  The paper should:")
    print("  a) Report the L-dependent bias-corrected values")
    print("  b) Discuss the physical implications of finer-than-Jeans fragmentation")
    print("  c) Or perform full NN analysis from raw HGBS data to verify the correction")
    print()

    # Save results
    output = {
        'analysis_date': '2026-05-01',
        'method': 'L-dependent bias correction from Campaign 10 periodic beading tests',
        'robust_regions': {
            'n_regions': len(robust_results),
            'weighted_nn_pc': weighted_nn,
            'weighted_nn_uncertainty_pc': weighted_uncertainty,
            'weighted_lambda_W': weighted_lambda_W,
            'weighted_lambda_W_uncertainty': weighted_lambda_W_uncertainty,
        },
        'all_regions': {
            'n_regions': len(all_results),
            'weighted_nn_pc': all_weighted_nn,
            'weighted_nn_uncertainty_pc': all_weighted_uncertainty,
            'weighted_lambda_W': all_weighted_lambda_W,
            'weighted_lambda_W_uncertainty': all_lambda_W_uncertainty,
        },
        'individual_results': results,
    }

    with open('ldependent_nn_spacing_results.json', 'w') as f:
        json.dump(output, f, indent=2)

    print(f"Results saved to: ldependent_nn_spacing_results.json")
    print()

if __name__ == '__main__':
    compute_ldependent_nn_spacing()
