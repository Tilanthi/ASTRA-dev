#!/usr/bin/env python3
"""
analyse_option_b_v2.py — Field Geometry Campaign Analysis (v2)
===============================================================
Reads the LATEST VALID HDF5 snapshot from each (theta, beta) simulation
and measures:
  1. Density contrast C = rho_max / rho_mean  (collapse indicator)
  2. Dominant fragmentation wavelength lambda_dom via power spectrum
  3. Number of gravitational cores (connected regions above threshold)
  4. Mean core separation (measured lambda)
  5. Ratio lambda_meas / lambda_MJ(theta, beta)   [the key test]

v2 changes vs v1:
  - Fallback to penultimate snapshot if latest HDF5 is corrupt (killed mid-write)
  - Scan all existing directories, not just those listed in status JSON
  - Include sims from both option_b_status.json and option_b_missing_status.json

Theoretical prediction under test:
  lambda_MJ(theta, beta) = lambda_J * sqrt(1 + 2*sin^2(theta) / beta)
  where lambda_J = 1.0  [code units, cs=1, 4piG=4pi^2, rho0=1]

Output: /home/fetch-agi/analysis_b/option_b_analysis_v2.json
        /home/fetch-agi/analysis_b/option_b_report_v2.md

Authors: Glenn J. White (Open University)
         ASTRA multi-agent system — 2026-04-19
"""

import json, os, re
from pathlib import Path
import numpy as np
from scipy import ndimage
import h5py

# ── Configuration ─────────────────────────────────────────────────────────────
RUN_DIR     = Path("/home/fetch-agi/option_b_runs")
OUT_DIR     = Path("/home/fetch-agi/analysis_b")
JSON_OUT    = OUT_DIR / "option_b_analysis_v2.json"
REPORT_OUT  = OUT_DIR / "option_b_report_v2.md"

L           = 8.0      # domain side in lambda_J
NX          = 128      # cells per dimension

THETAS = [0, 30, 45, 60, 75, 90]
BETAS  = [0.5, 0.75, 1.0, 1.5, 2.0]

# Core detection parameters
THRESHOLD_FACTOR = 2.5   # rho > factor * rho_mean
SMOOTH_SIGMA     = 1.5   # Gaussian smoothing (cells)

# ── Physics ───────────────────────────────────────────────────────────────────

def lambda_mj_theory(theta_deg, beta):
    t = np.radians(theta_deg)
    return np.sqrt(1.0 + 2.0 * np.sin(t)**2 / beta)

def growth_rate_theory(theta_deg, beta, k):
    """Linear growth rate gamma(k) for given angle and beta."""
    t = np.radians(theta_deg)
    four_pi_G = 4.0 * np.pi**2
    g2 = four_pi_G - k**2 * (1.0 + 2.0 * np.sin(t)**2 / beta)
    return np.sqrt(np.maximum(g2, 0.0))

# ── HDF5 helpers ─────────────────────────────────────────────────────────────

def try_open_hdf5(path):
    """Return (t, rho) if file is valid, or raise on corruption/error."""
    with h5py.File(path, 'r') as f:
        t    = float(f.attrs['Time'])
        prim = np.array(f['prim'], dtype=np.float32)
        locs = np.array(f['LogicalLocations'])
    nvars, nblocks, nz, ny, nx = prim.shape
    max_lx = int(locs[:,0].max()) + 1
    max_ly = int(locs[:,1].max()) + 1
    max_lz = int(locs[:,2].max()) + 1
    full = np.zeros((max_lz*nz, max_ly*ny, max_lx*nx), dtype=np.float32)
    for b in range(nblocks):
        lx, ly, lz = int(locs[b,0]), int(locs[b,1]), int(locs[b,2])
        full[lz*nz:(lz+1)*nz, ly*ny:(ly+1)*ny, lx*nx:(lx+1)*nx] = prim[0, b]
    return t, full

def assemble_density(run_dir, name):
    """
    Try snapshots from newest to oldest until one opens cleanly.
    Returns (t, rho, snap_name, is_penultimate).
    Raises RuntimeError if none can be opened.
    """
    snaps = sorted(run_dir.glob(f"{name}.prim.*.athdf"))
    if not snaps:
        raise RuntimeError("no snapshots found")

    errors = []
    for snap in reversed(snaps):  # newest first
        try:
            t, rho = try_open_hdf5(snap)
            is_pen = (snap != snaps[-1])  # True if we fell back
            return t, rho, snap.name, is_pen
        except Exception as e:
            errors.append(f"{snap.name}: {e}")
            continue

    raise RuntimeError("all snapshots corrupt: " + "; ".join(errors[-3:]))

# ── Analysis ──────────────────────────────────────────────────────────────────

def measure_power_spectrum_1d(rho, axis=0):
    """1D power spectrum along given axis (averaged over the other two)."""
    n = rho.shape[axis]
    dk = 2.0 * np.pi / L
    k_vals = np.fft.rfftfreq(n, d=1.0/n) * dk
    axes = [0, 1, 2]
    axes.remove(axis)
    power = np.zeros(len(k_vals))
    for i in range(rho.shape[axes[0]]):
        for j in range(rho.shape[axes[1]]):
            if axis == 0:
                sl = rho[:, i, j]
            elif axis == 1:
                sl = rho[i, :, j]
            else:
                sl = rho[i, j, :]
            ft = np.abs(np.fft.rfft(sl))**2
            power += ft
    power /= (rho.shape[axes[0]] * rho.shape[axes[1]])
    return k_vals, power

def find_cores(rho, threshold_factor=2.5, smooth_sigma=1.5):
    """Detect gravitational cores via connected-component labelling."""
    rho_mean = float(rho.mean())
    threshold = rho_mean * threshold_factor
    rho_smooth = ndimage.gaussian_filter(rho.astype(np.float64), sigma=smooth_sigma)
    above = rho_smooth > threshold
    labeled, n_labels = ndimage.label(above)
    cores = []
    dx = L / rho.shape[0]
    for lbl in range(1, n_labels + 1):
        mask = labeled == lbl
        indices = np.array(np.where(mask)).T
        weights = rho[mask]
        com = np.average(indices, axis=0, weights=weights)
        pos = com * dx
        cores.append({
            'position': pos.tolist(),
            'peak_rho': float(rho[mask].max()),
            'n_cells':  int(mask.sum()),
        })
    return cores, rho_mean

def core_separations_1d(cores, axis=2, L=8.0):
    """Mean nearest-neighbour separation along fragmentation axis (x1)."""
    if len(cores) < 2:
        return [], 0.0
    positions = np.array([c['position'][axis] for c in cores])
    positions.sort()
    gaps = []
    n = len(positions)
    for i in range(n):
        d = positions[(i+1) % n] - positions[i]
        if d < 0:
            d += L
        gaps.append(d)
    return gaps, float(np.mean(gaps))

def analyse_sim(name, theta_deg, beta, run_dir):
    """Full analysis for one (theta, beta) simulation."""
    try:
        t, rho, snap_name, used_penultimate = assemble_density(run_dir, name)
    except RuntimeError as e:
        return {'error': str(e)}

    rho_mean = float(rho.mean())
    rho_max  = float(rho.max())
    C        = rho_max / rho_mean

    # 1D power spectrum along x1 (HDF5 layout: z,y,x → axis 2 is x1)
    k_vals, power = measure_power_spectrum_1d(rho, axis=2)
    if len(k_vals) > 1:
        k_dom_idx = np.argmax(power[1:]) + 1
        k_dom     = float(k_vals[k_dom_idx])
        lam_dom   = 2.0 * np.pi / k_dom if k_dom > 0 else L
    else:
        k_dom, lam_dom = 0.0, L

    cores, _ = find_cores(rho, THRESHOLD_FACTOR, SMOOTH_SIGMA)
    gaps, mean_sep = core_separations_1d(cores, axis=2, L=L)

    lmj_th   = lambda_mj_theory(theta_deg, beta)
    k_mj     = 2.0 * np.pi / lmj_th
    gamma_mj = growth_rate_theory(theta_deg, beta, k_mj)
    gamma_0  = np.sqrt(4.0 * np.pi**2)

    ratio_dom  = lam_dom  / lmj_th if lmj_th > 0 else None
    ratio_sep  = mean_sep / lmj_th if (mean_sep > 0 and lmj_th > 0) else None

    return {
        'snapshot':          snap_name,
        'used_penultimate':  used_penultimate,
        't_final':           float(t),
        'rho_mean':          rho_mean,
        'rho_max':           rho_max,
        'C_final':           C,
        'lam_dom':           lam_dom,
        'k_dom':             k_dom,
        'n_cores':           len(cores),
        'mean_sep':          mean_sep,
        'sep_gaps':          gaps[:20],
        'lmj_theory':        lmj_th,
        'k_mj_theory':       k_mj,
        'gamma_mj':          gamma_mj,
        'gamma_0':           gamma_0,
        'ratio_dom_vs_lmj':  ratio_dom,
        'ratio_sep_vs_lmj':  ratio_sep,
    }

# ── Report ────────────────────────────────────────────────────────────────────

def write_report(results):
    # Collect valid entries for fit
    valid = [(r['theta_deg'], r['beta'], r['ratio_sep_vs_lmj'], r['n_cores'])
             for r in results.values()
             if 'error' not in r and r.get('n_cores', 0) >= 4
                and r.get('ratio_sep_vs_lmj') is not None
                and r.get('theta_deg', 0) != 0]   # exclude θ=0 box-scale artifact

    lines = [
        "# Option B: Intermediate B-Field Geometry — Analysis Report (v2)",
        "",
        f"**Campaign:** 30 simulations at 128³, L=8 λ_J, M=3, t_lim=15",
        f"**Test:**     λ_frag(θ,β) = f × λ_MJ(θ,β) = f × λ_J √(1 + 2sin²θ/β)",
        f"**Date:**     2026-04-19 | astra-climate (224 vCPU)",
        "",
        "---",
        "",
        "## Key Results Table",
        "",
        "| θ (°) | β    | λ_MJ | λ_sep | C_final | N_cores | λ_sep/λ_MJ | Note |",
        "|-------|------|------|-------|---------|---------|-----------|------|",
    ]

    for th in THETAS:
        for beta in BETAS:
            name = f"FG_t{th:02d}_b{int(beta*100):03d}"
            r = results.get(name, {})
            if 'error' in r:
                err = r['error'][:30]
                lines.append(f"| {th:5d} | {beta:.2f} | — | — | — | — | — | {err} |")
                continue
            if not r:
                lines.append(f"| {th:5d} | {beta:.2f} | — | — | — | — | — | not analysed |")
                continue
            lmj   = r.get('lmj_theory', 0)
            lsep  = r.get('mean_sep', 0)
            C     = r.get('C_final', 0)
            nc    = r.get('n_cores', 0)
            ratio = r.get('ratio_sep_vs_lmj', None)
            ratio_s = f"{ratio:.3f}" if ratio else "—"
            pen   = " ‡" if r.get('used_penultimate') else ""
            note  = "θ=0° box-scale" if th == 0 else ("")
            note  = note + pen
            lines.append(f"| {th:5d} | {beta:.2f} | {lmj:.3f} | {lsep:.3f} | "
                         f"{C:.3f} | {nc:7d} | {ratio_s:9s} | {note} |")

    lines += ["", "‡ = penultimate snapshot used (latest was corrupt)", ""]

    # Fit summary
    if valid:
        ratios = [v[2] for v in valid]
        mean_r = np.mean(ratios)
        std_r  = np.std(ratios)
        lines += [
            "---",
            "",
            "## Calibration Result",
            "",
            f"Excluding θ=0° (box-scale artifact) and N_cores < 4:",
            f"- Valid data points: **{len(valid)}**",
            f"- Mean λ_frag / λ_MJ(θ,β) = **{mean_r:.3f} ± {std_r:.3f}**",
            "",
            "### Individual valid entries:",
            "",
            "| θ (°) | β    | λ_MJ | λ_sep | N_cores | Ratio |",
            "|-------|------|------|-------|---------|-------|",
        ]
        for th, beta, ratio, nc in sorted(valid):
            lmj = lambda_mj_theory(th, beta)
            lsep = ratio * lmj
            lines.append(f"| {th:5d} | {beta:.2f} | {lmj:.3f} | {lsep:.3f} | {nc:7d} | {ratio:.3f} |")

        lines += [
            "",
            f"**Conclusion:** λ_frag = ({mean_r:.2f} ± {std_r:.2f}) × λ_MJ(θ,β)",
        ]
        if abs(mean_r - 1.0) < 0.15:
            lines.append("This is consistent with the theoretical prediction λ_frag ≈ λ_MJ to within ~15%.")

    lines += [
        "",
        "---",
        "",
        "## Caveats",
        "",
        "### θ=0° Box-Scale Artifact",
        "At θ=0° (B ∥ filament), the magnetic Jeans wavelength equals the thermal Jeans length:",
        "λ_MJ(0°,β) = λ_J = 1.0 for all β (since sin²0°=0).",
        "The growth rate at k=2π/λ_J is γ=0 (marginally stable seed mode).",
        "The fastest-growing mode is the box-scale k=2π/L (n=1), so the simulation",
        "produces a single large condensation rather than λ_J-spaced cores.",
        "θ=0° data excluded from the calibration.",
        "",
        "### dt-Death Spiral",
        "Isothermal MHD without sink particles: as cores collapse ρ→∞, dt→0.",
        "Simulations are killed when dt-spiral is detected. Analysis uses last valid snapshot.",
        "Simulations with N_cores<4 are excluded (insufficient statistics).",
        "",
        "---",
        "",
        "*Report generated by astra-pa on 2026-04-19.*",
        "*Simulations computed on astra-climate (224 vCPU GCE).*",
        "*ASTRA multi-agent scientific discovery system — Open University / VBRL Holdings Inc.*",
    ]
    REPORT_OUT.write_text("\n".join(lines))


# ── Main ──────────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    print(f"Analysing Option B results in {RUN_DIR}")
    print(f"Scanning all FG_t*_b* directories with HDF5 snapshots...\n")

    results = {}
    for th in THETAS:
        for beta in BETAS:
            name = f"FG_t{th:02d}_b{int(beta*100):03d}"
            sim_dir = RUN_DIR / name
            if not sim_dir.exists():
                print(f"  {name}: directory not found, skipping")
                results[name] = {'error': 'no directory',
                                 'theta_deg': th, 'beta': beta, 'name': name}
                continue
            n_snaps = len(list(sim_dir.glob(f"{name}.prim.*.athdf")))
            if n_snaps == 0:
                print(f"  {name}: 0 snapshots, skipping")
                results[name] = {'error': 'no snapshots',
                                 'theta_deg': th, 'beta': beta, 'name': name}
                continue
            print(f"  Analysing {name} (θ={th}° β={beta:.2f}, {n_snaps} snaps)...",
                  end=' ', flush=True)
            r = analyse_sim(name, th, beta, sim_dir)
            r['theta_deg'] = th
            r['beta']      = beta
            r['name']      = name
            results[name] = r
            if 'error' in r:
                print(f"ERROR: {r['error']}")
            else:
                C    = r.get('C_final', 0)
                nc   = r.get('n_cores', 0)
                lmj  = r.get('lmj_theory', 0)
                lsep = r.get('mean_sep', 0)
                pen  = " [penultimate]" if r.get('used_penultimate') else ""
                print(f"t={r['t_final']:.2f} C={C:.2f} N_cores={nc} "
                      f"λ_sep={lsep:.3f} λ_MJ={lmj:.3f}{pen}")

    JSON_OUT.write_text(json.dumps(results, indent=2))
    print(f"\nResults saved to {JSON_OUT}")

    write_report(results)
    print(f"Report saved to {REPORT_OUT}")

    # Summary statistics
    valid = [r for r in results.values()
             if 'error' not in r
             and r.get('n_cores', 0) >= 4
             and r.get('theta_deg', 0) != 0
             and r.get('ratio_sep_vs_lmj') is not None]
    print(f"\n=== Summary ===")
    print(f"  Sims with N_cores >= 4 (excl θ=0°): {len(valid)}")
    if valid:
        ratios = [r['ratio_sep_vs_lmj'] for r in valid]
        print(f"  Mean λ_frag/λ_MJ: {np.mean(ratios):.3f} ± {np.std(ratios):.3f}")
        print(f"  Range: [{min(ratios):.3f}, {max(ratios):.3f}]")
        print(f"  Entries:")
        for r in sorted(valid, key=lambda x: (x['theta_deg'], x['beta'])):
            print(f"    {r['name']}: θ={r['theta_deg']}° β={r['beta']:.2f} "
                  f"λ_sep={r['mean_sep']:.3f} λ_MJ={r['lmj_theory']:.3f} "
                  f"ratio={r['ratio_sep_vs_lmj']:.3f}")
