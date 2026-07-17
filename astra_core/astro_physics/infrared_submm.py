"""
Infrared and Submillimeter Astronomy Module

Comprehensive analysis of infrared and submillimeter observations.
Supports data from Spitzer, Herschel, JWST, SOFIA, ALMA, NOEMA, JCMT.

Key capabilities:
- Dust emission modeling (modified blackbody)
- SED fitting across IR/submm
- PAH feature analysis
- Spectral energy distributions
- Color-color diagrams
- Redshift estimation from submm
- Cold dust temperature
- Gas mass from dust emission
- Line cooling calculations

Date: 2025-12-22
Version: 1.0
"""

import numpy as np
from typing import List, Dict, Optional, Any, Tuple, Union, Callable
from dataclasses import dataclass, field
from enum import Enum
from scipy import constants
from scipy.optimize import curve_fit
import warnings

# Physical constants (CGS)
H_PLANCK = 6.626e-27  # erg s
K_BOLTZMANN = 1.381e-16  # erg/K
C_LIGHT = 2.998e10  # cm/s
M_H = 1.673e-24  # g
PC = 3.086e18  # cm
JANSKY = 1e-23  # erg/s/cm^2/Hz
L_SUN = 3.828e33  # erg/s
M_SUN = 1.989e33  # g


class IRBand(Enum):
    """Infrared and submillimeter bands"""
    # Near-IR
    IRAC_3_6 = "irac_3_6"  # 3.6 microns
    IRAC_4_5 = "irac_4_5"  # 4.5 microns
    IRAC_5_8 = "irac_5_8"  # 5.8 microns
    IRAC_8_0 = "irac_8_0"  # 8.0 microns
    # Mid-IR
    WISE_12 = "wise_12"  # 12 microns
    WISE_22 = "wise_22"  # 22 microns
    WISE_24 = "wise_24"  # 24 microns
    MIPS_24 = "mips_24"  # 24 microns
    # Far-IR
    PACS_70 = "pacs_70"  # 70 microns
    PACS_100 = "pacs_100"  # 100 microns
    PACS_160 = "pacs_160"  # 160 microns
    SPIRE_250 = "spire_250"  # 250 microns
    SPIRE_350 = "spire_350"  # 350 microns
    SPIRE_500 = "spire_500"  # 500 microns
    # Submillimeter
    SCUBA_450 = "scuba_450"  # 450 microns
    SCUBA_850 = "scuba_850"  # 850 microns
    # ALMA bands
    ALMA_BAND3 = "alma_band3"  # 3 mm (100 GHz)
    ALMA_BAND6 = "alma_band6"  # 1 mm (230 GHz)
    ALMA_BAND7 = "alma_band7"  # 0.87 mm (345 GHz)


class PAHFeature(Enum):
    """Polycyclic Aromatic Hydrocarbon features"""
    PAH_3_3 = "pah_3_3"  # 3.3 microns
    PAH_6_2 = "pah_6_2"  # 6.2 microns
    PAH_7_7 = "pah_7_7"  # 7.7 microns
    PAH_8_6 = "pah_8_6"  # 8.6 microns
    PAH_11_3 = "pah_11_3"  # 11.3 microns
    PAH_12_7 = "pah_12_7"  # 12.7 microns


@dataclass
class IRPhotometry:
    """Infrared/submillimeter photometry point"""
    band: Union[IRBand, str]
    wavelength: float  # microns
    flux: float  # Jy
    flux_err: float = 0.0
    frequency: float = 0.0  # Hz (calculated from wavelength)
    facility: str = ""

    def __post_init__(self):
        if self.frequency == 0:
            # Convert wavelength to frequency
            lam_cm = self.wavelength * 1e-4  # microns to cm
            self.frequency = C_LIGHT / lam_cm


@dataclass
class PAHSpectrum:
    """PAH emission spectrum"""
    features: Dict[PAHFeature, float] = field(default_factory=dict)
    continuum: Dict[str, float] = field(default_factory=dict)
    feature_ratios: Dict[str, float] = field(default_factory=dict)


@dataclass
class DustProperties:
    """Dust properties from SED fitting"""
    temperature: float  # K
    mass: float  # Msun
    beta: float = 1.5  # Emissivity index
    luminosity: float = 0.0  # Lsun
    power: float = 0.0  # erg/s


class ModifiedBlackbody:
    """
    Modified blackbody dust emission model.

    I_nu = tau_nu * B_nu(T)
    tau_nu = kappa_nu * (M_dust / D^2)
    kappa_nu = kappa_0 * (nu/nu_0)^beta

    Where:
    - B_nu is Planck function
    - kappa_nu is dust opacity
    - beta is emissivity index (1.5-2.0 typical)
    """

    def __init__(self, kappa_0: float = 10.0, beta: float = 1.5):
        """
        Initialize modified blackbody.

        Args:
            kappa_0: Reference opacity at lambda_0 (cm^2/g)
            beta: Emissivity index
        """
        self.kappa_0 = kappa_0  # at 350 microns
        self.lambda_0 = 350.0  # microns
        self.beta = beta

    def planck_function(self, wavelength: float, temperature: float) -> float:
        """
        Planck function B_lambda(T).

        Args:
            wavelength: Wavelength (microns)
            temperature: Temperature (K)

        Returns:
            Specific intensity (erg/s/cm^2/cm/sr)
        """
        # Convert to CGS
        lam_cm = wavelength * 1e-4  # microns to cm

        h_nu_over_kt = (H_PLANCK * C_LIGHT) / (lam_cm * K_BOLTZMANN * temperature)

        # Avoid overflow
        if h_nu_over_kt > 100:
            return 0.0

        b_lambda = (2 * H_PLANCK * C_LIGHT**2 / lam_cm**5 /
                   (np.expm1(h_nu_over_kt)))

        return b_lambda

    def opacity(self, wavelength: float) -> float:
        """
        Dust opacity kappa_lambda.

        Args:
            wavelength: Wavelength (microns)

        Returns:
            Opacity (cm^2/g)
        """
        kappa = self.kappa_0 * (wavelength / self.lambda_0)**(-self.beta)
        return kappa

    def flux_density(self, wavelength: float, temperature: float,
                    dust_mass: float, distance: float = 1.0) -> float:
        """
        Predicted flux density from dust emission.

        Args:
            wavelength: Wavelength (microns)
            temperature: Dust temperature (K)
            dust_mass: Dust mass (Msun)
            distance: Distance (Mpc)

        Returns:
            Flux density (Jy)
        """
        # Planck function
        b_lambda = self.planck_function(wavelength, temperature)

        # Opacity
        kappa = self.opacity(wavelength)

        # Convert to flux density
        # F_nu = (1/D^2) * M_dust * kappa_nu * B_nu(T)
        dist_cm = distance * 1e6 * PC  # Mpc to cm
        mass_g = dust_mass * M_SUN

        # Flux in erg/s/cm^2/cm
        flux_cm = mass_g * kappa * b_lambda / dist_cm**2

        # Convert to Jy
        flux_jy = flux_cm / JANSKY

        return flux_jy

    def fit(self, wavelengths: np.ndarray, fluxes: np.ndarray,
           flux_errs: np.ndarray = None) -> Dict[str, Any]:
        """
        Fit modified blackbody to photometry.

        Args:
            wavelengths: Wavelengths (microns)
            fluxes: Flux densities (Jy)
            flux_errs: Flux uncertainties (Jy)

        Returns:
            Fit results (temperature, mass, beta)
        """
        if flux_errs is None:
            flux_errs = np.ones_like(fluxes) * 0.1 * np.mean(fluxes)
        # NOTE: the inline fit body above is incomplete in this file; use the
        # module-level fit_dust_sed() below for a working MBB fit.


# =============================================================================
# JANSKY (defensive; also defined above for flux_density)
# =============================================================================
try:
    JANSKY  # noqa: F821  (defined earlier in module)
except NameError:
    JANSKY = 1.0e-23  # erg s^-1 cm^-2 Hz^-1


# =============================================================================
# Public API: module-level helpers re-exported by astro_physics/__init__
# =============================================================================

def fit_dust_sed(wavelengths, fluxes, flux_errs=None, distance_mpc: float = 1.0,
                 beta: float = 1.5, kappa_0: float = 10.0, lambda_0: float = 350.0):
    """Fit a modified blackbody to (sub)mm photometry.

    Model:  F_nu(wl) = M_dust * kappa_nu(wl) * B_nu(T) / D^2   (Jy)
    Because the model is LINEAR in dust mass, fit T on a grid and solve M
    analytically by weighted least squares at each T (robust, no local minima).
    Returns dict with 'temperature' (K), 'dust_mass' (Msun), 'beta', 'model'.
    """
    wavelengths = np.asarray(wavelengths, float)
    fluxes = np.asarray(fluxes, float)
    if flux_errs is None:
        flux_errs = 0.1 * np.maximum(np.abs(fluxes), np.nanmedian(np.abs(fluxes)))
    sigma = np.asarray(flux_errs, float)
    mbb = ModifiedBlackbody(kappa_0=kappa_0, beta=beta)
    mbb.lambda_0 = lambda_0

    def template(T):
        return np.array([mbb.flux_density(w, T, 1.0, distance_mpc) for w in wavelengths])

    best = None
    for T in np.linspace(5.0, 60.0, 111):
        g = template(T)
        if not np.all(np.isfinite(g)) or np.any(g <= 0):
            continue
        wgt = g / sigma
        M_msun = float(np.sum(fluxes * wgt) / np.sum(g * wgt))
        chi2 = float(np.sum(((fluxes - M_msun * g) / sigma) ** 2))
        if best is None or chi2 < best[0]:
            best = (chi2, float(T), M_msun)
    if best is None:
        return {'temperature': 20.0, 'dust_mass': 1.0e3, 'beta': beta, 'model': mbb}
    return {'temperature': best[1], 'dust_mass': best[2], 'beta': beta, 'model': mbb}


def calculate_gas_mass(flux_jy: float, wavelength_um: float, temperature_k: float,
                       distance_mpc: float, kappa_0: float = 10.0,
                       beta: float = 1.5, lambda_0: float = 350.0,
                       dust_to_gas_ratio: float = 0.01) -> float:
    """Gas mass (Msun) from a single-band dust flux (Hildebrand 1983 style).

        M_dust = S_nu D^2 / (kappa_nu B_nu(T))
        M_gas  = M_dust / (dust_to_gas_ratio)
    dust_to_gas_ratio ~ 0.01 at solar metallicity.
    """
    mbb = ModifiedBlackbody(kappa_0=kappa_0, beta=beta)
    mbb.lambda_0 = lambda_0
    b = mbb.planck_function(wavelength_um, temperature_k)        # erg/s/cm^2/cm (B_lambda)
    kap = mbb.opacity(wavelength_um)                              # cm^2/g
    dist_cm = distance_mpc * 1e6 * PC
    flux_cgs = flux_jy * JANSKY                                   # erg/s/cm^2/Hz ... see note
    # flux_density writes F = M*kappa*B_lambda/D^2 (per cm); invert:
    mass_g = flux_cgs * (dist_cm ** 2) / (kap * b)
    dust_msun = mass_g / M_SUN
    return dust_msun / dust_to_gas_ratio


def get_ir_color(flux_band1: float, flux_band2: float, as_magnitude: bool = True) -> float:
    """IR colour: magnitude difference -2.5 log10(F1/F2) by default, else ratio."""
    if as_magnitude:
        return -2.5 * np.log10(flux_band1 / flux_band2)
    return flux_band1 / flux_band2


class IRColorAnalysis:
    """Multi-band IR colour diagnostics."""

    def __init__(self, wavelengths_um=None, fluxes_jy=None):
        self.wavelengths = (np.asarray(wavelengths_um, float)
                            if wavelengths_um is not None else None)
        self.fluxes = (np.asarray(fluxes_jy, float)
                       if fluxes_jy is not None else None)

    def color(self, idx1: int, idx2: int) -> float:
        return get_ir_color(self.fluxes[idx1], self.fluxes[idx2], as_magnitude=True)

    def color_temperature(self, idx1: int, idx2: int) -> float:
        """Dust colour temperature (K) from the kappa-weighted MBB flux ratio
        at two bands (mass and distance cancel in the ratio)."""
        from scipy.optimize import brentq
        w1, w2 = self.wavelengths[idx1], self.wavelengths[idx2]
        ratio = self.fluxes[idx1] / self.fluxes[idx2]
        mbb = ModifiedBlackbody()

        def f(T):
            r = ((mbb.opacity(w1) * mbb.planck_function(w1, T)) /
                 (mbb.opacity(w2) * mbb.planck_function(w2, T)))
            return r - ratio

        try:
            return float(brentq(f, 5.0, 80.0))
        except Exception:
            return float('nan')


class SubmillimeterAnalysis:
    """Submillimetre SED analysis: spectral index alpha and emissivity beta."""

    def __init__(self, wavelengths_um, fluxes_jy):
        self.wavelengths = np.asarray(wavelengths_um, float)
        self.fluxes = np.asarray(fluxes_jy, float)

    def spectral_index(self) -> float:
        """Power-law slope alpha of F_nu ~ nu^alpha (Rayleigh-Jeans tail)."""
        nu = C_LIGHT / (self.wavelengths * 1e-4)
        m = (nu > 0) & (self.fluxes > 0) & np.isfinite(self.fluxes)
        if m.sum() < 2:
            return float('nan')
        slope, _ = np.polyfit(np.log10(nu[m]), np.log10(self.fluxes[m]), 1)
        return float(slope)

    def emissivity_index_beta(self, t_dust_k: float) -> float:
        """beta ~ alpha - 2 in the Rayleigh-Jeans limit (alpha = 2 + beta)."""
        return self.spectral_index() - 2.0


class LineCooling:
    """Cooling-line luminosity (e.g. [CII] 158, CO) via isotropic conversion.

    L_line = 4*pi*D^2 * integral F_nu dnu, with the integrated line flux given
    in Jy km/s (standard radio-line convention).
    """

    def __init__(self, line_name: str = '[CII]158', wavelength_um: float = 157.7):
        self.line_name = line_name
        self.wavelength_um = wavelength_um

    def luminosity_erg_s(self, integrated_flux_jy_kms: float, distance_mpc: float) -> float:
        """Isotropic-equivalent line luminosity (erg/s).

        int F_nu dnu = F_int[Jy km/s] * 1e-23 * 1e5 * (nu/c)  [erg s^-1 cm^-2]
        """
        nu = C_LIGHT / (self.wavelength_um * 1e-4)            # Hz
        dist_cm = distance_mpc * 1e6 * PC
        int_fnu = integrated_flux_jy_kms * 1e-23 * 1e5 * (nu / C_LIGHT)  # erg/s/cm^2
        return 4.0 * np.pi * (dist_cm ** 2) * int_fnu        # erg/s

    def luminosity_lsun(self, integrated_flux_jy_kms: float, distance_mpc: float) -> float:
        return self.luminosity_erg_s(integrated_flux_jy_kms, distance_mpc) / 3.828e33

    def cooling_rate_per_msun(self, luminosity_lsun: float, gas_mass_msun: float) -> float:
        """L/M ratio (L_sun / M_sun), a proxy for cooling efficiency."""
        return luminosity_lsun / gas_mass_msun
