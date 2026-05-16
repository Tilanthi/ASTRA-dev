#!/usr/bin/env python3
"""
Classification utilities for GOOD/FLAT/RADIAL_COLLAPSE criteria.

Provides quantitative criteria for classifying simulation outputs.
"""

import numpy as np


def classify_longitudinal_profile(rho_1D, W=1.0):
    """
    Classify a longitudinal density profile.

    Criteria:
    - BEADING: Clear peaks with amplitude > 0.15, variance > 0.05
    - TRANSITIONAL: Intermediate properties
    - FLAT: No significant peaks, variance < 0.02
    - RADIAL_COLLAPSE: Monotonic profile, no longitudinal structure

    Parameters
    ----------
    rho_1D : np.ndarray
        Longitudinal density profile
    W : float
        Filament width

    Returns
    -------
    dict
        Classification with confidence scores
    """
    # Normalize
    rho_mean = rho_1D.mean()
    rho_norm = (rho_1D - rho_mean) / rho_mean

    # Compute statistics
    variance = rho_norm.var()
    max_amplitude = np.abs(rho_norm).max()
    n_peaks = count_significant_peaks(rho_norm)

    # Classification logic
    if variance < 0.02 and max_amplitude < 0.1:
        classification = 'FLAT'
        confidence = 0.9
    elif n_peaks >= 3 and max_amplitude > 0.15:
        classification = 'BEADING'
        confidence = 0.95
    elif variance > 0.05 and max_amplitude > 0.1:
        classification = 'TRANSITIONAL'
        confidence = 0.7
    else:
        classification = 'RADIAL_COLLAPSE'
        confidence = 0.6

    return {
        'classification': classification,
        'confidence': confidence,
        'variance': variance,
        'max_amplitude': max_amplitude,
        'n_peaks': n_peaks
    }


def count_significant_peaks(rho_1D, threshold=0.1, min_distance=20):
    """Count significant peaks in normalized profile."""
    from scipy.signal import find_peaks
    peaks, _ = find_peaks(rho_1D, height=threshold, distance=min_distance)
    return len(peaks)
