#!/usr/bin/env python3
"""
C8 λ/W TARGETED RE-RUN
=======================
35 sims: 5β × 7θ × 1 seed (seed=42)
- tlim set per-sim to t_frag_s42 + 0.15 t_J (tight buffer, minimises runtime)
- HDF5 snapshots RETAINED (not cleaned) — needed for λ/W(θ,β) analysis
- Snapshot dt=0.05 t_J → 2–3 snapshots bracketing fragmentation
- Same domain as C8: 512×64×64, 16λ_J × 1λ_J × 1λ_J, oblique B

Author: ASTRA PA  Date: 2026-05-01
"""
import os, json, re, subprocess, time, threading, shutil
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path
from datetime import datetime, timezone
import numpy as np

ATHENA_EXE = "/home/fetch-agi/athena/bin/athena"
FOUR_PI_G  = 39.478417604357
W_CORE     = 0.3          # filament half-width in λ_J
DT_FRAG    = 1.0e-8
BASE_DIR   = Path("/data/peer_response_runs/C8_lw")
BASE_DIR.mkdir(parents=True, exist_ok=True)

log_lock  = threading.Lock()
results   = []
rlock     = threading.Lock()
CYCLE_PAT = re.compile(r'time=([0-9.e+\-]+)\s+dt=([0-9.e+\-]+)')

# ── Per-sim tlim from C8 seed=42 t_frag + 0.15 buffer ───────────────────────
TLIM_MAP = {
    (0,   0.3): 1.618, (0,   0.5): 1.598, (0,   1.0): 1.553,
    (0,   1.5): 1.362, (0,   2.0): 1.359,
    (15,  0.3): 1.577, (15,  0.5): 1.549, (15,  1.0): 1.421,
    (15,  1.5): 1.365, (15,  2.0): 1.294,
    (30,  0.3): 1.108, (30,  0.5): 1.023, (30,  1.0): 0.994,
    (30,  1.5): 0.987, (30,  2.0): 1.008,
    (45,  0.3): 0.976, (45,  0.5): 0.865, (45,  1.0): 0.792,
    (45,  1.5): 0.817, (45,  2.0): 0.818,
    (60,  0.3): 0.863, (60,  0.5): 0.782, (60,  1.0): 0.720,
    (60,  1.5): 0.728, (60,  2.0): 0.734,
    (75,  0.3): 0.798, (75,  0.5): 0.799, (75,  1.0): 0.689,
    (75,  1.5): 0.681, (75,  2.0): 0.694,
    (90,  0.3): 0.781, (90,  0.5): 0.810, (90,  1.0): 0.684,
    (90,  1.5): 0.668, (90,  2.0): 0.703,
}

def utcnow():
    return datetime.now(timezone.utc).strftime("%H:%M:%S")

def log(msg, fh=None):
    line = f"[{utcnow()}] {msg}"
    with log_lock:
        print(line, flush=True)
        if fh:
            fh.write(line + "\n"); fh.flush()

def find_tfrag_hst(hst_path):
    try:
        with open(hst_path) as f:
            lines = [l for l in f if not l.startswith('#') and l.strip()]
        for line in reversed(lines):
            p = line.split()
            if len(p) >= 2:
                try:
                    if float(p[1]) >= DT_FRAG:
                        return float(p[0])
                except ValueError:
                    continue
    except Exception:
        pass
    return None

def make_athinput(sid, beta, theta, tlim):
    return f"""<job>
problem_id = {sid}

<time>
cfl_number = 0.3
nlim       = -1
tlim       = {tlim}

<output1>
file_type  = hst
dt         = 0.005
id         = hst

<output2>
file_type  = hdf5
dt         = 0.05
id         = snap
variable   = prim

<mesh>
nx1 = 512
nx2 = 64
nx3 = 64
x1min = 0.0
x1max = 16.0
x2min = -0.5
x2max = 0.5
x3min = -0.5
x3max = 0.5
ix1_bc = periodic
ox1_bc = periodic
ix2_bc = periodic
ox2_bc = periodic
ix3_bc = periodic
ox3_bc = periodic

<meshblock>
nx1 = 64
nx2 = 64
nx3 = 32

<hydro>
iso_sound_speed = 1.0

<gravity>
grav_mean_rho = {max(1.5, 1.0):.6f}

<problem>
four_pi_G       = {FOUR_PI_G}
f_line_mass     = 1.5
plasma_beta     = {beta}
mach_number     = 1.0
W_core          = {W_CORE}
perturb_ampl    = 0.0001
random_seed     = 42
bfield_geometry = oblique
theta_deg       = {float(theta)}
"""

def run_sim(cfg, log_fh, results_file):
    sid     = cfg['sim_id']
    rundir  = Path(cfg['rundir'])
    np_sim  = cfg['np']
    timeout = cfg.get('timeout_s', 7200)

    rundir.mkdir(parents=True, exist_ok=True)
    (rundir / "athinput").write_text(cfg['athinput'])

    # Skip if already done
    hst_list = list(rundir.glob("*.hst"))
    if hst_list:
        tf = find_tfrag_hst(str(hst_list[0]))
        if tf is not None:
            log(f"SKIP {sid}  (t_frag={tf:.4f})", log_fh)
            res = {**cfg['params'], 'sim_id': sid,
                   'outcome': 'FRAG', 't_frag': tf, 'skipped': True, 'wall_s': 0}
            with rlock:
                results.append(res)
                json.dump(results, open(results_file, 'w'), indent=2)
            return res

    cmd = ["mpirun", "-np", str(np_sim),
           ATHENA_EXE, "-i", str(rundir / "athinput"), "-d", str(rundir)]
    t0 = time.time()
    outcome = "TIMEOUT"
    t_frag  = None
    last_dt = 1.0
    stdout_lines = []

    try:
        proc = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                                cwd=str(rundir), text=True, bufsize=1)
        for line in proc.stdout:
            stdout_lines.append(line)
            m = CYCLE_PAT.search(line)
            if m:
                sim_t = float(m.group(1))
                dt_v  = float(m.group(2))
                last_dt = dt_v
                if dt_v < DT_FRAG:
                    outcome = "FRAG"
                    t_frag  = sim_t
                    proc.kill()
                    break
            if time.time() - t0 > timeout:
                proc.kill(); break
        proc.wait(timeout=30)
    except Exception as e:
        outcome = "FAILED"
        log(f"ERROR {sid}: {e}", log_fh)

    wall = time.time() - t0

    # HST fallback
    if outcome != "FRAG":
        hst_list = list(rundir.glob("*.hst"))
        if hst_list:
            tf2 = find_tfrag_hst(str(hst_list[0]))
            if tf2:
                outcome = "FRAG"; t_frag = tf2

    # ── Save stdout (last 1000 lines)
    (rundir / "stdout.txt").write_text("".join(stdout_lines[-1000:]))

    # ── HDF5 KEPT — not deleted (needed for λ/W analysis)
    n_hdf5 = len(list(rundir.glob("*.athdf")))

    tf_str = f"{t_frag:.4f}" if t_frag else "N/A"
    log(f"{outcome:8s} {sid}  t_frag={tf_str}  dt={last_dt:.2e}  "
        f"wall={wall:.0f}s  hdf5={n_hdf5}", log_fh)

    res = {**cfg['params'], 'sim_id': sid,
           'outcome': outcome, 't_frag': t_frag, 'wall_s': wall, 'n_hdf5': n_hdf5}
    with rlock:
        results.append(res)
        json.dump(results, open(results_file, 'w'), indent=2)
    return res

# ── λ/W analysis ──────────────────────────────────────────────────────────────
def analyse_lambda_W(results_list, output_file):
    try:
        import h5py
        from scipy.signal import find_peaks
    except ImportError:
        log("h5py/scipy unavailable — skipping λ/W analysis")
        return []

    lw_results = []
    for res in results_list:
        if res.get('outcome') != 'FRAG':
            lw_results.append({**res, 'lambda_W': None, 'quality': 'NOT_FRAG'})
            continue

        sid    = res['sim_id']
        simdir = BASE_DIR / sid
        athdf  = sorted(simdir.glob("*.athdf"))
        if not athdf:
            lw_results.append({**res, 'lambda_W': None, 'quality': 'NO_HDF5'})
            continue

        # Use the last snapshot (post-fragmentation)
        try:
            with h5py.File(athdf[-1], 'r') as hf:
                rho = np.array(hf['prim'][0])   # density
                x1v = np.array(hf['x1v'])
        except Exception as e:
            log(f"  HDF5 error {sid}: {e}")
            lw_results.append({**res, 'lambda_W': None, 'quality': 'HDF5_ERROR'})
            continue

        # Column density along filament (x1) axis
        sigma   = np.sum(rho, axis=(0, 1))      # shape (nx1,)
        dx      = (x1v[-1] - x1v[0]) / (len(x1v) - 1)
        Lx      = x1v[-1] - x1v[0]
        sig_bg  = sigma.mean()
        drho    = sigma - sig_bg
        rho_max = sigma.max()

        # Peak detection
        min_sep = max(4, int(0.25 / dx))   # minimum 0.25 λ_J between peaks
        peaks, _ = find_peaks(drho,
                              height=0.04 * rho_max,
                              distance=min_sep,
                              prominence=0.03 * rho_max)
        n_peaks = len(peaks)

        if n_peaks < 2:
            lw_results.append({**res, 'lambda_W': None, 'n_peaks': n_peaks,
                               'quality': 'FLAT_PROFILE'})
            continue

        spacings_lJ = np.diff(peaks) * dx
        lam         = float(np.median(spacings_lJ))
        lam_std     = float(np.std(spacings_lJ))
        lw          = round(lam / W_CORE, 3)
        lw_std      = round(lam_std / W_CORE, 3)
        quality     = 'GOOD' if n_peaks >= 4 and 0.2 < lam < Lx / 2 else 'MARGINAL'

        lw_results.append({**res,
                           'lambda_W':     lw,
                           'lambda_W_std': lw_std,
                           'n_peaks':      n_peaks,
                           'lambda_frag':  round(lam, 4),
                           'quality':      quality})
        log(f"  λ/W {sid}: {lw:.3f}±{lw_std:.3f}  n_peaks={n_peaks}  [{quality}]")

    json.dump(lw_results, open(output_file, 'w'), indent=2)

    # Summary by theta and beta
    good = [r for r in lw_results if r.get('quality') in ('GOOD','MARGINAL') and r.get('lambda_W')]
    if good:
        print("\n" + "="*60)
        print("λ/W(θ, β) RESULTS")
        print("="*60)
        by_theta = {}
        for r in good:
            by_theta.setdefault(r['theta'], []).append(r['lambda_W'])
        print("By θ (mean ± std):")
        for th in sorted(by_theta):
            v = by_theta[th]
            print(f"  θ={th:3d}°:  λ/W = {np.mean(v):.3f} ± {np.std(v):.3f}  (n={len(v)})")

        by_beta = {}
        for r in good:
            by_beta.setdefault(r['beta'], []).append(r['lambda_W'])
        print("By β:")
        for b in sorted(by_beta):
            v = by_beta[b]
            print(f"  β={b}:  λ/W = {np.mean(v):.3f} ± {np.std(v):.3f}  (n={len(v)})")

        full_lw = [r['lambda_W'] for r in good]
        print(f"\nOverall λ/W: {np.mean(full_lw):.3f} ± {np.std(full_lw):.3f}  (N={len(full_lw)})")

    return lw_results

# ── Build queue ───────────────────────────────────────────────────────────────
def build_queue():
    THETAS = [0, 15, 30, 45, 60, 75, 90]
    BETAS  = [0.3, 0.5, 1.0, 1.5, 2.0]
    queue  = []
    for theta in THETAS:
        for beta in BETAS:
            tlim   = TLIM_MAP[(theta, beta)]
            bs     = f"{beta}".replace('.', 'p')
            sid    = f"C8lw_b{bs}_th{theta}_s42"
            rundir = BASE_DIR / sid
            queue.append({
                'sim_id':   sid,
                'rundir':   str(rundir),
                'athinput': make_athinput(sid, beta, theta, tlim),
                'np':       16,
                'timeout_s': 7200,
                'params':   {'theta': theta, 'beta': beta, 'seed': 42,
                             'tlim': tlim, 'campaign': 'C8lw'},
            })
    return queue

# ── Main ──────────────────────────────────────────────────────────────────────
def main():
    queue        = build_queue()
    results_file = str(BASE_DIR / "results.json")
    log_path     = BASE_DIR / "campaign.log"

    print("="*60)
    print(f"C8 λ/W RE-RUN: {len(queue)} sims, seed=42, tlim per-sim")
    print(f"Domain: 512×64×64, 16λ_J × 1λ_J × 1λ_J, oblique B")
    print(f"HDF5 snapshots: RETAINED for λ/W analysis")
    print(f"Max concurrent: 14 (224 CPUs / 16 per sim)")
    print("="*60)

    t0 = time.time()
    with open(log_path, 'w') as log_fh:
        with ThreadPoolExecutor(max_workers=14) as pool:
            futs = {pool.submit(run_sim, cfg, log_fh, results_file): cfg
                    for cfg in queue}
            n_done = 0
            for fut in as_completed(futs):
                n_done += 1
                elapsed = time.time() - t0
                rate    = n_done / (elapsed / 3600) if elapsed > 0 else 0
                eta     = (len(queue) - n_done) / rate if rate > 0 else 99
                log(f"  Progress: {n_done}/{len(queue)} | rate={rate:.1f}/hr | ETA={eta:.2f}h",
                    log_fh)

    wall_hr = (time.time() - t0) / 3600
    log(f"All sims complete in {wall_hr:.2f} hr")

    # ── λ/W analysis ──────────────────────────────────────────────────────────
    print()
    print("="*60)
    print("RUNNING λ/W ANALYSIS ON HDF5 SNAPSHOTS")
    print("="*60)
    lw_out = str(BASE_DIR / "lambda_W_analysis.json")
    lw_res = analyse_lambda_W(results, lw_out)
    print(f"\nλ/W analysis saved: {lw_out}")

    # ── Post-analysis HDF5 cleanup ─────────────────────────────────────────
    print()
    print("Cleaning HDF5 files post-analysis...")
    n_del = 0
    for p in BASE_DIR.rglob("*.athdf"):
        p.unlink()
        n_del += 1
    print(f"Deleted {n_del} HDF5 files")
    import subprocess as sp
    sp.run(["df", "-h", "/data"])

if __name__ == "__main__":
    main()
