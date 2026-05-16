#!/usr/bin/env python3
"""
Non-Ideal MHD Campaign Analysis Script
Analyzes results from ambipolar diffusion simulations
"""

import json
import numpy as np
import matplotlib.pyplot as plt
import matplotlib
matplotlib.use('Agg')
import h5py
from pathlib import Path
from scipy.signal import find_peaks
from typing import Dict, List, Tuple, Optional
import logging

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# ============================================================================
# Data Loading
# ============================================================================

def load_results(results_path: Path) -> Dict:
    """Load simulation results from JSON file."""
    with open(results_path, 'r') as f:
        data = json.load(f)
    return data

# ============================================================================
# HDF5 Data Analysis
# ============================================================================

def load_density_profile(sim_dir: Path, timestamp: float) -> np.ndarray:
    """
    Load axial density profile from HDF5 snapshot.

    Parameters
    ----------
    sim_dir : Path
        Simulation directory
    timestamp : float
        Snapshot timestamp to load

    Returns
    -------
    rho_x1 : np.ndarray
        Density profile along filament axis
    """
    # Find HDF5 file for this timestamp
    h5_files = list(sim_dir.glob(f"*.h5"))

    if not h5_files:
        logger.warning(f"No HDF5 files found in {sim_dir}")
        return None

    # Load the file closest to the requested timestamp
    h5_file = h5_files[0]

    try:
        with h5py.File(h5_file, 'r') as f:
            # Get density field
            # Shape: (nx1, nx2, nx3)
            rho = f['dens'][-1]  # Last timestamp

            # Extract axial profile at center
            ny, nz = rho.shape[1], rho.shape[2]
            rho_x1 = rho[:, ny//2, nz//2]

            return rho_x1

    except Exception as e:
        logger.error(f"Error loading {h5_file}: {e}")
        return None

def detect_longitudinal_peaks(rho_x1: np.ndarray, dx: float = 8.0/256) -> Tuple[np.ndarray, Dict]:
    """
    Detect peaks in axial density profile.

    Parameters
    ----------
    rho_x1 : np.ndarray
        Axial density profile
    dx : float
        Grid spacing in code units

    Returns
    -------
    peaks : np.ndarray
        Peak indices
    properties : dict
        Peak properties
    """
    if rho_x1 is None or len(rho_x1) == 0:
        return np.array([]), {}

    # Normalize density
    rho_norm = rho_x1 / rho_x1.mean()

    # Find peaks with prominence threshold
    peaks, properties = find_peaks(
        rho_norm,
        prominence=0.15,  # 15% above mean
        distance=int(1.0 / dx),  # Minimum spacing of 1 lambda_J
        width=int(0.5 / dx)  # Minimum width of 0.5 lambda_J
    )

    return peaks, properties

def calculate_lambda_W(peaks: np.ndarray, dx: float, W: float = 0.3) -> Optional[float]:
    """
    Calculate fragmentation spacing normalized by filament width.

    Parameters
    ----------
    peaks : np.ndarray
        Peak indices
    dx : float
        Grid spacing in code units
    W : float
        Filament core width in code units

    Returns
    -------
    lambda_W : float or None
        Fragmentation spacing λ/W
    """
    if len(peaks) < 2:
        return None

    # Calculate wavelength in code units
    wavelengths = np.diff(peaks) * dx

    # Mean wavelength
    lambda_mean = np.mean(wavelengths)

    # Normalize by filament width
    lambda_W = lambda_mean / (2 * np.pi * W)

    return lambda_W

# ============================================================================
# Figure Generation
# ============================================================================

def generate_figures(results: Dict, output_dir: Path) -> None:
    """Generate all analysis figures."""

    # Create output directory
    fig_dir = output_dir / "figures"
    fig_dir.mkdir(parents=True, exist_ok=True)

    # Figure 1: λ/W vs Am for different f values
    fig_lambda_vs_am(results, fig_dir)

    # Figure 2: Timescale comparison
    fig_timescales(results, fig_dir)

    # Figure 3: Detection rate vs Am
    fig_detection_rate(results, fig_dir)

    # Figure 4: Sample density profiles
    fig_density_profiles(results, fig_dir)

    logger.info(f"Figures saved to {fig_dir}")

def fig_lambda_vs_am(results: Dict, output_dir: Path) -> None:
    """Plot λ/W vs Am for different line mass fractions."""

    fig, axes = plt.subplots(1, 3, figsize=(15, 5), sharey=True)

    f_values = [1.5, 2.0, 2.5]
    Am_values = sorted(set(
        r["params"]["ambipolar_number_Am"]
        for r in results["results"].values()
        if r["status"] == "COMPLETE"
    ))

    colors = plt.cm.viridis(np.linspace(0, 1, len(Am_values)))

    for idx, f in enumerate(f_values):
        ax = axes[idx]

        lambda_W_values = []
        lambda_W_errors = []
        Am_plot = []

        for Am in Am_values:
            # Get all simulations with this f and Am
            matching = [
                r for r in results["results"].values()
                if (r["status"] == "COMPLETE" and
                    r["params"]["line_mass_fraction"] == f and
                    r["params"]["ambipolar_number_Am"] == Am)
            ]

            if matching:
                # Analyze each simulation
                lambdas = []
                for result in matching:
                    sim_dir = Path(result.get("sim_dir", ""))
                    if sim_dir.exists():
                        rho_x1 = load_density_profile(sim_dir, 2.0)
                        peaks, _ = detect_longitudinal_peaks(rho_x1)

                        if len(peaks) >= 2:
                            lambda_W = calculate_lambda_W(peaks, 8.0/256)
                            if lambda_W is not None:
                                lambdas.append(lambda_W)

                if lambdas:
                    lambda_W_values.append(np.mean(lambdas))
                    lambda_W_errors.append(np.std(lambdas))
                    Am_plot.append(Am)

        if lambda_W_values:
            ax.errorbar(Am_plot, lambda_W_values, yerr=lambda_W_errors,
                       marker='o', linestyle='-', capsize=5, markersize=8,
                       color='steelblue', linewidth=2)

        # Add reference lines
        ax.axhline(y=3.70, color='r', linestyle='--', alpha=0.5,
                  label='Near-critical calibration')
        ax.axhline(y=2.84, color='g', linestyle='--', alpha=0.5,
                  label='HGBS observation')

        ax.set_xlabel('Ambipolar Number $Am$')
        ax.set_ylabel(r'$\lambda/W$')
        ax.set_title(f'$f = {f}$')
        ax.legend()
        ax.grid(True, alpha=0.3)
        ax.set_xscale('log')
        ax.set_ylim([0, 6])

    plt.tight_layout()
    plt.savefig(output_dir / 'fig_lambda_vs_Am.pdf', dpi=300, bbox_inches='tight')
    plt.savefig(output_dir / 'fig_lambda_vs_Am.png', dpi=300, bbox_inches='tight')
    plt.close()

def fig_timescales(results: Dict, output_dir: Path) -> None:
    """Plot radial collapse vs longitudinal growth timescales."""

    fig, ax = plt.subplots(figsize=(10, 6))

    for Am in sorted(set(
        r["params"]["ambipolar_number_Am"]
        for r in results["results"].values()
    )):
        matching = [
            r for r in results["results"].values()
            if (r["status"] == "COMPLETE" and
                r["params"]["ambipolar_number_Am"] == Am)
        ]

        if matching:
            t_frags = [r["t_frag"] for r in matching if r["t_frag"] is not None]

            if t_frags:
                ax.scatter([Am] * len(t_frags), t_frags, alpha=0.6, s=50,
                          label=f'$Am = {Am}$')

    ax.set_xlabel('Ambipolar Number $Am$')
    ax.set_ylabel(r'$t_{\rm frag}$ ($t_{\rm J}$)')
    ax.set_title('Fragmentation Time vs Ambipolar Diffusion Strength')
    ax.legend()
    ax.grid(True, alpha=0.3)
    ax.set_xscale('log')

    plt.tight_layout()
    plt.savefig(output_dir / 'fig_timescales.pdf', dpi=300, bbox_inches='tight')
    plt.close()

def fig_detection_rate(results: Dict, output_dir: Path) -> None:
    """Plot longitudinal structure detection rate vs Am."""

    fig, ax = plt.subplots(figsize=(10, 6))

    Am_values = sorted(set(
        r["params"]["ambipolar_number_Am"]
        for r in results["results"].values()
    ))

    detection_rates = []

    for Am in Am_values:
        matching = [
            r for r in results["results"].values()
            if (r["status"] == "COMPLETE" and
                r["params"]["ambipolar_number_Am"] == Am)
        ]

        if matching:
            detected = 0
            for result in matching:
                # Check if longitudinal peaks were detected
                if result.get("longitudinal_peaks", 0) >= 2:
                    detected += 1

            rate = 100 * detected / len(matching)
            detection_rates.append(rate)

    ax.bar(range(len(Am_values)), detection_rates,
           tick_label=[f'{Am:.1f}' for Am in Am_values],
           alpha=0.7, color='steelblue')

    ax.axhline(y=50, color='r', linestyle='--', alpha=0.5,
              label='50% threshold')

    ax.set_xlabel('Ambipolar Number $Am$')
    ax.set_ylabel('Detection Rate (%)')
    ax.set_title('Longitudinal Structure Detection Rate vs Am')
    ax.legend()
    ax.grid(True, alpha=0.3, axis='y')
    ax.set_ylim([0, 105])

    plt.tight_layout()
    plt.savefig(output_dir / 'fig_detection_rate.pdf', dpi=300, bbox_inches='tight')
    plt.close()

def fig_density_profiles(results: Dict, output_dir: Path) -> None:
    """Plot sample density profiles showing longitudinal structure."""

    fig, axes = plt.subplots(2, 2, figsize=(12, 10))

    # Select representative cases
    cases = [
        {"f": 1.5, "Am": 0.0},
        {"f": 1.5, "Am": 1.0},
        {"f": 2.0, "Am": 0.0},
        {"f": 2.0, "Am": 1.0},
    ]

    for idx, (ax, case) in enumerate(zip(axes.flat, cases)):
        # Find matching simulation
        matching = [
            r for r in results["results"].values()
            if (r["status"] == "COMPLETE" and
                r["params"]["line_mass_fraction"] == case["f"] and
                r["params"]["ambipolar_number_Am"] == case["Am"])
        ]

        if matching and len(matching) > 0:
            result = matching[0]
            sim_dir = Path(result.get("sim_dir", ""))

            if sim_dir.exists():
                rho_x1 = load_density_profile(sim_dir, 2.0)

                if rho_x1 is not None:
                    x = np.linspace(-4, 4, len(rho_x1))

                    ax.plot(x, rho_x1 / rho_x1.mean(), linewidth=2)

                    # Detect and mark peaks
                    peaks, _ = detect_longitudinal_peaks(rho_x1)
                    if len(peaks) > 0:
                        ax.plot(x[peaks], rho_x1[peaks] / rho_x1.mean(),
                               'ro', markersize=8)

        ax.set_xlabel(r'$x/\lambda_J$')
        ax.set_ylabel(r'$\rho/\langle\rho\rangle$')
        ax.set_title(f"$f = {case['f']}$, $Am = {case['Am']}$")
        ax.grid(True, alpha=0.3)

    plt.tight_layout()
    plt.savefig(output_dir / 'fig_density_profiles.pdf', dpi=300, bbox_inches='tight')
    plt.close()

# ============================================================================
# Table Generation
# ============================================================================

def generate_tables(results: Dict, output_dir: Path) -> None:
    """Generate LaTeX tables for paper integration."""

    table_dir = output_dir / "tables"
    table_dir.mkdir(parents=True, exist_ok=True)

    # Table 1: Summary of λ/W measurements
    table_lambda_W(results, table_dir)

    logger.info(f"Tables saved to {table_dir}")

def table_lambda_W(results: Dict, output_dir: Path) -> None:
    """Generate LaTeX table of λ/W measurements."""

    table_file = output_dir / "table_lambda_W.tex"

    with open(table_file, 'w') as f:
        f.write(r'''\begin{table}[h]
\caption{Fragmentation Spacing Measurements from Non-Ideal MHD Simulations}
\begin{tabular}{cccccc}
\toprule
''' )
        f.write(r'$f$ & $Am$ & $\lambda/W$ & Std Dev & $N_{\rm peaks}$ \\' + '\n')
        f.write(r'\midrule' + '\n')

        for f in [1.5, 2.0, 2.5]:
            for Am in [0.0, 0.5, 1.0, 2.0]:
                matching = [
                    r for r in results["results"].values()
                    if (r["status"] == "COMPLETE" and
                        r["params"]["line_mass_fraction"] == f and
                        r["params"]["ambipolar_number_Am"] == Am)
                ]

                if matching:
                    # Compute statistics
                    lambdas = []
                    n_peaks_list = []

                    for result in matching:
                        lambdas.append(result.get("lambda_W", np.nan))
                        n_peaks_list.append(result.get("longitudinal_peaks", 0))

                    if lambdas:
                        mean_lambda = np.nanmean(lambdas)
                        std_lambda = np.nanstd(lambdas)
                        mean_npeaks = np.nanmean(n_peaks_list)

                        if not np.isnan(mean_lambda):
                            f.write(f'{f} & {Am} & {mean_lambda:.2f} & {std_lambda:.2f} & {mean_npeaks:.0f} \\\\\n')
                        else:
                            f.write(f'{f} & {Am} & -- & -- & {mean_npeaks:.0f} \\\\\n')
                    else:
                        f.write(f'{f} & {Am} & -- & -- & -- \\\\\n')

        f.write(r'''\bottomrule
\end{tabular}
\end{table}
''')

# ============================================================================
# Summary Report
# ============================================================================

def generate_summary_report(results: Dict, output_dir: Path) -> None:
    """Generate text summary of findings."""

    summary_file = output_dir / "summary.txt"

    with open(summary_file, 'w') as f:
        f.write("="*70 + "\n")
        f.write("NON-IDEAL MHD CAMPAIGN SUMMARY\n")
        f.write("="*70 + "\n\n")

        f.write(f"Campaign: {results['campaign_config']['campaign_name']}\n")
        f.write(f"Date: {results['end_time']}\n")
        f.write(f"Duration: {results['duration_hours']:.2f} hours\n\n")

        # Status summary
        f.write("SIMULATION STATUS\n")
        f.write("-"*70 + "\n")
        for status, count in results["summary"]["status_counts"].items():
            f.write(f"  {status}: {count}\n")
        f.write(f"\nSuccess rate: {results['summary']['success_rate']:.1f}%\n\n")

        # Key findings
        f.write("KEY FINDINGS\n")
        f.write("-"*70 + "\n")

        # Check if longitudinal structure was detected
        detected = sum(1 for r in results["results"].values()
                      if r.get("longitudinal_peaks", 0) >= 2)
        total_complete = results["summary"]["status_counts"].get("COMPLETE", 0)

        f.write(f"\n1. Longitudinal structure detection:\n")
        f.write(f"   {detected}/{total_complete} simulations showed longitudinal beading\n")

        if detected > 0:
            # Get λ/W measurements
            lambdas = [r.get("lambda_W") for r in results["results"].values()
                      if r.get("lambda_W") is not None]

            if lambdas:
                f.write(f"\n2. Fragmentation spacing measurements:\n")
                f.write(f"   Mean λ/W = {np.mean(lambdas):.2f} ± {np.std(lambdas):.2f}\n")
                f.write(f"   Range: [{np.min(lambdas):.2f}, {np.max(lambdas):.2f}]\n")

                # Compare with references
                f.write(f"\n3. Comparison with reference values:\n")
                f.write(f"   Near-critical calibration: 3.70 ± 0.40\n")
                f.write(f"   HGBS observation: 2.84 ± 0.12\n")
                f.write(f"   This campaign: {np.mean(lambdas):.2f} ± {np.std(lambdas):.2f}\n")

                # Am threshold analysis
                f.write(f"\n4. Ambipolar diffusion threshold:\n")
                for Am in [0.0, 0.5, 1.0, 2.0]:
                    matching = [r for r in results["results"].values()
                               if (r["params"]["ambipolar_number_Am"] == Am and
                                   r.get("longitudinal_peaks", 0) >= 2)]
                    rate = 100 * len(matching) / max(1, len([
                        r for r in results["results"].values()
                        if r["params"]["ambipolar_number_Am"] == Am
                    ]))
                    f.write(f"   Am = {Am}: {rate:.0f}% detection rate\n")

        f.write("\n" + "="*70 + "\n")

    logger.info(f"Summary report saved to {summary_file}")

# ============================================================================
# Main Analysis
# ============================================================================

def main():
    """Main analysis entry point."""

    # Load results
    results_path = Path("/data/non_ideal_mhd_runs/results.json")

    if not results_path.exists():
        logger.error(f"Results file not found: {results_path}")
        logger.info("Please run the simulation campaign first using run_campaign.py")
        return

    logger.info(f"Loading results from {results_path}")
    results = load_results(results_path)

    # Create output directory
    output_dir = Path("expected_output")
    output_dir.mkdir(exist_ok=True)

    # Analyze HDF5 data
    logger.info("Analyzing HDF5 data...")
    analyze_hdf5_data(results, Path("/data/non_ideal_mhd_runs/"))

    # Generate figures
    logger.info("Generating figures...")
    generate_figures(results, output_dir)

    # Generate tables
    logger.info("Generating tables...")
    generate_tables(results, output_dir)

    # Generate summary report
    logger.info("Generating summary report...")
    generate_summary_report(results, output_dir)

    # Save analyzed results
    analyzed_file = output_dir / "analyzed_results.json"
    with open(analyzed_file, 'w') as f:
        json.dump(results, f, indent=2, default=str)

    logger.info("Analysis complete!")

def analyze_hdf5_data(results: Dict, data_dir: Path) -> None:
    """Analyze HDF5 output files for longitudinal structure."""

    for sim_id, result in results["results"].items():
        if result["status"] != "COMPLETE":
            continue

        sim_dir = data_dir / sim_id

        if not sim_dir.exists():
            continue

        # Load density profile at final timestamp
        rho_x1 = load_density_profile(sim_dir, 2.0)

        if rho_x1 is not None:
            # Detect peaks
            peaks, properties = detect_longitudinal_peaks(rho_x1)

            # Store results
            result["longitudinal_peaks"] = len(peaks)
            result["sim_dir"] = str(sim_dir)

            if len(peaks) >= 2:
                lambda_W = calculate_lambda_W(peaks, 8.0/256)
                result["lambda_W"] = lambda_W

                logger.info(f"{sim_id}: {len(peaks)} peaks detected, λ/W = {lambda_W:.2f}")
            else:
                result["lambda_W"] = None
                logger.info(f"{sim_id}: {len(peaks)} peaks detected (no λ/W measurement)")

if __name__ == "__main__":
    main()
