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
Generate Athena++ input files for moderate supercriticality test

Creates .athinput files for all (ρ_c, β, seed) combinations.
"""

import json
from pathlib import Path
import numpy as np

# Load simulation design
design_file = Path(__file__).parent / 'moderate_supercriticality_design.json'
with open(design_file) as f:
    design = json.load(f)

# Physical constants
CS = 1.0
G_CODE = 0.20976621499511808
R_FIL = 1.0

def calculate_b_field(rho_center, beta):
    """Calculate magnetic field strength for given beta"""
    # β = P_thermal / P_magnetic = ρc_s² / (B²/μ₀)
    # In code units with μ₀ = 1: B = sqrt(2ρc_s²/β)
    return np.sqrt(2 * rho_center * CS**2 / beta)

def generate_athena_input(sim):
    """Generate Athena++ input file content for a simulation"""

    rho_c = sim['rho_center']
    beta = sim['beta']
    seed = sim['seed']

    B0 = calculate_b_field(rho_c, beta)

    # Grid parameters
    nx1, nx2, nx3 = 192, 48, 48  # Reduced from 256×64×64
    x1min, x1max = -10.0, 10.0  # 20 R_fil in x
    x2min, x2max = -2.5, 2.5    # 5 R_fil in y
    x3min, x3max = -2.5, 2.5    # 5 R_fil in z

    # Time parameters
    # For lower density, need longer evolution
    # Free-fall time ∝ 1/√ρ_c
    t_ff_unit = 1.0 / np.sqrt(G_CODE * rho_c)
    # Run to t = 2.0 × t_ff (well-developed fragmentation)
    tmax = 2.0 * t_ff_unit

    content = f"""<job>
problem_id   {sim['name']}

<par>
# Grid configuration
meshblock_size  {max(16, nx1//12)} {max(16, nx2//12)} {max(16, nx3//12)}
nx1          {nx1}
nx2          {nx2}
nx3          {nx3}
x1min        {x1min}
x1max        {x1max}
x2min        {x2min}
x2max        {x2max}
x3min        {x3min}
x3max        {x3max}

# Time configuration
tstart       0.0
tstop        {tmax:.4f}
dt           1.0e-4
nlim         1000000

# Output
output_dir   outputs/{sim['name']}
output filetype  .tab
dt_bin_dump  {tmax/20:.4f}

# Magnetic field configuration
# B = (Bx, By, Bz) = (B0, 0, 0) for longitudinal field along x-axis
b_field_choice  cartesian
b0_x            {B0:.6f}
b0_y            0.0
b0_z            0.0

# Self-gravity
gravity       gravity
gr_type       fft
G_con         {G_code:.12f}
four_pi_G     {4*np.pi*G_CODE:.12f}
potential_output  true

# Boundary conditions (periodic in all directions for numerical stability)
boundary_x1  periodic
boundary_x2  periodic
boundary_x3  periodic

# Solver
integrator    vl2
recon         linear_limn
flux          hlld
# Order of reconstruction
xorder        2
yorder        2
zorder        2

# Physics
eos           isothermal
iso_sound_speed {CS:.6f}
# No explicit viscosity/diffusivity
# Use implicit dissipation from scheme

# Refinement (uniform for now)
refinement     static
max_level      0
</par>

<problem>
# Filament problem
filament_type  gaussian
rho_center     {rho_c:.3f}
rho_background 0.1
radius         {R_FIL:.3f}

# Random perturbation seed
perturb_seed   {seed}
perturb_amplitude  0.01

# Density cap to prevent numerical issues
rho_max        1000.0
</problem>
"""

    return content

# Create output directory
output_dir = Path(__file__).parent / 'athena_inputs'
output_dir.mkdir(exist_ok=True)

# Generate input files
print(f"Generating {len(design['simulations'])} Athena++ input files...")

for sim in design['simulations']:
    content = generate_athena_input(sim)

    output_file = output_dir / f"{sim['name']}.athinput"
    with open(output_file, 'w') as f:
        f.write(content)

    print(f"  Created: {output_file.name}")

print(f"\nInput files saved to: {output_dir}")

# Also create a master list for batch submission
sim_list_file = output_dir / 'simulation_list.txt'
with open(sim_list_file, 'w') as f:
    for sim in design['simulations']:
        f.write(f"{sim['name']}\n")

print(f"Simulation list saved to: {sim_list_file}")
