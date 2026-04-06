"""
Interstellar Chemistry Module for Astrophysical Simulations

This module implements chemical reaction networks for interstellar medium,
including:
- Gas-phase chemistry (ions, molecules)
- Grain surface chemistry
- Photodissociation regions (PDRs)
- Dark cloud chemistry
- Shock chemistry
- Deuterium fractionation

Key capabilities:
- Chemical evolution with SPH coupling
- Multi-wavelength line emission prediction
- Isotope fractionation
- Dust grain physics

Version: 3.0.0
Date: 2026-03-16
"""

import numpy as np
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
import json


class ChemicalEnvironment(Enum):
    """Types of interstellar environments."""
    DIFFUSE_ISM = "diffuse_ism"
    TRANSLUCENT_CLOUD = "translucent_cloud"
    DARK_CLOUD = "dark_cloud"
    HOT_CORE = "hot_core"
    PDR = "photodissociation_region"
    SHOCK = "shock_region"
    HII_REGION = "hii_region"


class SpeciesType(Enum):
    """Types of chemical species."""
    ATOM = "atom"
    ION = "ion"
    MOLECULE = "molecule"
    RADICAL = "radical"
    GRAIN_SPECIES = "grain_species"
    ISOTOPE = "isotope"


@dataclass
class ChemicalSpecies:
    """A chemical species in the reaction network."""
    name: str
    species_type: SpeciesType
    mass: float  # Atomic mass units
    charge: int = 0
    formation_energy: float = 0.0  # Formation energy (K)
    dissociation_energy: float = 0.0  # Dissociation energy (K)
    dipole_moment: float = 0.0  # Debye
    isotopologue: Optional[str] = None  # If isotope, parent species name
    abundance: float = 1e-10  # Relative to H2


@dataclass
class ChemicalReaction:
    """A chemical reaction with rate coefficients."""
    reactants: List[str]
    products: List[str]
    reaction_type: str  # gas_phase, grain_surface, photodissociation, etc.
    alpha: float = 1.0  # Rate coefficient parameter
    beta: float = 0.0
    gamma: float = 0.0
    temperature_range: Tuple[float, float] = (10.0, 10000.0)

    def rate_coefficient(self, temperature: float, density: float = 1.0) -> float:
        """Calculate rate coefficient using Arrhenius or modified Arrhenius form."""
        if not (self.temperature_range[0] <= temperature <= self.temperature_range[1]):
            return 0.0

        if self.reaction_type in ['gas_phase', 'ion-neutral']:
            # Modified Arrhenius: k = alpha * (T/300)^beta * exp(-gamma/T)
            rate = self.alpha * (temperature / 300.0)**self.beta * np.exp(-self.gamma / temperature)
        elif self.reaction_type == 'grain_surface':
            # Grain surface rates depend on dust temperature and density
            rate = self.alpha * density * np.exp(-self.gamma / temperature)
        elif self.reaction_type == 'photodissociation':
            # Rate proportional to radiation field
            rate = self.alpha * np.exp(-self.gamma * density)  # Shielding
        elif self.reaction_type == 'cosmic_ray':
            # Cosmic ray ionization rate
            rate = self.alpha
        else:
            rate = self.alpha

        return max(rate, 1e-50)


@dataclass
class ChemicalState:
    """State of chemical abundances at a given time."""
    time: float
    abundances: Dict[str, float]  # species -> abundance
    temperature: float
    density: float
    visual_extinction: float = 10.0
    radiation_field: float = 1.0  # In units of Habing field
    cosmic_ray_ionization_rate: float = 1.3e-17


class InterstellarChemistryNetwork:
    """
    Chemical reaction network for interstellar medium.

    Includes major species and reactions for:
    - Carbon chemistry (CO, C+, C)
    - Oxygen chemistry (H2O, OH, O)
    - Nitrogen chemistry (N2, NH3, HCN)
    - Sulfur chemistry
    - Deuterium fractionation
    """

    def __init__(self, environment: ChemicalEnvironment = ChemicalEnvironment.DARK_CLOUD):
        self.environment = environment
        self.species: Dict[str, ChemicalSpecies] = {}
        self.reactions: List[ChemicalReaction] = []
        self.initial_abundances: Dict[str, float] = {}

        self._initialize_species()
        self._initialize_reactions()
        self._set_initial_abundances()

    def _initialize_species(self) -> None:
        """Initialize chemical species database."""
        # Atoms and ions
        self._add_species("H", SpeciesType.ATOM, 1.0, charge=0, formation_energy=0.0)
        self._add_species("H+", SpeciesType.ION, 1.0, charge=1)
        self._add_species("H2", SpeciesType.MOLECULE, 2.0, dissociation_energy=52000.0)
        self._add_species("H2+", SpeciesType.ION, 2.0, charge=1)
        self._add_species("H3+", SpeciesType.ION, 3.0, charge=1)
        self._add_species("He", SpeciesType.ATOM, 4.0)
        self._add_species("He+", SpeciesType.ION, 4.0, charge=1)

        # Carbon species
        self._add_species("C", SpeciesType.ATOM, 12.0)
        self._add_species("C+", SpeciesType.ION, 12.0, charge=1)
        self._add_species("CO", SpeciesType.MOLECULE, 28.0, dipole_moment=0.112,
                         dissociation_energy=124000.0)
        self._add_species("CH", SpeciesType.MOLECULE, 13.0, dissociation_energy=34700.0)
        self._add_species("CH+", SpeciesType.ION, 13.0, charge=1)
        self._add_species("CH2", SpeciesType.MOLECULE, 14.0)
        self._add_species("CH3+", SpeciesType.ION, 15.0, charge=1)
        self._add_species("HCO+", SpeciesType.ION, 29.0, charge=1, dipole_moment=3.9)

        # Oxygen species
        self._add_species("O", SpeciesType.ATOM, 16.0)
        self._add_species("O+", SpeciesType.ION, 16.0, charge=1)
        self._add_species("OH", SpeciesType.MOLECULE, 17.0, dissociation_energy=46200.0)
        self._add_species("OH+", SpeciesType.ION, 17.0, charge=1)
        self._add_species("H2O", SpeciesType.MOLECULE, 18.0, dipole_moment=1.85,
                         dissociation_energy=53300.0)
        self._add_species("H2O+", SpeciesType.ION, 18.0, charge=1)
        self._add_species("H3O+", SpeciesType.ION, 19.0, charge=1)

        # Nitrogen species
        self._add_species("N", SpeciesType.ATOM, 14.0)
        self._add_species("N+", SpeciesType.ION, 14.0, charge=1)
        self._add_species("N2", SpeciesType.MOLECULE, 28.0, dissociation_energy=79800.0)
        self._add_species("N2H+", SpeciesType.ION, 29.0, charge=1, dipole_moment=3.4)
        self._add_species("NH", SpeciesType.MOLECULE, 15.0)
        self._add_species("NH2", SpeciesType.MOLECULE, 16.0)
        self._add_species("NH3", SpeciesType.MOLECULE, 17.0, dipole_moment=1.47)

        # Sulfur species
        self._add_species("S", SpeciesType.ATOM, 32.0)
        self._add_species("S+", SpeciesType.ION, 32.0, charge=1)
        self._add_species("SO", SpeciesType.MOLECULE, 48.0)
        self._add_species("SO2", SpeciesType.MOLECULE, 64.0)
        self._add_species("CS", SpeciesType.MOLECULE, 44.0)

        # Deuterated species
        self._add_species("D", SpeciesType.ATOM, 2.0, isotopologue="H")
        self._add_species("HD", SpeciesType.MOLECULE, 3.0, isotopologue="H2")
        self._add_species("H2D+", SpeciesType.ION, 4.0, charge=1, isotopologue="H3+")
        self._add_species("DCO+", SpeciesType.ION, 29.0, charge=1, isotopologue="HCO+")
        self._add_species("N2D+", SpeciesType.ION, 30.0, charge=1, isotopologue="N2H+")

        # Complex organic molecules (COMs)
        self._add_species("H2CO", SpeciesType.MOLECULE, 30.0, dipole_moment=2.33)
        self._add_species("CH3OH", SpeciesType.MOLECULE, 32.0, dipole_moment=1.70)
        self._add_species("HCN", SpeciesType.MOLECULE, 27.0, dipole_moment=2.98)
        self._add_species("HNC", SpeciesType.MOLECULE, 27.0, dipole_moment=3.05)
        self._add_species("HC3N", SpeciesType.MOLECULE, 51.0, dipole_moment=3.72)

        # Ions and electrons
        self._add_species("e-", SpeciesType.ION, 0.0005, charge=-1)

    def _add_species(self, name: str, species_type: SpeciesType, mass: float,
                    **kwargs) -> None:
        """Add a species to the network."""
        self.species[name] = ChemicalSpecies(name=name, species_type=species_type,
                                            mass=mass, **kwargs)

    def _initialize_reactions(self) -> None:
        """Initialize chemical reaction network."""
        # H2 formation on grains
        self.reactions.append(ChemicalReaction(
            reactants=["H", "H", "grain"],
            products=["H2", "grain"],
            reaction_type="grain_surface",
            alpha=3.0e-17, beta=0.0, gamma=0.0
        ))

        # H2 ionization
        self.reactions.append(ChemicalReaction(
            reactants=["H2", "cosmic_ray"],
            products=["H2+", "e-"],
            reaction_type="cosmic_ray",
            alpha=1.3e-17
        ))

        # H2+ + H2 -> H3+ + H
        self.reactions.append(ChemicalReaction(
            reactants=["H2+", "H2"],
            products=["H3+", "H"],
            reaction_type="gas_phase",
            alpha=2.0e-9
        ))

        # H3+ destruction channels
        self.reactions.append(ChemicalReaction(
            reactants=["H3+", "CO"],
            products=["HCO+", "H2"],
            reaction_type="ion-neutral",
            alpha=1.7e-9
        ))

        self.reactions.append(ChemicalReaction(
            reactants=["H3+", "O"],
            products=["OH+", "H2"],
            reaction_type="ion-neutral",
            alpha=8.0e-10
        ))

        # CO formation
        self.reactions.append(ChemicalReaction(
            reactants=["C+", "OH"],
            products=["CO+", "H"],
            reaction_type="ion-neutral",
            alpha=3.0e-10
        ))

        self.reactions.append(ChemicalReaction(
            reactants=["CO+", "H2"],
            products=["HCO+", "H"],
            reaction_type="ion-neutral",
            alpha=2.0e-9
        ))

        # HCO+ recombination
        self.reactions.append(ChemicalReaction(
            reactants=["HCO+", "e-"],
            products=["CO", "H"],
            reaction_type="gas_phase",
            alpha=2.4e-7, beta=-0.69, gamma=0.0
        ))

        # OH chemistry
        self.reactions.append(ChemicalReaction(
            reactants=["OH+", "H2"],
            products=["H2O+", "H"],
            reaction_type="ion-neutral",
            alpha=1.0e-9
        ))

        self.reactions.append(ChemicalReaction(
            reactants=["H2O+", "H2"],
            products=["H3O+", "H"],
            reaction_type="ion-neutral",
            alpha=1.0e-9
        ))

        self.reactions.append(ChemicalReaction(
            reactants=["H3O+", "e-"],
            products=["H2O", "H"],
            reaction_type="gas_phase",
            alpha=4.0e-7, beta=-0.5, gamma=0.0
        ))

        # NH3 formation
        self.reactions.append(ChemicalReaction(
            reactants=["N+", "H2"],
            products=["NH2+", "H"],
            reaction_type="ion-neutral",
            alpha=1.0e-9
        ))

        # Deuterium fractionation
        self.reactions.append(ChemicalReaction(
            reactants=["H3+", "HD"],
            products=["H2D+", "H2"],
            reaction_type="ion-neutral",
            alpha=1.0e-10, beta=0.0, gamma=232.0
        ))

        self.reactions.append(ChemicalReaction(
            reactants=["H2D+", "CO"],
            products=["DCO+", "H2"],
            reaction_type="ion-neutral",
            alpha=2.0e-9
        ))

        self.reactions.append(ChemicalReaction(
            reactants=["N2H+", "HD"],
            products=["N2D+", "H2"],
            reaction_type="ion-neutral",
            alpha=1.0e-10, beta=0.0, gamma=232.0
        ))

        # Photodissociation reactions
        self.reactions.append(ChemicalReaction(
            reactants=["CO", "photon"],
            products=["C", "O"],
            reaction_type="photodissociation",
            alpha=1.0e-10, gamma=2.0  # Visual extinction dependence
        ))

        self.reactions.append(ChemicalReaction(
            reactants=["H2O", "photon"],
            products=["OH", "H"],
            reaction_type="photodissociation",
            alpha=1.0e-10, gamma=1.8
        ))

        # Sulfur chemistry
        self.reactions.append(ChemicalReaction(
            reactants=["S+", "H2"],
            products=["SH+", "H"],
            reaction_type="ion-neutral",
            alpha=1.0e-10
        ))

        self.reactions.append(ChemicalReaction(
            reactants=["SH+", "H2"],
            products=["H2S+", "H"],
            reaction_type="ion-neutral",
            alpha=1.0e-9
        ))

    def _set_initial_abundances(self) -> None:
        """Set initial elemental abundances."""
        # Low metal abundances for diffuse ISM
        self.initial_abundances = {
            "H": 1.0,  # Reference
            "He": 0.1,
            "C": 1.4e-4,
            "N": 7.5e-5,
            "O": 3.2e-4,
            "S": 1.5e-5,
            "e-": 7.0e-4,  # Ionization fraction
            "H2": 0.5,  # Molecular hydrogen fraction
            "D": 1.5e-5,  # Deuterium/Hydrogen ratio
        }

    def evolve_chemistry(
        self,
        initial_state: ChemicalState,
        time_end: float,
        dt: float = 1000.0
    ) -> List[ChemicalState]:
        """
        Evolve chemical abundances over time.

        Uses simple Euler integration (can be upgraded to CVODE).
        """
        state = initial_state
        history = [state]

        abundances = state.abundances.copy()
        time = state.time

        while time < time_end:
            # Calculate derivatives
            derivatives = self._calculate_derivatives(abundances, state)

            # Update abundances
            for species in abundances:
                if species in derivatives:
                    abundances[species] += derivatives[species] * dt
                    abundances[species] = max(abundances[species], 1e-30)

            # Ensure charge conservation
            self._enforce_charge_conservation(abundances)

            # Update time
            time += dt

            # Create new state
            new_state = ChemicalState(
                time=time,
                abundances=abundances.copy(),
                temperature=state.temperature,
                density=state.density,
                visual_extinction=state.visual_extinction,
                radiation_field=state.radiation_field
            )

            history.append(new_state)
            state = new_state

        return history

    def _calculate_derivatives(
        self,
        abundances: Dict[str, float],
        state: ChemicalState
    ) -> Dict[str, float]:
        """Calculate time derivatives of abundances."""
        derivatives = {species: 0.0 for species in abundances}

        T = state.temperature
        n = state.density

        for reaction in self.reactions:
            # Calculate rate coefficient
            rate = reaction.rate_coefficient(T, n)

            # Get reactant abundances
            reactant_concs = []
            valid_reaction = True

            for reactant in reaction.reactants:
                if reactant == "grain":
                    # Dust-to-gas ratio
                    reactant_concs.append(0.01)
                elif reactant == "photon":
                    # Radiation field strength with extinction
                    chi = state.radiation_field
                    Av = state.visual_extinction
                    reactant_concs.append(chi * np.exp(-Av / reaction.gamma))
                elif reactant == "cosmic_ray":
                    reactant_concs.append(1.0)
                elif reactant in abundances:
                    reactant_concs.append(abundances[reactant])
                else:
                    valid_reaction = False
                    break

            if not valid_reaction or len(reactant_concs) == 0:
                continue

            # Reaction rate
            reaction_rate = rate
            for conc in reactant_concs:
                reaction_rate *= conc

            # Update derivatives
            for reactant in reaction.reactants:
                if reactant in abundances:
                    derivatives[reactant] -= reaction_rate

            for product in reaction.products:
                if product in abundances:
                    derivatives[product] += reaction_rate
                elif product not in ["grain", "photon", "cosmic_ray"]:
                    # Add new species
                    derivatives[product] = reaction_rate

        return derivatives

    def _enforce_charge_conservation(self, abundances: Dict[str, float]) -> None:
        """Ensure charge neutrality by adjusting electron abundance."""
        total_positive = sum(
            abundances.get(s.name, 0.0) * s.charge
            for s in self.species.values() if s.charge > 0
        )

        total_negative = sum(
            abundances.get(s.name, 0.0) * abs(s.charge)
            for s in self.species.values() if s.charge < 0
        )

        # Adjust electrons to maintain neutrality
        abundances["e-"] = max(total_positive - (total_negative - abundances.get("e-", 0.0)), 1e-30)

    def get_abundance_evolution(
        self,
        species: List[str],
        time_points: np.ndarray
    ) -> Dict[str, np.ndarray]:
        """Get abundance evolution for specific species."""
        # Run evolution and extract species
        initial = ChemicalState(
            time=0.0,
            abundances=self.initial_abundances.copy(),
            temperature=10.0,
            density=1e4,
            visual_extinction=10.0
        )

        history = self.evolve_chemistry(initial, time_points[-1])

        evolution = {}
        for s in species:
            evolution[s] = np.array([
                state.abundances.get(s, 1e-30) for state in history
            ])

        return evolution


class DeuteriumFractionationModel:
    """
    Model for deuterium fractionation in cold clouds.

    Deuterium enhancement occurs via:
    - H3+ + HD -> H2D+ + H2 (exothermic at low T)
    - Subsequent reactions produce DCO+, N2D+, etc.
    """

    def __init__(self):
        self.network = InterstellarChemistryNetwork()

    def calculate_fractionation_ratio(
        self,
        temperature: float,
        density: float,
        co_depletion: float = 1.0
    ) -> Dict[str, float]:
        """
        Calculate deuterium fractionation ratios.

        Args:
            temperature: Gas temperature (K)
            density: Gas density (cm^-3)
            co_depletion: CO depletion factor

        Returns:
            Dictionary of fractionation ratios (D/H)
        """
        # Fractionation depends on temperature
        # At low T, the reaction H3+ + HD -> H2D+ + H2 is exothermic

        k_forward = 1.0e-10 * np.exp(-232.0 / temperature)  # Endothermic reverse
        k_reverse = 1.0e-10  # Forward is barrierless

        # Equilibrium ratio
        HD_abundance = 1.5e-5  # D/H ratio
        H2_abundance = 0.5

        # H2D+/H3+ ratio
        h2d_fraction = (k_reverse * HD_abundance) / (
            k_forward * H2_abundance + k_reverse * HD_abundance
        )

        # DCO+/HCO+ depends on CO abundance
        dco_hco_ratio = h2d_fraction / co_depletion

        # N2D+/N2H+ similar
        n2d_n2h_ratio = h2d_fraction / co_depletion

        return {
            "H2D+/H3+": h2d_fraction,
            "DCO+/HCO+": dco_hco_ratio,
            "N2D+/N2H+": n2d_n2h_ratio,
            "DCO+/HCO+_obs": dco_hco_ratio * 0.3,  # Observational correction
            "N2D+/N2H+_obs": n2d_n2h_ratio * 0.3
        }


class MolecularEmissionCalculator:
    """
    Calculate molecular line emission for multi-wavelength observations.

    Includes:
    - Rotational transitions (mm, sub-mm)
    - Hyperfine structure (radio)
    - Line radiative transfer
    """

    def __init__(self):
        # Molecular constants for common species
        self.molecular_data = {
            "CO": {
                "rotational_constant": 57.6,  # GHz
                "dipole_moment": 0.112,  # Debye
                "mass": 28.0,  # amu
            },
            "HCO+": {
                "rotational_constant": 44.6,
                "dipole_moment": 3.9,
                "mass": 29.0,
            },
            "N2H+": {
                "rotational_constant": 47.0,
                "dipole_moment": 3.4,
                "mass": 29.0,
                "hyperfine": True,  # Has hyperfine structure
                "hyperfine_spacing": 0.5,  # MHz
            },
            "NH3": {
                "inversion_frequency": 23.7,  # GHz
                "dipole_moment": 1.47,
                "mass": 17.0,
            },
            "H2O": {
                "rotational_constant": 27.9,
                "dipole_moment": 1.85,
                "mass": 18.0,
            },
        }

    def calculate_line_intensity(
        self,
        species: str,
        transition: Tuple[int, int],
        temperature: float,
        column_density: float,
        line_width: float = 1.0
    ) -> Dict[str, float]:
        """
        Calculate line intensity for a molecular transition.

        Args:
            species: Molecule name
            transition: (J_upper, J_lower)
            temperature: Excitation temperature (K)
            column_density: Column density (cm^-2)
            line_width: Line width (km/s)

        Returns:
            Dictionary with line properties
        """
        if species not in self.molecular_data:
            return {"intensity": 0.0, "frequency": 0.0}

        data = self.molecular_data[species]
        B = data["rotational_constant"]
        mu = data["dipole_molecule"] if "dipole_molecule" in data else data.get("dipole_moment", 1.0)

        J_u, J_l = transition

        # Transition frequency
        frequency = B * J_u * (J_u + 1) - B * J_l * (J_l + 1)

        # Einstein A coefficient (approximate)
        A_ul = 1.0e-11 * (mu**2) * (frequency**3) * J_u / (J_l + 1)

        # Statistical weights
        g_u = 2 * J_u + 1
        g_l = 2 * J_l + 1

        # Energy levels
        E_u = B * J_u * (J_u + 1)  # In temperature units
        E_l = B * J_l * (J_l + 1)

        # Boltzmann distribution
        partition_function = temperature / B
        N_u = column_density * (g_u / partition_function) * np.exp(-E_u / temperature)

        # Optical depth (approximate)
        delta_nu = frequency * line_width / 3e5  # Doppler width
        phi = 1.0 / (np.sqrt(np.pi) * delta_nu)  # Line profile

        # Line intensity (Rayleigh-Jeans limit)
        h = 6.626e-34
        k = 1.381e-23

        T_R = (h * frequency / k) * (N_u * A_ul) / (delta_nu * frequency)  # Brightness temp

        return {
            "intensity": T_R,
            "frequency": frequency,
            "wavelength": 3e8 / frequency * 100,  # cm
            "upper_energy": E_u,
            "einstein_A": A_ul,
            "optical_depth": min(T_R / temperature, 10.0)
        }

    def calculate_spectra(
        self,
        abundances: Dict[str, float],
        temperature: float,
        density: float,
        velocity_width: float,
        size: float = 1.0
    ) -> Dict[str, np.ndarray]:
        """
        Calculate full spectra for multiple molecules.

        Returns spectra in brightness temperature units.
        """
        spectra = {}

        # Frequency grid (100-400 GHz for ALMA Band 6)
        frequencies = np.linspace(100e9, 400e9, 10000)
        spectra_grid = np.zeros_like(frequencies)

        for species, abundance in abundances.items():
            if species not in self.molecular_data:
                continue

            # Column density
            column_density = abundance * density * size * 3.086e18  # cm^-2

            # Calculate multiple transitions
            data = self.molecular_data[species]
            B = data["rotational_constant"]

            for J in range(1, 11):  # Transitions up to J=10
                line_data = self.calculate_line_intensity(
                    species, (J, J-1), temperature, column_density, velocity_width
                )

                # Add Gaussian line profile
                line_freq = line_data["frequency"]
                delta_nu = line_freq * velocity_width / 3e5

                line_profile = line_data["intensity"] * np.exp(
                    -((frequencies - line_freq) / delta_nu)**2
                )

                spectra_grid += line_profile

        spectra[species] = spectra_grid
        spectra["frequencies"] = frequencies

        return spectra


class GrainSurfaceChemistry:
    """
    Model chemistry on dust grain surfaces.

    Includes:
    - H2 formation
    - Ice mantle buildup
    - Grain surface reactions
    - Desorption processes
    """

    def __init__(self):
        self.grain_radius = 0.1  # microns
        self.grain_density = 3.0  # g/cm^3
        self.site_density = 1e15  # sites/cm^2

    def calculate_h2_formation_rate(
        self,
        temperature: float,
        density: float,
        hydrogen_abundance: float
    ) -> float:
        """
        Calculate H2 formation rate on grains.

        Rate = n_H * n_grain * v_H * sticking_probability * efficiency
        """
        # Thermal velocity
        m_H = 1.67e-27  # kg
        k_B = 1.381e-23  # J/K

        v_thermal = np.sqrt(8 * k_B * temperature / (np.pi * m_H))

        # Dust-to-gas ratio
        dust_to_gas = 0.01

        # Grain number density
        grain_mass = 4/3 * np.pi * (self.grain_radius * 1e-6)**3 * self.grain_density * 1e3
        n_grain = density * dust_to_gas / grain_mass

        # Sticking probability
        if temperature < 10:
            sticking = 1.0
        elif temperature < 20:
            sticking = 0.5
        else:
            sticking = 0.1

        # H2 formation efficiency
        efficiency = 0.3  # Typically 0.1-1.0

        # Formation rate
        R_H2 = hydrogen_abundance * density * n_grain * v_thermal * sticking * efficiency

        return R_H2

    def calculate_ice_mantle_growth(
        self,
        gas_phase_abundances: Dict[str, float],
        temperature: float,
        density: float,
        time: float
    ) -> Dict[str, float]:
        """
        Calculate ice mantle growth over time.

        Returns ice abundances (relative to H).
        """
        ice_abundances = {}

        # Species that freeze out
        freeze_out_species = ["CO", "H2O", "CO2", "CH3OH", "NH3", "CH4"]

        for species in freeze_out_species:
            if species not in gas_phase_abundances:
                continue

            gas_abundance = gas_phase_abundances[species]

            # Binding energies (K)
            binding_energies = {
                "CO": 1150,
                "H2O": 5700,
                "CO2": 2900,
                "CH3OH": 4800,
                "NH3": 3050,
                "CH4": 1300
            }

            E_b = binding_energies.get(species, 2000)

            # Desorption rate (thermal)
            k_des = 1e12 * np.exp(-E_b / temperature)  # s^-1

            # Accretion rate
            m_species = sum(self._get_atomic_mass(elem) for elem in species)
            v_thermal = np.sqrt(8 * 1.381e-23 * temperature / (np.pi * m_species * 1.66e-27))

            grain_number_density = density * 0.01 / (
                4/3 * np.pi * (self.grain_radius * 1e-6)**3 * 3000
            )

            k_acc = gas_abundance * density * grain_number_density * v_thermal * 1e-10

            # Steady-state ice abundance
            if k_des > 0:
                ice_abundance = k_acc * gas_abundance / k_des
            else:
                ice_abundance = k_acc * gas_abundance * time

            ice_abundances[species] = min(ice_abundance, gas_abundance)

        return ice_abundances

    def _get_atomic_mass(self, element: str) -> float:
        """Get atomic mass for element."""
        masses = {
            "H": 1.0, "C": 12.0, "N": 14.0, "O": 16.0,
            "S": 32.0, "Si": 28.0, "Fe": 56.0
        }
        return masses.get(element, 12.0)


# =============================================================================
# Factory Functions
# =============================================================================

def create_chemistry_network(
    environment: ChemicalEnvironment = ChemicalEnvironment.DARK_CLOUD
) -> InterstellarChemistryNetwork:
    """Create a chemistry network for a specific environment."""
    return InterstellarChemistryNetwork(environment)


def create_deuterium_model() -> DeuteriumFractionationModel:
    """Create a deuterium fractionation model."""
    return DeuteriumFractionationModel()


def create_emission_calculator() -> MolecularEmissionCalculator:
    """Create a molecular emission calculator."""
    return MolecularEmissionCalculator()


# =============================================================================
# Causal Discovery Integration
# =============================================================================

class ChemistryCausalDiscovery:
    """
    Causal discovery for chemical reaction networks.

    Identifies causal pathways in chemical evolution.
    """

    def __init__(self, chemistry_network: InterstellarChemistryNetwork):
        self.network = chemistry_network

    def discover_causal_pathways(
        self,
        target_species: str,
        time_evolution: List[ChemicalState]
    ) -> List[Dict[str, Any]]:
        """
        Discover causal pathways leading to target species.

        Returns list of causal chains with temporal ordering.
        """
        pathways = []

        # Get abundance evolution of target
        target_abundances = [state.abundances.get(target_species, 0.0)
                           for state in time_evolution]

        # Find when abundance increases
        for i in range(1, len(time_evolution)):
            if target_abundances[i] > target_abundances[i-1] * 1.1:  # 10% increase
                # Look for reactions that produce target
                for reaction in self.network.reactions:
                    if target_species in reaction.products:
                        # Check if reactants were present
                        reactants_present = all(
                            time_evolution[i-1].abundances.get(r, 0.0) > 1e-20
                            for r in reaction.reactants
                            if r not in ["photon", "cosmic_ray", "grain"]
                        )

                        if reactants_present:
                            pathway = {
                                "target": target_species,
                                "reaction": f"{' + '.join(reaction.reactants)} -> "
                                          f"{' + '.join(reaction.products)}",
                                "time": time_evolution[i].time,
                                "contribution": target_abundances[i] - target_abundances[i-1],
                                "temperature": time_evolution[i].temperature
                            }
                            pathways.append(pathway)

        return pathways
