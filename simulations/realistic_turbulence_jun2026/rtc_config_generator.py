#!/usr/bin/env python3
"""
Realistic Turbulence Campaign Configuration Generator
Generates Athena++ input files for RTC-1200 simulation campaign
"""

import os
import numpy as np
from pathlib import Path

def generate_parameter_grid():
    """
    Generate parameter grid for Realistic Turbulence Campaign
    Returns: list of (f, beta, mturb, theta, seed) tuples
    """
    params = []

    # Core Grid: 480 simulations
    mturb_values = [2.0, 2.5, 3.0, 3.5, 4.0]
    f_values = [1.0, 1.2, 1.5, 2.0]
    beta_values = [0.3, 0.5, 1.0, 2.0]
    theta_values = [0, 90]  # longitudinal, perpendicular

    for mturb in mturb_values:
        for f in f_values:
            for beta in beta_values:
                for theta in theta_values:
                    for seed in [1, 2, 3]:
                        params.append((f, beta, mturb, theta, seed))

    # Near-Critical Extension: 240 simulations
    for mturb in mturb_values:
        for f in [1.0, 1.2]:
            for beta in beta_values:
                for seed in [1, 2, 3, 4, 5, 6]:  # 6 seeds for higher stats
                    params.append((f, beta, mturb, 0, seed))

    # Supercritical Extension: 240 simulations
    for mturb in mturb_values:
        for f in [1.5, 2.0]:
            for beta in beta_values:
                for theta in [0, 90]:
                    for seed in [1, 2, 3]:
                        params.append((f, beta, mturb, theta, seed))

    # Perpendicular-Field Focus: 240 simulations
    for mturb in mturb_values:
        for f in f_values:
            for beta in beta_values:
                for seed in [1, 2, 3]:
                    params.append((f, beta, mturb, 90, seed))

    print(f"Total parameters: {len(params)}")
    return params

def generate_athena_config(f, beta, mturb, theta, seed, output_dir):
    """
    Generate Athena++ input file for single simulation

    Parameters:
    -----------
    f : float
        Line-mass fraction (M_line/M_crit)
    beta : float
        Plasma beta (ratio of thermal to magnetic pressure)
    mturb : float
        Turbulent Mach number (REAL physical value, not scaled)
    theta : float
        Field angle (0 = longitudinal, 90 = perpendicular)
    seed : int
        Random seed for turbulent driving
    output_dir : str
        Output directory for simulation
    """

    # Physical parameters
    cs = 1.0  # Sound speed (code units)
    rho0 = 1.0  # Background density
    B0 = np.sqrt(8 * np.pi * rho0 * cs**2 / beta)  # Magnetic field strength

    # Geometry-dependent B-field
    if theta == 0:  # Longitudinal
        Bx = B0
        By = 0.0
        Bz = 0.0
    elif theta == 90:  # Perpendicular (B in y-direction)
        Bx = 0.0
        By = B0
        Bz = 0.0

    # Turbulence driving parameters (OU process)
    driving_wavelength = 8.0  # lambda_drive = Lx/2 = 8 lambda_J
    correlation_time = 0.1  # t_corr = 0.1 t_J
    driving_amplitude = mturb * cs  # REAL turbulence, not scaled by 10^-4

    # Create output directory
    sim_dir = Path(output_dir) / f"f{f:.1f}_b{beta:.1f}_m{mturb:.1f}_t{theta:.0f}_s{seed}"
    sim_dir.mkdir(parents=True, exist_ok=True)

    # Generate athena_input.txt
    athena_input = f"""<job>
ProblemID       = filament_spacing_pr
Coordinates      = cartesian

<time>
tstop           = 2.0
cfl_number      = 0.3
nlim            = 100000
</time>

<mesh>
nx1             = 512
nx2             = 64
nx3             = 64
x1min           = 0.0
x1max           = 16.0
x2min           = -1.0
x2max           = 1.0
x3min           = -1.0
x3max           = 1.0
ix1_bc         = periodic
ox1_bc         = periodic
ix2_bc         = periodic
ox2_bc         = periodic
ix3_bc         = periodic
ox3_bc         = periodic
AutoWithNghost = FALSE
</mesh>

<hydro>
gamma               = 1.0
R_ideal             = 1.0
CFL                 = 0.3
tcfl                = 1e-6
</hydro>

<mhd>
four_pi_G          = 39.47841760435743
</mhd>

<gravity>
gravity_type = fft
dirichlet_flag = 0
</gravity>

<fft>
dwavenum = 1
</fft>

<problem>
rho0            = {rho0}
p0              = {cs**2 / rho0}
Bx0             = {Bx}
By0             = {By}
Bz0             = {Bz}
filament_radius = 0.3
driving_type    = ou_stochastic
driving_amp     = {driving_amplitude}
driving_k       = {2 * np.pi / driving_wavelength}
corr_time       = {correlation_time}
random_seed     = {seed}
evolution_time   = 2.0
</problem>

<output>
output格式 = hdf5
dt             = 0.01
variables      = d,rho
file_type      = single
file_number    = 0
output1格式      = history
dt1             = 0.001
variables1      = dt, mass, 1-momentum, 2-momentum, 3-momentum
</output>

<static>
do_pgen        = false
restart        = false
</static>
</job>
"""

    with open(sim_dir / "athena_input.txt", "w") as f:
        f.write(athena_input)

    return sim_dir

def main():
    """
    Main: Generate all simulation configurations
    """
    # Get base directory
    base_dir = Path("/Users/gjw255/astrodata/SWARM/ASTRA-dev-main/simulations/realistic_turbulence_jun2026")
    config_dir = base_dir / "configs"
    config_dir.mkdir(exist_ok=True)

    # Generate parameter grid
    params = generate_parameter_grid()

    # Generate all configurations
    print(f"Generating {len(params)} simulation configurations...")
    sim_dirs = []
    for i, (f, beta, mturb, theta, seed) in enumerate(params):
        sim_dir = generate_athena_config(f, beta, mturb, theta, seed, config_dir)
        sim_dirs.append(sim_dir)

        if (i + 1) % 100 == 0:
            print(f"  Generated {i+1}/{len(params)} configurations...")

    # Save parameter list
    param_file = config_dir / "simulation_list.txt"
    with open(param_file, "w") as f:
        for sim_dir in sim_dirs:
            f.write(f"{sim_dir}\n")

    print(f"\nConfiguration generation complete!")
    print(f"Total simulations: {len(params)}")
    print(f"Configuration directory: {config_dir}")
    print(f"Simulation list: {param_file}")

if __name__ == "__main__":
    main()
