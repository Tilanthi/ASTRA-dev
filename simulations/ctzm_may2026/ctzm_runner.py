#!/usr/bin/env python3
"""
CTZM — Critical Transition Zone Mapping Runner — Referee Response May 2026
96 sims: f=[1.2,1.3,1.4,1.5] × beta=[0.3,0.5,1.0,2.0] × M=[1.0,2.0] × seeds=[0,1,2]
Domain: 256×64×64, L=8λ_J, longitudinal B, HDF5 at dt=0.02 tJ
Binary: /home/fetch-agi/athena/bin/athena  (filament_spacing_pr pgen, existing)

Key difference from prior campaigns: keeps ALL HDF5 snapshots per sim,
runs inline λ/W peak-detection after FRAG, then purges HDF5 immediately.
Science: does λ/W evolve smoothly or discontinuously across f=1.2-1.5?
"""

import json, os, signal, subprocess, sys, time, math, shutil, glob
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path
import numpy as np
from scipy.signal import find_peaks
from scipy.ndimage import gaussian_filter1d
import h5py

# ── Constants ──────────────────────────────────────────────────────────────
ATHENA_BIN  = "/home/fetch-agi/athena/bin/athena"
BASE_DIR    = Path("/data/ctzm_runs")
FOUR_PI_G   = 39.4784176044
CS          = 1.0
W_CORE      = 0.3          # filament half-width in λ_J
DX1         = 8.0 / 256    # λ_J per cell along filament axis
DT_KILL     = 1.0e-6       # fragmentation threshold
POLL        = 8.0          # seconds between dt polls
NP          = 32           # MPI ranks: 256×64×64 / 32³ = 32 meshblocks
MAX_CONC    = 6            # 6 × 32 = 192 vCPUs (safe on 220-vCPU node)
WALL_TIME   = 14400        # 4h per sim (near-critical f=1.2 may need ~2-3h)
TLIM        = 4.0          # generous simulation time limit (tJ)
HDF5_DT     = 0.02         # fine snapshots for λ/W time-series
MAX_HDF5_GB = 8.0          # safety cap: prune if a sim accumulates > 8 GB HDF5

# ── Parameter space (from ctzm_parameter_grid.json) ───────────────────────
F_LIST    = [1.2, 1.3, 1.4, 1.5]
BETA_LIST = [0.3, 0.5, 1.0, 2.0]
MACH_LIST = [1.0, 2.0]
SEEDS     = [0, 1, 2]

def build_sim_list():
    sims = []
    for f in F_LIST:
        for beta in BETA_LIST:
            for mach in MACH_LIST:
                for seed in SEEDS:
                    f_str   = f"{f:.1f}".replace('.','p')
                    b_str   = f"{beta:.1f}".replace('.','p')
                    m_str   = f"{mach:.1f}".replace('.','p')
                    run_id  = f"CTZM_f{f_str}_b{b_str}_m{m_str}_s{seed}"
                    sims.append({
                        "run_id": run_id,
                        "f": f, "beta": beta, "mach": mach, "seed": seed,
                    })
    return sims

# ── Input file generator ───────────────────────────────────────────────────
def make_athinput(run_dir: Path, p: dict) -> Path:
    athinput = f"""<comment>
problem   = CTZM transition zone mapping
run_id    = {p['run_id']}

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
f_line_mass     = {p['f']}
plasma_beta     = {p['beta']}
mach_number     = {p['mach']}
W_core          = {W_CORE}
perturb_ampl    = 1.0e-4
random_seed     = {p['seed']}
bfield_geometry = longitudinal
theta_deg       = 0.0
"""
    inp = run_dir / "athinput.ctzm"
    inp.write_text(athinput)
    return inp

# ── λ/W analysis from a single HDF5 snapshot ──────────────────────────────
def measure_lambda_W_snapshot(hdf5_path: Path):
    """
    Reconstruct global density from meshblocks, compute column density
    along filament axis, detect peaks, return (t, n_peaks, lambda_W).
    Returns None on any error.

    Athena++ HDF5 layout (confirmed from structure check):
      f.attrs['Time']          — simulation time (attribute, not dataset)
      f['prim']                — shape (n_vars, n_mb, nk, nj, ni); var 0 = density
      f['LogicalLocations']    — shape (n_mb, 3); cols = (x1_loc, x2_loc, x3_loc)
    """
    try:
        with h5py.File(hdf5_path, 'r') as f:
            t_val = float(f.attrs['Time'])
            prim  = f['prim'][...]          # (n_vars=5, n_mb=32, nk=32, nj=32, ni=32)
            locs  = f['LogicalLocations'][:] # (n_mb=32, 3)

        n_vars, n_mb, nk_mb, nj_mb, ni_mb = prim.shape
        NI, NJ, NK = 256, 64, 64

        # Reconstruct global density array
        rho_global = np.zeros((NK, NJ, NI), dtype=np.float32)
        for mb in range(n_mb):
            lx1, lx2, lx3 = int(locs[mb, 0]), int(locs[mb, 1]), int(locs[mb, 2])
            i0 = lx1 * ni_mb
            j0 = lx2 * nj_mb
            k0 = lx3 * nk_mb
            rho_global[k0:k0+nk_mb, j0:j0+nj_mb, i0:i0+ni_mb] = prim[0, mb]  # var 0 = rho

        # Column-averaged linear mass density along x1 (mean over x2, x3)
        col_rho = rho_global.mean(axis=(0, 1))  # shape (NI=256,)

        # Light smoothing (σ=2 cells)
        col_smooth = gaussian_filter1d(col_rho, sigma=2)

        # Peak detection — minimum prominence = 5% of dynamic range
        dyn_range = col_smooth.max() - col_smooth.min()
        min_prom  = max(0.05 * dyn_range, 0.01 * col_smooth.mean())
        peaks, _  = find_peaks(col_smooth, prominence=min_prom, distance=8)

        n_peaks = len(peaks)
        lw = None
        if n_peaks >= 2:
            spacings = np.diff(peaks) * DX1   # convert cells → λ_J
            lw = float(np.median(spacings) / W_CORE)

        return {"t": round(t_val, 4), "n_peaks": n_peaks, "lambda_W": lw}

    except Exception:
        return None

# ── Post-run: analyse all HDF5, classify, purge ───────────────────────────
def analyse_and_purge(run_dir: Path, t_frag):
    """
    Load every HDF5 snapshot, run peak detection, record λ/W time-series,
    classify as BEADING or RADIAL_COLLAPSE, then delete all HDF5 and XDMF.
    """
    hdf5_files = sorted(run_dir.glob("*.athdf"))
    series = []
    for hf in hdf5_files:
        result = measure_lambda_W_snapshot(hf)
        if result is not None:
            series.append(result)

    # Purge immediately
    for hf in hdf5_files:
        hf.unlink(missing_ok=True)
    for xf in run_dir.glob("*.xdmf"):
        xf.unlink(missing_ok=True)

    # Classification
    beading_snaps = [s for s in series if s["lambda_W"] is not None]
    if len(beading_snaps) >= 2:
        lw_vals        = [s["lambda_W"] for s in beading_snaps]
        classification = "BEADING"
        lw_mean        = float(np.mean(lw_vals))
        lw_std         = float(np.std(lw_vals))
        # Stable beading: coefficient of variation < 0.3
        if lw_std / lw_mean < 0.3:
            classification = "BEADING_STABLE"
        else:
            classification = "BEADING_TRANSIENT"
    else:
        classification = "RADIAL_COLLAPSE"
        lw_mean        = None
        lw_std         = None

    return classification, series, lw_mean, lw_std

# ── Run a single simulation ────────────────────────────────────────────────
def run_sim(p: dict) -> dict:
    run_id  = p["run_id"]
    run_dir = BASE_DIR / run_id
    run_dir.mkdir(parents=True, exist_ok=True)

    inp_file = make_athinput(run_dir, p)
    log_file = run_dir / "stdout.txt"

    cmd = [
        "mpirun", "--oversubscribe", "-np", str(NP),
        ATHENA_BIN, "-i", str(inp_file),
        "-d", str(run_dir),
    ]

    t_start = time.time()
    t_frag  = None
    outcome = "TIMEOUT"
    dt_min  = 999.0

    try:
        proc = subprocess.Popen(
            cmd,
            stdout=open(log_file, "w"),
            stderr=subprocess.STDOUT,
            preexec_fn=os.setsid
        )

        while True:
            elapsed = time.time() - t_start

            # Wall-time kill
            if elapsed > WALL_TIME:
                os.killpg(os.getpgid(proc.pid), signal.SIGKILL)
                outcome = "TIMEOUT"
                break

            # Poll returncode
            rc = proc.poll()
            if rc is not None:
                outcome = "COMPLETE" if rc == 0 else "FAILED"
                break

            # Safety HDF5 pruning: if accumulated > MAX_HDF5_GB, keep only last 30
            hdf5_list = sorted(run_dir.glob("*.athdf"))
            total_gb  = sum(h.stat().st_size for h in hdf5_list) / 1e9
            if total_gb > MAX_HDF5_GB and len(hdf5_list) > 30:
                for h in hdf5_list[:-30]:
                    h.unlink(missing_ok=True)

            # Scan HST for dt_min → FRAG detection
            hst_files = list(run_dir.glob("*.hst"))
            if hst_files:
                try:
                    lines = hst_files[0].read_text().split('\n')
                    for line in reversed(lines):
                        if line.strip() and not line.startswith('#'):
                            cols = line.split()
                            if len(cols) >= 2:
                                t_now  = float(cols[0])
                                dt_val = float(cols[1])
                                if dt_val < dt_min:
                                    dt_min = dt_val
                                if dt_val < DT_KILL:
                                    t_frag  = t_now
                                    outcome = "FRAG"
                                    os.killpg(os.getpgid(proc.pid), signal.SIGKILL)
                                    proc.wait(timeout=5)
                            break
                except Exception:
                    pass
                if outcome == "FRAG":
                    break

            time.sleep(POLL)

    except Exception as e:
        outcome = f"ERROR: {e}"

    wall = time.time() - t_start

    # ── Inline λ/W analysis + HDF5 purge ──────────────────────────────────
    classification = "N/A"
    lambda_W_series = []
    lw_mean = lw_std = None

    if outcome in ("FRAG", "COMPLETE", "TIMEOUT"):
        try:
            classification, lambda_W_series, lw_mean, lw_std = \
                analyse_and_purge(run_dir, t_frag)
        except Exception as e:
            classification = f"ANALYSIS_ERROR: {e}"
            # Still purge
            for hf in run_dir.glob("*.athdf"):
                hf.unlink(missing_ok=True)
    else:
        # On error: still clean up any HDF5
        for hf in run_dir.glob("*.athdf"):
            hf.unlink(missing_ok=True)

    result = {
        "run_id":           run_id,
        "f":                p["f"],
        "beta":             p["beta"],
        "mach":             p["mach"],
        "seed":             p["seed"],
        "outcome":          outcome,
        "t_frag":           t_frag,
        "dt_min":           dt_min,
        "wall_s":           round(wall, 1),
        "classification":   classification,
        "lw_mean":          lw_mean,
        "lw_std":           lw_std,
        "n_lw_snaps":       len([s for s in lambda_W_series if s["lambda_W"] is not None]),
        "lambda_W_series":  lambda_W_series,
    }

    lw_str = f"  λ/W={lw_mean:.2f}±{lw_std:.2f}" if lw_mean else ""
    print(
        f"[{run_id}] {outcome:8s} t={t_frag:.4f} t_J  {classification}{lw_str}"
        f"  wall={wall:.0f}s  dt={dt_min:.1e}",
        flush=True
    ) if t_frag else print(
        f"[{run_id}] {outcome:8s}  {classification}{lw_str}"
        f"  wall={wall:.0f}s  dt={dt_min:.1e}",
        flush=True
    )
    return result

# ── Main ───────────────────────────────────────────────────────────────────
def main():
    BASE_DIR.mkdir(parents=True, exist_ok=True)
    sims = build_sim_list()
    print(f"CTZM Campaign: {len(sims)} sims | NP={NP} | MAX_CONC={MAX_CONC}")
    print(f"f: {F_LIST} | beta: {BETA_LIST} | mach: {MACH_LIST} | seeds: {SEEDS}")
    print(f"HDF5 dt={HDF5_DT} tJ (inline λ/W analysis; HDF5 purged after each sim)")
    print("─" * 80)

    results   = []
    t_launch  = time.time()

    with ThreadPoolExecutor(max_workers=MAX_CONC) as pool:
        futures = {pool.submit(run_sim, s): s for s in sims}
        for fut in as_completed(futures):
            r = fut.result()
            results.append(r)
            (BASE_DIR / "ctzm_results.json").write_text(json.dumps(results, indent=2))

    total_wall = time.time() - t_launch
    n_frag     = sum(1 for r in results if r["outcome"] == "FRAG")
    n_timeout  = sum(1 for r in results if r["outcome"] == "TIMEOUT")
    n_beading  = sum(1 for r in results if "BEADING" in str(r.get("classification","")))
    n_radial   = sum(1 for r in results if r.get("classification") == "RADIAL_COLLAPSE")

    print("\n" + "=" * 80)
    print(f"CTZM CAMPAIGN COMPLETE: {len(results)} sims in {total_wall/60:.1f} min")
    print(f"  FRAG={n_frag}  TIMEOUT={n_timeout}")
    print(f"  BEADING={n_beading}  RADIAL_COLLAPSE={n_radial}")

    for f_val in F_LIST:
        sub = [r for r in results if r["f"]==f_val and r["outcome"]=="FRAG"]
        if sub:
            tfrags = [r["t_frag"] for r in sub]
            b_sub  = [r for r in sub if "BEADING" in str(r.get("classification",""))]
            lw_sub = [r["lw_mean"] for r in b_sub if r["lw_mean"]]
            lw_str = f" | mean λ/W={np.mean(lw_sub):.3f}" if lw_sub else " | no λ/W measured"
            print(f"  f={f_val}: {len(sub)} FRAG, "
                  f"mean t_frag={np.mean(tfrags):.4f} t_J, "
                  f"{len(b_sub)} BEADING{lw_str}")

    (BASE_DIR / "ctzm_results.json").write_text(json.dumps(results, indent=2))
    print(f"\nResults: {BASE_DIR}/ctzm_results.json")

if __name__ == "__main__":
    main()
