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
Quantum mechanics basics for astrophysics

Implements:
- Wave-particle duality and uncertainty principle
- Atomic structure and energy levels
- Quantum statistics (Fermi-Dirac, Bose-Einstein)
- Degenerate matter and compact objects
- Quantum tunneling

This provides the quantum physics foundation needed for understanding
atomic spectra, stellar interiors, white dwarfs, neutron stars, and
high-energy astrophysical phenomena.

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
    from .curriculum_learning import LearningStage, ComplexityLevel
except ImportError:
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


# Physical constants
H = 6.626e-27  # Planck constant (erg s)
HBAR = H / (2 * np.pi)  # Reduced Planck constant
C = 2.998e10  # Speed of light (cm/s)
ME = 9.109e-28  # Electron mass (g)
MP = 1.673e-24  # Proton mass (g)
KB = 1.381e-16  # Boltzmann constant (erg/K)
RY = 13.6  # Rydberg constant (eV)
E_CHARGE = 4.803e-10  # Elementary charge (esu)


class QuantumMechanics:
    """
    Quantum mechanics module for astrophysics

    Provides quantum physics foundation for astronomical applications.
    """

    # Stage definitions
    STAGE_QUANTUM_BASICS = "quantum_basics"
    STAGE_ATOMIC_PHYSICS = "atomic_physics"
    STAGE_QUANTUM_STATISTICS = "quantum_statistics"
    STAGE_DEGENERATE_MATTER = "degenerate_matter"
    STAGE_QUANTUM_PROCESSES = "quantum_processes"

    @staticmethod
    def get_learning_stages() -> List[LearningStage]:
        """Return all quantum mechanics learning stages"""
        return [
            # Stage 1: Quantum Basics
            LearningStage(
                name=QuantumMechanics.STAGE_QUANTUM_BASICS,
                complexity=ComplexityLevel.INTERMEDIATE,
                prerequisites=["basic_mechanics"],
                concepts=[
                    # Core concepts
                    "wave_particle_duality",
                    "uncertainty_principle",
                    "wave_function",
                    "probability_amplitude",
                    "quantum_superposition",
                    "quantum_entanglement",
                    "schrodinger_equation",
                    "quantum_states",
                    "quantum_numbers",
                    "quantization",
                    "zero_point_energy",
                    "quantum_harmonic_oscillator",
                    "quantum_tunneling",
                    "barrier_penetration"
                ],
                skills=[
                    # Computational skills
                    "compute_de_broglie_wavelength",
                    "apply_uncertainty_principle",
                    "normalize_wave_function",
                    "calculate_probability_density",
                    "solve_1d_schrodinger",
                    "compute_tunneling_probability",
                    "calculate_energy_levels",
                    "analyze_quantum_transitions"
                ],
                problems=[
                    {
                        "type": "de_broglie",
                        "description": "Calculate de Broglie wavelength of electron",
                        "parameters": {"velocity": 1e8}
                    },
                    {
                        "type": "uncertainty",
                        "description": "Apply uncertainty principle to confined particle",
                        "parameters": {"confinement_length": 1e-8}
                    },
                    {
                        "type": "tunneling",
                        "description": "Calculate alpha decay tunneling probability",
                        "parameters": {"barrier_width": 1e-12, "energy": 5e6}
                    }
                ],
                mastery_threshold=0.80
            ),

            # Stage 2: Atomic Physics
            LearningStage(
                name=QuantumMechanics.STAGE_ATOMIC_PHYSICS,
                complexity=ComplexityLevel.ADVANCED,
                prerequisites=[QuantumMechanics.STAGE_QUANTUM_BASICS, "electromagnetism"],
                concepts=[
                    # Atomic structure
                    "hydrogen_atom",
                    "bohr_model",
                    "quantum_numbers_n",
                    "quantum_numbers_l",
                    "quantum_numbers_m",
                    "spin_quantum_number",
                    "energy_levels",
                    "atomic_orbitals",
                    "electron_configuration",
                    "periodic_table",
                    "fine_structure",
                    "hyperfine_structure",
                    "lamb_shift",
                    "zeeman_effect",
                    "stark_effect",
                    "atomic_spectra",
                    "selection_rules",
                    "forbidden_transitions",
                    "isotopic_shift"
                ],
                skills=[
                    # Analysis skills
                    "compute_energy_levels",
                    "calculate_transition_frequencies",
                    "analyze_spectral_lines",
                    "determine_electron_configuration",
                    "apply_selection_rules",
                    "compute_fine_structure_splitting",
                    "analyze_zeeman_patterns",
                    "calculate_oscillator_strengths",
                    "interpret_atomic_spectra"
                ],
                problems=[
                    {
                        "type": "hydrogen_energy",
                        "description": "Calculate hydrogen energy level transition",
                        "parameters": {"n_initial": 3, "n_final": 2}
                    },
                    {
                        "type": "spectral_line",
                        "description": "Compute wavelength of H-alpha line",
                        "parameters": {}
                    },
                    {
                        "type": "fine_structure",
                        "description": "Calculate fine structure splitting of sodium D line",
                        "parameters": {}
                    }
                ],
                mastery_threshold=0.75
            ),

            # Stage 3: Quantum Statistics
            LearningStage(
                name=QuantumMechanics.STAGE_QUANTUM_STATISTICS,
                complexity=ComplexityLevel.ADVANCED,
                prerequisites=[QuantumMechanics.STAGE_QUANTUM_BASICS, "thermodynamics"],
                concepts=[
                    # Statistics
                    "fermi_dirac_statistics",
                    "bose_einstein_statistics",
                    "maxwell_boltzmann_statistics",
                    "fermions",
                    "bosons",
                    "pauli_exclusion_principle",
                    "fermi_energy",
                    "fermi_temperature",
                    "chemical_potential",
                    "density_of_states",
                    "fermi_surface",
                    "bose_einstein_condensation",
                    "critical_temperature",
                    "degeneracy_pressure",
                    "electron_degeneracy",
                    "neutron_degeneracy"
                ],
                skills=[
                    # Computation skills
                    "compute_fermi_energy",
                    "calculate_fermi_dirac_distribution",
                    "calculate_bose_einstein_distribution",
                    "compute_degeneracy_pressure",
                    "analyze_degenerate_objects",
                    "calculate_critical_temperature",
                    "compute_electron_specific_heat",
                    "analyze_white_dwarf_structure"
                ],
                problems=[
                    {
                        "type": "fermi_energy",
                        "description": "Calculate Fermi energy in white dwarf",
                        "parameters": {"density": 1e6}
                    },
                    {
                        "type": "degeneracy_pressure",
                        "description": "Compute electron degeneracy pressure",
                        "parameters": {"density": 1e5, "temperature": 1e7}
                    },
                    {
                        "type": "bec_temperature",
                        "description": "Calculate BEC critical temperature",
                        "parameters": {"density": 1e13, "mass": 23}  # Na atoms
                    }
                ],
                mastery_threshold=0.75
            ),

            # Stage 4: Degenerate Matter
            LearningStage(
                name=QuantumMechanics.STAGE_DEGENERATE_MATTER,
                complexity=ComplexityLevel.EXPERT,
                prerequisites=[
                    QuantumMechanics.STAGE_QUANTUM_STATISTICS,
                    "gravitational_physics"
                ],
                concepts=[
                    # Compact objects
                    "white_dwarfs",
                    "chandrasekhar_limit",
                    "electron_degeneracy_pressure",
                    "relativistic_degeneracy",
                    "neutron_stars",
                    "neutron_degeneracy_pressure",
                    "nuclear_equation_of_state",
                    "tolman_oppenheimer_volkoff",
                    "neutron_star_limit",
                    "pulsars",
                    "magnetars",
                    "compact_object_cooling",
                    "neutrino_cooling",
                    "photon_cooling",
                    "degenerate_cores",
                    "brown_dwarfs",
                    "gas_giant_interiors"
                ],
                skills=[
                    # Analysis skills
                    "compute_chandrasekhar_limit",
                    "analyze_white_dwarf_structure",
                    "calculate_electron_degeneracy_pressure",
                    "compute_neutron_star_radius",
                    "analyze_tov_equation",
                    "calculate_pulsar_period",
                    "analyze_magnetar_fields",
                    "compute_cooling_timescales",
                    "analyze_degenerate_core_structure"
                ],
                problems=[
                    {
                        "type": "chandrasekhar",
                        "description": "Calculate Chandrasekhar mass limit",
                        "parameters": {"mu_e": 2}
                    },
                    {
                        "type": "white_dwarf_radius",
                        "description": "Compute white dwarf radius from mass",
                        "parameters": {"mass": 0.6}
                    },
                    {
                        "type": "neutron_star",
                        "description": "Calculate neutron star structure",
                        "parameters": {"mass": 1.4}
                    }
                ],
                mastery_threshold=0.70
            ),

            # Stage 5: Quantum Processes in Astrophysics
            LearningStage(
                name=QuantumMechanics.STAGE_QUANTUM_PROCESSES,
                complexity=ComplexityLevel.EXPERT,
                prerequisites=[QuantumMechanics.STAGE_ATOMIC_PHYSICS],
                concepts=[
                    # Astrophysical quantum processes
                    "photoionization",
                    "recombination",
                    "collisional_excitation",
                    "radiative_cascade",
                    "stimulated_emission",
                    "maser_action",
                    "laser_action",
                    "raman_scattering",
                    "compton_scattering",
                    "inverse_compton",
                    "pair_production",
                    "annihilation",
                    "synchrotron_radiation",
                    "bremsstrahlung",
                    "free_free_emission",
                    "bound_free_emission",
                    "bound_bound_emission",
                    "charge_exchange",
                    "molecular_formation",
                    "dust_formation"
                ],
                skills=[
                    # Computation skills
                    "compute_photoionization_rate",
                    "calculate_recombination_coefficient",
                    "analyze_collisional_rates",
                    "compute_excitation_rates",
                    "calculate_compton_scattering",
                    "analyze_synchrotron_emission",
                    "compute_bremsstrahlung_spectrum",
                    "analyze_maser_mechanisms",
                    "calculate_ionization_equilibrium"
                ],
                problems=[
                    {
                        "type": "saha_equation",
                        "description": "Calculate ionization fraction using Saha equation",
                        "parameters": {"temperature": 10000, "density": 1e-10}
                    },
                    {
                        "type": "compton_scattering",
                        "description": "Compute inverse Compton scattering",
                        "parameters": {"photon_energy": 1e-9, "electron_energy": 1e6}
                    },
                    {
                        "type": "synchrotron",
                        "description": "Calculate synchrotron spectrum from electrons",
                        "parameters": {"magnetic_field": 1e-4, "electron_energy": 1e9}
                    }
                ],
                mastery_threshold=0.70
            )
        ]

    # Wave-Particle Duality

    @staticmethod
    def de_broglie_wavelength(
        momentum: Union[float, np.ndarray]
    ) -> Union[float, np.ndarray]:
        """
        Calculate de Broglie wavelength: λ = h/p

        Args:
            momentum: Momentum (g cm/s)

        Returns:
            Wavelength (cm)
        """
        return H / momentum

    @staticmethod
    def de_broglie_wavelength_from_velocity(
        mass: float,
        velocity: float
    ) -> float:
        """
        Calculate de Broglie wavelength from velocity

        Args:
            mass: Particle mass (g)
            velocity: Velocity (cm/s)

        Returns:
            Wavelength (cm)
        """
        momentum = mass * velocity
        return QuantumMechanics.de_broglie_wavelength(momentum)

    @staticmethod
    def heisenberg_uncertainty(
        delta_position: Optional[float] = None,
        delta_momentum: Optional[float] = None
    ) -> float:
        """
        Apply Heisenberg uncertainty principle: Δx·Δp ≥ ħ/2

        Args:
            delta_position: Position uncertainty (cm)
            delta_momentum: Momentum uncertainty (g cm/s)

        Returns:
            Minimum uncertainty for the unspecified quantity
        """
        if delta_position is not None and delta_momentum is not None:
            # Check if product satisfies uncertainty principle
            product = delta_position * delta_momentum
            return product >= HBAR / 2
        elif delta_position is not None:
            return HBAR / (2 * delta_position)
        elif delta_momentum is not None:
            return HBAR / (2 * delta_momentum)
        else:
            raise ValueError("Must specify at least one of delta_position or delta_momentum")

    # Atomic Physics

    @staticmethod
    def hydrogen_energy_level(n: int, Z: int = 1) -> float:
        """
        Calculate hydrogen energy level: E_n = -Z²Ry/n²

        Args:
            n: Principal quantum number
            Z: Atomic number

        Returns:
            Energy (eV)
        """
        return -Z**2 * RY / n**2

    @staticmethod
    def hydrogen_transition_wavelength(n_upper: int, n_lower: int, Z: int = 1) -> float:
        """
        Calculate wavelength of hydrogen transition

        Args:
            n_upper: Upper energy level
            n_lower: Lower energy level
            Z: Atomic number

        Returns:
            Wavelength (cm)
        """
        # Energy difference in eV
        delta_E = QuantumMechanics.hydrogen_energy_level(n_upper, Z) - \
                  QuantumMechanics.hydrogen_energy_level(n_lower, Z)

        # Convert to wavelength
        # E = hc/λ → λ = hc/E
        energy_erg = abs(delta_E) * 1.602e-12  # eV to erg
        wavelength = H * C / energy_erg

        return wavelength

    @staticmethod
    def bohr_radius(n: int = 1, Z: int = 1) -> float:
        """
        Calculate Bohr radius: a₀ = n²ħ²/(Zme²)

        Args:
            n: Principal quantum number
            Z: Atomic number

        Returns:
            Bohr radius (cm)
        """
        # a₀ = ħ²/(m_e e²) in CGS
        a0 = HBAR**2 / (ME * E_CHARGE**2)

        return n**2 * a0 / Z

    @staticmethod
    def ionization_energy(atomic_number: int, ionization_stage: int) -> float:
        """
        Estimate ionization energy using hydrogenic approximation

        Args:
            atomic_number: Atomic number Z
            ionization_stage: Ionization stage (1 for neutral, 2 for +1, etc.)

        Returns:
            Ionization energy (eV)
        """
        # Hydrogenic approximation: E = Z²Ry/n²
        # where n is the principal quantum number of the outermost electron
        effective_Z = atomic_number - ionization_stage + 1
        effective_n = ionization_stage  # Approximation

        return effective_Z**2 * RY / effective_n**2

    # Quantum Statistics

    @staticmethod
    def fermi_energy(density: float, mass: float, g: int = 2) -> float:
        """
        Calculate Fermi energy for degenerate fermions

        Args:
            density: Number density (cm⁻³)
            mass: Particle mass (g)
            g: Degeneracy factor (spin states)

        Returns:
            Fermi energy (erg)
        """
        # E_F = (ħ²/2m)(3π²n)^(2/3)
        n = density
        return (HBAR**2 / (2 * mass)) * (3 * np.pi**2 * n / g)**(2/3)

    @staticmethod
    def fermi_temperature(fermi_energy: float) -> float:
        """
        Calculate Fermi temperature: T_F = E_F/k_B

        Args:
            fermi_energy: Fermi energy (erg)

        Returns:
            Fermi temperature (K)
        """
        return fermi_energy / KB

    @staticmethod
    def fermi_dirac_distribution(
        energy: Union[float, np.ndarray],
        chemical_potential: float,
        temperature: float
    ) -> Union[float, np.ndarray]:
        """
        Calculate Fermi-Dirac distribution: f(E) = 1/(exp((E-μ)/kT) + 1)

        Args:
            energy: Energy level (erg)
            chemical_potential: Chemical potential μ (erg)
            temperature: Temperature (K)

        Returns:
            Occupation probability
        """
        if temperature == 0:
            # Zero temperature: step function
            return np.where(energy <= chemical_potential, 1.0, 0.0)
        else:
            return 1.0 / (np.exp((energy - chemical_potential) / (KB * temperature)) + 1)

    @staticmethod
    def bose_einstein_distribution(
        energy: Union[float, np.ndarray],
        chemical_potential: float,
        temperature: float
    ) -> Union[float, np.ndarray]:
        """
        Calculate Bose-Einstein distribution: f(E) = 1/(exp((E-μ)/kT) - 1)

        Args:
            energy: Energy level (erg)
            chemical_potential: Chemical potential μ (erg)
            temperature: Temperature (K)

        Returns:
            Occupation number
        """
        if temperature == 0:
            return np.inf  # Diverges at T=0 for bosons
        else:
            exponent = (energy - chemical_potential) / (KB * temperature)
            # Prevent overflow
            exponent = np.clip(exponent, -700, 700)
            return 1.0 / (np.exp(exponent) - 1)

    @staticmethod
    def bose_einstein_condensation_temperature(
        density: float,
        mass: float,
        g: int = 1
    ) -> float:
        """
        Calculate BEC critical temperature

        Args:
            density: Particle density (cm⁻³)
            mass: Particle mass (g)
            g: Degeneracy factor

        Returns:
            Critical temperature (K)
        """
        # T_c = (2πħ²/mk_B)(n/(ζ(3/2)g))^(2/3)
        n = density
        zeta_3_2 = 2.612  # Riemann zeta function ζ(3/2)

        return (2 * np.pi * HBAR**2 / (mass * KB)) * (n / (zeta_3_2 * g))**(2/3)

    # Degenerate Matter

    @staticmethod
    def chandrasekhar_limit(mu_e: float = 2) -> float:
        """
        Calculate Chandrasekhar mass limit

        Args:
            mu_e: Mean molecular weight per electron

        Returns:
            Mass limit (solar masses)
        """
        # M_Ch = (ħc/G)^(3/2) (1/μ_e m_H)² (ω₃⁰/2π)²
        # where ω₃⁰ ≈ 2.018 for n=3 polytrope

        # Numerical value: M_Ch ≈ 5.76/μ_e² solar masses (for non-rotating)
        return 5.76 / mu_e**2

    @staticmethod
    def electron_degeneracy_pressure(density: float, relativity: str = "nonrel") -> float:
        """
        Calculate electron degeneracy pressure

        Args:
            density: Electron number density (cm⁻³)
            relativity: "nonrel" or "rel" for relativistic treatment

        Returns:
            Pressure (dyn/cm²)
        """
        # Non-relativistic: P = (ħ²/5m_e)(3π²)^(2/3) n^(5/3)
        # Relativistic: P = (ħc/4)(3π²)^(1/3) n^(4/3)

        n = density

        if relativity == "nonrel":
            pressure = (HBAR**2 / (5 * ME)) * (3 * np.pi**2)**(2/3) * n**(5/3)
        else:  # relativistic
            pressure = (HBAR * C / 4) * (3 * np.pi**2)**(1/3) * n**(4/3)

        return pressure

    @staticmethod
    def white_dwarf_radius(mass: float, mu_e: float = 2) -> float:
        """
        Calculate white dwarf radius from mass (mass-radius relation)

        Args:
            mass: Mass (solar masses)
            mu_e: Mean molecular weight per electron

        Returns:
            Radius (km)
        """
        # R ∝ M^(-1/3) for non-relativistic degeneracy
        # R ≈ 0.01 R_sun (M/M_Ch)^(-1/3) (μ_e/2)^(-5/3)

        mass_ch = QuantumMechanics.chandrasekhar_limit(mu_e)
        radius_sun_km = 6.957e5

        radius = 0.01 * radius_sun_km * (mass / mass_ch)**(-1/3) * (mu_e / 2)**(-5/3)

        return radius

    @staticmethod
    def neutron_star_radius(mass: float, equation_of_state: str = "polytrope") -> float:
        """
        Calculate neutron star radius (approximate)

        Args:
            mass: Mass (solar masses)
            equation_of_state: EOS to use ("polytrope", "apr", etc.)

        Returns:
            Radius (km)
        """
        # Approximate mass-radius relation
        # For n=1 polytrope (soft EOS): R ∝ M^(-1/3)
        # For stiffer EOS: R ≈ 10-15 km relatively constant

        if equation_of_state == "polytrope":
            # Simple power law
            radius = 12.0 * (mass / 1.4)**(-1/3)  # km
        else:
            # Stiffer EOS: more constant radius
            radius = 12.0  # km (typical value)

        return radius

    @staticmethod
    def neutron_degeneracy_pressure(density: float) -> float:
        """
        Calculate neutron degeneracy pressure

        Args:
            density: Neutron number density (cm⁻³)

        Returns:
            Pressure (dyn/cm²)
        """
        # Similar to electrons but with neutron mass
        # P = (ħ²/5m_n)(3π²n)^(2/3) for non-relativistic

        n = density
        m_n = MP  # Neutron mass approximately equals proton mass

        pressure = (HBAR**2 / (5 * m_n)) * (3 * np.pi**2)**(2/3) * n**(5/3)

        return pressure

    # Quantum Processes

    @staticmethod
    def tunneling_probability(
        energy: float,
        barrier_height: float,
        barrier_width: float,
        mass: float = ME
    ) -> float:
        """
        Calculate quantum tunneling probability (WKB approximation)

        Args:
            energy: Particle energy (erg)
            barrier_height: Barrier height (erg)
            barrier_width: Barrier width (cm)
            mass: Particle mass (g)

        Returns:
            Tunneling probability
        """
        if energy >= barrier_height:
            return 1.0

        # WKB approximation: T ≈ exp(-2κL)
        # where κ = √(2m(V-E))/ħ

        kappa = np.sqrt(2 * mass * (barrier_height - energy)) / HBAR
        transmission = np.exp(-2 * kappa * barrier_width)

        return transmission

    @staticmethod
    def photoionization_cross_section(
        photon_energy: float,
        ionization_energy: float,
        atomic_number: int = 1
    ) -> float:
        """
        Calculate photoionization cross section (approximate)

        Args:
            photon_energy: Photon energy (erg)
            ionization_energy: Ionization energy (erg)
            atomic_number: Atomic number Z

        Returns:
            Cross section (cm²)
        """
        if photon_energy < ionization_energy:
            return 0.0

        # Near-threshold approximation
        # σ ≈ σ₀ (E_th/E)^(3.5)

        # Typical cross section at threshold
        sigma_0 = 6.3e-18 * atomic_number**(-2)  # cm²

        excess_energy = photon_energy / ionization_energy
        cross_section = sigma_0 * (excess_energy)**(-3.5)

        return cross_section

    @staticmethod
    def compton_scattering_energy(
        incident_energy: float,
        scattering_angle: float
    ) -> float:
        """
        Calculate scattered photon energy in Compton scattering

        Args:
            incident_energy: Incident photon energy (erg)
            scattering_angle: Scattering angle (rad)

        Returns:
            Scattered photon energy (erg)
        """
        # Compton formula: E' = E / (1 + (E/m_ec²)(1 - cosθ))

        m_ec2 = ME * C**2  # Electron rest energy

        scattered_energy = incident_energy / (
            1 + (incident_energy / m_ec2) * (1 - np.cos(scattering_angle))
        )

        return scattered_energy

    @staticmethod
    def saha_equation(
        temperature: float,
        electron_density: float,
        ionization_energy: float,
        partition_functions: Tuple[float, float] = (1, 1)
    ) -> float:
        """
        Calculate ionization fraction using Saha equation

        Args:
            temperature: Temperature (K)
            electron_density: Electron density (cm⁻³)
            ionization_energy: Ionization energy (erg)
            partition_functions: (Z_I, Z_II) partition functions

        Returns:
            Ionization fraction n_II/(n_I + n_II)
        """
        # n_II*n_e/n_I = (2πm_ekT/h²)^(3/2) (2Z_II/Z_I) exp(-χ/kT)

        thermal_de_broglie = (2 * np.pi * ME * KB * temperature / H**2)**(1.5)

        saha_const = thermal_de_broglie * (2 * partition_functions[1] / partition_functions[0]) * \
                     np.exp(-ionization_energy / (KB * temperature))

        # Solve for ionization fraction
        # Let x = n_II/n_total, then n_e = x*n_total
        # x²/(1-x) = saha_const/n_total

        n_total = electron_density  # Simplified
        x_squared = saha_const / n_total

        if x_squared < 1:
            x = np.sqrt(x_squared)
        else:
            x = 1.0  # Fully ionized

        return x


# Export public interface
__all__ = [
    'QuantumMechanics',
    'ComplexityLevel',
    'LearningStage'
]
