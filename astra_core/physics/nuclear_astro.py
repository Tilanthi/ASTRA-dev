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
Nuclear astrophysics curriculum stage for STAN-XI-ASTRO

Implements:
- Nuclear binding energy and stability
- Nuclear reactions (fusion, fission, capture)
- Nucleosynthesis pathways
- Stellar evolution and nucleosynthesis
- R-process and S-process
- Supernova nucleosynthesis
- Big Bang nucleosynthesis
- Nuclear equation of state

This provides the nuclear physics foundation for understanding
stellar energy generation, stellar evolution, and chemical enrichment.

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
AMU = 1.6605e-24  # Atomic mass unit (g)
ME = 9.109e-28  # Electron mass (g)
MP = 1.6726e-24  # Proton mass (g)
MN = 1.6749e-24  # Neutron mass (g)
MH = 1.6735e-24  # Hydrogen atom mass (g)
C = 2.998e10  # Speed of light (cm/s)
EV_TO_ERG = 1.602e-12  # eV to erg conversion
Q_VALUE = 1.492e-3  # MeV per amu


class NuclearAstrophysics:
    """
    Nuclear astrophysics module for stellar physics

    Provides nuclear physics foundation for understanding
    stellar energy generation, nucleosynthesis, and chemical evolution.
    """

    # Stage definitions
    STAGE_NUCLEAR_BASICS = "nuclear_basics"
    STAGE_STELLAR_NUCLEOSYNTHESIS = "stellar_nucleosynthesis"
    STAGE_EXPLOSIVE_NUCLEOSYNTHESIS = "explosive_nucleosynthesis"
    STAGE_BIG_BANG = "big_bang_nucleosynthesis"
    STAGE_EOS = "nuclear_equation_of_state"

    @staticmethod
    def get_learning_stages() -> List[LearningStage]:
        """Return all nuclear astrophysics learning stages"""
        return [
            # Stage 1: Nuclear Basics
            LearningStage(
                name=NuclearAstrophysics.STAGE_NUCLEAR_BASICS,
                complexity=ComplexityLevel.INTERMEDIATE,
                prerequisites=["basic_mechanics", "quantum_basics"],
                concepts=[
                    # Nuclear structure
                    "atomic_nucleus",
                    "proton_neutron",
                    "strong_force",
                    "binding_energy",
                    "mass_defect",
                    "nuclear_stability",
                    "magic_numbers",
                    "liquid_drop_model",
                    "shell_model",
                    "valley_of_stability",
                    "isotopes",
                    "radioactive_decay",
                    "half_life",
                    "alpha_decay",
                    "beta_decay",
                    "gamma_decay",
                    "nuclear_reactions",
                    "cross_section"
                ],
                skills=[
                    # Computation skills
                    "calculate_binding_energy",
                    "compute_mass_defect",
                    "predict_decay_stability",
                    "calculate_q_value",
                    "estimate_half_life",
                    "compute_reaction_rates",
                    "calculate_cross_sections"
                ],
                problems=[
                    {
                        "type": "binding_energy",
                        "description": "Calculate binding energy of 56Fe",
                        "parameters": {"mass_number": 56, "atomic_number": 26}
                    },
                    {
                        "type": "q_value",
                        "description": "Compute Q-value for 4He fusion",
                        "parameters": {}
                    },
                    {
                        "type": "decay_chain",
                        "description": "Calculate decay chain of 238U",
                        "parameters": {}
                    }
                ],
                mastery_threshold=0.80
            ),

            # Stage 2: Stellar Nucleosynthesis
            LearningStage(
                name=NuclearAstrophysics.STAGE_STELLAR_NUCLEOSYNTHESIS,
                complexity=ComplexityLevel.ADVANCED,
                prerequisites=[NuclearAstrophysics.STAGE_NUCLEAR_BASICS, "stellar_evolution"],
                concepts=[
                    # Hydrogen burning
                    "proton_proton_chain",
                    "cno_cycle",
                    "hydrogen_burning",
                    "helium_burning",
                    "triple_alpha_process",
                    "alpha_process",
                    "carbon_burning",
                    "neon_burning",
                    "oxygen_burning",
                    "silicon_burning",
                    "iron_peak",
                    "stellar_energy_generation",
                    "main_sequence",
                    "red_giant_branch",
                    "helium_flash",
                    # Advanced burning
                    "s_process",
                    "slow_neutron_capture",
                    "neutron_poisson",
                    "branching_point",
                    "seed_nuclei"
                ],
                skills=[
                    # Analysis skills
                    "calculate_pp_chain_energy",
                    "analyze_cno_cycle_efficiency",
                    "compute_triple_alpha_rate",
                    "analyze_burning_stages",
                    "calculate_energy_generation_rate",
                    "predict_nucleosynthesis_yield",
                    "analyze_s_process_pathways"
                ],
                problems=[
                    {
                        "type": "pp_chain",
                        "description": "Calculate energy yield of pp-chain",
                        "parameters": {"temperature": 1.5e7, "density": 100}
                    },
                    {
                        "type": "triple_alpha",
                        "description": "Compute triple-alpha reaction rate",
                        "parameters": {"temperature": 1e8}
                    },
                    {
                        "type": "s_process",
                        "description": "Analyze s-process flow to Ba",
                        "parameters": {"metallicity": 0.02}
                    }
                ],
                mastery_threshold=0.75
            ),

            # Stage 3: Explosive Nucleosynthesis
            LearningStage(
                name=NuclearAstrophysics.STAGE_EXPLOSIVE_NUCLEOSYNTHESIS,
                complexity=ComplexityLevel.EXPERT,
                prerequisites=[
                    NuclearAstrophysics.STAGE_STELLAR_NUCLEOSYNTHESIS,
                    "supernovae"
                ],
                concepts=[
                    # Supernova nucleosynthesis
                    "type_ia_supernova",
                    "type_ii_supernova",
                    "core_collapse",
                    "explosive_nucleosynthesis",
                    "r_process",
                    "rapid_neutron_capture",
                    "neutron_star_merger",
                    "kilonova",
                    "gamma_ray_bursts",
                    "isotopic_ratios",
                    "nucleosynthesis_yields",
                    "chemical_enrichment",
                    "supernova_remnants",
                    "mixing_fallback",
                    "explosive_burning"
                ],
                skills=[
                    # Computation and analysis
                    "calculate_r_process_path",
                    "predict_sn_yields",
                    "analyze_explosive_burning",
                    "compute_kilonova_nucleosynthesis",
                    "model_radioactive_decay",
                    "analyze_isotopic_anomalies",
                    "calculate_chemical_evolution"
                ],
                problems=[
                    {
                        "type": "r_process",
                        "description": "Calculate r-process path to uranium",
                        "parameters": {"neutron_density": 1e24, "timescale": 1}
                    },
                    {
                        "type": "sn_ia",
                        "description": "Model Type Ia supernova nucleosynthesis",
                        "parameters": {"mass": 1.38, "metallicity": 0.02}
                    },
                    {
                        "type": "kilonova",
                        "description": "Compute kilonova ejecta composition",
                        "parameters": {"mass_ratio": 1.4, "eccentricity": 0}
                    }
                ],
                mastery_threshold=0.70
            ),

            # Stage 4: Big Bang Nucleosynthesis
            LearningStage(
                name=NuclearAstrophysics.STAGE_BIG_BANG,
                complexity=ComplexityLevel.EXPERT,
                prerequisites=[NuclearAstrophysics.STAGE_NUCLEAR_BASICS, "cosmology"],
                concepts=[
                    # BBN
                    "big_bang_nucleosynthesis",
                    "primordial_nucleosynthesis",
                    "light_element_abundances",
                    "deuterium",
                    "helium_3",
                    "helium_4",
                    "lithium_7",
                    "baryon_to_photon_ratio",
                    "freeze_out_temperature",
                    "nuclear_statistical_equilibrium",
                    "neutron_proton_ratio",
                    "weak_interaction",
                    "cosmological_parameters",
                    "primordial_metallicity",
                    "spitzer_problem"
                ],
                skills=[
                    # Computation skills
                    "compute_bbn_abundances",
                    "calculate_freeze_out",
                    "predict_light_element_yields",
                    "constrain_cosmology",
                    "analyze_deuterium_evolution"
                ],
                problems=[
                    {
                        "type": "bbn_yield",
                        "description": "Calculate He-4 abundance from BBN",
                        "parameters": {"baryon_density": 0.02, "expansion_rate": 0.7}
                    },
                    {
                        "type": "deuterium",
                        "description": "Predict primordial D/H ratio",
                        "parameters": {"eta": 6e-10}
                    },
                    {
                        "type": "lithium",
                        "description": "Solve lithium problem in BBN",
                        "parameters": {}
                    }
                ],
                mastery_threshold=0.70
            ),

            # Stage 5: Nuclear Equation of State
            LearningStage(
                name=NuclearAstrophysics.STAGE_EOS,
                complexity=ComplexityLevel.EXPERT,
                prerequisites=[NuclearAstrophysics.STAGE_NUCLEAR_BASICS, "degenerate_matter"],
                concepts=[
                    # EOS for compact objects
                    "nuclear_equation_of_state",
                    "nuclear_matter",
                    "neutron_drip",
                    "neutron_stars",
                    "nuclear_pasta",
                    "quark_gluon_plasma",
                    "hyperons",
                    "delta_resonances",
                    "stiffness_parameter",
                    "symmetry_energy",
                    "nuclear_parity",
                    "binding_energy_model",
                    "relativistic_mean_field",
                    "tolman_oppenheimer_volkoff"
                ],
                skills=[
                    # Computation skills
                    "calculate_eos_pressure",
                    "compute_neutron_star_radius",
                    "analyze_tov_equation",
                    "model_nuclear_pasta_phases",
                    "calculate_maximum_mass",
                    "predict_stellar_radius"
                ],
                problems=[
                    {
                        "type": "eos",
                        "description": "Calculate pressure vs density for nuclear matter",
                        "parameters": {"density_range": [1e14, 1e15]}
                    },
                    {
                        "type": "tov",
                        "description": "Solve TOV equation for neutron star",
                        "parameters": {"central_density": 1e15}
                    },
                    {
                        "type": "maximum_mass",
                        "description": "Compute maximum mass for given EOS",
                        "parameters": {"stiffness": 2}
                    }
                ],
                mastery_threshold=0.70
            )
        ]

    # Nuclear Basics

    @staticmethod
    def binding_energy(mass_number: int, atomic_number: int) -> float:
        """
        Calculate nuclear binding energy using semi-empirical mass formula

        Args:
            mass_number: Mass number A
            atomic_number: Atomic number Z

        Returns:
            Binding energy (MeV)
        """
        A = mass_number
        Z = atomic_number
        N = A - Z  # Number of neutrons

        # Volume term: a_v A
        a_v = 15.75
        volume_term = a_v * A

        # Surface term: -a_s A^(2/3)
        a_s = 17.8
        surface_term = -a_s * A**(2/3)

        # Coulomb term: -a_c Z(Z-1)/A^(1/3)
        a_c = 0.711
        coulomb_term = -a_c * Z * (Z - 1) / A**(1/3)

        # Asymmetry term: -a_a (A-2Z)²/A
        a_a = 23.7
        asymmetry_term = -a_a * (A - 2*Z)**2 / A

        # Pairing term: +δ / √A
        # δ = +a_p for even-even, -a_p for odd-odd, 0 for odd-A
        a_p = 11.18
        if Z % 2 == 0 and N % 2 == 0:
            pairing = a_p / np.sqrt(A)
        elif Z % 2 == 1 and N % 2 == 1:
            pairing = -a_p / np.sqrt(A)
        else:
            pairing = 0

        # Total binding energy
        BE = volume_term + surface_term + coulomb_term + asymmetry_term + pairing

        return BE

    @staticmethod
    def mass_defect(mass_number: int, atomic_number: int) -> float:
        """
        Calculate mass defect: Δm = Z*m_p + N*m_n - M_nucleus

        Args:
            mass_number: Mass number A
            atomic_number: Atomic number Z

        Returns:
            Mass defect (amu)
        """
        Z = atomic_number
        N = mass_number - Z

        # Mass of constituent nucleons
        mass_nucleons = Z * MP + N * MN

        # Mass of nucleus (from binding energy)
        BE = NuclearAstrophysics.binding_energy(mass_number, atomic_number)
        mass_nucleus = mass_nucleons - BE / 931.5  # MeV to amu

        # Mass defect
        delta_m = mass_nucleons - mass_nucleus

        return delta_m

    @staticmethod
    def nuclear_reaction_rate(
        temperature: float,
        reduced_mass: float,
        coulomb_barrier: float,
        screening_factor: float = 1.0
    ) -> float:
        """
        Calculate nuclear reaction rate using Gamow peak approximation

        Args:
            temperature: Temperature (K)
            reduced_mass: Reduced mass of reactants (g)
            coulomb_barrier: Coulomb barrier (erg)
            screening_factor: Electron screening enhancement

        Returns:
            Reaction rate per pair (cm³/s)
        """
        kT = KB * temperature  # Thermal energy

        # Gamow energy E₀
        # E₀ = (π² Z₁² Z₂² e⁴ m_red / 2ħ²)^(1/3)
        # Simplified approximation

        # Tunneling probability
        # P ≈ exp(-2π² Z₁ Z₂ e²/ħv)
        # Using Gamow factor

        # Nuclear cross section approximation
        # S(E) ≈ S₀ (slowly varying)
        # σ(E) ≈ S(E)/E × exp(-2πη)

        # This is a simplified placeholder
        # Full calculation requires solving tunneling through Coulomb barrier

        rate = screening_factor * np.exp(-coulomb_barrier / kT) / (reduced_mass * temperature)**(2/3)

        return rate

    # Stellar Nucleosynthesis

    @staticmethod
    def pp_chain_energy(temperature: float, density: float, X: float = 0.7) -> float:
        """
        Calculate energy generation rate from pp-chain

        Args:
            temperature: Temperature (K)
            density: Mass density (g/cm³)
            X: Hydrogen mass fraction

        Returns:
            Energy generation rate (erg/g/s)
        """
        T6 = temperature / 1e6  # Temperature in millions of K
        rho = density

        # pp-chain energy generation: ε_pp ≈ 2.4×10⁶ ρ X² T₆^(-2/3) exp(-33.8/T₆^(1/3))
        # This is approximate

        # Pre-exponential factor
        pre_factor = 2.4e6 * rho * X**2

        # Temperature dependence
        t_factor = T6**(-2/3)
        exp_factor = np.exp(-33.8 * T6**(-1/3))

        epsilon = pre_factor * t_factor * exp_factor

        return epsilon

    @staticmethod
    def cno_cycle_energy(temperature: float, density: float, X: float = 0.7, Z: float = 0.02) -> float:
        """
        Calculate energy generation rate from CNO cycle

        Args:
            temperature: Temperature (K)
            density: Mass density (g/cm³)
            X: Hydrogen mass fraction
            Z: Metallicity (C, N, O mass fraction)

        Returns:
            Energy generation rate (erg/g/s)
        """
        T6 = temperature / 1e6
        rho = density

        # CNO cycle energy: ε_CNO ≈ 8×10²⁷ ρ X Z T₆^(-2/3) exp(-152.3/T₆^(1/3))
        # Higher temperature sensitivity than pp-chain

        pre_factor = 8e27 * rho * X * Z
        t_factor = T6**(-2/3)
        exp_factor = np.exp(-152.3 * T6**(-1/3))

        epsilon = pre_factor * t_factor * exp_factor

        return epsilon

    @staticmethod
    def triple_alpha_rate(temperature: float, density: float, Y: float = 0.3) -> float:
        """
        Calculate triple-alpha reaction rate: 3 4He → 12C

        Args:
            temperature: Temperature (K)
            density: Mass density (g/cm³)
            Y: Helium mass fraction

        Returns:
            Energy generation rate (erg/g/s)
        """
        T8 = temperature / 1e8
        rho = density

        # Triple-alpha rate: r_3α ≈ ρ² Y³ T₈⁴⁰
        # Strong temperature dependence!

        rate = 1e8 * rho**2 * Y**3 * T8**40  # Very approximate

        # Energy release: ~7.275 MeV per reaction
        Q = 7.275  # MeV

        epsilon = rate * Q * 1.6e-6  # MeV to erg

        return epsilon

    # Explosive Nucleosynthesis

    @staticmethod
    def r_process_path(
        neutron_density: float,
        timescale: float,
        seed_nuclei: str = "fe"
    ) -> Dict[str, float]:
        """
        Model r-process nucleosynthesis path

        Args:
            neutron_density: Neutron number density (cm⁻³)
            timescale: Duration of neutron flux (s)
            seed_nuclei: Starting nucleus

        Returns:
            Dictionary with final abundances of key isotopes
        """
        # Simplified r-process model
        # Full calculation requires network of thousands of nuclei

        # Rapid neutron capture on seed nuclei
        # β-decay back to stability
        # Produces elements up to Th and U

        abundances = {
            'Au': 1e-10,  # Gold
            'Pt': 1e-9,   # Platinum
            'U': 1e-11,   # Uranium
            'Th': 1e-11,  # Thorium
            'Eu': 1e-9    # Europium
        }

        # Scaling with neutron density and timescale
        scale = (neutron_density / 1e20) * (timescale / 1.0)

        for isotope in abundances:
            abundances[isotope] *= scale

        return abundances

    @staticmethod
    def supernova_yields(mass: float, metallicity: float, sn_type: str = "II") -> Dict[str, float]:
        """
        Calculate nucleosynthesis yields from supernova

        Args:
            mass: Progenitor mass (M⊙)
            metallicity: Initial metallicity Z/Z_⊙
            sn_type: Type of supernova ("II" or "Ia")

        Returns:
            Dictionary with yields of key elements (M⊙)
        """
        if sn_type == "II":
            # Core-collapse supernova yields (simplified)
            yields = {
                'O': 1.5,    # Oxygen
                'Mg': 0.1,   # Magnesium
                'Si': 0.07,  # Silicon
                'Fe': 0.1,   # Iron (depends on mass)
                'Ni': 0.005, # Nickel
                'alpha': 2.0 # Total alpha elements
            }

            # Mass dependence
            if mass > 20:
                yields['Fe'] = 0.2  # More Fe for more massive
            else:
                yields['Fe'] = 0.05

        else:  # Type Ia
            # Thermonuclear explosion of white dwarf
            yields = {
                'Ni': 0.6,   # Mostly Ni-56
                'Fe': 0.5,   # Decays from Ni
                'Si': 0.15,
                'S': 0.05,
                'Ca': 0.05,
                'alpha': 0.2  # Some alpha elements
            }

        # Metallicity scaling
        if metallicity < 1.0:
            for element in yields:
                if element != 'Fe' and sn_type == "II":
                    yields[element] *= metallicity

        return yields

    # Big Bang Nucleosynthesis

    @staticmethod
    def bbn_abundances(eta: float, expansion_rate: float = 0.7) -> Dict[str, float]:
        """
        Calculate primordial element abundances from Big Bang nucleosynthesis

        Args:
            eta: Baryon-to-photon ratio η = n_b/n_γ (typically ~6×10⁻¹⁰)
            expansion_rate: Hubble parameter constraint

        Returns:
            Dictionary with mass fractions of light elements
        """
        # Simplified BBN predictions
        # Full calculation requires solving nuclear reaction network

        # Helium-4 abundance (by mass)
        # Y_p ≈ 0.2485 + 0.0016 (η₁₀ - 6)
        eta_10 = eta / 1e-10
        Y_p = 0.2485 + 0.0016 * (eta_10 - 6)

        # Deuterium abundance (D/H by number)
        # D/H ≈ 2.6×10⁻⁵ (η₁₀/6)^(-1.6)
        D_H = 2.6e-5 * (eta_10 / 6)**(-1.6)

        # Helium-3 abundance
        # He-3/H ≈ 1.1×10⁻⁵ (η₁₀/6)^(-1.5)
        He3_H = 1.1e-5 * (eta_10 / 6)**(-1.5)

        # Lithium-7 abundance
        # Li/H ≈ 4.7×10⁻¹⁰ (η₁₀/6)^(2.3)
        Li_H = 4.7e-10 * (eta_10 / 6)**(2.3)

        abundances = {
            'He4_mass_fraction': Y_p,
            'D_H_ratio': D_H,
            'He3_H_ratio': He3_H,
            'Li_H_ratio': Li_H
        }

        return abundances

    # Nuclear Equation of State

    @staticmethod
    def nuclear_matter_eos(density: float, K: float = 230) -> float:
        """
        Calculate pressure from nuclear matter equation of state

        Args:
            density: Mass density (g/cm³)
            K: Incompressibility (MeV)

        Returns:
            Pressure (dyn/cm²)
        """
        # Nuclear saturation density
        rho_0 = 2.8e14  # g/cm³

        # Simple polynomial EOS: P = K (ρ - ρ_0)
        # More realistic: Skyrme or relativistic mean field models

        if density < rho_0:
            pressure = 0  # No pressure below saturation
        else:
            # Simplified: stiff nuclear matter
            delta_rho = density - rho_0
            pressure = K * delta_rho / (rho_0 * 1.6e-6)  # Convert MeV to erg

        return pressure

    @staticmethod
    def tov_equation(
        central_density: float,
        equation_of_state: str = "polytropic"
    ) -> Dict[str, float]:
        """
        Solve Tolman-Oppenheimer-Volkoff equation for neutron star

        Simplified solution for given central density

        Args:
            central_density: Central density (g/cm³)
            equation_of_state: EOS to use ("polytropic", "APR", etc.)

        Returns:
            Dictionary with mass, radius, central pressure
        """
        # Simplified Lane-Emden solution for n=3 polytrope
        # More realistic requires numerical integration of TOV equations

        if equation_of_state == "polytropic":
            # Polytropic EOS: P = K ρ^(1 + 1/n)
            # For n=3, radius R ∝ K^0.5, Mass M ∝ K^1.5

            # Rough scaling relations
            rho_c = central_density
            rho_0 = 2.8e14  # Nuclear saturation density

            if rho_c < rho_0:
                # Sub-nuclear densities
                mass = 1.4 * (rho_c / rho_0)**0.5  # Solar masses
                radius = 15 * (rho_c / rho_0)**(-0.5)  # km
            else:
                # Above saturation
                mass = 1.4 * (rho_c / rho_0)**0.5
                radius = 12 * (rho_c / rho_0)**(-0.33)

        else:
            # Approximate values for typical EOS
            mass = 1.4  # Solar masses
            radius = 12  # km

        # Central pressure from hydrostatic equilibrium
        # P_c ≈ (4π/3) G ρ_c² R²
        P_c = (4 * np.pi / 3) * G * central_density**2 * (radius * 1e5)**2

        return {
            'mass': mass,  # Solar masses
            'radius': radius,  # km
            'central_pressure': P_c  # dyn/cm²
        }


# Export public interface
__all__ = [
    'NuclearAstrophysics',
    'ComplexityLevel',
    'LearningStage'
]
