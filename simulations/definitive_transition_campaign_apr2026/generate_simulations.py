#!/usr/bin/env python3
"""
Generate Athena++ simulation configurations for Definitive 2D Transition Campaign
Complete (f, β) parameter space mapping: 648 simulations
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
    # Code units (consistent with moderate supercriticality campaign)
    cs = 1.0
    G_code = 0.20976621499511808  # 4*pi*G = 2.636 for rho_c = 10

    # From f = mu_line/mu_crit and Gaussian profile
    # rho_c = 2*f*cs^2 / (sqrt(2*pi)*G_code)
    rho_c = 2.0 * f * cs**2 / (np.sqrt(2.0 * np.pi) * G_code)

    # Magnetic field strength from beta
    # B0 = cs*sqrt(2*mu0*rho_c/beta)  (mu0 = 1 in code units)
    B0 = cs * np.sqrt(2.0 * 1.0 * rho_c / beta)

    return {
        'rho_c': rho_c,
        'B0': B0,
        'cs': cs,
        'G_code': G_code
    }

def generate_athena_config(f, beta, mach, seed, output_dir, campaign_phase="primary"):
    """Generate Athena++ configuration file for one parameter set"""

    params = calculate_physics_parameters(f, beta, mach)

    # Create run ID
    ftag = f"{f:.1f}".replace(".", "p")
    btag = f"{beta:.1f}".replace(".", "p")
    mtag = f"{mach:.1f}".replace(".", "p")
    run_id = f"DTC_f{ftag}_b{btag}_M{mtag}_s{seed}"  # DTC = Definitive Transition Campaign

    config = f"""<job>
problem_id   = {run_id}

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

    config_path = os.path.join(output_dir, run_id, "athena_input.dat")

    os.makedirs(os.path.dirname(config_path), exist_ok=True)

    with open(config_path, 'w') as f_out:
        f_out.write(config)

    return run_id, params

def main():
    """Generate all simulation configurations"""

    print("="*70)
    print("Definitive 2D Fragmentation Transition Campaign")
    print("Generating Athena++ configurations...")
    print("="*70)

    # Primary grid: 9 × 6 × 3 × 2 = 324 simulations
    f_values = [1.4, 1.5, 1.6, 1.7, 1.8, 1.9, 2.0, 2.1, 2.2]
    beta_values = [0.3, 0.5, 0.7, 0.9, 1.1, 1.3]
    mach_values_primary = [1.0, 2.0, 3.0]
    seeds = [42, 137]

    # Extended grid: M = 4.0, 5.0 (9 × 6 × 2 = 108 simulations)
    mach_values_extended = [4.0, 5.0]

    output_base = "/path/to/simulations/definitive_transition_campaign_apr2026"
    manifest = []

    print(f"\nPrimary Grid: {len(f_values)} f × {len(beta_values)} β × {len(mach_values_primary)} M × {len(seeds)} seeds = {len(f_values)*len(beta_values)*len(mach_values_primary)*len(seeds)} simulations")
    print(f"Extended Grid: {len(f_values)} f × {len(beta_values)} β × {len(mach_values_extended)} M × {len(seeds)} seeds = {len(f_values)*len(beta_values)*len(mach_values_extended)*len(seeds)} simulations")
    print(f"Total: {len(f_values)*len(beta_values)*(len(mach_values_primary)+len(mach_values_extended))*len(seeds)} simulations")
    print()

    # Generate primary grid
    print("Generating PRIMARY grid (M = 1.0, 2.0, 3.0)...")
    for f in f_values:
        for beta in beta_values:
            for mach in mach_values_primary:
                for seed in seeds:
                    run_id, params = generate_athena_config(
                        f, beta, mach, seed, output_base, campaign_phase="primary"
                    )

                    manifest.append({
                        'run_id': run_id,
                        'f': f,
                        'beta': beta,
                        'mach': mach,
                        'seed': seed,
                        'rho_c': params['rho_c'],
                        'B0': params['B0'],
                        'config_dir': os.path.join(output_base, run_id),
                        'status': 'pending',
                        'campaign_phase': 'primary'
                    })

                    print(f"  Generated: {run_id}")

    # Generate extended grid
    print("\nGenerating EXTENDED grid (M = 4.0, 5.0)...")
    for f in f_values:
        for beta in beta_values:
            for mach in mach_values_extended:
                for seed in seeds:
                    run_id, params = generate_athena_config(
                        f, beta, mach, seed, output_base, campaign_phase="extended"
                    )

                    manifest.append({
                        'run_id': run_id,
                        'f': f,
                        'beta': beta,
                        'mach': mach,
                        'seed': seed,
                        'rho_c': params['rho_c'],
                        'B0': params['B0'],
                        'config_dir': os.path.join(output_base, run_id),
                        'status': 'pending',
                        'campaign_phase': 'extended'
                    })

                    print(f"  Generated: {run_id}")

    # Save manifest
    manifest_path = os.path.join(output_base, "simulation_manifest.json")
    with open(manifest_path, 'w') as f_out:
        json.dump(manifest, f_out, indent=2)

    print(f"\nManifest saved to: {manifest_path}")
    print(f"Total configurations: {len(manifest)}")

    # Print example physics parameters
    print("\nExample physics parameters (f=1.8, beta=0.9, M=2.0):")
    example = calculate_physics_parameters(1.8, 0.9, 2.0)
    print(f"  rho_c = {example['rho_c']:.4f}")
    print(f"  B0    = {example['B0']:.4f}")
    print(f"  cs    = {example['cs']:.4f}")
    print(f"  G     = {example['G_code']:.4f}")

    # Print expected transition zone
    print("\nExpected fragmentation states (based on moderate supercriticality results):")
    print("f \\ beta | 0.3 | 0.5 | 0.7 | 0.9 | 1.1 | 1.3")
    print("---------|-----|-----|-----|-----|-----|-----")
    for f in [1.4, 1.5, 1.6, 1.7, 1.8, 1.9, 2.0, 2.1, 2.2]:
        row = f"{f:.1f}     |"
        for beta in [0.3, 0.5, 0.7, 0.9, 1.1, 1.3]:
            # Check if on beta = 2/f^2 line
            beta_line = 2.0 / f**2
            if abs(beta - beta_line) < 0.05:
                if f < 1.8:
                    row += " FRAG |"
                elif f > 1.9:
                    row += " SUPP |"
                else:
                    row += " ???? |"
            else:
                row += "  ??  |"
        print(row)

    # Print estimated computational cost
    print("\nEstimated computational cost:")
    print("  Per simulation (256³, 40 timesteps): ~3-5 hours on 64 cores")
    print(f"  Total simulations: {len(manifest)}")
    print(f"  Total wall time (200 cores): ~{len(manifest) * 4 * 64 / 200 / 3600:.1f} hours ({len(manifest) * 4 * 64 / 200 / 3600 / 24:.1f} days)")
    print(f"  Core-hours: {len(manifest) * 64 * 4:.0f} ({len(manifest) * 64 * 4 / 1000:.1f}k core-hours)")
    print(f"  Disk space: ~{len(manifest) * 5 / 1024:.1f} TB")

if __name__ == "__main__":
    main()
