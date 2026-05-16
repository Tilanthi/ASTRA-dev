#!/usr/bin/env python3
"""
Analyse Campaign Results — Process HDF5 outputs and measure λ/W
=================================================================

This script analyses completed simulations from a campaign directory,
measuring λ/W from HDF5 snapshots using peak detection.

Usage:
    python analyse_campaign.py <campaign_directory>

Example:
    python analyse_campaign.py /data/referee_response_may2026/ctzm_perp

Output:
    - <campaign_dir>/<campaign>_analysed.json (full results with λ/W)
    - <campaign_dir>/<campaign>_summary.json (aggregated statistics)
    - <campaign_dir>/figures/ (diagnostic plots)

Author: Claude (ASTRA System)
Date: 2026-05-13
"""

import sys
import json
import argparse
from pathlib import Path
from typing import Dict, List, Any, Optional
import numpy as np
from scipy.signal import find_peaks
from scipy.ndimage import gaussian_filter1d
import h5py
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

# ── Constants ───────────────────────────────────────────────────────────────
W_CORE = 0.3
DX1 = 8.0 / 256  # λ_J per cell along filament axis

def measure_lambda_W_snapshot(hdf5_path: Path) -> Optional[Dict[str, Any]]:
    """
    Measure λ/W from a single HDF5 snapshot.

    Returns dict with keys: t, n_peaks, lambda_W
    Returns None if analysis fails.
    """
    try:
        with h5py.File(hdf5_path, 'r') as f:
            t_val = float(f.attrs['Time'])
            prim = f['prim'][...]  # Shape: (n_vars, n_mb, nk, nj, ni)
            locs = f['LogicalLocations'][:]  # Shape: (n_mb, 3)

        n_vars, n_mb, nk_mb, nj_mb, ni_mb = prim.shape
        NI, NJ, NK = 256, 64, 64

        # Reconstruct global density array from meshblocks
        rho_global = np.zeros((NK, NJ, NI), dtype=np.float32)
        for mb in range(n_mb):
            lx1, lx2, lx3 = int(locs[mb, 0]), int(locs[mb, 1]), int(locs[mb, 2])
            i0 = lx1 * ni_mb
            j0 = lx2 * nj_mb
            k0 = lx3 * nk_mb
            rho_global[k0:k0+nk_mb, j0:j0+nj_mb, i0:i0+ni_mb] = prim[0, mb]

        # Column-averaged linear mass density along filament axis (x1)
        col_rho = rho_global.mean(axis=(0, 1))  # Mean over x2, x3 → shape (NI,)

        # Light Gaussian smoothing (σ=2 cells)
        col_smooth = gaussian_filter1d(col_rho, sigma=2)

        # Peak detection with adaptive prominence threshold
        dyn_range = col_smooth.max() - col_smooth.min()
        min_prominence = max(0.05 * dyn_range, 0.01 * col_smooth.mean())
        peaks, properties = find_peaks(
            col_smooth,
            prominence=min_prominence,
            distance=8  # Minimum spacing between peaks (in cells)
        )

        n_peaks = len(peaks)
        lw = None
        if n_peaks >= 2:
            # Measure spacing between consecutive peaks
            spacings = np.diff(peaks) * DX1  # Convert cells → λ_J
            lw_median = float(np.median(spacings) / W_CORE)
            lw_std = float(np.std(spacings) / W_CORE)
            lw = lw_median

        return {
            "t": round(t_val, 4),
            "n_peaks": n_peaks,
            "lambda_W": lw,
        }

    except Exception as e:
        return None

def analyse_single_simulation(run_dir: Path, run_id: str) -> Dict[str, Any]:
    """
    Analyse all HDF5 snapshots from a single simulation.

    Returns dict with classification and λ/W statistics.
    """
    hdf5_files = sorted(run_dir.glob("*.athdf"))

    if not hdf5_files:
        return {
            "run_id": run_id,
            "classification": "NO_HDF5",
            "n_hdf5": 0,
            "lw_mean": None,
            "lw_std": None,
            "lambda_W_series": [],
        }

    # Analyse each snapshot
    series = []
    for hf in hdf5_files:
        result = measure_lambda_W_snapshot(hf)
        if result is not None:
            result["filename"] = hf.name
            series.append(result)

    # Classification
    beading_snaps = [s for s in series if s["lambda_W"] is not None]

    if len(beading_snaps) >= 2:
        lw_vals = [s["lambda_W"] for s in beading_snaps]
        lw_mean = float(np.mean(lw_vals))
        lw_std = float(np.std(lw_vals))
        cv = lw_std / lw_mean if lw_mean > 0 else float('inf')

        if cv < 0.3:
            classification = "BEADING_STABLE"
        else:
            classification = "BEADING_TRANSIENT"

    else:
        classification = "RADIAL_COLLAPSE" if len(beading_snaps) < 2 else "NO_BEADING"
        lw_mean = None
        lw_std = None

    return {
        "run_id": run_id,
        "classification": classification,
        "n_hdf5": len(hdf5_files),
        "n_beading_snaps": len(beading_snaps),
        "lw_mean": lw_mean,
        "lw_std": lw_std,
        "lambda_W_series": series,
    }

def load_campaign_results(campaign_dir: Path) -> List[Dict[str, Any]]:
    """Load the basic campaign results from *_results.json."""
    results_file = campaign_dir / "ctzm_perp_results.json"
    if not results_file.exists():
        results_file = campaign_dir / "eos_sensitivity_results.json"
    if not results_file.exists():
        results_file = campaign_dir / "turb_amplitude_results.json"
    if not results_file.exists():
        results_file = campaign_dir / "all_campaigns_results.json"

    if not results_file.exists():
        raise FileNotFoundError(f"No results file found in {campaign_dir}")

    with open(results_file, 'r') as f:
        return json.load(f)

def analyse_campaign(campaign_dir: Path) -> Dict[str, Any]:
    """
    Analyse all simulations in a campaign directory.

    Returns aggregated summary statistics.
    """
    print(f"Analysing campaign: {campaign_dir}")
    print("="*70)

    # Load basic results
    basic_results = load_campaign_results(campaign_dir)
    print(f"Loaded {len(basic_results)} simulation results")

    # Determine campaign type
    campaign_dir = Path(campaign_dir)
    if "ctzm_perp" in str(campaign_dir).lower():
        campaign_type = "CTZM_PERP"
    elif "eos" in str(campaign_dir).lower():
        campaign_type = "EOS_SENSITIVITY"
    elif "turb" in str(campaign_dir).lower():
        campaign_type = "TURB_AMPLITUDE"
    else:
        campaign_type = "UNKNOWN"

    # Analyse each simulation
    analysed_results = []
    n_analysed = 0
    n_failed = 0

    for result in basic_results:
        run_id = result["run_id"]
        output_path = Path(result.get("output_dir", ""))

        if not output_path.exists():
            print(f"  [SKIP] {run_id}: output directory not found")
            result["analysis"] = {
                "classification": "NO_OUTPUT_DIR",
                "lw_mean": None,
                "lw_std": None,
            }
            analysed_results.append(result)
            n_failed += 1
            continue

        try:
            analysis = analyse_single_simulation(output_path, run_id)
            result["analysis"] = analysis
            result["lw_mean"] = analysis["lw_mean"]
            result["lw_std"] = analysis["lw_std"]
            result["classification"] = analysis["classification"]

            lw_str = f"λ/W={analysis['lw_mean']:.2f}±{analysis['lw_std']:.2f}" if analysis['lw_mean'] else "No λ/W"
            print(f"  [{n_analysed+1:3d}/{len(basic_results)}] {run_id}: {analysis['classification']} {lw_str}")

            analysed_results.append(result)
            n_analysed += 1

        except Exception as e:
            print(f"  [ERROR] {run_id}: {e}")
            result["analysis"] = {
                "classification": "ANALYSIS_ERROR",
                "error": str(e),
                "lw_mean": None,
                "lw_std": None,
            }
            analysed_results.append(result)
            n_failed += 1

    print(f"\nAnalysis complete:")
    print(f"  Analysed: {n_analysed}")
    print(f"  Failed: {n_failed}")
    print(f"  Total: {len(analysed_results)}")

    # Generate summary statistics
    summary = generate_summary(analysed_results, campaign_type)

    # Save analysed results
    analysed_file = campaign_dir / f"{campaign_type.lower()}_analysed.json"
    analysed_file.write_text(json.dumps(analysed_results, indent=2))

    # Save summary
    summary_file = campaign_dir / f"{campaign_type.lower()}_summary.json"
    summary_file.write_text(json.dumps(summary, indent=2))

    print(f"\nResults saved:")
    print(f"  Analysed: {analysed_file}")
    print(f"  Summary: {summary_file}")

    # Generate figures
    generate_figures(analysed_results, summary, campaign_type, campaign_dir)

    return summary

def generate_summary(results: List[Dict[str, Any]], campaign_type: str) -> Dict[str, Any]:
    """Generate aggregated summary statistics."""
    n_total = len(results)
    n_frag = sum(1 for r in results if r["outcome"] == "FRAG")
    n_timeout = sum(1 for r in results if r["outcome"] == "TIMEOUT")
    n_fail = sum(1 for r in results if r["outcome"] == "FAILED" or "ERROR" in r.get("outcome", ""))

    n_beading = sum(1 for r in results if "BEADING" in r.get("classification", ""))
    n_radial = sum(1 for r in results if "RADIAL" in r.get("classification", ""))

    lw_vals = [r["lw_mean"] for r in results if r.get("lw_mean")]
    lw_mean = float(np.mean(lw_vals)) if lw_vals else None
    lw_std = float(np.std(lw_vals)) if lw_vals else None

    summary = {
        "campaign_type": campaign_type,
        "n_total": n_total,
        "n_frag": n_frag,
        "n_timeout": n_timeout,
        "n_fail": n_fail,
        "n_beading": n_beading,
        "n_radial_collapse": n_radial,
        "lw_mean_over_all": lw_mean,
        "lw_std_over_all": lw_std,
        "n_with_lw_measurement": len(lw_vals),
    }

    # Campaign-specific statistics
    if campaign_type == "CTZM_PERP":
        summary["ctzm_stats"] = generate_ctzm_stats(results)
    elif campaign_type == "EOS_SENSITIVITY":
        summary["eos_stats"] = generate_eos_stats(results)
    elif campaign_type == "TURB_AMPLITUDE":
        summary["turb_stats"] = generate_turb_stats(results)

    return summary

def generate_ctzm_stats(results: List[Dict[str, Any]]) -> Dict[str, Any]:
    """Generate CTZM-specific statistics (λ/W vs f for each β)."""
    stats = {}

    for f in [1.2, 1.3, 1.4, 1.5]:
        for beta in [0.3, 0.5, 1.0, 2.0]:
            key = f"f{f:.1f}_b{beta:.1f}"
            subset = [r for r in results
                     if r.get("f") == f and r.get("beta") == beta
                     and r.get("lw_mean")]

            if subset:
                lw_vals = [r["lw_mean"] for r in subset]
                lw_errors = [r.get("lw_std", 0) for r in subset]

                stats[key] = {
                    "lw_mean": float(np.mean(lw_vals)),
                    "lw_std": float(np.std(lw_vals)),
                    "lw_sem": float(np.std(lw_vals) / np.sqrt(len(lw_vals))),
                    "n": len(lw_vals),
                }

    return stats

def generate_eos_stats(results: List[Dict[str, Any]]) -> Dict[str, Any]:
    """Generate EOS-specific statistics (λ/W vs γ)."""
    stats = {}

    for gamma in [0.7, 0.8, 0.9, 1.0]:
        subset = [r for r in results if r.get("gamma") == gamma and r.get("lw_mean")]

        if subset:
            lw_vals = [r["lw_mean"] for r in subset]
            stats[f"g{gamma:.1f}"] = {
                "lw_mean": float(np.mean(lw_vals)),
                "lw_std": float(np.std(lw_vals)),
                "n": len(lw_vals),
            }

    # Test for γ-dependence
    gamma_means = [stats[f"g{g:.1f}"]["lw_mean"] for g in [0.7, 0.8, 0.9, 1.0]
    gamma_dependence = {
        "min_lw": min(g for g in gamma_means if g),
        "max_lw": max(g for g in gamma_means if g),
        "variation_percent": ((max(g for g in gamma_means if g) - min(g for g in gamma_means if g)) / np.mean(gamma_means) * 100) if gamma_means else None,
    }
    stats["gamma_dependence"] = gamma_dependence

    return stats

def generate_turb_stats(results: List[Dict[str, Any]]) -> Dict[str, Any]:
    """Generate turbulence-specific statistics (λ/W vs amplitude)."""
    stats = {}

    for ampl in [1e-4, 1e-3, 1e-2, 1e-1, 1.0]:
        subset = [r for r in results if abs(r.get("ampl", 0) - ampl) < 1e-6 and r.get("lw_mean")]

        if subset:
            lw_vals = [r["lw_mean"] for r in subset]
            a_str = f"{ampl:.0e}"
            stats[a_str] = {
                "lw_mean": float(np.mean(lw_vals)),
                "lw_std": float(np.std(lw_vals)),
                "n": len(lw_vals),
            }

    return stats

def generate_figures(results: List[Dict[str, Any]], summary: Dict[str, Any],
                     campaign_type: str, output_dir: Path):
    """Generate diagnostic figures for the campaign."""
    fig_dir = output_dir / "figures"
    fig_dir.mkdir(exist_ok=True)

    print(f"\nGenerating figures in {fig_dir}...")

    # Figure 1: Classification summary
    fig, ax = plt.subplots(figsize=(8, 6))
    classifications = {}
    for r in results:
        c = r.get("classification", "UNKNOWN")
        classifications[c] = classifications.get(c, 0) + 1

    ax.bar(classifications.keys(), classifications.values())
    ax.set_ylabel('Number of Simulations')
    ax.set_title(f'{campaign_type}: Classification Summary')
    plt.xticks(rotation=45)
    plt.tight_layout()
    plt.savefig(fig_dir / f"{campaign_type.lower()}_classifications.png", dpi=150)
    plt.close()

    # Figure 2: λ/W distribution for beading simulations
    lw_vals = [r["lw_mean"] for r in results if r.get("lw_mean")]
    if lw_vals:
        fig, ax = plt.subplots(figsize=(8, 6))
        ax.hist(lw_vals, bins=20, edgecolor='black')
        ax.set_xlabel('λ/W')
        ax.set_ylabel('Number of Simulations')
        ax.set_title(f'{campaign_type}: λ/W Distribution (N={len(lw_vals)})')
        ax.axvline(np.mean(lw_vals), color='red', linestyle='--', label=f'Mean: {np.mean(lw_vals):.2f}')
        ax.legend()
        plt.tight_layout()
        plt.savefig(fig_dir / f"{campaign_type.lower()}_lw_distribution.png", dpi=150)
        plt.close()

    # Campaign-specific figures
    if campaign_type == "CTZM_PERP":
        generate_ctzm_figures(results, fig_dir)
    elif campaign_type == "EOS_SENSITIVITY":
        generate_eos_figures(results, fig_dir)
    elif campaign_type == "TURB_AMPLITUDE":
        generate_turb_figures(results, fig_dir)

    print(f"  Figures saved: {len(list(fig_dir.glob('*.png')))}")

def generate_ctzm_figures(results: List[Dict[str, Any]], fig_dir: Path):
    """Generate CTZM-specific figures."""
    fig, axes = plt.subplots(2, 2, figsize=(14, 10))
    axes = axes.flatten()

    beta_values = [0.3, 0.5, 1.0, 2.0]
    colors = ['blue', 'green', 'orange', 'red']

    for i, (beta, color) in enumerate(zip(beta_values, colors)):
        ax = axes[i]

        f_vals = []
        lw_means = []
        lw_stds = []

        for f in [1.2, 1.3, 1.4, 1.5]:
            subset = [r for r in results
                     if r.get("f") == f and r.get("beta") == beta
                     and r.get("lw_mean")]

            if subset:
                lw_vals = [r["lw_mean"] for r in subset]
                f_vals.append(f)
                lw_means.append(np.mean(lw_vals))
                lw_stds.append(np.std(lw_vals))

        if f_vals:
            ax.errorbar(f_vals, lw_means, yerr=lw_stds, marker='o', linestyle='-', color=color)
            ax.set_xlabel('Line-mass fraction f')
            ax.set_ylabel('λ/W')
            ax.set_title(f'β = {beta}')
            ax.grid(True, alpha=0.3)

            # Linear fit
            if len(f_vals) > 2:
                coeffs = np.polyfit(f_vals, lw_means, 1)
                r2 = np.corrcoef(f_vals, lw_means)[0,1]**2
                ax.text(0.05, 0.95, f'Slope: {coeffs[0]:.2f}\n$R^2$: {r2:.2f}',
                       transform=ax.transAxes, verticalalignment='top')

    plt.suptitle('CTZM_PERP: λ/W vs f for different β values')
    plt.tight_layout()
    plt.savefig(fig_dir / "ctzm_perp_lw_vs_f.png", dpi=150)
    plt.close()

def generate_eos_figures(results: List[Dict[str, Any]], fig_dir: Path):
    """Generate EOS-specific figures."""
    fig, ax = plt.subplots(figsize=(10, 6))

    gamma_vals = []
    lw_means = []
    lw_stds = []

    for gamma in [0.7, 0.8, 0.9, 1.0]:
        subset = [r for r in results if r.get("gamma") == gamma and r.get("lw_mean")]

        if subset:
            lw_vals = [r["lw_mean"] for r in subset]
            gamma_vals.append(gamma)
            lw_means.append(np.mean(lw_vals))
            lw_stds.append(np.std(lw_vals))

    if gamma_vals:
        ax.errorbar(gamma_vals, lw_means, yerr=lw_stds, marker='o', linestyle='-', capsize=5)
        ax.set_xlabel('Adiabatic index γ')
        ax.set_ylabel('λ/W')
        ax.set_title('EOS_SENSITIVITY: λ/W vs γ')
        ax.grid(True, alpha=0.3)
        ax.invert_xaxis()  # γ decreases from left to right

    plt.tight_layout()
    plt.savefig(fig_dir / "eos_sensitivity_lw_vs_gamma.png", dpi=150)
    plt.close()

def generate_turb_figures(results: List[Dict[str, Any]], fig_dir: Path):
    """Generate turbulence-specific figures."""
    fig, ax = plt.subplots(figsize=(10, 6))

    ampl_vals = []
    lw_means = []
    lw_stds = []

    for ampl in [1e-4, 1e-3, 1e-2, 1e-1, 1.0]:
        subset = [r for r in results if abs(r.get("ampl", 0) - ampl) < 1e-6 and r.get("lw_mean")]

        if subset:
            lw_vals = [r["lw_mean"] for r in subset]
            ampl_vals.append(ampl)
            lw_means.append(np.mean(lw_vals))
            lw_stds.append(np.std(lw_vals))

    if ampl_vals:
        ax.errorbar(ampl_vals, lw_means, yerr=lw_stds, marker='o', linestyle='-', capsize=5)
        ax.set_xscale('log')
        ax.set_xlabel('Perturbation Amplitude')
        ax.set_ylabel('λ/W')
        ax.set_title('TURB_AMPLITUDE: λ/W vs Turbulence Amplitude')
        ax.grid(True, alpha=0.3)

    plt.tight_layout()
    plt.savefig(fig_dir / "turb_amplitude_lw_vs_ampl.png", dpi=150)
    plt.close()

def main():
    parser = argparse.ArgumentParser(description='Analyse referee response campaign results')
    parser.add_argument('campaign_dir', type=str, help='Path to campaign directory')
    args = parser.parse_args()

    campaign_dir = Path(args.campaign_dir)

    if not campaign_dir.exists():
        print(f"Error: Campaign directory not found: {campaign_dir}")
        sys.exit(1)

    summary = analyse_campaign(campaign_dir)

    print("\n" + "="*70)
    print("ANALYSIS SUMMARY")
    print("="*70)
    print(f"Campaign: {summary['campaign_type']}")
    print(f"Total simulations: {summary['n_total']}")
    print(f"Fragmented: {summary['n_frag']} ({summary['n_frag']/summary['n_total']*100:.1f}%)")
    print(f"Timeout: {summary['n_timeout']}")
    print(f"Failed: {summary['n_fail']}")
    print(f"Beading: {summary['n_beading']}")
    print(f"Radial collapse: {summary['n_radial_collapse']}")
    print(f"λ/W measurements: {summary['n_with_lw_measurement']}")

    if summary['lw_mean_over_all']:
        print(f"Mean λ/W: {summary['lw_mean_over_all']:.2f} ± {summary['lw_std_over_all']:.2f}")

    print("\nNext step: Transfer results back to local machine")
    print(f"  scp -r {campaign_dir} user@local:/path/to/destination")

if __name__ == "__main__":
    main()
