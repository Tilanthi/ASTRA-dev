"""
Atmospheric Retrieval Module

Exoplanet atmosphere modeling including transmission and emission spectra,
cloud models, and chemical equilibrium.

Date: 2025-12-15
"""

import numpy as np
from typing import List, Dict, Optional, Any, Tuple, Union
from dataclasses import dataclass, field
from enum import Enum
from abc import ABC, abstractmethod
import warnings

# Physical constants (CGS)
K_BOLTZMANN = 1.381e-16  # erg/K
H_PLANCK = 6.626e-27  # erg s
C_LIGHT = 2.998e10  # cm/s
M_PROTON = 1.673e-24  # g
G_GRAV = 6.674e-8  # cm^3/g/s^2
SIGMA_SB = 5.67e-5  # erg/cm^2/s/K^4
R_GAS = 8.314e7  # erg/mol/K
AU = 1.496e13  # cm
R_JUPITER = 6.991e9  # cm
M_JUPITER = 1.898e30  # g
R_EARTH = 6.371e8  # cm
M_EARTH = 5.972e27  # g
R_SUN = 6.96e10  # cm


class MoleculeType(Enum):
    """Atmospheric molecular species"""
    H2O = "H2O"
    CO = "CO"
    CO2 = "CO2"
    CH4 = "CH4"
    NH3 = "NH3"
    HCN = "HCN"
    H2S = "H2S"
    Na = "Na"
    K = "K"
    TiO = "TiO"
    VO = "VO"
    FeH = "FeH"


@dataclass
class AtmosphereParameters:
    """Parameters defining an exoplanet atmosphere"""
    R_planet: float = 1.0  # Jupiter radii
    M_planet: float = 1.0  # Jupiter masses
    T_eq: float = 1000.0  # Equilibrium temperature (K)
    metallicity: float = 1.0  # Solar units
    C_O_ratio: float = 0.55  # Solar C/O
    log_Kzz: float = 8.0  # Eddy diffusion coefficient
    P_cloud: float = 1e-3  # Cloud-top pressure (bar)
    cloud_opacity: float = 0.0  # Gray cloud opacity


@dataclass
class PTProfile:
    """Pressure-temperature profile"""
    P: np.ndarray  # Pressure (bar)
    T: np.ndarray  # Temperature (K)
    z: np.ndarray = None  # Altitude (cm)


@dataclass
class SpectrumResult:
    """Container for spectrum calculation results"""
    wavelength: np.ndarray  # microns
    spectrum: np.ndarray  # Transit depth (Rp/R*)^2 or Fp/F*
    contributions: Dict[str, np.ndarray] = field(default_factory=dict)
    P_tau_unity: np.ndarray = None  # Pressure of tau=1 surface


# =============================================================================
# PRESSURE-TEMPERATURE PROFILES
# =============================================================================

class PTProfileModel(ABC):
    """Base class for P-T profile models"""

    @abstractmethod
    def calculate(self, params: AtmosphereParameters) -> PTProfile:
        pass


class GuillotPTProfile(PTProfileModel):
    """
    Guillot (2010) analytic P-T profile for irradiated planets.

    Two-stream approximation with internal heat and stellar irradiation.
    """

    def __init__(self, n_layers: int = 100):
        """
        Initialize P-T profile model.

        Args:
            n_layers: Number of atmospheric layers
        """
        self.n_layers = n_layers

    def calculate(self, params: AtmosphereParameters,
                  T_int: float = 100.0,
                  kappa_IR: float = 0.01,
                  gamma: float = 0.4,
                  P_min: float = 1e-6,
                  P_max: float = 100.0) -> PTProfile:
        """
        Calculate P-T profile.

        Args:
            params: Atmosphere parameters
            T_int: Internal temperature (K)
            kappa_IR: IR opacity (cm^2/g)
            gamma: Visible/IR opacity ratio
            P_min, P_max: Pressure range (bar)

        Returns:
            PTProfile object
        """
        P = np.logspace(np.log10(P_min), np.log10(P_max), self.n_layers)

        # Optical depth at each pressure
        g = G_GRAV * params.M_planet * M_JUPITER / (params.R_planet * R_JUPITER)**2
        tau = kappa_IR * P * 1e6 / g  # Convert bar to dyn/cm^2

        # Guillot profile
        T_irr = params.T_eq

        # Temperature at each layer
        T4_int = T_int**4 * (0.5 + 0.75 * tau)
        T4_irr = 0.75 * T_irr**4 * (
            2/3 + 2/(3*gamma) * (1 + (gamma*tau/2 - 1) * np.exp(-gamma*tau)) +
            2*gamma/3 * (1 - tau**2/2) * self._E2(gamma*tau)
        )

        T = (T4_int + T4_irr)**0.25

        # Calculate altitude (hydrostatic)
        mu = 2.3  # Mean molecular weight
        H = K_BOLTZMANN * T / (mu * M_PROTON * g)
        z = np.zeros_like(P)
        for i in range(1, len(P)):
            z[i] = z[i-1] - np.log(P[i]/P[i-1]) * H[i]

        return PTProfile(P=P, T=T, z=z)

    def _E2(self, x: np.ndarray) -> np.ndarray:
        """Second exponential integral approximation"""
        # Approximate E_2(x) for numerical stability
        return np.exp(-x) * np.where(
            x < 1,
            1 - 0.5 * x,
            1 / (x + 1)
        )


class IsothermalProfile(PTProfileModel):
    """Simple isothermal atmosphere"""

    def calculate(self, params: AtmosphereParameters,
                  P_min: float = 1e-6,
                  P_max: float = 100.0,
                  n_layers: int = 100) -> PTProfile:
        """Calculate isothermal P-T profile"""
        P = np.logspace(np.log10(P_min), np.log10(P_max), n_layers)
        T = np.ones_like(P) * params.T_eq

        # Hydrostatic altitude
        g = G_GRAV * params.M_planet * M_JUPITER / (params.R_planet * R_JUPITER)**2
        mu = 2.3
        H = K_BOLTZMANN * params.T_eq / (mu * M_PROTON * g)
        z = -H * np.log(P / P_max)

        return PTProfile(P=P, T=T, z=z)


# =============================================================================
# OPACITY SOURCES
# =============================================================================

class OpacityDatabase:
    """
    Molecular opacity cross-sections.

    Simplified implementation - full version would use line lists
    from HITRAN, ExoMol, or pre-computed k-tables.
    """

    # Approximate band centers (microns) and strengths
    OPACITY_BANDS = {
        MoleculeType.H2O: [
            (1.4, 1e-20), (1.9, 2e-20), (2.7, 5e-20), (6.3, 3e-19)
        ],
        MoleculeType.CO: [
            (2.3, 1e-20), (4.7, 5e-20)
        ],
        MoleculeType.CO2: [
            (2.0, 5e-21), (2.7, 2e-20), (4.3, 1e-19), (15.0, 5e-19)
        ],
        MoleculeType.CH4: [
            (1.7, 2e-20), (2.3, 3e-20), (3.3, 1e-19), (7.7, 2e-19)
        ],
        MoleculeType.NH3: [
            (1.5, 1e-20), (2.0, 2e-20), (10.5, 5e-19)
        ],
    }

    def __init__(self):
        """Initialize opacity database"""
        pass

    def cross_section(self, molecule: MoleculeType, wavelength: np.ndarray,
                      T: float, P: float) -> np.ndarray:
        """
        Get absorption cross-section.

        Args:
            molecule: Molecular species
            wavelength: Wavelength array (microns)
            T: Temperature (K)
            P: Pressure (bar)

        Returns:
            Cross-section array (cm^2/molecule)
        """
        sigma = np.zeros_like(wavelength)

        if molecule not in self.OPACITY_BANDS:
            return sigma

        for center, strength in self.OPACITY_BANDS[molecule]:
            # Gaussian band profile (simplified)
            width = 0.1 * center * (T / 300)**0.5  # Temperature-dependent width
            sigma += strength * np.exp(-0.5 * ((wavelength - center) / width)**2)

        # Pressure broadening
        sigma *= (1 + 0.1 * P)

        return sigma

    def rayleigh_scattering(self, wavelength: np.ndarray) -> np.ndarray:
        """
        Calculate H2 Rayleigh scattering cross-section.

        Args:
            wavelength: Wavelength (microns)

        Returns:
            Cross-section (cm^2/molecule)
        """
        # Rayleigh: sigma ~ lambda^-4
        # Normalization for H2 at 0.55 microns: ~3e-27 cm^2
        sigma_0 = 3e-27
        lambda_0 = 0.55

        return sigma_0 * (lambda_0 / wavelength)**4

    def collision_induced_absorption(self, wavelength: np.ndarray,
                                     T: float) -> np.ndarray:
        """
        H2-H2 and H2-He collision-induced absorption.

        Args:
            wavelength: Wavelength (microns)
            T: Temperature (K)

        Returns:
            CIA coefficient (cm^5/molecule^2)
        """
        # Simplified CIA - main bands around 2 microns
        cia = np.zeros_like(wavelength)

        # H2-H2 band
        center = 2.4
        width = 0.8
        peak = 1e-46 * (T / 300)**0.5

        cia += peak * np.exp(-0.5 * ((wavelength - center) / width)**2)

        return cia


# =============================================================================
# TRANSMISSION SPECTRUM
# =============================================================================

class TransmissionSpectrum:
    """
    Calculate transmission spectrum for transiting exoplanets.
    """

    def __init__(self, params: AtmosphereParameters = None):
        """
        Initialize transmission spectrum calculator.

        Args:
            params: Atmosphere parameters
        """
        self.params = params or AtmosphereParameters()
        self.opacity_db = OpacityDatabase()
        self.pt_model = GuillotPTProfile()

    def scale_height(self, T: float, mu: float = 2.3) -> float:
        """
        Calculate atmospheric scale height.

        Args:
            T: Temperature (K)
            mu: Mean molecular weight

        Returns:
            Scale height (cm)
        """
        g = G_GRAV * self.params.M_planet * M_JUPITER / \
            (self.params.R_planet * R_JUPITER)**2
        return K_BOLTZMANN * T / (mu * M_PROTON * g)

    def calculate(self, wavelength: np.ndarray,
                  abundances: Dict[MoleculeType, float] = None,
                  R_star: float = 1.0) -> SpectrumResult:
        """
        Calculate transmission spectrum.

        Args:
            wavelength: Wavelength array (microns)
            abundances: Molecular abundances (volume mixing ratios)
            R_star: Stellar radius (solar radii)

        Returns:
            SpectrumResult with transit depth
        """
        # Default solar-like abundances
        if abundances is None:
            abundances = {
                MoleculeType.H2O: 1e-3 * self.params.metallicity,
                MoleculeType.CO: 5e-4 * self.params.metallicity,
                MoleculeType.CH4: 1e-6 * self.params.metallicity,
            }

        # Get P-T profile
        pt = self.pt_model.calculate(self.params)

        # Planet and stellar radii
        R_p = self.params.R_planet * R_JUPITER
        R_s = R_star * R_SUN

        # Calculate effective altitude at each wavelength
        n_wave = len(wavelength)
        n_layers = len(pt.P)

        # Transit depth
        depth = np.zeros(n_wave)
        contributions = {mol.value: np.zeros(n_wave) for mol in abundances.keys()}

        for i, wl in enumerate(wavelength):
            # Optical depth at each layer
            tau = np.zeros(n_layers)

            for j in range(n_layers):
                T = pt.T[j]
                P = pt.P[j]

                # Number density
                n_tot = P * 1e6 / (K_BOLTZMANN * T)  # cm^-3

                # Sum opacities from all molecules
                kappa = 0.0
                for mol, vmr in abundances.items():
                    sigma = self.opacity_db.cross_section(mol, np.array([wl]), T, P)[0]
                    kappa += vmr * n_tot * sigma

                # H2 Rayleigh scattering
                sigma_ray = self.opacity_db.rayleigh_scattering(np.array([wl]))[0]
                kappa += 0.85 * n_tot * sigma_ray  # H2 volume fraction

                # Cloud opacity
                if P > self.params.P_cloud:
                    kappa += self.params.cloud_opacity * n_tot * 1e-24

                # Layer thickness
                if j > 0:
                    dz = np.abs(pt.z[j] - pt.z[j-1])
                else:
                    H = self.scale_height(T)
                    dz = H * np.log(pt.P[1] / pt.P[0])

                tau[j] = kappa * dz

            # Cumulative optical depth
            tau_cum = np.cumsum(tau[::-1])[::-1]

            # Effective radius (where tau ~ 0.56)
            H = self.scale_height(np.mean(pt.T))
            z_eff = np.interp(0.56, tau_cum[::-1], pt.z[::-1])
            R_eff = R_p + z_eff

            # Transit depth
            depth[i] = (R_eff / R_s)**2

        # Contributions per molecule (simplified)
        for mol in abundances.keys():
            contributions[mol.value] = depth * abundances[mol] / \
                                       sum(abundances.values())

        return SpectrumResult(
            wavelength=wavelength,
            spectrum=depth,
            contributions=contributions
        )


# =============================================================================
# EMISSION SPECTRUM
# =============================================================================

class EmissionSpectrum:
    """
    Calculate thermal emission spectrum for exoplanets.
    """

    def __init__(self, params: AtmosphereParameters = None):
        """
        Initialize emission spectrum calculator.

        Args:
            params: Atmosphere parameters
        """
        self.params = params or AtmosphereParameters()
        self.opacity_db = OpacityDatabase()
        self.pt_model = GuillotPTProfile()

    def blackbody(self, wavelength: np.ndarray, T: float) -> np.ndarray:
        """
        Calculate Planck function.

        Args:
            wavelength: Wavelength (microns)
            T: Temperature (K)

        Returns:
            Spectral radiance (erg/s/cm^2/sr/micron)
        """
        wl_cm = wavelength * 1e-4

        B = (2 * H_PLANCK * C_LIGHT**2 / wl_cm**5) / \
            (np.exp(H_PLANCK * C_LIGHT / (wl_cm * K_BOLTZMANN * T)) - 1)

        return B * 1e-4  # Convert to per micron

    def calculate(self, wavelength: np.ndarray,
                  abundances: Dict[MoleculeType, float] = None,
                  R_star: float = 1.0,
                  a: float = 0.05) -> SpectrumResult:
        """
        Calculate emission spectrum (planet/star flux ratio).

        Args:
            wavelength: Wavelength array (microns)
            abundances: Molecular abundances
            R_star: Stellar radius (solar radii)
            a: Semi-major axis (AU)

        Returns:
            SpectrumResult with Fp/Fs
        """
        if abundances is None:
            abundances = {
                MoleculeType.H2O: 1e-3 * self.params.metallicity,
                MoleculeType.CO: 5e-4 * self.params.metallicity,
            }

        # Get P-T profile
        pt = self.pt_model.calculate(self.params)

        R_p = self.params.R_planet * R_JUPITER
        R_s = R_star * R_SUN

        n_wave = len(wavelength)
        n_layers = len(pt.P)

        # Planet flux
        F_planet = np.zeros(n_wave)

        # Stellar flux (blackbody approximation)
        T_star = 5780 * (R_star)**(-0.5) * (a / 1)**(-0.5)  # Rough scaling
        B_star = self.blackbody(wavelength, T_star)
        F_star = np.pi * B_star * (R_s / (a * AU))**2

        for i, wl in enumerate(wavelength):
            # Contribution function
            contribution = np.zeros(n_layers)

            tau_above = 0.0
            for j in range(n_layers - 1, -1, -1):
                T = pt.T[j]
                P = pt.P[j]

                # Optical depth in layer
                n_tot = P * 1e6 / (K_BOLTZMANN * T)
                kappa = 0.0

                for mol, vmr in abundances.items():
                    sigma = self.opacity_db.cross_section(mol, np.array([wl]), T, P)[0]
                    kappa += vmr * n_tot * sigma

                # CIA
                cia = self.opacity_db.collision_induced_absorption(np.array([wl]), T)[0]
                kappa += 0.85**2 * n_tot**2 * cia

                H = K_BOLTZMANN * T / (2.3 * M_PROTON * G_GRAV *
                    self.params.M_planet * M_JUPITER / (R_p)**2)
                dz = H * 0.1  # Approximate layer thickness

                dtau = kappa * dz

                # Contribution to outgoing flux
                B = self.blackbody(np.array([wl]), T)[0]
                contribution[j] = B * np.exp(-tau_above) * (1 - np.exp(-dtau))

                tau_above += dtau

            F_planet[i] = np.pi * np.sum(contribution)

        # Flux ratio
        flux_ratio = F_planet / F_star * (R_p / R_s)**2

        return SpectrumResult(
            wavelength=wavelength,
            spectrum=flux_ratio,
            contributions={}
        )


# =============================================================================
# CLOUD MODEL
# =============================================================================

class CloudModel:
    """
    Cloud and haze models for exoplanet atmospheres.
    """

    def __init__(self, cloud_type: str = 'gray'):
        """
        Initialize cloud model.

        Args:
            cloud_type: 'gray', 'mie', or 'power_law'
        """
        self.cloud_type = cloud_type

    def gray_cloud_opacity(self, P: np.ndarray, P_cloud: float,
                           kappa_cloud: float = 1e-3) -> np.ndarray:
        """
        Gray cloud opacity (wavelength-independent).

        Args:
            P: Pressure array (bar)
            P_cloud: Cloud-top pressure (bar)
            kappa_cloud: Cloud opacity (cm^2/g)

        Returns:
            Opacity array
        """
        opacity = np.zeros_like(P)
        opacity[P > P_cloud] = kappa_cloud
        return opacity

    def power_law_haze(self, wavelength: np.ndarray,
                       a: float = 1.0, gamma: float = -4.0) -> np.ndarray:
        """
        Power-law haze opacity.

        opacity ~ a * (lambda / lambda_0)^gamma

        Args:
            wavelength: Wavelength (microns)
            a: Amplitude
            gamma: Power-law index (typically -4 for Rayleigh-like)

        Returns:
            Enhancement factor relative to Rayleigh
        """
        lambda_0 = 0.35  # Reference wavelength
        return a * (wavelength / lambda_0)**gamma

    def mie_scattering(self, wavelength: np.ndarray,
                       r_particle: float = 0.1,
                       n_real: float = 1.5,
                       n_imag: float = 0.0) -> np.ndarray:
        """
        Mie scattering cross-section (simplified).

        Args:
            wavelength: Wavelength (microns)
            r_particle: Particle radius (microns)
            n_real: Real refractive index
            n_imag: Imaginary refractive index

        Returns:
            Scattering cross-section (cm^2)
        """
        # Size parameter
        x = 2 * np.pi * r_particle / wavelength

        # Simplified Mie (geometrical limit for large particles)
        Q_sca = np.where(x < 1,
                        (8/3) * x**4 * ((n_real**2 - 1) / (n_real**2 + 2))**2,
                        2.0)  # Geometrical limit

        cross_section = Q_sca * np.pi * (r_particle * 1e-4)**2

        return cross_section


# =============================================================================
# CHEMICAL EQUILIBRIUM
# =============================================================================

class ChemicalEquilibrium:
    """
    Calculate equilibrium chemistry abundances.

    Uses simplified analytic expressions from Burrows & Sharp (1999).
    """

    def __init__(self, metallicity: float = 1.0, C_O: float = 0.55):
        """
        Initialize chemical equilibrium calculator.

        Args:
            metallicity: Metallicity in solar units
            C_O: Carbon-to-oxygen ratio
        """
        self.metallicity = metallicity
        self.C_O = C_O

        # Solar abundances (log10, relative to H)
        self.solar_C = -3.57 + np.log10(metallicity)
        self.solar_O = -3.31 + np.log10(metallicity)
        self.solar_N = -4.17 + np.log10(metallicity)

    def co_ch4_equilibrium(self, T: float, P: float) -> Tuple[float, float]:
        """
        CO/CH4 equilibrium abundances.

        Args:
            T: Temperature (K)
            P: Pressure (bar)

        Returns:
            (X_CO, X_CH4) volume mixing ratios
        """
        # Burrows & Sharp transition
        # CO dominates at high T, CH4 at low T
        # Transition around T_eq ~ 1500 K at 1 bar

        log_K = 4.0 - 5000 / T  # Simplified equilibrium constant

        K = 10**log_K * P**(-1)

        # Total C abundance
        X_C_total = 10**self.solar_C

        # Equilibrium partitioning
        if K > 100:
            X_CO = X_C_total
            X_CH4 = X_C_total / K
        elif K < 0.01:
            X_CH4 = X_C_total
            X_CO = X_C_total * K
        else:
            X_CO = X_C_total * K / (1 + K)
            X_CH4 = X_C_total / (1 + K)

        return X_CO, X_CH4

    def h2o_abundance(self, T: float, P: float) -> float:
        """
        H2O equilibrium abundance.

        Args:
            T: Temperature (K)
            P: Pressure (bar)

        Returns:
            H2O volume mixing ratio
        """
        # H2O stable across wide T range
        # Limited by O that's not in CO

        X_CO, _ = self.co_ch4_equilibrium(T, P)
        X_O_total = 10**self.solar_O

        # Remaining O goes to H2O
        X_H2O = max(X_O_total - X_CO, 1e-10)

        # Thermal dissociation at very high T
        if T > 2500:
            X_H2O *= np.exp(-(T - 2500) / 500)

        return X_H2O

    def nh3_n2_equilibrium(self, T: float, P: float) -> Tuple[float, float]:
        """
        NH3/N2 equilibrium.

        Args:
            T: Temperature (K)
            P: Pressure (bar)

        Returns:
            (X_NH3, X_N2) mixing ratios
        """
        # N2 dominates at high T, NH3 at low T
        log_K = 6.0 - 8000 / T

        K = 10**log_K * P**(-1)

        X_N_total = 10**self.solar_N

        if K > 100:
            X_N2 = X_N_total
            X_NH3 = X_N_total / K
        elif K < 0.01:
            X_NH3 = X_N_total
            X_N2 = X_N_total * K
        else:
            X_N2 = X_N_total * K / (1 + K)
            X_NH3 = X_N_total / (1 + K)

        return X_NH3, X_N2

    def abundances_at_pt(self, T: float, P: float) -> Dict[MoleculeType, float]:
        """
        Get all equilibrium abundances at given P, T.

        Args:
            T: Temperature (K)
            P: Pressure (bar)

        Returns:
            Dictionary of mixing ratios
        """
        X_CO, X_CH4 = self.co_ch4_equilibrium(T, P)
        X_H2O = self.h2o_abundance(T, P)
        X_NH3, X_N2 = self.nh3_n2_equilibrium(T, P)

        return {
            MoleculeType.CO: X_CO,
            MoleculeType.CH4: X_CH4,
            MoleculeType.H2O: X_H2O,
            MoleculeType.NH3: X_NH3,
        }


# =============================================================================
# ATMOSPHERIC RETRIEVAL
# =============================================================================

class AtmosphericRetrieval:
    """
    Bayesian atmospheric retrieval framework.

    Fits atmospheric parameters to observed spectra.
    """

    def __init__(self, params: AtmosphereParameters = None):
        """
        Initialize retrieval.

        Args:
            params: Initial atmospheric parameters
        """
        self.params = params or AtmosphereParameters()
        self.transmission = TransmissionSpectrum(self.params)
        self.emission = EmissionSpectrum(self.params)

    def log_likelihood(self, model: np.ndarray, data: np.ndarray,
                       errors: np.ndarray) -> float:
        """
        Calculate log-likelihood.

        Args:
            model: Model spectrum
            data: Observed spectrum
            errors: Measurement errors

        Returns:
            Log-likelihood value
        """
        chi2 = np.sum(((data - model) / errors)**2)
        return -0.5 * chi2

    def log_prior(self, theta: Dict[str, float]) -> float:
        """
        Calculate log-prior probability.

        Args:
            theta: Parameter dictionary

        Returns:
            Log-prior value
        """
        # Uniform priors with bounds
        bounds = {
            'T_eq': (500, 3000),
            'metallicity': (0.01, 100),
            'C_O': (0.1, 2.0),
            'log_Kzz': (4, 12),
            'P_cloud': (1e-6, 10),
            'cloud_opacity': (0, 100),
        }

        for key, (low, high) in bounds.items():
            if key in theta:
                if theta[key] < low or theta[key] > high:
                    return -np.inf

        return 0.0  # Uniform within bounds

    def run_retrieval(self, wavelength: np.ndarray, data: np.ndarray,
                      errors: np.ndarray, spectrum_type: str = 'transmission',
                      n_iterations: int = 1000) -> Dict[str, Any]:
        """
        Run MCMC retrieval (simplified).

        Args:
            wavelength: Wavelength array (microns)
            data: Observed spectrum
            errors: Measurement errors
            spectrum_type: 'transmission' or 'emission'
            n_iterations: Number of MCMC steps

        Returns:
            Retrieval results with posterior samples
        """
        # Simplified MCMC (would use emcee or dynesty in practice)

        # Parameter names to vary
        param_names = ['T_eq', 'metallicity']

        # Initial values
        current = {
            'T_eq': self.params.T_eq,
            'metallicity': self.params.metallicity,
        }

        samples = []
        likelihoods = []

        # Current model
        self._update_params(current)
        if spectrum_type == 'transmission':
            model = self.transmission.calculate(wavelength).spectrum
        else:
            model = self.emission.calculate(wavelength).spectrum

        current_ll = self.log_likelihood(model, data, errors)
        current_lp = self.log_prior(current)

        for i in range(n_iterations):
            # Propose new parameters
            proposal = current.copy()
            for key in param_names:
                scale = 0.1 * np.abs(current[key])
                proposal[key] = current[key] + np.random.normal(0, scale)

            # Calculate new model
            self._update_params(proposal)
            if spectrum_type == 'transmission':
                model = self.transmission.calculate(wavelength).spectrum
            else:
                model = self.emission.calculate(wavelength).spectrum

            new_ll = self.log_likelihood(model, data, errors)
            new_lp = self.log_prior(proposal)

            # Metropolis-Hastings acceptance
            log_alpha = new_ll + new_lp - current_ll - current_lp

            if np.log(np.random.random()) < log_alpha:
                current = proposal
                current_ll = new_ll
                current_lp = new_lp

            samples.append(current.copy())
            likelihoods.append(current_ll)

        # Burn-in removal and thinning
        samples = samples[n_iterations // 4:]

        # Extract parameter distributions
        results = {
            'samples': samples,
            'median': {key: np.median([s[key] for s in samples])
                      for key in param_names},
            'std': {key: np.std([s[key] for s in samples])
                   for key in param_names},
            'best_fit': samples[np.argmax(likelihoods[n_iterations // 4:])],
        }

        return results

    def _update_params(self, theta: Dict[str, float]):
        """Update internal parameters"""
        for key, value in theta.items():
            if hasattr(self.params, key):
                setattr(self.params, key, value)

        self.transmission.params = self.params
        self.emission.params = self.params


# =============================================================================
# EXPORTS
# =============================================================================

__all__ = [
    'MoleculeType',
    'AtmosphereParameters',
    'PTProfile',
    'SpectrumResult',
    'GuillotPTProfile',
    'IsothermalProfile',
    'OpacityDatabase',
    'TransmissionSpectrum',
    'EmissionSpectrum',
    'CloudModel',
    'ChemicalEquilibrium',
    'AtmosphericRetrieval',
]



def utility_function_27(*args, **kwargs):
    """Utility function 27."""
    return None



def utility_function_7(*args, **kwargs):
    """Utility function 7."""
    return None
