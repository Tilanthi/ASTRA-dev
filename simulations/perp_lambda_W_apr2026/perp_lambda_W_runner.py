#!/usr/bin/env python3
"""
Perpendicular B-field λ/W Campaign Runner
==========================================
Referee Concern #4: Direct λ/W measurements for perpendicular-field configurations.

24 Athena++ MHD simulations:
  f    ∈ {2.0, 2.5, 3.0}   (supercritical, robust fragmentation)
  β    ∈ {0.3, 1.0}         (magnetically sub/trans-critical)
  M    ∈ {1.0, 2.0}         (Mach number)
  seed ∈ {42, 43}           (two independent realisations)

Key difference from previous campaigns:
  - Full HDF5 snapshots every DT_HDF5 = 0.05 t_J (required for λ/W extraction)
  - tlim = 2.0 t_J (perp sims fragment by ~0.64 t_J max; gives 3× margin)
  - theta = 90° (B perpendicular to filament axis)
  - Domain 256×64×64 cells (8×2×2 λ_J), np=16 per sim

Usage (on astra-climate):
  cd /data/perp_lambda_W_runs
  python3 /home/fetch-agi/perp_lambda_W_runner.py

Requirements:
  - Ray cluster running: ray start --head --num-cpus=224
  - Athena++ binary: /home/fetch-agi/athena/bin/athena
  - Output dir: /data/perp_lambda_W_runs/  (SSD mount)
  - Python: ray, numpy, h5py, scipy
"""

import ray
import json
import subprocess
import os
import sys
import time
import re
import shutil
from pathlib import Path
from itertools import product

# ── Configuration ─────────────────────────────────────────────────────────────
ATHENA_BIN    = "/home/fetch-agi/athena/bin/athena"
SIMBASE       = "/data/perp_lambda_W_runs"
RUNNER_LOG    = f"{SIMBASE}/campaign.log"
RESULTS_JSON  = f"{SIMBASE}/results.json"

NP_PER_SIM    = 16       # MPI ranks per simulation (256×64×64 / 16 meshblocks)
MAX_CONCURRENT = 9       # 9 × 16 = 144 cores (leaves 80 for OS + analysis)
WALLCLOCK_LIM  = 21600   # 6 hours in seconds
TLIM           = 2.0     # physical time limit in t_J
DT_HDF5        = 0.05    # HDF5 snapshot interval in t_J  ← CRITICAL for λ/W
DT_HST         = 0.005   # history file interval (for dt watchdog)
DT_KILL        = 1e-8    # dt threshold for fragmentation detection

# Campaign parameter grid
F_VALUES    = [2.0, 2.5, 3.0]
BETA_VALUES = [0.3, 1.0]
MACH_VALUES = [1.0, 2.0]
SEEDS       = [42, 43]
THETA       = 90.0       # perpendicular B-field

# Athena++ physics parameters
FOUR_PI_G   = 39.478418  # 4π² (G=1 code units)
ISO_CS      = 1.0        # isothermal sound speed
TURB_AMPL   = 1.0e-4    # turbulence amplitude (synthetic, Kolmogorov)
TURB_MODES  = 8

# ── Generate simulation grid ──────────────────────────────────────────────────
def build_sim_list():
    sims = []
    idx = 0
    for f, beta, mach, seed in product(F_VALUES, BETA_VALUES, MACH_VALUES, SEEDS):
        sim_id = f"PLW_f{f:.1f}_b{beta:.1f}_M{mach:.1f}_s{seed}"
        sims.append({
            "idx":    idx,
            "sim_id": sim_id,
            "f":      f,
            "beta":   beta,
            "mach":   mach,
            "seed":   seed,
            "theta":  THETA,
        })
        idx += 1
    return sims

# ── Athena++ input file ───────────────────────────────────────────────────────
def make_input_file(sim, sim_dir):
    """Generate Athena++ input file for one simulation."""
    # Magnetic field strength: B = sqrt(2/beta) * c_s
    # In code units with rho_0=1, cs=1: B0 = sqrt(2/beta)
    # For perpendicular B (theta=90°): field in x2 direction
    import math
    B0 = math.sqrt(2.0 / sim["beta"]) if sim["beta"] > 0 else 0.0

    # B perpendicular: bx2 carries the field (x2 = transverse)
    inp = f"""
<comment>
problem  = Perpendicular B-field lambda/W campaign (Referee Concern 4)
sim_id   = {sim["sim_id"]}
f        = {sim["f"]}
beta     = {sim["beta"]}
mach     = {sim["mach"]}
seed     = {sim["seed"]}
theta    = {sim["theta"]}

<job>
problem_id = {sim["sim_id"]}

<time>
integrator  = vl2
cfl_number  = 0.3
tlim        = {TLIM}
nlim        = -1

<mesh>
nx1         = 256
nx2         = 64
nx3         = 64
x1min       = -4.0
x1max       = 4.0
x2min       = -1.0
x2max       = 1.0
x3min       = -1.0
x3max       = 1.0
ix1_bc      = periodic
ox1_bc      = periodic
ix2_bc      = periodic
ox2_bc      = periodic
ix3_bc      = periodic
ox3_bc      = periodic

<meshblock>
nx1         = 64
nx2         = 32
nx3         = 32

<hydro>
iso_sound_speed = {ISO_CS}

<field>
b0          = {B0:.6f}

<gravity>
grav_style  = fft
four_pi_G   = {FOUR_PI_G}

<problem>
f           = {sim["f"]}
beta        = {sim["beta"]}
mach        = {sim["mach"]}
seed        = {sim["seed"]}
theta       = {sim["theta"]}
four_pi_G   = {FOUR_PI_G}
turb_ampl   = {TURB_AMPL}
turb_modes  = {TURB_MODES}

<output1>
file_type   = hst
variable    = dt
dt          = {DT_HST}
id          = hst

<output2>
file_type   = hdf5
variable    = prim
dt          = {DT_HDF5}
id          = out
""".strip()

    fpath = Path(sim_dir) / f"athinput.{sim['sim_id']}"
    fpath.write_text(inp)
    return str(fpath)

# ── Single simulation runner (Ray remote task) ─────────────────────────────────
@ray.remote(num_cpus=NP_PER_SIM)
def run_sim(sim, simbase, athena_bin, wallclock_lim, dt_kill):
    """Execute one Athena++ MHD simulation and return result dict."""
    import subprocess, time, os, re
    from pathlib import Path

    sim_id  = sim["sim_id"]
    sim_dir = Path(simbase) / sim_id
    sim_dir.mkdir(parents=True, exist_ok=True)

    input_file = make_input_file(sim, sim_dir)
    log_file   = sim_dir / "stdout.txt"
    hst_file   = sim_dir / f"{sim_id}.hst"

    cmd = ["mpirun", "-np", str(NP_PER_SIM), athena_bin,
           "-i", input_file, "-d", str(sim_dir)]

    t_start = time.time()
    outcome = "RUNNING"
    t_frag  = None
    dt_min  = float("inf")

    try:
        proc = subprocess.Popen(
            cmd,
            stdout=open(log_file, "w"),
            stderr=subprocess.STDOUT,
            cwd=str(sim_dir),
        )

        # Poll stdout log for dt collapse
        deadline = t_start + wallclock_lim
        while proc.poll() is None and time.time() < deadline:
            time.sleep(10)
            # Scan stdout for dt
            try:
                txt = log_file.read_text()
                dt_vals = re.findall(r"dt=\s*([0-9Ee+\-\.]+)", txt)
                if dt_vals:
                    dt_cur = float(dt_vals[-1])
                    dt_min = min(dt_min, dt_cur)
                    if dt_cur < dt_kill:
                        # Extract simulation time from last cycle line
                        t_vals = re.findall(r"time=\s*([0-9Ee+\-\.]+)", txt)
                        if t_vals:
                            t_frag = float(t_vals[-1])
                        proc.terminate()
                        try: proc.wait(timeout=30)
                        except: proc.kill()
                        outcome = "FRAG"
                        break
            except Exception:
                pass

        if proc.poll() is None:
            proc.terminate()
            try: proc.wait(timeout=60)
            except: proc.kill()
            if outcome == "RUNNING":
                outcome = "TIMEOUT"

        elif proc.returncode == 0 and outcome == "RUNNING":
            outcome = "COMPLETE"   # ran to tlim without dt collapse

    except Exception as e:
        outcome = "FAILED"

    wall_s = int(time.time() - t_start)

    # Count HDF5 snapshots produced
    n_hdf5 = len(list(sim_dir.glob("*.athdf")))

    result = {
        "sim_id":  sim_id,
        "f":       sim["f"],
        "beta":    sim["beta"],
        "mach":    sim["mach"],
        "seed":    sim["seed"],
        "theta":   sim["theta"],
        "outcome": outcome,
        "t_frag":  t_frag,
        "dt_min":  dt_min if dt_min < float("inf") else None,
        "wall_s":  wall_s,
        "n_hdf5":  n_hdf5,
        "sim_dir": str(sim_dir),
    }
    return result

# ── Campaign orchestrator ──────────────────────────────────────────────────────
def log(msg, logpath=RUNNER_LOG):
    ts = time.strftime("%Y-%m-%d %H:%M:%S UTC", time.gmtime())
    line = f"[{ts}] {msg}"
    print(line, flush=True)
    with open(logpath, "a") as fh:
        fh.write(line + "\n")

def run_campaign():
    os.makedirs(SIMBASE, exist_ok=True)

    # Sanity checks
    if not os.path.isfile(ATHENA_BIN):
        print(f"ERROR: Athena binary not found: {ATHENA_BIN}")
        sys.exit(1)

    sims = build_sim_list()
    log(f"Perpendicular λ/W campaign: {len(sims)} simulations")
    log(f"f={F_VALUES}  β={BETA_VALUES}  M={MACH_VALUES}  seeds={SEEDS}  θ={THETA}°")
    log(f"np={NP_PER_SIM}/sim  max_concurrent={MAX_CONCURRENT}  tlim={TLIM} t_J")
    log(f"HDF5 snapshots every {DT_HDF5} t_J — CRITICAL for λ/W extraction")
    log(f"Output: {SIMBASE}")

    # Connect to existing Ray cluster
    ray.init(address="auto", ignore_reinit_error=True)
    log(f"Ray cluster: {ray.cluster_resources()}")

    all_results = []
    pending     = []
    sim_queue   = list(sims)

    def flush_completed():
        still_pending = []
        for ref, meta in pending:
            if ray.wait([ref], timeout=0)[0]:
                try:
                    r = ray.get(ref)
                    all_results.append(r)
                    outcome_str = r["outcome"]
                    tfrag_str   = f"t_frag={r['t_frag']:.4f}" if r["t_frag"] else "t_frag=N/A"
                    log(f"  DONE [{len(all_results)}/{len(sims)}] {r['sim_id']} "
                        f"→ {outcome_str}  {tfrag_str}  wall={r['wall_s']}s  n_hdf5={r['n_hdf5']}")
                    # Save intermediate results
                    with open(RESULTS_JSON, "w") as fh:
                        json.dump(all_results, fh, indent=2, default=str)
                except Exception as e:
                    log(f"  ERROR retrieving result for {meta['sim_id']}: {e}")
            else:
                still_pending.append((ref, meta))
        pending[:] = still_pending

    t_campaign_start = time.time()
    while sim_queue or pending:
        flush_completed()
        # Launch new sims up to MAX_CONCURRENT
        while sim_queue and len(pending) < MAX_CONCURRENT:
            sim = sim_queue.pop(0)
            log(f"  LAUNCH {sim['sim_id']}  (queue remaining: {len(sim_queue)})")
            ref = run_sim.remote(sim, SIMBASE, ATHENA_BIN, WALLCLOCK_LIM, DT_KILL)
            pending.append((ref, sim))
        time.sleep(15)

    flush_completed()
    wall_total = int(time.time() - t_campaign_start)

    n_frag    = sum(1 for r in all_results if r["outcome"] == "FRAG")
    n_timeout = sum(1 for r in all_results if r["outcome"] == "TIMEOUT")
    n_failed  = sum(1 for r in all_results if r["outcome"] == "FAILED")
    n_complete= sum(1 for r in all_results if r["outcome"] == "COMPLETE")

    log("=" * 60)
    log(f"CAMPAIGN COMPLETE — {wall_total}s wall time")
    log(f"  FRAG={n_frag}  TIMEOUT={n_timeout}  FAILED={n_failed}  COMPLETE={n_complete}")
    log(f"  Results: {RESULTS_JSON}")
    log("=" * 60)
    log("NEXT STEP: python3 /home/fetch-agi/analyse_perp_lambda_W.py")

    with open(RESULTS_JSON, "w") as fh:
        json.dump(all_results, fh, indent=2, default=str)

if __name__ == "__main__":
    run_campaign()
