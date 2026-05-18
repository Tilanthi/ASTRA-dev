#!/usr/bin/env python3
"""
extract_lambda_W.py

Extract fragmentation spacing (λ/W) from simulation outputs.

Usage:
    python extract_lambda_W.py <h5_file>
    python extract_lambda_W.py <h5_file> --threshold 3.0
    python extract_lambda_W.py <h5_file> --plot
"""

import sys
import os
import h5py
import numpy as np
import argparse
from pathlib import Path
from scipy.signal import find_peaks
from scipy.ndimage import gaussian_filter1d
import matplotlib.pyplot as plt


def load_density_field(h5_file: str) -> Tuple[np.ndarray, float]:
    """
    Load density field from HDF5 file.

    Parameters
    ----------
    h5_file : str
        Path to HDF5 file

    Returns
    -------
    rho : array
        Density field
    dx : float
        Grid spacing in λ_J units
    """
    with h5py.File(h5_file, 'r') as f:
        # Try Athena++ v21.0 structure
        if 'Level0' in f:
            last_level = f['Level0'][-1]

            if 'prim' in last_level:
                rho = last_level['prim']['rho'][()]

                # Get grid size
                shape = rho.shape
                nx, ny, nz = shape[0], shape[1], shape[2]

                # Domain is 8x2x2 λ_J for Phase 1
                dx = 8.0 / nx

                return rho, dx

    raise ValueError(f"Could not load density from {h5_file}")


def extract_1d_density(rho: np.ndarray, axis: int = 0) -> np.ndarray:
    """
    Extract 1D density profile along filament axis.

    Parameters
    ----------
    rho : array
        3D density field
    axis : int
        Axis along filament (default: 0)

    Returns
    -------
    rho_1d : array
        1D density profile averaged over transverse directions
    """
    # Extract midplane
    mid_idx = [s // 2 for s in rho.shape]

    # Average over transverse directions
    if axis == 0:
        # Filament along x-axis
        rho_midplane = rho[:, mid_idx[1], mid_idx[2]]
    elif axis == 1:
        # Filament along y-axis
        rho_midplane = rho[mid_idx[0], :, mid_idx[2]]
    else:
        # Filament along z-axis
        rho_midplane = rho[mid_idx[0], mid_idx[1], :]

    return rho_midplane


def detect_cores(rho_1d: np.ndarray, dx: float,
                threshold: float = 3.0,
                min_distance: int = 10) -> Tuple[np.ndarray, dict]:
    """
    Detect dense cores from 1D density profile.

    Parameters
    ----------
    rho_1d : array
        1D density profile
    dx : float
        Grid spacing
    threshold : float
        Peak detection threshold (in units of background)
    min_distance : int
        Minimum distance between peaks (in grid cells)

    Returns
    -------
    peaks : array
        Peak positions (in grid units)
    properties : dict
        Peak properties
    """
    # Smooth to reduce noise
    rho_smooth = gaussian_filter1d(rho_1d, sigma=2)

    # Background level (median)
    background = np.median(rho_1d)

    # Find peaks
    peaks, properties = find_peaks(
        rho_smooth,
        height=threshold * background,
        distance=min_distance
    )

    return peaks, properties


def extract_lambda_W(peaks: np.ndarray, dx: float,
                    W_core: float = 0.3) -> Tuple[float, float]:
    """
    Extract fragmentation spacing from detected peaks.

    Parameters
    ----------
    peaks : array
        Peak positions (in grid units)
    dx : float
        Grid spacing (in λ_J units)
    W_core : float
        Filament core half-width (0.3 λ_J)

    Returns
    -------
    lambda_W : float
        Mean spacing normalized to core width
    lambda_W_std : float
        Standard deviation of spacing
    """
    if len(peaks) < 2:
        return np.nan, np.nan

    # Convert to physical units
    peak_positions = peaks * dx

    # Compute spacing between adjacent peaks
    spacings = np.diff(peak_positions)

    # Normalize to core width
    W_core_phys = W_core  # In λ_J units
    lambda_W_values = spacings / W_core_phys

    # Return mean and std
    return np.mean(lambda_W_values), np.std(lambda_W_values)


def classify_fragmentation(rho: np.ndarray) -> Tuple[str, float]:
    """
    Classify fragmentation outcome.

    Parameters
    ----------
    rho : array
        3D density field

    Returns
    -------
    outcome : str
        'BEADING', 'RADIAL_COLLAPSE', or 'MIXED'
    confidence : float
        Confidence in classification (0-1)
    """
    # Check for axial density variations
    mid_idx = [s // 2 for s in rho.shape]
    rho_axis = rho[:, mid_idx[1], mid_idx[2]]

    # Compute variance along axis
    var_axis = np.var(rho_axis)
    var_total = np.var(rho)

    # Beading criterion: significant axial variation
    beading_strength = var_axis / var_total

    if beading_strength > 0.1:
        return 'BEADING', beading_strength
    else:
        return 'RADIAL_COLLAPSE', 1.0 - beading_strength


def plot_results(rho_1d: np.ndarray, peaks: np.ndarray,
                dx: float, lambda_W: float, lambda_W_std: float,
                output_file: str = None):
    """
    Plot density profile and detected peaks.

    Parameters
    ----------
    rho_1d : array
        1D density profile
    peaks : array
        Detected peak positions
    dx : float
        Grid spacing
    lambda_W : float
        Fragmentation spacing
    lambda_W_std : float
        Spacing standard deviation
    output_file : str
        Save plot to file
    """
    x_grid = np.arange(len(rho_1d)) * dx

    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(12, 8))

    # Top panel: Full profile
    ax1.plot(x_grid, rho_1d, 'k-', linewidth=1, alpha=0.7, label='Density')

    # Smoothed profile
    rho_smooth = gaussian_filter1d(rho_1d, sigma=2)
    ax1.plot(x_grid, rho_smooth, 'r-', linewidth=2, label='Smoothed')

    # Mark peaks
    if len(peaks) > 0:
        peak_x = peaks * dx
        peak_y = rho_smooth[peaks]
        ax1.plot(peak_x, peak_y, 'bo', markersize=8, label=f'{len(peaks)} cores')

    ax1.set_xlabel('Position (λ_J)')
    ax1.set_ylabel('Density (normalized)')
    ax1.set_title('Filament Density Profile')
    ax1.legend()
    ax1.grid(True, alpha=0.3)

    # Bottom panel: Spacing histogram
    if len(peaks) > 1:
        peak_positions = peaks * dx
        spacings = np.diff(peak_positions) / 0.3  # Normalized to W

        ax2.hist(spacings, bins=len(spacings), edgecolor='k', alpha=0.7)
        ax2.axvline(lambda_W, color='r', linestyle='--',
                   linewidth=2, label=f'Mean: λ/W = {lambda_W:.2f}')
        ax2.set_xlabel('Spacing (λ/W)')
        ax2.set_ylabel('Count')
        ax2.set_title('Fragmentation Spacing Distribution')
        ax2.legend()
    else:
        ax2.text(0.5, 0.5, 'Insufficient peaks for spacing analysis',
                ha='center', va='center', transform=ax2.transAxes)

    plt.tight_layout()

    if output_file:
        plt.savefig(output_file, dpi=150, bbox_inches='tight')
        print(f"Plot saved to: {output_file}")
    else:
        plt.show()

    plt.close()


def main():
    parser = argparse.ArgumentParser(
        description="Extract fragmentation spacing from simulation outputs"
    )
    parser.add_argument(
        "h5_file",
        help="Path to HDF5 output file"
    )
    parser.add_argument(
        "--threshold", "-t",
        type=float,
        default=3.0,
        help="Peak detection threshold (default: 3.0)"
    )
    parser.add_argument(
        "--min-distance", "-d",
        type=int,
        default=10,
        help="Minimum distance between peaks (default: 10)"
    )
    parser.add_argument(
        "--core-width", "-W",
        type=float,
        default=0.3,
        help="Filament core half-width in λ_J (default: 0.3)"
    )
    parser.add_argument(
        "--plot", "-p",
        action="store_true",
        help="Generate diagnostic plot"
    )
    parser.add_argument(
        "--output", "-o",
        help="Output file for plot"
    )

    args = parser.parse_args()

    print("="*60)
    print("Fragmentation Spacing Analysis")
    print("="*60)

    # Load density field
    print(f"\nLoading: {args.h5_file}")
    rho, dx = load_density_field(args.h5_file)
    print(f"  Grid shape: {rho.shape}")
    print(f"  Grid spacing: {dx:.4f} λ_J")

    # Extract 1D profile
    rho_1d = extract_1d_density(rho, axis=0)

    # Detect cores
    print(f"\nDetecting cores (threshold: {args.threshold}× background)...")
    peaks, properties = detect_cores(rho_1d, dx, args.threshold, args.min_distance)

    if len(peaks) == 0:
        print("  ✗ No cores detected")
        return
    elif len(peaks) == 1:
        print(f"  ⚠ Only 1 core detected (insufficient for spacing)")
    else:
        print(f"  ✓ {len(peaks)} cores detected")

    # Extract spacing
    lambda_W, lambda_W_std = extract_lambda_W(
        peaks, dx, args.core_width
    )

    if not np.isnan(lambda_W):
        print(f"\nFragmentation Spacing:")
        print(f"  λ/W = {lambda_W:.3f} ± {lambda_W_std:.3f}")
    else:
        print(f"\nFragmentation Spacing:")
        print(f"  N/A (insufficient peaks)")

    # Classify outcome
    outcome, confidence = classify_fragmentation(rho)
    print(f"\nOutcome:")
    print(f"  {outcome} (confidence: {confidence:.2f})")

    print("="*60)

    # Generate plot
    if args.plot:
        output_file = args.output
        if output_file is None:
            output_file = Path(args.h5_file).stem + "_lambda_W.pdf"

        plot_results(rho_1d, peaks, dx, lambda_W, lambda_W_std, output_file)

    # Output JSON
    import json
    output_data = {
        "file": args.h5_file,
        "n_cores": len(peaks),
        "lambda_W": float(lambda_W) if not np.isnan(lambda_W) else None,
        "lambda_W_std": float(lambda_W_std) if not np.isnan(lambda_W_std) else None,
        "outcome": outcome,
        "confidence": float(confidence)
    }

    output_file = Path(args.h5_file).stem + "_lambda_W.json"
    with open(output_file, 'w') as f:
        json.dump(output_data, f, indent=2)
    print(f"\nResults saved to: {output_file}")


if __name__ == "__main__":
    main()
