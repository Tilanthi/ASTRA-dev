"""
Spectral line analysis: line-profile fitting, identification, optical-depth
correction, and optically-thin column-density estimation.

  * Gaussian and Voigt profile fitting (scipy.special.voigt_profile).
  * Hyperfine-structure fitting (sum of components at relative offsets).
  * Line identification by frequency against a reference catalogue.
  * Column density from an optically-thin emission line
    (N_u = (8 pi k nu / h c^2 A_ul) * integral T_R dv; total via a linear-rotor
    partition function Q ~ kT/(hB)).

References:
  scipy.special.voigt_profile (Olivero & Longbothum 1977 for Voigt);
  Draine, "Physics of the ISM and IGM", Ch. 6;
  Wilson, Rohlfs & Huttemeister, "Tools of Radio Astronomy".
"""

import numpy as np
from dataclasses import dataclass
from typing import Optional, List, Tuple
from scipy.optimize import curve_fit
from scipy.special import voigt_profile

# CGS constants
H_PLANCK = 6.62607015e-27
K_BOLTZMANN = 1.380649e-16
C_LIGHT = 2.99792458e10


@dataclass
class LineFitResult:
    amplitude: float
    center: float
    width: float           # Gaussian sigma (velocity) or Voigt sigma
    gamma: float = 0.0     # Lorentzian width (Voigt only)
    baseline: float = 0.0
    center_err: float = 0.0
    success: bool = True


def _gaussian(v, A, v0, sigma, b):
    return A * np.exp(-0.5 * ((v - v0) / sigma) ** 2) + b


def _voigt(v, A, v0, sigma, gamma, b):
    return A * voigt_profile(v - v0, sigma, gamma) + b


class GaussianLineFitter:
    """Fit A*exp(-(v-v0)^2/2sigma^2) + baseline to a spectral line."""

    def fit(self, velocity, flux, p0=None) -> LineFitResult:
        velocity = np.asarray(velocity, float)
        flux = np.asarray(flux, float)
        if p0 is None:
            i = int(np.argmax(flux - np.median(flux)))
            p0 = [flux[i] - np.median(flux), velocity[i],
                  (velocity.max() - velocity.min()) / 20.0, np.median(flux)]
        try:
            popt, pcov = curve_fit(_gaussian, velocity, flux, p0=p0, maxfev=10000)
            err = np.sqrt(np.diag(pcov))
            return LineFitResult(amplitude=popt[0], center=popt[1], width=abs(popt[2]),
                                 baseline=popt[3], center_err=err[1], success=True)
        except Exception:
            return LineFitResult(0.0, 0.0, 0.0, success=False)

    @staticmethod
    def model(velocity, amplitude, center, width, baseline=0.0):
        return _gaussian(velocity, amplitude, center, width, baseline)


class VoigtProfileFitter:
    """Fit a Voigt profile (convolution of Gaussian and Lorentzian)."""

    def fit(self, velocity, flux, p0=None) -> LineFitResult:
        velocity = np.asarray(velocity, float)
        flux = np.asarray(flux, float)
        if p0 is None:
            i = int(np.argmax(flux - np.median(flux)))
            p0 = [flux[i] - np.median(flux), velocity[i],
                  (velocity.max() - velocity.min()) / 20.0,
                  (velocity.max() - velocity.min()) / 40.0, np.median(flux)]
        try:
            popt, _ = curve_fit(_voigt, velocity, flux, p0=p0, maxfev=20000)
            return LineFitResult(amplitude=popt[0], center=popt[1], width=abs(popt[2]),
                                 gamma=abs(popt[3]), baseline=popt[4], success=True)
        except Exception:
            return LineFitResult(0.0, 0.0, 0.0, success=False)


class HyperfineStructureFitter:
    """Fit a hyperfine multiplet = sum of Gaussians at (center + offsets) with
    fixed relative intensities, sharing a common width and baseline.

    Args:
        offsets: velocity offsets of each hfs component (same units as `velocity`)
        relative_intensities: relative strengths of each component
    """

    def __init__(self, offsets: np.ndarray, relative_intensities: np.ndarray):
        self.off = np.asarray(offsets, float)
        self.rel = np.asarray(relative_intensities, float)

    def fit(self, velocity, flux, p0=None) -> LineFitResult:
        velocity = np.asarray(velocity, float)
        flux = np.asarray(flux, float)
        off, rel = self.off, self.rel

        def model(v, A, v0, sigma, b):
            total = np.zeros_like(v)
            for o, r in zip(off, rel):
                total += r * np.exp(-0.5 * ((v - v0 - o) / sigma) ** 2)
            return A * total / rel.max() + b

        if p0 is None:
            i = int(np.argmax(flux - np.median(flux)))
            p0 = [flux[i] - np.median(flux), velocity[i] - float(off[np.argmax(rel)]),
                  (velocity.max() - velocity.min()) / 30.0, np.median(flux)]
        try:
            popt, _ = curve_fit(model, velocity, flux, p0=p0, maxfev=20000)
            return LineFitResult(amplitude=popt[0], center=popt[1], width=abs(popt[2]),
                                 baseline=popt[3], success=True)
        except Exception:
            return LineFitResult(0.0, 0.0, 0.0, success=False)


class ColumnDensityCalculator:
    """Column densities from optically-thin line emission.

    Upper-state column (optically thin emission):
        N_u = (8 pi k nu / h c^2 A_ul) * integral T_R dv
    Total column via a linear-rotor partition function Q(T_ex) ~ kT_ex/(hB):
        N_tot = N_u * Q(T_ex)/g_u * exp(E_u / k T_ex)
    """

    def upper_state(self, integrated_brightness_K_cms: float, nu_Hz: float,
                    A_ul: float) -> float:
        """N_u (cm^-2) from the velocity-integrated brightness temperature."""
        return (8.0 * np.pi * K_BOLTZMANN * nu_Hz) / (H_PLANCK * C_LIGHT ** 2 * A_ul) \
            * integrated_brightness_K_cms

    def total_linear_rotor(self, integrated_brightness_K_cms: float, nu_Hz: float,
                           A_ul: float, E_upper_K: float, g_upper: float,
                           T_ex: float, B_Hz: float) -> float:
        """Total column (cm^-2) assuming a linear-rotor partition function."""
        N_u = self.upper_state(integrated_brightness_K_cms, nu_Hz, A_ul)
        Q = K_BOLTZMANN * T_ex / (H_PLANCK * B_Hz)            # linear rotor, T >> hB/k
        return N_u * (Q / g_upper) * np.exp(E_upper_K / T_ex)


class OpticalDepthCorrector:
    """Recover line-center optical depth and total column from a brightness
    temperature, given an excitation temperature.

    T_R = (J(T_ex) - J(T_bg)) (1 - exp(-tau))  ->  tau = -ln(1 - T_R/(J(T_ex)-J(T_bg)))
    """

    def __init__(self, nu_Hz: float, T_bg: float = 2.725):
        self.nu = nu_Hz
        self.Tbg = T_bg

    def _J(self, T):
        x = H_PLANCK * self.nu / (K_BOLTZMANN * T)
        return (H_PLANCK * self.nu / K_BOLTZMANN) / np.expm1(x)

    def tau(self, T_R: float, T_ex: float) -> float:
        denom = self._J(T_ex) - self._J(self.Tbg)
        frac = T_R / denom
        if frac >= 1.0:
            return np.inf
        return -np.log(1.0 - frac)


class LineIdentifier:
    """Identify an observed frequency against a reference catalogue."""

    def __init__(self, catalogue: List[Tuple[str, float]]):
        """catalogue: list of (name, rest_frequency_Hz)."""
        self.cat = catalogue

    def identify(self, obs_freq_Hz: float, tolerance_Hz: float,
                 velocity_max_km_s: float = None) -> Optional[Tuple[str, float]]:
        tol = tolerance_Hz
        if velocity_max_km_s is not None:
            tol = max(tol, velocity_max_km_s * 1e5 / C_LIGHT * obs_freq_Hz)
        best = None
        for name, rest in self.cat:
            if abs(obs_freq_Hz - rest) <= tol:
                if best is None or abs(obs_freq_Hz - rest) < abs(obs_freq_Hz - best[1]):
                    best = (name, rest)
        return best


def fit_gaussian_line(velocity, flux, **kw) -> LineFitResult:
    return GaussianLineFitter().fit(velocity, flux, **kw)


def identify_line(obs_freq_Hz: float, catalogue=None, tolerance_Hz: float = 1e7):
    if catalogue is None:
        catalogue = [('CO(1-0)', 115.27120180e9), ('CO(2-1)', 230.53800000e9),
                     ('13CO(1-0)', 110.20135300e9), ('CII', 1900.53690000e9),
                     ('CS(2-1)', 97.98095000e9)]
    return LineIdentifier(catalogue).identify(obs_freq_Hz, tolerance_Hz)


__all__ = [
    'LineFitResult', 'GaussianLineFitter', 'VoigtProfileFitter',
    'HyperfineStructureFitter', 'LineIdentifier', 'OpticalDepthCorrector',
    'ColumnDensityCalculator', 'fit_gaussian_line', 'identify_line',
]
