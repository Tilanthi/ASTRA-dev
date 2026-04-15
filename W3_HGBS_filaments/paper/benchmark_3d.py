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
3D Simulation Benchmark
Tests runtime on current hardware for different grid sizes
"""

import numpy as np
import time
import json
from filament_3d_simulations import FilamentHydro3D, SimulationParams

def run_benchmark(grid_size, t_myr=1.0):
    """
    Run a single simulation benchmark

    Args:
        grid_size: Tuple of (nz, nx, ny)
        t_myr: Evolution time in Myr
    """
    nz, nx, ny = grid_size
    total_cells = nz * nx * ny

    print("="*80)
    print(f"BENCHMARK: {nz}³ grid ({total_cells:,} cells)")
    print("="*80)

    # Create parameters
    params = SimulationParams(
        nz=nz, nx=nx, ny=ny,
        L_pc=0.4,
        P_ext_kbcm=2e5,
        B_microG=0,
        t_final_myr=t_myr,
        dt_years=100.0
    )

    # Create solver
    print(f"\nInitializing solver...")
    solver = FilamentHydro3D(params)

    # Run simulation with timing
    print(f"\nRunning simulation for {t_myr} Myr...")
    start_time = time.time()

    outputs = solver.run(output_interval_myr=0.5)

    elapsed = time.time() - start_time

    # Analyze results
    analysis = solver.analyze_core_spacing()

    # Report
    print(f"\n{'='*80}")
    print(f"BENCHMARK RESULTS")
    print(f"{'='*80}")
    print(f"Grid size: {nz}×{nx}×{ny} = {total_cells:,} cells")
    print(f"Evolution time: {t_myr} Myr")
    print(f"Wall time: {elapsed:.1f} seconds ({elapsed/60:.1f} minutes)")
    print(f"\nCores formed: {analysis['n_cores']}")
    if analysis.get('spacing_pc'):
        print(f"Core spacing: {analysis['spacing_pc']:.3f} pc")
    print(f"Max density: {np.max(solver.rho):.3e} g/cm³")
    print(f"L/H ratio: {analysis['L_over_H']:.1f}")

    # Performance metrics
    steps = int(t_myr * 1e6 * 3.154e7 / (params.dt_years * 3.154e7))
    cells_per_sec = total_cells * steps / elapsed
    print(f"\nPerformance:")
    print(f"  Time steps: {steps}")
    print(f"  Cells processed: {total_cells * steps:,}")
    print(f"  Throughput: {cells_per_sec:,.0f} cells/second")

    return {
        'grid_size': f"{nz}³",
        'nz': nz,
        'nx': nx,
        'ny': ny,
        'total_cells': total_cells,
        't_myr': t_myr,
        'elapsed_seconds': elapsed,
        'elapsed_minutes': elapsed / 60,
        'cores_formed': analysis['n_cores'],
        'spacing_pc': analysis.get('spacing_pc'),
        'max_density': float(np.max(solver.rho)),
        'steps': steps,
        'cells_per_second': cells_per_sec
    }


def main():
    """Run benchmarks for increasing grid sizes"""

    print("\n" + "="*80)
    print("3D HYDRODYNAMICAL SIMULATION BENCHMARK")
    print("="*80)
    print(f"\nSoftware info:")
    print(f"  NumPy version: {np.__version__}")
    print(f"  SciPy available: {True}")

    results = []

    # Test 64³ grid (shorter run for faster benchmark)
    print("\n")
    result = run_benchmark((64, 64, 64), t_myr=0.2)
    results.append(result)

    # Save results
    with open('benchmark_3d_results.json', 'w') as f:
        json.dump(results, f, indent=2)

    print(f"\n{'='*80}")
    print("BENCHMARK COMPLETE")
    print(f"{'='*80}")
    print(f"\nResults saved to benchmark_3d_results.json")

    # Extrapolation to larger grids
    print(f"\nEXTRAPOLATION TO LARGER GRIDS:")
    baseline_time = results[0]['elapsed_seconds']
    baseline_cells = results[0]['total_cells']

    for grid_name, cells in [('128³', 128**3), ('256³', 256**3)]:
        scale_factor = cells / baseline_cells
        estimated_time = baseline_time * scale_factor
        print(f"  {grid_name} ({cells:,} cells):")
        print(f"    Estimated time: {estimated_time/60:.1f} minutes ({estimated_time/3600:.1f} hours)")


if __name__ == '__main__':
    main()
