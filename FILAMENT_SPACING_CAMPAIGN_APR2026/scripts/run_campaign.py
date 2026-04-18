#!/usr/bin/env python3
"""
1-Day Filament Spacing Campaign — Ray Parallel Edition
Glenn J. White (Open University) / ASTRA System

Resolution: 128×128×32 (8× validation cell count)
  - 201 cells per Jeans length — scientifically excellent
  - Batch 1 (100 sims): ~21 hours on 224 cores
  - Batch 2 (120 sims): follow-on ~25 hours

Physics:
  - Isothermal MHD + FFT self-gravity (Athena++)
  - 4πG = 4π² ≈ 39.48  →  λ_J = 1.0 code unit
  - Perturbation at magneto-Jeans wavelength: λ_MJ = √(1 + 2/β)
  - tlim = 2.0 code units ≈ 4 free-fall times

Parallelism: Ray with 16 CPUs per task → 14 simultaneous sims on 224 cores
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

ATHENA_BIN  = "/home/fetch-agi/athena/bin/athena"
WORK_DIR    = Path("/home/fetch-agi/campaign_1day_v2")
STATUS_FILE = Path("/home/fetch-agi/campaign_status_v2.json")
LOG_DIR     = WORK_DIR / "logs"

N_PROCS_PER_SIM = 16   # MPI processes per Athena++ run
                        # → 224/16 = 14 simultaneous sims
NX1, NX2, NX3  = 128, 128, 32
L1, L2, L3     = 4.0, 4.0, 1.0   # Domain full widths

FOUR_PI_G  = 4.0 * np.pi**2      # 39.478 — sets λ_J = 1.0 code unit
TLIM       = 2.0                  # Code time units ≈ 4 free-fall times
CFL        = 0.3
DT_OUTPUT  = 0.2                  # HDF5 snapshot interval → 10 outputs per sim

CAMPAIGN_START = time.time()


# ── Helper functions (used in Ray remote context) ─────────────────────────────

def wavelength_for_beta(beta):
    """Magneto-Jeans wavelength (code units) with 4πG = 4π²."""
    lam = np.sqrt(1.0 + 2.0 / beta)
    return min(lam, 0.92 * L1 / 2)   # cap at 92% of half-domain = 1.84


def make_input_file(sim, sim_dir):
    """Generate standard Athena++ input file for a simulation."""
    lam = wavelength_for_beta(sim["beta"])

    content = f"""# Filament Spacing Campaign — {sim['name']}
# M={sim['mach']:.2f}  β={sim['beta']:.3f}  ε={sim['epsilon']:.2e}  batch={sim['batch']}

<job>
problem_id = {sim['name']}

<time>
cfl_number  = {CFL}
tlim        = {TLIM}
nlim        = -1

<mesh>
nx1    = {NX1}
x1min  = {-L1/2:.2f}
x1max  =  {L1/2:.2f}
ix1_bc = periodic
ox1_bc = periodic

nx2    = {NX2}
x2min  = {-L2/2:.2f}
x2max  =  {L2/2:.2f}
ix2_bc = periodic
ox2_bc = periodic

nx3    = {NX3}
x3min  = {-L3/2:.2f}
x3max  =  {L3/2:.2f}
ix3_bc = periodic
ox3_bc = periodic

<meshblock>
nx1 = 32
nx2 = 32
nx3 = 32

<hydro>
iso_sound_speed = 1.0

<problem>
four_pi_G    = {FOUR_PI_G:.6f}
mach_number  = {sim['mach']:.4f}
plasma_beta  = {sim['beta']:.4f}
wavelength   = {lam:.6f}
perturb_ampl = {sim['epsilon']:.6e}

<output1>
file_type = hdf5
variable  = prim
id        = out1
dt        = {DT_OUTPUT}
"""
    path = sim_dir / f"{sim['name']}.in"
    path.write_text(content)
    return path


# ── Ray remote task ───────────────────────────────────────────────────────────

try:
    import ray

    @ray.remote(num_cpus=N_PROCS_PER_SIM)
    def run_sim_ray(sim, work_dir_str, athena_bin):
        """Run one Athena++ simulation via mpirun."""
        import time, subprocess
        from pathlib import Path

        work_dir = Path(work_dir_str)
        sim_dir  = work_dir / sim["name"]
        out_dir  = sim_dir / "outputs"
        sim_dir.mkdir(parents=True, exist_ok=True)
        out_dir.mkdir(exist_ok=True)

        # Write input file
        lam = float(np.sqrt(1.0 + 2.0 / sim["beta"]))
        lam = min(lam, 0.92 * 4.0 / 2)

        content = f"""<job>
problem_id = {sim['name']}

<time>
cfl_number  = 0.3
tlim        = 2.0
nlim        = -1

<mesh>
nx1    = 128
x1min  = -2.00
x1max  =  2.00
ix1_bc = periodic
ox1_bc = periodic
nx2    = 128
x2min  = -2.00
x2max  =  2.00
ix2_bc = periodic
ox2_bc = periodic
nx3    = 32
x3min  = -0.50
x3max  =  0.50
ix3_bc = periodic
ox3_bc = periodic

<meshblock>
nx1 = 32
nx2 = 32
nx3 = 32

<hydro>
iso_sound_speed = 1.0

<problem>
four_pi_G    = 39.478418
mach_number  = {sim['mach']:.4f}
plasma_beta  = {sim['beta']:.4f}
wavelength   = {lam:.6f}
perturb_ampl = {sim['epsilon']:.6e}

<output1>
file_type = hdf5
variable  = prim
id        = out1
dt        = 0.2
"""
        input_path = sim_dir / f"{sim['name']}.in"
        input_path.write_text(content)

        cmd = [
            "mpirun",
            "--oversubscribe",
            "-np", str(16),
            "--bind-to", "none",
            athena_bin,
            "-i", str(input_path),
            "-d", "outputs/",
        ]

        t0 = time.time()
        log_path = sim_dir / "athena.log"
        with open(log_path, "w") as f:
            proc = subprocess.run(
                cmd, stdout=f, stderr=subprocess.STDOUT, cwd=str(sim_dir)
            )
        elapsed = time.time() - t0

        n_out = len(list(out_dir.glob("*.athdf")))
        return {
            "name":       sim["name"],
            "mach":       sim["mach"],
            "beta":       sim["beta"],
            "epsilon":    sim["epsilon"],
            "batch":      sim["batch"],
            "status":     "PASS" if proc.returncode == 0 else "FAIL",
            "returncode": proc.returncode,
            "elapsed_s":  round(elapsed, 1),
            "n_outputs":  n_out,
        }

    RAY_AVAILABLE = True

except ImportError:
    RAY_AVAILABLE = False


# ── Parameter generation ──────────────────────────────────────────────────────

def sim_name(M, B, eps, batch, tag=""):
    """Short simulation name safe for Athena++ problem_id."""
    # Encode M and B without decimals
    m_tag  = f"M{int(M*10):03d}"          # M=2.5 → M025
    b_tag  = f"b{int(B*1000):04d}"        # β=0.7 → b0700
    e_tag  = f"e{int(-np.log10(eps)):d}"  # 1e-2 → e2
    return f"{m_tag}_{b_tag}_{e_tag}_bt{batch}{tag}"


def generate_batch1():
    mach  = [0.5, 1.0, 1.5, 2.0, 2.5, 3.0, 4.0, 5.0, 7.0, 10.0]
    beta  = [0.1, 0.2, 0.5, 0.7, 1.0, 1.5, 2.0, 3.0, 5.0, 10.0]
    sims  = []
    for M, B in product(mach, beta):
        sims.append(dict(
            mach=M, beta=B, epsilon=1e-2, batch=1,
            name=sim_name(M, B, 1e-2, 1)
        ))
    return sims  # 100 sims


def generate_batch2():
    sims = []
    # Regime boundaries (M-β transition region)
    for M in [2.0, 2.5, 3.0, 4.0]:
        for B in [0.7, 0.8, 0.9, 1.0, 1.2, 1.5]:
            for eps in [1e-2, 1e-3]:
                sims.append(dict(
                    mach=M, beta=B, epsilon=eps, batch=2,
                    name=sim_name(M, B, eps, 2, "r")
                ))
    # W3-like conditions (M~2.5-3.5, β~0.5-1.5)
    for M in [2.5, 3.0, 3.5]:
        for B in [0.5, 0.7, 1.0, 1.5]:
            for eps in [1e-2, 1e-3, 1e-1]:
                sims.append(dict(
                    mach=M, beta=B, epsilon=eps, batch=2,
                    name=sim_name(M, B, eps, 2, "w")
                ))
    # High-Mach exploration
    for M in [5.0, 7.0, 10.0]:
        for B in [0.5, 1.0, 2.0, 5.0]:
            for eps in [1e-2, 1e-3]:
                sims.append(dict(
                    mach=M, beta=B, epsilon=eps, batch=2,
                    name=sim_name(M, B, eps, 2, "h")
                ))
    return sims[:120]  # exactly 120


# ── Status / progress tracking ────────────────────────────────────────────────

def write_status(batch, total, done, failed, results):
    elapsed = time.time() - CAMPAIGN_START
    remaining = total - done - failed
    eta_s = (elapsed / max(done, 1)) * remaining if done > 0 else None
    status = {
        "batch":        batch,
        "total":        total,
        "completed":    done,
        "failed":       failed,
        "remaining":    remaining,
        "elapsed_h":    round(elapsed / 3600, 2),
        "eta_h":        round(eta_s / 3600, 2) if eta_s else None,
        "updated":      time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "results":      results,
    }
    STATUS_FILE.write_text(json.dumps(status, indent=2))
    return status


def print_progress(status):
    eta = f"{status['eta_h']:.1f}h" if status['eta_h'] else "estimating..."
    print(
        f"  [{time.strftime('%H:%M:%S')}] "
        f"Batch {status['batch']} | "
        f"{status['completed']}/{status['total']} done | "
        f"{status['failed']} failed | "
        f"Elapsed: {status['elapsed_h']:.1f}h | "
        f"ETA: {eta}"
    )


# ── Batch runner ──────────────────────────────────────────────────────────────

def run_batch_ray(sims, batch_num):
    """Submit all sims in a batch to Ray and wait, with live progress."""
    global CAMPAIGN_START
    results_all = []
    done, failed = 0, 0

    print(f"\n{'='*70}")
    print(f"  BATCH {batch_num}: {len(sims)} simulations")
    print(f"  16 MPI procs each  ·  14 simultaneous (224 cores)")
    print(f"  Expected completion: {len(sims) * 170667 / (224 * 3600):.1f} h")
    print(f"{'='*70}")

    # Submit ALL at once — Ray queues automatically at 14 simultaneous
    futures = [
        run_sim_ray.remote(sim, str(WORK_DIR), ATHENA_BIN)
        for sim in sims
    ]

    not_ready = futures
    ready_refs = []

    while not_ready:
        ready_refs, not_ready = ray.wait(not_ready, num_returns=1, timeout=60)
        for ref in ready_refs:
            r = ray.get(ref)
            results_all.append(r)
            if r["status"] == "PASS":
                done += 1
            else:
                failed += 1
                print(f"  ⚠ FAIL: {r['name']} (exit {r['returncode']})")

        st = write_status(batch_num, len(sims), done, failed, results_all)
        print_progress(st)

    return results_all


def run_batch_sequential(sims, batch_num):
    """Fallback: sequential run without Ray."""
    results_all = []
    for i, sim in enumerate(sims):
        print(f"[{i+1}/{len(sims)}] {sim['name']}")
        sim_dir = WORK_DIR / sim["name"]
        out_dir = sim_dir / "outputs"
        sim_dir.mkdir(parents=True, exist_ok=True)
        out_dir.mkdir(exist_ok=True)
        ip = make_input_file(sim, sim_dir)
        cmd = ["mpirun", "-np", "16", "--bind-to", "none", "--oversubscribe",
               ATHENA_BIN, "-i", str(ip), "-d", "outputs/"]
        t0 = time.time()
        r = subprocess.run(cmd, cwd=str(sim_dir), capture_output=True)
        elapsed = time.time() - t0
        n_out = len(list(out_dir.glob("*.athdf")))
        result = dict(
            name=sim["name"], mach=sim["mach"], beta=sim["beta"],
            epsilon=sim["epsilon"], batch=batch_num,
            status="PASS" if r.returncode == 0 else "FAIL",
            returncode=r.returncode, elapsed_s=round(elapsed, 1),
            n_outputs=n_out,
        )
        results_all.append(result)
        print(f"  → {result['status']} in {elapsed/3600:.2f}h ({n_out} outputs)")
        write_status(batch_num, len(sims), len(results_all), 0, results_all)
    return results_all


# ── Quick analysis ─────────────────────────────────────────────────────────────

def quick_analysis(results, batch_num):
    """Compute density contrast for all completed sims, write summary."""
    try:
        import h5py
    except ImportError:
        print("  h5py not available — skipping density analysis")
        return

    summary = []
    for r in results:
        if r["status"] != "PASS":
            continue
        sim_dir = WORK_DIR / r["name"]
        outputs = sorted((sim_dir / "outputs").glob("*.athdf"))
        if not outputs:
            continue
        try:
            with h5py.File(outputs[-1], "r") as f:
                data = f["prim"][:]
                rho = data[0]  # density is variable 0
                rho_mean = float(np.mean(rho))
                rho_max  = float(np.max(rho))
                contrast = rho_max / rho_mean
                frac_2x  = float(np.sum(rho > 2*rho_mean) / rho.size * 100)
            summary.append(dict(
                name=r["name"], mach=r["mach"], beta=r["beta"],
                epsilon=r["epsilon"],
                rho_mean=round(rho_mean, 4),
                rho_max=round(rho_max, 4),
                contrast=round(contrast, 4),
                frac_gt2x=round(frac_2x, 2),
                n_outputs=r["n_outputs"],
                elapsed_h=round(r["elapsed_s"]/3600, 3),
            ))
        except Exception as e:
            print(f"  Analysis error for {r['name']}: {e}")

    if not summary:
        return

    out_path = WORK_DIR / f"batch{batch_num}_analysis.json"
    out_path.write_text(json.dumps(summary, indent=2))
    print(f"\n  Analysis written: {out_path}")

    # Print ASCII table
    print(f"\n  {'Name':<30} {'M':>4} {'β':>5} {'ρmax/ρmean':>10} {'>2×mean %':>10}")
    print(f"  {'-'*30} {'-'*4} {'-'*5} {'-'*10} {'-'*10}")
    for s in sorted(summary, key=lambda x: (-x['contrast'], x['mach'])):
        print(f"  {s['name']:<30} {s['mach']:>4.1f} {s['beta']:>5.2f} "
              f"{s['contrast']:>10.3f} {s['frac_gt2x']:>10.2f}")


# ── Main ──────────────────────────────────────────────────────────────────────

def main():
    WORK_DIR.mkdir(parents=True, exist_ok=True)
    LOG_DIR.mkdir(exist_ok=True)

    print("=" * 70)
    print("  1-DAY FILAMENT SPACING CAMPAIGN — astra-climate")
    print(f"  Resolution: {NX1}×{NX2}×{NX3} (128³-class)")
    print(f"  4πG = {FOUR_PI_G:.3f}  →  λ_J = 1.0 code unit")
    print(f"  tlim = {TLIM} code units  ≈  4 free-fall times")
    print(f"  MPI: {N_PROCS_PER_SIM} procs/sim  ·  ~14 simultaneous on 224 cores")
    print(f"  Started: {time.strftime('%Y-%m-%d %H:%M:%S UTC', time.gmtime())}")
    print("=" * 70)

    # Initialise Ray
    if RAY_AVAILABLE:
        ray.init(address="auto", ignore_reinit_error=True)
        print(f"\n  Ray initialised: {ray.available_resources()}")
        runner = run_batch_ray
    else:
        print("\n  Ray not available — using sequential fallback")
        runner = run_batch_sequential

    # ── Batch 1: broad parameter sweep ──────────────────────────────────────
    print("\n─── BATCH 1: Broad 10×10 (M,β) sweep ──────────────────────────────")
    batch1 = generate_batch1()
    t1_start = time.time()
    results1 = runner(batch1, batch_num=1)
    t1_elapsed = time.time() - t1_start

    n_pass1 = sum(1 for r in results1 if r["status"] == "PASS")
    print(f"\n  Batch 1 complete: {n_pass1}/{len(batch1)} passed in {t1_elapsed/3600:.2f}h")

    with open(WORK_DIR / "batch1_results.json", "w") as f:
        json.dump(results1, f, indent=2)

    quick_analysis(results1, 1)

    # ── Batch 2: focused deep-dive ───────────────────────────────────────────
    print("\n─── BATCH 2: Focused deep-dive (regime boundaries + W3 + high-M) ──")
    batch2 = generate_batch2()
    t2_start = time.time()
    results2 = runner(batch2, batch_num=2)
    t2_elapsed = time.time() - t2_start

    n_pass2 = sum(1 for r in results2 if r["status"] == "PASS")
    print(f"\n  Batch 2 complete: {n_pass2}/{len(batch2)} passed in {t2_elapsed/3600:.2f}h")

    with open(WORK_DIR / "batch2_results.json", "w") as f:
        json.dump(results2, f, indent=2)

    quick_analysis(results2, 2)

    # ── Final summary ────────────────────────────────────────────────────────
    total_elapsed = time.time() - CAMPAIGN_START
    total_pass    = n_pass1 + n_pass2
    total_sims    = len(batch1) + len(batch2)

    print("\n" + "=" * 70)
    print("  CAMPAIGN COMPLETE")
    print(f"  Total: {total_pass}/{total_sims} simulations passed")
    print(f"  Elapsed: {total_elapsed/3600:.2f} h")
    print(f"  Output: {WORK_DIR}")
    print("=" * 70)

    write_status("DONE", total_sims, total_pass,
                 total_sims - total_pass, results1 + results2)

    if RAY_AVAILABLE:
        ray.shutdown()


if __name__ == "__main__":
    main()
