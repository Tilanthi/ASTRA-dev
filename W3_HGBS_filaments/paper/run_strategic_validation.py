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
Strategic 3D Validation - 20 targeted simulations
Testing parameter combinations around the best-fitting values
"""

import numpy as np
import json
import time
from run_3d_simulations import Filament3DSolver
from datetime import datetime

def run_simulation(sim_id, params):
    """Run a single simulation"""
    print(f"\n{'='*70}")
    print(f"Simulation {sim_id}: {params['name']}")
    print(f"{'='*70}")
    print(f"  L={params['L_pc']:.2f} pc, P_ext={params['P_ext']:.1e} K/cm³, B={params['B']} μG")
    print(f"  Evolution: {params['t_myr']} Myr ({params['n_steps']} steps)")

    start_time = time.time()

    try:
        # Create solver
        solver = Filament3DSolver(
            nz=64, nx=64, ny=64,
            L_pc=params['L_pc'],
            P_ext_kbcm=params['P_ext'],
            B_microG=params['B']
        )

        # Run simulation
        solver.run(t_myr=params['t_myr'], n_steps=params['n_steps'])

        # Analyze results
        analysis = solver.analyze()

        elapsed = time.time() - start_time

        result = {
            'sim_id': sim_id,
            'name': params['name'],
            'L_pc': params['L_pc'],
            'P_ext_kbcm': params['P_ext'],
            'B_microG': params['B'],
            't_myr': params['t_myr'],
            'n_steps': params['n_steps'],
            'elapsed_seconds': elapsed,
            'analysis': analysis
        }

        # Report results
        n_cores = analysis['n_cores']
        spacing = analysis.get('spacing_pc')

        print(f"\n  Results (in {elapsed:.1f}s):")
        print(f"    Cores formed: {n_cores}")
        if spacing:
            print(f"    Core spacing: {spacing:.3f} pc")
            diff_pct = 100 * (spacing - 0.213) / 0.213
            print(f"    Difference from observed: {diff_pct:+.1f}%")
        else:
            print(f"    Core spacing: N/A (insufficient cores)")

        return result

    except Exception as e:
        elapsed = time.time() - start_time
        print(f"\n  ERROR: {e}")
        return {
            'sim_id': sim_id,
            'name': params['name'],
            'error': str(e),
            'elapsed_seconds': elapsed
        }


def main():
    """Run strategic validation simulations"""

    print("\n" + "="*70)
    print("STRATEGIC 3D VALIDATION - 20 SIMULATIONS")
    print("="*70)
    print(f"\nStart time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

    # Define strategic parameter combinations
    # Based on best-fitting parameters from linear theory:
    # L/H = 10, P_ext = 2e5 K/cm³, B = 0 μG

    simulations = []

    # Series 1: Length variation (L/H = 8, 10, 12)
    for i, L_pc in enumerate([0.32, 0.40, 0.48], 1):
        simulations.append({
            'id': i,
            'name': f"Length_L{L_pc*100:.0f}",
            'L_pc': L_pc,
            'P_ext': 2e5,
            'B': 0,
            't_myr': 3.0,
            'n_steps': 6000
        })

    # Series 2: Pressure variation (1e5, 2e5, 3e5 K/cm³)
    for i, P_ext in enumerate([1e5, 2e5, 3e5], 4):
        simulations.append({
            'id': i,
            'name': f"Pressure_P{P_ext/1e5:.0f}",
            'L_pc': 0.40,
            'P_ext': P_ext,
            'B': 0,
            't_myr': 3.0,
            'n_steps': 6000
        })

    # Series 3: Evolution time (2, 3, 5 Myr)
    for i, t_myr in enumerate([2.0, 3.0, 5.0], 7):
        simulations.append({
            'id': i,
            'name': f"Time_t{t_myr:.0f}",
            'L_pc': 0.40,
            'P_ext': 2e5,
            'B': 0,
            't_myr': t_myr,
            'n_steps': int(t_myr * 2000)
        })

    # Series 4: Magnetic field (0, 10, 20 μG)
    for i, B in enumerate([0, 10, 20], 10):
        simulations.append({
            'id': i,
            'name': f"Magnetic_B{B}",
            'L_pc': 0.40,
            'P_ext': 2e5,
            'B': B,
            't_myr': 3.0,
            'n_steps': 6000
        })

    # Series 5: Best match combinations
    best_combos = [
        (0.40, 2e5, 0, "Best_2D_match"),
        (0.32, 5e5, 0, "W3_like"),
        (0.48, 1e5, 0, "CRA_like"),
        (0.40, 1.5e5, 10, "WithB_field"),
    ]
    for i, (L, P, B, name) in enumerate(best_combos, 13):
        simulations.append({
            'id': i,
            'name': name,
            'L_pc': L,
            'P_ext': P,
            'B': B,
            't_myr': 3.0,
            'n_steps': 6000
        })

    # Series 6: High-resolution validation (5 Myr)
    for i, (L, P, B, name) in enumerate([(0.40, 2e5, 0, "Best_long")], 17):
        simulations.append({
            'id': i,
            'name': name,
            'L_pc': L,
            'P_ext': P,
            'B': B,
            't_myr': 5.0,
            'n_steps': 10000
        })

    # Run simulations
    results = []
    total_estimated_time = sum(s['n_steps'] for s in simulations) * 0.00833

    print(f"\nPlanned simulations: {len(simulations)}")
    print(f"Estimated total time: {total_estimated_time/60:.1f} minutes")
    print(f"\n{'='*70}")

    overall_start = time.time()

    for sim in simulations:
        result = run_simulation(sim['id'], sim)
        results.append(result)

        # Progress update
        completed = len(results)
        elapsed_total = time.time() - overall_start
        avg_time = elapsed_total / completed
        remaining = (len(simulations) - completed) * avg_time

        print(f"\n  Progress: {completed}/{len(simulations)} ({completed/len(simulations)*100:.0f}%)")
        print(f"  Elapsed: {elapsed_total/60:.1f} min, Remaining: ~{remaining/60:.1f} min")

    # Save results
    output_file = 'strategic_3d_validation_results.json'
    with open(output_file, 'w') as f:
        json.dump(results, f, indent=2)

    total_time = time.time() - overall_start

    # Summary
    print(f"\n{'='*70}")
    print(f"STRATEGIC VALIDATION COMPLETE")
    print(f"{'='*70}")
    print(f"Total time: {total_time/60:.1f} minutes")
    print(f"Results saved to: {output_file}")

    # Analyze results
    successful = [r for r in results if 'error' not in r]
    with_cores = [r for r in successful if r['analysis'].get('spacing_pc')]

    print(f"\nSummary:")
    print(f"  Successful simulations: {len(successful)}/{len(results)}")
    print(f"  Formed cores: {len(with_cores)}/{len(successful)}")

    if with_cores:
        spacings = [r['analysis']['spacing_pc'] for r in with_cores]
        print(f"  Spacing range: {min(spacings):.3f} - {max(spacings):.3f} pc")

        # Find closest to observed value (0.213 pc)
        closest = min(with_cores, key=lambda r: abs(r['analysis']['spacing_pc'] - 0.213))
        diff = closest['analysis']['spacing_pc'] - 0.213
        print(f"\n  Closest to observed (0.213 pc):")
        print(f"    {closest['name']}: {closest['analysis']['spacing_pc']:.3f} pc ({100*diff/0.213:+.1f}%)")

    print(f"\nEnd time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")


if __name__ == '__main__':
    main()
