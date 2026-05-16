#!/usr/bin/env python3
"""
REFEREE RESPONSE CAMPAIGNS C8 & C12 — Parallel Runner
=======================================================
C8: Mixed Field Geometry λ/W Calibration  (175 sims) — CRITICAL
C12: Refined DTC with Extended Coverage   (300 sims) — MEDIUM

Runs C8 and C12 simultaneously, each in its own ThreadPoolExecutor,
splitting 224 CPUs as: C8→7 concurrent (112 CPUs), C12→7 concurrent (112 CPUs).
np=16 per simulation for both campaigns.

Binary: /home/fetch-agi/athena/bin/athena (filament_spacing_pr pgen)
Date: 2026-04-30
"""
import os, sys, json, re, subprocess, time, threading, shutil, glob
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path
from datetime import datetime, timezone
import numpy as np

# ── Athena++ binary ──────────────────────────────────────────────────────────
ATHENA_EXE   = "/home/fetch-agi/athena/bin/athena"
FOUR_PI_G    = 39.478417604357   # 4π² → λ_J=1, cs=1 in code units
W_CORE       = 0.3               # Filament Gaussian half-width (λ_J)
DT_FRAG      = 1.0e-8            # dt threshold for fragmentation detection

# ── Output directories ───────────────────────────────────────────────────────
BASE_DIR = Path("/data/peer_response_runs")
C8_DIR   = BASE_DIR / "C8"
C12_DIR  = BASE_DIR / "C12"
C10_DIR  = BASE_DIR / "C10"
for d in [C8_DIR, C12_DIR, C10_DIR]:
    d.mkdir(parents=True, exist_ok=True)

# ── Thread-safe logging ──────────────────────────────────────────────────────
log_lock    = threading.Lock()
c8_results  = []
c12_results = []
c8_rlock    = threading.Lock()
c12_rlock   = threading.Lock()

def utcnow():
    return datetime.now(timezone.utc).strftime("%H:%M:%S")

def log(msg, log_fh=None):
    line = f"[{utcnow()}] {msg}"
    with log_lock:
        print(line, flush=True)
        if log_fh:
            log_fh.write(line + "\n")
            log_fh.flush()

# ── Fragmentation detection ──────────────────────────────────────────────────
CYCLE_PAT = re.compile(r'time=([0-9.e+\-]+)\s+dt=([0-9.e+\-]+)')

def find_tfrag_hst(hst_path):
    """Read .hst file: return last time with dt >= DT_FRAG, or None."""
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
        return None
    except Exception:
        return None

def clean_hdf5_keep_last(sim_dir, keep=1):
    """Delete all .athdf files except the last keep snapshots."""
    files = sorted(sim_dir.glob("*.athdf"))
    for f in files[:-keep]:
        try:
            f.unlink()
        except Exception:
            pass
    # Also delete xdmf companions for deleted files
    for f in sim_dir.glob("*.athdf.xdmf"):
        base = str(f).replace(".xdmf", "")
        if not Path(base).exists():
            try:
                f.unlink()
            except Exception:
                pass

# ────────────────────────────────────────────────────────────────────────────
# ATHINPUT TEMPLATES
# ────────────────────────────────────────────────────────────────────────────

def make_athinput_c8(sid, f, beta, theta, seed, tlim=2.5):
    """
    C8: 512×64×64, 16λ_J × 1λ_J × 1λ_J, oblique B at theta_deg.
    Meshblock: 64×64×32 → 8×1×2=16 meshblocks → np=16.
    """
    # Use 'oblique' geometry for all angles (handles 0° and 90° correctly too)
    bgeom = 'oblique'
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
dt         = 0.20
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
mach_number     = 1.0
W_core          = {W_CORE}
perturb_ampl    = 0.0001
random_seed     = {seed}
bfield_geometry = {bgeom}
theta_deg       = {theta}
"""


def make_athinput_c12(sid, f, M, beta, seed, tlim=5.0):
    """
    C12: 256×64×64, 8λ_J × 1λ_J × 1λ_J, longitudinal B.
    Extended M range, β=0.3 focus. Corrected tlim=5.0 t_J.
    Meshblock: 32×32×32 → 8×2×2=32 meshblocks → np=16 (2 per rank).
    """
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
dt         = 0.25
id         = snap
variable   = prim

<mesh>
nx1 = 256
nx2 = 64
nx3 = 64
x1min = 0.0
x1max = 8.0
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
mach_number     = {M}
W_core          = {W_CORE}
perturb_ampl    = 0.0001
random_seed     = {seed}
bfield_geometry = longitudinal
theta_deg       = 0.0
"""


# ────────────────────────────────────────────────────────────────────────────
# CAMPAIGN 8: MIXED FIELD GEOMETRY
# ────────────────────────────────────────────────────────────────────────────

def build_c8_queue():
    F_VALS    = [1.5]
    BETA_VALS = [0.3, 0.5, 1.0, 1.5, 2.0]
    THETA_VALS = [0, 15, 30, 45, 60, 75, 90]
    SEEDS     = [42, 137, 314, 527, 816]

    queue = []
    for f in F_VALS:
        for beta in BETA_VALS:
            for theta in THETA_VALS:
                for seed in SEEDS:
                    fs = f"{f}".replace('.','p')
                    bs = f"{beta}".replace('.','p')
                    sid = f"C8_f{fs}_b{bs}_th{theta}_s{seed}"
                    rundir = C8_DIR / sid
                    athin  = make_athinput_c8(sid, f, beta, theta, seed)
                    queue.append({
                        'sim_id': sid, 'rundir': rundir, 'athinput': athin, 'np': 16,
                        'timeout_s': 7200,  # 2-hour hard limit (most fast, some oblique slower)
                        'params': {'f': f, 'beta': beta, 'theta': theta, 'seed': seed,
                                   'campaign': 'C8'}
                    })
    return queue


# ────────────────────────────────────────────────────────────────────────────
# CAMPAIGN 12: REFINED DTC
# ────────────────────────────────────────────────────────────────────────────

def build_c12_queue():
    F_VALS    = [1.2, 1.4, 1.6, 1.8, 2.0, 2.2]
    MACH_VALS = [0.5, 0.8, 1.0, 1.2, 1.5, 2.0, 2.5, 3.0, 4.0, 5.0]
    BETA_VALS = [0.3]   # Focus β=0.3 where DTC artifacts occurred
    SEEDS     = [42, 137, 314, 527, 816]

    queue = []
    for f in F_VALS:
        for M in MACH_VALS:
            for beta in BETA_VALS:
                for seed in SEEDS:
                    fs = f"{f}".replace('.','p')
                    ms = f"{M}".replace('.','p')
                    bs = f"{beta}".replace('.','p')
                    sid = f"C12_f{fs}_M{ms}_b{bs}_s{seed}"
                    rundir = C12_DIR / sid
                    athin  = make_athinput_c12(sid, f, M, beta, seed)
                    queue.append({
                        'sim_id': sid, 'rundir': rundir, 'athinput': athin, 'np': 16,
                        'timeout_s': 21600,  # 6-hour corrected timeout (per spec)
                        'params': {'f': f, 'M': M, 'beta': beta, 'seed': seed,
                                   'campaign': 'C12'}
                    })
    return queue


# ────────────────────────────────────────────────────────────────────────────
# SIMULATION RUNNER
# ────────────────────────────────────────────────────────────────────────────

def run_sim(cfg, log_fh, results_list, results_lock, results_file):
    """Run a single Athena++ sim. Returns result dict."""
    sid      = cfg['sim_id']
    rundir   = Path(cfg['rundir'])
    athinput = cfg['athinput']
    np_sim   = cfg['np']
    timeout  = cfg.get('timeout_s', 7200)

    rundir.mkdir(parents=True, exist_ok=True)
    (rundir / "athinput").write_text(athinput)

    # Skip if already done
    hst_list = list(rundir.glob("*.hst"))
    if hst_list:
        tf = find_tfrag_hst(str(hst_list[0]))
        if tf is not None:
            log(f"SKIP {sid}  (already done, t_frag={tf:.4f})", log_fh)
            res = {'id': sid, **cfg.get('params', {}),
                   'outcome': 'FRAG', 't_frag': tf, 'skipped': True, 'wall_s': 0}
            with results_lock:
                results_list.append(res)
                with open(results_file, 'w') as fh:
                    json.dump(results_list, fh, indent=2)
            return res

    cmd = ["mpirun", "-np", str(np_sim),
           ATHENA_EXE, "-i", str(rundir / "athinput"), "-d", str(rundir)]
    t0       = time.time()
    outcome  = "TIMEOUT"
    t_frag   = None
    last_dt  = 1.0
    last_t   = 0.0
    stdout_lines = []

    try:
        proc = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                                cwd=str(rundir), text=True, bufsize=1)
        for line in proc.stdout:
            stdout_lines.append(line)
            m = CYCLE_PAT.search(line)
            if m:
                sim_t  = float(m.group(1))
                dt_v   = float(m.group(2))
                last_dt = dt_v
                last_t  = sim_t
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
        hst_list = list(rundir.glob("*.hst"))
        if hst_list:
            tf2 = find_tfrag_hst(str(hst_list[0]))
            if tf2 is not None and outcome != "TIMEOUT":
                outcome = "FRAG"
                t_frag  = tf2

    # Save stdout
    (rundir / "stdout.txt").write_text("".join(stdout_lines[-2000:]))

    # Clean HDF5: keep only last snapshot for λ/W analysis
    clean_hdf5_keep_last(rundir, keep=1)

    tf_str = f"{t_frag:.4f}" if t_frag is not None else "N/A"
    log(f"{outcome:8s} {sid}  t_frag={tf_str}  last_dt={last_dt:.2e}  last_t={last_t:.3f}  wall={wall:.0f}s",
        log_fh)

    res = {'id': sid, **cfg.get('params', {}),
           'outcome': outcome, 't_frag': t_frag, 'wall_s': wall}

    with results_lock:
        results_list.append(res)
        with open(results_file, 'w') as fh:
            json.dump(results_list, fh, indent=2)
    return res


# ────────────────────────────────────────────────────────────────────────────
# λ/W ANALYSIS (post-campaign)
# ────────────────────────────────────────────────────────────────────────────

def analyse_lambda_W(campaign_dir, results, campaign_name, output_file):
    """Extract λ/W from final HDF5 snapshots. Returns list of result dicts."""
    try:
        import h5py
        from scipy.signal import find_peaks
    except ImportError:
        log(f"h5py/scipy not available — skipping λ/W analysis")
        return []

    lw_results = []
    W_CORE_LJ  = 0.3  # Filament FWHM in λ_J units

    for res in results:
        if res.get('outcome') != 'FRAG':
            lw_results.append({**res, 'lambda_W': None, 'quality': 'NOT_FRAG'})
            continue

        sid    = res['id']
        simdir = campaign_dir / sid
        athdf_files = sorted(simdir.glob("*.athdf"))
        if not athdf_files:
            lw_results.append({**res, 'lambda_W': None, 'quality': 'NO_HDF5'})
            continue

        # Use last (post-fragmentation) snapshot
        hdf5_path = athdf_files[-1]
        try:
            with h5py.File(hdf5_path, 'r') as hf:
                rho = np.array(hf['prim'][0])   # IDN=0
                x1v = np.array(hf['x1v'])
        except Exception as e:
            log(f"  λ/W ERROR {sid}: {e}")
            lw_results.append({**res, 'lambda_W': None, 'quality': 'HDF5_ERROR'})
            continue

        # Column density along filament axis (x1)
        sigma = np.sum(rho, axis=(0, 1))   # shape: (nx1,)
        rho_max = sigma.max()
        sigma_norm = sigma / rho_max

        dx = (x1v[-1] - x1v[0]) / (len(x1v) - 1)
        Lx = x1v[-1] - x1v[0]

        # Derivative to detect beading
        drho = sigma_norm - sigma_norm.mean()

        # Find peaks
        min_spacing = max(5, int(0.3 / dx))
        peaks, props = find_peaks(drho,
                                  height=0.05 * sigma_norm.max(),
                                  distance=min_spacing,
                                  prominence=0.03 * sigma_norm.max())
        n_peaks = len(peaks)

        if n_peaks < 2:
            lw_results.append({**res, 'lambda_W': None, 'n_peaks': n_peaks,
                               'quality': 'FLAT_PROFILE'})
            continue

        spacings_lJ = np.diff(peaks) * dx
        lambda_frag = float(np.median(spacings_lJ))
        lw          = round(lambda_frag / W_CORE_LJ, 3)
        lw_std      = round(float(np.std(spacings_lJ)) / W_CORE_LJ, 3)

        quality = 'GOOD' if n_peaks >= 4 and 0.3 < lambda_frag < Lx / 2 else 'MARGINAL'

        lw_results.append({**res,
                           'lambda_W':     lw,
                           'lambda_W_std': lw_std,
                           'n_peaks':      n_peaks,
                           'lambda_frag':  round(lambda_frag, 4),
                           'quality':      quality})

    # Summary
    good = [r for r in lw_results if r.get('quality') in ('GOOD', 'MARGINAL') and r.get('lambda_W')]
    if good:
        lw_vals = [r['lambda_W'] for r in good]
        log(f"{campaign_name} λ/W: {np.mean(lw_vals):.3f} ± {np.std(lw_vals):.3f} "
            f"(N_good={len(good)}/{len(lw_results)})")

    with open(output_file, 'w') as fh:
        json.dump(lw_results, fh, indent=2)
    return lw_results


# ────────────────────────────────────────────────────────────────────────────
# CAMPAIGN 10: L/3 CONVERGENCE (Pure Python, no Athena++)
# ────────────────────────────────────────────────────────────────────────────

def run_c10_analysis():
    """C10: L/3 convergence test — pure statistical analysis."""
    log("=" * 60)
    log("CAMPAIGN 10: L/3 Convergence Test (pure analysis)")
    log("=" * 60)

    HGBS_REGIONS = {
        'Taurus':    {'L': 8.5,  'N': 536},
        'OrionB':    {'L': 12.0, 'N': 1844},
        'Aquila':    {'L': 10.0, 'N': 749},
        'Perseus':   {'L': 9.0,  'N': 816},
        'Ophiuchus': {'L': 6.0,  'N': 513},
        'Serpens':   {'L': 7.0,  'N': 194},
        'TMC1':      {'L': 5.0,  'N': 178},
        'CRA':       {'L': 6.0,  'N': 239},
    }

    BEADING_SPACING = 0.3  # pc
    SEEDS = [42, 137, 314]

    results = {'periodic_beading': [], 'random_uniform': [], 'bias_stats': {}}

    biases_pairwise = []
    biases_nn       = []

    for region, info in HGBS_REGIONS.items():
        L = info['L']
        N = info['N']

        for seed in SEEDS:
            np.random.seed(seed)

            # ── Periodic beading ──
            n_cores  = int(L / BEADING_SPACING)
            pos      = np.arange(n_cores) * BEADING_SPACING
            pos     += np.random.uniform(-0.05 * BEADING_SPACING,
                                          0.05 * BEADING_SPACING, n_cores)
            pos      = np.clip(pos, 0, L)

            # Pairwise median
            dists_all = [abs(pos[j] - pos[i]) for i in range(len(pos))
                         for j in range(i + 1, len(pos))]
            pm  = float(np.median(dists_all))
            nn  = float(np.median(np.diff(np.sort(pos))))
            bias_pm = (pm  - BEADING_SPACING) / BEADING_SPACING
            bias_nn = (nn  - BEADING_SPACING) / BEADING_SPACING

            biases_pairwise.append(bias_pm)
            biases_nn.append(bias_nn)

            results['periodic_beading'].append({
                'region': region, 'seed': seed, 'L': L, 'N_cores': n_cores,
                'true_spacing': BEADING_SPACING,
                'pairwise_median': round(pm, 4),
                'nn_median':       round(nn, 4),
                'bias_pairwise':   round(bias_pm, 4),
                'bias_nn':         round(bias_nn, 4),
            })

            # ── Random uniform ──
            np.random.seed(seed + 1000)
            pos_rand = np.sort(np.random.uniform(0, L, N))
            pm_r = float(np.median([abs(pos_rand[j] - pos_rand[i])
                                    for i in range(min(N, 200))
                                    for j in range(i + 1, min(N, 200))]))
            nn_r = float(np.median(np.diff(pos_rand)))

            results['random_uniform'].append({
                'region': region, 'seed': seed, 'L': L, 'N_cores': N,
                'pairwise_median': round(pm_r, 4),
                'nn_median':       round(nn_r, 4),
                'L_over_3':        round(L / 3.0, 4),
            })

    results['bias_stats'] = {
        'pairwise_mean': round(float(np.mean(biases_pairwise)), 4),
        'pairwise_std':  round(float(np.std(biases_pairwise)), 4),
        'nn_mean':       round(float(np.mean(biases_nn)), 4),
        'nn_std':        round(float(np.std(biases_nn)), 4),
    }

    log(f"C10 BIAS STATS:")
    log(f"  Pairwise median bias: {results['bias_stats']['pairwise_mean']:.4f} "
        f"± {results['bias_stats']['pairwise_std']:.4f}")
    log(f"  NN spacing bias:      {results['bias_stats']['nn_mean']:.4f} "
        f"± {results['bias_stats']['nn_std']:.4f}")

    out_file = C10_DIR / "C10_results.json"
    with open(out_file, 'w') as fh:
        json.dump(results, fh, indent=2)
    log(f"C10 results saved: {out_file}")
    return results


# ────────────────────────────────────────────────────────────────────────────
# MAIN
# ────────────────────────────────────────────────────────────────────────────

def run_campaign(queue, results_list, results_lock, results_file, log_path,
                 max_workers, label):
    """Run a campaign queue with a ThreadPoolExecutor."""
    with open(log_path, 'w') as log_fh:
        log(f"{'='*60}", log_fh)
        log(f"CAMPAIGN {label}: {len(queue)} simulations, {max_workers} concurrent", log_fh)
        log(f"{'='*60}", log_fh)

        n_done = 0
        t_start = time.time()

        with ThreadPoolExecutor(max_workers=max_workers) as pool:
            futures = {pool.submit(run_sim, cfg, log_fh,
                                   results_list, results_lock, results_file): cfg
                       for cfg in queue}
            for fut in as_completed(futures):
                n_done += 1
                cfg = futures[fut]
                try:
                    res = fut.result()
                except Exception as e:
                    log(f"EXCEPTION {cfg['sim_id']}: {e}", log_fh)
                elapsed = time.time() - t_start
                rate    = n_done / (elapsed / 3600)
                eta_hr  = (len(queue) - n_done) / rate if rate > 0 else 99
                log(f"  [{label}] {n_done}/{len(queue)} done | "
                    f"rate={rate:.1f} sim/hr | ETA={eta_hr:.1f}h", log_fh)

        log(f"Campaign {label} COMPLETE", log_fh)

    return results_list


def main():
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument('--campaign', choices=['C8','C12','C10','ALL'], default='ALL')
    parser.add_argument('--max-conc-c8',  type=int, default=7)
    parser.add_argument('--max-conc-c12', type=int, default=7)
    args = parser.parse_args()

    t_global_start = time.time()

    log("=" * 70)
    log("REFEREE RESPONSE CAMPAIGNS C8 + C12 — START")
    log(f"CPUs available: {os.cpu_count()}")
    log(f"C8  concurrent: {args.max_conc_c8}  ({args.max_conc_c8 * 16} CPUs)")
    log(f"C12 concurrent: {args.max_conc_c12} ({args.max_conc_c12 * 16} CPUs)")
    log("=" * 70)

    # ── C10 always runs first (fast, no Athena++) ──
    if args.campaign in ('C10', 'ALL'):
        run_c10_analysis()

    # ── Build queues ──
    c8_queue  = build_c8_queue()  if args.campaign in ('C8',  'ALL') else []
    c12_queue = build_c12_queue() if args.campaign in ('C12', 'ALL') else []

    log(f"C8  queue: {len(c8_queue)} sims")
    log(f"C12 queue: {len(c12_queue)} sims")

    c8_results_file  = C8_DIR  / "results.json"
    c12_results_file = C12_DIR / "results.json"
    c8_log_path  = C8_DIR  / "campaign.log"
    c12_log_path = C12_DIR / "campaign.log"

    # ── Run C8 and C12 simultaneously in threads ──
    threads = []
    if c8_queue:
        t8 = threading.Thread(
            target=run_campaign,
            args=(c8_queue, c8_results, c8_rlock, c8_results_file,
                  c8_log_path, args.max_conc_c8, 'C8'),
            daemon=False)
        threads.append(t8)

    if c12_queue:
        t12 = threading.Thread(
            target=run_campaign,
            args=(c12_queue, c12_results, c12_rlock, c12_results_file,
                  c12_log_path, args.max_conc_c12, 'C12'),
            daemon=False)
        threads.append(t12)

    for t in threads:
        t.start()
    for t in threads:
        t.join()

    # ── Post-campaign λ/W analysis ──
    log("=" * 70)
    log("POST-CAMPAIGN λ/W ANALYSIS")
    log("=" * 70)

    if c8_results:
        frags_c8 = [r for r in c8_results if r.get('outcome') == 'FRAG']
        log(f"C8: {len(frags_c8)}/{len(c8_results)} FRAG — running λ/W analysis...")
        lw_c8 = analyse_lambda_W(C8_DIR, c8_results, 'C8',
                                  C8_DIR / "lambda_W_analysis.json")

    if c12_results:
        frags_c12 = [r for r in c12_results if r.get('outcome') == 'FRAG']
        log(f"C12: {len(frags_c12)}/{len(c12_results)} FRAG — running λ/W analysis...")
        lw_c12 = analyse_lambda_W(C12_DIR, c12_results, 'C12',
                                   C12_DIR / "lambda_W_analysis.json")

    # ── Final summary ──
    wall_total = (time.time() - t_global_start) / 3600
    log("=" * 70)
    log(f"ALL CAMPAIGNS COMPLETE — total wall time: {wall_total:.2f} hr")
    if c8_results:
        n8_frag = sum(1 for r in c8_results if r.get('outcome') == 'FRAG')
        n8_to   = sum(1 for r in c8_results if r.get('outcome') == 'TIMEOUT')
        log(f"C8:  {n8_frag} FRAG | {n8_to} TIMEOUT | {len(c8_results)} total")
    if c12_results:
        n12_frag = sum(1 for r in c12_results if r.get('outcome') == 'FRAG')
        n12_to   = sum(1 for r in c12_results if r.get('outcome') == 'TIMEOUT')
        log(f"C12: {n12_frag} FRAG | {n12_to} TIMEOUT | {len(c12_results)} total")
    log("=" * 70)

    # Save master summary
    summary = {
        'date': datetime.now(timezone.utc).isoformat(),
        'wall_hours': round(wall_total, 2),
        'C8':  {'n_sims': len(c8_results),
                'n_frag': sum(1 for r in c8_results if r.get('outcome') == 'FRAG'),
                'n_timeout': sum(1 for r in c8_results if r.get('outcome') == 'TIMEOUT')},
        'C12': {'n_sims': len(c12_results),
                'n_frag': sum(1 for r in c12_results if r.get('outcome') == 'FRAG'),
                'n_timeout': sum(1 for r in c12_results if r.get('outcome') == 'TIMEOUT')},
    }
    with open(BASE_DIR / "MASTER_SUMMARY.json", 'w') as fh:
        json.dump(summary, fh, indent=2)


if __name__ == "__main__":
    main()
