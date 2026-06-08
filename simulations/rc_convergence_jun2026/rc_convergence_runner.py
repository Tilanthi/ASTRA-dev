#!/usr/bin/env python3
"""
rc_convergence_runner.py — Rigid Cylinder Box-Size Convergence Test
====================================================================

Tests whether the rigid-cylinder λ/W ≈ 2.65 result at f=2.6 is a physical
fragmentation signal or a numerical box-resonance artefact.

Strategy: Run f=2.6, β=1.0, seeds={1,2,3} at THREE box lengths:
  - Lx = 8.0  (Lz × 0.5) : nx1=256, meshblock 8
  - Lx = 16.0 (Lz × 1.0) : EXISTING — from rigid_cylinder_campaign_jun2026
  - Lx = 32.0 (Lz × 2.0) : nx1=1024, meshblock 32

If λ/W is a resonance, it scales with Lx (number of preferred modes ∝ Lx).
If λ/W is physical, it converges to the same value at all Lx.

Cell size kept constant: dx = 16/512 = 0.03125 Jeans lengths.
Box transverse dimensions unchanged: ±1.0 in y,z (reflecting walls).

6 new simulations. Reference: existing 3 at Lx=16.

PI: Glenn J. White (Open University)
ASTRA-PA — 2026-06-08
"""

import os, sys, math, time, signal, threading, logging, subprocess
from pathlib import Path
from concurrent.futures import ProcessPoolExecutor, as_completed

import numpy as np
from scipy.ndimage import gaussian_filter1d
from scipy.signal import find_peaks
import h5py
import csv

# ── Paths ─────────────────────────────────────────────────────────────────────
ATHENA_BIN   = "/home/fetch-agi/athena/bin/athena"
CAMP_DIR     = Path("/data/rc_convergence")
SIMS_DIR     = CAMP_DIR / "sims"
RESULTS_DIR  = CAMP_DIR / "results"
LOG_FILE     = CAMP_DIR / "rc_convergence.log"
RESULTS_CSV  = RESULTS_DIR / "rc_convergence_results.csv"

# ── Physics ───────────────────────────────────────────────────────────────────
FOUR_PI_G   = 39.4784176044
W_CORE      = 0.3
W_FULL      = 0.6        # Formation width denominator
HGBS_MIN    = 2.52
HGBS_MAX    = 3.08

# ── Runner ────────────────────────────────────────────────────────────────────
MPIRANKS    = 32
MAX_CONC    = 3          # 3 concurrent × 32 MPI = 96 CPUs (leave headroom)
TLIM        = 2.0
HDF5_DT     = 0.05
HST_DT      = 0.005
CFL         = 0.3
TIMEOUT_SEC = 10800      # 3h hard cap
GRAV_RATIO  = 2000
DT_FLOOR    = 5e-6
DISK_WARN_GB = 30        # warn if /data free < 30 GB
DISK_KILL_GB = 15        # purge intermediate HDF5 if < 15 GB

# ── Campaign grid: 6 new sims (Lx=8 and Lx=32 only — Lx=16 already done) ────
ALL_SIMS = []
for lx_scale, nx1, mb_nx1 in [(0.5, 256, 8), (2.0, 1024, 32)]:
    lx     = 16.0 * lx_scale   # physical box length
    x1max  =  lx / 2.0
    x1min  = -lx / 2.0
    for seed in [1, 2, 3]:
        ALL_SIMS.append({
            "sim_id":   f"RCC_f2.6_b1.0_Lx{lx_scale:.1f}_s{seed}",
            "f":        2.6,
            "beta":     1.0,
            "mach":     1.0,
            "seed":     seed,
            "lx_scale": lx_scale,
            "lx":       lx,
            "x1min":    x1min,
            "x1max":    x1max,
            "nx1":      nx1,
            "mb_nx1":   mb_nx1,
        })

# ── Logging ───────────────────────────────────────────────────────────────────
for d in [SIMS_DIR, RESULTS_DIR]:
    d.mkdir(parents=True, exist_ok=True)

fmt = '%(asctime)s %(levelname)-8s %(message)s'
logging.basicConfig(
    level=logging.INFO, format=fmt,
    handlers=[logging.FileHandler(LOG_FILE, mode='w'),
              logging.StreamHandler(sys.stdout)]
)
log = logging.getLogger("rc_conv")


def disk_free_gb():
    st = os.statvfs("/data")
    return st.f_bavail * st.f_frsize / 1e9


def purge_intermediate_hdf5(sdir: Path, keep_last: int = 3):
    """Keep only the last `keep_last` HDF5 files to free space."""
    snaps = sorted(sdir.glob("*.athdf"))
    to_del = snaps[:-keep_last] if len(snaps) > keep_last else []
    for f in to_del:
        try:
            f.unlink()
            xdmf = f.with_suffix(".athdf.xdmf")
            if xdmf.exists():
                xdmf.unlink()
        except Exception:
            pass
    return len(to_del)


# ── athinput generation ───────────────────────────────────────────────────────
def make_athinput(sim: dict) -> str:
    f    = sim["f"]
    beta = sim["beta"]
    mach = sim["mach"]
    seed = sim["seed"]
    sid  = sim["sim_id"]
    x1min = sim["x1min"]
    x1max = sim["x1max"]
    nx1   = sim["nx1"]
    mb_nx1 = sim["mb_nx1"]

    return f"""<comment>
problem   = rigid_cylinder_convergence_test
job_label = {sid}

<job>
problem_id  = filament_frag

<output1>
file_type   = hdf5
variable    = prim
dt          = {HDF5_DT}
id          = prim

<output2>
file_type   = hst
dt          = {HST_DT}
id          = hst

<time>
cfl_number  = {CFL}
tlim        = {TLIM}
nlim        = -1

<mesh>
nx1         = {nx1}
x1min       = {x1min:.4f}
x1max       = {x1max:.4f}
ix1_bc      = periodic
ox1_bc      = periodic

nx2         = 64
x2min       = -1.0
x2max       =  1.0
ix2_bc      = user
ox2_bc      = user

nx3         = 64
x3min       = -1.0
x3max       =  1.0
ix3_bc      = user
ox3_bc      = user

<meshblock>
nx1 = {mb_nx1}
nx2 = 64
nx3 = 64

<hydro>
gamma           = 1.0
iso_sound_speed = 1.0

<gravity>
grav_mean_rho   = 1.0

<problem>
four_pi_G       = {FOUR_PI_G}
f_line_mass     = {f}
plasma_beta     = {beta}
theta_deg       = 0.0
mach_number     = {mach}
perturb_ampl    = 1.0
random_seed     = {seed}
W_core          = {W_CORE}
"""


# ── Kill helper ───────────────────────────────────────────────────────────────
def _kill(proc):
    pid = proc.pid
    for fn in [
        lambda: os.killpg(os.getpgid(pid), signal.SIGKILL),
        lambda: os.kill(pid, signal.SIGKILL),
        lambda: subprocess.run(["pkill", "-KILL", "-P", str(pid)],
                               capture_output=True, timeout=5),
    ]:
        try:
            fn()
        except Exception:
            pass
    time.sleep(0.5)


# ── λ/W measurement ───────────────────────────────────────────────────────────
def read_rho1d(athdf: Path, lx: float):
    """Return (rho_1d, NX) with physical length lx."""
    try:
        with h5py.File(str(athdf), "r") as fh:
            prim = fh["prim"][:]
            locs = fh["LogicalLocations"][:]
            mb   = fh.attrs["MeshBlockSize"]
            root = fh.attrs["RootGridSize"]
        rho_blk = prim[0]
        NX, NY, NZ = int(root[0]), int(root[1]), int(root[2])
        nx_mb, ny_mb, nz_mb = int(mb[0]), int(mb[1]), int(mb[2])
        rho3d = np.zeros([NZ, NY, NX], dtype=np.float32)
        for i, (ix1, ix2, ix3) in enumerate(locs):
            x0 = int(ix1) * nx_mb
            y0 = int(ix2) * ny_mb
            z0 = int(ix3) * nz_mb
            rho3d[z0:z0+nz_mb, y0:y0+ny_mb, x0:x0+nx_mb] = rho_blk[i]
        return rho3d.mean(axis=(0, 1)), NX
    except Exception:
        return None, None


def measure_lw(sdir: Path, lx: float) -> dict:
    """Measure λ/W from the best HDF5 snapshot in sdir."""
    snaps = sorted(sdir.glob("*.athdf"))
    if not snaps:
        return {"lW": None, "flag": "no_hdf5", "n_peaks": 0,
                "lambda_phys": None, "snap": None}

    dx_expected = lx / (512 * (lx / 16.0))   # constant regardless of box size

    best_score, best_data = -1.0, None
    for snap in snaps:
        rho1d, NX = read_rho1d(snap, lx)
        if rho1d is None:
            continue
        dx       = lx / NX
        sigma_px = max(2, int(W_FULL / dx / 4))
        sm       = gaussian_filter1d(rho1d, sigma=sigma_px)
        contrast = sm.max() / max(sm.mean(), 1e-10)
        amp      = sm.max() - sm.mean()
        min_d    = max(4, int(W_FULL / dx))
        prom     = max(0.1 * amp, 0.03 * sm.mean())
        peaks, _ = find_peaks(sm, distance=min_d, prominence=prom)
        score    = len(peaks) * math.log(contrast + 1)
        if score > best_score:
            best_score = score
            best_data  = (rho1d, NX, dx, peaks, contrast, snap.name)

    if best_data is None:
        return {"lW": None, "flag": "read_err", "n_peaks": 0,
                "lambda_phys": None, "snap": None}

    rho1d, NX, dx, peaks, contrast, snap_name = best_data
    if len(peaks) < 2:
        lw, lambda_phys, flag = None, None, "too_few_peaks"
    else:
        spacings     = np.diff(peaks) * dx
        lambda_phys  = float(np.mean(spacings))
        lw           = round(lambda_phys / W_FULL, 4)
        flag         = "ok"
        hgbs = HGBS_MIN <= lw <= HGBS_MAX
        log.info(f"  λ/W={lw:.4f}  λ={lambda_phys:.4f} J  npk={len(peaks)}"
                 f"  contrast={contrast:.2f}  HGBS={'YES' if hgbs else 'no'}")

    return {"lW": lw, "flag": flag, "n_peaks": len(peaks),
            "lambda_phys": lambda_phys, "snap": snap_name}


# ── Single sim runner ─────────────────────────────────────────────────────────
def run_single(sim: dict, idx: int, ntot: int) -> dict:
    sid   = sim["sim_id"]
    lx    = sim["lx"]
    sdir  = SIMS_DIR / sid
    sdir.mkdir(parents=True, exist_ok=True)

    hst   = sdir / "filament_frag.hst"
    inp   = sdir / f"{sid}.athinput"
    inp.write_text(make_athinput(sim))

    cmd = ["mpirun", "--oversubscribe", "-n", str(MPIRANKS),
           ATHENA_BIN, "-i", str(inp), "-d", str(sdir)]

    t0          = time.time()
    kill_reason = ""
    grav0       = None
    dt0         = None

    proc = subprocess.Popen(
        cmd, cwd=str(sdir),
        stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
        preexec_fn=os.setsid
    )

    def monitor():
        nonlocal kill_reason, grav0, dt0
        while proc.poll() is None:
            time.sleep(30)
            # Disk check — purge intermediates if low
            free = disk_free_gb()
            if free < DISK_KILL_GB:
                n = purge_intermediate_hdf5(sdir, keep_last=3)
                log.warning(f"Disk low ({free:.1f} GB free) — purged {n} HDF5 from {sid}")
            elif free < DISK_WARN_GB:
                log.warning(f"Disk warning: {free:.1f} GB free")

            if not hst.exists():
                continue
            try:
                rows = [l for l in hst.read_text().splitlines()
                        if not l.startswith("#") and l.strip()]
                if not rows:
                    continue
                last  = rows[-1].split()
                t_cur = float(last[0])
                dt_cur = abs(float(last[1]))
                grav_e = abs(float(last[9]))   # col 10 = grav-E

                if grav0 is None and grav_e > 0:
                    grav0 = grav_e
                if dt0 is None and dt_cur > 0:
                    dt0 = dt_cur

                if grav0 and grav_e / grav0 > GRAV_RATIO:
                    kill_reason = f"GRAV_FRAG@t={t_cur:.3f}"
                    _kill(proc)
                    return
                if dt0 and dt_cur < DT_FLOOR and t_cur > 0.05:
                    kill_reason = f"DT_COLLAPSE@t={t_cur:.3f}"
                    _kill(proc)
                    return
            except Exception:
                pass

    mon = threading.Thread(target=monitor, daemon=True)
    mon.start()

    try:
        proc.wait(timeout=TIMEOUT_SEC)
    except subprocess.TimeoutExpired:
        kill_reason = "TIMEOUT"
        _kill(proc)

    if not kill_reason:
        kill_reason = "COMPLETED"

    mon.join(timeout=5)
    wall = round(time.time() - t0)

    # λ/W measurement
    meas = measure_lw(sdir, lx)

    # Purge HDF5 after measurement to conserve disk
    for f_hdf5 in sdir.glob("*.athdf"):
        try:
            f_hdf5.unlink()
            xdmf = Path(str(f_hdf5) + ".xdmf")
            if xdmf.exists():
                xdmf.unlink()
        except Exception:
            pass
    log.info(f"  HDF5 purged for {sid} (disk free: {disk_free_gb():.1f} GB)")

    result = {
        "sim_id":    sid,
        "f":         sim["f"],
        "beta":      sim["beta"],
        "lx_scale":  sim["lx_scale"],
        "lx":        lx,
        "seed":      sim["seed"],
        "kill_reason": kill_reason,
        "wall_s":    wall,
        "lW":        meas["lW"],
        "flag":      meas["flag"],
        "n_peaks":   meas["n_peaks"],
        "lambda_phys": meas["lambda_phys"],
        "hgbs_match": (meas["lW"] is not None and
                       HGBS_MIN <= meas["lW"] <= HGBS_MAX),
    }

    log.info(
        f"[{idx}/{ntot}]  {sid:42s}  lW={str(meas['lW']):>8s}  "
        f"wall={wall:5d}s  Lx={lx:.1f}  {kill_reason}"
    )
    return result


# ── CSV writer ────────────────────────────────────────────────────────────────
FIELDS = ["sim_id","f","beta","lx_scale","lx","seed","kill_reason",
          "wall_s","lW","flag","n_peaks","lambda_phys","hgbs_match"]

def write_csv(results):
    with open(RESULTS_CSV, "w", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=FIELDS)
        w.writeheader()
        w.writerows([{k: r.get(k) for k in FIELDS} for r in results])


# ── Main ──────────────────────────────────────────────────────────────────────
def main():
    log.info("=" * 70)
    log.info("RC BOX-SIZE CONVERGENCE TEST")
    log.info(f"  6 sims: f=2.6, β=1.0, Lx∈{{8,32}}, seeds={{1,2,3}}")
    log.info(f"  Binary: {ATHENA_BIN}")
    log.info(f"  Disk free at start: {disk_free_gb():.1f} GB")
    log.info("=" * 70)

    results = []
    ntot    = len(ALL_SIMS)

    with ProcessPoolExecutor(max_workers=MAX_CONC) as ex:
        futs = {ex.submit(run_single, sim, i+1, ntot): sim
                for i, sim in enumerate(ALL_SIMS)}
        for fut in as_completed(futs):
            try:
                r = fut.result()
                results.append(r)
                write_csv(results)
            except Exception as e:
                sim = futs[fut]
                log.error(f"FAILED {sim['sim_id']}: {e}")

    log.info("\n" + "=" * 70)
    log.info("CONVERGENCE TEST COMPLETE")
    log.info(f"Disk free at end: {disk_free_gb():.1f} GB")
    log.info("")
    log.info("RESULTS SUMMARY")
    log.info(f"{'sim_id':45s}  {'Lx':>4}  {'lW':>8}  {'HGBS':>5}  event")
    log.info("-" * 80)
    for r in sorted(results, key=lambda x: (x["lx_scale"], x["seed"])):
        lw_str = f"{r['lW']:.4f}" if r["lW"] else "   None"
        hgbs   = "YES" if r["hgbs_match"] else "no"
        log.info(f"{r['sim_id']:45s}  {r['lx']:>4.0f}  {lw_str:>8}  "
                 f"{hgbs:>5}  {r['kill_reason']}")
    log.info("=" * 70)


if __name__ == "__main__":
    main()
