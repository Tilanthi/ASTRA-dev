#!/usr/bin/env python3
"""
Generate Athena++ simulation configurations for Transition Mapping Campaign
Maps fragmentation transition at f = 1.5-2.5, beta = 0.5-1.5
"""

import numpy as np
import os
import json
from pathlib import Path

def calculate_physics_parameters(f, beta, mach):
    """
    Calculate physical parameters for given f, beta, mach

    Physics setup (code units: cs = 1, rho_critical = 1):
    - Critical line mass: mu_crit = 2*cs^2/G
    - For Gaussian filament: mu_line = sqrt(2*pi)*rho0*W^2
    - Supercriticality: f = mu_line/mu_crit
    - Plasma beta: beta = 2*cs^2*mu0*rho/B^2
    """
    # Code units
    cs = 1.0
    G_code = 0.20976621499511808  # 4*pi*G = 2.636 for rho_c = 10

    # From f = mu_line/mu_crit and Gaussian profile
    # For rho(r) = rho_c * exp(-r^2/2), mu_line = sqrt(2*pi)*rho_c*W^2
    # With W = 1 and mu_crit = 2*cs^2/G:
    # f = sqrt(2*pi)*rho_c / (2*cs^2/G) = sqrt(2*pi)*rho_c*G/(2*cs^2)
    # Therefore: rho_c = 2*f*cs^2 / (sqrt(2*pi)*G)

    rho_c = 2.0 * f * cs**2 / (np.sqrt(2.0 * np.pi) * G_code)

    # Magnetic field strength from beta
    # beta = 2*cs^2*mu0*rho/B^2 => B = cs*sqrt(2*mu0*rho/beta)
    B0 = cs * np.sqrt(2.0 * 1.0 * rho_c / beta)  # mu0 = 1 in code units

    return {
        'rho_c': rho_c,
        'B0': B0,
        'cs': cs,
        'G_code': G_code
    }

def generate_athena_config(f, beta, mach, seed, output_dir):
    """Generate Athena++ configuration file for one parameter set"""

    params = calculate_physics_parameters(f, beta, mach)

    config = f"""<job>
problem_id   = MSC_f{f:.1f}_b{beta:.1f}_M{mach:.1f}_s{seed}

<time>
tlim        = 4.0
ncycle_out  = 1000

<mesh>
nx1         = 256
nx2         = 256
nx3         = 256
x1min       = -8.0
x1max       = 8.0
x2min       = -2.0
x2max       = 2.0
x3min       = -2.0
x3max       = 2.0

<meshblock>
nx1         = 64
nx2         = 64
nx3         = 64

<hydro>
isothermal_hydro   = true
gamma_adi          = 1.0001

<mhd>
# MHD enabled

<gravity>
grav_field_type = fft

<problem>
rho0         = {params['rho_c']:.6f}
B0_x         = {params['B0']:.6f}
B0_y         = 0.0
B0_z         = 0.0
mach         = {mach:.1f}
seed         = {seed}

<output>
output      = hst
file_type   = hst
dt          = 0.1
variable    = dom, time, dt, mass, momentum, 1-M/mass, 2-M/mass, 3-M/mass

output      = vtk
file_type   = vtk
dt          = 1.0
variable    = prim
dataset     = total

output      = tab
file_type   = tab
dt          = 0.1
variable    = prim
dataset     = total
"""

    sim_name = f"MSC_f{f:.1f}_b{beta:.1f}_M{mach:.1f}_s{seed}"
    config_path = os.path.join(output_dir, sim_name, "athena_input.dat")

    os.makedirs(os.path.dirname(config_path), exist_ok=True)

    with open(config_path, 'w') as f_out:
        f_out.write(config)

    return sim_name, params

def main():
    """Generate all simulation configurations"""

    # Parameter grid
    f_values = [1.5, 1.6, 1.7, 1.8, 1.9, 2.0, 2.1, 2.2, 2.3, 2.4, 2.5]
    beta_values = [0.5, 0.7, 0.9, 1.1, 1.3, 1.5]
    mach_values = [1.0, 2.0, 3.0]
    seeds = [42, 137]

    output_base = "/path/to/simulations/transition_mapping_campaign_apr2026"
    manifest = []

    print("Generating Athena++ configurations...")
    print(f"f values: {f_values}")
    print(f"beta values: {beta_values}")
    print(f"Mach values: {mach_values}")
    print(f"Seeds: {seeds}")
    print(f"Total simulations: {len(f_values)*len(beta_values)*len(mach_values)*len(seeds)}")
    print()

    for f in f_values:
        for beta in beta_values:
            for mach in mach_values:
                for seed in seeds:
                    sim_name, params = generate_athena_config(
                        f, beta, mach, seed, output_base
                    )

                    manifest.append({
                        'run_id': sim_name,
                        'f': f,
                        'beta': beta,
                        'mach': mach,
                        'seed': seed,
                        'rho_c': params['rho_c'],
                        'B0': params['B0'],
                        'config_dir': os.path.join(output_base, sim_name),
                        'status': 'pending'
                    })

                    print(f"Generated: {sim_name}")

    # Save manifest
    manifest_path = os.path.join(output_base, "simulation_manifest.json")
    with open(manifest_path, 'w') as f_out:
        json.dump(manifest, f_out, indent=2)

    print(f"\nManifest saved to: {manifest_path}")
    print(f"Total configurations: {len(manifest)}")

    # Print example physics parameters
    print("\nExample physics parameters (f=2.0, beta=1.0, M=2.0):")
    example = calculate_physics_parameters(2.0, 1.0, 2.0)
    print(f"  rho_c = {example['rho_c']:.4f}")
    print(f"  B0    = {example['B0']:.4f}")
    print(f"  cs    = {example['cs']:.4f}")
    print(f"  G     = {example['G_code']:.4f}")

    # Print estimated computational cost
    print("\nEstimated computational cost:")
    print("  Per simulation (256³, 40 timesteps): ~2-4 hours on 64 cores")
    print(f"  Total wall time (240 sims, 200 cores): ~24-48 hours")
    print(f"  Core-hours: {240 * 64 * 3:.0f} ({240 * 64 * 3 / 2000:.1f}k core-hours)")

if __name__ == "__main__":
    main()
