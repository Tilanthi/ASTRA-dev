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
Quick benchmark of simplified 3D solver
"""
from run_3d_simulations import Filament3DSolver
import time
import json

def benchmark(nz, nx, ny, t_myr=0.5, n_steps=1000):
    """Run a benchmark simulation"""
    total_cells = nz * nx * ny
    print(f"\n{'='*60}")
    print(f"Grid: {nz}×{nx}×{ny} = {total_cells:,} cells")
    print(f"{'='*60}")

    start = time.time()
    solver = Filament3DSolver(nz=nz, nx=nx, ny=ny, L_pc=0.4, P_ext_kbcm=2e5)
    init_time = time.time() - start
    print(f"Initialization: {init_time:.2f}s")

    start = time.time()
    solver.run(t_myr=t_myr, n_steps=n_steps)
    sim_time = time.time() - start
    print(f"Simulation: {sim_time:.2f}s ({sim_time/60:.1f} min)")

    analysis = solver.analyze()
    print(f"Results: {analysis['n_cores']} cores, spacing = {analysis.get('spacing_pc', 'N/A')} pc")

    # Performance metrics
    steps_per_sec = n_steps / sim_time
    cells_per_sec = total_cells * steps_per_sec

    return {
        'grid': f"{nz}×{nx}×{ny}",
        'nz': nz,
        'nx': nx,
        'ny': ny,
        'total_cells': total_cells,
        'init_time': init_time,
        'sim_time': sim_time,
        'steps': n_steps,
        'cores_formed': analysis['n_cores'],
        'spacing_pc': analysis.get('spacing_pc'),
        'steps_per_sec': steps_per_sec,
        'cells_per_sec': cells_per_sec
    }

print("\n" + "="*60)
print("3D SIMULATION BENCHMARK (Simplified Solver)")
print("="*60)

results = []

# Test different grid sizes
test_cases = [
    (32, 32, 32),   # 32K cells
    (64, 64, 64),   # 262K cells
    (128, 32, 32),  # 131K cells (longer filament)
]

for nz, nx, ny in test_cases:
    result = benchmark(nz, nx, ny, t_myr=0.5, n_steps=1000)
    results.append(result)

# Save results
with open('benchmark_results.json', 'w') as f:
    json.dump(results, f, indent=2)

print("\n" + "="*60)
print("SUMMARY")
print("="*60)
for r in results:
    print(f"{r['grid']:15s}: {r['sim_time']:6.1f}s  ({r['cells_per_sec']:,.0f} cells/sec)")

# Extrapolate to 1 Myr
print(f"\nExtrapolation to 1 Myr (2000 steps):")
baseline = results[1]  # 64³ baseline
time_1myr = baseline['sim_time'] * 2
print(f"  64³: {time_1myr/60:.1f} min")
print(f"  128³: {time_1myr*8:.1f} min")
print(f"  256³: {time_1myr*64:.1f} min")

print(f"\nResults saved to benchmark_results.json")
