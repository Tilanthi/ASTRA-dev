#!/usr/bin/env python3
"""
TEST_M3_RESOLUTION: Resolution Convergence Test for Stochastic Zone
Ray-based parallel execution of Athena++ filament fragmentation simulations

Purpose: Address theoretical reviewer concern T-M3 — validate whether apparent
stochastic behavior in DTC transition zone reflects physical behavior or numerical noise

Author: ASTRA System
Date: 2026-04-21
"""

import os
import sys
import json
import time
import subprocess
import numpy as np
from pathlib import Path
from itertools import product

# ── Configuration ────────────────────────────────────────────────────────────

# Paths (adjust for your HPC system)
ATHENA_BIN = os.path.expanduser("~/athena/bin/athena")
WORK_DIR = Path.cwd() / "results"
STATUS_FILE = Path.cwd() / "status_resolution.json"
LOG_DIR = Path.cwd() / "logs"

# Ray configuration
N_PROCS_PER_SIM = 16   # MPI processes per Athena++ run
N_CPUS_AVAILABLE = 220  # Total cores on your HPC cluster

# Domain configuration (from DTC)
FOUR_PI_G = 4.0 * np.pi**2  # 39.478 — sets λ_J = 1.0
L1, L2, L3 = 8.0, 2.0, 2.0    # Domain dimensions
TLIM = 4.0                      # Run time in code units
CFL = 0.3
DT_OUTPUT = 0.5                 # HDF5 output interval

# Load test points
with open(Path.cwd() / "config" / "test_points.json", "r") as f:
    CONFIG = json.load(f)

TEST_POINTS = CONFIG["test_points"]
RESOLUTIONS = CONFIG["resolutions"]
SEEDS = CONFIG["seeds"]

print(f"TEST_M3_RESOLUTION: Resolution convergence test")
print(f"  Test points: {len(TEST_POINTS)}")
print(f"  Resolutions: {len(RESOLUTIONS)} ({[r['name'] for r in RESOLUTIONS]})")
print(f"  Seeds: {SEEDS}")
print(f"  Total simulations: {len(TEST_POINTS) * len(RESOLUTIONS) * len(SEEDS)}")

# ── Helper functions ───────────────────────────────────────────────────────────

def wavelength_for_beta(beta):
    """Magneto-Jeans wavelength (code units) with 4πG = 4π²."""
    return np.sqrt(1.0 + 2.0 / beta)

def make_input_file(sim, sim_dir):
    """Generate Athena++ input file for a simulation."""
    lam = wavelength_for_beta(sim["beta"])
    nx = sim["nx"]

    content = f"""# TEST_M3_RESOLUTION: Resolution convergence test
# {sim['name']} — Resolution: {nx}^3, f={sim['f']}, beta={sim['beta']}, M={sim['mach']}, seed={sim['seed']}

<job>
problem_id = {sim['name']}

<time>
cfl_number  = {CFL}
tlim        = {TLIM}
nlim        = -1

<mesh>
nx1    = {nx}
x1min  = {-L1/2:.2f}
x1max  =  {L1/2:.2f}
ix1_bc = periodic
ox1_bc = periodic

nx2    = {nx}
x2min  = {-L2/2:.2f}
x2max  =  {L2/2:.2f}
ix2_bc = periodic
ox2_bc = periodic

nx3    = {nx}
x3min  = {-L3/2:.2f}
x3max  =  {L3/2:.2f}
ix3_bc = periodic
ox3_bc = periodic

<meshblock>
nx1 = {max(32, nx//4)}
nx2 = {max(32, nx//4)}
nx3 = {max(32, nx//4)}

<hydro>
iso_sound_speed = 1.0

<problem>
four_pi_G    = {FOUR_PI_G:.6f}
mach_number  = {sim['mach']:.4f}
plasma_beta  = {sim['beta']:.4f}
wavelength   = {lam:.6f}
perturb_ampl = 1.0e-4
random_seed  = {sim['seed']}

<output1>
file_type = hdf5
variable  = prim
id        = out1
dt        = {DT_OUTPUT}

<output2>
file_type = history
id        = myhst
dt        = 0.01
variable  = vol_avg_rho, vol_avg_p, vol_avg_v1, vol_avg_v2, vol_avg_v3
"""
    input_path = sim_dir / f"{sim['name']}.in"
    input_path.write_text(content)
    return input_path


# ── Ray remote task ───────────────────────────────────────────────────────────

try:
    import ray

    @ray.remote(num_cpus=N_PROCS_PER_SIM)
    def run_sim_ray(sim, work_dir_str, athena_bin):
        """Run one Athena++ simulation via mpirun."""
        import time
        import subprocess
        from pathlib import Path

        work_dir = Path(work_dir_str)
        sim_dir = work_dir / sim["name"]
        out_dir = sim_dir / "outputs"
        sim_dir.mkdir(parents=True, exist_ok=True)
        out_dir.mkdir(exist_ok=True)

        # Write input file
        input_path = make_input_file(sim, sim_dir)

        # MPI command
        cmd = [
            "mpirun",
            "--oversubscribe",
            "-np", str(N_PROCS_PER_SIM),
            "--bind-to", "none",
            athena_bin,
            "-i", str(input_path),
            "-d", str(out_dir),
        ]

        # Run simulation
        t0 = time.time()
        log_path = sim_dir / "athena.log"

        try:
            with open(log_path, "w") as f:
                proc = subprocess.run(
                    cmd,
                    stdout=f,
                    stderr=subprocess.STDOUT,
                    cwd=sim_dir,
                    check=False
                )

            elapsed = time.time() - t0

            # Check for successful completion
            hst_file = out_dir / f"{sim['name']}.myhst"
            success = hst_file.exists()

            return {
                "name": sim["name"],
                "success": success,
                "elapsed_time": elapsed,
                "resolution": sim["nx"],
            }

        except Exception as e:
            return {
                "name": sim["name"],
                "success": False,
                "error": str(e),
                "elapsed_time": time.time() - t0,
                "resolution": sim["nx"],
            }

    # ── Main execution ─────────────────────────────────────────────────────────

    def main():
        """Run all resolution test simulations using Ray."""

        # Initialize Ray
        ray.init(
            num_cpus=N_CPUS_AVAILABLE,
            ignore_reinit_error=True,
            _plasma_directory=LOG_DIR / "ray_plasma"
        )

        print(f"Ray initialized: {N_CPUS_AVAILABLE} CPUs available")
        print(f"Concurrent simulations: {N_CPUS_AVAILABLE // N_PROCS_PER_SIM}")

        # Generate all simulations
        simulations = []

        for res in RESOLUTIONS:
            nx = res["nx"]
            res_name = res["name"]

            for pt in TEST_POINTS:
                f = pt["f"]
                beta = pt["beta"]
                mach = pt["mach"]
                pt_id = pt["id"]

                for seed in SEEDS:
                    sim_name = f"RES_{res_name}_{pt_id}_f{f}_b{beta}_M{mach}_s{seed}"

                    sim = {
                        "name": sim_name,
                        "f": f,
                        "beta": beta,
                        "mach": mach,
                        "seed": seed,
                        "nx": nx,
                        "res_name": res_name,
                    }

                    simulations.append(sim)

        print(f"\nGenerated {len(simulations)} simulation configurations")
        print(f"Estimated runtime: {len(simulations) * 32 / (N_CPUS_AVAILABLE // N_PROCS_PER_SIM):.0f} hours")
        print(f"  (assuming 32 hours per 256^3 simulation on {N_CPUS_AVAILABLE // N_PROCS_PER_SIM} concurrent workers)\n")

        # Create work directory
        WORK_DIR.mkdir(parents=True, exist_ok=True)
        LOG_DIR.mkdir(parents=True, exist_ok=True)

        # Submit all simulations to Ray
        print("Submitting simulations to Ray...")
        t_start = time.time()

        futures = [
            run_sim_ray.remote(sim, str(WORK_DIR), ATHENA_BIN)
            for sim in simulations
        ]

        print(f"Submitted {len(futures)} tasks")
        print(f"Monitoring progress (this will take {len(simulations) * 32 / (N_CPUS_AVAILABLE // N_PROCS_PER_SIM):.0f} hours)...\n")

        # Wait for completion and collect results
        results = []
        completed = 0

        for i, future in enumerate(futures):
            result = ray.get(future)
            results.append(result)
            completed += 1

            progress = completed / len(futures) * 100
            print(f"[{progress:5.1f}%] {result['name']}: "
                  f"{'OK' if result['success'] else 'FAILED'} "
                  f"({result.get('elapsed_time', 0):.0f}s)")

        total_elapsed = time.time() - t_start

        # Save status
        status = {
            "campaign": "TEST_M3_RESOLUTION",
            "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
            "total_elapsed_hours": total_elapsed / 3600,
            "n_sims": len(simulations),
            "n_completed": sum(1 for r in results if r["success"]),
            "n_failed": sum(1 for r in results if not r["success"]),
            "results": results
        }

        with open(STATUS_FILE, "w") as f:
            json.dump(status, f, indent=2)

        # Summary
        print(f"\n{'='*70}")
        print(f"TEST_M3_RESOLUTION Complete")
        print(f"{'='*70}")
        print(f"Total time: {total_elapsed/3600:.1f} hours")
        print(f"Completed: {status['n_completed']}/{status['n_sims']}")
        print(f"Failed: {status['n_failed']}")
        print(f"\nStatus saved to: {STATUS_FILE}")
        print(f"\nNext step: Run analysis script")
        print(f"  cd ../../analysis/")
        print(f"  python3 analyze_resolution.py")
        print(f"{'='*70}\n")

        # Shutdown Ray
        ray.shutdown()

        return 0 if status["n_failed"] == 0 else 1

    if __name__ == "__main__":
        sys.exit(main())

except ImportError:
    print("ERROR: Ray not installed. Install with: pip install ray[default]")
    sys.exit(1)
