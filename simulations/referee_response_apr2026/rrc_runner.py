#!/usr/bin/env python3
"""
REFEREE RESPONSE CAMPAIGNS — Complete Runner
C5: Turbulence λ/W Measurements    (54 sims)  — Highest Priority
C6: Perpendicular-B β-Dependence   (100 sims) — High Priority
C7: Critical Transition Mapping    (135 sims) — Medium Priority

Runs C5 → C6 → C7 sequentially with full λ/W analysis after each.
Binary: /home/fetch-agi/athena/bin/athena (filament_spacing_pr pgen)
Date: 2026-04-30
"""
import os, sys, json, re, subprocess, time, threading, shutil, glob
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path
from datetime import datetime, timezone
import numpy as np

# ── Athena++ binary ─────────────────────────────────────────────────────
ATHENA_EXE   = "/home/fetch-agi/athena/bin/athena"
FOUR_PI_G    = 39.478417604357   # 4π² → λ_J=1, cs=1 in code units
W_CORE       = 0.3               # Filament Gaussian half-width (λ_J)
DT_FRAG      = 1.0e-8            # dt threshold for fragmentation detection
MACH         = 1.0               # Background Mach number (quiescent)

# ── Output directory ────────────────────────────────────────────────────
BASE_DIR     = Path("/data/referee_response_runs")
BASE_DIR.mkdir(parents=True, exist_ok=True)

log_lock = threading.Lock()
_results  = []
_rlock    = threading.Lock()

# ────────────────────────────────────────────────────────────────────────
def utcnow():
    return datetime.now(timezone.utc).strftime("%H:%M:%S")

def log(msg, log_fh=None):
    line = f"[{utcnow()}] {msg}"
    with log_lock:
        print(line, flush=True)
        if log_fh:
            log_fh.write(line + "\n")
            log_fh.flush()

def find_tfrag_hst(hst_path):
    """Read .hst file: return last time with dt >= DT_FRAG, or None."""
    try:
        with open(hst_path) as f:
            lines = [l for l in f if not l.startswith('#') and l.strip()]
        t_last = None
        for line in reversed(lines):
            p = line.split()
            if len(p) >= 2:
                try:
                    if float(p[1]) >= DT_FRAG:
                        return float(p[0])
                    t_last = float(p[0])
                except ValueError:
                    continue
        return t_last
    except Exception:
        return None

CYCLE_PAT = re.compile(r'time=([0-9.e+\-]+)\s+dt=([0-9.e+\-]+)')

def run_sim(cfg, log_fh, results_file):
    """Run a single Athena++ sim. Returns result dict."""
    sid      = cfg['sim_id']
    rundir   = cfg['rundir']
    athinput = cfg['athinput']
    np_sim   = cfg['np']
    timeout  = cfg.get('timeout_s', 14400)  # 4-hour hard limit

    rundir.mkdir(parents=True, exist_ok=True)

    # Write athinput file
    (rundir / "athinput").write_text(athinput)

    # Skip if already done
    hst_pat = list(rundir.glob("*.hst"))
    if hst_pat:
        tf = find_tfrag_hst(str(hst_pat[0]))
        if tf is not None:
            log(f"SKIP {sid}  (already done, t={tf:.4f})", log_fh)
            return {'id': sid, **cfg.get('params', {}),
                    'outcome': 'FRAG', 't_frag': tf, 'skipped': True, 'wall_s': 0}

    cmd = ["mpirun", "-np", str(np_sim),
           ATHENA_EXE, "-i", str(rundir / "athinput"), "-d", str(rundir)]
    t0       = time.time()
    outcome  = "TIMEOUT"
    t_frag   = None
    last_dt  = 1.0
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
                proc.kill()
                outcome = "TIMEOUT"
                break
        proc.wait(timeout=30)
    except Exception as e:
        outcome = "FAILED"
        log(f"FAILED  {sid}  error={e}", log_fh)

    wall = time.time() - t0

    # HST fallback
    if outcome != "FRAG":
        hst_pat = list(rundir.glob("*.hst"))
        if hst_pat:
            tf2 = find_tfrag_hst(str(hst_pat[0]))
            if tf2 is not None and outcome == "TIMEOUT":
                pass  # Ran to tlim → STABLE/TIMEOUT
            elif tf2 is not None:
                outcome = "FRAG"
                t_frag  = tf2

    # Write stdout
    (rundir / "stdout.txt").write_text("".join(stdout_lines))

    tf_str = f"{t_frag:.4f}" if t_frag else "N/A"
    log(f"{outcome:8s} {sid}  t={tf_str}  dt={last_dt:.2e}  wall={wall:.0f}s", log_fh)

    res = {'id': sid, **cfg.get('params', {}),
           'outcome': outcome, 't_frag': t_frag, 'wall_s': wall}

    with _rlock:
        _results.append(res)
        with open(results_file, 'w') as fh:
            json.dump(_results, fh, indent=2)
    return res

def clean_hdf5(campaign_dir, keep_last_n=5):
    """Delete all .athdf HDF5 files except the last N snapshots per sim dir."""
    cleaned_bytes = 0
    for sim_dir in campaign_dir.iterdir():
        if not sim_dir.is_dir():
            continue
        athdf_files = sorted(sim_dir.glob("*.athdf"))
        to_delete = athdf_files[:-keep_last_n] if len(athdf_files) > keep_last_n else []
        for f in to_delete:
            try:
                cleaned_bytes += f.stat().st_size
                f.unlink()
            except Exception:
                pass
    gb = cleaned_bytes / 1e9
    return gb

# ────────────────────────────────────────────────────────────────────────
# ATHINPUT TEMPLATES
# ────────────────────────────────────────────────────────────────────────

def make_athinput_std(sid, f, beta, perturb_ampl, seed, bgeom, theta,
                     nx1=256, nx2=64, nx3=64,
                     bx1min=-4.0, bx1max=4.0, x2half=1.0, tlim=2.5):
    """Standard 256×64×64 athinput (C5 and C7 format)."""
    return f"""<job>
problem_id = {sid}

<time>
cfl_number = 0.3
nlim       = -1
tlim       = {tlim}

<output1>
file_type  = hst
dt         = 0.01
id         = hst

<output2>
file_type  = hdf5
dt         = 0.05
id         = snap
variable   = prim

<mesh>
nx1 = {nx1}
nx2 = {nx2}
nx3 = {nx3}
x1min = {bx1min}
x1max = {bx1max}
x2min = {-x2half}
x2max = {x2half}
x3min = {-x2half}
x3max = {x2half}
ix1_bc = periodic
ox1_bc = periodic
ix2_bc = periodic
ox2_bc = periodic
ix3_bc = periodic
ox3_bc = periodic

<meshblock>
nx1 = 32
nx2 = 32
nx3 = 32

<hydro>
iso_sound_speed = 1.0

<gravity>
grav_mean_rho = {max(float(f), 1.0):.6f}

<problem>
four_pi_G       = {FOUR_PI_G}
f_line_mass     = {f}
plasma_beta     = {beta}
mach_number     = {MACH}
W_core          = {W_CORE}
perturb_ampl    = {perturb_ampl}
random_seed     = {seed}
bfield_geometry = {bgeom}
theta_deg       = {theta}
"""

def make_athinput_c6(sid, f, beta, seed, tlim=2.5):
    """C6: 512×64×64, 16λ_J × 1λ_J × 1λ_J, perpendicular B."""
    return f"""<job>
problem_id = {sid}

<time>
cfl_number = 0.3
nlim       = -1
tlim       = {tlim}

<output1>
file_type  = hst
dt         = 0.01
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
grav_mean_rho = {max(float(f), 1.0):.6f}

<problem>
four_pi_G       = {FOUR_PI_G}
f_line_mass     = {f}
plasma_beta     = {beta}
mach_number     = {MACH}
W_core          = {W_CORE}
perturb_ampl    = 0.0001
random_seed     = {seed}
bfield_geometry = perpendicular
theta_deg       = 90.0
"""

# ────────────────────────────────────────────────────────────────────────
# CAMPAIGN 5: TURBULENCE λ/W MEASUREMENTS
# ────────────────────────────────────────────────────────────────────────
def build_c5_queue(base):
    F_VALS      = [1.0, 1.1, 1.2]
    BETA_VALS   = [0.5, 1.0, 2.0]
    TURB_TYPES  = [('turbphys', 1.0), ('turbsynth', 0.0001)]
    SEEDS       = [42, 137, 314]
    queue = []
    for f in F_VALS:
        for beta in BETA_VALS:
            for tname, tampl in TURB_TYPES:
                for seed in SEEDS:
                    fs = f"{f}".replace('.','p')
                    bs = f"{beta}".replace('.','p')
                    sid = f"C5_f{fs}_b{bs}_{tname}_s{seed}"
                    rundir = base / sid
                    athin = make_athinput_std(sid, f, beta, tampl, seed,
                                             'longitudinal', 0.0,
                                             nx1=256, nx2=64, nx3=64,
                                             bx1min=0.0, bx1max=8.0, x2half=1.0)
                    queue.append({
                        'sim_id': sid, 'rundir': rundir, 'athinput': athin, 'np': 16,
                        'params': {'f': f, 'beta': beta, 'turb_type': tname,
                                   'turb_ampl': tampl, 'seed': seed, 'campaign': 'C5'}
                    })
    return queue

# ────────────────────────────────────────────────────────────────────────
# CAMPAIGN 6: PERPENDICULAR-B β-DEPENDENCE
# ────────────────────────────────────────────────────────────────────────
def build_c6_queue(base):
    F_VALS    = [1.2, 1.3, 1.4, 1.5]
    BETA_VALS = [0.3, 0.5, 1.0, 1.5, 2.0]
    SEEDS     = [42, 137, 314, 527, 816]
    queue = []
    for f in F_VALS:
        for beta in BETA_VALS:
            for seed in SEEDS:
                fs = f"{f}".replace('.','p')
                bs = f"{beta}".replace('.','p')
                sid = f"C6_f{fs}_b{bs}_s{seed}"
                rundir = base / sid
                athin = make_athinput_c6(sid, f, beta, seed)
                queue.append({
                    'sim_id': sid, 'rundir': rundir, 'athinput': athin, 'np': 16,
                    'params': {'f': f, 'beta': beta, 'seed': seed, 'campaign': 'C6'}
                })
    return queue

# ────────────────────────────────────────────────────────────────────────
# CAMPAIGN 7: CRITICAL TRANSITION MAPPING
# ────────────────────────────────────────────────────────────────────────
def build_c7_queue(base):
    F_VALS    = [0.9, 0.95, 1.0, 1.05, 1.1, 1.15, 1.2, 1.25, 1.3]
    BETA_VALS = [0.3, 0.5, 1.0, 1.5, 2.0]
    SEEDS     = [42, 137, 314]
    queue = []
    for f in F_VALS:
        for beta in BETA_VALS:
            for seed in SEEDS:
                fs = f"{f}".replace('.','p')
                bs = f"{beta}".replace('.','p')
                sid = f"C7_f{fs}_b{bs}_s{seed}"
                rundir = base / sid
                athin = make_athinput_std(sid, f, beta, 0.0001, seed,
                                         'longitudinal', 0.0,
                                         nx1=256, nx2=64, nx3=64,
                                         bx1min=0.0, bx1max=8.0, x2half=1.0)
                queue.append({
                    'sim_id': sid, 'rundir': rundir, 'athinput': athin, 'np': 16,
                    'params': {'f': f, 'beta': beta, 'seed': seed, 'campaign': 'C7'}
                })
    return queue

# ────────────────────────────────────────────────────────────────────────
# RUN CAMPAIGN
# ────────────────────────────────────────────────────────────────────────
def run_campaign(cname, queue, max_conc, results_file, log_file):
    global _results
    _results = []

    # Load existing results for skip logic
    if results_file.exists():
        try:
            with open(results_file) as fh:
                _results = json.load(fh)
        except Exception:
            _results = []

    done_ids = {r['id'] for r in _results}
    pending  = [c for c in queue if c['sim_id'] not in done_ids]

    with open(log_file, 'a') as lfh:
        log(f"{'='*60}", lfh)
        log(f"{cname}: {len(queue)} sims total, {len(pending)} pending | "
            f"np=16 | max_conc={max_conc}", lfh)
        log(f"{'='*60}", lfh)

        t0 = time.time()
        with ThreadPoolExecutor(max_workers=max_conc) as ex:
            futs = {ex.submit(run_sim, cfg, lfh, results_file): cfg for cfg in pending}
            for fut in as_completed(futs):
                try:
                    fut.result()
                except Exception as e:
                    log(f"Thread error: {e}", lfh)

        n_frag    = sum(1 for r in _results if r.get('outcome') == 'FRAG')
        n_timeout = sum(1 for r in _results if r.get('outcome') == 'TIMEOUT')
        n_fail    = sum(1 for r in _results if r.get('outcome') == 'FAILED')
        wall      = time.time() - t0
        log(f"DONE {cname}  FRAG={n_frag}  STABLE/TIMEOUT={n_timeout}  "
            f"FAILED={n_fail}  wall={wall/3600:.2f}h", lfh)

    return _results

# ────────────────────────────────────────────────────────────────────────
# λ/W ANALYSIS
# ────────────────────────────────────────────────────────────────────────
def analyse_lambda_W(campaign_dir, results, campaign_name, output_file):
    """
    Extract λ/W from HDF5 snapshots.
    Uses the last-but-one snapshot (fragmentation epoch).
    Returns list of dicts with lambda_W measurements.
    """
    try:
        import h5py
        from scipy.signal import find_peaks
    except ImportError:
        return []

    lw_results = []

    for res in results:
        if res.get('outcome') != 'FRAG':
            continue
        sid = res['id']
        rundir = campaign_dir / sid

        # Find HDF5 snapshots
        athdf_files = sorted(rundir.glob("*.snap.*.athdf"))
        if not athdf_files:
            # Try .athdf directly
            athdf_files = sorted(rundir.glob("*.athdf"))

        if len(athdf_files) < 1:
            lw_results.append({**res, 'lambda_W': None, 'n_peaks': 0,
                                'quality': 'NO_SNAPSHOT'})
            continue

        # Use last available snapshot (fragmentation epoch)
        snap = athdf_files[-1]

        try:
            # Multi-block Athena++ HDF5: prim shape = (nvars, n_blocks, nz, ny, nx)
            with h5py.File(str(snap), 'r') as hf:
                if 'prim' not in hf and 'cons' not in hf:
                    lw_results.append({**res, 'lambda_W': None, 'n_peaks': 0,
                                        'quality': 'NO_DENSITY'})
                    continue
                prim_key = 'prim' if 'prim' in hf else 'cons'
                prim     = hf[prim_key][:]           # (nvars, n_blocks, nz, ny, nx)
                x1v_blk  = hf['x1v'][:]              # (n_blocks, nx_per_block)
                logloc   = hf['LogicalLocations'][:]  # (n_blocks, 3)

            rho_all  = prim[0]         # density: (n_blocks, nz, ny, nx)
            n_blocks = rho_all.shape[0]

            # Group blocks by ix1 logical index (unique per x1 column)
            ix_map = {}
            for b in range(n_blocks):
                ix     = int(logloc[b, 0])
                rho_yz = rho_all[b].mean(axis=(0, 1))  # (nx_block,)
                x1_b   = x1v_blk[b]
                if ix not in ix_map:
                    ix_map[ix] = {'rho_sum': np.zeros(len(x1_b)), 'n': 0, 'x1': x1_b}
                ix_map[ix]['rho_sum'] += rho_yz
                ix_map[ix]['n'] += 1

            # Concatenate in ix order → 1-D axial profile
            ix_sorted = sorted(ix_map.keys())
            x1    = np.concatenate([ix_map[ix]['x1'] for ix in ix_sorted])
            rho_x = np.concatenate([ix_map[ix]['rho_sum'] / ix_map[ix]['n']
                                     for ix in ix_sorted])

            nx = len(x1)
            dx = float(x1[1] - x1[0]) if nx > 1 else 1.0
            Lx = float(x1[-1] - x1[0]) + dx

        except Exception as e:
            lw_results.append({**res, 'lambda_W': None, 'n_peaks': 0,
                                'quality': f'HDF5_ERROR: {e}'})
            continue

        # Subtract background (mean density)
        rho_bg = rho_x.min()
        drho   = rho_x - rho_bg
        rho_max = drho.max()

        if rho_max < 0.05:
            lw_results.append({**res, 'lambda_W': None, 'n_peaks': 0,
                                'quality': 'FLAT_PROFILE'})
            continue

        # Find peaks
        min_spacing = max(5, int(0.3 / dx))  # 0.3 λ_J in cells
        peaks, props = find_peaks(drho, height=0.1*rho_max,
                                   distance=min_spacing, prominence=0.05*rho_max)
        n_peaks = len(peaks)

        if n_peaks < 2:
            lw_results.append({**res, 'lambda_W': None, 'n_peaks': n_peaks,
                                'quality': 'FEW_PEAKS'})
            continue

        # Compute inter-peak spacings
        spacings_px = np.diff(peaks)
        spacings_lJ = spacings_px * dx  # in λ_J units
        lambda_frag = float(np.median(spacings_lJ))
        lambda_frag_std = float(np.std(spacings_lJ))

        # λ/W ratio
        W = W_CORE  # 0.3 λ_J
        lw  = lambda_frag / W
        lw_std = lambda_frag_std / W

        # Quality flag
        if n_peaks >= 4 and lambda_frag > 0.3 and lambda_frag < Lx/2:
            quality = 'GOOD'
        elif n_peaks >= 2:
            quality = 'FEW_PEAKS'
        elif lambda_frag < 0.2:
            quality = 'SPURIOUS'
        else:
            quality = 'MARGINAL'

        snap_t = None
        # Try to read time from HDF5 attributes
        try:
            with h5py.File(str(snap), 'r') as hf:
                if 'Time' in hf.attrs:
                    snap_t = float(hf.attrs['Time'])
        except Exception:
            pass

        lw_results.append({
            **res,
            'lambda_frag_lJ':  round(lambda_frag, 4),
            'lambda_frag_std': round(lambda_frag_std, 4),
            'lambda_W':        round(lw, 3),
            'lambda_W_std':    round(lw_std, 3),
            'n_peaks':         n_peaks,
            'quality':         quality,
            'snap_file':       str(snap.name),
            'snap_t':          snap_t,
        })

    # Save analysis
    with open(output_file, 'w') as fh:
        json.dump(lw_results, fh, indent=2)

    # Print summary
    good = [r for r in lw_results if r.get('quality') == 'GOOD']
    print(f"\n=== λ/W Analysis {campaign_name} ===")
    print(f"Total analysed: {len(lw_results)}, GOOD: {len(good)}")
    if good:
        lw_vals = [r['lambda_W'] for r in good]
        print(f"λ/W (GOOD):  mean={np.mean(lw_vals):.3f} ± {np.std(lw_vals):.3f}")
        print(f"             range=[{min(lw_vals):.3f}, {max(lw_vals):.3f}]")
    return lw_results

# ────────────────────────────────────────────────────────────────────────
# MAIN
# ────────────────────────────────────────────────────────────────────────
def main():
    import argparse
    p = argparse.ArgumentParser()
    p.add_argument('--campaign', choices=['C5','C6','C7','ALL'], default='ALL')
    p.add_argument('--max-conc-c5', type=int, default=14)
    p.add_argument('--max-conc-c6', type=int, default=12)
    p.add_argument('--max-conc-c7', type=int, default=14)
    args = p.parse_args()

    campaigns = []
    if args.campaign in ('C5', 'ALL'):
        campaigns.append(('C5', build_c5_queue, args.max_conc_c5))
    if args.campaign in ('C6', 'ALL'):
        campaigns.append(('C6', build_c6_queue, args.max_conc_c6))
    if args.campaign in ('C7', 'ALL'):
        campaigns.append(('C7', build_c7_queue, args.max_conc_c7))

    for cname, build_fn, max_conc in campaigns:
        cdir         = BASE_DIR / cname
        cdir.mkdir(exist_ok=True)
        log_file     = cdir / "campaign.log"
        results_file = cdir / "results.json"
        analysis_out = cdir / "lambda_W_analysis.json"

        queue   = build_fn(cdir)
        results = run_campaign(cname, queue, max_conc, results_file, log_file)

        # Clean HDF5: keep last 5 snapshots per sim
        print(f"\n[{utcnow()}] Cleaning HDF5 for {cname}...")
        gb_freed = clean_hdf5(cdir, keep_last_n=5)
        print(f"[{utcnow()}] Freed {gb_freed:.2f} GB from {cname}")

        # λ/W analysis
        print(f"[{utcnow()}] Running λ/W analysis for {cname}...")
        lw = analyse_lambda_W(cdir, results, cname, analysis_out)
        print(f"[{utcnow()}] Analysis saved to {analysis_out}")

    print(f"\n[{utcnow()}] ALL CAMPAIGNS COMPLETE")

if __name__ == '__main__':
    main()
