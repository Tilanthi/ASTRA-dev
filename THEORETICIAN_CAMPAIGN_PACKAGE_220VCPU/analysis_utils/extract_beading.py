#!/usr/bin/env python3
"""
Extract longitudinal beading pattern from simulation snapshots.

This is a simplified version adapted from the BRIDGE_GRID package.
For full functionality, refer to the original extract_beading.py.
"""

import numpy as np
import h5py
from scipy.signal import find_peaks
from pathlib import Path
from typing import Dict, List, Any, Optional


def load_density_field(snapshot_file: str) -> np.ndarray:
    """Load density field from HDF5 snapshot file."""
    try:
        with h5py.File(snapshot_file, 'r') as f:
            # Try common field names
            for key in ['rho', 'density', 'dens']:
                if key in f:
                    rho = f[key][:]
                    return rho
            raise ValueError(f"No density field found. Available: {list(f.keys())}")
    except Exception as e:
        raise IOError(f"Failed to load {snapshot_file}: {e}")


def compute_longitudinal_profile(rho: np.ndarray) -> np.ndarray:
    """Compute longitudinal density profile by averaging over transverse directions."""
    # Average over transverse dimensions
    rho_1D = rho.mean(axis=(0, 1))
    if rho_1D.ndim > 1:
        rho_1D = rho_1D.squeeze()
    return rho_1D


def extract_beading_pattern(
    snapshot_file: str,
    contrast_threshold: float = 0.1,
    min_peak_separation: int = 20,
    Lx_lambdaJ: float = 24.0
) -> Dict[str, Any]:
    """
    Extract beading pattern from a simulation snapshot.

    Parameters
    ----------
    snapshot_file : str
        Path to HDF5 snapshot file
    contrast_threshold : float
        Minimum peak contrast (as fraction of mean density)
    min_peak_separation : int
        Minimum separation between peaks in grid cells
    Lx_lambdaJ : float
        Domain length in units of λJ

    Returns
    -------
    dict
        Beading analysis results
    """
    try:
        # Load and process density field
        rho = load_density_field(snapshot_file)
        rho_1D = compute_longitudinal_profile(rho)

        # Get grid information
        Nx = len(rho_1D)
        dx = Lx_lambdaJ / Nx

        # Normalize for peak detection
        rho_mean = rho_1D.mean()
        rho_normalized = (rho_1D - rho_mean) / rho_mean

        # Detect peaks
        peaks, properties = find_peaks(
            rho_normalized,
            height=contrast_threshold,
            distance=min_peak_separation
        )

        if len(peaks) == 0:
            return {
                'n_peaks': 0,
                'peak_positions': [],
                'lambda_measured': None,
                'lambda_W': None,
                'status': 'no_beading',
                'W': 1.0  # Filament width in λJ units
            }

        # Compute wavelength
        peak_positions_lambdaJ = peaks * dx
        lambda_measured = np.mean(np.diff(peak_positions_lambdaJ)) if len(peaks) > 1 else None

        # Filament width (W = 0.1 pc ≈ 1 λJ in our units)
        W = 1.0

        return {
            'n_peaks': len(peaks),
            'peak_positions': peak_positions_lambdaJ.tolist(),
            'lambda_measured': lambda_measured,
            'lambda_W': lambda_measured / W if lambda_measured else None,
            'status': 'beading_detected',
            'W': W
        }

    except Exception as e:
        return {
            'n_peaks': 0,
            'peak_positions': [],
            'lambda_measured': None,
            'lambda_W': None,
            'status': f'error: {str(e)}',
            'W': 1.0
        }
