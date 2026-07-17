
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


# =============================================================================
# POWER SPECTRUM
# =============================================================================

class PowerSpectrumAnalysis:
    """Isotropic power spectrum of a 2D field via FFT, with slope fitting."""

    def power_spectrum_2d(self, field: np.ndarray) -> Tuple[np.ndarray, np.ndarray]:
        """Return (k, P(k)) radially-averaged. k in pixel units (k=0 excluded)."""
        field = np.asarray(field, dtype=float)
        f = np.fft.fftn(field)
        P = np.abs(np.fft.fftshift(f)) ** 2
        ny, nx = field.shape[-2], field.shape[-1]
        cy, cx = ny // 2, nx // 2
        yy, xx = np.indices((ny, nx))
        r = np.sqrt((xx - cx) ** 2 + (yy - cy) ** 2).astype(int)
        rmax = r.max()
        sumP = np.bincount(r.ravel(), P.ravel(), minlength=rmax + 1)
        cnt = np.bincount(r.ravel(), minlength=rmax + 1)
        cnt[cnt == 0] = 1
        radial = sumP / cnt
        k = np.arange(rmax + 1)
        return k[1:], radial[1:]

    def fit_slope(self, k: np.ndarray, P: np.ndarray,
                  kmin: float = None, kmax: float = None) -> float:
        """Fit log P = slope * log k + c. Kolmogorov 2D -> slope ~ -8/3."""
        k = np.asarray(k, float); P = np.asarray(P, float)
        m = (k > 0) & np.isfinite(P) & (P > 0)
        if kmin is not None:
            m &= k >= kmin
        if kmax is not None:
            m &= k <= kmax
        if m.sum() < 2:
            return np.nan
        slope, _ = np.polyfit(np.log10(k[m]), np.log10(P[m]), 1)
        return float(slope)


# =============================================================================
# VELOCITY ANALYSIS
# =============================================================================

class VelocityAnalysis:
    """Moment / dispersion analysis of a velocity field or cube."""

    def velocity_dispersion(self, velocity_field: np.ndarray) -> float:
        """1D velocity dispersion (same units as input)."""
        v = np.asarray(velocity_field, float)
        return float(np.std(v))

    def centroid_velocity(self, cube: np.ndarray, vaxis: int = 0) -> np.ndarray:
        """Intensity-weighted centroid velocity along `vaxis`."""
        cube = np.asarray(cube, float)
        v = np.arange(cube.shape[vaxis]).reshape([-1 if i == vaxis else 1 for i in range(cube.ndim)])
        num = np.sum(cube * v, axis=vaxis)
        den = np.sum(cube, axis=vaxis)
        den[den == 0] = np.nan
        return num / den

    def line_width(self, velocity_dispersion_cm_s: float) -> float:
        """FWHM = 2*sqrt(2*ln2)*sigma."""
        return velocity_dispersion_cm_s * 2.3548200450309493


# =============================================================================
# SPECTRAL PCA (Brunt & Heyer 2002 style)
# =============================================================================

class SpectralPCA:
    """Principal Component Analysis of a position-velocity (spectral) cube."""

    def __init__(self, n_components: int = 3):
        self.n_components = n_components

    def fit(self, cube: np.ndarray, vaxis: int = 0) -> Dict[str, np.ndarray]:
        """Return eigenvalues (variance spectrum) and the leading PCs.

        Reshapes the cube to (n_channels, n_pixels) and forms the covariance
        matrix across velocity channels, then eigen-decomposes it.
        """
        cube = np.asarray(cube, float)
        # move velocity axis to front, flatten spatial
        pv = np.moveaxis(cube, vaxis, 0).reshape(cube.shape[vaxis], -1)
        pv = pv - pv.mean(axis=1, keepdims=True)
        cov = np.cov(pv)
        eigvals, eigvecs = np.linalg.eigh(cov)
        order = np.argsort(eigvals)[::-1]
        eigvals = eigvals[order]
        eigvecs = eigvecs[:, order]
        return {
            'eigenvalues': eigvals[:self.n_components],
            'components': eigvecs[:, :self.n_components],
            'explained_variance_ratio': (eigvals / eigvals.sum())[:self.n_components],
        }


# =============================================================================
# DAVIS-CHANDRASEKHAR-FERMI
# =============================================================================

class DavisChandrasekharFermi:
    """Davis (1951) / Chandrasekhar & Fermi (1953) plane-of-sky B-field estimator.

        B_pos = Q * sqrt(4*pi*rho) * sigma_v,NT / sigma_theta

    where rho = mu * m_H * n is the mass density, sigma_v,NT the non-thermal
    velocity dispersion, and sigma_theta the polarization-angle dispersion
    (radians). Q ~ 0.5 (Ostriker, Stone & Gammie 2001; Crutcher 2004).
    """

    M_H = 1.6735575e-24  # g

    def __init__(self, correction_factor: float = 0.5):
        self.Q = correction_factor

    def magnetic_field_gauss(self, number_density: float,
                             velocity_dispersion_cm_s: float,
                             angle_dispersion_rad: float,
                             mu: float = 2.33) -> float:
        """B_pos in Gauss. n (cm^-3), sigma_v (cm/s), sigma_theta (rad)."""
        rho = mu * self.M_H * number_density
        return self.Q * np.sqrt(4.0 * np.pi * rho) * velocity_dispersion_cm_s / angle_dispersion_rad

    def magnetic_field_microgauss(self, number_density: float,
                                  sigma_v_km_s: float,
                                  sigma_theta_deg: float,
                                  mu: float = 2.33) -> float:
        """Convenience wrapper: returns B_pos in microgauss."""
        return self.magnetic_field_gauss(
            number_density, sigma_v_km_s * 1e5, np.deg2rad(sigma_theta_deg), mu) * 1e6


# =============================================================================
# HISTOGRAM OF RELATIVE ORIENTATIONS (Soler et al. 2013)
# =============================================================================

class HistogramRelativeOrientations:
    """Relative orientation between a (polarization) angle field and a
    (column-density gradient) angle field (Soler+ 2013)."""

    def gradient_angle(self, image: np.ndarray) -> np.ndarray:
        """Angle (rad) of the image gradient; pi/2 - phi for relative-orientation convention."""
        gy, gx = np.gradient(np.asarray(image, float))
        phi = np.arctan2(gy, gx)
        return np.mod(np.pi / 2.0 - phi, np.pi)

    def relative_orientation(self, polarization_angle: np.ndarray,
                             gradient_angle: np.ndarray, nbins: int = 18) -> Dict[str, np.ndarray]:
        """Histogram of (polarization - gradient) orientation differences.

        Returns dict with 'bin_centers' (deg) and 'histogram' (normalised).
        Alignment (diff~0) crests high; perpendicularity (diff~90) troughs.
        """
        diff = np.mod(polarization_angle - gradient_angle, np.pi)
        hist, edges = np.histogram(diff, bins=nbins, range=(0, np.pi), density=True)
        centers = 0.5 * (edges[:-1] + edges[1:])
        return {'bin_centers_deg': np.rad2deg(centers), 'histogram': hist}

    def hro_parameter(self, polarization_angle: np.ndarray,
                      image: np.ndarray, nbins: int = 18) -> float:
        """Soler+ (2013) HRO parameter: projects gradient angle from the image
        onto the polarization direction and sums a (cos 2phi)-weighted moment."""
        gphi = self.gradient_angle(image)
        proj = np.cos(2.0 * np.mod(polarization_angle - gphi, np.pi))
        return float(np.nanmean(proj))


# =============================================================================
# TURBULENCE STATISTICS
# =============================================================================

class TurbulenceStatistics:
    """Dimensionless turbulence diagnostics (Mach numbers, sonic scale)."""

    K_B = 1.380649e-16
    M_H = 1.6735575e-24

    def _sound_speed(self, T_K: float, mu: float = 2.33) -> float:
        return np.sqrt(self.K_B * T_K / (mu * self.M_H))

    def mach_number(self, velocity_dispersion_cm_s: float, T_K: float,
                    mu: float = 2.33) -> float:
        """Sonic Mach number M = sigma_v / c_s."""
        return velocity_dispersion_cm_s / self._sound_speed(T_K, mu)

    def alfven_speed(self, B_gauss: float, number_density: float,
                     mu: float = 2.33) -> float:
        """Alfven speed v_A = B / sqrt(4*pi*rho)  [cm/s]."""
        rho = mu * self.M_H * number_density
        return B_gauss / np.sqrt(4.0 * np.pi * rho)

    def alfvenic_mach(self, velocity_dispersion_cm_s: float, B_gauss: float,
                      number_density: float, mu: float = 2.33) -> float:
        """M_A = sigma_v / v_A."""
        return velocity_dispersion_cm_s / self.alfven_speed(B_gauss, number_density, mu)
