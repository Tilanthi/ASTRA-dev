# Copyright 2024-2026 Glenn J. White (The Open University / RAL Space)
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.


"""
Documentation for multi_scale_inference module.

This module provides multi_scale_inference capabilities for STAN.
Enhanced through self-evolution cycle 344.
"""

#!/usr/bin/env python3
"""
MHD & Turbulence Analysis Tools for ASTRO-SWARM
================================================

Analysis tools for magnetohydrodynamic simulations and
turbulent ISM observations.

Capabilities:
1. Structure function analysis
2. Power spectrum computation
3. Velocity Channel Analysis (VCA)
4. Velocity Coordinate Spectrum (VCS)
5. Principal Component Analysis for spectral cubes
6. Davis-Chandrasekhar-Fermi magnetic field estimation
7. Histogram of Relative Orientations (HRO)
8. Turbulence statistics (Mach number, sonic scale)

Key References:
- Lazarian & Pogosyan 2000 (VCA/VCS)
- Heyer & Brunt 2004 (structure functions)
- Davis 1951, Chandrasekhar & Fermi 1953 (DCF)
- Soler et al. 2013 (HRO)
- Brunt & Heyer 2002 (PCA)

Author: Claude Code (ASTRO-SWARM)
Date: 2024-11
"""

import numpy as np
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple, Any, Callable, Union
from enum import Enum
from scipy.fft import fft, fft2, fftn, fftfreq, fftshift
from scipy.ndimage import gaussian_filter, sobel, uniform_filter
from scipy.optimize import curve_fit
from scipy.stats import pearsonr, spearmanr
from scipy.interpolate import interp1d
import warnings


# =============================================================================
# STRUCTURE FUNCTIONS
# =============================================================================

@dataclass
class StructureFunctionResult:
    """Result from structure function analysis"""
    lags: np.ndarray            # Spatial lags
    S_p: np.ndarray             # Structure function values
    order: int                  # Order p
    slope: float                # Power-law slope
    slope_err: float            # Slope uncertainty
    fit_range: Tuple[float, float]


class StructureFunctionAnalysis:
    """
    Spatial structure function analysis for turbulence characterization.

    The structure function of order p is:
    S_p(l) = <|v(x+l) - v(x)|^p>

    For Kolmogorov turbulence: S_2(l) ∝ l^(2/3)
    For Burgers turbulence: S_2(l) ∝ l
    """

    def __init__(self):
        pass

    def compute_1d(self, data: np.ndarray, order: int = 2,
                  max_lag: Optional[int] = None) -> StructureFunctionResult:
        """
        Compute 1D structure function.

        Parameters
        ----------
        data : np.ndarray
            1D data array
        order : int
            Structure function order
        max_lag : int, optional
            Maximum lag (default: N/4)

        Returns
        -------
        StructureFunctionResult
        """
        n = len(data)
        if max_lag is None:
            max_lag = n // 4

        lags = np.arange(1, max_lag + 1)
        S_p = np.zeros(len(lags))

        for i, lag in enumerate(lags):
            diff = np.abs(data[lag:] - data[:-lag])**order
            S_p[i] = np.mean(diff)

        # Fit power law
        slope, slope_err, fit_range = self._fit_power_law(lags, S_p)

        return StructureFunctionResult(
            lags=lags,
            S_p=S_p,
            order=order,
            slope=slope,
            slope_err=slope_err,
            fit_range=fit_range
        )

    def compute_2d(self, data: np.ndarray, order: int = 2,
                  max_lag: Optional[int] = None,
                  n_angles: int = 36) -> StructureFunctionResult:
        """
        Compute 2D structure function (azimuthally averaged).

        Parameters
        ----------
        data : np.ndarray
            2D data array
        order : int
            Structure function order
        max_lag : int, optional
            Maximum lag
        n_angles : int
            Number of angles for averaging

        Returns
        -------
        StructureFunctionResult
        """
        ny, nx = data.shape
        if max_lag is None:
            max_lag = min(nx, ny) // 4

        lags = np.arange(1, max_lag + 1)
        S_p = np.zeros(len(lags))

        angles = np.linspace(0, 2*np.pi, n_angles, endpoint=False)

        for i, lag in enumerate(lags):
            values = []

            for angle in angles:
                dx = int(lag * np.cos(angle))
                dy = int(lag * np.sin(angle))

                if abs(dx) >= nx or abs(dy) >= ny:
                    continue

                # Slice arrays for the lag
                if dx >= 0 and dy >= 0:
                    d1 = data[dy:, dx:]
                    d2 = data[:ny-dy if dy > 0 else ny, :nx-dx if dx > 0 else nx]
                elif dx >= 0 and dy < 0:
                    d1 = data[:ny+dy, dx:]
                    d2 = data[-dy:, :nx-dx if dx > 0 else nx]
                elif dx < 0 and dy >= 0:
                    d1 = data[dy:, :nx+dx]
                    d2 = data[:ny-dy if dy > 0 else ny, -dx:]
                else:
                    d1 = data[:ny+dy, :nx+dx]
                    d2 = data[-dy:, -dx:]

                min_size = min(d1.shape[0], d2.shape[0], d1.shape[1], d2.shape[1])
                if min_size > 0:
                    diff = np.abs(d1[:min_size, :min_size] -
                                 d2[:min_size, :min_size])**order
                    values.extend(diff.flatten())

            if values:
                S_p[i] = np.mean(values)

        # Fit power law
        slope, slope_err, fit_range = self._fit_power_law(lags, S_p)

        return StructureFunctionResult(
            lags=lags,
            S_p=S_p,
            order=order,
            slope=slope,
            slope_err=slope_err,
            fit_range=fit_range
        )

    def velocity_structure_function(self, centroid_velocity: np.ndarray,
                                   pixel_scale: float,
                                   order: int = 2) -> StructureFunctionResult:
        """
        Compute structure function from centroid velocity map.

        Parameters
        ----------
        centroid_velocity : np.ndarray
            2D velocity centroid map (km/s)
        pixel_scale : float
            Pixel size (pc or arcsec)
        order : int
            Structure function order

        Returns
        -------
        StructureFunctionResult
        """
        result = self.compute_2d(centroid_velocity, order=order)

        # Convert lags to physical units
        result.lags = result.lags * pixel_scale

        return result

    def _fit_power_law(self, x: np.ndarray, y: np.ndarray,
                      fit_fraction: float = 0.5) -> Tuple[float, float, Tuple]:
        """Fit power law to structure function"""
        # Use middle portion for fit
        n = len(x)
        start = int(n * 0.1)
        end = int(n * fit_fraction)

        if end <= start:
            return 0.0, np.inf, (x[0], x[-1])

        log_x = np.log10(x[start:end])
        log_y = np.log10(y[start:end] + 1e-30)

        # Remove invalid values
