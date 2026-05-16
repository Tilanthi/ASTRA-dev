#!/usr/bin/env python3
"""
TEST_M5_NONISOTHERMAL: Non-Isothermal Equation of State Effects Test
Ray-based parallel execution of Athena++ filament fragmentation simulations

Purpose: Address theoretical reviewer concern T-M5 — test whether paper's central
negative conclusion holds under more realistic thermodynamics (polytropic EOS)

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

# ── Configuration ────────────────────────────────────────────────────────────

ATHENA_BIN = os.path.expanduser("~/athena/bin/athena")
WORK_DIR = Path.cwd() / "results"
STATUS_FILE = Path.cwd() / "status_nonisothermal.json"
LOG_DIR = Path.cwd() / "logs"

N_PROCS_PER_SIM = 16
N_CPUS_AVAILABLE = 220

FOUR_PI_G = 4.0 * np.pi**2
L1, L2, L3 = 8.0, 2.0, 2.0
TLIM = 4.0
CFL = 0.3
DT_OUTPUT = 0.5

with open(Path.cwd() / "config" / "test_points.json", "r") as f:
    CONFIG = json.load(f)

TEST_POINTS = CONFIG["test_points"]
EOS_TYPES = CONFIG["eos_types"]

print(f"TEST_M5_NONISOTHERMAL: Non-isothermal EOS effects test")
print(f"  Test points: {len(TEST_POINTS)}")
print(f"  EOS types: {len(EOS_TYPES)} ({[eos['name'] for eos in EOS_TYPES]})")
print(f"  Total simulations: {len(TEST_POINTS) * len(EOS_TYPES)}")

def wavelength_for_beta(beta):
    return np.sqrt(1.0 + 2.0 / beta)

def make_input_file(sim, sim_dir):
    """Generate Athena++ input file with polytropic EOS."""
    lam = wavelength_for_beta(sim["beta"])
    gamma = sim["gamma"]
    eos_name = sim["eos_name"]

    # Note: Athena++ supports polytropic EOS via gamma parameter
    # gamma = 1.0: isothermal
    # gamma < 1.0: cooling (effective equation of state)
    # gamma > 1.0: heating

    content = f"""# TEST_M5_NONISOTHERMAL: EOS effects test
# {sim['name']} — EOS={eos_name} (gamma={gamma}), f={sim['f']}, beta={sim['beta']}, M={sim['mach']}

<job>
problem_id = {sim['name']}

<time>
cfl_number  = {CFL}
tlim        = {TLIM}
nlim        = -1

<mesh>
nx1    = 256
x1min  = {-L1/2:.2f}
x1max  =  {L1/2:.2f}
ix1_bc = periodic
ox1_bc = periodic

nx2    = 256
x2min  = {-L2/2:.2f}
x2max  =  {L2/2:.2f}
ix2_bc = periodic
ox2_bc = periodic

nx3    = 256
x3min  = {-L3/2:.2f}
x3max  =  {L3/2:.2f}
ix3_bc = periodic
ox3_bc = periodic

<meshblock>
nx1 = 64
nx2 = 64
nx3 = 64

<hydro>
iso_sound_speed = 1.0
gamma           = {gamma:.3f}

<problem>
four_pi_G    = {FOUR_PI_G:.6f}
mach_number  = {sim['mach']:.4f}
plasma_beta  = {sim['beta']:.4f}
wavelength   = {lam:.6f}
perturb_ampl = 1.0e-4
random_seed  = 42

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

try:
    import ray

    @ray.remote(num_cpus=N_PROCS_PER_SIM)
    def run_sim_ray(sim, work_dir_str, athena_bin):
        import time, subprocess
        from pathlib import Path

        work_dir = Path(work_dir_str)
        sim_dir = work_dir / sim["name"]
        out_dir = sim_dir / "outputs"
        sim_dir.mkdir(parents=True, exist_ok=True)
        out_dir.mkdir(exist_ok=True)

        input_path = make_input_file(sim, sim_dir)

        cmd = [
            "mpirun", "--oversubscribe", "-np", str(N_PROCS_PER_SIM),
            "--bind-to", "none", athena_bin, "-i", str(input_path), "-d", str(out_dir),
        ]

        t0 = time.time()
        log_path = sim_dir / "athena.log"

        try:
            with open(log_path, "w") as f:
                subprocess.run(cmd, stdout=f, stderr=subprocess.STDOUT, cwd=sim_dir, check=False)

            hst_file = out_dir / f"{sim['name']}.myhst"
            success = hst_file.exists()

            return {
                "name": sim["name"],
                "success": success,
                "elapsed_time": time.time() - t0,
                "eos_name": sim["eos_name"],
                "gamma": sim["gamma"],
            }
        except Exception as e:
            return {
                "name": sim["name"], "success": False, "error": str(e),
                "elapsed_time": time.time() - t0, "eos_name": sim["eos_name"],
                "gamma": sim["gamma"],
            }

    def main():
        ray.init(num_cpus=N_CPUS_AVAILABLE, ignore_reinit_error=True,
                 _plasma_directory=LOG_DIR / "ray_plasma")

        print(f"Ray initialized: {N_CPUS_AVAILABLE} CPUs")
        print(f"Concurrent simulations: {N_CPUS_AVAILABLE // N_PROCS_PER_SIM}\n")

        simulations = []

        for eos in EOS_TYPES:
            eos_name = eos["name"]
            gamma = eos["gamma"]

            for pt in TEST_POINTS:
                f, beta, mach, pt_id = pt["f"], pt["beta"], pt["mach"], pt["id"]
                sim_name = f"EOS_{eos_name}_{pt_id}_f{f}_b{beta}_M{mach}"

                simulations.append({
                    "name": sim_name, "f": f, "beta": beta, "mach": mach,
                    "seed": 42, "eos_name": eos_name, "gamma": gamma,
                })

        print(f"Generated {len(simulations)} simulation configurations")
        print(f"Estimated runtime: ~{len(simulations) * 32 / (N_CPUS_AVAILABLE // N_PROCS_PER_SIM):.0f} hours\n")

        WORK_DIR.mkdir(parents=True, exist_ok=True)
        LOG_DIR.mkdir(parents=True, exist_ok=True)

        t_start = time.time()
        futures = [run_sim_ray.remote(s, str(WORK_DIR), ATHENA_BIN) for s in simulations]

        print(f"Submitted {len(futures)} tasks\n")

        results, completed = [], 0
        for future in futures:
            result = ray.get(future)
            results.append(result)
            completed += 1
            print(f"[{completed/len(futures)*100:5.1f}%] {result['name']}: "
                  f"{'OK' if result['success'] else 'FAILED'} ({result.get('elapsed_time',0):.0f}s)")

        total_elapsed = time.time() - t_start

        status = {
            "campaign": "TEST_M5_NONISOTHERMAL",
            "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
            "total_elapsed_hours": total_elapsed / 3600,
            "n_sims": len(simulations),
            "n_completed": sum(1 for r in results if r["success"]),
            "n_failed": sum(1 for r in results if not r["success"]),
            "results": results
        }

        with open(STATUS_FILE, "w") as f:
            json.dump(status, f, indent=2)

        print(f"\n{'='*70}\nTEST_M5_NONISOTHERMAL Complete")
        print(f"Total time: {total_elapsed/3600:.1f}h")
        print(f"Completed: {status['n_completed']}/{status['n_sims']}\n")
        print(f"Status: {STATUS_FILE}\nNext: cd ../../analysis/ && python3 analyze_nonisothermal.py\n{'='*70}\n")

        ray.shutdown()
        return 0 if status["n_failed"] == 0 else 1

    if __name__ == "__main__":
        sys.exit(main())

except ImportError:
    print("ERROR: Ray not installed")
    sys.exit(1)
