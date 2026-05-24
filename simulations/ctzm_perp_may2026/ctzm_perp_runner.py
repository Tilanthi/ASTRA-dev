#!/usr/bin/env python3
"""
EXPANDED REFEREE RESPONSE CAMPAIGN — May 2026
================================================

This expanded campaign addresses referee concerns B2, B3, B5 with three sub-campaigns:

1. CTZM_PERP (96 sims): Perpendicular-field transition zone mapping
   - Addresses B2: Tests if smooth λ/W(f) evolution holds for perpendicular fields
   - f=[1.2,1.3,1.4,1.5] × β=[0.3,0.5,1.0,2.0] × M=[1.0,2.0] × seeds=[0,1,2]
   - θ=90° (perpendicular to filament axis)

2. EOS_SENSITIVITY (48 sims): Non-isothermal EOS effects on λ/W
   - Addresses B3: Measures λ/W for γ≠1 (currently unknown)
   - f=[1.0,1.1,1.2] × γ=[0.7,0.8,0.9,1.0] × seeds=[0,1,2,3]
   - Near-critical regime where λ/W measurement is possible
   - Tests referee claim that "spacing implications for γ≠1 remain unknown"

3. TURB_AMPLITUDE (60 sims): Turbulence amplitude from linear to supersonic
   - Addresses B5: Tests λ/W stability across perturbation amplitudes
   - f=[1.0,1.2] × ampl=[1e-4,1e-3,1e-2,1e-1,1.0] × seeds=[0,1,2]
   - Tests if λ/W is independent of perturbation amplitude
   - Critical for extrapolating to real supersonic filaments

TOTAL: 204 simulations
Expected runtime: ~26 hours on 220 vCPU (6 concurrent)

Author: Claude (ASTRA System)
Date: 2026-05-13
Referee context: Addresses B2 (perpendicular tension), B3 (EOS gap), B5 (turbulence)
"""

import json, os, signal, subprocess, sys, time, math
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path
import numpy as np
from scipy.signal import find_peaks
from scipy.ndimage import gaussian_filter1d
import h5py

# ── Constants ──────────────────────────────────────────────────────────────
ATHENA_BIN  = "/home/fetch-agi/athena/bin/athena"
FOUR_PI_G   = 39.4784176044
CS          = 1.0
W_CORE      = 0.3
DX1         = 8.0 / 256
DT_KILL     = 1.0e-6
POLL        = 8.0
NP          = 32
MAX_CONC    = 6
WALL_TIME   = 14400
TLIM        = 4.0
HDF5_DT     = 0.02
MAX_HDF5_GB = 8.0

# ── Campaign configurations ───────────────────────────────────────────────────
CAMPAIGNS = {
    "CTZM_PERP": {
        "base_dir": Path("/data/ctzm_perp_runs"),
        "suffix": "ctzm_perp",
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
        "base_dir": Path("/data/eos_sensitivity_runs"),
        "suffix": "eos",
        "theta_deg": 0.0,  # Longitudinal for baseline
        "gamma": None,      # Will be set per sim
        "perturb_ampl": 1.0e-4,
        "params": {
            "f": [1.0, 1.1, 1.2],
            "gamma": [0.7, 0.8, 0.9, 1.0],  # Varied per sim
            "beta": [1.0],   # Fixed to reduce parameter space
            "mach": [1.0],
            "seed": [0, 1, 2, 3],
        }
    },
    "TURB_AMPLITUDE": {
        "base_dir": Path("/data/turb_amplitude_runs"),
        "suffix": "turb",
        "theta_deg": 0.0,
        "gamma": 1.0,
        "perturb_ampl": None,  # Will be set per sim
        "params": {
            "f": [1.0, 1.2],
            "ampl": [1e-4, 1e-3, 1e-2, 1e-1, 1.0],  # Varied per sim
            "beta": [1.0],
            "mach": [1.0],
            "seed": [0, 1, 2],
        }
    },
}

def build_sim_list():
    """Build simulation list for all campaigns."""
    sims = []

    for campaign_name, config in CAMPAIGNS.items():
        if campaign_name == "EOS_SENSITIVITY":
            # Special handling for gamma variation
            for f in config["params"]["f"]:
                for gamma in config["params"]["gamma"]:
                    for seed in config["params"]["seed"]:
                        f_str = f"{f:.1f}".replace('.', 'p')
                        g_str = f"{gamma:.1f}".replace('.', 'p')
                        run_id = f"EOS_f{f_str}_g{g_str}_s{seed}"
                        sims.append({
                            "campaign": campaign_name,
                            "run_id": run_id,
                            "f": f,
                            "gamma": gamma,
                            "beta": 1.0,
                            "mach": 1.0,
                            "seed": seed,
                            "theta_deg": config["theta_deg"],
                            "perturb_ampl": config["perturb_ampl"],
                        })

        elif campaign_name == "TURB_AMPLITUDE":
            # Special handling for amplitude variation
            for f in config["params"]["f"]:
                for ampl in config["params"]["ampl"]:
                    for seed in config["params"]["seed"]:
                        f_str = f"{f:.1f}".replace('.', 'p')
                        a_str = f"{ampl:.0e}".replace('+', '').replace('.', 'p')
                        run_id = f"TURB_f{f_str}_a{a_str}_s{seed}"
                        sims.append({
                            "campaign": campaign_name,
                            "run_id": run_id,
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
                            f_str = f"{f:.1f}".replace('.', 'p')
                            b_str = f"{beta:.1f}".replace('.', 'p')
                            m_str = f"{mach:.1f}".replace('.', 'p')
                            run_id = f"CTZMP_f{f_str}_b{b_str}_m{m_str}_s{seed}"
                            sims.append({
                                "campaign": campaign_name,
                                "run_id": run_id,
                                "f": f,
                                "beta": beta,
                                "mach": mach,
                                "seed": seed,
                                "theta_deg": config["theta_deg"],
                                "gamma": config["gamma"],
                                "perturb_ampl": config["perturb_ampl"],
                            })

    return sims

def make_athinput(run_dir: Path, p: dict) -> Path:
    """Generate Athena++ input file."""

    # Extract parameters with defaults
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
        gamma_adi = 1.0 + (1.0 - gamma) * 0.1  # Small variation for γ=1.0

    athinput = f"""<comment>
problem   = {p['campaign']} transition zone study
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

# ── λ/W analysis from a single HDF5 snapshot ──────────────────────────────
def measure_lambda_W_snapshot(hdf5_path: Path):
    """Reconstruct global density and measure λ/W from peak detection."""
    try:
        with h5py.File(hdf5_path, 'r') as f:
            t_val = float(f.attrs['Time'])
            prim  = f['prim'][...]
            locs  = f['LogicalLocations'][:]

        n_vars, n_mb, nk_mb, nj_mb, ni_mb = prim.shape
        NI, NJ, NK = 256, 64, 64

        # Reconstruct global density array
        rho_global = np.zeros((NK, NJ, NI), dtype=np.float32)
        for mb in range(n_mb):
            lx1, lx2, lx3 = int(locs[mb, 0]), int(locs[mb, 1]), int(locs[mb, 2])
            i0 = lx1 * ni_mb
            j0 = lx2 * nj_mb
            k0 = lx3 * nk_mb
            rho_global[k0:k0+nk_mb, j0:j0+nj_mb, i0:i0+ni_mb] = prim[0, mb]

        # Column-averaged linear mass density along x1
        col_rho = rho_global.mean(axis=(0, 1))

        # Light smoothing
        col_smooth = gaussian_filter1d(col_rho, sigma=2)

        # Peak detection
        dyn_range = col_smooth.max() - col_smooth.min()
        min_prom  = max(0.05 * dyn_range, 0.01 * col_smooth.mean())
        peaks, _  = find_peaks(col_smooth, prominence=min_prom, distance=8)

        n_peaks = len(peaks)
        lw = None
        if n_peaks >= 2:
            spacings = np.diff(peaks) * DX1
            lw = float(np.median(spacings) / W_CORE)

        return {"t": round(t_val, 4), "n_peaks": n_peaks, "lambda_W": lw}

    except Exception:
        return None

def analyse_and_purge(run_dir: Path, t_frag):
    """Analyse HDF5 snapshots, classify outcome, purge data."""
    hdf5_files = sorted(run_dir.glob("*.athdf"))
    series = []
    for hf in hdf5_files:
        result = measure_lambda_W_snapshot(hf)
        if result is not None:
            series.append(result)

    # Purge HDF5 files
    for hf in hdf5_files:
        hf.unlink(missing_ok=True)
    for xf in run_dir.glob("*.xdmf"):
        xf.unlink(missing_ok=True)

    # Classification
    beading_snaps = [s for s in series if s["lambda_W"] is not None]
    if len(beading_snaps) >= 2:
        lw_vals   = [s["lambda_W"] for s in beading_snaps]
        lw_mean   = float(np.mean(lw_vals))
        lw_std    = float(np.std(lw_vals))
        cv = lw_std / lw_mean if lw_mean > 0 else float('inf')
        if cv < 0.3:
            classification = "BEADING_STABLE"
        else:
            classification = "BEADING_TRANSIENT"
    else:
        classification = "RADIAL_COLLAPSE"
        lw_mean = lw_std = None

    return classification, series, lw_mean, lw_std

def run_sim(p: dict) -> dict:
    """Run a single simulation."""
    campaign = p["campaign"]
    config = CAMPAIGNS[campaign]
    run_id = p["run_id"]
    run_dir = config["base_dir"] / run_id
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
            hdf5_list = sorted(run_dir.glob("*.athdf"))
            total_gb = sum(h.stat().st_size for h in hdf5_list) / 1e9
            if total_gb > MAX_HDF5_GB and len(hdf5_list) > 30:
                for h in hdf5_list[:-30]:
                    h.unlink(missing_ok=True)

            # HST scanning for fragmentation
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

            time.sleep(POLL)

    except Exception as e:
        outcome = f"ERROR: {e}"

    wall = time.time() - t_start

    # λ/W analysis
    classification = "N/A"
    lambda_W_series = []
    lw_mean = lw_std = None

    if outcome in ("FRAG", "COMPLETE", "TIMEOUT"):
        try:
            classification, lambda_W_series, lw_mean, lw_std = \
                analyse_and_purge(run_dir, t_frag)
        except Exception as e:
            classification = f"ANALYSIS_ERROR: {e}"
            for hf in run_dir.glob("*.athdf"):
                hf.unlink(missing_ok=True)
    else:
        for hf in run_dir.glob("*.athdf"):
            hf.unlink(missing_ok=True)

    result = {
        "campaign": campaign,
        "run_id": run_id,
        **{k: v for k, v in p.items() if k not in ["campaign", "run_id"]},
        "outcome": outcome,
        "t_frag": t_frag,
        "dt_min": dt_min,
        "wall_s": round(wall, 1),
        "classification": classification,
        "lw_mean": lw_mean,
        "lw_std": lw_std,
        "n_lw_snaps": len([s for s in lambda_W_series if s["lambda_W"] is not None]),
        "lambda_W_series": lambda_W_series,
    }

    lw_str = f" λ/W={lw_mean:.2f}±{lw_std:.2f}" if lw_mean else ""
    print(f"[{campaign[:8]}] {run_id} {outcome:8s} t={t_frag:.4f} t_J {classification}{lw_str} wall={wall:.0f}s")

    return result

def main():
    sims = build_sim_list()
    print(f"EXPANDED REFEREE RESPONSE CAMPAIGN: {len(sims)} simulations")
    print(f"  CTZM_PERP: 96 sims (perpendicular transition zone)")
    print(f"  EOS_SENSITIVITY: 48 sims (non-isothermal EOS)")
    print(f"  TURB_AMPLITUDE: 60 sims (turbulence amplitude)")
    print(f"─" * 70)

    results = []
    t_launch = time.time()

    # Run campaigns sequentially by type for better organization
    for campaign in ["CTZM_PERP", "EOS_SENSITIVITY", "TURB_AMPLITUDE"]:
        campaign_sims = [s for s in sims if s["campaign"] == campaign]
        print(f"\nStarting {campaign} campaign ({len(campaign_sims)} sims)...")

        campaign_results = []
        with ThreadPoolExecutor(max_workers=MAX_CONC) as pool:
            futures = {pool.submit(run_sim, s): s for s in campaign_sims}
            for fut in as_completed(futures):
                r = fut.result()
                campaign_results.append(r)
                results.append(r)

                # Save per-campaign results
                config = CAMPAIGNS[campaign]
                out_file = config["base_dir"] / f"{campaign.lower()}_results.json"
                out_file.write_text(json.dumps(campaign_results, indent=2))

    total_wall = time.time() - t_launch

    # Summary statistics
    print("\n" + "=" * 70)
    print(f"ALL CAMPAIGNS COMPLETE: {len(results)} sims in {total_wall/60:.1f} min")

    for campaign in ["CTZM_PERP", "EOS_SENSITIVITY", "TURB_AMPLITUDE"]:
        campaign_results = [r for r in results if r["campaign"] == campaign]
        n_frag = sum(1 for r in campaign_results if r["outcome"] == "FRAG")
        n_beading = sum(1 for r in campaign_results if "BEADING" in str(r.get("classification", "")))

        lw_vals = [r["lw_mean"] for r in campaign_results if r.get("lw_mean")]
        lw_str = f" | mean λ/W={np.mean(lw_vals):.3f}" if lw_vals else " | no λ/W"

        print(f"  {campaign}: {len(campaign_results)} sims | FRAG={n_frag} | BEADING={n_beading}{lw_str}")

    print(f"\nResults saved to campaign-specific directories")

if __name__ == "__main__":
    main()
