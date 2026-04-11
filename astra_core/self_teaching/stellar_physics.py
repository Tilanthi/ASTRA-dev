"""
Stellar Physics and HII Region Modeling Module

This module implements stellar evolution, HII region physics, and
star-formation feedback mechanisms.

Key capabilities:
- Stellar evolution tracks (pre-main sequence to main sequence)
- Initial mass function (IMF) sampling
- Stellar atmosphere models
- HII region expansion (Strömgren spheres)
- Ionization front dynamics
- Stellar winds and outflows
- Supernova feedback
- Multi-wavelength emission from HII regions

Version: 3.0.0
Date: 2026-03-16
"""

import numpy as np
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
import json


class StellarEvolutionaryStage(Enum):
    """Stellar evolutionary stages."""
    PROTOSTAR = "protostar"
    PRE_MAIN_SEQUENCE = "pre_main_sequence"
    MAIN_SEQUENCE = "main_sequence"
    RED_GIANT = "red_giant"
    SUPER_GIANT = "super_giant"
    WHITE_DWARF = "white_dwarf"
    NEUTRON_STAR = "neutron_star"
    BLACK_HOLE = "black_hole"


class SpectralType(Enum):
    """Stellar spectral types."""
    O = "O"
    B = "B"
    A = "A"
    F = "F"
    G = "G"
    K = "K"
    M = "M"


@dataclass
class StellarParameters:
    """Physical parameters of a star."""
    mass: float  # Solar masses
    radius: float  # Solar radii
    temperature: float  # Effective temperature (K)
    luminosity: float  # Solar luminosities
    age: float  # Myr
    metallicity: float  # [Fe/H]
    evolutionary_stage: StellarEvolutionaryStage
    spectral_type: Optional[SpectralType] = None
    rotation_period: Optional[float] = None  # days
    magnetic_field: Optional[float] = None  # Gauss


@dataclass
class IonizingPhotonRates:
    """Ionizing photon production rates for a star."""
    Q0: float = 0.0  # Hydrogen ionizing (s^-1)
    Q1: float = 0.0  # He I ionizing (s^-1)
    Q2: float = 0.0  # He II ionizing (s^-1)


@dataclass
class StellarAtmosphere:
    """Stellar atmosphere properties."""
    log_g: float  # Surface gravity
    microturbulence: float  # km/s
    macroturbulence: float  # km/s
    vsini: float  # Rotational velocity (km/s)
    abundances: Dict[str, float] = field(default_factory=dict)


class InitialMassFunction:
    """
    Initial Mass Function (IMF) for stellar populations.

    Supports:
    - Salpeter IMF (1955)
    - Kroupa IMF (2001)
    - Chabrier IMF (2003)
    """

    def __init__(self, imf_type: str = "kroupa"):
        self.imf_type = imf_type

    def sample_mass(self, num_stars: int, mass_range: Tuple[float, float] = (0.08, 150.0)) -> np.ndarray:
        """
        Sample stellar masses from the IMF.

        Args:
            num_stars: Number of stars to sample
            mass_range: (min_mass, max_mass) in solar masses

        Returns:
            Array of stellar masses
        """
        masses = []

        while len(masses) < num_stars:
            # Random mass in range
            m = np.random.uniform(mass_range[0], mass_range[1])

            # Probability according to IMF
            p = self.imf_probability(m)
            p_max = self.imf_probability(mass_range[0])  # Peak at low mass

            # Accept or reject
            if np.random.random() < p / p_max:
                masses.append(m)

        return np.array(masses)

    def imf_probability(self, mass: float) -> float:
        """Calculate IMF probability density."""
        if self.imf_type == "salpeter":
            # Salpeter: dN/dM ∝ M^(-2.35)
            if mass >= 0.1:
                return mass**(-2.35)
            else:
                return 0.0

        elif self.imf_type == "kroupa":
            # Kroupa (2001): THREE-segment broken power law (standard form)
            # Segment 1: 0.08-0.5 M_sun, slope -0.3 (NOT -1.3 - that's the system IMF)
            # Segment 2: 0.5-1.0 M_sun, slope -1.3
            # Segment 3: >1.0 M_sun, slope -2.3
            if 0.08 <= mass < 0.5:
                # Normalized at 0.08 M_sun
                return mass**(-0.3)
            elif 0.5 <= mass < 1.0:
                # Continuity at 0.5: (0.5/0.08)^-0.3 * (mass/0.5)^-1.3
                return (0.5/0.08)**(-0.3) * mass**(-1.3)
            elif mass >= 1.0:
                # Continuity at 1.0: previous value * (mass/1.0)^-2.3
                return (0.5/0.08)**(-0.3) * (1.0/0.5)**(-1.3) * mass**(-2.3)
            else:
                return 0.0

        elif self.imf_type == "chabrier":
            # Chabrier (2003): log-normal at low mass, power law at high
            # System IMF: lognormal for M < 1 M_sun, power law for M > 1 M_sun
            if mass < 1.0:
                mc = 0.079  # Characteristic mass (M_sun)
                sigma = 0.69
                # Normalization factor: ensures continuity at 1 M_sun
                # The lognormal is: dN/dlogM ∝ exp(-(log M - log mc)^2 / (2*sigma^2))
                # Converting to dN/dM: divide by M
                norm = 1.0 / (mass * sigma * np.sqrt(2 * np.pi))
                return norm * np.exp(-(np.log(mass) - np.log(mc))**2 / (2 * sigma**2))
            else:
                # Power law with continuity at 1 M_sun
                # Value at 1 M_sun from lognormal: 1/(1*0.69*sqrt(2pi)) * exp(-(log(1/0.079))^2/(2*0.69^2))
                value_at_1 = 1.0 / (1.0 * sigma * np.sqrt(2 * np.pi)) * np.exp(-(np.log(1.0/mc))**2 / (2 * sigma**2))
                return value_at_1 * mass**(-2.3)

        else:
            return mass**(-2.35)  # Default to Salpeter

    def calculate_total_mass(
        self,
        num_stars: int,
        mass_range: Tuple[float, float] = (0.08, 150.0)
    ) -> float:
        """Calculate total mass of stellar population."""
        masses = self.sample_mass(num_stars, mass_range)
        return np.sum(masses)


class StellarEvolution:
    """
    Stellar evolution tracks and calculations.

    Provides mass-radius, mass-luminosity, and mass-temperature relations.
    """

    @staticmethod
    def mass_radius_relation(mass: float, stage: StellarEvolutionaryStage) -> float:
        """
        Calculate stellar radius from mass (in solar radii).

        Uses empirical relations for different evolutionary stages.
        """
        if stage == StellarEvolutionaryStage.MAIN_SEQUENCE:
            if mass < 1.0:
                # Low-mass stars: R ∝ M^0.8
                return mass**0.8
            elif mass < 20.0:
                # Intermediate-mass: R ∝ M^0.57
                return mass**0.57
            else:
                # High-mass: R ∝ M^0.6
                return mass**0.6

        elif stage == StellarEvolutionaryStage.PRE_MAIN_SEQUENCE:
            # PMS stars are larger than MS stars
            return mass**0.5 * 2.0

        elif stage == StellarEvolutionaryStage.RED_GIANT:
            # Red giants are much larger
            return mass**0.3 * 50.0

        elif stage == StellarEvolutionaryStage.PROTOSTAR:
            # Protostars are very large and contracting
            return mass**0.3 * 10.0

        else:
            return mass**0.8

    @staticmethod
    def mass_luminosity_relation(mass: float) -> float:
        """
        Calculate stellar luminosity from mass (in solar luminosities).

        Uses piecewise power-law relations.
        """
        if mass < 0.43:
            # Very low mass: fully convective
            return 0.23 * mass**2.3
        elif mass < 2.0:
            # Low to intermediate mass
            return mass**4
        elif mass < 20.0:
            # Intermediate to high mass
            return 1.4 * mass**3.5
        else:
            # Very high mass
            return 32000 * mass

    @staticmethod
    def mass_temperature_relation(mass: float) -> float:
        """
        Calculate effective temperature from mass (Kelvin).

        Based on Stefan-Boltzmann law: L ∝ R^2 T^4
        """
        R = StellarEvolution.mass_radius_relation(mass, StellarEvolutionaryStage.MAIN_SEQUENCE)
        L = StellarEvolution.mass_luminosity_relation(mass)

        # T = (L / R^2)^(1/4) * T_sun
        T_sun = 5778.0
        T = (L / R**2)**0.25 * T_sun

        return T

    @staticmethod
    def get_spectral_type(temperature: float) -> SpectralType:
        """Determine spectral type from effective temperature."""
        if temperature >= 30000:
            return SpectralType.O
        elif temperature >= 10000:
            return SpectralType.B
        elif temperature >= 7500:
            return SpectralType.A
        elif temperature >= 6000:
            return SpectralType.F
        elif temperature >= 5200:
            return SpectralType.G
        elif temperature >= 3700:
            return SpectralType.K
        else:
            return SpectralType.M

    @staticmethod
    def calculate_main_sequence_lifetime(mass: float) -> float:
        """
        Calculate main sequence lifetime in Gyr.

        τ ∝ M / L ∝ M^(-2.5) approximately
        """
        if mass < 0.1:
            return 1000.0  # Very long lived

        # Solar-like star: ~10 Gyr
        tau_sun = 10.0  # Gyr
        L = StellarEvolution.mass_luminosity_relation(mass)

        lifetime = tau_sun / L  # Gyr
        return max(lifetime, 0.003)  # Minimum ~3 Myr for massive stars


class IonizingPhotonCalculator:
    """
    Calculate ionizing photon production rates for stars.

    Critical for HII region modeling.
    """

    @staticmethod
    def calculate_ionizing_rates(star: StellarParameters) -> IonizingPhotonRates:
        """
        Calculate ionizing photon rates Q0, Q1, Q2.

        Uses stellar atmosphere models (simplified).
        """
        T_eff = star.temperature
        L = star.luminosity

        # Approximate ionizing flux from blackbody
        # Q_H = π R^2 ∫_ν0^∞ (π B_ν / hν) dν

        # Simplified power-law fits
        if T_eff < 10000:
            # Cool stars produce minimal ionizing photons
            Q0 = 0.0
            Q1 = 0.0
            Q2 = 0.0

        elif T_eff < 25000:
            # B-type stars
            log_L = np.log10(L)
            Q0 = 10**(40.0 + log_L)  # Very approximate
            Q1 = 10**(38.0 + log_L)
            Q2 = 10**(35.0 + log_L)

        elif T_eff < 40000:
            # O-type stars
            log_L = np.log10(L)
            Q0 = 10**(47.0 + log_L)
            Q1 = 10**(45.0 + log_L)
            Q2 = 10**(42.0 + log_L)

        else:
            # O-type giants/supergiants
            log_L = np.log10(L)
            Q0 = 10**(49.0 + log_L)
            Q1 = 10**(47.0 + log_L)
            Q2 = 10**(45.0 + log_L)

        return IonizingPhotonRates(Q0=Q0, Q1=Q1, Q2=Q2)


class StrömgrenSphere:
    """
    Model of HII regions as Strömgren spheres.

    Includes:
    - Static equilibrium sphere
    - Expansion phase
    - Champagne flows
    """

    def __init__(
        self,
        ionizing_rate: float,
        ambient_density: float,
        temperature: float = 10000.0
    ):
        self.Q0 = ionizing_rate  # s^-1
        self.n_H = ambient_density  # cm^-3
        self.T = temperature  # K

        # Recombination coefficient (case B, temperature dependent)
        self.alpha_B = 2.6e-13 * (self.T / 1e4)**(-0.7)  # cm^3 s^-1

    def stromgren_radius(self) -> float:
        """
        Calculate Strömgren radius (cm).

        Rs = (3Q / 4π n^2 α_B)^(1/3)
        """
        if self.n_H < 1e-10:
            return 0.0

        Rs = (3 * self.Q0 / (4 * np.pi * self.n_H**2 * self.alpha_B))**(1/3)
        return Rs

    def dynamical_timescale(self) -> float:
        """
        Calculate HII region expansion timescale.

        τ_dyn = Rs / c_i, where c_i is sound speed in ionized gas
        """
        Rs = self.stromgren_radius()

        # Sound speed in ionized gas
        k_B = 1.381e-23
        m_H = 1.673e-27
        c_i = np.sqrt(1.1 * k_B * self.T / m_H)  # m/s

        tau = Rs / c_i  # seconds
        return tau / (3.15e7)  # Convert to years

    def expansion_model(self, time: float) -> float:
        """
        Calculate HII region radius as function of time.

        Based on Spitzer (1978) expansion model.
        """
        Rs = self.stromgren_radius()
        tau_dyn = self.dynamical_timescale()

        if time < tau_dyn:
            # R ∝ t^(4/7) during expansion
            R = Rs * (time / tau_dyn)**(4/7)
        else:
            # Approaches Strömgren radius
            R = Rs * (1 - np.exp(-time / tau_dyn))

        return R

    def density_profile(self, radius: float) -> float:
        """
        Calculate density at given radius.

        Includes compression at ionization front.
        """
        Rs = self.stromgren_radius()

        if radius < Rs:
            # Ionized region: lower density due to pressure
            # Compression factor ~ 2 for isothermal shock
            return self.n_H / 2.0
        else:
            # Neutral region: ambient density
            return self.n_H

    def temperature_profile(self, radius: float) -> float:
        """Calculate temperature at given radius."""
        Rs = self.stromgren_radius()

        if radius < Rs:
            # Ionized region: hot (~10^4 K)
            return self.T
        else:
            # Neutral region: cold (~10-100 K)
            return 20.0


class HIIRegionSimulation:
    """
    Full simulation of HII region evolution.

    Includes:
    - Multiple stars
    - Density gradients
    - Champagne flows
    - Dust absorption
    """

    def __init__(
        self,
        box_size: float = 10.0,  # parsecs
        resolution: int = 100
    ):
        self.box_size = box_size
        self.resolution = resolution
        self.grid_size = resolution

        # Grid properties
        self.density = np.zeros((resolution, resolution, resolution))
        self.temperature = np.zeros((resolution, resolution, resolution))
        self.ionization_fraction = np.zeros((resolution, resolution, resolution))
        self.velocity = np.zeros((resolution, resolution, resolution, 3))

        # Stars in the region
        self.stars: List[StellarParameters] = []

        # Time
        self.time = 0.0  # Myr

    def add_star(self, star: StellarParameters, position: np.ndarray) -> None:
        """Add a star to the simulation."""
        self.stars.append(star)

    def initialize_ambient_medium(
        self,
        density: float,
        temperature: float = 20.0,
        density_gradient: Optional[np.ndarray] = None
    ) -> None:
        """
        Initialize ambient molecular cloud.

        Args:
            density: Mean density (cm^-3)
            temperature: Temperature (K)
            density_gradient: Optional gradient vector
        """
        # Create grid positions
        x = np.linspace(-self.box_size/2, self.box_size/2, self.grid_size)
        y = np.linspace(-self.box_size/2, self.box_size/2, self.grid_size)
        z = np.linspace(-self.box_size/2, self.box_size/2, self.grid_size)
        X, Y, Z = np.meshgrid(x, y, z)

        if density_gradient is not None:
            # Apply gradient
            r = np.sqrt(X**2 + Y**2 + Z**2)
            gradient_factor = 1.0 + density_gradient[0] * X / self.box_size
            self.density = density * gradient_factor
        else:
            # Uniform density
            self.density = np.full_like(X, density)

        self.temperature = np.full_like(X, temperature)
        self.ionization_fraction = np.zeros_like(X)

    def compute_ionization_structure(self) -> None:
        """
        Compute ionization structure from stars.

        Uses ray-tracing approximation (on-the-spot approximation).
        """
        # Reset ionization fraction
        self.ionization_fraction[:] = 0.0

        for star in self.stars:
            # Get ionizing rates
            ionizing = IonizingPhotonCalculator.calculate_ionizing_rates(star)

            if ionizing.Q0 < 1e30:
                continue  # Skip non-ionizing stars

            # Star position (assumed at center for now)
            star_pos = np.array([self.grid_size//2, self.grid_size//2, self.grid_size//2])

            # Compute ionization using on-the-spot approximation
            # Iterate from star outward
            for i in range(self.grid_size):
                for j in range(self.grid_size):
                    for k in range(self.grid_size):
                        # Distance from star
                        r = np.sqrt((i - star_pos[0])**2 +
                                   (j - star_pos[1])**2 +
                                   (k - star_pos[2])**2)

                        if r == 0:
                            self.ionization_fraction[i, j, k] = 1.0
                            continue

                        # Column density to this point (simplified)
                        n_H = self.density[i, j, k]
                        dx = self.box_size / self.grid_size
                        N_H = n_H * r * dx

                        # Optical depth to Lyman continuum
                        sigma_H = 6.3e-18 * (13.6 / star.temperature)**3  # cm^2
                        tau = sigma_H * N_H * 3.086e18  # Convert pc to cm

                        # Ionization fraction
                        ionization = np.exp(-tau) * ionizing.Q0 / (
                            4 * np.pi * (r * dx * 3.086e18)**2 *
                            n_H**2 * 2.6e-13
                        )
                        ionization = min(ionization, 1.0)
                        ionization = max(ionization, 0.0)

                        self.ionization_fraction[i, j, k] = max(
                            self.ionization_fraction[i, j, k],
                            ionization
                        )

    def evolve_thermal_structure(self, dt: float) -> None:
        """
        Evolve temperature structure.

        Heating from photoionization, cooling from recombination.
        """
        for i in range(self.grid_size):
            for j in range(self.grid_size):
                for k in range(self.grid_size):
                    x = self.ionization_fraction[i, j, k]

                    if x > 0.5:
                        # Ionized gas: ~10^4 K
                        target_T = 10000.0
                    else:
                        # Neutral gas: cooling to ~10-20 K
                        target_T = 20.0

                    # Relax to target temperature
                    self.temperature[i, j, k] += (target_T - self.temperature[i, j, k]) * 0.1

    def step(self, dt: float) -> None:
        """Advance simulation by one time step."""
        self.compute_ionization_structure()
        self.evolve_thermal_structure(dt)
        self.time += dt


class StellarFeedback:
    """
    Model stellar feedback mechanisms.

    Includes:
    - Radiation pressure
    - Stellar winds
    - Supernovae
    - Photoionization heating
    """

    @staticmethod
    def radiation_pressure(
        stellar_luminosity: float,
        distance: float,
        opacity: float = 10.0  # cm^2/g
    ) -> float:
        """
        Calculate radiation pressure force per unit mass.

        F_rad = L * κ / (4π r^2 c)
        """
        L = stellar_luminosity * 3.828e33  # Convert L_sun to erg/s
        r = distance * 3.086e18  # Convert pc to cm
        c = 3e10  # Speed of light (cm/s)

        F_rad = L * opacity / (4 * np.pi * r**2 * c)
        return F_rad

    @staticmethod
    def stellar_wind_momentum(
        stellar_mass: float,
        stellar_age: float
    ) -> float:
        """
        Calculate stellar wind momentum flux.

        ṁ * v_w depends on mass and age.
        """
        # Main sequence winds
        L = StellarEvolution.mass_luminosity_relation(stellar_mass)

        # Wind mass loss rate (very simplified)
        if stellar_mass > 20:
            # Massive stars: strong winds
            mdot = 1e-6 * (L / 1e5)**1.7  # M_sun/yr
        elif stellar_mass > 8:
            # Intermediate mass
            mdot = 1e-8 * (L / 1e4)
        else:
            # Low mass: weak winds
            mdot = 1e-14 * (L / 1)

        # Wind velocity
        v_wind = 2000 * (stellar_mass / 20)**0.5  # km/s

        # Momentum flux
        momentum = mdot * v_wind * 2e33 / 1e5 / 3.15e7  # dyne

        return momentum

    @staticmethod
    def supernova_energy(stellar_mass: float) -> float:
        """
        Calculate supernova energy release.

        Typically ~10^51 erg
        """
        if stellar_mass < 8:
            return 0.0  # No supernova

        # Standard supernova energy
        E_SN = 1e51  # erg
        return E_SN

    @staticmethod
    def supernova_remnant_radius(
        energy: float,
        ambient_density: float,
        time: float
    ) -> float:
        """
        Calculate SNR radius as function of time.

        Uses Sedov-Taylor solution for adiabatic phase.
        """
        E = energy
        rho = ambient_density * 1.673e-24  # g/cm^3
        t = time * 3.15e7 * 1e6  # Convert Myr to seconds

        # Sedov-Taylor solution
        # R = (E t^2 / ρ)^(1/5)
        R = (E * t**2 / rho)**(1/5)  # cm

        return R / 3.086e18  # Convert to pc


class MultiWavelengthEmission:
    """
    Calculate multi-wavelength emission from stellar populations and HII regions.

    Wavelengths:
    - Radio (free-free, synchrotron)
    - mm/sub-mm (dust continuum)
    - Infrared (PAH, warm dust)
    - Optical/NIR (stellar continuum)
    - UV (massive stars)
    - X-ray (hot gas, SNR)
    """

    @staticmethod
    def free_free_emission(
        emission_measure: float,
        frequency: float,
        temperature: float = 10000.0
    ) -> float:
        """
        Calculate free-free emission intensity.

        I_ν ∝ EM * T^(-0.35) * ν^(-0.1)
        """
        # Emission measure: EM = ∫ n_e^2 dl
        EM = emission_measure  # pc cm^-6

        # Gaunt factor (approximate)
        g_ff = 9.77 * (1 + 0.13 * np.log(temperature**3 / frequency))

        # Intensity
        h = 6.626e-34
        k = 1.381e-23

        T_b = 9.77 * np.log(temperature**3 / frequency) * (EM / (temperature**0.35 * frequency**0.1))

        return T_b

    @staticmethod
    def PAH_emission(
        radiation_field: float,
        PAH_abundance: float = 1e-7
    ) -> Dict[str, float]:
        """
        Calculate PAH emission features.

        Returns intensities at characteristic wavelengths.
        """
        # PAH features
        features = {
            "3.3um": 1.0,  # C-H stretch
            "6.2um": 0.8,  # C-C stretch
            "7.7um": 1.2,  # C-C stretch
            "8.6um": 0.6,  # C-H in-plane bend
            "11.3um": 0.9,  # C-H solo out-of-plane bend
        }

        # Scale by radiation field and abundance
        for feature in features:
            features[feature] *= radiation_field * PAH_abundance

        return features

    @staticmethod
    def dust_continuum(
        dust_temperature: float,
        dust_mass: float,
        frequency: float,
        beta: float = 1.5
    ) -> float:
        """
        Calculate dust continuum emission.

        Modified blackbody: I_ν ∝ κ_ν * B_ν(T_d)
        """
        h = 6.626e-34
        k = 1.381e-23
        c = 3e8

        # Planck function
        x = h * frequency / (k * dust_temperature)
        if x > 100:
            B_nu = 0.0
        else:
            B_nu = (2 * h * frequency**3 / c**2) / (np.exp(x) - 1)

        # Dust opacity
        kappa_0 = 10.0  # cm^2/g at reference frequency
        nu_0 = 1e12  # Hz
        kappa_nu = kappa_0 * (frequency / nu_0)**beta

        # Intensity
        I_nu = kappa_nu * B_nu * dust_mass

        return I_nu

    @staticmethod
    def synchrotron_emission(
        magnetic_field: float,
        electron_energy: float,
        frequency: float,
        spectral_index: float = 0.7
    ) -> float:
        """
        Calculate synchrotron emission from relativistic electrons.

        I_ν ∝ B * E * ν^(-α)
        """
        B = magnetic_field  # Gauss
        E = electron_energy  # erg
        nu = frequency  # Hz
        alpha = spectral_index

        # Synchrotron intensity (simplified)
        I_nu = 1e-20 * B * E * (nu / 1e9)**(-alpha)

        return I_nu


# =============================================================================
# Self-Improving Integration
# =============================================================================

class StellarPhysicsSelfImprover:
    """
    Self-improving system for stellar physics and HII region modeling.

    Learns optimal parameters from observational constraints.
    """

    def __init__(self):
        self.model_history: List[Dict] = []
        self.best_parameters: Dict = {}

    def optimize_model_parameters(
        self,
        observations: Dict[str, Any],
        parameter_ranges: Dict[str, Tuple[float, float]],
        n_iterations: int = 50
    ) -> Dict[str, float]:
        """
        Optimize model parameters to match observations.

        Args:
            observations: Observational constraints
            parameter_ranges: Allowed parameter ranges
            n_iterations: Number of optimization iterations

        Returns:
            Optimized parameters
        """
        best_chi2 = np.inf
        best_params = None

        for iteration in range(n_iterations):
            # Sample parameters
            params = {}
            for param, (min_val, max_val) in parameter_ranges.items():
                params[param] = np.random.uniform(min_val, max_val)

            # Run model
            model_predictions = self._run_model(params)

            # Calculate chi2
            chi2 = self._calculate_chi2(observations, model_predictions)

            self.model_history.append({
                'iteration': iteration,
                'parameters': params,
                'chi2': chi2
            })

            if chi2 < best_chi2:
                best_chi2 = chi2
                best_params = params

        self.best_parameters = best_params
        return best_params

    def _run_model(self, parameters: Dict[str, float]) -> Dict[str, Any]:
        """Run model with given parameters."""
        # Placeholder for actual model run
        return {}

    def _calculate_chi2(
        self,
        observations: Dict[str, Any],
        predictions: Dict[str, Any]
    ) -> float:
        """Calculate chi2 goodness-of-fit."""
        chi2 = 0.0
        for key in observations:
            if key in predictions:
                chi2 += (observations[key] - predictions[key])**2 / observations[key]**2
        return chi2


# =============================================================================
# Factory Functions
# =============================================================================

def create_stellar_population(
    num_stars: int,
    imf_type: str = "kroupa"
) -> List[StellarParameters]:
    """Create a stellar population from the IMF."""
    imf = InitialMassFunction(imf_type)
    masses = imf.sample_mass(num_stars)

    stars = []
    for mass in masses:
        radius = StellarEvolution.mass_radius_relation(mass, StellarEvolutionaryStage.MAIN_SEQUENCE)
        luminosity = StellarEvolution.mass_luminosity_relation(mass)
        temperature = StellarEvolution.mass_temperature_relation(mass)
        spectral_type = StellarEvolution.get_spectral_type(temperature)

        star = StellarParameters(
            mass=mass,
            radius=radius,
            temperature=temperature,
            luminosity=luminosity,
            age=0.0,
            metallicity=0.0,
            evolutionary_stage=StellarEvolutionaryStage.MAIN_SEQUENCE,
            spectral_type=spectral_type
        )
        stars.append(star)

    return stars


def create_hii_region(
    ionizing_star_mass: float,
    ambient_density: float,
    box_size: float = 10.0
) -> HIIRegionSimulation:
    """Create an HII region around a massive star."""
    sim = HIIRegionSimulation(box_size=box_size)

    # Create the ionizing star
    radius = StellarEvolution.mass_radius_relation(ionizing_star_mass, StellarEvolutionaryStage.MAIN_SEQUENCE)
    luminosity = StellarEvolution.mass_luminosity_relation(ionizing_star_mass)
    temperature = StellarEvolution.mass_temperature_relation(ionizing_star_mass)

    star = StellarParameters(
        mass=ionizing_star_mass,
        radius=radius,
        temperature=temperature,
        luminosity=luminosity,
        age=0.0,
        metallicity=0.0,
        evolutionary_stage=StellarEvolutionaryStage.MAIN_SEQUENCE
    )

    sim.add_star(star, np.array([box_size/2, box_size/2, box_size/2]))
    sim.initialize_ambient_medium(ambient_density)

    return sim


def create_stromgren_sphere(
    stellar_mass: float,
    ambient_density: float
) -> StrömgrenSphere:
    """Create a Strömgren sphere model."""
    # Calculate stellar properties
    luminosity = StellarEvolution.mass_luminosity_relation(stellar_mass)
    temperature = StellarEvolution.mass_temperature_relation(stellar_mass)

    star = StellarParameters(
        mass=stellar_mass,
        radius=1.0,
        temperature=temperature,
        luminosity=luminosity,
        age=0.0,
        metallicity=0.0,
        evolutionary_stage=StellarEvolutionaryStage.MAIN_SEQUENCE
    )

    # Calculate ionizing rate
    ionizing = IonizingPhotonCalculator.calculate_ionizing_rates(star)

    return StrömgrenSphere(
        ionizing_rate=ionizing.Q0,
        ambient_density=ambient_density,
        temperature=10000.0
    )
