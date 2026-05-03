#!/usr/bin/env python3
"""
Configuration generator for Targeted Supercritical f=1.5 Campaign

Generates Athena++ input files for extended-domain simulations at f=1.5.

Author: ASTRA Agent System
Date: 2026-05-03
"""

import numpy as np
from pathlib import Path

def generate_f15_config(output_dir, seed):
    """
    Generate Athena++ configuration for f=1.5 extended domain simulation.

    Parameters
    ----------
    output_dir : str
        Output directory for config file
    seed : int
        Random seed for turbulence
    """

    # Physical parameters
    f_ratio = 1.5
    beta_plasma = 1.0
    mach_number = 1.0
    theta_deg = 0.0  # Longitudinal field

    # Domain parameters
    Lx_lambdaJ = 24.0  # Extended domain (3× standard)
    Ly_lambdaJ = 1.0
    Lz_lambdaJ = 1.0

    # Resolution
    Nx = 1536
    Ny = 64
    Nz = 64

    # Grid setup
    dx = Lx_lambdaJ / Nx
    dy = Ly_lambdaJ / Ny
    dz = Lz_lambdaJ / Nz

    # Problem configuration
    config_content = f"""<problem>
  # ========================================================================
  # Targeted Supercritical Test: f = 1.5, Extended Domain
  # ========================================================================
  # Purpose: Test whether extended domain allows longitudinal beading
  #          to develop before radial collapse at f = 1.5
  #
  # Domain: 24λ_J × 1λ_J × 1λ_J (3× extended in longitudinal direction)
  # Resolution: 1536 × 64 × 64 (uniform grid, dx = dy = dz)
  # ========================================================================

  <filament>
    # Filament parameters
    f_ratio            = {f_ratio}      # 1.5× critical mass-to-line ratio
    beta_plasma        = {beta_plasma}  # Intermediate field strength
    mach_number        = {mach_number}  # Fiducial turbulence
    theta_deg          = {theta_deg}    # Longitudinal B field (B || filament axis)

    # Domain specification
    Lx_lambdaJ         = {Lx_lambdaJ}
    Ly_lambdaJ         = {Ly_lambdaJ}
    Lz_lambdaJ         = {Lz_lambdaJ}

    # Grid resolution
    Nx                 = {Nx}
    Ny                 = {Ny}
    Nz                 = {Nz}

    # Random seed for turbulent perturbations
    rng_seed           = {seed}

    # Equation of state
    gamma              = 1.0    # Isothermal
    cs_iso             = 1.0    # Sound speed (normalized)

    # Magnetic field configuration
    B0_ratio           = {1.0/np.sqrt(beta_plasma)}  # From plasma beta
    field_geometry     = longitudinal  # B || x-axis

    # Checkpoint/restart
    checkpoint_dir     = ./checkpoints/
    checkpoint_interval = 0.05  # Checkpoint every 0.05 t_J

    # Output
    output_dir         = ./outputs/
    output_interval    = 0.1    # Output every 0.1 t_J
    vtk_interval       = 0.2    # VTK outputs for visualization

    # Simulation termination
    t_max              = 2.0    # Maximum 2 Jeans times
    max_walltime       = 21600  # 6 hours wall-clock timeout

    # Sink particles
    sink_enabled       = true
    sink_density_thresh = 1e4   # Formation threshold
    sink_merge_radius  = 0.02   # Merge radius
    sink_min_mass      = 0.01   # Minimum mass
    sink_accretion_rad = 0.02   # Accretion radius

  </filament>
</problem>

<job>
  <job>
    problem_id      = TARGETED_F15_extended_seed{seed:03d}
    max_runtime     = 21600  # 6 hours
    num_cores       = 16
    restart_file    =
  </job>
</job>
"""

    # Write config file
    config_file = Path(output_dir) / f"targeted_f15_extended_seed{seed:03d}.athinput"
    with open(config_file, 'w') as f:
        f.write(config_content)

    print(f"Generated config: {config_file}")
    return config_file


def main():
    """Generate all configuration files."""

    # Create output directory
    output_dir = Path("configs")
    output_dir.mkdir(exist_ok=True)

    # Random seeds
    seeds = [42, 137, 251, 367, 499]

    print("="*70)
    print("TARGETED SUPERCRITICAL F=1.5 CAMPAIGN: Config Generation")
    print("="*70)
    print(f"Output directory: {output_dir.absolute()}")
    print(f"Number of configs: {len(seeds)}")
    print()

    # Generate configs
    config_files = []
    for seed in seeds:
        config_file = generate_f15_config(output_dir, seed)
        config_files.append(config_file)

    print()
    print("="*70)
    print("CONFIG GENERATION COMPLETE")
    print("="*70)
    print(f"Generated {len(config_files)} configuration files:")
    for cf in config_files:
        print(f"  - {cf.name}")
    print()
    print("Next steps:")
    print("1. Review config files in ./configs/")
    print("2. Compile Athena++ with problem generator")
    print("3. Run simulations using run_campaign.py")
    print()


if __name__ == '__main__':
    main()
