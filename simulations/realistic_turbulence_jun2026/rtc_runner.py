#!/usr/bin/env python3
"""
Realistic Turbulence Campaign (RTC) Runner
==========================================
1200 Athena++ MHD simulations — physical turbulence regime Mturb = 2–4
Addresses Referee Concerns #1 (Transient Beading) and #2 (Turbulence Amplitude Gap)

Cluster:  fetch-agi@34.143.130.135  (224 vCPU, 220 GB RAM, /data 492 GB)
Binary:   /home/fetch-agi/athena/bin/athena
Grid:     512 × 64 × 64, domain 16λJ × 2λJ × 2λJ, MPI NP=32 (8×2×2 meshblocks)
Ray:      CONCURRENCY=6 sliding window  (6 × 32 = 192 vCPUs)

KEY DIFFERENCE FROM TAG/Transonic campaigns:
  perturb_ampl = 1.0  (physical Mach 2–4)
  TAG used     = 1e-4  (linear regime only)

Sub-campaigns:
  CG  — Core Grid             480 sims  (5M × 4f × 4β × 2θ × 3seeds)
  NC  — Near-Critical Ext.    240 sims  (5M × 2f × 4β × θ=0 × 6seeds)
  SC  — Supercritical Ext.    240 sims  (5M × 2f × 4β × 2θ × 3seeds)
  PF  — Perpendicular Focus   240 sims  (5M × 4f × 4β × θ=90 × 3seeds)
  TOTAL: 1200 simulations

Author: ASTRA-PA — 2026-05-30
PI:     Glenn J. White (Open University)
"""

import os, sys, time, shutil, subprocess, json
from pathlib import Path
from datetime import datetime, timedelta
import numpy as np

# ── Campaign paths ────────────────────────────────────────────────────────
ATHENA_BIN  = "/home/fetch-agi/athena/bin/athena"
BASE_DIR    = Path("/data/rtc_campaign")
SIMS_DIR    = BASE_DIR / "sims"
RESULTS_DIR = BASE_DIR / "results"
FIGURES_DIR = RESULTS_DIR / "figures"
LOG_FILE    = BASE_DIR / "rtc_campaign.log"
PROGRESS_CSV = RESULTS_DIR / "RTC_results_progress.csv"
FINAL_CSV    = RESULTS_DIR / "RTC_results_all1200.csv"

# ── Physics constants ─────────────────────────────────────────────────────
FOUR_PI_G    = 39.4784176044
CS           = 1.0
W_CORE       = 0.3
NX1, NX2, NX3 = 512, 64, 64
LX1, LX2, LX3 = 16.0, 2.0, 2.0
DX1          = LX1 / NX1        # 0.03125 λJ/cell
DT_KILL      = 1.0e-6           # CFL watchdog → fragmentation
TLIM         = 2.0              # tJ
HDF5_DT      = 0.01             # tJ — fine temporal for peak tracking
HST_DT       = 0.001            # tJ
NP           = 32               # MPI ranks per simulation
MAX_CONC     = 6                # simultaneous sims (6 × 32 = 192 vCPUs)
WALL_TIME    = 7200             # 2 h per sim timeout
PERTURB_AMPL = 1.0              # 1.0 = physical regime; TAG used 1e-4

# ── Build simulation list ─────────────────────────────────────────────────
def build_sim_list():
    """Generate 1200-simulation parameter grid across 4 sub-campaigns."""
    sims = []

    mturb_all = [2.0, 2.5, 3.0, 3.5, 4.0]
    f_all     = [1.0, 1.2, 1.5, 2.0]
    beta_all  = [0.3, 0.5, 1.0, 2.0]

    def add(tag, f, beta, mturb, theta, seed):
        geom = "longitudinal" if theta == 0 else "perpendicular"
        fs = f"{f:.1f}".replace('.','p')
        bs = f"{beta:.1f}".replace('.','p')
        ms = f"{mturb:.1f}".replace('.','p')
        run_id = f"RTC_{tag}_f{fs}_b{bs}_m{ms}_t{theta}_s{seed}"
        sims.append({
            "run_id": run_id, "tag": tag,
            "f": f, "beta": beta, "mturb": mturb,
            "theta": theta, "seed": seed,
            "bfield_geometry": geom,
        })

    # CG: Core Grid — 480 sims
    for mturb in mturb_all:
        for f in f_all:
            for beta in beta_all:
                for theta in [0, 90]:
                    for seed in [1, 2, 3]:
                        add("CG", f, beta, mturb, theta, seed)

    # NC: Near-Critical Extension — 240 sims (6 seeds for f=1.0,1.2; θ=0)
    for mturb in mturb_all:
        for f in [1.0, 1.2]:
            for beta in beta_all:
                for seed in [1, 2, 3, 4, 5, 6]:
                    add("NC", f, beta, mturb, 0, seed)

    # SC: Supercritical Extension — 240 sims
    for mturb in mturb_all:
        for f in [1.5, 2.0]:
            for beta in beta_all:
                for theta in [0, 90]:
                    for seed in [1, 2, 3]:
                        add("SC", f, beta, mturb, theta, seed)

    # PF: Perpendicular Focus — 240 sims
    for mturb in mturb_all:
        for f in f_all:
            for beta in beta_all:
                for seed in [1, 2, 3]:
                    add("PF", f, beta, mturb, 90, seed)

    assert len(sims) == 1200, f"Expected 1200 sims, got {len(sims)}"
    return sims


# ── Per-simulation Ray task ───────────────────────────────────────────────
def run_one_sim(p: dict) -> dict:
    """
    Full pipeline for one Athena++ simulation.
    Runs inside a Ray worker process.
    Steps: generate input → run Athena++ → analyse → purge HDF5 → return results
    """
    import os, time, subprocess
    from pathlib import Path
    from datetime import datetime
    import numpy as np
    from scipy.signal import find_peaks
    from scipy.ndimage import gaussian_filter1d
    import h5py

    run_id  = p['run_id']
    run_dir = Path("/data/rtc_campaign/sims") / run_id
    run_dir.mkdir(parents=True, exist_ok=True)

    t0 = time.time()
    result = {k: p[k] for k in ['run_id','tag','f','beta','mturb','theta','seed']}
    result.update({
        "status": "unknown", "runtime_s": 0,
        "lW": None, "lW_status": "not_run",
        "t_frag": None, "morphology": "UNKNOWN",
        "tau_peak_max": 0.0, "tau_peak_mean": 0.0,
        "survives_0p1": False, "n_peaks_final": 0,
        "n_peak_events": 0, "peak_analysis_status": "not_run",
        "n_athdf_purged": 0,
    })

    try:
        # ── 1. Generate Athena++ input ────────────────────────────────────
        athinput_txt = f"""<comment>
problem   = RTC Physical Turbulence (Mach {p['mturb']})
run_id    = {run_id}

<job>
problem_id = {run_id}

<time>
cfl_number = 0.3
nlim       = -1
tlim       = 2.0

<mesh>
nx1        = 512
x1min      = 0.0
x1max      = 16.0
ix1_bc     = periodic
ox1_bc     = periodic

nx2        = 64
x2min      = -1.0
x2max      =  1.0
ix2_bc     = periodic
ox2_bc     = periodic

nx3        = 64
x3min      = -1.0
x3max      =  1.0
ix3_bc     = periodic
ox3_bc     = periodic

<meshblock>
nx1        = 64
nx2        = 32
nx3        = 32

<hydro>
iso_sound_speed = 1.0

<gravity>
grav_mean_rho = {p['f']:.6f}

<output1>
file_type  = hst
dt         = 0.001
id         = hst

<output2>
file_type  = hdf5
variable   = prim
dt         = 0.01
id         = prim

<problem>
four_pi_G       = 39.4784176044
f_line_mass     = {p['f']:.6f}
plasma_beta     = {p['beta']:.6f}
mach_number     = {p['mturb']:.6f}
perturb_ampl    = 1.000000
W_core          = 0.3
random_seed     = {p['seed']}
bfield_geometry = {p['bfield_geometry']}
theta_deg       = {float(p['theta']):.1f}
"""
        inp_path = run_dir / f"athinput.{run_id}"
        inp_path.write_text(athinput_txt)

        # ── 2. Run Athena++ with MPI ──────────────────────────────────────
        cmd = [
            "mpirun", "-n", "32",
            "/home/fetch-agi/athena/bin/athena",
            "-i", str(inp_path),
            "-d", str(run_dir),
        ]
        proc = subprocess.run(
            cmd, capture_output=True, text=True,
            cwd=str(run_dir), timeout=7200
        )
        runtime = time.time() - t0
        result["runtime_s"]  = runtime
        result["returncode"] = proc.returncode

        # Save logs (trimmed)
        (run_dir / "stdout.txt").write_text(
            proc.stdout[-4000:] if proc.stdout else "")
        (run_dir / "stderr.txt").write_text(
            proc.stderr[-2000:] if proc.stderr else "")

        # ── 3. Detect radial collapse from history file ───────────────────
        hst_files   = sorted(run_dir.glob("*.hst"))
        morphology  = "STABLE"
        t_frag      = None
        radial_collapse = False

        if hst_files:
            try:
                hst_data = np.loadtxt(str(hst_files[0]), comments='#')
                if hst_data.ndim >= 2 and hst_data.shape[1] >= 2:
                    t_col  = hst_data[:, 0]
                    dt_col = hst_data[:, 1]
                    mask   = dt_col < 1.0e-6
                    if mask.any():
                        radial_collapse = True
                        t_frag   = float(t_col[np.argmax(mask)])
                        morphology = "RADIAL_COLLAPSE"
            except Exception:
                pass

        # ── 4. Measure λ/W from .athdf snapshots ─────────────────────────
        DX = 16.0 / 512  # 0.03125 λJ/cell
        athdf_files = sorted(run_dir.glob(f"{run_id}.prim.*.athdf"))
        lW, lW_status = None, "no_athdf"

        if athdf_files and not radial_collapse:
            try:
                fn = athdf_files[-1]
                with h5py.File(str(fn), 'r') as hf:
                    prim = hf['prim'][:]
                    locs = hf['LogicalLocations'][:]
                    MBS  = hf.attrs['MeshBlockSize']
                    RGS  = hf.attrs['RootGridSize']

                rho_mb = prim[0]
                NXg = int(RGS[0]); NYg = int(RGS[1]); NZg = int(RGS[2])
                MBX = int(MBS[0]); MBY = int(MBS[1]); MBZ = int(MBS[2])
                rho_full = np.zeros((NZg, NYg, NXg), dtype=np.float32)
                for mb in range(locs.shape[0]):
                    il = int(locs[mb,0]); jl = int(locs[mb,1]); kl = int(locs[mb,2])
                    rho_full[kl*MBZ:(kl+1)*MBZ,
                             jl*MBY:(jl+1)*MBY,
                             il*MBX:(il+1)*MBX] = rho_mb[mb]

                col      = rho_full.mean(axis=(0,1)).astype(float)
                sigma    = max(4, NXg // 80)
                smoothed = gaussian_filter1d(col, sigma=sigma)
                med      = float(np.median(smoothed))
                min_dist = max(16, NXg // 24)

                peaks, _ = find_peaks(smoothed, height=1.3*med, distance=min_dist)
                if len(peaks) < 2:
                    peaks, _ = find_peaks(smoothed, height=1.1*med, distance=min_dist)

                if len(peaks) >= 2:
                    lam_lJ = float(np.median(np.diff(peaks))) * DX
                    lW     = lam_lJ / 0.3
                    lW_status = f"ok:{len(peaks)}_peaks"
                    morphology = "FULL" if len(peaks) >= 3 else "PARTIAL"
                    if t_frag is None:
                        try:
                            with h5py.File(str(fn), 'r') as hf:
                                t_frag = float(hf.attrs.get('Time', 2.0))
                        except Exception:
                            t_frag = 2.0
                else:
                    lW_status = f"too_few_peaks:{len(peaks)}"
            except Exception as ex:
                lW_status = f"lW_error:{ex}"

        result["lW"]       = lW
        result["lW_status"] = lW_status
        result["t_frag"]   = t_frag
        result["morphology"] = morphology

        # ── 5. Transient peak survival analysis ───────────────────────────
        #       (Referee Concern #1: do peaks survive ≥ 0.1 tJ ?)
        peak_res = {
            "tau_peak_max": 0.0, "tau_peak_mean": 0.0,
            "survives_0p1": False, "n_peaks_final": 0,
            "n_peak_events": 0, "peak_analysis_status": "insufficient",
        }
        if len(athdf_files) >= 5:
            try:
                profiles, times = [], []
                for fn in athdf_files:
                    with h5py.File(str(fn), 'r') as hf:
                        prim = hf['prim'][:]
                        locs = hf['LogicalLocations'][:]
                        MBS  = hf.attrs['MeshBlockSize']
                        RGS  = hf.attrs['RootGridSize']
                        t_val = float(hf.attrs.get('Time', len(profiles) * HDF5_DT))
                    rho_mb = prim[0]
                    NXg = int(RGS[0]); NYg = int(RGS[1]); NZg = int(RGS[2])
                    MBX = int(MBS[0]); MBY = int(MBS[1]); MBZ = int(MBS[2])
                    rho_full = np.zeros((NZg, NYg, NXg), dtype=np.float32)
                    for mb in range(locs.shape[0]):
                        il = int(locs[mb,0]); jl = int(locs[mb,1]); kl = int(locs[mb,2])
                        rho_full[kl*MBZ:(kl+1)*MBZ,
                                 jl*MBY:(jl+1)*MBY,
                                 il*MBX:(il+1)*MBX] = rho_mb[mb]
                    profiles.append(rho_full.mean(axis=(0,1)).astype(float))
                    times.append(t_val)

                # Sliding-window peak tracking
                active   = {}   # position_bin → t_formation
                finished = []
                sigma_p  = max(4, 512 // 80)
                min_d    = max(16, 512 // 24)
                MTOL     = 10   # peak match tolerance (cells)

                for col_i, t_i in zip(profiles, times):
                    sm  = gaussian_filter1d(col_i, sigma=sigma_p)
                    med = float(np.median(sm))
                    pks, _ = find_peaks(sm, height=1.3*med, distance=min_d)

                    matched = set()
                    for pk in pks:
                        best = min(active.keys(),
                                   key=lambda ap: abs(pk-ap),
                                   default=None)
                        if best is not None and abs(pk - best) <= MTOL:
                            matched.add(best)
                            t_form = active.pop(best)
                            active[pk] = t_form  # update position
                        else:
                            active[pk] = t_i     # new peak

                    for ap in list(active.keys()):
                        if ap not in matched and ap not in pks.tolist():
                            lt = t_i - active.pop(ap)
                            if lt > 0:
                                finished.append(lt)

                # Close still-active peaks
                t_end = times[-1] if times else TLIM
                for ap, t_form in active.items():
                    lt = t_end - t_form
                    if lt > 0:
                        finished.append(lt)

                # Peaks in final snapshot
                sm_last = gaussian_filter1d(profiles[-1], sigma=sigma_p)
                med_last = float(np.median(sm_last))
                pks_last, _ = find_peaks(sm_last, height=1.3*med_last, distance=min_d)

                peak_res = {
                    "tau_peak_max":  float(max(finished)) if finished else 0.0,
                    "tau_peak_mean": float(np.mean(finished)) if finished else 0.0,
                    "survives_0p1":  bool(max(finished) >= 0.1) if finished else False,
                    "n_peaks_final": int(len(pks_last)),
                    "n_peak_events": len(finished),
                    "peak_analysis_status": "ok",
                }
            except Exception as e:
                peak_res["peak_analysis_status"] = f"error:{e}"
        result.update(peak_res)

        # ── 6. Purge .athdf files to free disk ────────────────────────────
        n_purged = 0
        for athdf in run_dir.glob("*.athdf"):
            try:
                athdf.unlink()
                n_purged += 1
            except Exception:
                pass
        # Also purge .xdmf sidecar files
        for xdmf in run_dir.glob("*.xdmf"):
            try:
                xdmf.unlink()
            except Exception:
                pass
        result["n_athdf_purged"] = n_purged

        result["status"] = "completed" if proc.returncode == 0 else "failed"

    except subprocess.TimeoutExpired:
        result["status"]    = "timeout"
        result["runtime_s"] = time.time() - t0
    except Exception as e:
        result["status"]    = "error"
        result["error"]     = str(e)
        result["runtime_s"] = time.time() - t0

    tag_str = f"{result.get('tag','?')}  lW={result.get('lW') or '-':6}  " \
              f"τ_max={result.get('tau_peak_max',0):.3f}tJ  " \
              f"morph={result.get('morphology','?')}"
    print(f"[{datetime.now().strftime('%H:%M:%S')}] "
          f"{result['status'].upper():10s} {run_id[:50]}  "
          f"{tag_str}  {result.get('runtime_s',0)/60:.1f}min",
          flush=True)
    return result


# ── Disk usage check ──────────────────────────────────────────────────────
def disk_free_gb():
    usage = shutil.disk_usage("/data")
    return usage.free / 1e9


# ── Main orchestrator ─────────────────────────────────────────────────────
def main():
    import ray
    import pandas as pd

    t_start = time.time()

    # Create directories
    for d in [BASE_DIR, SIMS_DIR, RESULTS_DIR, FIGURES_DIR]:
        d.mkdir(parents=True, exist_ok=True)

    # Logging to file + stdout
    log_fh = open(str(LOG_FILE), 'a')
    def log(msg):
        ts = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        line = f"[{ts}] {msg}"
        print(line, flush=True)
        log_fh.write(line + "\n")
        log_fh.flush()

    log("=" * 72)
    log("Realistic Turbulence Campaign (RTC) — STARTING")
    log("=" * 72)
    log(f"Cluster:       34.143.130.135  (224 vCPU)")
    log(f"Concurrency:   {MAX_CONC} sims × {NP} MPI = {MAX_CONC*NP} vCPUs")
    log(f"Turbulence:    Mach 2.0–4.0  perturb_ampl=1.0  (PHYSICAL REGIME)")
    log(f"HDF5 dt:       {HDF5_DT} tJ  (200 snapshots/sim, purged after analysis)")
    log(f"Disk free:     {disk_free_gb():.0f} GB on /data")

    # Build full sim list
    all_sims = build_sim_list()
    log(f"Total sims:    {len(all_sims)} (CG=480 NC=240 SC=240 PF=240)")

    # Resume check
    if PROGRESS_CSV.exists():
        df_done   = pd.read_csv(str(PROGRESS_CSV))
        done_ids  = set(df_done['run_id'].values)
        remaining = [s for s in all_sims if s['run_id'] not in done_ids]
        results_df = df_done
        log(f"Resuming:      {len(done_ids)} done, {len(remaining)} remaining")
    else:
        remaining  = all_sims
        results_df = pd.DataFrame()
        log(f"Fresh start:   {len(remaining)} sims to run")

    if not remaining:
        log("All simulations already complete!")
        log_fh.close()
        return

    n_total = len(remaining)
    eta_h   = n_total * 45 / 60 / MAX_CONC   # assume 45 min/sim
    log(f"ETA (est.):    {eta_h:.0f}h ({eta_h/24:.1f} days)")
    log(f"Expected end:  ~{(datetime.now()+timedelta(hours=eta_h)).strftime('%Y-%m-%d %H:%M UTC')}")

    # Connect to Ray cluster (started externally with explicit address)
    ray_addr = os.environ.get("RAY_ADDRESS", "10.148.0.5:6379")
    log(f"Connecting to Ray cluster at {ray_addr}...")
    ray.init(address=ray_addr,
             ignore_reinit_error=True,
             runtime_env={"env_vars": {"OMP_NUM_THREADS": "1"}})
    resources = ray.cluster_resources()
    log(f"Ray cluster:   {resources.get('CPU',0):.0f} CPUs, "
        f"{resources.get('memory',0)/1e9:.0f} GB memory")

    # Wrap function as Ray remote
    run_remote = ray.remote(
        num_cpus=NP,
        memory=10_000_000_000   # 10 GB per task
    )(run_one_sim)

    # ── Sliding-window execution ──────────────────────────────────────────
    log(f"\nSubmitting {n_total} simulations (window={MAX_CONC})...\n")

    active_futures = []
    all_results    = []
    n_done         = 0
    runtimes_s     = []

    for i, p in enumerate(remaining):

        # Disk guard: if < 40 GB free, wait until sims finish and purge
        free = disk_free_gb()
        if free < 40:
            log(f"DISK GUARD: {free:.0f} GB free — pausing submissions...")
            while disk_free_gb() < 80:
                time.sleep(30)
            log(f"Disk recovered: {disk_free_gb():.0f} GB free — resuming")

        # Submit one task
        fut = run_remote.remote(p)
        active_futures.append(fut)

        # When window full (or last sim), drain one slot
        if len(active_futures) >= MAX_CONC or i == n_total - 1:
            # Collect ALL completed futures when on last batch
            drain_all = (i == n_total - 1)

            while active_futures:
                done, active_futures = ray.wait(active_futures, num_returns=1,
                                                timeout=8000)
                if not done:
                    log("WARNING: ray.wait timed out — some tasks may be slow")
                    break

                res = ray.get(done[0])
                all_results.append(res)
                n_done += 1
                if res.get('runtime_s'):
                    runtimes_s.append(res['runtime_s'])

                # Incremental save
                results_df = pd.concat(
                    [results_df, pd.DataFrame([res])], ignore_index=True
                )
                results_df.to_csv(str(PROGRESS_CSV), index=False)

                # Progress log
                avg_s   = float(np.mean(runtimes_s)) if runtimes_s else 2700
                eta_rem = (n_total - n_done) * avg_s / MAX_CONC
                log(
                    f"Progress {n_done:4d}/{n_total}  "
                    f"({100*n_done/n_total:5.1f}%)  "
                    f"avg={avg_s/60:.1f}min  ETA={eta_rem/3600:.1f}h  "
                    f"disk={disk_free_gb():.0f}GB  "
                    f"last: {res.get('morphology','?')} lW={res.get('lW') or '-'}"
                )

                # Exit inner loop to accept more submissions (unless draining last batch)
                if not drain_all and len(active_futures) < MAX_CONC:
                    break

    # ── Final save ────────────────────────────────────────────────────────
    results_df.to_csv(str(FINAL_CSV), index=False)
    total_wall = (time.time() - t_start) / 3600

    # ── Summary ───────────────────────────────────────────────────────────
    log("\n" + "=" * 72)
    log("CAMPAIGN COMPLETE")
    log("=" * 72)
    df = results_df

    log(f"Total simulations:  {len(df)}")
    for st in ['completed','failed','timeout','error']:
        n = len(df[df.get('status', pd.Series()) == st]) if 'status' in df.columns else 0
        log(f"  {st:12s}: {n}")
    log(f"Wall time:          {total_wall:.1f}h")

    if 'morphology' in df.columns:
        log("\nMorphology breakdown:")
        for morph, cnt in df['morphology'].value_counts().items():
            log(f"  {morph:22s}: {cnt}")

    if 'lW' in df.columns:
        lW_vals = pd.to_numeric(df['lW'], errors='coerce').dropna()
        if len(lW_vals) > 0:
            log(f"\nλ/W  (n={len(lW_vals)} measurable sims):")
            log(f"  mean ± σ = {lW_vals.mean():.3f} ± {lW_vals.std():.3f}")
            log(f"  median   = {lW_vals.median():.3f}")
            log(f"  range    = {lW_vals.min():.3f} – {lW_vals.max():.3f}")

    if 'survives_0p1' in df.columns:
        n_surv = int(df['survives_0p1'].sum())
        log(f"\nTransient peak survival (τ ≥ 0.1 tJ): {n_surv}/{len(df)}")

    log(f"\nResults: {FINAL_CSV}")
    log("=" * 72)

    ray.shutdown()
    log_fh.close()


if __name__ == "__main__":
    # Catch Ctrl+C gracefully
    import signal
    def _sigint(sig, frame):
        print("\nInterrupted. Progress saved.", flush=True)
        sys.exit(0)
    signal.signal(signal.SIGINT, _sigint)
    main()

# Also expose HDF5_DT for external reference
__all__ = ['build_sim_list', 'main']
