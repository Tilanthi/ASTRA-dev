#!/usr/bin/env python3
"""
analyse_option_a_v2.py — Single-Fibre High-Resolution Analysis
===============================================================
Analyses FIB1_HR_b07 and FIB1_HR_b09 from Option A v2:
  - L=8 λ_J, 256³, single Gaussian fibre, n_modes=10
  - DT_OUTPUT=0.02, snapshots at t=0, 0.02, 0.04, ...

Key improvements over v1:
  1. Power spectrum computed WITHIN THE FIBRE MASK (ρ > ρ_threshold)
     rather than averaging over all spatial slices including background.
  2. Tracks per-mode amplitude growth A(k,t) = sqrt(P(k,t))
     compared to linear theory: A(k,t) = A0 × exp(γ(k)×t)
  3. Measures core separation ALONG FIBRE AXIS once cores appear

Outputs: /home/fetch-agi/analysis_a_v2/option_a_v2_analysis.json
         /home/fetch-agi/analysis_a_v2/option_a_v2_report.md

Authors: Glenn J. White (Open University)
         ASTRA multi-agent system — 2026-04-19
"""

import json
from pathlib import Path
import numpy as np
from scipy import ndimage
import h5py

RUN_DIR = Path("/home/fetch-agi/option_a_v2_runs")
OUT_DIR = Path("/home/fetch-agi/analysis_a_v2")

L  = 8.0
NX = 256
DX = L / NX

SIMS = [
    {"name": "FIB1_HR_b07", "beta": 0.70, "n_fibers": 1,
     "rho_c": 4.0, "sigma": 0.60, "n_modes": 10,
     "cx2": 4.0, "cx3": 4.0},
    {"name": "FIB1_HR_b09", "beta": 0.90, "n_fibers": 1,
     "rho_c": 4.0, "sigma": 0.60, "n_modes": 10,
     "cx2": 4.0, "cx3": 4.0},
]

# ── Physics ───────────────────────────────────────────────────────────────────

def lmj_fiber(beta, rho_c=4.0):
    return (1.0/np.sqrt(rho_c)) * np.sqrt(1.0 + 2.0/beta)

def lmj_bg(beta):
    return np.sqrt(1.0 + 2.0/beta)

def growth_rate_fiber(k, beta, rho_c=4.0):
    """Linear growth rate γ(k) in fibre interior (B⊥ fibre axis)."""
    four_pi_G_rho = 4.0 * np.pi**2 * rho_c
    cs2_eff = 1.0 + 2.0/beta    # using background β (B doesn't change with ρ)
    g2 = four_pi_G_rho - k**2 * cs2_eff
    return np.sqrt(np.maximum(g2, 0.0))

# ── HDF5 ─────────────────────────────────────────────────────────────────────

def assemble_density(path):
    with h5py.File(path, 'r') as f:
        t    = float(f.attrs['Time'])
        prim = np.array(f['prim'], dtype=np.float32)
        locs = np.array(f['LogicalLocations'])
    _, nblocks, nz, ny, nx = prim.shape
    mx = int(locs[:,0].max())+1; my = int(locs[:,1].max())+1; mz = int(locs[:,2].max())+1
    full = np.zeros((mz*nz, my*ny, mx*nx), dtype=np.float32)
    for b in range(nblocks):
        lx,ly,lz = int(locs[b,0]),int(locs[b,1]),int(locs[b,2])
        full[lz*nz:(lz+1)*nz, ly*ny:(ly+1)*ny, lx*nx:(lx+1)*nx] = prim[0,b]
    return t, full

# ── Per-snapshot analysis ─────────────────────────────────────────────────────

def analyse_snapshot(rho, sim, t):
    beta  = sim['beta']
    rho_c = sim['rho_c']
    cx2   = sim['cx2']
    cx3   = sim['cx3']
    sigma = sim['sigma']

    rho_mean = float(rho.mean())
    rho_max  = float(rho.max())
    C = rho_max / rho_mean

    # ── Fibre mask: 3D Gaussian envelope ≥ ½ peak
    x2_arr = (np.arange(NX) + 0.5) * DX
    x3_arr = (np.arange(NX) + 0.5) * DX
    x2_3d, x3_3d = np.meshgrid(x2_arr, x3_arr, indexing='ij')   # (NX, NX)
    dr2 = (x2_3d - cx2)**2 + (x3_3d - cx3)**2
    # Broadcast to (x3, x2, x1) shape for masking
    dr2_3d = dr2.T[:, :, np.newaxis]   # (NZ, NY, 1) → broadcast over x1
    fiber_mask_3d = dr2_3d < (2.0 * sigma)**2   # within 2σ

    # Mean density inside vs outside fibre
    fiber_mask_full = np.broadcast_to(dr2_3d < (2.0 * sigma)**2, rho.shape)
    rho_fib_mean = float(rho[fiber_mask_full].mean())

    # ── 1D power spectrum WITHIN FIBRE along x1 (axis=2)
    # Strategy: for each (x3,x2) position inside the fibre mask, extract
    # the 1D profile rho[iz,iy,:] along x1 and compute its FFT
    dk    = 2.0 * np.pi / L
    k_arr = np.fft.rfftfreq(NX, d=1.0/NX) * dk
    nk    = len(k_arr)

    power_fib = np.zeros(nk)
    n_lines   = 0

    # Use the mean 2D cross-section mask (averaged over x1, then apply threshold)
    # Mask shape: (NZ, NY) from averaging dr2_3d over x1
    fib2d = dr2_3d[:, :, 0] < (2.0 * sigma)**2   # (NZ, NY)

    # Also add density threshold: cells where rho_x1mean > rho_c/2
    rho_x1mean = rho.mean(axis=2)   # (NZ, NY)
    fib2d_rho  = fib2d & (rho_x1mean > rho_mean * rho_c / 2.0)
    if fib2d_rho.sum() == 0:
        fib2d_rho = fib2d   # fallback to geometry only

    for iz in range(NX):
        for iy in range(NX):
            if not fib2d_rho[iz, iy]:
                continue
            sl = rho[iz, iy, :].astype(np.float64)
            # Detrend: subtract mean
            sl_detrend = sl - sl.mean()
            ft = np.abs(np.fft.rfft(sl_detrend))**2
            power_fib += ft
            n_lines   += 1

    if n_lines > 0:
        power_fib /= n_lines
        # Normalise by mean² for dimensionless perturbation power
        power_fib_norm = power_fib / rho_mean**2
    else:
        power_fib_norm = np.zeros(nk)

    # Dominant mode (exclude DC k=0)
    if nk > 1 and power_fib_norm[1:].max() > 0:
        k_dom_idx = np.argmax(power_fib_norm[1:]) + 1
        k_dom     = float(k_arr[k_dom_idx])
        lam_dom   = 2.0 * np.pi / k_dom if k_dom > 0 else L
        power_dom = float(power_fib_norm[k_dom_idx])
    else:
        k_dom = 0.0; lam_dom = L; power_dom = 0.0

    # ── Power at specific theoretically-motivated modes
    lmj_f = lmj_fiber(beta, rho_c)
    k_mj  = 2.0 * np.pi / lmj_f
    lam_seed_min = L / sim['n_modes']
    k_seed_min   = 2.0 * np.pi / lam_seed_min

    def power_at_k(k_target):
        if k_target <= 0 or k_arr[-1] < k_target:
            return 0.0
        idx = int(np.argmin(np.abs(k_arr - k_target)))
        return float(power_fib_norm[idx])

    # ── Radial FWHM of fibre (x1-averaged cross-section)
    r_arr  = np.linspace(0, 3.0*sigma, 40)
    r_mids = 0.5*(r_arr[:-1]+r_arr[1:])
    profile = np.zeros(len(r_mids))
    dr      = np.sqrt(dr2)   # (NX,NX) — will need matching to rho dims

    # rho averaged over x1 and over annuli in (x2,x3)
    rho_avg_x1 = rho.mean(axis=2)   # (NZ, NY)
    dr_img     = np.sqrt(dr2).T     # (NZ, NY) — note dr2 was (x2,x3) → T gives (x3,x2)
    for ib, (r0, r1) in enumerate(zip(r_arr[:-1], r_arr[1:])):
        ann = (dr_img >= r0) & (dr_img < r1)
        if ann.sum() > 0:
            profile[ib] = float(rho_avg_x1[ann].mean())

    peak = profile.max()
    half = 0.5 * peak
    ab   = r_mids[profile >= half]
    fwhm = float(ab[-1]-ab[0]) if len(ab) >= 2 else float(2.355*sigma)

    # ── Core detection along x1
    rho_along = rho.mean(axis=(0,1))     # (NX,) — mean over x2,x3 → along x1
    # Better: mean within fibre mask along x1
    fiber_sum  = None  # not used
    # Simple: 1D profile along x1 at fibre centre
    ix2c = int(round(cx2/DX - 0.5)); ix3c = int(round(cx3/DX - 0.5))
    rho_along_centre = rho[ix3c, ix2c, :]

    rho_1d_smooth = ndimage.gaussian_filter1d(rho_along_centre.astype(np.float64), sigma=2.0)
    above_thresh  = rho_1d_smooth > rho_mean * rho_c * 1.5
    labeled_1d, n_cores_1d = ndimage.label(above_thresh)

    # Core positions along x1
    core_x1 = []
    for lbl in range(1, n_cores_1d+1):
        idx = np.where(labeled_1d == lbl)[0]
        wts = rho_along_centre[idx]
        com = float(np.average(idx, weights=wts)) * DX
        core_x1.append(com)

    if len(core_x1) >= 2:
        core_x1.sort()
        gaps  = [core_x1[(i+1)%len(core_x1)] - core_x1[i] for i in range(len(core_x1))]
        gaps  = [g if g > 0 else g + L for g in gaps]
        lam_sep_1d = float(np.mean(gaps))
    else:
        lam_sep_1d = 0.0

    return {
        't':            float(t),
        'rho_mean':     rho_mean,
        'rho_max':      rho_max,
        'C':            C,
        'rho_fib_mean': rho_fib_mean,
        'n_fiber_lines': n_lines,
        'lam_dom':      lam_dom,
        'k_dom':        k_dom,
        'power_dom':    power_dom,
        'fwhm':         fwhm,
        'n_cores_1d':   n_cores_1d,
        'lam_sep_1d':   lam_sep_1d,
        'power_at_lmj': power_at_k(k_mj),
        'power_at_seed_min': power_at_k(k_seed_min),
        # Power spectrum for plotting (modes 1..20)
        'k_modes':      k_arr[1:21].tolist(),
        'power_modes':  power_fib_norm[1:21].tolist(),
    }

# ── Per-sim analysis ──────────────────────────────────────────────────────────

def analyse_sim(sim):
    name    = sim['name']
    run_dir = RUN_DIR / name
    snaps   = sorted(run_dir.glob(f"{name}.prim.*.athdf"))
    if not snaps:
        return {'error': 'no snapshots', 'name': name}

    print(f"\n  === {name} ({len(snaps)} snapshots, β={sim['beta']:.2f}) ===")
    lmj_f = lmj_fiber(sim['beta'], sim['rho_c'])
    lmj_b = lmj_bg(sim['beta'])
    print(f"    λ_MJ,fibre = {lmj_f:.4f}  |  λ_MJ,bg = {lmj_b:.4f}")
    print(f"    λ_min seeded = {L/sim['n_modes']:.4f}  (< λ_MJ,fibre: {L/sim['n_modes'] < lmj_f})")
    print(f"    Expected cores: ~{int(round(L/lmj_f))} (theory)  /  ~{int(round(L/(1.107*lmj_f)))} (calibrated f=1.107)")

    snap_results = []
    for snap in snaps:
        try:
            t, rho = assemble_density(snap)
        except Exception as e:
            print(f"    {snap.name}: ERROR {e}")
            continue
        res = analyse_snapshot(rho, sim, t)
        snap_results.append(res)
        print(f"    {snap.name}: t={t:.3f} C={res['C']:.2f} "
              f"λ_dom={res['lam_dom']:.3f} n_cores={res['n_cores_1d']} "
              f"λ_sep={res['lam_sep_1d']:.3f} FWHM={res['fwhm']:.3f} "
              f"(fiber lines: {res['n_fiber_lines']})")
        del rho

    # Growth rate fit to density contrast C(t)
    gamma_obs = 0.0
    if len(snap_results) >= 3:
        ts = np.array([r['t'] for r in snap_results])
        Cs = np.array([r['C'] for r in snap_results])
        log_C = np.log(np.maximum(Cs, 1e-6))
        if ts[-1] > ts[0]:
            gamma_obs = float(np.polyfit(ts, log_C, 1)[0])

    # Power spectrum growth rate at λ_MJ mode
    gamma_lmj_obs = 0.0
    if len(snap_results) >= 3:
        ts     = np.array([r['t'] for r in snap_results])
        p_lmj  = np.array([r['power_at_lmj'] for r in snap_results])
        if p_lmj.max() > 0 and ts[-1] > ts[0]:
            valid = p_lmj > 0
            if valid.sum() >= 3:
                log_p = np.log(np.maximum(p_lmj[valid], 1e-30))
                gamma_lmj_obs = float(np.polyfit(ts[valid], log_p, 1)[0]) / 2.0  # P~A² → γ_P = 2γ_A

    gamma_max_th = float(np.sqrt(4.0 * np.pi**2 * sim['rho_c']))
    k_mj         = 2.0 * np.pi / lmj_f
    gamma_mj_th  = float(growth_rate_fiber(k_mj, sim['beta'], sim['rho_c']))

    print(f"    γ_max theory = {gamma_max_th:.3f}  |  γ(λ_MJ) theory = {gamma_mj_th:.3f}")
    print(f"    γ_obs (C fit) = {gamma_obs:.3f}  |  γ_obs (P_MJ) = {gamma_lmj_obs:.3f}")

    return {
        'name':            name,
        'beta':            sim['beta'],
        'rho_c':           sim['rho_c'],
        'n_modes':         sim['n_modes'],
        'lam_seed_min':    L / sim['n_modes'],
        'lambda_mj_fiber': lmj_f,
        'lambda_mj_bg':    lmj_b,
        'gamma_max_theory':  gamma_max_th,
        'gamma_mj_theory':   gamma_mj_th,
        'gamma_obs_C':       gamma_obs,
        'gamma_obs_Pmj':     gamma_lmj_obs,
        'n_expected_theory': int(round(L / lmj_f)),
        'n_expected_calib':  int(round(L / (1.107 * lmj_f))),
        'snapshots':         snap_results,
    }

# ── Report ────────────────────────────────────────────────────────────────────

def write_report(results):
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    lines = [
        "# Option A v2: Single-Fibre High-Resolution Analysis",
        "",
        "**Purpose:** Test the magnetic Jeans fragmentation formula INSIDE a fibre",
        "by seeding perturbation modes that span BOTH stable (λ<λ_MJ) and unstable (λ>λ_MJ) scales.",
        "",
        "**Key improvement over v1:** n_modes=10 with L=8 seeds λ_min=0.8 λ_J < λ_MJ,fibre(β=0.7)=0.982.",
        "Power spectrum computed WITHIN the fibre mask (2σ radius, density threshold).",
        "",
        "| Parameter | Value |",
        "|-----------|-------|",
        "| Grid | 256³, L=8 λ_J, dx=0.03125 λ_J |",
        "| Fibre | σ=0.60 λ_J, FWHM=1.41 λ_J, ρ_c=4.0 |",
        "| Perturbation | n_modes=10, A=5%, λ∈[0.8,8.0]λ_J |",
        "| B-field | Symmetric radial (0,B₀/√2,B₀/√2) ⊥ fibre axis |",
        "| M_sonic | 3.0 |",
        "",
        "---",
        "",
        "## Mode Stability Analysis",
        "",
        "| β | λ_MJ,fibre | Unstable modes (λ>λ_MJ) | Stable modes seeded |",
        "|---|-----------|-------------------------|---------------------|",
    ]
    for beta in [0.70, 0.90]:
        lmj_f = lmj_fiber(beta)
        n_ust = int(L / lmj_f)
        stbl  = [f"n={n_ust+1} (λ={L/(n_ust+1):.3f})", f"n={n_ust+2} (λ={L/(n_ust+2):.3f})"]
        lines.append(f"| {beta:.2f} | {lmj_f:.3f} λ_J | n=1..{n_ust} "
                     f"(λ≥{L/n_ust:.3f} λ_J) | {', '.join(stbl)} |")

    lines += ["", "---", "", "## Results", ""]

    for r in results.values():
        if 'error' in r:
            lines.append(f"### {r['name']}: ERROR — {r['error']}\n")
            continue

        snaps = r['snapshots']
        if not snaps:
            lines.append(f"### {r['name']}: no valid snapshots\n")
            continue

        t_final = snaps[-1]['t'] if snaps else 0
        lines += [
            f"### {r['name']} (β={r['beta']:.2f}, λ_MJ,fibre={r['lambda_mj_fiber']:.3f} λ_J)",
            "",
            f"- λ_min seeded = {r['lam_seed_min']:.2f} λ_J  "
            f"({'< λ_MJ,fibre — CORRECT TEST' if r['lam_seed_min'] < r['lambda_mj_fiber'] else '≥ λ_MJ,fibre — incomplete test'})",
            f"- Expected: ~{r['n_expected_theory']} cores (λ_MJ theory)  /  "
            f"~{r['n_expected_calib']} cores (calibrated f=1.107)",
            f"- γ_max theory = {r['gamma_max_theory']:.3f}  |  "
            f"γ(λ_MJ) theory = {r['gamma_mj_theory']:.3f}",
            f"- γ_obs (C fit) = **{r['gamma_obs_C']:.3f}**  |  "
            f"γ_obs (power at λ_MJ) = **{r['gamma_obs_Pmj']:.3f}**",
            "",
            "| t/t_J | C | λ_dom | FWHM | N_cores | λ_sep | P(λ_MJ) |",
            "|-------|---|-------|------|---------|-------|---------|",
        ]
        for s in snaps:
            lines.append(f"| {s['t']:.3f} | {s['C']:.2f} | {s['lam_dom']:.3f} | "
                         f"{s['fwhm']:.3f} | {s['n_cores_1d']:7d} | "
                         f"{s['lam_sep_1d']:.3f} | {s['power_at_lmj']:.3e} |")

        # Final state
        fs = snaps[-1]
        lines += [
            "",
            f"**Final state (t={t_final:.3f} t_J):** C={fs['C']:.1f}, "
            f"N_cores={fs['n_cores_1d']}, λ_sep={fs['lam_sep_1d']:.3f} λ_J",
        ]
        if fs['n_cores_1d'] > 0 and fs['lam_sep_1d'] > 0:
            ratio = fs['lam_sep_1d'] / r['lambda_mj_fiber']
            lines.append(f"**λ_sep / λ_MJ,fibre = {ratio:.3f}** "
                         f"(expected: 1.107 ± 0.117 from Option B calibration)")
        lines.append("")

    lines += [
        "---", "",
        "## Comparison with Option B Calibration",
        "",
        "Option B established λ_frag = (1.107 ± 0.117) × λ_MJ(θ,β) for uniform-density sims.",
        "Option A v2 tests whether this calibration applies INSIDE a structured fibre",
        "(ρ_c/ρ_bg=4, σ=0.6 λ_J) where the local Jeans length is √4=2× smaller.",
        "",
        "If λ_sep / λ_MJ,fibre ≈ 1.11 ± 0.12, the calibration is fibre-geometry-independent.",
        "",
        "---",
        "*Report generated by astra-pa on 2026-04-19.*",
        "*Simulations computed on astra-climate (224 vCPU GCE).*",
        "*ASTRA multi-agent scientific discovery system — Open University / VBRL Holdings Inc.*",
    ]

    report_path = OUT_DIR / "option_a_v2_report.md"
    report_path.write_text("\n".join(lines))
    return report_path

# ── Main ──────────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    print("Option A v2 — Single-Fibre High-Resolution Analysis")
    print(f"Reading from {RUN_DIR}\n")

    results = {}
    for sim in SIMS:
        r = analyse_sim(sim)
        results[sim['name']] = r

    json_path = OUT_DIR / "option_a_v2_analysis.json"
    json_path.write_text(json.dumps(results, indent=2))
    print(f"\nResults: {json_path}")

    rpt = write_report(results)
    print(f"Report:  {rpt}")

    # Summary
    print("\n=== Summary ===")
    for name, r in results.items():
        if 'error' in r: continue
        snaps = r.get('snapshots', [])
        if snaps:
            fs = snaps[-1]
            ratio = fs['lam_sep_1d']/r['lambda_mj_fiber'] if fs['lam_sep_1d']>0 else 0
            print(f"  {name}: t={fs['t']:.3f} C={fs['C']:.1f} "
                  f"N_cores={fs['n_cores_1d']} "
                  f"λ_sep={fs['lam_sep_1d']:.3f} λ_MJ={r['lambda_mj_fiber']:.3f} "
                  f"ratio={ratio:.3f}")
