"""
Relativistic physics curriculum stage for STAN-XI-ASTRO

Implements advanced physics curriculum covering:
- Special relativity (Lorentz transformations, time dilation, length contraction)
- General relativity basics (metric tensor, geodesics, Einstein field equations)
- Black hole physics (Schwarzschild and Kerr metrics, event horizons)
- Gravitational redshift and lensing
- Relativistic beaming and jets
- Gravitational waves

This extends the physics curriculum from classical mechanics through MHD to include
relativistic effects essential for high-energy astrophysics.

Date: 2025-12-23
Version: 47.0
"""

import numpy as np
from typing import Dict, List, Any, Optional, Tuple, Union
from dataclasses import dataclass, field
from enum import Enum
import logging

logger = logging.getLogger(__name__)

# Import curriculum learning base
try:
    from .curriculum_learning import (
        PhysicsCurriculum, LearningStage, ComplexityLevel,
        LearningProgress
    )
except ImportError:
    # Fallback definitions if curriculum_learning not available
    class ComplexityLevel(Enum):
        INTRODUCTORY = 1
        INTERMEDIATE = 2
        ADVANCED = 3
        EXPERT = 4

    @dataclass
    class LearningStage:
        name: str
        complexity: ComplexityLevel
        prerequisites: List[str] = field(default_factory=list)
        concepts: List[str] = field(default_factory=list)
        skills: List[str] = field(default_factory=list)
        problems: List[Dict[str, Any]] = field(default_factory=list)
        mastery_threshold: float = 0.9


# Physical constants (CGS units)
C = 2.998e10  # Speed of light (cm/s)
G = 6.674e-8  # Gravitational constant (dyn cm^2/g^2)
H = 6.626e-27  # Planck constant (erg s)
HC = H * C  # h*c in erg cm


class RelativisticPhysics:
    """
    Relativistic physics module for curriculum learning

    Provides learning stages for special and general relativity,
    extending from intermediate to expert level complexity.
    """

    # Stage definitions
    STAGE_SPECIAL_RELATIVITY = "special_relativity"
    STAGE_GENERAL_RELATIVITY = "general_relativity"
    STAGE_BLACK_HOLES = "black_holes"
    STAGE_GRAVITATIONAL_WAVES = "gravitational_waves"
    STAGE_RELATIVISTIC_COSMOLOGY = "relativistic_cosmology"

    @staticmethod
    def get_learning_stages() -> List[LearningStage]:
        """
        Return all relativistic physics learning stages

        Returns:
            List of LearningStage objects in recommended order
        """
        return [
            # Stage 1: Special Relativity
            LearningStage(
                name=RelativisticPhysics.STAGE_SPECIAL_RELATIVITY,
                complexity=ComplexityLevel.ADVANCED,
                prerequisites=["basic_mechanics", "electromagnetism"],
                concepts=[
                    # Core concepts
                    "lorentz_transformation",
                    "time_dilation",
                    "length_contraction",
                    "relativistic_velocity_addition",
                    "mass_energy_equivalence",
                    "relativistic_momentum",
                    "relativistic_energy",
                    "spacetime_interval",
                    "light_cone",
                    "proper_time",
                    "minkowski_metric",
                    "four_vectors",
                    "relativistic_doppler",
                    "beaming"
                ],
                skills=[
                    # Computational skills
                    "compute_lorentz_factor",
                    "apply_time_dilation_formula",
                    "calculate_length_contraction",
                    "relativistic_velocity_composition",
                    "compute_relativistic_energy",
                    "analyze_spacetime_diagrams",
                    "compute_relativistic_doppler_shift",
                    "calculate_relativistic_beaming"
                ],
                problems=[
                    {
                        "type": "time_dilation",
                        "description": "Calculate time dilation for muon decay",
                        "parameters": {"velocity": 0.99, "lifetime": 2.2e-6}
                    },
                    {
                        "type": "length_contraction",
                        "description": "Calculate length contraction of spaceship",
                        "parameters": {"velocity": 0.8, "proper_length": 100}
                    },
                    {
                        "type": "energy_momentum",
                        "description": "Compute relativistic kinetic energy",
                        "parameters": {"mass": 1, "velocity": 0.9}
                    }
                ],
                mastery_threshold=0.80
            ),

            # Stage 2: General Relativity Basics
            LearningStage(
                name=RelativisticPhysics.STAGE_GENERAL_RELATIVITY,
                complexity=ComplexityLevel.EXPERT,
                prerequisites=[
                    RelativisticPhysics.STAGE_SPECIAL_RELATIVITY,
                    "gravitational_physics"
                ],
                concepts=[
                    # Geometric foundations
                    "metric_tensor",
                    "geodesic_equation",
                    "christoffel_symbols",
                    "riemann_tensor",
                    "ricci_tensor",
                    "ricci_scalar",
                    "einstein_tensor",
                    "einstein_field_equations",
                    "stress_energy_tensor",
                    "schwarzschild_metric",
                    "gravitational_redshift",
                    "light_deflection",
                    "shapiro_delay",
                    "perihelion_precession",
                    "geodetic_precession",
                    "equivalence_principle"
                ],
                skills=[
                    # Mathematical skills
                    "compute_metric_components",
                    "calculate_christoffel_symbols",
                    "solve_geodesic_equations",
                    "compute_einstein_tensor",
                    "solve_schwarzschild_geodesics",
                    "calculate_gravitational_redshift",
                    "compute_light_deflection_angle",
                    "analyze_perihelion_precession",
                    "calculate_proper_time_interval"
                ],
                problems=[
                    {
                        "type": "schwarzschild_radius",
                        "description": "Calculate Schwarzschild radius for stellar mass black hole",
                        "parameters": {"mass": 10}  # Solar masses
                    },
                    {
                        "type": "gravitational_redshift",
                        "description": "Compute gravitational redshift from neutron star surface",
                        "parameters": {"mass": 1.4, "radius": 10}
                    },
                    {
                        "type": "light_deflection",
                        "description": "Calculate light deflection by the Sun",
                        "parameters": {"impact_parameter": 1.0}
                    }
                ],
                mastery_threshold=0.75
            ),

            # Stage 3: Black Hole Physics
            LearningStage(
                name=RelativisticPhysics.STAGE_BLACK_HOLES,
                complexity=ComplexityLevel.EXPERT,
                prerequisites=[RelativisticPhysics.STAGE_GENERAL_RELATIVITY],
                concepts=[
                    # Black hole properties
                    "event_horizon",
                    "singularity",
                    "apparent_horizon",
                    "trapped_surface",
                    "ergosphere",
                    "kerr_metric",
                    "kerr_newman_metric",
                    "rotating_black_holes",
                    "frame_dragging",
                    "penrose_process",
                    "superradiance",
                    "hawking_radiation",
                    "black_thermodynamics",
                    "information_paradox",
                    "accretion_disk_physics",
                    "bondi_accretion",
                    "eddington_luminosity",
                    "blandford_znajek_mechanism",
                    "quasi_periodic_oscillations"
                ],
                skills=[
                    # Analysis skills
                    "compute_event_horizon_radius",
                    "calculate_ergosphere_boundary",
                    "analyze_frame_dragging_effects",
                    "compute_hawking_temperature",
                    "calculate_black_hole_entropy",
                    "analyze_accretion_disk_structure",
                    "compute_eddington_luminosity",
                    "analyze_jet_formation_mechanisms",
                    "calculate_quasinormal_modes",
                    "analyze_black_hole_shadow"
                ],
                problems=[
                    {
                        "type": "kerr_horizon",
                        "description": "Calculate event horizon for rotating black hole",
                        "parameters": {"mass": 10, "spin": 0.9}
                    },
                    {
                        "type": "accretion_power",
                        "description": "Compute accretion disk luminosity",
                        "parameters": {"mass": 1e6, "accretion_rate": 0.1}
                    },
                    {
                        "type": "hawking_radiation",
                        "description": "Calculate Hawking temperature and lifetime",
                        "parameters": {"mass": 1e10}
                    }
                ],
                mastery_threshold=0.70
            ),

            # Stage 4: Gravitational Waves
            LearningStage(
                name=RelativisticPhysics.STAGE_GRAVITATIONAL_WAVES,
                complexity=ComplexityLevel.EXPERT,
                prerequisites=[RelativisticPhysics.STAGE_GENERAL_RELATIVITY],
                concepts=[
                    # Gravitational wave fundamentals
                    "linearized_gravity",
                    "quadrupole_formula",
                    "gravitational_wave_polarizations",
                    "plus_polarization",
                    "cross_polarization",
                    "strain_amplitude",
                    "chirp_mass",
                    "inspiral_merger_ringdown",
                    "post_newtonian_expansion",
                    "matched_filtering",
                    "lisa",
                    "ligo",
                    "virgo",
                    "kagra",
                    "pulsar_timing_arrays",
                    "stochastic_background",
                    "continuous_waves",
                    "binary_neutron_stars",
                    "binary_black_holes"
                ],
                skills=[
                    # Computation and analysis
                    "compute_quadrupole_moment",
                    "calculate_strain_amplitude",
                    "analyze_chirp_signal",
                    "compute_chirp_mass",
                    "calculate_merger_time",
                    "analyze_post_newtonian_waveforms",
                    "apply_matched_filtering",
                    "estimate_source_parameters",
                    "calculate_detector_response",
                    "analyze_pulsar_timing_residuals"
                ],
                problems=[
                    {
                        "type": "binary_inspiral",
                        "description": "Calculate gravitational wave strain from binary inspiral",
                        "parameters": {"mass1": 30, "mass2": 30, "distance": 100}
                    },
                    {
                        "type": "chirp_mass",
                        "description": "Compute chirp mass from observed frequency evolution",
                        "parameters": {"frequency_derivative": 1e-7, "frequency": 100}
                    },
                    {
                        "type": "merger_time",
                        "description": "Calculate time to merger for binary system",
                        "parameters": {"mass1": 10, "mass2": 10, "separation": 0.1}
                    }
                ],
                mastery_threshold=0.70
            ),

            # Stage 5: Relativistic Cosmology
            LearningStage(
                name=RelativisticPhysics.STAGE_RELATIVISTIC_COSMOLOGY,
                complexity=ComplexityLevel.EXPERT,
                prerequisites=[RelativisticPhysics.STAGE_GENERAL_RELATIVITY],
                concepts=[
                    # Cosmological framework
                    "friedmann_lemaitre_robertson_walker",
                    "friedmann_equations",
                    "hubble_parameter",
                    "scale_factor",
                    "cosmological_constant",
                    "dark_energy",
                    "critical_density",
                    "density_parameters",
                    "deceleration_parameter",
                    "equation_of_state",
                    "inflation",
                    "reheating",
                    "big_bang_nucleosynthesis",
                    "recombination",
                    "reionization",
                    "cosmic_microwave_background",
                    "large_scale_structure",
                    "baryon_acoustic_oscillations",
                    "type_ia_supernovae"
                ],
                skills=[
                    # Cosmological calculations
                    "solve_friedmann_equations",
                    "compute_hubble_parameter",
                    "calculate_cosmic_distances",
                    "analyze_expansion_history",
                    "compute_cmb_temperature",
                    "calculate_recombination_redshift",
                    "analyze_structure_formation",
                    "compute_matter_power_spectrum",
                    "interpret_observational_constraints"
                ],
                problems=[
                    {
                        "type": "expansion_history",
                        "description": "Calculate scale factor evolution in ΛCDM",
                        "parameters": {"H0": 70, "omega_m": 0.3, "omega_lambda": 0.7}
                    },
                    {
                        "type": "cosmic_distances",
                        "description": "Compute luminosity and angular diameter distances",
                        "parameters": {"redshift": 1.0, "H0": 70, "omega_m": 0.3}
                    },
                    {
                        "type": "cmb_anisotropy",
                        "description": "Analyze CMB angular power spectrum features",
                        "parameters": {"l_max": 2500}
                    }
                ],
                mastery_threshold=0.70
            )
        ]

    # Special Relativity Calculations

    @staticmethod
    def lorentz_factor(velocity: Union[float, np.ndarray]) -> Union[float, np.ndarray]:
        """
        Calculate Lorentz factor γ = 1/√(1 - v²/c²)

        Args:
            velocity: Velocity in cm/s (can be array)

        Returns:
            Lorentz factor γ

        Raises:
            ValueError: If velocity >= c
        """
        beta = velocity / C

        # Handle array input
        if isinstance(velocity, np.ndarray):
            if np.any(np.abs(beta) >= 1):
                raise ValueError("Velocity cannot exceed speed of light")
            return 1.0 / np.sqrt(1 - beta**2)
        else:
            if abs(beta) >= 1:
                raise ValueError("Velocity cannot exceed speed of light")
            return 1.0 / np.sqrt(1 - beta**2)

    @staticmethod
    def time_dilation(
        proper_time: Union[float, np.ndarray],
        velocity: Union[float, np.ndarray]
    ) -> Union[float, np.ndarray]:
        """
        Calculate coordinate time from proper time: t = γτ

        Args:
            proper_time: Proper time interval (s)
            velocity: Velocity (cm/s)

        Returns:
            Coordinate time interval (s)
        """
        gamma = RelativisticPhysics.lorentz_factor(velocity)
        return gamma * proper_time

    @staticmethod
    def length_contraction(
        proper_length: Union[float, np.ndarray],
        velocity: Union[float, np.ndarray]
    ) -> Union[float, np.ndarray]:
        """
        Calculate contracted length: L = L₀/γ

        Args:
            proper_length: Proper length (cm)
            velocity: Velocity (cm/s)

        Returns:
            Contracted length (cm)
        """
        gamma = RelativisticPhysics.lorentz_factor(velocity)
        return proper_length / gamma

    @staticmethod
    def relativistic_energy(
        mass: Union[float, np.ndarray],
        velocity: Union[float, np.ndarray]
    ) -> Union[float, np.ndarray]:
        """
        Calculate total relativistic energy: E = γmc²

        Args:
            mass: Rest mass (g)
            velocity: Velocity (cm/s)

        Returns:
            Total energy (erg)
        """
        gamma = RelativisticPhysics.lorentz_factor(velocity)
        return gamma * mass * C**2

    @staticmethod
    def relativistic_momentum(
        mass: Union[float, np.ndarray],
        velocity: Union[float, np.ndarray]
    ) -> Union[float, np.ndarray]:
        """
        Calculate relativistic momentum: p = γmv

        Args:
            mass: Rest mass (g)
            velocity: Velocity (cm/s)

        Returns:
            Relativistic momentum (g cm/s)
        """
        gamma = RelativisticPhysics.lorentz_factor(velocity)
        return gamma * mass * velocity

    @staticmethod
    def relativistic_kinetic_energy(
        mass: Union[float, np.ndarray],
        velocity: Union[float, np.ndarray]
    ) -> Union[float, np.ndarray]:
        """
        Calculate relativistic kinetic energy: K = (γ - 1)mc²

        Args:
            mass: Rest mass (g)
            velocity: Velocity (cm/s)

        Returns:
            Kinetic energy (erg)
        """
        gamma = RelativisticPhysics.lorentz_factor(velocity)
        return (gamma - 1) * mass * C**2

    @staticmethod
    def relativistic_velocity_addition(
        v1: Union[float, np.ndarray],
        v2: Union[float, np.ndarray]
    ) -> Union[float, np.ndarray]:
        """
        Add relativistic velocities: (v₁ + v₂) / (1 + v₁v₂/c²)

        Args:
            v1: First velocity (cm/s)
            v2: Second velocity (cm/s)

        Returns:
            Combined velocity (cm/s)
        """
        return (v1 + v2) / (1 + v1 * v2 / C**2)

    @staticmethod
    def relativistic_doppler(
        rest_frequency: float,
        velocity: float,
        angle: float = 0.0
    ) -> float:
        """
        Calculate relativistic Doppler shift

        Args:
            rest_frequency: Rest frequency (Hz)
            velocity: Source velocity (cm/s)
            angle: Angle between velocity and line of sight (rad)

        Returns:
            Observed frequency (Hz)
        """
        gamma = RelativisticPhysics.lorentz_factor(velocity)
        beta = velocity / C
        cos_theta = np.cos(angle)

        # Relativistic Doppler formula
        factor = gamma * (1 - beta * cos_theta)
        return rest_frequency / factor

    # General Relativity Calculations

    @staticmethod
    def schwarzschild_radius(mass: float) -> float:
        """
        Calculate Schwarzschild radius: Rs = 2GM/c²

        Args:
            mass: Mass (g)

        Returns:
            Schwarzschild radius (cm)
        """
        return 2 * G * mass / C**2

    @staticmethod
    def gravitational_redshift(
        mass: float,
        radius: float,
        wavelength_emitted: float
    ) -> float:
        """
        Calculate gravitational redshift: z = 1/√(1 - Rs/r) - 1

        Args:
            mass: Gravitating mass (g)
            radius: Emission radius (cm)
            wavelength_emitted: Emitted wavelength (cm)

        Returns:
            Observed wavelength (cm)
        """
        rs = RelativisticPhysics.schwarzschild_radius(mass)
        redshift_factor = 1.0 / np.sqrt(1 - rs / radius) - 1
        return wavelength_emitted * (1 + redshift_factor)

    @staticmethod
    def light_deflection_angle(
        mass: float,
        impact_parameter: float
    ) -> float:
        """
        Calculate light deflection angle: α = 4GM/bc²

        Args:
            mass: Gravitating mass (g)
            impact_parameter: Impact parameter (cm)

        Returns:
            Deflection angle (rad)
        """
        return 4 * G * mass / (impact_parameter * C**2)

    @staticmethod
    def calculate_christoffel_symbols(
        metric: np.ndarray,
        inverse_metric: np.ndarray
    ) -> np.ndarray:
        """
        Calculate Christoffel symbols: Γ^μ_νλ = ½g^μσ(∂_νg_λσ + ∂_λg_νσ - ∂_σg_νλ)

        Args:
            metric: Metric tensor g_μν
            inverse_metric: Inverse metric tensor g^μν

        Returns:
            Christoffel symbols Γ^μ_νλ [upper, lower1, lower2]
        """
        dim = metric.shape[0]
        christoffel = np.zeros((dim, dim, dim))

        # Numerical derivative approximation
        h = 1e-6

        for mu in range(dim):
            for nu in range(dim):
                for lam in range(dim):
                    for sigma in range(dim):
                        # Γ^μ_νλ = ½g^μσ(∂_νg_λσ + ∂_λg_νσ - ∂_σg_νλ)

                        # Derivatives (numerical)
                        dg_lam_nu = (metric[lam, nu + 1] - metric[lam, nu]) / h if nu < dim - 1 else 0
                        dg_nu_lam = (metric[nu, lam + 1] - metric[nu, lam]) / h if lam < dim - 1 else 0
                        dg_nu_sigma = (metric[nu, sigma + 1] - metric[nu, sigma]) / h if sigma < dim - 1 else 0

                        christoffel[mu, nu, lam] += 0.5 * inverse_metric[mu, sigma] * (
                            dg_lam_nu + dg_nu_lam - dg_nu_sigma
                        )

        return christoffel

    # Black Hole Physics

    @staticmethod
    def kerr_horizon_radius(mass: float, spin_parameter: float) -> Tuple[float, float]:
        """
        Calculate Kerr black hole horizon radii

        Args:
            mass: Black hole mass (g)
            spin_parameter: Dimensionless spin a = Jc/GM² (|a| ≤ 1)

        Returns:
            (outer_horizon, inner_horizon) in cm
        """
        rs = RelativisticPhysics.schwarzschild_radius(mass)

        # Outer horizon: r+ = (1 + √(1 - a²)) * Rs/2
        # Inner horizon: r- = (1 - √(1 - a²)) * Rs/2
        sqrt_term = np.sqrt(1 - spin_parameter**2)

        r_outer = 0.5 * rs * (1 + sqrt_term)
        r_inner = 0.5 * rs * (1 - sqrt_term)

        return r_outer, r_inner

    @staticmethod
    def ergosphere_radius(
        mass: float,
        spin_parameter: float,
        latitude: float = 0.0
    ) -> float:
        """
        Calculate Kerr ergosphere boundary at given latitude

        Args:
            mass: Black hole mass (g)
            spin_parameter: Dimensionless spin a
            latitude: Latitude angle from equatorial plane (rad)

        Returns:
            Ergosphere radius (cm)
        """
        rs = RelativisticPhysics.schwarzschild_radius(mass)

        # Ergosphere: r = Rs + √(Rs² - a²cos²θ)
        cos_theta = np.cos(latitude)
        ergosphere = rs + np.sqrt(rs**2 - (rs * spin_parameter * cos_theta)**2)

        return ergosphere

    @staticmethod
    def hawking_temperature(mass: float) -> float:
        """
        Calculate Hawking temperature: T = ħc³/(8πGMk_B)

        Args:
            mass: Black hole mass (g)

        Returns:
            Hawking temperature (K)
        """
        hbar = H / (2 * np.pi)
        k_B = 1.381e-16  # Boltzmann constant (erg/K)

        return hbar * C**3 / (8 * np.pi * G * mass * k_B)

    @staticmethod
    def hawking_luminosity(mass: float) -> float:
        """
        Calculate Hawking radiation luminosity

        Args:
            mass: Black hole mass (g)

        Returns:
            Luminosity (erg/s)
        """
        temperature = RelativisticPhysics.hawking_temperature(mass)
        rs = RelativisticPhysics.schwarzschild_radius(mass)

        # Stefan-Boltzmann law for black hole
        sigma = 5.670e-5  # Stefan-Boltzmann constant (erg cm⁻² s⁻¹ K⁻⁴)
        area = 4 * np.pi * rs**2

        # L = σAT⁴ (with graybody factor ~0.01)
        graybody_factor = 0.01
        return graybody_factor * sigma * area * temperature**4

    @staticmethod
    def eddington_luminosity(mass: float) -> float:
        """
        Calculate Eddington luminosity: L_Edd = 4πGMm_pc/σ_T

        Args:
            mass: Mass (g)

        Returns:
            Eddington luminosity (erg/s)
        """
        m_p = 1.673e-24  # Proton mass (g)
        sigma_T = 6.652e-25  # Thomson cross section (cm²)

        return 4 * np.pi * G * mass * m_p * C / sigma_T

    @staticmethod
    def eddington_accretion_rate(luminosity: float, efficiency: float = 0.1) -> float:
        """
        Calculate accretion rate from luminosity: Ṁ = L/(ηMc²)

        Args:
            luminosity: Luminosity (erg/s)
            efficiency: Radiative efficiency η

        Returns:
            Accretion rate (g/s)
        """
        return luminosity / (efficiency * C**2)

    # Gravitational Waves

    @staticmethod
    def chirp_mass(mass1: float, mass2: float) -> float:
        """
        Calculate chirp mass: M_chirp = (m₁m₂)^(3/5)/(m₁+m₂)^(1/5)

        Args:
            mass1: Primary mass (g)
            mass2: Secondary mass (g)

        Returns:
            Chirp mass (g)
        """
        total_mass = mass1 + mass2
        reduced_mass = mass1 * mass2 / total_mass
        return (reduced_mass ** (3/5)) * (total_mass ** (2/5))

    @staticmethod
    def gravitational_wave_strain(
        chirp_mass: float,
        distance: float,
        frequency: float,
        inclination: float = 0.0
    ) -> float:
        """
        Calculate gravitational wave strain amplitude

        Args:
            chirp_mass: Chirp mass (g)
            distance: Luminosity distance (cm)
            frequency: GW frequency (Hz)
            inclination: Inclination angle (rad)

        Returns:
            Strain amplitude h
        """
        # h = (4/𝑟)(GMc/c³)^(5/3)(πf)^(2/3)

        # Convert to geometric units
        mc_geom = chirp_mass * G / C**3
        freq_pi = np.pi * frequency

        # Strain amplitude
        h = (4 / distance) * (mc_geom ** (5/3)) * (freq_pi ** (2/3))

        # Include inclination dependence
        h *= (1 + np.cos(inclination)**2) / 2

        return h

    @staticmethod
    def merger_time_from_frequency(
        chirp_mass: float,
        initial_frequency: float,
        final_frequency: Optional[float] = None
    ) -> float:
        """
        Calculate time to merger from initial frequency

        Args:
            chirp_mass: Chirp mass (g)
            initial_frequency: Initial GW frequency (Hz)
            final_frequency: Final frequency (Hz), defaults to ISCO

        Returns:
            Time to merger (s)
        """
        if final_frequency is None:
            # ISCO frequency for Schwarzschild
            final_frequency = C**3 / (6**(3/2) * np.pi * G * chirp_mass)

        # Time to coalescence: t = (5/256)(Mc/c³)^(-5/3)(πf)^(-8/3)
        mc_geom = chirp_mass * G / C**3

        t_initial = (5 / 256) * (mc_geom ** (-5/3)) * (np.pi * initial_frequency) ** (-8/3)
        t_final = (5 / 256) * (mc_geom ** (-5/3)) * (np.pi * final_frequency) ** (-8/3)

        return t_initial - t_final

    # Cosmology

    @staticmethod
    def hubble_parameter(
        redshift: float,
        H0: float,
        omega_m: float = 0.3,
        omega_lambda: float = 0.7
    ) -> float:
        """
        Calculate Hubble parameter at redshift: H(z) = H₀√(Ω_m(1+z)³ + Ω_Λ)

        Args:
            redshift: Redshift z
            H0: Hubble constant (km/s/Mpc)
            omega_m: Matter density parameter
            omega_lambda: Dark energy density parameter

        Returns:
            Hubble parameter at z (km/s/Mpc)
        """
        return H0 * np.sqrt(omega_m * (1 + redshift)**3 + omega_lambda)

    @staticmethod
    def proper_distance(
        redshift: float,
        H0: float,
        omega_m: float = 0.3,
        omega_lambda: float = 0.7
    ) -> float:
        """
        Calculate proper distance to redshift (numerical integration)

        Args:
            redshift: Redshift z
            H0: Hubble constant (km/s/Mpc)
            omega_m: Matter density parameter
            omega_lambda: Dark energy density parameter

        Returns:
            Proper distance (Mpc)
        """
        # Convert H0 to s⁻¹
        H0_s = H0 * 1e5 / (3.086e24)  # km/s/Mpc to s⁻¹
        c_mpc = C / (3.086e24)  # Speed of light in Mpc/s

        # Numerical integration
        nz = 100
        z_array = np.linspace(0, redshift, nz)
        dz = z_array[1] - z_array[0]

        integral = 0.0
        for z in z_array:
            Hz = RelativisticPhysics.hubble_parameter(z, H0 * 1e5 / 3.086e24, omega_m, omega_lambda)
            Hz_s = Hz * 1e5 / 3.086e24
            integral += c_mpc / Hz_s

        return integral * dz

    @staticmethod
    def luminosity_distance(
        redshift: float,
        H0: float,
        omega_m: float = 0.3,
        omega_lambda: float = 0.7
    ) -> float:
        """
        Calculate luminosity distance: d_L = (1+z)d_P

        Args:
            redshift: Redshift z
            H0: Hubble constant (km/s/Mpc)
            omega_m: Matter density parameter
            omega_lambda: Dark energy density parameter

        Returns:
            Luminosity distance (Mpc)
        """
        d_proper = RelativisticPhysics.proper_distance(redshift, H0, omega_m, omega_lambda)
        return (1 + redshift) * d_proper

    @staticmethod
    def angular_diameter_distance(
        redshift: float,
        H0: float,
        omega_m: float = 0.3,
        omega_lambda: float = 0.7
    ) -> float:
        """
        Calculate angular diameter distance: d_A = d_L/(1+z)²

        Args:
            redshift: Redshift z
            H0: Hubble constant (km/s/Mpc)
            omega_m: Matter density parameter
            omega_lambda: Dark energy density parameter

        Returns:
            Angular diameter distance (Mpc)
        """
        d_luminosity = RelativisticPhysics.luminosity_distance(redshift, H0, omega_m, omega_lambda)
        return d_luminosity / (1 + redshift)**2


# Export public interface
__all__ = [
    'RelativisticPhysics',
    'ComplexityLevel',
    'LearningStage'
]
