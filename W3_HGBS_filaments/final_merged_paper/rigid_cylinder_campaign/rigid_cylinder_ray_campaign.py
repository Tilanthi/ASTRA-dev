#!/usr/bin/env python3
"""
Ray-based Campaign Manager for Rigid Cylinder Simulations
============================================================

This script manages the submission and analysis of Athena++ simulations
with rigid cylindrical boundary conditions to address the supercritical
extrapolation problem.

Usage:
    python rigid_cylinder_ray_campaign.py [--submit] [--analyze] [--package]

Author: G. J. White
Date: June 2026
"""

import ray
import numpy as np
import subprocess
import os
import json
import glob
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Any
import argparse

# ============================================================================
# CAMPAIGN CONFIGURATION
# ============================================================================

CAMPAIGN_CONFIG = {
    "name": "RIGID_CYLINDER_SUPERCRITICAL",
    "version": "1.0",
    "date": "2026-06-05",

    # Simulation grid
    "line_mass_f": [1.5, 1.8, 2.2, 2.6, 3.0],
    "plasma_beta": [0.5, 1.0, 2.0],
    "mach_m": [1.0],
    "theta_deg": [0.0],
    "seeds_per_point": 3,

    # Domain (long axial direction for longitudinal modes)
    "L_x": 16.0,  # Axial length in λ_J
    "L_y": 2.0,  # Radial extent
    "L_z": 2.0,  # Radial extent

    # Resolution
    "nx": 256,
    "ny": 64,
    "nz": 64,

    # Physics
    "gamma": 1.0,

    # Time
    "t_max": 2.0,  # Maximum time in t_J
    "courant": 0.4,
    "output_interval": 0.05,  # Output every 0.05 t_J

    # Rigid cylinder BC
    "cylinder_radius": 1.0,
    "cylinder_axis": "x",

    # Resources
    "num_cpus": 4,  # Per simulation
    "max_runtime": 7200,  # 2 hours per sim
    "wallclock_hours": 2,
}

# Calculate total simulations
TOTAL_SIMS = (
    len(CAMPAIGN_CONFIG["line_mass_f"]) *
    len(CAMPAIGN_CONFIG["plasma_beta"]) *
    len(CAMPAIGN_CONFIG["mach_m"]) *
    CAMPAIGN_CONFIG["seeds_per_point"]
)

# ============================================================================
# SIMULATION LIST GENERATION
# ============================================================================

def generate_simulation_list() -> List[Dict[str, Any]]:
    """Generate list of all simulation parameters."""

    simulations = []
    sim_id = 0

    for f in CAMPAIGN_CONFIG["line_mass_f"]:
        for beta in CAMPAIGN_CONFIG["plasma_beta"]:
            for mach in CAMPAIGN_CONFIG["mach_m"]:
                for theta in CAMPAIGN_CONFIG["theta_deg"]:
                    for seed in range(1, CAMPAIGN_CONFIG["seeds_per_point"] + 1):

                        sim = {
                            "sim_id": f"rigid_f{f:.1f}_beta{beta:.1f}_m{mach:.1f}_theta{theta:.1f}_seed{seed:02d}",
                            "f": f,
                            "beta": beta,
                            "mach": mach,
                            "theta": theta,
                            "seed": seed,
                            "L_x": CAMPAIGN_CONFIG["L_x"],
                            "L_y": CAMPAIGN_CONFIG["L_y"],
                            "L_z": CAMPAIGN_CONFIG["L_z"],
                            "nx": CAMPAIGN_CONFIG["nx"],
                            "ny": CAMPAIGN_CONFIG["ny"],
                            "nz": CAMPAIGN_CONFIG["nz"],
                            "gamma": CAMPAIGN_CONFIG["gamma"],
                            "t_max": CAMPAIGN_CONFIG["t_max"],
                            "courant": CAMPAIGN_CONFIG["courant"],
                            "cylinder_radius": CAMPAIGN_CONFIG["cylinder_radius"],
                            "num_cpus": CAMPAIGN_CONFIG["num_cpus"],
                        }

                        simulations.append(sim)
                        sim_id += 1

    return simulations

# ============================================================================
# ATHENA++ SETUP
# ============================================================================

def create_initial_conditions(sim: Dict[str, Any], output_dir: str) -> str:
    """Create initial conditions file for rigid cylinder filament."""

    from astropy.io import fits
    from astropy import units as u

    # Create grid
    nx, ny, nz = sim["nx"], sim["ny"], sim["nz"]
    x = np.linspace(0, sim["L_x"], nx)
    y = np.linspace(-sim["L_y"]/2, sim["L_y"]/2, ny)
    z = np.linspace(-sim["L_z"]/2, sim["L_z"]/2, nz)

    XX, YY, ZZ = np.meshgrid(x, y, z, indexing='ij')

    # Radial distance from axis
    RR = np.sqrt(YY**2 + ZZ**2)

    # Critical line mass
    # In simulation units: c_s = 1, G = 1, so M_line,crit = 2
    # For line-mass fraction f: M_line = f * M_line,crit = 2f

    # Density profile (King profile)
    W_core = 0.3  # Core half-width
    rho_center = sim["f"] * 2.0  # Scaled by line-mass

    rho = rho_center * (1 + (RR/W_core)**2)**(-0.5)

    # Apply rigid cylinder BC
    R_cyl = sim["cylinder_radius"] * sim["L_y"] / 2
    mask = RR >= R_cyl
    rho[mask] = 0.0  # Zero density outside cylinder

    # Add perturbations
    np.random.seed(sim["seed"])
    pert_amp = 1e-4

    # Longitudinal sinusoidal perturbation
    # k for most unstable mode
    k_most_unstable = 2 * np.pi / (4 * np.pi)  # λ = 4πH for most unstable

    longitudinal = pert_amp * np.sin(k_most_unstable * XX)
    noise = pert_amp * 0.1 * np.random.randn(*rho.shape)

    rho *= (1 + longitudinal + noise)

    # Magnetic field (longitudinal)
    # For β = c_s^2 / (v_A^2) = 2 / B^2, so B = sqrt(2/β)
    B0 = np.sqrt(2.0 / sim["beta"])
    Bx = np.full_like(rho, B0)
    By = np.zeros_like(rho)
    Bz = np.zeros_like(rho)

    # Zero initial velocity
    Vx = np.zeros_like(rho)
    Vy = np.zeros_like(rho)
    Vz = np.zeros_like(rho)

    # Create FITS file
    ic_filename = Path(output_dir) / f"ic_{sim['sim_id']}.fits"

    # Ensure output directory exists
    Path(output_dir).mkdir(parents=True, exist_ok=True)

    hdu = fits.PrimaryHDU()
    hdu.data = rho
    hdu.header['NAXIS'] = 3
    hdu.header['NAXIS1'] = nx
    hdu.header['NAXIS2'] = ny
    hdu.header['NAXIS3'] = nz
    hdu.header['CTYPE1'] = 'x'
    hdu.header['CTYPE2'] = 'y'
    hdu.header['CTYPE3'] = 'z'
    hdu.header['CUNIT1'] = 'lambda_J'
    hdu.header['CUNIT2'] = 'lambda_J'
    hdu.header['CUNIT3'] = 'lambda_J'

    hdu.writeto(ic_filename, overwrite=True)

    # Also save magnetic field
    bhdu = fits.ImageHDU(data=Bx, header=hdu.header)
    bhdu.header['EXTNAME'] = 'B_x'

    with fits.open(ic_filename, 'update') as hdul:
        hdul.append(bhdu)

    print(f"  Created IC: {ic_filename}")

    return str(ic_filename)

def create_athena_input_file(sim: Dict[str, Any], output_dir: str) -> str:
    """Create Athena++ input file with rigid cylinder BC."""

    input_filename = Path(output_dir) / f"athena_{sim['sim_id']}.inp"

    # Calculate simulation parameters
    L_cyl = sim["cylinder_radius"] * sim["L_y"] / 2
    beta = sim["beta"]
    B0 = np.sqrt(2.0 / beta)

    input_content = f"""# Athena++ input file for rigid cylinder simulation
# Simulation: {sim['sim_id']}

<job>
    problem_id = {sim['sim_id']}
{int(output_dir.split('/')[-1]) % 1000000:06d}
</job>

<problem>
    <problem_type>3D_cartesian</problem_type>
    <coord_system>cartesian</coord_system>

    <x1_min>0.0</x1_min>
    <x1_max>{sim['L_x']}</x1_max>
    <x2_min>{-sim['L_y']/2}</x2_min>
    <x2_max>{sim['L_y']/2}</x2_max>
    <x3_min>{-sim['L_z']/2}</x3_min>
    <x3_max>{sim['L_z']/2}</x3_max>

    <gravity>g_mode = 'planar'</gravity>

    <hydro>
        <reconstruction>plm</reconstruction>
        <riemann>hlle</riemann>
        <integrator>vl2</integrator>
        <correction_ctype>src</correction_ctype>
        <order>{sim['courant']}</order>
        <fluid>
            <gamma>{sim['gamma']}</gamma>
        </fluid>
    </hydro>

    <mhd>
        <b_scaling>uniform</b_scaling>
        <reconstruction>plm</reconstruction>
        <riemann>hlle</riemann>
        <integrator>vl2</integrator>
        <correction_ctype>src</correction_ctype>
        <order>{sim['courant']}</order>
    </mhd>

    <particles>
        <num_particles>0</num_particles>
    </particles>

    <output>
        <output_dir>{output_dir}/outputs</output_dir>
        <file_prefix>rigid_{sim['sim_id']}</file_prefix>

        <dt_out>{sim['t_max']/100.0}</dt_out>
        <iouttype_ih>
            <out1>
                <variable>
                    <prim var_name='rho'/>
                    <prim var_name='vx1'/>
                    <prim var_name='vx2'/>
                    <prim var_name='vx3'/>
                    <prim var_name='Bx1'/>
                    <prim var_name='Bx2'/>
                    <prim var_name='Bx3'/>
                </variable>
            </out1>
        </iouttype_ih>

        <hst_out>
            <level>full</level>
        </hst_out>

        <restart_out>
            <level>full</level>
        </restart_out>
    </output>

    <time>
        <cfl_number>{sim['courant']}</cfl_number>
        <nlimit>10000000</nlimit>
        <tlim>{sim['t_max']}</tlim>
        <integrator>rk3</integrator>
        <first_order/>
    </time>

    <mboundaries>
        <x1_bcs>
            <bc_ix1_dens>outflow</bc_ix1_dens>
            <bc_ix1_vel>outflow</bc_ix1_vel>
            <bc_ix1_mag>outflow</bc_ix1_mag>
            <bc_ox1_dens>outflow</bc_ox1_dens>
            <bc_ox1_vel>outflow</bc_ox1_vel>
            <bc_ox1_mag>outflow</bc_ox1_mag>
        </x1_bcs>

        <x2_bcs>
            <bc_ix2_dens>
                <ix2_bc>reflecting</ix2_bc>
                <ix2_bc_value>0.0</ix2_bc_value>
            </bc_ix2_dens>
            <bc_ix2_vel>reflecting</bc_ix2_vel>
            <bc_ix2_mag>reflecting</bc_ix2_mag>

            <bc_ox2_dens>
                <ox2_bc>reflecting</ox2_bc>
                <ox2_bc_value>0.0</ox2_bc_value>
            </bc_ox2_dens>
            <bc_ox2_vel>reflecting</bc_ox2_vel>
            <bc_ox2_mag>reflecting</bc_ox2_mag>
        </x2_bcs>

        <x3_bcs>
            <bc_ix3_dens>
                <ix3_bc>reflecting</ix3_bc>
                <ix3_bc_value>0.0</ix3_bc_value>
            </bc_ix3_dens>
            <bc_ix3_vel>reflecting</bc_ix3_vel>
            <bc_ix3_mag>reflecting</bc_ix3_mag>

            <bc_ox3_dens>
                <ox3_bc>reflecting</ox3_bc>
                <ox3_bc_value>0.0</ox3_bc_value>
            </bc_ox3_dens>
            <bc_ox3_vel>reflecting</bc_ox3_vel>
            <bc_ox3_mag>reflecting</bc_ox3_mag>
        </x3_bcs>
    </mboundaries>

    <ambient>
        <rho>
            <rho_floor>1.0e-10</rho_floor>
            <rho_ceiling>1.0e10</rho_ceiling>
        </rho>
    </ambient>
</problem>
"""

    input_filename.write_text(input_content)

    print(f"  Created input: {input_filename}")

    return str(input_filename)

# ============================================================================
# RAY ACTORS
# ============================================================================

@ray.remote(num_cpus=4, max_calls=1)
def run_single_simulation(sim: Dict[str, Any]) -> Dict[str, Any]:
    """Run a single Athena++ simulation."""

    print(f"Starting simulation: {sim['sim_id']}")

    # Create output directory
    output_dir = f"/rigid_cylinder_outputs/{sim['sim_id']}"
    os.makedirs(output_dir, exist_ok=True)
    os.makedirs(f"{output_dir}/outputs", exist_ok=True)

    try:
        # Create input files
        ic_file = create_initial_conditions(sim, output_dir)
        input_file = create_athena_input_file(sim, output_dir)

        # Construct Athena++ command
        # NOTE: Update this path to point to your Athena++ installation
        athena_bin = "/usr/local/bin/athena"  # UPDATE THIS PATH
        athena_cmd = [
            athena_bin,
            "-i", "athena_" + sim['sim_id'] + ".inp",
            "-r", "ic_" + sim['sim_id'] + ".fits",
        ]

        # Run simulation
        start_time = datetime.now()

        result = subprocess.run(
            athena_cmd,
            cwd=output_dir,
            capture_output=True,
            text=True,
            timeout=CAMPAIGN_CONFIG["max_runtime"],
        )

        end_time = datetime.now()
        runtime = (end_time - start_time).total_seconds()

        success = result.returncode == 0

        # Check output
        hdf5_files = glob.glob(f"{output_dir}/outputs/*.hdf5")

        return {
            "sim_id": sim["sim_id"],
            "f": sim["f"],
            "beta": sim["beta"],
            "mach": sim["mach"],
            "theta": sim["theta"],
            "seed": sim["seed"],
            "success": success,
            "runtime_seconds": runtime,
            "output_dir": output_dir,
            "n_hdf5_files": len(hdf5_files),
            "stdout": result.stdout if not success else None,
            "stderr": result.stderr,
        }

    except subprocess.TimeoutExpired:
        return {
            "sim_id": sim["sim_id"],
            "f": sim["f"],
            "beta": sim["beta"],
            "mach": sim["mach"],
            "theta": sim["theta"],
            "seed": sim["seed"],
            "success": False,
            "error": "Timeout after {} seconds".format(CAMPAIGN_CONFIG["max_runtime"]),
        }
    except Exception as e:
        return {
            "sim_id": sim["sim_id"],
            "f": sim["f"],
            "beta": sim["beta"],
            "mach": sim["mach"],
            "theta": sim["theta"],
            "seed": sim["seed"],
            "success": False,
            "error": str(e),
        }

# ============================================================================
# ANALYSIS FUNCTIONS
# ============================================================================

def analyze_lambda_W(hdf5_file: str, sim_params: Dict[str, Any]) -> Dict[str, Any]:
    """Extract λ/W measurement from HDF5 output."""

    import h5py
    from scipy.signal import find_peaks

    try:
        with h5py.File(hdf5_file, 'r') as f:
            # Get density from last time step
            rho = f['density'][-1]  # Shape: (nx, ny, nz, 1)
            rho = rho.squeeze()

        # Extract axial profile (average over y-z)
        rho_axial = np.mean(rho, axis=(1, 2))

        # Normalize
        rho_norm = rho_axial / np.mean(rho_axial)

        # Find peaks (cores)
        peaks, properties = find_peaks(
            rho_norm,
            distance=int(sim_params["nx"] / 64),  # Minimum spacing
            prominence=0.1,
            width=5
        )

        if len(peaks) < 2:
            return {
                "n_peaks": len(peaks),
                "lambda_W": None,
                "classification": "NO_FRAGMENTATION" if len(peaks) < 2 else "SINGLE_PEAK"
            }

        # Calculate spacings
        dx = sim_params["L_x"] / sim_params["nx"]
        spacings = np.diff(peaks) * dx

        # Median spacing
        lambda_median = np.median(spacings)

        # Convert to λ/W
        W_cyl = sim_params["cylinder_radius"]
        lambda_by_W = lambda_median / W_cyl

        return {
            "n_peaks": len(peaks),
            "lambda_W": lambda_by_W,
            "spacings": spacings.tolist(),
            "classification": "FRAGMENTED",
        }

    except Exception as e:
        return {
            "error": str(e),
            "classification": "ERROR",
        }

def analyze_campaign_results(results: List[Dict[str, Any]]) -> Dict[str, Any]:
    """Analyze all simulation results."""

    analyzed = []

    for result in results:
        if not result.get("success", False):
            analyzed.append({
                **result,
                "classification": "FAILED",
                "lambda_W": None,
            })
            continue

        # Find HDF5 files
        hdf5_files = glob.glob(f"{result['output_dir']}/outputs/*.hdf5")

        if not hdf5_files:
            analyzed.append({
                **result,
                "classification": "NO_OUTPUT",
                "lambda_W": None,
            })
            continue

        # Analyze the last HDF5 file
        hdf5_file = sorted(hdf5_files)[-1]

        sim_params = {
            "L_x": result["L_x"],
            "nx": result["nx"],
            "cylinder_radius": result["cylinder_radius"],
        }

        analysis = analyze_lambda_W(hdf5_file, sim_params)

        analyzed.append({
            **result,
            "analysis": analysis,
            "classification": analysis.get("classification", "UNKNOWN"),
            "lambda_W": analysis.get("lambda_W"),
        })

    # Calculate statistics
    frag_results = [r for r in analyzed if r.get("classification") == "FRAGMENTED"]

    if frag_results:
        lambda_W_values = [r["lambda_W"] for r in frag_results if r["lambda_W"] is not None]

        # Fit λ/W vs. f
        from scipy.optimize import curve_fit

        def power_law(x, a, b):
            return a * x**b

        if len(lambda_W_values) > 3:
            f_values = [r["f"] for r in frag_results if r["lambda_W"] is not None]

            try:
                popt, pcov = curve_fit(power_law, f_values, lambda_W_values)
                perr = np.sqrt(np.diag(pcov))

                fit_results = {
                    "lambda_W_f_power_law_a": popt[0],
                    "lambda_W_f_power_law_b": popt[1],
                    "lambda_W_f_power_law_a_err": perr[0],
                    "lambda_W_f_power_law_b_err": perr[1],
                }
            except:
                fit_results = {"error": "Fit failed"}
        else:
            fit_results = {"error": "Insufficient data"}
    else:
        lambda_W_values = []
        fit_results = {"error": "No fragmentation detected"}

    return {
        "total_simulations": len(results),
        "successful": sum(1 for r in results if r.get("success", False)),
        "fragmented": len(frag_results),
        "analyzed": analyzed,
        "lambda_W_values": lambda_W_values,
        "fit_results": fit_results,
    }

# ============================================================================
# PACKAGING
# ============================================================================

def package_campaign(results_file: str, output_dir: str) -> str:
    """Package campaign results into tar.gz for GitHub."""

    from datetime import datetime

    # Create package directory
    package_name = f"rigid_cylinder_campaign_{datetime.now().strftime('%Y%m%d')}"
    package_dir = Path(output_dir) / package_name
    package_dir.mkdir(parents=True, exist_ok=True)

    # Copy campaign spec
    import shutil
    shutil.copy2(__file__, package_dir / "rigid_cylinder_ray_campaign.py")

    # Copy README
    readme_src = Path(__file__).parent / "README.md"
    if readme_src.exists():
        shutil.copy2(readme_src, package_dir / "README.md")

    # Copy results
    if Path(results_file).exists():
        shutil.copy2(results_file, package_dir / "campaign_results.json")

    # Create analysis summary
    with open(results_file) as f:
        results = json.load(f)

    summary = {
        "campaign": "RIGID_CYLINDER_SUPERCRITICAL",
        "date": datetime.now().isoformat(),
        "total_simulations": len(results.get("results", [])),
        "successful": sum(1 for r in results.get("results", []) if r.get("success", False)),
        "fragmented": sum(1 for r in results.get("results", []) if r.get("analysis", {}).get("classification") == "FRAGMENTED"),
    }

    with open(package_dir / "summary.json", 'w') as f:
        json.dump(summary, f, indent=2)

    # Create tar.gz
    tarball = f"{package_dir}.tar.gz"

    subprocess.run([
        "tar", "-czf", tarball,
        "-C", str(Path(package_dir).parent),
        package_name
    ], check=True)

    print(f"\n✓ Campaign packaged: {tarball}")
    print(f"  Size: {Path(tarball).stat().st_size / (1024**3):.1f} GB")

    return tarball

def push_to_github(tarball_path: str, repo_url: str = "git@github.com:Tilanthi/ASTRA-dev.git") -> str:
    """Push packaged campaign to GitHub repository."""

    # Move to repository directory
    repo_dir = "/Users/gjw255/astrodata/SWARM/ASTRA-dev"

    # Copy tarball to repo
    tarball_name = Path(tarball_path).name
    repo_tarball = Path(repo_dir) / "campaigns" / tarball_name

    Path(repo_dir).joinpath("campaigns").mkdir(parents=True, exist_ok=True)
    shutil.copy2(tarball_path, repo_tarball)

    # Git operations
    os.chdir(repo_dir)

    try:
        # Add file
        subprocess.run(["git", "add", f"campaigns/{tarball_name}"], check=True)

        # Commit
        commit_msg = f"Add rigid cylinder campaign: {tarball_name}"
        subprocess.run(["git", "commit", "-m", commit_msg], check=True)

        # Push
        subprocess.run(["git", "push", "origin", "main"], check=True)

        full_url = f"{repo_url.rstrip('.git')}/blob/main/campaigns/{tarball_name}"
        print(f"\n✓ Pushed to GitHub: {full_url}")

        return full_url

    except subprocess.CalledProcessError as e:
        print(f"✗ Git operation failed: {e}")
        return f"ERROR: {e}"

# ============================================================================
# MAIN EXECUTION
# ============================================================================

def main():
    parser = argparse.ArgumentParser(description="Rigid Cylinder Campaign Manager")
    parser.add_argument("--submit", action="store_true", help="Submit simulations to Ray")
    parser.add_argument("--analyze", action="store_true", help="Analyze completed simulations")
    parser.add_argument("--package", action="store_true", help="Package and push results to GitHub")
    parser.add_argument("--config", action="store_true", help="Show campaign configuration")

    args = parser.parse_args()

    print("="*70)
    print("RIGID CYLINDER SUPERCRITICAL CAMPAIGN")
    print("="*70)
    print(f"Total simulations: {TOTAL_SIMS}")
    print(f"Parameters: f ∈ {CAMPAIGN_CONFIG['line_mass_f']}")
    print(f"            β ∈ {CAMPAIGN_CONFIG['plasma_beta']}")
    print(f"            Seeds per point: {CAMPAIGN_CONFIG['seeds_per_point']}")
    print("="*70)

    # Initialize Ray
    ray.init(
        num_cpus=220,
        _memory=400 * 1024 * 1024,
        _object_store_memory=100 * 1024 * 1024,
        logging_level="INFO",
    )

    try:
        if args.config:
            print("\nCampaign Configuration:")
            print(json.dumps(CAMPAIGN_CONFIG, indent=2))
            return

        if args.submit:
            print("\n🚀 Launching campaign on Ray cluster...")

            # Generate simulation list
            simulations = generate_simulation_list()
            print(f"Generated {len(simulations)} simulations")

            # Submit to Ray
            print(f"\nSubmitting to Ray (220 CPUs)...")
            futures = [run_single_simulation.remote(sim) for sim in simulations]

            # Wait for completion
            print("\n⏳ Running simulations (this will take several hours)...")
            results = ray.get(futures)

            # Save results
            results_file = "rigid_cylinder_campaign_results.json"
            with open(results_file, 'w') as f:
                json.dump({
                    "campaign": CAMPAIGN_CONFIG,
                    "results": results,
                    "timestamp": datetime.now().isoformat(),
                }, f, indent=2)

            print(f"\n✓ Results saved to: {results_file}")

            # Automatic analysis
            print("\n📊 Analyzing results...")
            analysis = analyze_campaign_results(results)

            analysis_file = "rigid_cylinder_analysis.json"
            with open(analysis_file, 'w') as f:
                json.dump(analysis, f, indent=2)

            print(f"✓ Analysis saved to: {analysis_file}")

            # Show summary
            print("\n" + "="*70)
            print("CAMPAIGN SUMMARY")
            print("="*70)
            print(f"Total simulations: {analysis['total_simulations']}")
            print(f"Successful: {analysis['successful']}")
            print(f"Fragmented: {analysis['fragmented']}")
            print(f"λ/W values: {analysis['lambda_W_values']}")

            if 'fit_results' in analysis and 'error' not in analysis['fit_results']:
                fit = analysis['fit_results']
                print(f"\nλ/W(f) = {fit['lambda_W_f_power_law_a']:.2f} × f^{fit['lambda_W_f_power_law_b']:.2f}")

            # Package
            tarball = package_campaign(results_file, "/rigid_cylinder_outputs")

            # Push to GitHub
            github_url = push_to_github(tarball)

            print(f"\n{'='*70}")
            print("FULL PATH TO PACKAGE:")
            print(f"{'='*70}")
            print(f"\n{tarball}\n")
            print(f"GitHub URL: {github_url}")

        elif args.analyze:
            print("\n📊 Analyzing existing results...")
            results_file = "rigid_cylinder_campaign_results.json"

            with open(results_file) as f:
                data = json.load(f)

            analysis = analyze_campaign_results(data["results"])

            print(f"\n✓ Analysis saved to: rigid_cylinder_analysis.json")
            print(f"Fragmented: {analysis['fragmented']}/{len(data['results'])}")
            print(f"λ/W values: {analysis['lambda_W_values']}")

        elif args.package:
            results_file = "rigid_cylinder_campaign_results.json"
            tarball = package_campaign(results_file, "/rigid_cylinder_outputs")
            github_url = push_to_github(tarball)

            print(f"\n{'='*70}")
            print("FULL PATH TO PACKAGE:")
            print(f"{'='*70}")
            print(f"\n{tarball}\n")
            print(f"GitHub URL: {github_url}")

    finally:
        ray.shutdown()

if __name__ == "__main__":
    main()
