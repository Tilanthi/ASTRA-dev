#!/usr/bin/env python3
"""
Generate Athena++ simulation configs for Theoretician Peer Review Response Campaign.

This campaign addresses three major concerns from theoretician reviewer:
1. STV: Supercritical Transition Validation - direct λ/W measurements at f ≥ 1.5
2. PFS: Perpendicular-Field Systematics - why only 27/100 show "GOOD" beading
3. NCRI: Near-Critical Resolution Investigation - resolve FLAT entries in Campaign 8
"""

import json
import itertools
import numpy as np
from pathlib import Path
from typing import Dict, List, Any


def generate_config(
    campaign: str,
    domain_type: str,
    f: float,
    beta: float,
    M: float,
    theta: float,
    seed: int,
    time_series: bool = False,
    resolution: str = '256'
) -> Dict[str, Any]:
    """
    Generate Athena++ input file for a single simulation.

    Parameters
    ----------
    campaign : str
        'STV', 'PFS', or 'NCRI'
    domain_type : str
        'standard' (8λJ), 'long' (16λJ), 'extended' (24λJ), 'bridge' (12λJ)
    f : float
        Line mass fraction
    beta : float
        Plasma beta
    M : float
        Mach number
    theta : float
        Field angle in degrees (0 = longitudinal, 90 = perpendicular)
    seed : int
        Random seed
    time_series : bool
        Whether to output multiple time snapshots (for PFS)
    resolution : str
        Resolution identifier: '128', '256', or '512x64'

    Returns
    -------
    dict
        Simulation configuration
    """
    # Domain dimensions in code units (λJ = 1)
    if domain_type == 'standard':
        Lx, Ly, Lz = 8.0, 2.0, 2.0
        if resolution == '128':
            Nx, Ny, Nz = 128, 32, 32
        elif resolution == '256':
            Nx, Ny, Nz = 256, 64, 64
        elif resolution == '512x64':
            Nx, Ny, Nz = 512, 64, 64
        else:
            raise ValueError(f"Unknown resolution: {resolution}")

    elif domain_type == 'long':
        Lx, Ly, Lz = 16.0, 1.0, 1.0
        if resolution == '128':
            Nx, Ny, Nz = 256, 64, 64
        elif resolution == '256':
            Nx, Ny, Nz = 512, 64, 64
        elif resolution == '512x64':
            Nx, Ny, Nz = 512, 64, 64
        else:
            raise ValueError(f"Unknown resolution: {resolution}")

    elif domain_type == 'extended':
        Lx, Ly, Lz = 24.0, 1.0, 1.0
        if resolution == '256':
            Nx, Ny, Nz = 768, 64, 64
        elif resolution == '512x64':
            Nx, Ny, Nz = 768, 64, 64
        else:
            raise ValueError(f"Unknown resolution for extended: {resolution}")

    elif domain_type == 'bridge':
        Lx, Ly, Lz = 12.0, 1.5, 1.5
        Nx, Ny, Nz = 384, 48, 48

    else:
        raise ValueError(f"Unknown domain_type: {domain_type}")

    # Physics parameters
    cs = 1.0  # Sound speed
    four_pi_G = 4.0 * np.pi**2  # Normalized so lambda_J = 1

    # Magnetic field strength from plasma beta
    v_A = cs / np.sqrt(beta)

    # Turbulence amplitude
    dv = M * cs * 1e-4

    # Field geometry
    B_x = v_A * np.cos(np.radians(theta))
    B_y = v_A * np.sin(np.radians(theta))
    B_z = 0.0

    # Timeout based on domain size (longer domains need more time)
    if Lx >= 20:
        timeout = 10800  # 3 hours for very long domains
    elif Lx >= 12:
        timeout = 7200   # 2 hours
    else:
        timeout = 3600   # 1 hour

    # Output frequency
    if time_series:
        # More frequent snapshots for time evolution analysis
        snap_dt = 0.1
    else:
        snap_dt = 0.2

    config = {
        'job': {
            'problem_id': 'filament_fragmentation',
            'output_dir': f'outputs/{campaign}/'
        },
        'mesh': {
            'nx1': Nx,
            'nx2': Ny,
            'nx3': Nz,
            'x1min': 0.0,
            'x1max': Lx,
            'x2min': -Ly/2,
            'x2max': Ly/2,
            'x3min': -Lz/2,
            'x3max': Lz/2
        },
        'hydro': {
            'gamma': 1.0,  # Isothermal
            'cs0': cs
        },
        'field': {
            'b1_initial': B_x,
            'b2_initial': B_y,
            'b3_initial': B_z
        },
        'gravity': {
            'four_pi_G': four_pi_G
        },
        'filament': {
            'line_mass_fraction': f,
            'W_core': 0.3,
            'profile': 'gaussian',
            'perturbation_amplitude': dv
        },
        'time': {
            'tlim': 6.0,
            'dt_initial': 1e-4,
            'dt_min': 1e-12,
            'cfl_number': 0.3
        },
        'output': {
            'basename': f"{campaign}_f{f}_beta{beta}_M{M}_theta{theta}_s{seed}",
            'file_type': 'hst',
            'dt': snap_dt,
            'hst_dt': 0.01,
            'variables': ['rho', 'vx1', 'vx2', 'vx3', 'B1', 'B2', 'B3']
        },
        'random_seed': seed,
        'timeout_seconds': timeout,
        'metadata': {
            'campaign': campaign,
            'domain_type': domain_type,
            'f': f,
            'beta': beta,
            'M': M,
            'theta': theta,
            'seed': seed,
            'Lx_lambdaJ': Lx,
            'Ly_lambdaJ': Ly,
            'Lz_lambdaJ': Lz,
            'resolution': f"{Nx}x{Ny}x{Nz}",
            'time_series': time_series
        }
    }

    return config


def generate_stv_campaigns() -> List[Dict]:
    """Generate Supercritical Transition Validation campaign configs."""
    configs = []

    f_vals = [1.5, 1.8, 2.0, 2.5, 3.0]
    beta_vals = [0.3, 1.0, 3.0]
    M = 1.0
    theta = 0.0  # Longitudinal field
    seeds = [42, 137, 251, 367, 499]  # 5 seeds for statistics

    for f, beta, seed in itertools.product(f_vals, beta_vals, seeds):
        config = generate_config(
            campaign='STV',
            domain_type='extended',
            f=f,
            beta=beta,
            M=M,
            theta=theta,
            seed=seed
        )
        configs.append(config)

    print(f"Generated {len(configs)} STV configs")
    return configs


def generate_pfs_campaigns() -> List[Dict]:
    """Generate Perpendicular-Field Systematics campaign configs."""
    configs = []

    f_vals = [1.0, 1.2, 1.5, 2.0]
    beta_vals = [0.3, 1.0, 3.0]
    M = 1.0
    theta = 90.0  # Perpendicular field
    seeds = [42, 137, 251, 367, 499]

    for f, beta, seed in itertools.product(f_vals, beta_vals, seeds):
        config = generate_config(
            campaign='PFS',
            domain_type='long',
            f=f,
            beta=beta,
            M=M,
            theta=theta,
            seed=seed,
            time_series=True  # Enable time series for evolution analysis
        )
        configs.append(config)

    print(f"Generated {len(configs)} PFS configs")
    return configs


def generate_ncri_campaigns() -> List[Dict]:
    """Generate Near-Critical Resolution Investigation campaign configs."""
    configs = []

    f_vals = [1.0, 1.2, 1.3, 1.4, 1.5]
    beta_vals = [0.3]  # Focus on the problematic beta value
    M = 1.0
    theta = 0.0  # Longitudinal field
    seeds = [42, 137, 251]

    domain_types = ['standard', 'bridge', 'long']  # Test domain size effect
    resolutions = ['128', '256', '512x64']  # Test resolution effect

    for f, domain_type, resolution, seed in itertools.product(
        f_vals, domain_types, resolutions, seeds
    ):
        # Map domain_type to resolution
        if domain_type == 'standard' and resolution == '512x64':
            continue  # Skip incompatible combination
        if domain_type == 'bridge' and resolution in ['128', '256']:
            continue  # Bridge uses fixed resolution

        # Handle resolution naming for standard domain
        res_key = resolution
        if domain_type == 'standard' and resolution == '128':
            res_key = '128'
        elif domain_type == 'standard' and resolution == '256':
            res_key = '256'
        elif domain_type == 'long':
            res_key = '512x64'  # Long domain uses this resolution

        config = generate_config(
            campaign='NCRI',
            domain_type=domain_type,
            f=f,
            beta=beta_vals[0],
            M=M,
            theta=theta,
            seed=seed,
            resolution=res_key
        )
        configs.append(config)

    print(f"Generated {len(configs)} NCRI configs")
    return configs


def save_configs(configs: List[Dict], campaign: str, output_dir: Path):
    """Save configuration files to disk."""
    campaign_dir = output_dir / campaign
    campaign_dir.mkdir(parents=True, exist_ok=True)

    for config in configs:
        metadata = config['metadata']
        basename = config['output']['basename']
        filename = f"config_{basename}.json"

        filepath = campaign_dir / filename
        with open(filepath, 'w') as f:
            json.dump(config, f, indent=2)

    print(f"Saved {len(configs)} configs to {campaign_dir}/")


def generate_manifest(output_dir: Path):
    """Generate manifest file listing all configurations."""
    all_configs = []

    for campaign in ['STV', 'PFS', 'NCRI']:
        campaign_dir = output_dir / campaign
        config_files = list(campaign_dir.glob('config_*.json'))

        for config_file in config_files:
            with open(config_file) as f:
                config = json.load(f)
                all_configs.append({
                    'config_file': str(config_file.relative_to(output_dir)),
                    'campaign': config['metadata']['campaign'],
                    'f': config['metadata']['f'],
                    'beta': config['metadata']['beta'],
                    'M': config['metadata']['M'],
                    'theta': config['metadata']['theta'],
                    'seed': config['metadata']['seed'],
                    'Lx_lambdaJ': config['metadata']['Lx_lambdaJ'],
                    'resolution': config['metadata']['resolution']
                })

    manifest_path = output_dir / 'manifest.json'
    with open(manifest_path, 'w') as f:
        json.dump({
            'total_configs': len(all_configs),
            'campaigns': {
                'STV': sum(1 for c in all_configs if c['campaign'] == 'STV'),
                'PFS': sum(1 for c in all_configs if c['campaign'] == 'PFS'),
                'NCRI': sum(1 for c in all_configs if c['campaign'] == 'NCRI')
            },
            'configs': all_configs
        }, f, indent=2)

    print(f"Generated manifest with {len(all_configs)} total configs")


def main():
    """Generate all campaign configurations."""
    output_dir = Path('configs')

    print("Generating configuration files for Theoretician Peer Review Response Campaign")
    print("=" * 80)

    # Generate all campaigns
    stv_configs = generate_stv_campaigns()
    pfs_configs = generate_pfs_campaigns()
    ncri_configs = generate_ncri_campaigns()

    # Save all configs
    save_configs(stv_configs, 'STV', output_dir)
    save_configs(pfs_configs, 'PFS', output_dir)
    save_configs(ncri_configs, 'NCRI', output_dir)

    # Generate manifest
    generate_manifest(output_dir)

    print("=" * 80)
    print(f"Total configs generated: {len(stv_configs) + len(pfs_configs) + len(ncri_configs)}")
    print(f"  STV:  {len(stv_configs)}")
    print(f"  PFS:  {len(pfs_configs)}")
    print(f"  NCRI: {len(ncri_configs)}")
    print(f"\nConfigs saved to: {output_dir.absolute()}")


if __name__ == '__main__':
    main()
