#!/usr/bin/env python3
"""
CTZM Campaign Analysis Pipeline
================================

Analyzes HDF5 outputs from CTZM campaign to measure λ/W evolution
and classify simulations as BEADING vs RADIAL.

Usage:
    python ctzm_analyze.py --results_dir output_ctzm

Author: ASTRA Autonomous System
Date: 2026-05-13
"""

import h5py
import numpy as np
import json
import argparse
from pathlib import Path
from typing import Dict, List, Tuple, Optional
import logging
from dataclasses import dataclass

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('ctzm_analyze.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# ======================================================================
# CTZM Configuration Constants
# ======================================================================

CTZM_CONFIG = {
    "domain": {
        "Lx": 8.0,
        "Ly": 2.0,
        "Lz": 2.0,
        "W_core": 0.3,  # Core half-width in lambda_J units
    },
    "peak_detection": {
        "smoothing_sigma": 2,  # Cells
        "prominence_threshold": 0.05,  # 5% above background
        "min_peaks": 2,
        "max_peaks": 20,
    },
    "classification": {
        "beading_threshold": 0.02,  # Longitudinal variance > 2%
        "stability_window": 0.1,  # tJ window to check stability
        "min_peaks_for_beading": 3,
    }
}

# ======================================================================
# Data Structures
# ======================================================================

@dataclass
class SnapshotData:
    """Data from a single HDF5 snapshot."""
    sim_id: str
    snapshot_num: int
    time_tj: float
    density_profile: np.ndarray
    x_coords: np.ndarray


@dataclass
class PeakDetectionResult:
    """Results from peak detection in a single snapshot."""
    snapshot_num: int
    time_tj: float
    n_peaks: int
    peak_positions: np.ndarray  # In units of lambda_J
    peak_spacings: np.ndarray   # In units of lambda_J
    median_spacing: float       # In units of lambda_J
    lambda_W: float             # Normalized to W_core
    density_contrast: float     # rho_max / rho_0


@dataclass
class SimulationClassification:
    """Classification result for a single simulation."""
    sim_id: str
    classification: str  # BEADING_STABLE, BEADING_TRANSIENT, RADIAL_COLLAPSE
    t_frag: Optional[float]
    lambda_W_final: Optional[float]
    lambda_W_stable_time: Optional[float]
    n_peaks_final: int
    density_contrast: float
    confidence: float  # 0-1


# ======================================================================
# HDF5 Data Extraction
# ======================================================================

def extract_density_profile(hdf5_path: Path) -> Tuple[np.ndarray, np.ndarray, float]:
    """
    Extract longitudinal density profile from HDF5 file.

    Args:
        hdf5_path: Path to HDF5 snapshot file

    Returns:
        (x_coords, density_profile, time_tj)
    """
    try:
        with h5py.File(hdf5_path, 'r') as f:
            # Get density field
            # Path: 'dens' or 'Variables/dens' depending on output format
            if 'dens' in f:
                density = f['dens'][:]
            elif 'Variables' in f and 'dens' in f['Variables']:
                density = f['Variables/dens'][:]
            else:
                raise ValueError(f"Cannot find density data in {hdf5_path}")

            # Get simulation time
            if 'Time' in f.attrs:
                time = f.attrs['Time']
            elif 'Time' in f:
                time = f['Time'][()]
            else:
                time = 0.0

            # Extract longitudinal profile along y = z = 0 (filament axis)
            # Density shape: (nz, ny, nx)
            nz, ny, nx = density.shape

            # Get profile along x-axis at y=ny//2, z=nz//2
            y_mid = ny // 2
            z_mid = nz // 2
            profile = density[z_mid, y_mid, :]

            # Create x-coordinate array (0 to Lx)
            Lx = CTZM_CONFIG["domain"]["Lx"]
            x_coords = np.linspace(0, Lx, nx)

            return x_coords, profile, time

    except Exception as e:
        logger.error(f"Failed to extract density profile from {hdf5_path}: {e}")
        raise


# ======================================================================
# Peak Detection Algorithm
# ======================================================================

def detect_peaks(density_profile: np.ndarray, x_coords: np.ndarray,
                 smoothing_sigma: int = 2) -> PeakDetectionResult:
    """
    Detect peaks in longitudinal density profile.

    Args:
        density_profile: 1D density array
        x_coords: x-coordinate array (same length as density_profile)
        smoothing_sigma: Gaussian smoothing kernel size (cells)

    Returns:
        PeakDetectionResult object
    """
    from scipy.ndimage import gaussian_filter1d
    from scipy.signal import find_peaks

    # Apply Gaussian smoothing to reduce noise
    smoothed = gaussian_filter1d(density_profile, sigma=smoothing_sigma)

    # Background density (median)
    background = np.median(smoothed)

    # Peak prominence threshold (5% above background)
    prominence = CTZM_CONFIG["peak_detection"]["prominence_threshold"] * background

    # Find peaks
    peak_indices, properties = find_peaks(
        smoothed,
        prominence=prominence,
        distance=5,  # Minimum distance between peaks (cells)
    )

    # Extract peak positions and spacings
    if len(peak_indices) < CTZM_CONFIG["peak_detection"]["min_peaks"]:
        # Not enough peaks detected
        return PeakDetectionResult(
            snapshot_num=-1,
            time_tj=0.0,
            n_peaks=0,
            peak_positions=np.array([]),
            peak_spacings=np.array([]),
            median_spacing=0.0,
            lambda_W=0.0,
            density_contrast=np.max(smoothed) / background if background > 0 else 0.0
        )

    peak_positions = x_coords[peak_indices]
    peak_spacings = np.diff(peak_positions)
    median_spacing = np.median(peak_spacings) if len(peak_spacings) > 0 else 0.0

    # Calculate lambda/W ratio
    W_core = CTZM_CONFIG["domain"]["W_core"]
    lambda_W = median_spacing / W_core if median_spacing > 0 else 0.0

    return PeakDetectionResult(
        snapshot_num=-1,  # Will be filled by caller
        time_tj=0.0,      # Will be filled by caller
        n_peaks=len(peak_indices),
        peak_positions=peak_positions,
        peak_spacings=peak_spacings,
        median_spacing=median_spacing,
        lambda_W=lambda_W,
        density_contrast=np.max(smoothed) / background if background > 0 else 0.0
    )


# ======================================================================
# Longitudinal Variance Calculation
# ======================================================================

def calculate_longitudinal_variance(density_profile: np.ndarray) -> float:
    """
    Calculate fractional longitudinal density variance.

    This is the key metric for BEADING vs RADIAL classification:
    - RADIAL_COLLAPSE: variance < 2%
    - BEADING: variance > 2%

    Args:
        density_profile: 1D density array

    Returns:
        Fractional variance (std_dev / mean)
    """
    mean = np.mean(density_profile)
    std = np.std(density_profile)

    if mean > 0:
        return std / mean
    else:
        return 0.0


# ======================================================================
# Single Simulation Analysis
# ======================================================================

def analyze_single_simulation(output_dir: Path) -> SimulationClassification:
    """
    Analyze all snapshots from a single simulation.

    Args:
        output_dir: Path to simulation output directory

    Returns:
        SimulationClassification object
    """
    sim_id = output_dir.name

    # Find all HDF5 snapshot files
    hdf5_files = sorted(output_dir.glob("*.hdf5"))
    if not hdf5_files:
        hdf5_files = sorted(output_dir.glob("*/*.hdf5"))  # Check subdirectories

    if not hdf5_files:
        logger.warning(f"No HDF5 files found in {output_dir}")
        return SimulationClassification(
            sim_id=sim_id,
            classification="NO_DATA",
            t_frag=None,
            lambda_W_final=None,
            lambda_W_stable_time=None,
            n_peaks_final=0,
            density_contrast=0.0,
            confidence=0.0
        )

    logger.info(f"Analyzing {len(hdf5_files)} snapshots from {sim_id}")

    # Analyze each snapshot
    results = []
    for i, hdf5_path in enumerate(hdf5_files):
        try:
            x_coords, density_profile, time = extract_density_profile(hdf5_path)

            # Detect peaks
            peak_result = detect_peaks(density_profile, x_coords)
            peak_result.snapshot_num = i
            peak_result.time_tj = time

            # Calculate longitudinal variance
            variance = calculate_longitudinal_variance(density_profile)

            results.append({
                "snapshot_num": i,
                "time": time,
                "peak_result": peak_result,
                "variance": variance,
            })

        except Exception as e:
            logger.warning(f"Failed to analyze snapshot {i} from {sim_id}: {e}")

    if not results:
        return SimulationClassification(
            sim_id=sim_id,
            classification="ANALYSIS_FAILED",
            t_frag=None,
            lambda_W_final=None,
            lambda_W_stable_time=None,
            n_peaks_final=0,
            density_contrast=0.0,
            confidence=0.0
        )

    # Classify simulation based on evolution
    return classify_simulation(results, sim_id)


def classify_simulation(results: List[Dict], sim_id: str) -> SimulationClassification:
    """
    Classify simulation based on time evolution of peak detection results.

    Classification criteria:
    - BEADING_STABLE: Longitudinal beading detected and stabilizes
    - BEADING_TRANSIENT: Beading detected but λ_W unstable
    - RADIAL_COLLAPSE: No longitudinal beading (variance < 2%)

    Args:
        results: List of snapshot analysis results
        sim_id: Simulation ID

    Returns:
        SimulationClassification object
    """
    # Get final state
    final_result = results[-1]
    final_peak = final_result["peak_result"]
    final_variance = final_result["variance"]
    final_time = final_result["time"]

    # Check for fragmentation (dt_watchdog criterion)
    # If simulation ended early, it likely fragmented
    if final_time < 3.5:  # Didn't reach t_max = 4.0
        t_frag = final_time
    else:
        t_frag = None

    # Primary classification: longitudinal variance
    if final_variance < CTZM_CONFIG["classification"]["beading_threshold"]:
        # Variance < 2% → RADIAL_COLLAPSE
        return SimulationClassification(
            sim_id=sim_id,
            classification="RADIAL_COLLAPSE",
            t_frag=t_frag,
            lambda_W_final=None,
            lambda_W_stable_time=None,
            n_peaks_final=final_peak.n_peaks,
            density_contrast=final_peak.density_contrast,
            confidence=0.95  # High confidence for clear cases
        )

    # Variance > 2% → Check for beading
    if final_peak.n_peaks < CTZM_CONFIG["classification"]["min_peaks_for_beading"]:
        # Not enough peaks → TRANSIENT
        return SimulationClassification(
            sim_id=sim_id,
            classification="BEADING_TRANSIENT",
            t_frag=t_frag,
            lambda_W_final=final_peak.lambda_W,
            lambda_W_stable_time=None,
            n_peaks_final=final_peak.n_peaks,
            density_contrast=final_peak.density_contrast,
            confidence=0.7  # Lower confidence for transient cases
        )

    # Check if λ_W stabilized
    lambda_W_values = [r["peak_result"].lambda_W for r in results
                       if r["peak_result"].n_peaks >= CTZM_CONFIG["classification"]["min_peaks_for_beading"]]

    if len(lambda_W_values) < 3:
        # Not enough data points to assess stability
        return SimulationClassification(
            sim_id=sim_id,
            classification="BEADING_TRANSIENT",
            t_frag=t_frag,
            lambda_W_final=final_peak.lambda_W,
            lambda_W_stable_time=None,
            n_peaks_final=final_peak.n_peaks,
            density_contrast=final_peak.density_contrast,
            confidence=0.5  # Low confidence
        )

    # Check stability in final time window
    window_size = CTZM_CONFIG["classification"]["stability_window"]
    recent_values = lambda_W_values[-5:]  # Last 5 snapshots
    if len(recent_values) >= 3:
        recent_std = np.std(recent_values)
        if recent_std < 0.2:  # λ_W stable within 20%
            # Found stabilization time
            stable_idx = len(lambda_W_values) - len(recent_values)
            stable_time = results[stable_idx]["time"]

            return SimulationClassification(
                sim_id=sim_id,
                classification="BEADING_STABLE",
                t_frag=t_frag,
                lambda_W_final=final_peak.lambda_W,
                lambda_W_stable_time=stable_time,
                n_peaks_final=final_peak.n_peaks,
                density_contrast=final_peak.density_contrast,
                confidence=0.9  # High confidence for stable beading
            )

    # Unstable beading
    return SimulationClassification(
        sim_id=sim_id,
        classification="BEADING_TRANSIENT",
        t_frag=t_frag,
        lambda_W_final=final_peak.lambda_W,
        lambda_W_stable_time=None,
        n_peaks_final=final_peak.n_peaks,
        density_contrast=final_peak.density_contrast,
        confidence=0.6
    )


# ======================================================================
# Campaign-Wide Analysis
# ======================================================================

def analyze_campaign(results_dir: Path) -> Dict:
    """
    Analyze all simulations in the CTZM campaign.

    Args:
        results_dir: Path to output directory containing all simulation results

    Returns:
        Dictionary with campaign-wide analysis results
    """
    # Find all simulation output directories
    sim_dirs = sorted([d for d in results_dir.iterdir() if d.is_dir()])

    logger.info(f"Found {len(sim_dirs)} simulation directories")

    # Analyze each simulation
    classifications = []
    for sim_dir in sim_dirs:
        try:
            classification = analyze_single_simulation(sim_dir)
            classifications.append(classification)
            logger.info(
                f"{classification.sim_id}: {classification.classification} | "
                f"λ/W = {classification.lambda_W_final:.2f} | "
                f"Confidence = {classification.confidence:.2f}"
            )
        except Exception as e:
            logger.error(f"Failed to analyze {sim_dir}: {e}")

    # Compile summary statistics
    summary = {
        "campaign": "CTZM",
        "total_sims": len(classifications),
        "beading_stable": len([c for c in classifications if c.classification == "BEADING_STABLE"]),
        "beading_transient": len([c for c in classifications if c.classification == "BEADING_TRANSIENT"]),
        "radial_collapse": len([c for c in classifications if c.classification == "RADIAL_COLLAPSE"]),
        "no_data": len([c for c in classifications if c.classification in ["NO_DATA", "ANALYSIS_FAILED"]]),
        "classifications": [c.__dict__ for c in classifications],
    }

    logger.info("=" * 60)
    logger.info("CTZM CAMPAIGN ANALYSIS SUMMARY")
    logger.info("=" * 60)
    logger.info(f"Total simulations: {summary['total_sims']}")
    logger.info(f"BEADING_STABLE: {summary['beading_stable']}")
    logger.info(f"BEADING_TRANSIENT: {summary['beading_transient']}")
    logger.info(f"RADIAL_COLLAPSE: {summary['radial_collapse']}")
    logger.info(f"NO_DATA: {summary['no_data']}")
    logger.info("=" * 60)

    return summary


# ======================================================================
# Main Entry Point
# ======================================================================

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="CTZM Campaign Analysis")
    parser.add_argument(
        "--results_dir",
        type=str,
        default="output_ctzm",
        help="Path to directory containing simulation outputs"
    )
    parser.add_argument(
        "--output",
        type=str,
        default="ctzm_analysis_results.json",
        help="Path to output JSON file"
    )

    args = parser.parse_args()

    results_dir = Path(args.results_dir)

    if not results_dir.exists():
        logger.error(f"Results directory not found: {results_dir}")
        exit(1)

    try:
        # Run analysis
        summary = analyze_campaign(results_dir)

        # Save results
        output_path = Path(args.output)
        with open(output_path, 'w') as f:
            json.dump(summary, f, indent=2)

        logger.info(f"Analysis results saved to {output_path}")

    except Exception as e:
        logger.error(f"Analysis failed: {e}")
        exit(1)
