#!/usr/bin/env python3
"""
EXPANDED REFEREE RESPONSE CAMPAIGN — Ray Cluster Runner
========================================================

Designed for Ray clusters (not SLURM). Uses Ray's distributed computing
to run 204 simulations across 3 sub-campaigns addressing referee concerns.

Campaigns:
1. CTZM_PERP (96 sims): Perpendicular-field transition zone mapping
2. EOS_SENSITIVITY (48 sims): Non-isothermal EOS effects on λ/W
3. TURB_AMPLITUDE (60 sims): Turbulence amplitude from linear to supersonic

Author: Claude (ASTRA System)
Date: 2026-05-13
"""

import os
import json
import signal
import subprocess
import time
from pathlib import Path
from typing import Dict, List, Any
import numpy as np
import ray

# ── Configuration ────────────────────────────────────────────────────────────
ATHENA_BIN = "/path/to/athena/bin/athena"  # UPDATE THIS PATH
BASE_DIR = Path("/data/referee_response_may2026")
FOUR_PI_G = 39.4784176044
CS = 1.0
W_CORE = 0.3
DX1 = 8.0 / 256
DT_KILL = 1.0e-6
WALL_TIME = 14400  # 4 hours per sim
TLIM = 4.0
HDF5_DT = 0.02
MAX_HDF5_GB = 8.0
NP = 32  # MPI ranks per simulation

# Ray configuration
RAY_NUM_CPUS = 220  # Adjust to your cluster
RAY_NUM_WORKERS = 6  # Concurrent simulations

# ── Campaign Definitions ─────────────────────────────────────────────────────
CAMPAIGNS = {
    "CTZM_PERP": {
        "description": "Perpendicular-field transition zone (Referee B2)",
        "n_sims": 96,
        "output_dir": "ctzm_perp",
        "theta_deg": 90.0,
        "gamma": 1.0,
        "perturb_ampl": 1.0e-4,
        "params": {
            "f": [1.2, 1.3, 1.4, 1.5],
            "beta": [0.3, 0.5, 1.0, 2.0],
            "mach": [1.0, 2.0],
            "seed": [0, 1, 2],
        }
    },
    "EOS_SENSITIVITY": {
        "description": "Non-isothermal EOS effects (Referee B3)",
        "n_sims": 48,
        "output_dir": "eos_sensitivity",
        "theta_deg": 0.0,
        "gamma": None,  # Varied per sim
        "perturb_ampl": 1.0e-4,
        "params": {
            "f": [1.0, 1.1, 1.2],
            "gamma": [0.7, 0.8, 0.9, 1.0],
            "beta": [1.0],
            "mach": [1.0],
            "seed": [0, 1, 2, 3],
        }
    },
    "TURB_AMPLITUDE": {
        "description": "Turbulence amplitude scaling (Referee B5)",
        "n_sims": 60,
        "output_dir": "turb_amplitude",
        "theta_deg": 0.0,
        "gamma": 1.0,
        "perturb_ampl": None,  # Varied per sim
        "params": {
            "f": [1.0, 1.2],
            "ampl": [1e-4, 1e-3, 1e-2, 1e-1, 1.0],
            "beta": [1.0],
            "mach": [1.0],
            "seed": [0, 1, 2],
        }
    },
}

def build_sim_list() -> List[Dict[str, Any]]:
    """Build complete simulation list for all campaigns."""
    sims = []

    for campaign_name, config in CAMPAIGNS.items():
        if campaign_name == "EOS_SENSITIVITY":
            for f in config["params"]["f"]:
                for gamma in config["params"]["gamma"]:
                    for seed in config["params"]["seed"]:
                        sims.append({
                            "campaign": campaign_name,
                            "f": f,
                            "gamma": gamma,
                            "beta": 1.0,
                            "mach": 1.0,
                            "seed": seed,
                            "theta_deg": config["theta_deg"],
                            "perturb_ampl": config["perturb_ampl"],
                        })

        elif campaign_name == "TURB_AMPLITUDE":
            for f in config["params"]["f"]:
                for ampl in config["params"]["ampl"]:
                    for seed in config["params"]["seed"]:
                        sims.append({
                            "campaign": campaign_name,
                            "f": f,
                            "ampl": ampl,
                            "beta": 1.0,
                            "mach": 1.0,
                            "seed": seed,
                            "theta_deg": config["theta_deg"],
                            "gamma": 1.0,
                        })

        else:  # CTZM_PERP
            for f in config["params"]["f"]:
                for beta in config["params"]["beta"]:
                    for mach in config["params"]["mach"]:
                        for seed in config["params"]["seed"]:
                            sims.append({
                                "campaign": campaign_name,
                                "f": f,
                                "beta": beta,
                                "mach": mach,
                                "seed": seed,
                                "theta_deg": config["theta_deg"],
                                "gamma": config["gamma"],
                                "perturb_ampl": config["perturb_ampl"],
                            })

    return sims

def make_athinput(run_dir: Path, p: Dict[str, Any]) -> Path:
    """Generate Athena++ input file."""
    theta = p.get("theta_deg", 0.0)
    gamma = p.get("gamma", 1.0)
    ampl = p.get("perturb_ampl", 1.0e-4)
    beta = p.get("beta", 1.0)
    mach = p.get("mach", 1.0)
    f = p["f"]
    seed = p["seed"]

    # Determine gamma_adi for EOS
    if gamma < 1.0:
        gamma_adi = gamma
    else:
        gamma_adi = 1.0 + (1.0 - gamma) * 0.1

    # Generate run_id
    campaign = p["campaign"]
    if campaign == "EOS_SENSITIVITY":
        f_str = f"{f:.1f}".replace('.', 'p')
        g_str = f"{gamma:.1f}".replace('.', 'p')
        run_id = f"EOS_f{f_str}_g{g_str}_s{seed}"
    elif campaign == "TURB_AMPLITUDE":
        f_str = f"{f:.1f}".replace('.', 'p')
        a_str = f"{ampl:.0e}".replace('+', '').replace('.', 'p')
        run_id = f"TURB_f{f_str}_a{a_str}_s{seed}"
    else:  # CTZM_PERP
        f_str = f"{f:.1f}".replace('.', 'p')
        b_str = f"{beta:.1f}".replace('.', 'p')
        m_str = f"{mach:.1f}".replace('.', 'p')
        run_id = f"CTZMP_f{f_str}_b{b_str}_m{m_str}_s{seed}"

    athinput = f"""<comment>
problem   = {campaign} study
run_id    = {run_id}

<job>
problem_id = filament_spacing_pr

<time>
cfl_number = 0.3
nlim       = -1
tlim       = {TLIM}

<mesh>
nx1        = 256
x1min      = -4.0
x1max      = 4.0
ix1_bc     = periodic
ox1_bc     = periodic

nx2        = 64
x2min      = -1.0
x2max      = 1.0
ix2_bc     = periodic
ox2_bc     = periodic

nx3        = 64
x3min      = -1.0
x3max      = 1.0
ix3_bc     = periodic
ox3_bc     = periodic

<meshblock>
nx1        = 32
nx2        = 32
nx3        = 32

<hydro>
iso_sound_speed = {CS}
gamma_adi        = {gamma_adi}

<gravity>
grav_mean_rho = 1.0

<output1>
file_type  = hst
dt         = 0.01

<output2>
file_type  = hdf5
variable   = prim
dt         = {HDF5_DT}

<problem>
four_pi_G       = {FOUR_PI_G}
f_line_mass     = {f}
plasma_beta     = {beta}
mach_number     = {mach}
W_core          = {W_CORE}
perturb_ampl    = {ampl}
random_seed     = {seed}
bfield_geometry = {"longitudinal" if theta == 0.0 else "perpendicular"}
theta_deg       = {theta}
"""

    inp = run_dir / "athinput.athena"
    inp.write_text(athinput)
    return inp

@ray.remote
def run_single_simulation(p: Dict[str, Any], campaign: str) -> Dict[str, Any]:
    """Run a single simulation (Ray remote task)."""
    config = CAMPAIGNS[campaign]
    output_base = BASE_DIR / config["output_dir"]

    # Generate run_id
    if campaign == "EOS_SENSITIVITY":
        f_str = f"{p['f']:.1f}".replace('.', 'p')
        g_str = f"{p['gamma']:.1f}".replace('.', 'p')
        run_id = f"EOS_f{f_str}_g{g_str}_s{p['seed']}"
    elif campaign == "TURB_AMPLITUDE":
        f_str = f"{p['f']:.1f}".replace('.', 'p')
        a_str = f"{p['ampl']:.0e}".replace('+', '').replace('.', 'p')
        run_id = f"TURB_f{f_str}_a{a_str}_s{p['seed']}"
    else:
        f_str = f"{p['f']:.1f}".replace('.', 'p')
        b_str = f"{p['beta']:.1f}".replace('.', 'p')
        m_str = f"{p['mach']:.1f}".replace('.', 'p')
        run_id = f"CTZMP_f{f_str}_b{b_str}_m{m_str}_s{p['seed']}"

    run_dir = output_base / run_id
    run_dir.mkdir(parents=True, exist_ok=True)

    inp_file = make_athinput(run_dir, p)
    log_file = run_dir / "stdout.txt"

    cmd = [
        "mpirun", "--oversubscribe", "-np", str(NP),
        ATHENA_BIN, "-i", str(inp_file),
        "-d", str(run_dir),
    ]

    t_start = time.time()
    t_frag = None
    outcome = "TIMEOUT"
    dt_min = 999.0

    try:
        proc = subprocess.Popen(
            cmd,
            stdout=open(log_file, "w"),
            stderr=subprocess.STDOUT,
            preexec_fn=os.setsid
        )

        poll_interval = 8.0
        while True:
            elapsed = time.time() - t_start

            if elapsed > WALL_TIME:
                os.killpg(os.getpgid(proc.pid), signal.SIGKILL)
                outcome = "TIMEOUT"
                break

            rc = proc.poll()
            if rc is not None:
                outcome = "COMPLETE" if rc == 0 else "FAILED"
                break

            # HDF5 pruning
            hdf5_list = sorted((run_dir / "*.athdf").parent.glob("*.athdf")) if (run_dir / "*.athdf").parent.exists() else []
            total_gb = sum(h.stat().st_size for h in hdf5_list) / 1e9 if hdf5_list else 0
            if total_gb > MAX_HDF5_GB and len(hdf5_list) > 30:
                for h in hdf5_list[:-30]:
                    h.unlink(missing_ok=True)

            # HST scanning
            hst_files = list(run_dir.glob("*.hst"))
            if hst_files:
                try:
                    lines = hst_files[0].read_text().split('\n')
                    for line in reversed(lines):
                        if line.strip() and not line.startswith('#'):
                            cols = line.split()
                            if len(cols) >= 2:
                                t_now = float(cols[0])
                                dt_val = float(cols[1])
                                if dt_val < dt_min:
                                    dt_min = dt_val
                                if dt_val < DT_KILL:
                                    t_frag = t_now
                                    outcome = "FRAG"
                                    os.killpg(os.getpgid(proc.pid), signal.SIGKILL)
                                    proc.wait(timeout=5)
                            break
                except Exception:
                    pass
                if outcome == "FRAG":
                    break

            time.sleep(poll_interval)

    except Exception as e:
        outcome = f"ERROR: {str(e)}"

    wall = time.time() - t_start

    # Store basic outcome (λ/W analysis done separately)
    result = {
        "campaign": campaign,
        "run_id": run_id,
        **p,
        "outcome": outcome,
        "t_frag": t_frag,
        "dt_min": dt_min,
        "wall_s": round(wall, 1),
        "output_dir": str(run_dir),
    }

    print(f"[{campaign[:8]}] {run_id} {outcome:8s} t={t_frag:.4f} t_J wall={wall:.0f}s")

    return result

def run_campaign(campaign_name: str, sims: List[Dict[str, Any]]):
    """Run all simulations for a single campaign using Ray."""
    print(f"\n{'='*70}")
    print(f"Starting {campaign_name} campaign ({len(sims)} simulations)")
    print(f"{'='*70}\n")

    campaign_sims = [s for s in sims if s["campaign"] == campaign_name]
    config = CAMPAIGNS[campaign_name]

    # Create output directory
    output_dir = BASE_DIR / config["output_dir"]
    output_dir.mkdir(parents=True, exist_ok=True)

    # Submit all sims to Ray
    futures = []
    for sim in campaign_sims:
        future = run_single_simulation.remote(sim, campaign_name)
        futures.append(future)

    # Collect results as they complete
    results = []
    while futures:
        # Wait for at least one future to complete
        ready_futures, futures = ray.wait(futures, num_returns=1, timeout=10.0)

        for future in ready_futures:
            try:
                result = ray.get(future)
                results.append(result)
            except Exception as e:
                print(f"Error retrieving result: {e}")

        # Periodic save
        if len(results) % 10 == 0:
            output_file = output_dir / f"{campaign_name.lower()}_partial.json"
            output_file.write_text(json.dumps(results, indent=2))
            print(f"Saved partial results: {len(results)}/{len(campaign_sims)} complete")

    # Final save
    output_file = output_dir / f"{campaign_name.lower()}_results.json"
    output_file.write_text(json.dumps(results, indent=2))

    # Summary
    n_frag = sum(1 for r in results if r["outcome"] == "FRAG")
    n_timeout = sum(1 for r in results if r["outcome"] == "TIMEOUT")
    n_fail = sum(1 for r in results if r["FAILED"] in r.get("outcome", ""))

    print(f"\n{campaign_name} COMPLETE:")
    print(f"  Total: {len(results)} sims")
    print(f"  FRAG: {n_frag} | TIMEOUT: {n_timeout} | FAIL: {n_fail}")
    print(f"  Results: {output_file}")

    return results

def main():
    """Main entry point."""
    print("="*70)
    print("EXPANDED REFEREE RESPONSE CAMPAIGN — Ray Cluster")
    print("="*70)
    print(f"\nTotal simulations: 204")
    print(f"  CTZM_PERP: 96 sims")
    print(f"  EOS_SENSITIVITY: 48 sims")
    print(f"  TURB_AMPLITUDE: 60 sims")
    print(f"\nOutput directory: {BASE_DIR}")
    print(f"Athena++ binary: {ATHENA_BIN}")
    print(f"\nRay configuration:")
    print(f"  CPUs: {RAY_NUM_CPUS}")
    print(f"  Concurrent workers: {RAY_NUM_WORKERS}")
    print("\n" + "="*70)

    # Initialize Ray
    ray.init(num_cpus=RAY_NUM_CPUS)

    try:
        # Build simulation list
        sims = build_sim_list()
        print(f"\nBuilt simulation list: {len(sims)} total simulations")

        # Run campaigns sequentially
        all_results = []
        for campaign in ["CTZM_PERP", "EOS_SENSITIVITY", "TURB_AMPLITUDE"]:
            results = run_campaign(campaign, sims)
            all_results.extend(results)

        # Save combined results
        combined_file = BASE_DIR / "all_campaigns_results.json"
        combined_file.write_text(json.dumps(all_results, indent=2))

        print(f"\n{'='*70}")
        print(f"ALL CAMPAIGNS COMPLETE")
        print(f"{'='*70}")
        print(f"Total simulations: {len(all_results)}")
        print(f"Combined results: {combined_file}")
        print(f"\nNext step: Run analysis script on each campaign directory")
        print(f"  python analyse_campaign.py <campaign_dir>")

    finally:
        ray.shutdown()

if __name__ == "__main__":
    main()
