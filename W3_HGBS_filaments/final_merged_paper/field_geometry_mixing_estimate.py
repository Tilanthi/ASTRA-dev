#!/usr/bin/env python3
"""
Field Geometry Mixing Estimate

The Campaign 6 result shows:
- Perpendicular fields (90% of HGBS filaments per Planck): λ/W ≈ 1.25
- Longitudinal fields: λ/W ≈ 3.7 (field-geometry-calibrated)
- Observed HGBS: λ/W ≈ 2.8

Question: What mixture of field geometries would reproduce the observed value?

Simple linear mixing model:
λ_obs = f_long * λ_long + (1 - f_long) * λ_perp

Solve for f_long to match observations.
"""

import json
import numpy as np

# Known values
LAMBDA_PERP = 1.25    # Perpendicular field geometry
LAMBDA_LONG = 3.70    # Longitudinal field geometry (field-geometry-calibrated)
LAMBDA_OBS = 2.80     # Observed PM-based HGBS value
PLANCK_LONG_FRACTION = 0.10  # Planck finds ~10% longitudinal

def solve_mixing_model(lambda_obs, lambda_long, lambda_perp):
    """
    Solve for required longitudinal fraction to match observations.

    λ_obs = f_long * λ_long + (1 - f_long) * λ_perp
    λ_obs = λ_perp + f_long * (lambda_long - lambda_perp)
    f_long = (λ_obs - λ_perp) / (lambda_long - λ_perp)
    """
    f_long = (lambda_obs - lambda_perp) / (lambda_long - lambda_perp)
    return f_long

def calculate_confidence_intervals(lambda_obs, lambda_long=3.70, lambda_long_std=0.18,
                                   lambda_perp=1.25, lambda_perp_std=0.09):
    """Calculate confidence interval for mixing fraction."""

    # Using error propagation for f_long = (λ_obs - λ_perp) / (λ_long - λ_perp)
    # Treating λ_obs as exact (for this calculation)

    delta = lambda_long - lambda_perp
    delta_std = np.sqrt(lambda_long_std**2 + lambda_perp_std**2)

    # Partial derivatives
    df_dlambda_long = -(lambda_obs - lambda_perp) / delta**2
    df_dlambda_perp = (lambda_obs - lambda_long) / delta**2

    # Variance
    var_f = (df_dlambda_long * lambda_long_std)**2 + (df_dlambda_perp * lambda_perp_std)**2
    std_f = np.sqrt(var_f)

    return std_f

def main():
    """Run field geometry mixing analysis."""

    print("=" * 70)
    print("FIELD GEOMETRY MIXING ESTIMATE")
    print("=" * 70)

    # Calculate required longitudinal fraction
    f_long_required = solve_mixing_model(LAMBDA_OBS, LAMBDA_LONG, LAMBDA_PERP)

    print(f"\nKnown values:")
    print(f"  λ/W (perpendicular field):     {LAMBDA_PERP:.2f}")
    print(f"  λ/W (longitudinal field):      {LAMBDA_LONG:.2f}")
    print(f"  λ/W (observed HGBS):           {LAMBDA_OBS:.2f}")
    print(f"  Planck longitudinal fraction:  {PLANCK_LONG_FRACTION:.0%}")

    print(f"\n" + "-" * 70)
    print(f"Mixing model: λ_obs = f_long * λ_long + (1 - f_long) * λ_perp")
    print("-" * 70)

    print(f"\nRequired longitudinal fraction to match observations:")
    print(f"  f_long = ({LAMBDA_OBS:.2f} - {LAMBDA_PERP:.2f}) / ({LAMBDA_LONG:.2f} - {LAMBDA_PERP:.2f})")
    print(f"  f_long = {f_long_required:.3f} = {f_long_required:.1%}")

    # Calculate discrepancy with Planck
    discrepancy_factor = f_long_required / PLANCK_LONG_FRACTION

    print(f"\nDiscrepancy with Planck:")
    print(f"  Required: {f_long_required:.1%} longitudinal")
    print(f"  Planck:   {PLANCK_LONG_FRACTION:.1%} longitudinal")
    print(f"  Discrepancy factor: {discrepancy_factor:.1f}×")

    # Calculate confidence interval
    std_f = calculate_confidence_intervals(LAMBDA_OBS)
    ci_lower = f_long_required - 2*std_f
    ci_upper = f_long_required + 2*std_f

    print(f"\nConfidence interval (95%):")
    print(f"  f_long = {f_long_required:.1%} ± {2*std_f:.1%}")
    print(f"  Range: [{ci_lower:.1%}, {ci_upper:.1%}]")

    # Test various observed values
    print(f"\n" + "=" * 70)
    print("SENSITIVITY TO OBSERVED VALUE")
    print("=" * 70)

    test_observations = [
        (2.17, "NN weighted mean"),
        (2.20, "NN unweighted mean"),
        (2.00, "NN median"),
    ]

    print("\nFor different observed values:")
    print(f"{'Observed λ/W':<15} | {'f_long required':<20} | {'vs Planck'}")
    print("-" * 60)

    for lambda_test, name in test_observations:
        f_test = solve_mixing_model(lambda_test, LAMBDA_LONG, LAMBDA_PERP)
        ratio = f_test / PLANCK_LONG_FRACTION
        print(f"{lambda_test:.2f} ({name:<13}) | {f_test:.1%} ({'':>3})  | {ratio:.1f}× discrepancy")

    # Key findings
    print(f"\n" + "=" * 70)
    print("KEY FINDINGS")
    print("=" * 70)

    print(f"""
1. To match the observed λ/W = {LAMBDA_OBS:.2f}:
   - Required longitudinal fraction: {f_long_required:.1%}
   - Planck observed fraction: ~10%
   - Discrepancy: {discrepancy_factor:.1f}×

2. Alternative explanations:
   a) Field geometry misclassification:
      - Planck measures angle between mean field and filament orientation
      - This may not correlate cleanly with effective fragmentation geometry
      - Some "perpendicular" filaments may have longitudinal components at core scales

   b) Non-MHD physics:
      - Turbulent anisotropy could modify effective geometry
      - Non-ideal MHD effects (ambipolar diffusion) could change λ/W
      - Time-dependent thermodynamics (heating/cooling) not in model

   c) Sample selection bias:
      - HGBS filaments with NN measurements may favor longitudinal geometries
      - Longitudinal fields produce clearer core chains (easier to detect)
      - This could bias the observed sample toward longitudinal-like behavior

   d) Multi-filament complexity:
      - Simulations: single filaments with pure field geometry
      - Observations: multi-filament systems with mixed/projection effects
      - The "effective" geometry in complex systems may differ from pure cases

3. Similar magnitude of discrepancies:
   - Observed vs perpendicular: {LAMBDA_OBS:.2f} / {LAMBDA_PERP:.2f} = {LAMBDA_OBS/LAMBDA_PERP:.2f}× too long
   - Observed vs longitudinal: {LAMBDA_LONG:.2f} / {LAMBDA_OBS:.2f} = {LAMBDA_LONG/LAMBDA_OBS:.2f}× too short

   These similar ratios ({LAMBDA_OBS/LAMBDA_PERP:.1f}× and {LAMBDA_LONG/LAMBDA_OBS:.1f}×) are intriguing
   and may suggest that real HGBS filaments sample mixed field geometries, but the
   required mixture fraction differs from independent Planck constraints.

4. Implications:
   - The perpendicular-field result is a major unexplained discrepancy
   - Current simulations (single filaments, pure field geometries) cannot fully
     explain HGBS observations
   - Future work: (1) Multi-filament simulations with mixed field geometries,
     (2) Better connection between field geometry measurements and fragmentation
     predictions, (3) Observational tests of geometry-dependent fragmentation
    """)

    # Save results
    results = {
        'lambda_perp': LAMBDA_PERP,
        'lambda_long': LAMBDA_LONG,
        'lambda_obs': LAMBDA_OBS,
        'f_long_required': f_long_required,
        'planck_long_fraction': PLANCK_LONG_FRACTION,
        'discrepancy_factor': discrepancy_factor,
        'confidence_interval_95': [ci_lower, ci_upper],
        'sensitivity_tests': test_observations,
    }

    output_file = '/Users/gjw255/astrodata/SWARM/ASTRA-dev-main/W3_HGBS_filaments/final_merged_paper/field_geometry_mixing_results.json'
    with open(output_file, 'w') as f:
        json.dump(results, f, indent=2)

    print(f"\nResults saved to: {output_file}")

if __name__ == '__main__':
    main()
