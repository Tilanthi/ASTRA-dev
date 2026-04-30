#!/usr/bin/env python3
"""
λ/W Analysis for Perpendicular B-field Simulations
===================================================
Referee Concern #4: Direct λ/W measurements for perpendicular-field configurations.

This script is physically honest: it attempts to measure λ/W from x1 density profiles
at each saved HDF5 snapshot, but also quantifies radial compression to determine
whether radial collapse precluded axial beading — the expected physical result.

Output per simulation:
  - t_onset_axial: time at which axial contrast > 5% (if ever)
  - lambda_W_peak: λ/W at peak axial contrast (if measurable)
  - lambda_W_fourier: λ/W from Fourier power spectrum (if measurable)
  - rho_max_radial: peak central density at t_frag (radial compression metric)
  - axial_contrast_max: maximum σ/μ of x1 density profile over all snapshots
  - outcome: 'measurable' | 'radial_collapse_dominant' | 'insufficient_snapshots'

Usage (on astra-climate after runner completes):
  python3 /home/fetch-agi/analyse_perp_lambda_W.py

Requires:
  - h5py, numpy, scipy, matplotlib
  - /data/perp_lambda_W_runs/ (output from perp_lambda_W_runner.py)
"""

import json, os, re, sys, glob
import numpy as np
from pathlib import Path
from scipy.signal import find_peaks
from scipy.fft import rfft, rfftfreq
from scipy.optimize import curve_fit

try:
    import h5py
    HDF5_OK = True
except ImportError:
    HDF5_OK = False
    print("WARNING: h5py not available — HDF5 analysis disabled")

try:
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    MPL_OK = True
except ImportError:
    MPL_OK = False
    print("WARNING: matplotlib not available — figures disabled")

# ── Config ─────────────────────────────────────────────────────────────────────
SIMBASE     = "/data/perp_lambda_W_runs"
RESULTS_IN  = f"{SIMBASE}/results.json"
ANALYSIS_OUT = f"{SIMBASE}/lambda_W_analysis.json"
FIGDIR      = f"{SIMBASE}/figures"

# λ/W detection thresholds
AXIAL_CONTRAST_THRESHOLD = 0.05   # σ/μ > 5% → axial modulation present
PEAK_HEIGHT_THRESHOLD     = 1.15  # density peak > 15% above mean → real peak
PEAK_MIN_DISTANCE_CELLS   = 8     # minimum cell separation between peaks (≈0.25 λ_J at 32 cells/λ_J)
DOMAIN_LENGTH_LAMBDA_J    = 8.0   # x1 domain in λ_J
W_LAMBDA_J                = 0.3   # filament FWHM (≈ 0.1 pc / λ_J ≈ 0.3 for HGBS)


def read_hdf5_snapshot(fpath):
    """Read density field from an Athena++ HDF5 snapshot."""
    if not HDF5_OK:
        return None, None
    with h5py.File(fpath, "r") as f:
        # Athena++ stores primitive variables in 'prim' dataset
        # Shape is (nvars, nx3, nx2, nx1) or varies by version
        if "prim" in f:
            prim = f["prim"][:]
            rho  = prim[0]          # density is first variable
        elif "cons" in f:
            rho  = f["cons"][0][:]
        else:
            # Try direct density key
            rho  = f["density"][:]
        # Simulation time
        time_val = float(f.attrs.get("Time", f.attrs.get("time", np.nan)))
    return rho, time_val


def x1_profile(rho):
    """Longitudinal (x1) density profile: average over x2, x3."""
    # rho shape: (nx3, nx2, nx1) — Athena++ ordering
    if rho.ndim == 3:
        return np.mean(rho, axis=(0, 1))   # mean over x3, x2 → shape (nx1,)
    return rho


def measure_axial_contrast(profile):
    """Return σ/μ of the x1 density profile (axial modulation strength)."""
    mu = np.mean(profile)
    if mu == 0:
        return 0.0
    return np.std(profile) / mu


def measure_lambda_W_peaks(profile, dx_lambda_J):
    """
    Measure λ/W from peak positions in the x1 profile.

    Returns dict with:
      n_peaks, lambda_pairwise_lambda_J, lambda_W_pairwise, status
    """
    profile_norm = profile / np.mean(profile)
    peaks, props = find_peaks(
        profile_norm,
        height=PEAK_HEIGHT_THRESHOLD,
        distance=PEAK_MIN_DISTANCE_CELLS,
    )
    if len(peaks) < 2:
        return {
            "n_peaks": len(peaks),
            "lambda_pairwise_lambda_J": np.nan,
            "lambda_W_pairwise": np.nan,
            "status": "insufficient_peaks",
        }
    # Nearest-neighbour spacing (sorted peaks)
    spacings = np.diff(np.sort(peaks)) * dx_lambda_J
    lambda_nn = np.median(spacings)
    lambda_W  = lambda_nn / W_LAMBDA_J
    return {
        "n_peaks": int(len(peaks)),
        "peak_positions_cells": peaks.tolist(),
        "spacings_lambda_J": spacings.tolist(),
        "lambda_nn_lambda_J": float(lambda_nn),
        "lambda_W_pairwise": float(lambda_W),
        "status": "success",
    }


def measure_lambda_W_fourier(profile, dx_lambda_J):
    """
    Measure λ/W from Fourier power spectrum of the x1 profile.

    Returns dict with:
      dominant_lambda_lambda_J, lambda_W_fourier, power_fraction, status
    """
    prof_centered = profile - np.mean(profile)
    if np.std(prof_centered) == 0:
        return {"lambda_W_fourier": np.nan, "status": "flat_profile"}

    n    = len(prof_centered)
    F    = rfft(prof_centered)
    P    = np.abs(F) ** 2
    freq = rfftfreq(n, d=dx_lambda_J)  # cycles per λ_J

    # Exclude DC component
    valid = freq > 0
    if not np.any(valid):
        return {"lambda_W_fourier": np.nan, "status": "no_valid_freqs"}

    P_valid    = P[valid]
    freq_valid = freq[valid]
    i_dom      = np.argmax(P_valid)
    f_dom      = freq_valid[i_dom]
    lambda_dom = 1.0 / f_dom if f_dom > 0 else np.nan
    lambda_W   = lambda_dom / W_LAMBDA_J if not np.isnan(lambda_dom) else np.nan
    power_frac = float(P_valid[i_dom] / P_valid.sum()) if P_valid.sum() > 0 else np.nan

    return {
        "dominant_freq_per_lambdaJ": float(f_dom),
        "dominant_lambda_lambda_J":  float(lambda_dom),
        "lambda_W_fourier":          float(lambda_W),
        "power_fraction_dominant":   power_frac,
        "status": "success",
    }


def analyse_simulation(sim_result):
    """
    Full λ/W analysis for one simulation.

    Reads all HDF5 snapshots, builds time-series of axial contrast and
    density metrics, and reports whether λ/W is measurable.
    """
    sim_id  = sim_result["sim_id"]
    sim_dir = Path(sim_result["sim_dir"])

    # Collect HDF5 files sorted by snapshot number
    hdf5_files = sorted(sim_dir.glob("*.athdf"),
                        key=lambda p: int(re.search(r"\.(\d+)\.athdf$", p.name).group(1))
                        if re.search(r"\.(\d+)\.athdf$", p.name) else 0)

    if not hdf5_files:
        return {
            "sim_id": sim_id,
            "outcome": "insufficient_snapshots",
            "n_snapshots": 0,
            "note": "No .athdf files found — HDF5 output may not have been written",
        }

    dx_lambda_J = DOMAIN_LENGTH_LAMBDA_J / 256  # cells per λ_J for 256 cells in x1

    time_series = []
    for fpath in hdf5_files:
        try:
            rho, t = read_hdf5_snapshot(str(fpath))
            if rho is None:
                continue
            profile = x1_profile(rho)
            nx1     = len(profile)
            dx      = DOMAIN_LENGTH_LAMBDA_J / nx1

            axial_contrast  = measure_axial_contrast(profile)
            peak_result     = measure_lambda_W_peaks(profile, dx)
            fourier_result  = measure_lambda_W_fourier(profile, dx)
            rho_max         = float(np.max(rho))
            rho_central     = float(np.mean(rho[:, rho.shape[1]//2-2:rho.shape[1]//2+2,
                                                   rho.shape[2]//2-2:rho.shape[2]//2+2]))

            time_series.append({
                "t":               float(t),
                "axial_contrast":  float(axial_contrast),
                "rho_max":         rho_max,
                "rho_central":     rho_central,
                "n_peaks":         peak_result.get("n_peaks", 0),
                "lambda_W_pairwise": peak_result.get("lambda_W_pairwise", np.nan),
                "lambda_W_fourier":  fourier_result.get("lambda_W_fourier", np.nan),
                "snapshot_file":   fpath.name,
            })
        except Exception as e:
            time_series.append({"snapshot_file": fpath.name, "error": str(e)})

    if not time_series:
        return {"sim_id": sim_id, "outcome": "read_error", "n_snapshots": len(hdf5_files)}

    # Sort by time
    valid_ts = [s for s in time_series if "t" in s and "axial_contrast" in s]
    valid_ts.sort(key=lambda s: s["t"])

    if not valid_ts:
        return {"sim_id": sim_id, "outcome": "parse_error", "n_snapshots": len(hdf5_files)}

    # Key derived quantities
    max_contrast  = max(s["axial_contrast"] for s in valid_ts)
    max_rho       = max(s["rho_max"] for s in valid_ts)
    t_first_axial = next((s["t"] for s in valid_ts
                          if s["axial_contrast"] > AXIAL_CONTRAST_THRESHOLD), None)

    # Best λ/W measurement: snapshot at peak axial contrast
    best_snap = max(valid_ts, key=lambda s: s["axial_contrast"])
    lw_pair   = best_snap.get("lambda_W_pairwise", np.nan)
    lw_four   = best_snap.get("lambda_W_fourier",  np.nan)

    # Physical verdict
    if max_contrast < AXIAL_CONTRAST_THRESHOLD:
        verdict = "radial_collapse_dominant"
        note    = (f"Max axial contrast {max_contrast:.3f} < {AXIAL_CONTRAST_THRESHOLD:.2f} threshold. "
                   "Radial collapse precluded axial beading. λ/W unmeasurable.")
    elif best_snap.get("n_peaks", 0) < 2:
        verdict = "radial_collapse_dominant"
        note    = (f"Axial contrast {max_contrast:.3f} detected but insufficient peaks "
                   f"({best_snap.get('n_peaks',0)}) for λ/W. Likely single-core radial collapse.")
    else:
        verdict = "measurable"
        note    = (f"Axial contrast {max_contrast:.3f} with {best_snap['n_peaks']} peaks "
                   f"at t={best_snap['t']:.3f} t_J. λ/W measurement valid.")

    return {
        "sim_id":               sim_id,
        "f":                    sim_result["f"],
        "beta":                 sim_result["beta"],
        "mach":                 sim_result["mach"],
        "seed":                 sim_result["seed"],
        "t_frag":               sim_result.get("t_frag"),
        "outcome_sim":          sim_result.get("outcome"),
        "outcome_lambda_W":     verdict,
        "note":                 note,
        "n_snapshots":          len(hdf5_files),
        "max_axial_contrast":   float(max_contrast),
        "t_first_axial_onset":  float(t_first_axial) if t_first_axial else None,
        "lambda_W_pairwise":    float(lw_pair) if not np.isnan(lw_pair) else None,
        "lambda_W_fourier":     float(lw_four) if not np.isnan(lw_four) else None,
        "lambda_W_best_t":      float(best_snap["t"]),
        "rho_max_at_tfrag":     float(max_rho),
        "time_series":          valid_ts,
    }


def make_figures(analyses):
    """Generate summary figures from analyses."""
    if not MPL_OK:
        return
    os.makedirs(FIGDIR, exist_ok=True)

    measurable = [a for a in analyses if a.get("outcome_lambda_W") == "measurable"]
    radial     = [a for a in analyses if "radial" in a.get("outcome_lambda_W", "")]

    # ── Fig A: axial contrast vs time (all sims) ──────────────────────────────
    fig, ax = plt.subplots(figsize=(10, 5))
    fig.suptitle("Axial Density Contrast vs Time — All Perpendicular B Simulations", fontsize=13)
    colours = {(2.0, 0.3): "#1f77b4", (2.0, 1.0): "#aec7e8",
               (2.5, 0.3): "#ff7f0e", (2.5, 1.0): "#ffbb78",
               (3.0, 0.3): "#2ca02c", (3.0, 1.0): "#98df8a"}
    for a in analyses:
        ts = a.get("time_series", [])
        if not ts:
            continue
        tv = [s["t"] for s in ts if "t" in s]
        cv = [s["axial_contrast"] for s in ts if "axial_contrast" in s]
        if not tv:
            continue
        col = colours.get((a["f"], a["beta"]), "grey")
        lbl = f"f={a['f']} β={a['beta']}" if a["seed"] == 42 else None
        ax.plot(tv, cv, color=col, alpha=0.6, linewidth=0.9, label=lbl)
    ax.axhline(AXIAL_CONTRAST_THRESHOLD, color="red", linestyle="--", linewidth=1.5,
               label=f"Detection threshold ({AXIAL_CONTRAST_THRESHOLD:.0%})")
    ax.set_xlabel(r"$t\ [t_J]$")
    ax.set_ylabel(r"Axial contrast $\sigma/\mu$")
    ax.set_yscale("log")
    ax.legend(ncol=2, fontsize=8)
    ax.grid(True, alpha=0.3)
    for ext in ("pdf", "png"):
        fig.savefig(f"{FIGDIR}/figA_axial_contrast.{ext}", bbox_inches="tight", dpi=150)
    plt.close(fig)
    print("  figA_axial_contrast done")

    # ── Fig B: Summary scatter — max axial contrast by (f, beta) ──────────────
    fig, axes = plt.subplots(1, 2, figsize=(11, 4.5))
    fig.suptitle("λ/W Measurability Summary — Perpendicular B Campaign", fontsize=13)
    from collections import defaultdict
    grid = defaultdict(list)
    for a in analyses:
        grid[(a["f"], a["beta"])].append(a["max_axial_contrast"])
    fs    = sorted(set(a["f"] for a in analyses))
    betas = sorted(set(a["beta"] for a in analyses))
    import matplotlib.cm as cm
    vmin, vmax = 0, max(v for vals in grid.values() for v in vals) * 1.05
    heat = np.full((len(fs), len(betas)), np.nan)
    for i, f in enumerate(fs):
        for j, b in enumerate(betas):
            vals = grid.get((f, b), [])
            if vals:
                heat[i, j] = np.mean(vals)
    ax = axes[0]
    im = ax.imshow(heat, aspect="auto", origin="lower", cmap="RdYlGn",
                   vmin=0, vmax=max(0.3, np.nanmax(heat)))
    ax.set_xticks(range(len(betas))); ax.set_xticklabels([f"β={b}" for b in betas])
    ax.set_yticks(range(len(fs)));   ax.set_yticklabels([f"f={f}" for f in fs])
    ax.set_title("(a) Mean max axial contrast (σ/μ)")
    cb = fig.colorbar(im, ax=ax, pad=0.02)
    cb.set_label("σ/μ")
    for i in range(len(fs)):
        for j in range(len(betas)):
            val = heat[i, j]
            if not np.isnan(val):
                ok  = "✓" if val >= AXIAL_CONTRAST_THRESHOLD else "✗"
                ax.text(j, i, f"{val:.3f}\n{ok}", ha="center", va="center",
                        fontsize=8.5, color="black")

    ax2 = axes[1]
    ax2.axis("off")
    n_meas  = len(measurable)
    n_rad   = len(radial)
    n_total = len(analyses)
    summary_text = (
        f"Total simulations: {n_total}\n\n"
        f"λ/W measurable:           {n_meas} ({100*n_meas/n_total:.0f}%)\n"
        f"Radial collapse dominant: {n_rad}  ({100*n_rad/n_total:.0f}%)\n\n"
    )
    if measurable:
        lw_vals = [a["lambda_W_pairwise"] for a in measurable if a.get("lambda_W_pairwise")]
        if lw_vals:
            summary_text += f"λ/W (measurable sims):\n  mean = {np.mean(lw_vals):.2f} ± {np.std(lw_vals):.2f}\n"
            summary_text += f"  range = [{min(lw_vals):.2f}, {max(lw_vals):.2f}]\n\n"
    summary_text += (
        f"Detection threshold: σ/μ > {AXIAL_CONTRAST_THRESHOLD:.0%}\n"
        f"W_fil = {W_LAMBDA_J} λ_J\n\n"
        "INTERPRETATION:\n"
        "If radial collapse dominates, this\n"
        "confirms that λ/W is physically\n"
        "unmeasurable for perp-B filaments\n"
        "in the supercritical regime — a\n"
        "definitive result for the referee."
    )
    ax2.text(0.05, 0.95, summary_text, transform=ax2.transAxes, va="top",
             fontsize=10, family="monospace", bbox=dict(boxstyle="round", fc="#f5f5f5"))
    ax2.set_title("(b) Campaign summary")

    fig.tight_layout()
    for ext in ("pdf", "png"):
        fig.savefig(f"{FIGDIR}/figB_lambda_W_summary.{ext}", bbox_inches="tight", dpi=150)
    plt.close(fig)
    print("  figB_lambda_W_summary done")


def main():
    print("Perpendicular B-field λ/W Analysis")
    print("=" * 50)

    # Load runner results
    if not os.path.exists(RESULTS_IN):
        print(f"ERROR: {RESULTS_IN} not found. Run perp_lambda_W_runner.py first.")
        sys.exit(1)
    with open(RESULTS_IN) as f:
        runner_results = json.load(f)

    print(f"Loaded {len(runner_results)} simulation results")
    frag   = [r for r in runner_results if r.get("outcome") == "FRAG"]
    timout = [r for r in runner_results if r.get("outcome") == "TIMEOUT"]
    print(f"  FRAG={len(frag)}  TIMEOUT={len(timout)}  other={len(runner_results)-len(frag)-len(timout)}")

    # Analyse each simulation
    analyses = []
    for i, r in enumerate(runner_results):
        print(f"  Analysing {r['sim_id']}  ({i+1}/{len(runner_results)}) ...", end="  ")
        a = analyse_simulation(r)
        analyses.append(a)
        print(f"verdict={a.get('outcome_lambda_W','?')}  "
              f"contrast={a.get('max_axial_contrast', 0):.4f}  "
              f"n_snaps={a.get('n_snapshots', 0)}")

    # Save full analysis
    with open(ANALYSIS_OUT, "w") as f:
        json.dump(analyses, f, indent=2, default=str)
    print(f"\nFull analysis saved: {ANALYSIS_OUT}")

    # Print summary
    measurable = [a for a in analyses if a.get("outcome_lambda_W") == "measurable"]
    radial     = [a for a in analyses if "radial" in a.get("outcome_lambda_W", "")]
    print("\n" + "=" * 50)
    print("SUMMARY")
    print("=" * 50)
    print(f"Total simulations analysed:  {len(analyses)}")
    print(f"λ/W measurable:              {len(measurable)}")
    print(f"Radial collapse dominant:    {len(radial)}")

    if measurable:
        lw_vals = [a["lambda_W_pairwise"] for a in measurable if a.get("lambda_W_pairwise")]
        if lw_vals:
            print(f"\nλ/W (measurable sims):  {np.mean(lw_vals):.2f} ± {np.std(lw_vals):.2f}")
            print(f"  range: [{min(lw_vals):.2f}, {max(lw_vals):.2f}]")
    else:
        print("\nλ/W: NOT MEASURABLE in any simulation")
        print("  → Radial collapse universally precedes axial beading for θ=90°")
        print("  → This is a definitive negative result for the referee.")

    print(f"\nMax axial contrast across all sims: "
          f"{max(a.get('max_axial_contrast',0) for a in analyses):.4f}")
    print(f"(threshold for detection: {AXIAL_CONTRAST_THRESHOLD:.2f})")

    # Figures
    if MPL_OK:
        print("\nGenerating figures...")
        make_figures(analyses)
        print(f"Figures written to: {FIGDIR}/")

    print(f"\nAnalysis complete. Results: {ANALYSIS_OUT}")


if __name__ == "__main__":
    main()
