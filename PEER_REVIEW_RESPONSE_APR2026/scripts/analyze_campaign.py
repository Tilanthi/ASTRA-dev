#!/usr/bin/env python3
"""
Analysis script for filament spacing peer review response campaign.

This script analyzes simulation outputs, extracts fragmentation metrics,
and generates figures for paper integration.

Author: ASTRA System
Date: 2026-04-23
"""

import os
import sys
import json
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from pathlib import Path
from typing import Dict, List, Optional, Tuple
from scipy import signal
from scipy.optimize import curve_fit

# Try to import h5py for HDF5 analysis
try:
    import h5py
    HAS_H5PY = True
except ImportError:
    HAS_H5PY = False
    print("WARNING: h5py not installed. HDF5 analysis will be limited.")

# ==============================================================================
# Configuration
# ==============================================================================

# Paths
SCRIPT_DIR = Path(__file__).parent
PROJECT_ROOT = SCRIPT_DIR.parent
CONFIG_DIR = PROJECT_ROOT / "config"
STATUS_DIR = PROJECT_ROOT / "status"
RUNS_DIR = PROJECT_ROOT / "runs"
ANALYSIS_OUTPUT_DIR = PROJECT_ROOT / "analysis_output"

# Analysis parameters
PEAK_PROMINENCE = 0.1  # Minimum peak prominence for detection
MIN_PEAKS = 2  # Minimum number of peaks for fragmentation classification

# ==============================================================================
# Utility Functions
# ==============================================================================

def setup_directories():
    """Create analysis output directory."""
    ANALYSIS_OUTPUT_DIR.mkdir(exist_ok=True)


def load_status_files() -> pd.DataFrame:
    """Load all status JSON files into a DataFrame."""
    status_files = list(STATUS_DIR.glob("*.json"))

    if not status_files:
        print("WARNING: No status files found in status/ directory")
        return pd.DataFrame()

    records = []
    for status_file in status_files:
        try:
            with open(status_file, 'r') as f:
                data = json.load(f)
                records.append(data)
        except:
            pass

    df = pd.DataFrame(records)
    return df


def load_manifest() -> pd.DataFrame:
    """Load simulation manifest."""
    manifest_file = CONFIG_DIR / "simulation_manifest.json"

    with open(manifest_file, 'r') as f:
        manifest = json.load(f)

    return pd.DataFrame(manifest)


# ==============================================================================
# Peak Detection from HDF5
# ==============================================================================

def detect_longitudinal_peaks(hdf5_file: Path) -> Dict:
    """
    Detect longitudinal density peaks from HDF5 snapshot.

    Parameters
    ----------
    hdf5_file : Path
        Path to HDF5 snapshot file

    Returns
    -------
    dict
        Peak detection results
    """
    if not HAS_H5PY:
        return {
            'n_peaks': 0,
            'peak_positions': [],
            'peak_amplitudes': [],
            'lambda_frag': None,
            'quality': 'none'
        }

    try:
        with h5py.File(hdf5_file, 'r') as f:
            # Extract density along filament axis (x1 direction)
            # Assuming cylindrical filament along x1
            rho = f['dens'][:]

            # Compute density profile along filament axis
            # Average over transverse directions (x2, x3)
            rho_x1 = np.mean(rho, axis=(1, 2))

            # Normalize
            rho_x1_norm = (rho_x1 - np.min(rho_x1)) / (np.max(rho_x1) - np.min(rho_x1))

            # Detect peaks
            peaks, properties = signal.find_peaks(
                rho_x1_norm,
                prominence=PEAK_PROMINENCE
            )

            # Extract peak properties
            peak_positions = peaks.tolist()
            peak_amplitudes = rho_x1_norm[peaks].tolist()

            # Calculate fragmentation spacing
            n_peaks = len(peaks)

            if n_peaks >= 2:
                # Calculate peak-to-peak spacings
                spacings = np.diff(peak_positions)
                lambda_frag = np.mean(spacings)
                lambda_frag_std = np.std(spacings)

                # Quality metric
                quality = evaluate_peak_quality(rho_x1_norm, peaks)
            else:
                lambda_frag = None
                lambda_frag_std = None
                quality = 'none'

            return {
                'n_peaks': n_peaks,
                'peak_positions': peak_positions,
                'peak_amplitudes': peak_amplitudes,
                'lambda_frag': lambda_frag,
                'lambda_frag_std': lambda_frag_std,
                'quality': quality
            }

    except Exception as e:
        print(f"ERROR analyzing {hdf5_file}: {e}")
        return {
            'n_peaks': 0,
            'peak_positions': [],
            'peak_amplitudes': [],
            'lambda_frag': None,
            'quality': 'error'
        }


def evaluate_peak_quality(profile: np.ndarray, peaks: np.ndarray) -> str:
    """
    Evaluate the quality of longitudinal peak detection.

    Parameters
    ----------
    profile : np.ndarray
        Normalized density profile along filament axis
    peaks : np.ndarray
        Detected peak positions

    Returns
    -------
    str
        Quality label: 'excellent', 'good', 'marginal', or 'none'
    """
    n_peaks = len(peaks)

    if n_peaks < 2:
        return 'none'

    # Calculate contrast
    peak_amplitudes = profile[peaks]
    trough_amplitudes = np.percentile(profile, 10)

    contrast = np.mean(peak_amplitudes) - trough_amplitudes

    # Calculate regularity of spacing
    if n_peaks >= 3:
        spacings = np.diff(peaks)
        regularity = 1.0 - np.std(spacings) / np.mean(spacings)
    else:
        regularity = 0.5  # Can't assess with only 2 peaks

    # Quality criteria
    if contrast > 0.5 and regularity > 0.8:
        return 'excellent'
    elif contrast > 0.3 and regularity > 0.6:
        return 'good'
    elif contrast > 0.15 and regularity > 0.4:
        return 'marginal'
    else:
        return 'none'


def analyze_simulation_hdf5(sim_id: str, phase: int) -> Dict:
    """
    Analyze HDF5 outputs for a single simulation.

    Parameters
    ----------
    sim_id : str
        Simulation ID
    phase : int
        Campaign phase

    Returns
    -------
    dict
        Analysis results
    """
    sim_dir = RUNS_DIR / f"phase{phase}" / sim_id

    # Find HDF5 snapshots
    hdf5_files = sorted(sim_dir.glob("*.athdf"))

    if not hdf5_files:
        return {
            'sim_id': sim_id,
            'hdf5_analyzed': False,
            'n_peaks': 0,
            'lambda_frag': None
        }

    # Analyze final snapshot
    final_snapshot = hdf5_files[-1]
    peaks = detect_longitudinal_peaks(final_snapshot)

    return {
        'sim_id': sim_id,
        'hdf5_analyzed': True,
        'hdf5_files': len(hdf5_files),
        **peaks
    }


# ==============================================================================
# Figure Generation
# ==============================================================================

def generate_figure_1_beading_threshold(df_status: pd.DataFrame, df_manifest: pd.DataFrame):
    """
    Generate Figure 1: Beading threshold map.

    Shows where longitudinal beading emerges in (f, beta) parameter space.
    """
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(12, 5))

    # Phase 1: Near-critical longitudinal
    phase1 = df_manifest[df_manifest['phase'] == 1].copy()
    if not phase1.empty:
        # Merge with analysis results
        phase1 = phase1.merge(df_status[['sim_id', 'n_peaks', 'lambda_frag']],
                             on='sim_id', how='left')

        # Create heatmap
        f_values = sorted(phase1['f'].unique())
        beta_values = sorted(phase1['beta'].unique())

        heatmap = np.zeros((len(beta_values), len(f_values)))

        for i, beta in enumerate(beta_values):
            for j, f in enumerate(f_values):
                subset = phase1[(phase1['f'] == f) & (phase1['beta'] == beta)]
                if not subset.empty:
                    # Mean number of peaks across seeds and M
                    n_peaks_mean = subset['n_peaks'].mean()
                    heatmap[i, j] = n_peaks_mean

        im = ax1.imshow(heatmap, aspect='auto', origin='lower',
                       extent=[f_values[0], f_values[-1], beta_values[0], beta_values[-1]],
                       cmap='viridis')

        ax1.set_xlabel('Line mass fraction f')
        ax1.set_ylabel('Plasma beta')
        ax1.set_title('Phase 1: Near-Critical (Longitudinal B)')
        plt.colorbar(im, ax=ax1, label='Mean N peaks')

    # Phase 2: Perpendicular field
    phase2 = df_manifest[df_manifest['phase'] == 2].copy()
    if not phase2.empty:
        phase2 = phase2.merge(df_status[['sim_id', 'n_peaks', 'lambda_frag']],
                             on='sim_id', how='left')

        f_values = sorted(phase2['f'].unique())
        beta_values = sorted(phase2['beta'].unique())

        heatmap = np.zeros((len(beta_values), len(f_values)))

        for i, beta in enumerate(beta_values):
            for j, f in enumerate(f_values):
                subset = phase2[(phase2['f'] == f) & (phase2['beta'] == beta)]
                if not subset.empty:
                    n_peaks_mean = subset['n_peaks'].mean()
                    heatmap[i, j] = n_peaks_mean

        im = ax2.imshow(heatmap, aspect='auto', origin='lower',
                       extent=[f_values[0], f_values[-1], beta_values[0], beta_values[-1]],
                       cmap='viridis')

        ax2.set_xlabel('Line mass fraction f')
        ax2.set_ylabel('Plasma beta')
        ax2.set_title('Phase 2: Perpendicular B')
        plt.colorbar(im, ax=ax2, label='Mean N peaks')

    plt.tight_layout()
    plt.savefig(ANALYSIS_OUTPUT_DIR / 'fig1_beading_threshold.pdf', dpi=300)
    plt.savefig(ANALYSIS_OUTPUT_DIR / 'fig1_beading_threshold.png', dpi=300)
    plt.close()

    print("Generated fig1_beading_threshold.pdf")


def generate_figure_2_lambda_W_comparison(df_status: pd.DataFrame, df_manifest: pd.DataFrame):
    """
    Generate Figure 2: Lambda/W comparison across field geometries.

    Shows measured fragmentation spacing for different field geometries.
    """
    fig, ax = plt.subplots(figsize=(10, 6))

    # Filter simulations with detected peaks
    with_peaks = df_status[df_status['n_peaks'] >= 2].copy()

    if with_peaks.empty:
        print("WARNING: No simulations with detected peaks for fig2")
        return

    # Merge with manifest
    merged = with_peaks.merge(df_manifest, on='sim_id')

    # Convert lambda_frag to lambda/W
    # Assuming core radius = 0.3 lambda_J, so W = 0.6 lambda_J
    W_lambda_J = 0.6
    merged['lambda_W'] = merged['lambda_frag'] / W_lambda_J

    # Plot by field geometry
    for bfield in ['longitudinal', 'perpendicular', 'oblique']:
        subset = merged[merged['bfield'] == bfield]

        if not subset.empty:
            # Group by f and plot mean lambda/W
            grouped = subset.groupby('f').agg({
                'lambda_W': ['mean', 'std']
            }).reset_index()
            grouped.columns = ['f', 'lambda_W_mean', 'lambda_W_std']

            ax.errorbar(grouped['f'], grouped['lambda_W_mean'],
                       yerr=grouped['lambda_W_std'],
                       marker='o', label=bfield.capitalize(), capsize=5)

    # HGBS reference line
    ax.axhline(y=2.1, color='red', linestyle='--', label='HGBS (λ/W = 2.1)')

    # IM92 reference line
    ax.axhline(y=4.0, color='gray', linestyle=':', label='IM92 (λ/W = 4.0)')

    ax.set_xlabel('Line mass fraction f')
    ax.set_ylabel('Fragmentation spacing λ/W')
    ax.set_title('Fragmentation Spacing vs. Field Geometry')
    ax.legend()
    ax.grid(True, alpha=0.3)

    plt.tight_layout()
    plt.savefig(ANALYSIS_OUTPUT_DIR / 'fig2_lambda_W_comparison.pdf', dpi=300)
    plt.savefig(ANALYSIS_OUTPUT_DIR / 'fig2_lambda_W_comparison.png', dpi=300)
    plt.close()

    print("Generated fig2_lambda_W_comparison.pdf")


def generate_summary_report(df_status: pd.DataFrame, df_manifest: pd.DataFrame):
    """
    Generate summary report addressing each peer review concern.
    """
    report_lines = [
        "# Peer Review Response Campaign - Summary Report",
        f"Generated: {pd.Timestamp.now().strftime('%Y-%m-%d %H:%M:%S UTC')}",
        "",
        "## Executive Summary",
        "",
    ]

    # Campaign statistics
    total_sims = len(df_manifest)
    completed_sims = len(df_status[df_status['status'].isin(['FRAG', 'STABLE', 'COMPLETED'])])
    fragmented_sims = len(df_status[df_status['status'] == 'FRAG'])
    beading_sims = len(df_status[df_status['n_peaks'] >= 2])

    report_lines.extend([
        f"- Total simulations: {total_sims}",
        f"- Completed simulations: {completed_sims} ({completed_sims/total_sims*100:.1f}%)",
        f"- Fragmented simulations: {fragmented_sims}",
        f"- Longitudinal beading detected: {beading_sims}",
        "",
        "## Response by Concern",
        ""
    ])

    # T1/T2: Longitudinal Fragmentation Detection
    phase1_sims = df_status.merge(
        df_manifest[df_manifest['phase'] == 1],
        on='sim_id',
        how='inner'
    )
    phase1_beading = phase1_sims[phase1_sims['n_peaks'] >= 2]

    report_lines.extend([
        "### T1/T2: Longitudinal Fragmentation Detection",
        f"- Simulations with ≥2 peaks: {len(phase1_beading)}",
        f"- Threshold f for beading: [ANALYZE FROM DATA]",
        f"- Sample snapshots showing beading: [ADD REFERENCES]",
        ""
    ])

    # T3: Realistic Field Geometry
    phase2_sims = df_status.merge(
        df_manifest[df_manifest['phase'] == 2],
        on='sim_id',
        how='inner'
    )
    phase2_beading = phase2_sims[phase2_sims['n_peaks'] >= 2]

    if not phase2_beading.empty:
        lambda_W_values = phase2_beading['lambda_frag'] / 0.6  # Convert to lambda/W
        report_lines.extend([
            "### T3: Realistic Field Geometry",
            f"- Perpendicular field beading rate: {len(phase2_beading)}/{len(phase2_sims)}",
            f"- λ/W for perpendicular fields: {lambda_W_values.mean():.2f} ± {lambda_W_values.std():.2f}",
            f"- Comparison with HGBS: {'Agrees' if abs(lambda_W_values.mean() - 2.1) < 0.5 else 'Differs'}",
            ""
        ])
    else:
        report_lines.extend([
            "### T3: Realistic Field Geometry",
            "- No perpendicular field beading detected yet",
            "- Analysis ongoing",
            ""
        ])

    # T9: Field-Geometry Calibration
    phase3_sims = df_status.merge(
        df_manifest[df_manifest['phase'] == 3],
        on='sim_id',
        how='inner'
    )

    report_lines.extend([
        "### T9: Field-Geometry Calibration",
        f"- Oblique field simulations: {len(phase3_sims)}",
        "- Calibration validation: [PENDING ANALYSIS]",
        ""
    ])

    # Conclusions
    report_lines.extend([
        "## Conclusions",
        "",
        "### Fully Addressed",
        "- [List concerns fully addressed]",
        "",
        "### Partially Addressed",
        "- [List concerns partially addressed]",
        "",
        "### Additional Work Needed",
        "- [List remaining gaps]",
        ""
    ])

    # Write report
    with open(ANALYSIS_OUTPUT_DIR / 'SUMMARY_REPORT.md', 'w') as f:
        f.write('\n'.join(report_lines))

    print("Generated SUMMARY_REPORT.md")


# ==============================================================================
# Main Execution
# ==============================================================================

def main():
    """Main analysis function."""
    print("Starting campaign analysis...")

    # Setup
    setup_directories()

    # Load data
    print("Loading status files...")
    df_status = load_status_files()

    print("Loading manifest...")
    df_manifest = load_manifest()

    if df_status.empty:
        print("ERROR: No simulation data found. Run simulations first.")
        sys.exit(1)

    print(f"Found {len(df_status)} completed simulations")

    # Analyze HDF5 outputs for peak detection
    print("\nAnalyzing HDF5 snapshots for peak detection...")

    all_analysis = []

    for _, sim in df_manifest.iterrows():
        sim_id = sim['sim_id']
        phase = sim['phase']

        # Check if already analyzed
        status = df_status[df_status['sim_id'] == sim_id]

        if status.empty:
            continue

        # Analyze HDF5 if not already done
        if 'n_peaks' not in status.columns or pd.isna(status['n_peaks'].values[0]):
            analysis = analyze_simulation_hdf5(sim_id, phase)
            all_analysis.append(analysis)
        else:
            all_analysis.append({
                'sim_id': sim_id,
                'n_peaks': status['n_peaks'].values[0],
                'lambda_frag': status.get('lambda_frag', [None])[0]
            })

    # Update status dataframe with peak detection results
    df_analysis = pd.DataFrame(all_analysis)

    for col in ['n_peaks', 'lambda_frag']:
        if col in df_analysis.columns:
            df_status = df_status.drop(columns=[col], errors='ignore')
            df_status = df_status.merge(df_analysis[['sim_id', col]],
                                      on='sim_id', how='left')

    # Generate figures
    print("\nGenerating figures...")
    generate_figure_1_beading_threshold(df_status, df_manifest)
    generate_figure_2_lambda_W_comparison(df_status, df_manifest)

    # Generate summary report
    print("\nGenerating summary report...")
    generate_summary_report(df_status, df_manifest)

    # Generate simulation catalog
    print("\nGenerating simulation catalog...")
    df_catalog = df_manifest.merge(df_status, on='sim_id', how='left')
    df_catalog.to_csv(ANALYSIS_OUTPUT_DIR / 'simulation_catalog.csv', index=False)

    print("\n" + "="*60)
    print("Analysis complete!")
    print(f"Output directory: {ANALYSIS_OUTPUT_DIR}")
    print("="*60 + "\n")


if __name__ == "__main__":
    main()
