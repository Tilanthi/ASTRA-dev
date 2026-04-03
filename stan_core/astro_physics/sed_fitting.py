#!/usr/bin/env python3
"""
SED Fitting Engine for ASTRO-SWARM
===================================

Multi-wavelength Spectral Energy Distribution fitting for galaxies,
stars, dust, and AGN components.

Capabilities:
1. Multi-component SED assembly (optical → radio)
2. Modified blackbody dust fitting with variable β
3. Stellar population synthesis models
4. AGN decomposition templates
5. Bayesian SED fitting with full posterior
6. Photometric redshift estimation

Key References:
- da Cunha et al. 2008 (MAGPHYS)
- Boquien et al. 2019 (CIGALE)
- Conroy 2013 (stellar population synthesis)
- Dale & Helou 2002 (IR templates)
- Draine & Li 2007 (dust models)

Author: Claude Code (ASTRO-SWARM)
Date: 2024-11
"""

import numpy as np
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple, Any, Callable, Union
from enum import Enum
from abc import ABC, abstractmethod
from scipy.optimize import minimize, differential_evolution
from scipy.interpolate import interp1d, RegularGridInterpolator
from scipy.integrate import quad, trapezoid
import warnings

# Physical Constants (CGS)
c_light = 2.998e10      # cm/s
h_planck = 6.626e-27    # erg s
k_B = 1.38e-16          # erg/K
L_sun = 3.828e33        # erg/s
pc_to_cm = 3.086e18
Jy_to_cgs = 1e-23


# =============================================================================
# FILTER SYSTEM
# =============================================================================

@dataclass
class PhotometricFilter:
    """Photometric filter transmission curve"""
    name: str
    wavelength: np.ndarray      # Angstrom
    transmission: np.ndarray
    effective_wavelength: float = 0.0
    zero_point_Jy: float = 3631.0  # AB system

    def __post_init__(self):
        if self.effective_wavelength == 0.0:
            # Calculate effective wavelength
            num = trapezoid(self.wavelength * self.transmission, self.wavelength)
            den = trapezoid(self.transmission, self.wavelength)
            self.effective_wavelength = num / den

    def convolve(self, wavelength: np.ndarray, flux: np.ndarray) -> float:
        """
        Convolve spectrum with filter.

        Parameters
        ----------
        wavelength : np.ndarray
            Spectrum wavelength (Angstrom)
        flux : np.ndarray
            Spectrum flux density (erg/s/cm²/Hz or Jy)

        Returns
        -------
        float : Filter-averaged flux
        """
        # Interpolate transmission to spectrum wavelength grid
        trans_interp = interp1d(self.wavelength, self.transmission,
                               bounds_error=False, fill_value=0.0)
        trans = trans_interp(wavelength)

        # Convolve
        num = trapezoid(flux * trans, wavelength)
        den = trapezoid(trans, wavelength)

        return num / den if den > 0 else 0.0


class FilterLibrary:
    """
    Standard photometric filter library.
    """

    # Common filter effective wavelengths (Angstrom) and zero points
    STANDARD_FILTERS = {
        # Optical
        'SDSS_u': {'lambda_eff': 3551, 'fwhm': 599},
        'SDSS_g': {'lambda_eff': 4686, 'fwhm': 1379},
        'SDSS_r': {'lambda_eff': 6166, 'fwhm': 1382},
        'SDSS_i': {'lambda_eff': 7480, 'fwhm': 1535},
        'SDSS_z': {'lambda_eff': 8932, 'fwhm': 1370},

        # NIR
        '2MASS_J': {'lambda_eff': 12350, 'fwhm': 1620},
        '2MASS_H': {'lambda_eff': 16620, 'fwhm': 2510},
        '2MASS_Ks': {'lambda_eff': 21590, 'fwhm': 2620},

        # Mid-IR (Spitzer/WISE)
        'WISE_W1': {'lambda_eff': 33526, 'fwhm': 6626},
        'WISE_W2': {'lambda_eff': 46028, 'fwhm': 10423},
        'WISE_W3': {'lambda_eff': 115608, 'fwhm': 55055},
        'WISE_W4': {'lambda_eff': 220883, 'fwhm': 41013},

        # Far-IR (Herschel)
        'PACS_70': {'lambda_eff': 700000, 'fwhm': 250000},
        'PACS_100': {'lambda_eff': 1000000, 'fwhm': 350000},
        'PACS_160': {'lambda_eff': 1600000, 'fwhm': 850000},
        'SPIRE_250': {'lambda_eff': 2500000, 'fwhm': 700000},
        'SPIRE_350': {'lambda_eff': 3500000, 'fwhm': 1000000},
        'SPIRE_500': {'lambda_eff': 5000000, 'fwhm': 1500000},

        # Submm
        'SCUBA2_450': {'lambda_eff': 4500000, 'fwhm': 300000},
        'SCUBA2_850': {'lambda_eff': 8500000, 'fwhm': 500000},
        'ALMA_Band6': {'lambda_eff': 13000000, 'fwhm': 3000000},
        'ALMA_Band7': {'lambda_eff': 8700000, 'fwhm': 2000000},
    }

    @classmethod
    def get_filter(cls, name: str) -> PhotometricFilter:
        """Get a standard filter (approximate Gaussian transmission)"""
        if name not in cls.STANDARD_FILTERS:
            raise ValueError(f"Unknown filter: {name}")

        params = cls.STANDARD_FILTERS[name]
        lambda_eff = params['lambda_eff']
        fwhm = params['fwhm']

        # Create Gaussian transmission curve
        sigma = fwhm / 2.355
        wavelength = np.linspace(lambda_eff - 3*fwhm, lambda_eff + 3*fwhm, 100)
        transmission = np.exp(-0.5 * ((wavelength - lambda_eff) / sigma)**2)

        return PhotometricFilter(
            name=name,
            wavelength=wavelength,
            transmission=transmission,
            effective_wavelength=lambda_eff
        )

    @classmethod
    def available_filters(cls) -> List[str]:
        """List available filters"""
        return list(cls.STANDARD_FILTERS.keys())


# =============================================================================
# SED COMPONENTS
# =============================================================================

class SEDComponent(ABC):
    """Abstract base class for SED components"""

    @abstractmethod
    def evaluate(self, wavelength: np.ndarray, params: Dict[str, float]) -> np.ndarray:
        """
        Evaluate component flux at given wavelengths.

        Parameters
        ----------
        wavelength : np.ndarray
            Wavelength in Angstrom
        params : dict
            Component parameters

        Returns
        -------
        np.ndarray : Flux density (erg/s/cm²/Hz)
        """
        pass

    @abstractmethod
    def parameter_names(self) -> List[str]:
        """Return list of parameter names"""
        pass


class ModifiedBlackbody(SEDComponent):
    """
    Modified blackbody dust emission.

    S_ν ∝ ν^β * B_ν(T_dust) * (1 - exp(-τ))

    Parameters:
    - T_dust: Dust temperature (K)
    - beta: Dust emissivity index
    - M_dust: Dust mass (solar masses)
    - kappa_0: Opacity at reference wavelength (cm²/g)
    - lambda_0: Reference wavelength (micron)
    """

    def __init__(self, distance_Mpc: float = 10.0):
        self.distance_Mpc = distance_Mpc
        self.distance_cm = distance_Mpc * 3.086e24

    def evaluate(self, wavelength: np.ndarray, params: Dict[str, float]) -> np.ndarray:
        """Evaluate modified blackbody"""
        T_dust = params.get('T_dust', 30.0)
        beta = params.get('beta', 2.0)
        M_dust = params.get('M_dust', 1e7)  # Solar masses
        kappa_0 = params.get('kappa_0', 0.77)  # cm²/g at 850 μm
        lambda_0 = params.get('lambda_0', 850.0)  # Reference wavelength μm

        # Convert wavelength to frequency
        wavelength_cm = wavelength * 1e-8  # Angstrom to cm
        nu = c_light / wavelength_cm  # Hz

        # Reference frequency
        nu_0 = c_light / (lambda_0 * 1e-4)  # Hz

        # Planck function
        x = h_planck * nu / (k_B * T_dust)
        with np.errstate(over='ignore'):
            B_nu = np.where(x < 700,
                          2 * h_planck * nu**3 / c_light**2 / (np.exp(x) - 1),
                          0.0)

        # Dust opacity
        kappa = kappa_0 * (nu / nu_0)**beta

        # Dust mass in grams
        M_dust_g = M_dust * 1.989e33

        # Optical depth (for optically thin case)
        # τ = κ * M / (4π * D²) for uniform sphere
        # Simpler: optically thin approximation
        tau = kappa * M_dust_g / (4 * np.pi * self.distance_cm**2)

        # Flux density
        # For optically thin: S_ν = κ * M * B_ν / D²
        flux = kappa * M_dust_g * B_nu / self.distance_cm**2

        return flux

    def parameter_names(self) -> List[str]:
        return ['T_dust', 'beta', 'M_dust', 'kappa_0', 'lambda_0']


class TwoTemperatureDust(SEDComponent):
    """
    Two-temperature dust model (warm + cold components).

    Common for galaxies with both star-forming regions (warm)
    and diffuse ISM (cold).
    """

    def __init__(self, distance_Mpc: float = 10.0):
        self.warm = ModifiedBlackbody(distance_Mpc)
        self.cold = ModifiedBlackbody(distance_Mpc)

    def evaluate(self, wavelength: np.ndarray, params: Dict[str, float]) -> np.ndarray:
        """Evaluate two-temperature dust"""
        warm_params = {
            'T_dust': params.get('T_warm', 50.0),
            'beta': params.get('beta_warm', 1.5),
            'M_dust': params.get('M_warm', 1e5),
            'kappa_0': params.get('kappa_0', 0.77),
            'lambda_0': params.get('lambda_0', 850.0)
        }

        cold_params = {
            'T_dust': params.get('T_cold', 20.0),
            'beta': params.get('beta_cold', 2.0),
            'M_dust': params.get('M_cold', 1e7),
            'kappa_0': params.get('kappa_0', 0.77),
            'lambda_0': params.get('lambda_0', 850.0)
        }

        flux_warm = self.warm.evaluate(wavelength, warm_params)
        flux_cold = self.cold.evaluate(wavelength, cold_params)

        return flux_warm + flux_cold

    def parameter_names(self) -> List[str]:
        return ['T_warm', 'T_cold', 'beta_warm', 'beta_cold',
                'M_warm', 'M_cold', 'kappa_0', 'lambda_0']


class PowerLaw(SEDComponent):
    """
    Power-law SED component.

    S_ν ∝ ν^α

    Useful for synchrotron, free-free, or AGN continuum.
    """

    def evaluate(self, wavelength: np.ndarray, params: Dict[str, float]) -> np.ndarray:
        """Evaluate power law"""
        alpha = params.get('alpha', -0.7)  # Spectral index
        norm = params.get('norm', 1e-26)  # Normalization (erg/s/cm²/Hz at ref freq)
        nu_ref = params.get('nu_ref', 1.4e9)  # Reference frequency (Hz)

        wavelength_cm = wavelength * 1e-8
        nu = c_light / wavelength_cm

        flux = norm * (nu / nu_ref)**alpha

        return flux

    def parameter_names(self) -> List[str]:
        return ['alpha', 'norm', 'nu_ref']


class StellarPopulation(SEDComponent):
    """
    Simplified stellar population SED.

    Uses a combination of blackbodies to approximate
    stellar population SEDs of different ages.
    """

    # Characteristic temperatures for different stellar populations
    POPULATION_TEMPS = {
        'young': [30000, 15000, 8000],  # O, B, A stars
        'intermediate': [6000, 5000],    # F, G stars
        'old': [4000, 3500]              # K, M stars
    }

    def __init__(self, distance_Mpc: float = 10.0):
        self.distance_Mpc = distance_Mpc
        self.distance_cm = distance_Mpc * 3.086e24

    def evaluate(self, wavelength: np.ndarray, params: Dict[str, float]) -> np.ndarray:
        """Evaluate stellar population SED"""
        M_star = params.get('M_star', 1e10)  # Solar masses
        age_Gyr = params.get('age', 1.0)     # Age in Gyr
        metallicity = params.get('Z', 0.02)  # Solar = 0.02
        A_V = params.get('A_V', 0.0)         # Visual extinction

        wavelength_cm = wavelength * 1e-8
        nu = c_light / wavelength_cm

        # Simple age-dependent mix of stellar temperatures
        if age_Gyr < 0.1:
            temps = self.POPULATION_TEMPS['young']
            weights = [0.5, 0.3, 0.2]
        elif age_Gyr < 1.0:
            temps = self.POPULATION_TEMPS['young'] + self.POPULATION_TEMPS['intermediate']
            weights = [0.2, 0.2, 0.2, 0.2, 0.2]
        else:
            temps = self.POPULATION_TEMPS['intermediate'] + self.POPULATION_TEMPS['old']
            weights = [0.2, 0.3, 0.3, 0.2]

        # Sum blackbodies
        flux = np.zeros_like(wavelength, dtype=float)
        for T, w in zip(temps, weights):
            x = h_planck * nu / (k_B * T)
            with np.errstate(over='ignore'):
                B_nu = np.where(x < 700,
                              2 * h_planck * nu**3 / c_light**2 / (np.exp(x) - 1),
                              0.0)
            flux += w * B_nu

        # Scale by stellar mass (very rough approximation)
        # Assume M/L ~ 1 in V-band
        L_star = M_star * L_sun  # erg/s
        flux *= L_star / (4 * np.pi * self.distance_cm**2)

        # Apply dust extinction (Calzetti law approximation)
        if A_V > 0:
            lambda_um = wavelength * 1e-4  # Angstrom to micron
            k_lambda = 2.659 * (-2.156 + 1.509/lambda_um - 0.198/lambda_um**2 +
                               0.011/lambda_um**3) + 4.05
            k_lambda = np.clip(k_lambda, 0, 10)
            A_lambda = A_V * k_lambda / 4.05
            flux *= 10**(-0.4 * A_lambda)

        return flux

    def parameter_names(self) -> List[str]:
        return ['M_star', 'age', 'Z', 'A_V']


class AGNTemplate(SEDComponent):
    """
    AGN SED template.

    Combines:
    - UV/optical accretion disk (multi-temperature blackbody)
    - IR torus emission (modified blackbody)
    - X-ray power law (optional)
    """

    def __init__(self, distance_Mpc: float = 10.0):
        self.distance_Mpc = distance_Mpc
        self.distance_cm = distance_Mpc * 3.086e24

    def evaluate(self, wavelength: np.ndarray, params: Dict[str, float]) -> np.ndarray:
        """Evaluate AGN template"""
        L_bol = params.get('L_bol', 1e45)  # Bolometric luminosity (erg/s)
        f_torus = params.get('f_torus', 0.3)  # Fraction reprocessed by torus
        T_torus = params.get('T_torus', 300)  # Torus temperature (K)
        alpha_UV = params.get('alpha_UV', -0.5)  # UV spectral index

        wavelength_cm = wavelength * 1e-8
        nu = c_light / wavelength_cm

        flux = np.zeros_like(wavelength, dtype=float)

        # UV/Optical: Power law + big blue bump
        # Simplified: power law with exponential cutoff
        nu_ref = c_light / (3000 * 1e-8)  # 3000 Angstrom
        uv_optical = (nu / nu_ref)**alpha_UV
        uv_optical *= np.exp(-h_planck * nu / (k_B * 3e5))  # High-freq cutoff
        uv_optical *= np.exp(-(nu_ref / nu)**2)  # Low-freq cutoff

        # Normalize to (1-f_torus) * L_bol
        norm_uv = (1 - f_torus) * L_bol / (4 * np.pi * self.distance_cm**2)
        # Rough normalization
        flux += norm_uv * uv_optical / np.max(uv_optical)

        # Torus: Modified blackbody
        x = h_planck * nu / (k_B * T_torus)
        with np.errstate(over='ignore'):
            B_nu = np.where(x < 700,
                          2 * h_planck * nu**3 / c_light**2 / (np.exp(x) - 1),
                          0.0)

        norm_torus = f_torus * L_bol / (4 * np.pi * self.distance_cm**2)
        flux += norm_torus * B_nu / np.max(B_nu + 1e-30)

        return flux

    def parameter_names(self) -> List[str]:
        return ['L_bol', 'f_torus', 'T_torus', 'alpha_UV']


# =============================================================================
# COMPOSITE SED MODEL
# =============================================================================

class CompositeSED:
    """
    Composite SED model combining multiple components.
    """

    def __init__(self, distance_Mpc: float = 10.0):
        self.distance_Mpc = distance_Mpc
        self.components: Dict[str, SEDComponent] = {}

    def add_component(self, name: str, component: SEDComponent):
        """Add a component to the model"""
        self.components[name] = component

    def add_dust(self, two_temp: bool = False):
        """Add dust component"""
        if two_temp:
            self.components['dust'] = TwoTemperatureDust(self.distance_Mpc)
        else:
            self.components['dust'] = ModifiedBlackbody(self.distance_Mpc)

    def add_stars(self):
        """Add stellar component"""
        self.components['stars'] = StellarPopulation(self.distance_Mpc)

    def add_agn(self):
        """Add AGN component"""
        self.components['agn'] = AGNTemplate(self.distance_Mpc)

    def add_synchrotron(self):
        """Add synchrotron component"""
        self.components['synchrotron'] = PowerLaw()

    def evaluate(self, wavelength: np.ndarray,
                params: Dict[str, float]) -> Dict[str, np.ndarray]:
        """
        Evaluate all components.

        Parameters
        ----------
        wavelength : np.ndarray
            Wavelength in Angstrom
        params : dict
            All component parameters

        Returns
        -------
        dict : Flux from each component and total
        """
        result = {}
        total = np.zeros_like(wavelength, dtype=float)

        for name, component in self.components.items():
            flux = component.evaluate(wavelength, params)
            result[name] = flux
            total += flux

        result['total'] = total
        return result

    def get_photometry(self, wavelength: np.ndarray, params: Dict[str, float],
                      filters: List[PhotometricFilter]) -> Dict[str, float]:
        """
        Get synthetic photometry in given filters.

        Parameters
        ----------
        wavelength : np.ndarray
            Model wavelength grid
        params : dict
            Model parameters
        filters : list
            List of PhotometricFilter objects

        Returns
        -------
        dict : Flux in each filter (Jy)
        """
        sed = self.evaluate(wavelength, params)
        total_flux = sed['total']

        # Convert to Jy
        flux_Jy = total_flux / Jy_to_cgs

        photometry = {}
        for filt in filters:
            photometry[filt.name] = filt.convolve(wavelength, flux_Jy)

        return photometry

    def parameter_names(self) -> List[str]:
        """Get all parameter names"""
        names = []
        for component in self.components.values():
            names.extend(component.parameter_names())
        return list(set(names))


# =============================================================================
# SED FITTING
# =============================================================================

@dataclass
class SEDFitResult:
    """Results from SED fitting"""
    best_params: Dict[str, float]
    param_errors: Dict[str, float]
    chi_squared: float
    reduced_chi_squared: float
    n_data: int
    n_params: int
    model_photometry: Dict[str, float]
    residuals: Dict[str, float]
    components: Dict[str, np.ndarray]
    success: bool
    method: str


class SEDFitter:
    """
    Bayesian SED fitting engine.
    """

    def __init__(self, sed_model: CompositeSED,
                filters: List[PhotometricFilter]):
        """
        Parameters
        ----------
        sed_model : CompositeSED
            SED model to fit
        filters : list
            Photometric filters
        """
        self.model = sed_model
        self.filters = filters

        # Fine wavelength grid for model evaluation
        lambda_min = min(f.effective_wavelength for f in filters) * 0.5
        lambda_max = max(f.effective_wavelength for f in filters) * 2.0
        self.wavelength = np.logspace(np.log10(lambda_min),
                                      np.log10(lambda_max), 1000)

    def fit(self, observed_flux: Dict[str, float],
           observed_errors: Dict[str, float],
           param_bounds: Dict[str, Tuple[float, float]],
           fixed_params: Optional[Dict[str, float]] = None,
           method: str = 'differential_evolution') -> SEDFitResult:
        """
        Fit SED to observed photometry.

        Parameters
        ----------
        observed_flux : dict
            Observed flux in each filter (Jy)
        observed_errors : dict
            Flux uncertainties (Jy)
        param_bounds : dict
            Parameter bounds {name: (min, max)}
        fixed_params : dict, optional
            Fixed parameter values
        method : str
            Optimization method

        Returns
        -------
        SEDFitResult
        """
        if fixed_params is None:
            fixed_params = {}

        # Get free parameter names
        free_params = [p for p in param_bounds.keys() if p not in fixed_params]
        bounds = [param_bounds[p] for p in free_params]

        # Build arrays for fitting
        filter_names = list(observed_flux.keys())
        flux_obs = np.array([observed_flux[f] for f in filter_names])
        flux_err = np.array([observed_errors[f] for f in filter_names])

        # Get filters in correct order
        filter_dict = {f.name: f for f in self.filters}
        filter_list = [filter_dict[name] for name in filter_names if name in filter_dict]

        def chi_squared(theta):
