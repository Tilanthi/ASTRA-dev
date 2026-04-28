#!/usr/bin/env python3
"""
Generate Athena++ simulation configs for peer review response campaign.

Campaigns:
- SUPERCRITICAL-LONG: Extended domains (16-32λJ) for direct λ/W measurement
- BRIDGE-GRID: Dense f sampling (1.1-2.0) for extrapolation validation
- TIMEOUT-CONVERGENCE: Systematic timeout validation
- CALIBRATION-VALIDATION: Hierarchical Bayesian calibration analysis
"""

import json
import itertools
import numpy as np
from pathlib import Path
from typing import Dict, List, Any


def generate_config(
    domain_type: str,
    f: float,
    beta: float,
    M: float,
    seed: int,
    campaign_name: str,
    theta: float = 90.0,
    gamma: float = 1.0
) -> Dict[str, Any]:
    """
    Generate Athena++ input file for a single simulation.

    Parameters
    ----------
    domain_type : str
        'standard', 'long', 'extended', 'verylong'
    f : float
        Line mass fraction
    beta : float
        Plasma beta
    M : float
        Mach number
    seed : int
        Random seed
    campaign_name : str
        Campaign identifier
    theta : float
        Field angle relative to filament axis (degrees)
    gamma : float
        Polytropic index (1.0 = isothermal)

    Returns
    -------
    dict
        Simulation configuration
    """
    # Domain dimensions in code units (λJ = 1)
    if domain_type == 'standard':
        Lx, Ly, Lz = 8.0, 2.0, 2.0
        Nx, Ny, Nz = 256, 64, 64
    elif domain_type == 'long':
        Lx, Ly, Lz = 16.0, 1.0, 1.0  # Square transverse, 2x longitudinal
        Nx, Ny, Nz = 512, 64, 64
    elif domain_type == 'extended':
        Lx, Ly, Lz = 24.0, 1.0, 1.0
        Nx, Ny, Nz = 768, 64, 64
    elif domain_type == 'verylong':
        Lx, Ly, Lz = 32.0, 1.0, 1.0
        Nx, Ny, Nz = 1024, 64, 64
    elif domain_type == 'bridge':
        Lx, Ly, Lz = 12.0, 1.5, 1.5
        Nx, Ny, Nz = 384, 48, 48
    else:
        raise ValueError(f"Unknown domain_type: {domain_type}")

    # Physics parameters
    cs = 1.0  # Sound speed
    four_pi_G = 4.0 * np.pi**2  # Normalized so lambda_J = 1

    # Magnetic field strength from plasma beta
    # β = cs²/v_A² → v_A = cs/√β
    v_A = cs / np.sqrt(beta)

    # Turbulence amplitude (relative to thermal)
    dv = M * cs * 1e-4  # Small perturbation amplitude

    # Field geometry (B1 component along x-axis, B2/B3 for oblique)
    B_x = v_A * np.cos(np.radians(theta))
    B_y = v_A * np.sin(np.radians(theta))
    B_z = 0.0

    config = {
        'job': {
            'problem_id': 'filament_fragmentation',
            'output_dir': f'outputs/{campaign_name}/'
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
            'gamma': gamma,
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
            'W_core': 0.3,  # Core half-width in λJ
            'profile': 'gaussian',
            'perturbation_amplitude': dv
        },
        'time': {
            'tlim': 6.0,  # Extended hard timeout
            'dt_initial': 1e-4,
            'dt_min': 1e-12,
            'cfl_number': 0.3
        },
        'output': {
            'basename': f"{campaign_name}_f{f}_beta{beta}_M{M}_theta{theta}_s{seed}",
            'file_type': 'hst',
            'dt': 0.1,  # Full outputs every 0.1 tJ
            'hst_dt': 0.01,  # High-temporal resolution for beading detection
            'variables': ['rho', 'vx1', 'vx2', 'vx3', 'B1']
        },
        'random_seed': seed,
        'metadata': {
            'campaign': campaign_name,
            'domain_type': domain_type,
            'f': f,
            'beta': beta,
            'M': M,
            'theta': theta,
            'gamma': gamma,
            'seed': seed,
            'Lx_lambdaJ': Lx,
            'resolution': f"{Nx}x{Ny}x{Nz}"
        }
    }

    return config


def generate_campaign_configs(
    campaign_name: str,
    param_grid: Dict[str, List],
    domain_type: str = 'standard'
) -> List[Dict[str, Any]]:
    """
    Generate all configs for a campaign.

    Parameters
    ----------
    campaign_name : str
        Campaign identifier
    param_grid : dict
        Parameter grid with keys: f, beta, M, seed, etc.
    domain_type : str
        Domain type for this campaign

    Returns
    -------
    list
        List of simulation configs
    """
    configs = []

    # Extract parameter lists
    f_values = param_grid.get('f', [2.0])
    beta_values = param_grid.get('beta', [1.0])
    M_values = param_grid.get('M', [1.0])
    seed_values = param_grid.get('seed', [42])
    theta_values = param_grid.get('theta', [90.0])

    # Generate all combinations
    for f, beta, M, seed, theta in itertools.product(
        f_values, beta_values, M_values, seed_values, theta_values
    ):
        try:
            config = generate_config(
                domain_type=domain_type,
                f=f,
                beta=beta,
                M=M,
                seed=seed,
                campaign_name=campaign_name,
                theta=theta
            )
            configs.append(config)
        except Exception as e:
            print(f"Warning: Failed to generate config for f={f}, beta={beta}, M={M}: {e}")

    return configs


def save_configs(configs: List[Dict[str, Any]], output_dir: Path) -> List[Path]:
    """
    Save simulation configs to JSON files.

    Parameters
    ----------
    configs : list
        List of simulation configs
    output_dir : Path
        Output directory

    Returns
    -------
    list
        List of saved config file paths
    """
    output_dir = Path(output_dir)
    output_dir.mkdir(exist_ok=True, parents=True)

    config_paths = []
    for i, config in enumerate(configs):
        # Create filename from metadata
        metadata = config['metadata']
        config_filename = (
            f"config_{metadata['campaign']}_"
            f"f{metadata['f']}_"
            f"beta{metadata['beta']}_"
            f"M{metadata['M']}_"
            f"theta{metadata['theta']}_"
            f"s{metadata['seed']}.json"
        )

        config_path = output_dir / config_filename
        with open(config_path, 'w') as f:
            json.dump(config, f, indent=2)

        config_paths.append(config_path)

    return config_paths


# Campaign parameter grids
SUPERCRITICAL_LONG_GRID = {
    'f': [1.5, 2.0, 2.5],
    'beta': [0.3, 1.0, 5.0],
    'M': [1.0],
    'seed': [42, 137, 256],
    'theta': [90.0]
}

BRIDGE_GRID = {
    'f': [1.1, 1.2, 1.3, 1.4, 1.5, 1.6, 1.8, 2.0],
    'beta': [0.3, 1.0, 5.0],
    'M': [1.0],
    'seed': [42, 137],
    'theta': [90.0]
}

TIMEOUT_GRID = {
    'f': [1.4, 1.6, 1.8, 2.0, 2.2],
    'beta': [0.3, 0.5, 1.0],
    'M': [1.0, 2.0, 3.0],
    'seed': [42],
    'theta': [90.0]
}

CALIBRATION_GRID = {
    'f': [1.5, 2.0, 2.5],
    'beta': [0.5, 1.0, 2.0],
    'M': [1.0, 2.0],
    'seed': [42, 137, 256],
    'theta': [30.0, 60.0, 90.0]
}

DOMAIN_CONVERGENCE_GRID = {
    'f': [2.0],
    'beta': [1.0],
    'M': [1.0],
    'seed': [42, 137],
    'theta': [90.0]
}


def main():
    """Generate all campaign configs."""
    print("="*70)
    print("Athena++ Simulation Config Generator")
    print("Peer Review Response Campaigns")
    print("="*70)
    print()

    base_output_dir = Path('peer_review_simulation_configs')

    # SUPERCRITICAL-LONG campaign
    print("Generating SUPERCRITICAL-LONG campaign configs...")
    print("-" * 70)

    supercrit_total = 0
    for domain_type in ['long', 'extended', 'verylong']:
        configs = generate_campaign_configs(
            'SUPERCRITICAL_LONG',
            SUPERCRITICAL_LONG_GRID,
            domain_type=domain_type
        )
        output_dir = base_output_dir / 'supercritical_long' / domain_type
        paths = save_configs(configs, output_dir)
        supercrit_total += len(configs)
        print(f"  {domain_type:10s}: {len(configs):3d} configs → {output_dir}")

    print(f"  SUPERCRITICAL-LONG total: {supercrit_total} configs")
    print()

    # BRIDGE-GRID campaign
    print("Generating BRIDGE-GRID campaign configs...")
    print("-" * 70)

    bridge_configs = generate_campaign_configs(
        'BRIDGE_GRID',
        BRIDGE_GRID,
        domain_type='bridge'
    )
    bridge_output = base_output_dir / 'bridge_grid'
    bridge_paths = save_configs(bridge_configs, bridge_output)
    print(f"  BRIDGE-GRID: {len(bridge_configs)} configs → {bridge_output}")
    print()

    # TIMEOUT-CONVERGENCE campaign
    print("Generating TIMEOUT-CONVERGENCE campaign configs...")
    print("-" * 70)

    timeout_configs = generate_campaign_configs(
        'TIMEOUT_CONVERGENCE',
        TIMEOUT_GRID,
        domain_type='standard'
    )
    timeout_output = base_output_dir / 'timeout_convergence'
    timeout_paths = save_configs(timeout_configs, timeout_output)
    print(f"  TIMEOUT-CONVERGENCE: {len(timeout_configs)} configs → {timeout_output}")
    print()

    # CALIBRATION-VALIDATION campaign
    print("Generating CALIBRATION-VALIDATION campaign configs...")
    print("-" * 70)

    calib_configs = generate_campaign_configs(
        'CALIBRATION_VALIDATION',
        CALIBRATION_GRID,
        domain_type='standard'
    )
    calib_output = base_output_dir / 'calibration_validation'
    calib_paths = save_configs(calib_configs, calib_output)
    print(f"  CALIBRATION-VALIDATION: {len(calib_configs)} configs → {calib_output}")
    print()

    # DOMAIN-CONVERGENCE campaign
    print("Generating DOMAIN-CONVERGENCE campaign configs...")
    print("-" * 70)

    domain_configs = []
    for domain_type in ['standard', 'long', 'extended', 'verylong']:
        configs = generate_campaign_configs(
            'DOMAIN_CONVERGENCE',
            DOMAIN_CONVERGENCE_GRID,
            domain_type=domain_type
        )
        output_dir = base_output_dir / 'domain_convergence' / domain_type
        paths = save_configs(configs, output_dir)
        domain_configs.extend(configs)
        print(f"  {domain_type:10s}: {len(configs):3d} configs → {output_dir}")

    print(f"  DOMAIN-CONVERGENCE total: {len(domain_configs)} configs")
    print()

    # Summary
    print("="*70)
    print("CONFIG GENERATION SUMMARY")
    print("="*70)
    print(f"Campaign                 | Configs | Domain Type")
    print("-" * 70)
    print(f"SUPERCRITICAL-LONG       | {supercrit_total:7d} | long/extended/verylong")
    print(f"BRIDGE-GRID              | {len(bridge_configs):7d} | bridge (L=12λJ)")
    print(f"TIMEOUT-CONVERGENCE      | {len(timeout_configs):7d} | standard (L=8λJ)")
    print(f"CALIBRATION-VALIDATION   | {len(calib_configs):7d} | standard (L=8λJ)")
    print(f"DOMAIN-CONVERGENCE       | {len(domain_configs):7d} | all types")
    print("-" * 70)

    total = supercrit_total + len(bridge_configs) + len(timeout_configs) + len(calib_configs) + len(domain_configs)
    print(f"TOTAL                    | {total:7d} |")
    print("="*70)
    print()
    print(f"All configs saved to: {base_output_dir.absolute()}")
    print()

    # Generate manifest
    manifest = {
        'generation_date': '2026-04-27',
        'total_configs': total,
        'campaigns': {
            'SUPERCRITICAL_LONG': {
                'count': supercrit_total,
                'domain_types': ['long', 'extended', 'verylong'],
                'purpose': 'Direct λ/W measurement in supercritical regime'
            },
            'BRIDGE_GRID': {
                'count': len(bridge_configs),
                'domain_type': 'bridge',
                'purpose': 'Validate extrapolation from near-critical to supercritical'
            },
            'TIMEOUT_CONVERGENCE': {
                'count': len(timeout_configs),
                'domain_type': 'standard',
                'purpose': 'Validate timeout adequacy across parameter space'
            },
            'CALIBRATION_VALIDATION': {
                'count': len(calib_configs),
                'domain_type': 'standard',
                'purpose': 'Re-derive calibration factor with uncertainty breakdown'
            },
            'DOMAIN_CONVERGENCE': {
                'count': len(domain_configs),
                'domain_types': ['standard', 'long', 'extended', 'verylong'],
                'purpose': 'Test domain size convergence of λ measurement'
            }
        },
        'parameter_space': {
            'f_range': '[1.1, 2.5]',
            'beta_range': '[0.3, 5.0]',
            'M_range': '[1.0, 3.0]',
            'theta_values': '[30, 60, 90] degrees'
        }
    }

    manifest_path = base_output_dir / 'MANIFEST.json'
    with open(manifest_path, 'w') as f:
        json.dump(manifest, f, indent=2)

    print(f"Manifest saved to: {manifest_path}")
    print()

    # Resource estimate
    print("RESOURCE ESTIMATE")
    print("-" * 70)
    print("Assuming 4 hours per simulation (64 cores, standard domain):")
    cpu_hours_standard = total * 4
    print(f"  Standard domains: {cpu_hours_standard:,} CPU-hours")

    # Extended domains take longer
    n_extended = supercrit_total // 3  # extended + verylong
    cpu_hours_extended = n_extended * 12  # 3x longer
    print(f"  Extended domains: {cpu_hours_extended:,} CPU-hours")

    total_cpu_hours = cpu_hours_standard + cpu_hours_extended
    print(f"  TOTAL: {total_cpu_hours:,} CPU-hours")
    print()
    print(f"On 200-core cluster with 3 concurrent simulations:")
    wall_time_hours = total_cpu_hours / 200
    wall_time_days = wall_time_hours / 24
    print(f"  Estimated wall time: {wall_time_hours:.1f} hours ({wall_time_days:.1f} days)")
    print("="*70)


if __name__ == '__main__':
    main()
