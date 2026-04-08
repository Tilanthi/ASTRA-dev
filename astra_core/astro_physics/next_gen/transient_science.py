"""
Transient Science Module

Provides capabilities for transient classification, light curve fitting,
and physical modeling of supernovae, GRBs, kilonovae, and other transients.

Date: 2025-12-15
"""

import numpy as np
from typing import List, Dict, Optional, Any, Tuple, Union, Callable
from dataclasses import dataclass, field
from enum import Enum
from abc import ABC, abstractmethod
import warnings

# Physical constants (CGS)
C_LIGHT = 2.998e10  # cm/s
M_SUN = 1.989e33  # g
L_SUN = 3.828e33  # erg/s
PC = 3.086e18  # cm
DAY = 86400.0  # seconds
KEV_TO_ERG = 1.602e-9
STEFAN_BOLTZMANN = 5.67e-5  # erg/cm^2/s/K^4


# NumPy 2.0 compatibility: trapz was renamed to trapezoid
def _trapz_compat(y, x=None, dx=1.0, axis=-1):
    """Compatibility wrapper for _trapz_compat (removed in NumPy 2.0)."""
    try:
        return np.trapezoid(y, x=x, dx=dx, axis=axis)
    except AttributeError:
        # Fallback for NumPy < 2.0
        return _trapz_compat(y, x=x, dx=dx, axis=axis)


class TransientType(Enum):
    """Classification of transient types"""
    SN_IA = "SN Ia"
    SN_IB = "SN Ib"
    SN_IC = "SN Ic"
    SN_IIP = "SN IIP"
    SN_IIL = "SN IIL"
    SN_IIN = "SN IIn"
    SN_IBN = "SN Ibn"
    TDE = "TDE"
    KILONOVA = "Kilonova"
    GRB_AFTERGLOW = "GRB Afterglow"
    NOVA = "Nova"
    LBV = "LBV"
    CV = "CV"
    UNKNOWN = "Unknown"


@dataclass
class LightCurve:
    """Container for light curve data"""
    times: np.ndarray  # MJD or days from reference
    mags: np.ndarray  # magnitudes
    mag_errs: np.ndarray  # magnitude errors
    band: str  # filter band
    flux: np.ndarray = None  # flux in mJy
    flux_errs: np.ndarray = None
    upper_limits: np.ndarray = None  # boolean mask

    def __post_init__(self):
        """Convert mags to flux if not provided"""
        if self.flux is None:
            # AB magnitude to mJy
            self.flux = 10**((23.9 - self.mags) / 2.5) * 1e-3
            self.flux_errs = self.flux * np.log(10) / 2.5 * self.mag_errs


@dataclass
class TransientFitResult:
    """Result from light curve fitting"""
    model_name: str
    parameters: Dict[str, float]
    uncertainties: Dict[str, float]
    chi_squared: float
    dof: int
    model_flux: np.ndarray
    residuals: np.ndarray
    classification: Optional[TransientType] = None
    metadata: Dict[str, Any] = field(default_factory=dict)


# =============================================================================
# SUPERNOVA MODELS
# =============================================================================

class SupernovaModels:
    """
    Forward models for supernova light curves.

    Includes Type Ia (stretch-luminosity), core-collapse models,
    and radioactive decay physics.
    """

    # Ni56 decay constants
    TAU_NI56 = 8.8 * DAY  # half-life 6.1 days
    TAU_CO56 = 111.3 * DAY  # half-life 77.1 days
    E_NI56 = 3.90e10  # erg/s/g (gamma-rays)
    E_CO56_GAMMA = 6.78e9  # erg/s/g (gamma-rays)
    E_CO56_POS = 1.43e9  # erg/s/g (positrons)

    def __init__(self):
        """Initialize supernova models"""
        self.template_cache = {}

    def arnett_model(self, t: np.ndarray, m_ni: float, m_ej: float,
                     v_ej: float, kappa: float = 0.2,
                     t0: float = 0.0) -> np.ndarray:
        """
        Arnett (1982) model for radioactively-powered SNe.

        Args:
            t: Time array (days from explosion)
            m_ni: Ni56 mass (solar masses)
            m_ej: Ejecta mass (solar masses)
            v_ej: Ejecta velocity (km/s)
            kappa: Opacity (cm^2/g)
            t0: Explosion time offset (days)

        Returns:
            Bolometric luminosity (erg/s)
        """
        t = np.asarray(t) - t0
        t = np.maximum(t, 0.01)  # Avoid t=0

        # Convert units
        m_ni_g = m_ni * M_SUN
        m_ej_g = m_ej * M_SUN
        v_ej_cm = v_ej * 1e5  # km/s to cm/s

        # Diffusion timescale (Arnett 1982, eq. 35)
        tau_m = np.sqrt(2 * kappa * m_ej_g / (13.8 * C_LIGHT * v_ej_cm))
        tau_m_days = tau_m / DAY

        # Dimensionless time
        x = t / tau_m_days

        # Radioactive heating rate
        def heating_rate(t_sec):
            """Total heating rate from Ni56 + Co56 chain"""
            t = t_sec  # already in seconds

            # Ni56 abundance
            f_ni = np.exp(-t / self.TAU_NI56)

            # Co56 abundance (from Ni56 decay)
            f_co = (self.TAU_CO56 / (self.TAU_CO56 - self.TAU_NI56)) * \
                   (np.exp(-t / self.TAU_CO56) - np.exp(-t / self.TAU_NI56))

            # Heating rate
            Q_ni = self.E_NI56 * f_ni
            Q_co = (self.E_CO56_GAMMA + self.E_CO56_POS) * f_co

            return m_ni_g * (Q_ni + Q_co)

        # Arnett's integral solution
        L = np.zeros_like(t, dtype=float)

        for i, ti in enumerate(t):
            if ti <= 0:
                L[i] = 0
                continue

            # Numerical integration of heating with diffusion
            t_sec = ti * DAY
            tau_m_sec = tau_m_days * DAY

            # Simple trapezoidal integration
            n_points = 100
            t_prime = np.linspace(0.01, t_sec, n_points)
            dt = t_prime[1] - t_prime[0]

            integrand = heating_rate(t_prime) * \
                       np.exp((t_prime / tau_m_sec)**2 - (t_sec / tau_m_sec)**2)

            L[i] = (2 / tau_m_sec) * np.exp(-(t_sec / tau_m_sec)**2) * \
                   _trapz_compat(integrand * t_prime / tau_m_sec, dx=dt / tau_m_sec)

        return L

    def sn_ia_template(self, t: np.ndarray, m_peak: float, stretch: float = 1.0,
                       color: float = 0.0, t_max: float = 0.0,
                       band: str = 'B') -> np.ndarray:
        """
        Type Ia supernova template with stretch-luminosity correction.

        Uses Phillips (1993) relation and SALT2-like parameterization.

        Args:
            t: Time array (days)
            m_peak: Peak magnitude
            stretch: Light curve stretch (x1 in SALT2)
            color: Color parameter (c in SALT2)
            t_max: Time of maximum
            band: Photometric band

        Returns:
            Apparent magnitude
        """
        # Stretch the time axis
        t_stretched = (t - t_max) / stretch

        # Template shape (simplified Hsiao-like)
        # Rise phase
        tau_rise = 17.0  # days
        tau_fall1 = 40.0  # initial decline
        tau_fall2 = 100.0  # late decline

        mag = np.zeros_like(t, dtype=float)

        # Before maximum
        mask_rise = t_stretched < 0
        mag[mask_rise] = m_peak - 2.5 * np.log10(
            1 - np.exp(t_stretched[mask_rise] / tau_rise)
        )

        # After maximum - two component decline
        mask_fall = t_stretched >= 0
        decline = 0.8 * np.exp(-t_stretched[mask_fall] / tau_fall1) + \
                  0.2 * np.exp(-t_stretched[mask_fall] / tau_fall2)
        mag[mask_fall] = m_peak - 2.5 * np.log10(decline)

        # Apply color correction (Tripp relation)
        # alpha ~ 0.14, beta ~ 3.1 for standard SALT2
        alpha = 0.14
        beta = 3.1
        mag = mag + alpha * (stretch - 1) + beta * color

        return mag

    def sn_iip_plateau(self, t: np.ndarray, m_plateau: float,
                       t_plateau: float = 100.0, t0: float = 0.0,
                       drop: float = 2.0) -> np.ndarray:
        """
        Type IIP supernova with hydrogen recombination plateau.

        Args:
            t: Time (days)
            m_plateau: Plateau magnitude
            t_plateau: Plateau duration (days)
            t0: Explosion time
            drop: Magnitude drop after plateau

        Returns:
            Apparent magnitude
        """
        t_rel = t - t0
        t_rel = np.maximum(t_rel, 0.01)

        mag = np.zeros_like(t, dtype=float)

        # Rise phase (shock breakout cooling)
        tau_rise = 5.0
        mask_rise = t_rel < 20
        mag[mask_rise] = m_plateau + 2.0 - 0.1 * t_rel[mask_rise]

        # Plateau phase
        mask_plateau = (t_rel >= 20) & (t_rel < t_plateau)
        # Slight decline during plateau
        mag[mask_plateau] = m_plateau + 0.01 * (t_rel[mask_plateau] - 20)

        # Post-plateau drop and Co56 tail
        mask_tail = t_rel >= t_plateau
        t_tail = t_rel[mask_tail] - t_plateau

        # Rapid transition
        transition = 1 - np.exp(-t_tail / 10.0)

        # Co56 decline rate: 0.98 mag/100 days
        co56_decline = 0.0098 * t_tail

        mag[mask_tail] = m_plateau + drop * transition + co56_decline

        return mag

    def bolometric_to_band(self, L_bol: np.ndarray, T_eff: np.ndarray,
                           band: str = 'V', distance_pc: float = 10.0) -> np.ndarray:
        """
        Convert bolometric luminosity to band magnitude.

        Args:
            L_bol: Bolometric luminosity (erg/s)
            T_eff: Effective temperature (K)
            band: Photometric band
            distance_pc: Distance in parsecs

        Returns:
            Apparent magnitude
        """
        # Band effective wavelengths (Angstroms)
        band_lambda = {
            'U': 3600, 'B': 4400, 'V': 5500, 'R': 6400, 'I': 8000,
            'g': 4770, 'r': 6231, 'i': 7625, 'z': 9134
        }

        if band not in band_lambda:
            band = 'V'

        lam = band_lambda[band] * 1e-8  # cm

        # Blackbody spectral radiance
        h = 6.626e-27  # erg s
        k = 1.381e-16  # erg/K

        B_lambda = (2 * h * C_LIGHT**2 / lam**5) / \
                   (np.exp(h * C_LIGHT / (lam * k * T_eff)) - 1)

        # Bolometric correction (approximate)
        BC = 2.5 * np.log10(STEFAN_BOLTZMANN * T_eff**4 /
                           (np.pi * B_lambda * 1e8))  # per Angstrom

        # Absolute bolometric magnitude
        M_bol = -2.5 * np.log10(L_bol / L_SUN) + 4.74

        # Absolute band magnitude
        M_band = M_bol - BC

        # Apparent magnitude
        d_cm = distance_pc * PC
        m_band = M_band + 5 * np.log10(distance_pc / 10)

        return m_band


# =============================================================================
# GRB AFTERGLOW MODEL
# =============================================================================

class GRBAfterglowModel:
    """
    GRB afterglow synchrotron emission model.

    Based on Sari, Piran & Narayan (1998) standard fireball model.
    """

    def __init__(self):
        """Initialize GRB afterglow model"""
        pass

    def synchrotron_spectrum(self, nu: np.ndarray, t: float,
                             E_iso: float = 1e52, n: float = 1.0,
                             epsilon_e: float = 0.1, epsilon_B: float = 0.01,
                             p: float = 2.3, z: float = 1.0,
                             d_L: float = None) -> np.ndarray:
        """
        Calculate synchrotron flux density at given frequencies.

        Args:
            nu: Observed frequency array (Hz)
            t: Observer time (days)
            E_iso: Isotropic equivalent energy (erg)
            n: Circumburst density (cm^-3)
            epsilon_e: Fraction of energy in electrons
            epsilon_B: Fraction of energy in magnetic field
            p: Electron power-law index
            z: Redshift
            d_L: Luminosity distance (cm), calculated if None

        Returns:
            Flux density (mJy)
        """
        if d_L is None:
            # Simple Hubble law for now
            H0 = 70  # km/s/Mpc
            d_L = (z * C_LIGHT / (H0 * 1e5)) * 3.086e24  # cm

        # Convert time to seconds
        t_sec = t * DAY / (1 + z)  # source frame

        # Characteristic Lorentz factor (adiabatic evolution)
        # Gamma ~ (E / (n * m_p * c^5 * t^3))^(1/8)
        m_p = 1.67e-24  # g
        Gamma = 10 * (E_iso / 1e52)**0.125 * n**(-0.125) * \
                (t_sec / DAY)**(-0.375)
        Gamma = max(Gamma, 1.1)

        # Magnetic field strength
        B = np.sqrt(32 * np.pi * epsilon_B * n * m_p) * Gamma * C_LIGHT

        # Characteristic frequencies
        m_e = 9.11e-28  # g
        e = 4.8e-10  # esu

        # Minimum Lorentz factor of electrons
        gamma_m = epsilon_e * (p - 2) / (p - 1) * (m_p / m_e) * Gamma

        # Synchrotron frequency for gamma_m
        nu_m = 3.7e6 * epsilon_e**2 * epsilon_B**0.5 * E_iso**(0.5) * \
               (t_sec / DAY)**(-1.5) * (1 + z)**0.5  # Hz

        # Cooling frequency
        nu_c = 2.7e12 * epsilon_B**(-1.5) * E_iso**(-0.5) * n**(-1) * \
               (t_sec / DAY)**(-0.5) * (1 + z)**(-0.5)  # Hz

        # Peak flux
        F_max = 1.1 * epsilon_B**0.5 * E_iso * n**0.5 / (d_L**2) * \
                (1 + z)  # mJy

        # Spectrum segments (slow cooling: nu_m < nu_c)
        flux = np.zeros_like(nu, dtype=float)

        if nu_m < nu_c:
            # Slow cooling
            mask1 = nu < nu_m
            mask2 = (nu >= nu_m) & (nu < nu_c)
            mask3 = nu >= nu_c

            flux[mask1] = F_max * (nu[mask1] / nu_m)**(1/3)
            flux[mask2] = F_max * (nu[mask2] / nu_m)**(-(p-1)/2)
            flux[mask3] = F_max * (nu_c / nu_m)**(-(p-1)/2) * \
                         (nu[mask3] / nu_c)**(-p/2)
        else:
            # Fast cooling
            mask1 = nu < nu_c
            mask2 = (nu >= nu_c) & (nu < nu_m)
            mask3 = nu >= nu_m

            flux[mask1] = F_max * (nu[mask1] / nu_c)**(1/3)
            flux[mask2] = F_max * (nu[mask2] / nu_c)**(-0.5)
            flux[mask3] = F_max * (nu_m / nu_c)**(-0.5) * \
                         (nu[mask3] / nu_m)**(-p/2)

        return flux

    def light_curve(self, t: np.ndarray, nu: float = 1e14,
                    **kwargs) -> np.ndarray:
        """
        Calculate light curve at fixed frequency.

        Args:
            t: Time array (days)
            nu: Observed frequency (Hz)
            **kwargs: Parameters for synchrotron_spectrum

        Returns:
            Flux density array (mJy)
        """
        flux = np.array([
            self.synchrotron_spectrum(np.array([nu]), ti, **kwargs)[0]
            for ti in t
        ])
        return flux

    def jet_break_correction(self, t: np.ndarray, t_jet: float,
                             flux_no_break: np.ndarray,
                             p: float = 2.3) -> np.ndarray:
        """
        Apply jet break correction to light curve.

        Args:
            t: Time array (days)
            t_jet: Jet break time (days)
            flux_no_break: Flux without jet break
            p: Electron power-law index

        Returns:
            Corrected flux array
        """
        # Post-jet break: flux ~ t^(-p) instead of t^(-(3p-3)/4)
        flux = flux_no_break.copy()

        mask = t > t_jet
        if np.any(mask):
            # Smooth transition
            t_trans = 0.5 * t_jet  # transition width
            transition = 0.5 * (1 + np.tanh((t[mask] - t_jet) / t_trans))

            # Steeper decline
            pre_break_slope = -(3 * p - 3) / 4
            post_break_slope = -p

            extra_decline = (t[mask] / t_jet)**(post_break_slope - pre_break_slope)
            flux[mask] = flux[mask] * (1 - transition) + \
                        flux[mask] * extra_decline * transition

        return flux


# =============================================================================
# KILONOVA MODEL
# =============================================================================

class KilonovaModel:
    """
    Kilonova model for neutron star merger electromagnetic counterparts.

    Includes r-process heating and lanthanide opacity effects.
    """

    # R-process heating rate parameters (Korobkin et al. 2012)
    HEATING_PARAMS = {
        'epsilon_0': 2e18,  # erg/s/g at 1 day
        'alpha': 1.3,  # time power-law
        't_0': 1.0  # reference time (days)
    }

    def __init__(self):
        """Initialize kilonova model"""
        pass

    def heating_rate(self, t: np.ndarray, m_ej: float,
                     thermalization_efficiency: float = 0.5) -> np.ndarray:
        """
        R-process radioactive heating rate.

        Args:
            t: Time (days)
            m_ej: Ejecta mass (solar masses)
            thermalization_efficiency: Fraction of decay energy thermalized

        Returns:
            Heating rate (erg/s)
        """
        eps_0 = self.HEATING_PARAMS['epsilon_0']
        alpha = self.HEATING_PARAMS['alpha']
        t_0 = self.HEATING_PARAMS['t_0']

        m_ej_g = m_ej * M_SUN

        # Heating rate with time dependence
        eps = eps_0 * (t / t_0)**(-alpha)

        # Thermalization efficiency decreases at late times
        eta = thermalization_efficiency * np.exp(-(t / 10.0)**0.5)

        return eta * eps * m_ej_g

    def luminosity(self, t: np.ndarray, m_ej: float, v_ej: float,
                   kappa: float = 10.0, kappa_gamma: float = 1e4) -> np.ndarray:
        """
        Kilonova bolometric luminosity using Arnett-like model.

        Args:
            t: Time (days)
            m_ej: Ejecta mass (solar masses)
            v_ej: Ejecta velocity (c)
            kappa: Optical opacity (cm^2/g)
            kappa_gamma: Gamma-ray opacity (cm^2/g)

        Returns:
            Bolometric luminosity (erg/s)
        """
        t = np.asarray(t)
        t = np.maximum(t, 0.01)

        m_ej_g = m_ej * M_SUN
        v_ej_cm = v_ej * C_LIGHT

        # Diffusion timescale
        tau_d = np.sqrt(3 * kappa * m_ej_g / (4 * np.pi * v_ej_cm * C_LIGHT))
        tau_d_days = tau_d / DAY

        # Arnett's rule at peak: L_peak ~ heating_rate(t_peak)
        # More sophisticated: solve diffusion equation

        L = np.zeros_like(t, dtype=float)

        for i, ti in enumerate(t):
            t_sec = ti * DAY

            # Numerical integration
            n_points = 100
            t_prime = np.linspace(0.01, ti, n_points)

            Q = self.heating_rate(t_prime, m_ej)

            # Diffusion kernel
            kernel = (2 / tau_d_days) * t_prime / tau_d_days * \
                    np.exp((t_prime / tau_d_days)**2 - (ti / tau_d_days)**2)

            L[i] = _trapz_compat(Q * kernel, t_prime)

        return L

    def two_component_model(self, t: np.ndarray,
                            m_red: float = 0.01, v_red: float = 0.1,
                            m_blue: float = 0.01, v_blue: float = 0.3) -> Tuple[np.ndarray, np.ndarray]:
        """
        Two-component kilonova: lanthanide-rich (red) + lanthanide-poor (blue).

        Args:
            t: Time (days)
            m_red: Red component mass (M_sun)
            v_red: Red component velocity (c)
            m_blue: Blue component mass (M_sun)
            v_blue: Blue component velocity (c)

        Returns:
            (L_red, L_blue) luminosities (erg/s)
        """
        # High opacity for lanthanide-rich ejecta
        L_red = self.luminosity(t, m_red, v_red, kappa=10.0)

        # Low opacity for lanthanide-poor ejecta
        L_blue = self.luminosity(t, m_blue, v_blue, kappa=0.5)

        return L_red, L_blue

    def effective_temperature(self, L: np.ndarray, t: np.ndarray,
                              v_ej: float) -> np.ndarray:
        """
        Estimate effective temperature from luminosity.

        Args:
            L: Luminosity (erg/s)
            t: Time (days)
            v_ej: Ejecta velocity (c)

        Returns:
            Effective temperature (K)
        """
        # Photospheric radius: R ~ v * t
        R = v_ej * C_LIGHT * t * DAY

        # Stefan-Boltzmann
        T_eff = (L / (4 * np.pi * R**2 * STEFAN_BOLTZMANN))**0.25

        return T_eff


# =============================================================================
# LIGHT CURVE FITTER
# =============================================================================

class LightCurveFitter:
    """
    General-purpose light curve fitting with multiple models.
    """

    def __init__(self):
        """Initialize fitter"""
        self.sn_models = SupernovaModels()
        self.grb_model = GRBAfterglowModel()
        self.kn_model = KilonovaModel()

    def fit_polynomial(self, lc: LightCurve, degree: int = 3,
                       t_ref: float = None) -> TransientFitResult:
        """
        Fit polynomial to light curve (for smooth interpolation).

        Args:
            lc: Light curve data
            degree: Polynomial degree
            t_ref: Reference time for centering

        Returns:
            Fit result
        """
        if t_ref is None:
            t_ref = np.median(lc.times)

        t_centered = lc.times - t_ref

        # Weighted polynomial fit
        weights = 1.0 / lc.mag_errs**2

        coeffs = np.polyfit(t_centered, lc.mags, degree, w=np.sqrt(weights))

        model_mags = np.polyval(coeffs, t_centered)
        residuals = lc.mags - model_mags

        chi2 = np.sum((residuals / lc.mag_errs)**2)
        dof = len(lc.times) - degree - 1

        params = {f'c{i}': c for i, c in enumerate(coeffs)}
        params['t_ref'] = t_ref

        return TransientFitResult(
            model_name='polynomial',
            parameters=params,
            uncertainties={},  # Would need proper error estimation
            chi_squared=chi2,
            dof=dof,
            model_flux=10**((23.9 - model_mags) / 2.5) * 1e-3,
            residuals=residuals
        )

    def fit_sn_ia(self, lc: LightCurve,
                  stretch_bounds: Tuple[float, float] = (0.7, 1.3),
                  color_bounds: Tuple[float, float] = (-0.3, 0.3)) -> TransientFitResult:
        """
        Fit Type Ia supernova template to light curve.

        Args:
            lc: Light curve data
            stretch_bounds: Bounds on stretch parameter
            color_bounds: Bounds on color parameter

        Returns:
            Fit result
        """
        from scipy.optimize import minimize


# Custom optimization variant 26
