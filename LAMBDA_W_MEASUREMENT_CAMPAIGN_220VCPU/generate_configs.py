#!/usr/bin/env python3
"""
Generate Athena++ simulation configs for λ/W Direct Measurement Campaign.

This campaign is designed to CORRECTLY address the theoretician's concerns about
λ/W measurements (not t_frag timescales).

Three sub-campaigns:
1. LW_DIRECT: Direct λ/W measurements at f ≥ 1.5 to test calibration extrapolation
2. PERP_TIMESERIES: Time-series λ/W analysis for perpendicular fields
3. DOMAIN_TEST: Domain size/resolution investigation for FLAT entries

This campaign DIFFERS from the previous theoretician campaign by:
- Measuring λ/W (fragmentation wavelength), not t_frag (fragmentation time)
- Extracting beading patterns from HDF5 snapshots
- Multiple time outputs for time-series analysis
- Extended domains to ensure beading develops before collapse
"""

import json
import numpy as np
import itertools
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
    n_snapshots: int = 10,
    L_extra: float = 1.0,
    resolution: str = '256'
) -> Dict[str, Any]:
    """
    Generate Athena++ configuration for λ/W measurement.

    Parameters
    ----------
    campaign : str
        'LW_DIRECT', 'PERP_TIMESERIES', or 'DOMAIN_TEST'
    domain_type : str
        'extended32' (32λJ), 'extended24' (24λJ), 'extended16' (16λJ), 'standard' (8λJ)
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
    n_snapshots : int
        Number of time snapshots for HDF5 output (for time-series analysis)
    L_extra : float
        Extra domain length multiplier (for DOMAIN_TEST)
    resolution : str
        '256' (256³), '128' (128³), or '512x64' (512×64×64)

    Returns
    -------
    dict
        Simulation configuration
    """
    # Domain dimensions - key for λ/W extraction!
    if domain_type == 'extended32':
        Lx, Ly, Lz = 32.0, 1.0, 1.0
        if resolution == '256':
            Nx, Ny, Nz = 1024, 64, 64
        elif resolution == '512x64':
            Nx, Ny, Nz = 1024, 64, 64
        else:
            raise ValueError(f"Unsupported resolution for extended32: {resolution}")

    elif domain_type == 'extended24':
        Lx, Ly, Lz = 24.0, 1.0, 1.0
        if resolution == '256':
            Nx, Ny, Nz = 768, 64, 64
        elif resolution == '512x64':
            Nx, Ny, Nz = 768, 64, 64
        else:
            raise ValueError(f"Unsupported resolution for extended24: {resolution}")

    elif domain_type == 'extended16':
        Lx, Ly, Lz = 16.0, 1.0, 1.0
        if resolution == '256':
            Nx, Ny, Nz = 512, 64, 64
        elif resolution == '512x64':
            Nx, Ny, Nz = 512, 64, 64
        elif resolution == '128':
            Nx, Ny, Nz = 256, 64, 64
        else:
            raise ValueError(f"Unsupported resolution for extended16: {resolution}")

    elif domain_type == 'extended12':
        Lx, Ly, Lz = 12.0, 1.5, 1.5
        Nx, Ny, Nz = 384, 48, 48

    elif domain_type == 'standard':
        Lx, Ly, Lz = 8.0, 2.0, 2.0
        if resolution == '256':
            Nx, Ny, Nz = 256, 64, 64
        elif resolution == '128':
            Nx, Ny, Nz = 128, 32, 32
        else:
            raise ValueError(f"Unsupported resolution for standard: {resolution}")

    else:
        raise ValueError(f"Unknown domain_type: {domain_type}")

    # Physics parameters
    cs = 1.0
    four_pi_G = 4.0 * np.pi**2

    # Magnetic field strength
    v_A = cs / np.sqrt(beta)

    # Turbulence amplitude
    dv = M * cs * 1e-4

    # Field geometry
    B_x = v_A * np.cos(np.radians(theta))
    B_y = v_A * np.sin(np.radians(theta))
    B_z = 0.0

    # Timeout - longer for extended domains to allow beading to develop
    if Lx >= 24:
        timeout = 14400  # 4 hours
    elif Lx >= 16:
        timeout = 10800  # 3 hours
    else:
        timeout = 7200   # 2 hours

    # Output configuration - CRITICAL for λ/W extraction
    # Need HDF5 snapshots at multiple times for time-series analysis
    t_max = 6.0  # Maximum simulation time
    if n_snapshots > 1:
        snap_dt = (t_max - 0.5) / (n_snapshots - 1)  # Start at t=0.5, end at t_max
        snap_times = [0.5 + i * snap_dt for i in range(n_snapshots)]
    else:
        snap_times = [t_max]  # Just final snapshot

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
            'tlim': t_max,
            'dt_initial': 1e-4,
            'dt_min': 1e-12,
            'cfl_number': 0.3
        },
        'output': {
            'basename': f"{campaign}_f{f}_beta{beta}_M{M}_theta{theta}_s{seed}",
            'file_type': 'hst',  # History file
            'dt': 0.05,  # HST output every 0.05 t_J
            'hst_dt': 0.01,  # High-temporal resolution for t_frag measurement
            # CRITICAL: HDF5 snapshots for λ/W extraction
            'snapshots': snap_times,
            'snapshot_variables': ['rho', 'vx1', 'vx2', 'vx3', 'B1', 'B2', 'B3']
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
            'n_snapshots': n_snapshots,
            'snap_times': snap_times
        }
    }

    return config


def generate_lw_direct_campaigns() -> List[Dict]:
    """
    Generate LW_DIRECT campaign: Direct λ/W measurements at f ≥ 1.5.

    This addresses Concern 5 about calibration extrapolation.
    """
    configs = []

    # Parameters: f = 1.5, 2.0, 2.5, 3.0; β = 0.3, 1.0, 3.0; 3 seeds
    f_vals = [1.5, 2.0, 2.5, 3.0]
    beta_vals = [0.3, 1.0, 3.0]
    M = 1.0
    theta = 0.0  # Longitudinal field
    seeds = [42, 137, 251]  # 3 seeds for statistics
    n_snapshots = 10  # Multiple snapshots to find when beading appears

    for f, beta, seed in itertools.product(f_vals, beta_vals, seeds):
        config = generate_config(
            campaign='LW_DIRECT',
            domain_type='extended32',  # 32λJ to ensure multiple wavelengths develop
            f=f,
            beta=beta,
            M=M,
            theta=theta,
            seed=seed,
            n_snapshots=n_snapshots
        )
        configs.append(config)

    print(f"Generated {len(configs)} LW_DIRECT configs")
    return configs


def generate_perp_timeseries_campaigns() -> List[Dict]:
    """
    Generate PERP_TIMESERIES campaign: Time-series λ/W for perpendicular fields.

    This addresses Concern 6 about why only 27/100 perpendicular simulations
    showed "GOOD" beading. We need to extract λ/W at multiple times to see
    when/why axial beading appears or disappears.
    """
    configs = []

    # Parameters: f = 1.0, 1.5, 2.0; β = 0.3, 1.0, 3.0; θ = 90°; 3 seeds
    f_vals = [1.0, 1.5, 2.0]
    beta_vals = [0.3, 1.0, 3.0]
    M = 1.0
    theta = 90.0  # Perpendicular field
    seeds = [42, 137, 251]
    n_snapshots = 20  # More snapshots for finer time resolution

    for f, beta, seed in itertools.product(f_vals, beta_vals, seeds):
        config = generate_config(
            campaign='PERP_TIMESERIES',
            domain_type='extended24',  # 24λJ to capture beading evolution
            f=f,
            beta=beta,
            M=M,
            theta=theta,
            seed=seed,
            n_snapshots=n_snapshots
        )
        configs.append(config)

    print(f"Generated {len(configs)} PERP_TIMESERIES configs")
    return configs


def generate_domain_test_campaigns() -> List[Dict]:
    """
    Generate DOMAIN_TEST campaign: Domain size/resolution investigation.

    This addresses Concern 7 about FLAT entries in Campaign 8.
    Test at the problematic point (f=1.5, β=0.3, θ=0°) with different domain sizes
    and resolutions to explain why λ/W extraction failed.
    """
    configs = []

    # Test domain sizes: 8λJ, 12λJ, 16λJ, 24λJ, 32λJ
    domain_types = ['standard', 'extended12', 'extended16', 'extended24', 'extended32']

    # Test resolutions: 128³, 256³
    resolutions = ['128', '256']

    # Fixed parameters at the problematic point
    f = 1.5
    beta = 0.3
    M = 1.0
    theta = 0.0
    seeds = [42, 137, 251]
    n_snapshots = 10

    for domain_type, resolution, seed in itertools.product(domain_types, resolutions, seeds):
        # Skip incompatible combinations
        if domain_type == 'standard' and resolution == '256':
            continue  # Standard domain with 256³ might be too computationally expensive
        if domain_type == 'extended12' and resolution == '128':
            continue  # Skip incompatible combinations

        try:
            config = generate_config(
                campaign='DOMAIN_TEST',
                domain_type=domain_type,
                f=f,
                beta=beta,
                M=M,
                theta=theta,
                seed=seed,
                n_snapshots=n_snapshots,
                resolution=resolution
            )
            configs.append(config)
        except ValueError as e:
            print(f"Skipping {domain_type}+{resolution}: {e}")

    print(f"Generated {len(configs)} DOMAIN_TEST configs")
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

    for campaign in ['LW_DIRECT', 'PERP_TIMESERIES', 'DOMAIN_TEST']:
        campaign_dir = output_dir / campaign
        config_files = list(campaign_dir.glob("config_*.json"))

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
                    'resolution': config['metadata']['resolution'],
                    'n_snapshots': config['metadata']['n_snapshots']
                })

    manifest_path = output_dir / 'manifest.json'
    with open(manifest_path, 'w') as f:
        json.dump({
            'total_configs': len(all_configs),
            'campaigns': {
                'LW_DIRECT': sum(1 for c in all_configs if c['campaign'] == 'LW_DIRECT'),
                'PERP_TIMESERIES': sum(1 for c in all_configs if c['campaign'] == 'PERP_TIMESERIES'),
                'DOMAIN_TEST': sum(1 for c in all_configs if c['campaign'] == 'DOMAIN_TEST')
            },
            'configs': all_configs
        }, f, indent=2)

    print(f"Generated manifest with {len(all_configs)} total configs")


def main():
    """Generate all λ/W measurement campaign configurations."""
    output_dir = Path("configs")

    print("Generating configuration files for λ/W Direct Measurement Campaign")
    print("=" * 80)
    print("This campaign CORRECTLY addresses theoretician concerns about λ/W measurements")
    print("(not t_frag timescales like the previous campaign)")
    print("=" * 80)
    print()

    # Generate all campaigns
    lw_configs = generate_lw_direct_campaigns()
    pert_configs = generate_perp_timeseries_campaigns()
    domain_configs = generate_domain_test_campaigns()

    # Save all configs
    save_configs(lw_configs, 'LW_DIRECT', output_dir)
    save_configs(pert_configs, 'PERP_TIMESERIES', output_dir)
    save_configs(domain_configs, 'DOMAIN_TEST', output_dir)

    # Generate manifest
    generate_manifest(output_dir)

    print("=" * 80)
    print(f"Total configs generated: {len(lw_configs) + len(pert_configs) + len(domain_configs)}")
    print(f"  LW_DIRECT:      {len(lw_configs)}")
    print(f"  PERP_TIMESERIES: {len(pert_configs)}")
    print(f"  DOMAIN_TEST:    {len(domain_configs)}")
    print(f"\nConfigs saved to: {output_dir.absolute()}")
    print()
    print("Key differences from previous campaign:")
    print("  ✓ Measures λ/W (wavelength), not t_frag (time)")
    print("  ✓ HDF5 snapshots at multiple times for time-series analysis")
    print("  ✓ Extended domains (16-32λJ) to ensure beading develops")
    print("  ✓ Domain size tests to explain FLAT entries")


if __name__ == '__main__':
    main()
