#!/usr/bin/env python3
"""
Athena++ Rigid Cylinder Campaign: Supercritical Filament Fragmentation
================================================================================

Purpose: Address the referee's concern about extrapolation from near-critical
(f ≈ 1.0–1.2) to supercritical (f ≥ 1.5) regime by using rigid cylindrical
boundary conditions to suppress radial collapse, allowing longitudinal
fragmentation modes to develop.

Campaign Specification:
- f = 1.5, 1.8, 2.2, 2.6, 3.0 (5 line-mass values)
- β = 0.5, 1.0, 2.0 (3 plasma beta values)
- θ = 0° (longitudinal B-field only)
- M = 1.0 (moderate turbulence)
- Seeds: 3 per parameter point (45 simulations total)

Boundary Conditions:
- Rigid cylindrical wall at r = R_filament
- Outflow BC at axial boundaries
- This suppresses radial collapse while allowing longitudinal modes

Measurements:
- High-cadence HDF5 snapshots (every 0.05 t_J)
- Extract λ/W from density peaks along filament axis
- Measure fragmentation timescale t_frag
- Characterize mode structure

Author: G. J. White
Date: June 2026
"""

import ray
from ray import serve
import numpy as np
import subprocess
import os
import json
from pathlib import Path
from datetime import datetime

# ============================================================================
# CAMPAIGN CONFIGURATION
# ============================================================================

CAMPAIGN_CONFIG = {
    "name": "RIGID_CYLINDER_SUPERCRITICAL",
    "description": "Supercritical filament fragmentation with rigid cylindrical boundary",
    "date": "2026-06-05",

    # Simulation parameters
    "line_mass_f": [1.5, 1.8, 2.2, 2.6, 3.0],  # f values
    "plasma_beta": [0.5, 1.0, 2.0],                   # β values
    "mach_m": [1.0],                                    # Fixed M
    "theta_deg": [0.0],                                 # Longitudinal B
    "seeds_per_point": 3,                              # Random seeds
    "resolution": 128,                                 # 128^3 for speed

    # Physics
    "gamma": 1.0,                                      # Isothermal
    "eos_type": "isothermal",
    "boundary_type": "rigid_cylinder",

    # Domain (longer cylinder for longitudinal modes)
    "l_x": 16.0,              # Axial length (in λ_J units)
    "l_y": 1.0,               # Radial (in λ_J units)
    "l_z": 1.0,               # Radial (in λ_J units)

    # Grid
    "nx": 1024,               # Axial resolution
    "ny": 64,                # Radial resolution
    "nz": 64,                # Radial resolution

    # Time integration
    "t_max": 2.0,             # Maximum time (in t_J)
    "courant": 0.3,
    "dt_out": 0.05,           # Output cadence (in t_J)

    # Rigid cylinder BC
    "cylinder_radius": 1.0,   # In units of l_y/2
    "cylinder_axis": "x",
}

# ============================================================================
# ATHENA++ PROBLEM GENERATOR TEMPLATE
# ============================================================================

PROBLEM_TEMPLATE = """
# Athena++ Rigid Cylinder Filament Problem File
# Auto-generated for rigid_cylinder_campaign

<problem>
    <problem_type>2D_or_3D_cartesian</problem_type>
    <coord_system>cartesian</coord_system>
    <x1_min>0.0</x1_min>
    <x1_max>{l_x}</x1_max>
    <x2_min>{x2_min}</x2_min>
    <x2_max>{x2_max}</x2_max>
    <x3_min>{x3_min}</x3_min>
    <x3_max>{x3_max}</x3_max>

    <gravity>g_mode = 'planar'</gravity>

    <hydro>
        <hydro Reconstruction = 'linear Reconstruction = 'plm'</reconstruction>
        <riemann>solver = 'hlle'</solver>

        <hydro_integration>
            <integrator>vl2</integrator>
            <correction_ctype> 'src'</correction_ctype>
        </hydro_integration>

        <order>{courant_number}</order>

        <fluid>
            <num_fluids>1</num_fluids>
            <fluid>
                <gamma>{gamma}</gamma>
            </fluid>
        </fluid>
    </hydro>

    <mhd>
        <b_scaling '{magnetic_scaling}'

        <b_order>{b_order}</b_order>

        <reconstruction> 'plm'</reconstruction>
        <riemann> 'hlle'</riemann>

        <integrator> 'vl2'</integrator>
        <correction_ctype> 'src'</correction_ctype>
    </mhd>

    <particles>
        <num_particles>0</num_particles>
    </particles>

    <outputs>
        <output {
            <output_dir>{output_dir}</output_dir>
            <file_prefix>file_prefix</file_prefix>
            <file_type>{file_type}</file_type>
            <dt_out>{dt_out}</dt_out>
            <iouttype_ih>
                <out1>
                    <variable>
                        <prim var_name='rho'
                        <prim var_name='vx1'
                        <prim var_name='vx2'
                        <prim var_name='vx3'
                    </variable>
                    <level>full</level>
                </out1>
            </iouttype_ih>

            <summary_out>
                <variables>
                    <variable>
                        <prim var_name='rho'
                        <prim var_name='vx1'
                        <prim var_name='vx2'
                        <prim var_name='vx3'
                    </variable>
                </variables>
                <level>full</level>
            </summary_out>

            <hst_out>
                <level>full</level>
                <file_prefix'hst'</file_prefix>
            </hst_out>
        </output>

        <output {
            <output_dir>{output_dir}</output_dir>
            <file_prefix>file_prefix</file_prefix>
            <file_type>'hdf5'</file_type>
            <dt_out>{dt_out_hdf5}</dt_out>
            <iouttype_ih>
                <out1>
                    <variable>
                        <prim var_name='rho'
                        <prim var_name='vx1'
                        <prim var_name='vx2'
                        <prim var_name='vx3'
                    </variable>
                    <level>full</level>
                </out1>
            </iouttype_ih>

            <summary_out>
                <variables>
                    <variable>
                        <prim var_name='rho'
                    </variable>
                </variables>
                <level>full</level>
            </summary_out>
        </output>
    </outputs>

    <time>
        <cfl_number>{courant}</cfl_number>
        <nlimit>10000000</nlimit>
        <tlim>{t_max}</tlim>

        <integrator> 'rk3'</integrator>
        <first_order></first_order>
    </time>

    <mboundaries>
        <x1_bcs>
            <bc_ix1_dens>
                <bc_ix1_vel>
                <bc_ix1_mag>
            </bc_ix1_dens>
            <bc_ox1_dens>
                <bc_ox1_vel>
                <bc_ox1_mag>
            </bc_ox1_dens>
        </x1_bcs>

        <x2_bcs>
            <bc_ix2_dens>
                <bc_ix2_vel>
                <bc_ix2_mag>
            </bc_ix2_dens>
            <bc_ox2_dens>
                <bc_ox2_vel>
                <bc_ox2_mag>
            </bc_ox2_dens>
        </x2_bcs>

        <x3_bcs>
            <bc_ix3_dens>
                <bc_ix3_vel>
                <bc_ix3_mag>
            </bc_ix3_dens>
            <bc_ox3_dens>
                <bc_ox3_vel>
                <bc_ox3_mag>
            </bc_ox3_dens>
        </x3_bcs>
    </mboundaries>
</problem>
"""

# ============================================================================
# RAY EXECUTION
# ============================================================================

def create_athena_problem_file(sim_params, output_dir):
    """Create Athena++ problem file for rigid cylinder simulation."""

    # Fill in template
    problem_content = PROBLEM_TEMPLATE.format(
        l_x=sim_params['l_x'],
        l_y=sim_params['l_y'],
        l_z=sim_params['l_z'],
        x2_min=-sim_params['l_y']/2,
        x2_max=sim_params['l_y']/2,
        x3_min=-sim_params['l_z']/2,
        x3_max=sim_params['l_z']/2,
        gamma=sim_params['gamma'],
        courant_number=sim_params['courant_number'],
        courant=sim_params['courant'],
        magnetic_scaling=sim_params.get('magnetic_scaling', 'uniform'),
        b_order=sim_params.get('b_order', 2),
        output_dir=output_dir,
        file_type='tab',
        dt_out=sim_params['dt_out'],
        dt_out_hdf5=sim_params['dt_out_hdf5'],
        t_max=sim_params['t_max'],
    )

    problem_file = Path(output_dir) / "rigid_cylinder_problem.block"
    problem_file.write_text(problem_content)

    return str(problem_file)

def run_athena_simulation(sim_params):
    """Run a single Athena++ simulation with Ray."""

    # Create output directory
    output_dir = f"{sim_params['output_base']}/f{sim_params['f']}_beta{sim_params['beta']}_seed{sim_params['seed']}"
    os.makedirs(output_dir, exist_ok=True)

    # Create problem file
    problem_file = create_athena_problem_file(sim_params, output_dir)

    # Set up initial conditions
    ic_file = create_rigid_cylinder_initial_conditions(sim_params, output_dir)

    # Build Athena++ command
    athena_exe = "/path/to/athena/bin/athena"  # Update this path
    cmd = [
        athena_exe,
        "-i", problem_file,
        "-r", ic_file,
        "-t", str(sim_params['ncores']),
        ">", f"{output_dir}/athena.log", "2>&1"
    ]

    # Run simulation
    try:
        result = subprocess.run(
            " ".join(cmd),
            shell=True,
            cwd=output_dir,
            timeout=7200,  # 2 hour timeout
            capture_output=True,
            text=True
        )

        success = result.returncode == 0

        return {
            "sim_id": sim_params['sim_id'],
            "f": sim_params['f'],
            "beta": sim_params['beta'],
            "seed": sim_params['seed'],
            "success": success,
            "output_dir": output_dir,
            "log": result.stdout,
            "error": result.stderr if not success else None
        }

    except subprocess.TimeoutExpired:
        return {
            "sim_id": sim_params['sim_id'],
            "f": sim_params['f'],
            "beta": sim_params['beta'],
            "seed": sim_params['seed'],
            "success": False,
            "output_dir": output_dir,
            "error": "Timeout after 2 hours"
        }
    except Exception as e:
        return {
            "sim_id": sim_params['sim_id'],
            "f": sim_params['f'],
            "beta": sim_params['beta'],
            "seed": sim_params['seed'],
            "success": False,
            "output_dir": output_dir,
            "error": str(e)
        }

def create_rigid_cylinder_initial_conditions(sim_params, output_dir):
    """Create initial conditions with rigid cylinder boundary."""

    from astropy.io import fits
    from astropy import units as u

    # Physical parameters
    f = sim_params['f']
    beta = sim_params['beta']
    seed = sim_params['seed']

    # Grid dimensions
    nx = sim_params['nx']
    ny = sim_params['ny']
    nz = sim_params['nz']

    # Create coordinate arrays
    x = np.linspace(0, sim_params['l_x'], nx)
    y = np.linspace(-sim_params['l_y']/2, sim_params['l_y']/2, ny)
    z = np.linspace(-sim_params['l_z']/2, sim_params['l_z']/2, nz)

    XX, YY, ZZ = np.meshgrid(x, y, z, indexing='ij')

    # Calculate radial distance from cylinder axis
    RR = np.sqrt(YY**2 + ZZ**2)

    # Critical line mass for isothermal cylinder
    # M_line,crit = 2*c_s^2/G
    # In simulation units: c_s = 1, G = 1
    # So M_line,crit = 2

    # Set up filament density profile
    # Density profile: King profile with core radius = W_core
    W_core = 0.3  # Core half-width in λ_J units
    rho_center = f * 2.0  # Scaled by line-mass fraction

    rho = rho_center * (1 + (RR/W_core)**2)**(-0.5)

    # Apply rigid cylinder boundary condition
    # Mask out region outside cylinder
    cylinder_radius = sim_params.get('cylinder_radius', 1.0) * sim_params['l_y']/2
    mask = RR > cylinder_radius
    rho[mask] = 0.0  # Or set to very low value

    # Add perturbations
    np.random.seed(seed)
    perturbation_amplitude = 1e-4

    # Longitudinal sinusoidal perturbation
    # k = 2π/λ where λ = 4πH (most unstable mode)
    k_most_unstable = 0.5  # In simulation units

    longitudinal_perturbation = perturbation_amplitude * np.sin(k_most_unstable * XX)

    # Small random turbulence
    noise = perturbation_amplitude * np.random.randn(*rho.shape) * 0.1
    rho *= (1 + longitudinal_perturbation + noise)

    # Magnetic field (longitudinal)
    # B_x = B0, B_y = B_z = 0
    # B0 = sqrt(2/β) for c_s = 1, ρ = 1
    B0 = np.sqrt(2.0/beta)

    Bx = np.full_like(rho, B0)
    By = np.zeros_like(rho)
    Bz = np.zeros_like(rho)

    # Velocities (initially zero)
    Vx = np.zeros_like(rho)
    Vy = np.zeros_like(rho)
    Vz = np.zeros_like(rho)

    # Create FITS file
    hdu = fits.PrimaryHDU()
    hdu.data = rho
    hdu.header['NAXIS'] = 3
    hdu.header['NAXIS1'] = nx
    hdu.header['NAXIS2'] = ny
    hdu.header['NAXIS3'] = nz

    ic_file = Path(output_dir) / "rigid_cylinder_initial_conditions.fits"
    hdu.writeto(ic_file, overwrite=True)

    return str(ic_file)

@ray.remote(num_cpus=4, num_gpus=0)
def run_simulation_remote(sim_params):
    """Run simulation on Ray worker."""
    return run_athena_simulation(sim_params)

def generate_simulation_list():
    """Generate list of all simulations to run."""

    simulations = []
    sim_id = 0

    for f in CAMPAIGN_CONFIG['line_mass_f']:
        for beta in CAMPAIGN_CONFIG['plasma_beta']:
            for seed in range(1, CAMPAIGN_CONFIG['seeds_per_point'] + 1):

                sim_params = {
                    'sim_id': f"rigid_f{f}_beta{beta}_seed{seed}",
                    'f': f,
                    'beta': beta,
                    'theta': CAMPAIGN_CONFIG['theta_deg'],
                    'mach_m': CAMPAIGN_CONFIG['mach_m'],
                    'seed': seed,
                    'gamma': CAMPAIGN_CONFIG['gamma'],
                    'courant': CAMPAIGN_CONFIG['courant'],
                    'courant_number': 0.4,
                    'dt_out': CAMPAIGN_CONFIG['dt_out'],
                    'dt_out_hdf5': CAMPAIGN_CONFIG['dt_out_hdf5'],
                    't_max': CAMPAIGN_CONFIG['t_max'],
                    'l_x': CAMPAIGN_CONFIG['l_x'],
                    'l_y': CAMPAIGN_CONFIG['l_y'],
                    'l_z': CAMPAIGN_CONFIG['l_z'],
                    'nx': CAMPAIGN_CONFIG['nx'],
                    'ny': CAMPAIGN_CONFIG['ny'],
                    'nz': CAMPAIGN_CONFIG['nz'],
                    'magnetic_scaling': 'uniform',
                    'b_order': 2,
                    'ncores': 4,
                    'output_base': '/path/to/output/rigid_cylinder_campaign',
                }

                simulations.append(sim_params)
                sim_id += 1

    return simulations

def main():
    """Main execution function."""

    print("="*70)
    print("RIGID CYLINDER SUPERCRITICAL FILAMENT CAMPAIGN")
    print("="*70)
    print(f"Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"Total simulations: {len(CAMPAIGN_CONFIG['line_mass_f']) * len(CAMPAIGN_CONFIG['plasma_beta']) * CAMPAIGN_CONFIG['seeds_per_point']}")
    print()

    # Initialize Ray
    ray.init(
        num_cpus=220,
        _memory=400 * 1024 * 1024,  # 400 GB memory
        _object_store_memory=100 * 1024 * 1024,
        logging_level="INFO",
    )

    try:
        # Generate simulation list
        print("Generating simulation list...")
        simulations = generate_simulation_list()
        print(f"Total simulations to run: {len(simulations)}")

        # Submit simulations to Ray
        print("Submitting simulations to Ray cluster...")
        futures = [run_simulation_remote.remote(sim) for sim in simulations]

        # Collect results
        print(f"\nRunning {len(futures)} simulations...")
        print("="*70)

        results = []
        for i, future in enumerate(ray.as_completed(futures)):
            result = ray.get(future)
            results.append(result)

            status = "✓" if result['success'] else "✗"
            print(f"[{i+1:3d}/{len(futures)}] {status} f={result['f']:.1f} β={result['beta']:.1f} seed={result['seed']}: ", end="")

            if result['success']:
                print("SUCCESS")
            else:
                print(f"FAILED - {result.get('error', 'Unknown error')}")

        # Save results
        results_file = f"{CAMPAIGN_CONFIG['output_base']}/campaign_results.json"
        os.makedirs(os.path.dirname(results_file), exist_ok=True)

        with open(results_file, 'w') as f:
            json.dump({
                'campaign_config': CAMPAIGN_CONFIG,
                'results': results,
                'timestamp': datetime.now().isoformat(),
            }, f, indent=2)

        print()
        print("="*70)
        print(f"Results saved to: {results_file}")
        print("="*70)

    finally:
        ray.shutdown()

if __name__ == '__main__':
    main()
