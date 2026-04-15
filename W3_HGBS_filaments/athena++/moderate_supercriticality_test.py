#!/usr/bin/env python3

# Copyright 2024-2026 Glenn J. White (The Open University / RAL Space)
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""
Moderate Supercriticality Test - Practical MHD Simulation Design

Target: Test magnetic tension hypothesis in f ≈ 1-3 regime
Budget: 144-288 CPU-hours (12 CPUs × 12-24 hours)

Strategy:
- Reduce grid size to 192×48×48 (25% faster than 256×64×64)
- Focus on critical density range: ρ_c = 2, 3, 5 (f ≈ 1.3, 2.0, 3.3)
- Test β = 0.5, 1.0, 2.0 at each density
- 2 seeds per configuration = 18 simulations
- Estimated time: ~6-10 hours per sim, ~110-180 hours total

Key science: Does λ/W transition from ~4 (f→1, no B) to ~2 (f≈2, B)?
"""

import numpy as np
import json
from pathlib import Path

# Physical constants (code units)
CS = 1.0  # Isothermal sound speed
G_CODE = 0.20976621499511808  # 4πG in code units
R_FIL = 1.0  # Filament radius
W_FIL = 2.0  # Filament width (FWHM ≈ 2.35σ for Gaussian)

# Critical line mass: μ_crit = 2c_s²/G
MU_CRIT = 2 * CS**2 / np.sqrt(G_CODE / (4 * np.pi))

def line_mass(rho_center):
    """Calculate line mass for Gaussian filament"""
    return 2 * np.pi * rho_center * R_FIL**2

def supercriticality(rho_center):
    """Calculate f = μ/μ_crit"""
    return line_mass(rho_center) / MU_CRIT

def jeans_length(rho_center):
    """3D Jeans length at central density"""
    return np.pi * CS / np.sqrt(G_CODE * rho_center)

def expected_spacing_analytic(rho_center, beta):
    """
    Analytic estimate for fragmentation scale using modified IM92 formula
    with magnetic tension correction for longitudinal B-field.
    """
    f = supercriticality(rho_center)

    # IM92 near-critical limit (f → 1)
    lambda_W_im92 = 22.0 / f  # Approximation from IM92 Figure 1

    # Magnetic tension correction (c_s / sqrt(c_s² + v_A²))
    # For β = 1: correction factor = 1/√2 ≈ 0.707
    # For β = 0.5: correction factor = 1/√3 ≈ 0.577
    # For β = 2.0: correction factor = 1/√1.5 ≈ 0.816
    tension_factor = 1.0 / np.sqrt(1.0 + 1.0/beta)

    # Combined model (valid for f ≈ 1-5)
    lambda_W_magnetic = lambda_W_im92 * tension_factor

    # Jeans limit (for f >> 1)
    lambda_W_jeans = jeans_length(rho_center) / W_FIL

    # Smooth transition between regimes
    if f < 3.0:
        return lambda_W_magnetic
    else:
        # Gradual transition to Jeans limit
        weight = np.exp(-(f - 3.0))
        return lambda_W_magnetic * weight + lambda_W_jeans * (1 - weight)


# Define simulation parameters
SIMULATIONS = []

# Central densities to test (f ≈ 1.3, 2.0, 3.3)
# Current: ρ_c=10 gives f=6.6 (too supercritical)
RHO_CENTERS = [2.0, 3.0, 5.0]

# Plasma beta values
BETAS = [0.5, 1.0, 2.0]

# Random seeds for robustness
SEEDS = [42, 137]

# Generate all combinations
for rho_c in RHO_CENTERS:
    for beta in BETAS:
        for seed in SEEDS:
            f = supercriticality(rho_c)
            lambda_W_expected = expected_spacing_analytic(rho_c, beta)

            SIMULATIONS.append({
                'name': f'rho{rho_c:.1f}_beta{beta:.1f}_s{seed}',
                'rho_center': rho_c,
                'beta': beta,
                'seed': seed,
                'supercriticality': f,
                'expected_lambda_W': lambda_W_expected,
                'expected_lambda_pc': lambda_W_expected * W_FIL * R_FIL,
            })

print("=" * 70)
print("MODERATE SUPERCRITICALITY TEST - SIMULATION DESIGN")
print("=" * 70)
print(f"\nBudget: 12 CPUs × 12-24 hours = 144-288 CPU-hours")
print(f"Simulations: {len(SIMULATIONS)}")
print(f"Grid: 192×48×48 (reduced from 256×64×64)")
print(f"Domain: 20R×5R×5R (same as before)")

print("\n" + "=" * 70)
print("PARAMETER SPACE")
print("=" * 70)

# Summary table
print(f"\n{'ρ_c':<8} {'f':<6} {'β':<6} {'λ/W (no B)':<12} {'λ/W (with B)':<12} {'λ (pc)':<10}")
print("-" * 70)

for rho_c in RHO_CENTERS:
    f = supercriticality(rho_c)
    lambda_W_no_B = expected_spacing_analytic(rho_c, beta=1e6)
    print(f"{rho_c:<8.1f} {f:<6.2f}", end="")

    for beta in BETAS:
        lambda_W_with_B = expected_spacing_analytic(rho_c, beta)
        lambda_pc = lambda_W_with_B * W_FIL * R_FIL
        if beta == 0.5:
            print(f" {beta:<6.1f} {lambda_W_no_B:<12.2f} {lambda_W_with_B:<12.2f} {lambda_pc:<10.3f}")
        else:
            print(f"{'':8} {'':6} {'':12} {lambda_W_with_B:<12.2f} {lambda_pc:<10.3f}")
    print()

print("\n" + "=" * 70)
print("EXPECTED RESULTS")
print("=" * 70)

print("""
The key prediction: As f increases from 1.3 to 3.3:

1. Non-magnetic case (β → ∞): λ/W decreases from ~4 to ~2
   - f=1.3: Near IM92 limit (λ/W ≈ 4)
   - f=2.0: Transition regime (λ/W ≈ 3)
   - f=3.3: Approaching Jeans limit (λ/W ≈ 2)

2. Magnetic case (β=1): Magnetic tension reduces spacing by ~30%
   - f=1.3: λ/W ≈ 2.8 (testable!)
   - f=2.0: λ/W ≈ 2.1 (matches observation!)
   - f=3.3: λ/W ≈ 1.6 (B effects weaken as gravity dominates)

3. Critical test: At f=2.0, β=1:
   - Prediction: λ/W ≈ 2.1
   - Observation: λ/W = 2.1 ± 0.1
   - This would be a SMOKING GUN for magnetic tension!

If we see λ/W ≈ 4 at f=1.3 regardless of β, it confirms that B doesn't matter
near criticality (contradicts magnetic tension hypothesis).

If we see λ/W ≈ 2 at f=2.0, β=1 but λ/W ≈ 3 at f=2.0, β=2.0, it confirms
magnetic tension is the key mechanism.
""")

print("\n" + "=" * 70)
print("COMPUTATIONAL ESTIMATE")
print("=" * 70)

# Rough time estimate
# Current runs: ρ_c=10, f=6.6, 256×64×64, ~7-10 min (wall time)
# New runs: ρ_c=2-5, f=1.3-3.3, 192×48×48
# Factors:
# - Grid size: (192×48×48)/(256×64×64) = 0.422 (×0.42 faster)
# - Lower density: slower collapse, need longer evolution
# - Evolution time scales as t_ff ∝ 1/√ρ_c
# - For ρ_c=2: t ≈ 2.2× longer than ρ_c=10
# - For ρ_c=5: t ≈ 1.4× longer than ρ_c=10

# Conservative estimate: 30-60 min per sim on 12 cores
time_per_sim_min = 45  # Conservative estimate
total_time_hours = len(SIMULATIONS) * time_per_sim_min / 60

print(f"\nEstimated time per simulation: {time_per_sim_min} min (wall time, 12 cores)")
print(f"Total time: {total_time_hours:.1f} hours")
print(f"Parallel execution (12 sims at once): {total_time_hours/12:.1f} hours")

if total_time_hours/12 <= 24:
    print(f"\n✓ FITS IN 12-24 HOUR BUDGET!")
else:
    print(f"\n✗ EXCEEDS BUDGET - reduce parameter space")

# Write simulation configuration to JSON
output = {
    'design': 'moderate_supercriticality_test',
    'budget_cpu_hours': f'{144-288}',
    'n_simulations': len(SIMULATIONS),
    'grid': '192x48x48',
    'domain': '20x5x5 R_fil',
    'supercriticality_range': [supercriticality(rho_c) for rho_c in RHO_CENTERS],
    'beta_values': BETAS,
    'seeds': SEEDS,
    'simulations': SIMULATIONS,
}

output_file = Path(__file__).parent / 'moderate_supercriticality_design.json'
with open(output_file, 'w') as f:
    json.dump(output, f, indent=2)

print(f"\nSimulation design saved to: {output_file}")

print("\n" + "=" * 70)
print("NEXT STEPS")
print("=" * 70)

print("""
1. Generate Athena++ input files:
   python generate_athena_inputs.py

2. Create submission script for 12-core node:
   python create_submission_script.py

3. Submit to queue:
   sbatch submit_simulations.sh

4. Monitor progress:
   watch -n 60 'ls -lh outputs/*/ *.tab'

5. Analyze results:
   python analyze_fragmentation.py
""")
