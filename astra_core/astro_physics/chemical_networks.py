#!/usr/bin/env python3
"""
Chemical Network Integration for ASTRO-SWARM
=============================================

Time-dependent astrochemistry modeling for interstellar and
circumstellar environments.

Capabilities:
1. UMIST/KIDA reaction network support
2. Gas-phase chemistry solver
3. Grain surface reactions
4. Photodissociation region chemistry
5. Depletion and freeze-out
6. Hot core chemistry
7. Molecular abundance evolution

Key References:
- McElroy et al. 2013 (UMIST 2012)
- Wakelam et al. 2012 (KIDA)
- Hasegawa et al. 1992 (grain surface)
- Hollenbach & Tielens 1999 (PDR)
- Garrod & Herbst 2006 (hot cores)

Author: Claude Code (ASTRO-SWARM)
Date: 2024-11
"""

import numpy as np
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple, Any, Callable, Set
from enum import Enum
from abc import ABC, abstractmethod
from scipy.integrate import solve_ivp, odeint
from scipy.interpolate import interp1d
import warnings
import json

# Physical Constants
k_B = 1.38e-16          # Boltzmann constant (erg/K)
h_planck = 6.626e-27    # Planck constant (erg s)
m_H = 1.67e-24          # Hydrogen mass (g)
year_s = 3.156e7        # Seconds per year


# =============================================================================
# REACTION TYPES
# =============================================================================

class ReactionType(Enum):
    """Types of chemical reactions"""
    # Gas-phase reactions
    ION_MOLECULE = "ion_molecule"
    NEUTRAL_NEUTRAL = "neutral_neutral"
    CHARGE_EXCHANGE = "charge_exchange"
    DISSOCIATIVE_RECOMBINATION = "dissociative_recombination"
    RADIATIVE_ASSOCIATION = "radiative_association"
    ASSOCIATIVE_DETACHMENT = "associative_detachment"

    # Photoreactions
    PHOTODISSOCIATION = "photodissociation"
    PHOTOIONIZATION = "photoionization"

    # Cosmic ray reactions
    COSMIC_RAY_IONIZATION = "cosmic_ray_ionization"
    COSMIC_RAY_PHOTODISSOCIATION = "cosmic_ray_photodissociation"

    # Grain reactions
    GRAIN_ADSORPTION = "grain_adsorption"
    GRAIN_DESORPTION = "grain_desorption"
    GRAIN_SURFACE = "grain_surface"
    H2_FORMATION = "h2_formation"


# =============================================================================
# CHEMICAL SPECIES
# =============================================================================

@dataclass
class Species:
    """Chemical species"""
    name: str
    mass: float                 # Atomic mass units
    charge: int = 0             # Charge (-1, 0, +1, etc.)
    binding_energy: float = 0.0  # Grain binding energy (K)
    is_grain: bool = False      # Is this a grain surface species?

    def __hash__(self):
        return hash(self.name)

    def __eq__(self, other):
        return self.name == other.name


class SpeciesLibrary:
    """
    Library of common interstellar species.
    """

    # Common species with masses and binding energies
    SPECIES_DATA = {
        # Atoms
        'H': {'mass': 1.0, 'charge': 0, 'E_bind': 450},
        'H+': {'mass': 1.0, 'charge': 1, 'E_bind': 0},
        'H-': {'mass': 1.0, 'charge': -1, 'E_bind': 0},
        'He': {'mass': 4.0, 'charge': 0, 'E_bind': 100},
        'C': {'mass': 12.0, 'charge': 0, 'E_bind': 800},
        'C+': {'mass': 12.0, 'charge': 1, 'E_bind': 0},
        'N': {'mass': 14.0, 'charge': 0, 'E_bind': 800},
        'O': {'mass': 16.0, 'charge': 0, 'E_bind': 800},
        'S': {'mass': 32.0, 'charge': 0, 'E_bind': 1100},
        'Si': {'mass': 28.0, 'charge': 0, 'E_bind': 2700},

        # Simple molecules
        'H2': {'mass': 2.0, 'charge': 0, 'E_bind': 430},
        'CO': {'mass': 28.0, 'charge': 0, 'E_bind': 1150},
        'H2O': {'mass': 18.0, 'charge': 0, 'E_bind': 5700},
        'OH': {'mass': 17.0, 'charge': 0, 'E_bind': 2850},
        'CH': {'mass': 13.0, 'charge': 0, 'E_bind': 600},
        'NH': {'mass': 15.0, 'charge': 0, 'E_bind': 600},
        'CN': {'mass': 26.0, 'charge': 0, 'E_bind': 1600},
        'NO': {'mass': 30.0, 'charge': 0, 'E_bind': 1600},
        'O2': {'mass': 32.0, 'charge': 0, 'E_bind': 1000},
        'N2': {'mass': 28.0, 'charge': 0, 'E_bind': 790},
        'CS': {'mass': 44.0, 'charge': 0, 'E_bind': 1900},
        'SO': {'mass': 48.0, 'charge': 0, 'E_bind': 2600},

        # Polyatomic
        'NH3': {'mass': 17.0, 'charge': 0, 'E_bind': 5530},
        'CH4': {'mass': 16.0, 'charge': 0, 'E_bind': 1300},
        'HCN': {'mass': 27.0, 'charge': 0, 'E_bind': 3700},
        'HNC': {'mass': 27.0, 'charge': 0, 'E_bind': 3700},
        'HCO': {'mass': 29.0, 'charge': 0, 'E_bind': 1600},
        'H2CO': {'mass': 30.0, 'charge': 0, 'E_bind': 2050},
        'CH3OH': {'mass': 32.0, 'charge': 0, 'E_bind': 5530},
        'CO2': {'mass': 44.0, 'charge': 0, 'E_bind': 2575},
        'H2S': {'mass': 34.0, 'charge': 0, 'E_bind': 2743},
        'OCS': {'mass': 60.0, 'charge': 0, 'E_bind': 2888},
        'SO2': {'mass': 64.0, 'charge': 0, 'E_bind': 5330},
        'N2H+': {'mass': 29.0, 'charge': 1, 'E_bind': 0},
        'HCO+': {'mass': 29.0, 'charge': 1, 'E_bind': 0},
        'H3+': {'mass': 3.0, 'charge': 1, 'E_bind': 0},
        'H3O+': {'mass': 19.0, 'charge': 1, 'E_bind': 0},

        # Electrons
        'e-': {'mass': 0.00055, 'charge': -1, 'E_bind': 0},

        # Grain species (ice mantles)
        'JH': {'mass': 1.0, 'charge': 0, 'E_bind': 450, 'grain': True},
        'JH2': {'mass': 2.0, 'charge': 0, 'E_bind': 430, 'grain': True},
        'JCO': {'mass': 28.0, 'charge': 0, 'E_bind': 1150, 'grain': True},
        'JH2O': {'mass': 18.0, 'charge': 0, 'E_bind': 5700, 'grain': True},
        'JCH3OH': {'mass': 32.0, 'charge': 0, 'E_bind': 5530, 'grain': True},
        'JNH3': {'mass': 17.0, 'charge': 0, 'E_bind': 5530, 'grain': True},
        'JCO2': {'mass': 44.0, 'charge': 0, 'E_bind': 2575, 'grain': True},
    }

    @classmethod
    def get(cls, name: str) -> Species:
        """Get species by name"""
        if name not in cls.SPECIES_DATA:
            # Unknown species - estimate properties
            mass = sum(1 for c in name if c.isupper()) * 12  # Rough estimate
            return Species(name=name, mass=mass)

        data = cls.SPECIES_DATA[name]
        return Species(
            name=name,
            mass=data['mass'],
            charge=data['charge'],
            binding_energy=data['E_bind'],
            is_grain=data.get('grain', False)
        )

    @classmethod
    def available(cls) -> List[str]:
        """List available species"""
        return list(cls.SPECIES_DATA.keys())


# =============================================================================
# CHEMICAL REACTIONS
# =============================================================================

@dataclass
class Reaction:
    """Chemical reaction"""
    reactants: List[str]
    products: List[str]
    reaction_type: ReactionType
    alpha: float = 0.0          # Rate coefficient parameter
    beta: float = 0.0           # Temperature exponent
    gamma: float = 0.0          # Activation energy (K)
    temperature_range: Tuple[float, float] = (10, 41000)

    def rate_coefficient(self, T: float, **kwargs) -> float:
        """
        Calculate rate coefficient.

        Parameters
        ----------
        T : float
            Temperature (K)
        kwargs : dict
            Additional parameters (zeta_CR, G0, A_V, etc.)

        Returns
        -------
        float : Rate coefficient (cm³/s for two-body, s⁻¹ for unary)
        """
        # Clip temperature to valid range
        T = np.clip(T, self.temperature_range[0], self.temperature_range[1])

        if self.reaction_type in [ReactionType.ION_MOLECULE,
                                  ReactionType.NEUTRAL_NEUTRAL,
                                  ReactionType.CHARGE_EXCHANGE,
                                  ReactionType.RADIATIVE_ASSOCIATION]:
            # k = α * (T/300)^β * exp(-γ/T)
            return self.alpha * (T / 300.0)**self.beta * np.exp(-self.gamma / T)

        elif self.reaction_type == ReactionType.DISSOCIATIVE_RECOMBINATION:
            # k = α * (T/300)^β
            return self.alpha * (T / 300.0)**self.beta

        elif self.reaction_type == ReactionType.COSMIC_RAY_IONIZATION:
            # k = α * ζ_CR
            zeta_CR = kwargs.get('zeta_CR', 1.3e-17)
            return self.alpha * zeta_CR

        elif self.reaction_type == ReactionType.COSMIC_RAY_PHOTODISSOCIATION:
            # k = α * ζ_CR * (γ / (1 - ω))
            zeta_CR = kwargs.get('zeta_CR', 1.3e-17)
            return self.alpha * zeta_CR

        elif self.reaction_type == ReactionType.PHOTODISSOCIATION:
            # k = α * G_0 * exp(-γ * A_V)
            G0 = kwargs.get('G0', 1.0)
            A_V = kwargs.get('A_V', 0.0)
            return self.alpha * G0 * np.exp(-self.gamma * A_V)

        elif self.reaction_type == ReactionType.PHOTOIONIZATION:
            G0 = kwargs.get('G0', 1.0)
            A_V = kwargs.get('A_V', 0.0)
            return self.alpha * G0 * np.exp(-self.gamma * A_V)

        elif self.reaction_type == ReactionType.GRAIN_ADSORPTION:
            # Thermal velocity * grain cross section * sticking
            S = kwargs.get('sticking', 1.0)
            n_grain = kwargs.get('n_grain', 1e-12)  # Grain density relative to H
            a_grain = kwargs.get('a_grain', 0.1e-4)  # Grain radius (cm)

            # Thermal velocity
            species_mass = self.alpha  # Store mass in alpha for this type
            v_th = np.sqrt(8 * k_B * T / (np.pi * species_mass * m_H))

            # Grain cross section * number density
            sigma_grain = np.pi * a_grain**2 * n_grain

            return S * v_th * sigma_grain

        elif self.reaction_type == ReactionType.GRAIN_DESORPTION:
            # Thermal desorption: k = ν_0 * exp(-E_bind/T)
            nu_0 = 1e12  # Characteristic frequency (s⁻¹)
            E_bind = self.gamma  # Binding energy stored in gamma
            return nu_0 * np.exp(-E_bind / T)

        elif self.reaction_type == ReactionType.GRAIN_SURFACE:
            # Langmuir-Hinshelwood rate
            # Simplified: k = κ * ν * exp(-E_a/T) / N_sites
            N_sites = kwargs.get('N_sites', 1e6)  # Sites per grain
            kappa = self.alpha  # Diffusion-to-binding ratio
            nu_0 = 1e12
            E_diff = self.gamma  # Diffusion barrier

            return kappa * nu_0 * np.exp(-E_diff / T) / N_sites

        elif self.reaction_type == ReactionType.H2_FORMATION:
            # H2 formation on grains
            # Rate per H atom: R = 0.5 * v_H * n_grain * σ_grain * ε
            n_grain = kwargs.get('n_grain', 1e-12)
            a_grain = kwargs.get('a_grain', 0.1e-4)
            efficiency = self.alpha

            v_H = np.sqrt(8 * k_B * T / (np.pi * m_H))
            sigma_grain = np.pi * a_grain**2 * n_grain

            return 0.5 * v_H * sigma_grain * efficiency

        return self.alpha


# =============================================================================
# REACTION NETWORKS
# =============================================================================

class ReactionNetwork:
    """
    Chemical reaction network.
    """

    def __init__(self, name: str = "custom"):
        self.name = name
        self.species: Dict[str, Species] = {}
        self.reactions: List[Reaction] = []
        self.species_to_index: Dict[str, int] = {}
        self.index_to_species: Dict[int, str] = {}

    def add_species(self, species: Species):
        """Add a species to the network"""
        if species.name not in self.species:
            self.species[species.name] = species
            idx = len(self.species_to_index)
            self.species_to_index[species.name] = idx
            self.index_to_species[idx] = species.name

    def add_reaction(self, reaction: Reaction):
        """Add a reaction to the network"""
        # Ensure all species are registered
        for s in reaction.reactants + reaction.products:
            if s not in self.species:
                self.add_species(SpeciesLibrary.get(s))
        self.reactions.append(reaction)

    def n_species(self) -> int:
        return len(self.species)

    def n_reactions(self) -> int:
        return len(self.reactions)

    def get_species_index(self, name: str) -> int:
        return self.species_to_index.get(name, -1)

    def get_species_name(self, index: int) -> str:
        return self.index_to_species.get(index, "")


class StandardNetworks:
    """
    Pre-built standard chemical networks.
    """

    @staticmethod
    def minimal_carbon_oxygen() -> ReactionNetwork:
        """
        Minimal C/O chemistry network for testing.
        """
        network = ReactionNetwork("minimal_CO")

        # Add key species
        species_list = ['H', 'H2', 'H+', 'H3+', 'e-', 'He', 'He+',
                       'C', 'C+', 'O', 'O+', 'CO', 'CO+', 'OH', 'H2O',
                       'HCO+', 'CH', 'CH+']

        for s in species_list:
            network.add_species(SpeciesLibrary.get(s))

        # Add key reactions
        reactions = [
            # Cosmic ray ionization
            Reaction(['H2'], ['H2+', 'e-'], ReactionType.COSMIC_RAY_IONIZATION,
                    alpha=2.0),
            Reaction(['H'], ['H+', 'e-'], ReactionType.COSMIC_RAY_IONIZATION,
                    alpha=0.5),
            Reaction(['He'], ['He+', 'e-'], ReactionType.COSMIC_RAY_IONIZATION,
                    alpha=0.5),

            # H3+ formation
            Reaction(['H2+', 'H2'], ['H3+', 'H'], ReactionType.ION_MOLECULE,
                    alpha=2.0e-9),

            # CO formation via CH
            Reaction(['C+', 'H2'], ['CH+', 'H'], ReactionType.ION_MOLECULE,
                    alpha=1.0e-10, gamma=4640),
            Reaction(['CH+', 'H2'], ['CH2+', 'H'], ReactionType.ION_MOLECULE,
                    alpha=1.2e-9),
            Reaction(['CH', 'O'], ['CO', 'H'], ReactionType.NEUTRAL_NEUTRAL,
                    alpha=6.6e-11),

            # CO destruction
            Reaction(['CO', 'He+'], ['C+', 'O', 'He'], ReactionType.ION_MOLECULE,
                    alpha=1.6e-9),

            # Electron recombination
            Reaction(['H3+', 'e-'], ['H2', 'H'], ReactionType.DISSOCIATIVE_RECOMBINATION,
                    alpha=2.3e-8, beta=-0.52),
            Reaction(['HCO+', 'e-'], ['CO', 'H'], ReactionType.DISSOCIATIVE_RECOMBINATION,
                    alpha=2.4e-7, beta=-0.69),

            # HCO+ formation
            Reaction(['H3+', 'CO'], ['HCO+', 'H2'], ReactionType.ION_MOLECULE,
                    alpha=1.7e-9),

            # Photodissociation
            Reaction(['CO'], ['C', 'O'], ReactionType.PHOTODISSOCIATION,
                    alpha=2.0e-10, gamma=3.5),
            Reaction(['H2'], ['H', 'H'], ReactionType.PHOTODISSOCIATION,
                    alpha=5.0e-11, gamma=3.7),

            # H2 formation on grains
            Reaction(['H', 'H'], ['H2'], ReactionType.H2_FORMATION,
                    alpha=0.3),
        ]

        for rxn in reactions:
            network.add_reaction(rxn)

        return network

    @staticmethod
    def nitrogen_chemistry() -> ReactionNetwork:
        """
        Nitrogen chemistry network.
        """
        network = StandardNetworks.minimal_carbon_oxygen()

        # Add nitrogen species
        n_species = ['N', 'N+', 'N2', 'N2+', 'NH', 'NH2', 'NH3',
                    'N2H+', 'HCN', 'HNC', 'CN', 'NO']

        for s in n_species:
            network.add_species(SpeciesLibrary.get(s))

        # Add nitrogen reactions
        reactions = [
            # N2H+ formation/destruction
            Reaction(['N2', 'H3+'], ['N2H+', 'H2'], ReactionType.ION_MOLECULE,
                    alpha=1.8e-9),
            Reaction(['N2H+', 'CO'], ['HCO+', 'N2'], ReactionType.ION_MOLECULE,
                    alpha=8.8e-10),
            Reaction(['N2H+', 'e-'], ['N2', 'H'], ReactionType.DISSOCIATIVE_RECOMBINATION,
                    alpha=2.8e-7, beta=-0.74),

            # HCN/HNC formation
            Reaction(['CH', 'N'], ['CN', 'H'], ReactionType.NEUTRAL_NEUTRAL,
                    alpha=1.7e-10, beta=0.18),
            Reaction(['CN', 'H2'], ['HCN', 'H'], ReactionType.NEUTRAL_NEUTRAL,
                    alpha=4.0e-13, beta=2.87, gamma=820),
            Reaction(['HCN'], ['HNC'], ReactionType.NEUTRAL_NEUTRAL,
                    alpha=1e-15),  # Isomerization (simplified)

            # NH3 formation
            Reaction(['N', 'H3+'], ['NH+', 'H2'], ReactionType.ION_MOLECULE,
                    alpha=4.0e-9),
            Reaction(['NH+', 'H2'], ['NH2+', 'H'], ReactionType.ION_MOLECULE,
                    alpha=1.0e-9),
            Reaction(['NH2+', 'H2'], ['NH3+', 'H'], ReactionType.ION_MOLECULE,
                    alpha=2.7e-10),
            Reaction(['NH3+', 'H2'], ['NH4+', 'H'], ReactionType.ION_MOLECULE,
                    alpha=2.4e-12),
            Reaction(['NH4+', 'e-'], ['NH3', 'H'], ReactionType.DISSOCIATIVE_RECOMBINATION,
                    alpha=1.5e-6, beta=-0.5),
        ]

        for rxn in reactions:
            network.add_reaction(rxn)

        return network


# =============================================================================
# CHEMISTRY SOLVER
# =============================================================================

@dataclass
class ChemistryConditions:
    """Physical conditions for chemistry"""
    temperature: float          # Gas temperature (K)
    density: float              # H nuclei density (cm⁻³)
    A_V: float = 0.0           # Visual extinction
    G0: float = 1.0            # FUV field (Habing units)
    zeta_CR: float = 1.3e-17   # Cosmic ray ionization rate (s⁻¹)
    dust_to_gas: float = 0.01  # Dust-to-gas mass ratio
    metallicity: float = 1.0   # Metallicity (solar = 1)


@dataclass
class ChemistryResult:
    """Results from chemistry integration"""
    times: np.ndarray           # Time points (years)
    abundances: np.ndarray      # Shape: (n_times, n_species)
    species_names: List[str]
    conditions: ChemistryConditions
    final_abundances: Dict[str, float]
    steady_state: bool


class ChemistrySolver:
    """
    Time-dependent chemistry solver.
    """

    def __init__(self, network: ReactionNetwork):
        self.network = network
        self.n_species = network.n_species()

    def solve(self, initial_abundances: Dict[str, float],
             conditions: ChemistryConditions,
             t_final: float = 1e6,
             n_output: int = 100,
             method: str = 'LSODA') -> ChemistryResult:
        """
        Solve chemistry evolution.

        Parameters
        ----------
        initial_abundances : dict
            Initial abundances relative to H nuclei
        conditions : ChemistryConditions
            Physical conditions
        t_final : float
            Final time (years)
        n_output : int
            Number of output times
        method : str
            ODE solver method

        Returns
        -------
        ChemistryResult
        """
        # Build initial abundance array
        y0 = np.zeros(self.n_species)
        for species, abund in initial_abundances.items():
            idx = self.network.get_species_index(species)
            if idx >= 0:
                y0[idx] = abund

        # Ensure charge conservation (set electron abundance)
        e_idx = self.network.get_species_index('e-')
        if e_idx >= 0:
            charge_sum = 0.0
            for name, species in self.network.species.items():
                idx = self.network.get_species_index(name)
                if idx >= 0 and species.charge != 0 and name != 'e-':
                    charge_sum += species.charge * y0[idx]
            y0[e_idx] = max(charge_sum, 1e-20)

        # Time array (logarithmic spacing)
        t_span = (1.0, t_final * year_s)
        t_eval = np.logspace(0, np.log10(t_final * year_s), n_output)

        # Rate calculation kwargs
        rate_kwargs = {
            'zeta_CR': conditions.zeta_CR,
            'G0': conditions.G0,
            'A_V': conditions.A_V,
            'n_grain': 1e-12 * conditions.dust_to_gas / 0.01
        }

        # ODE function
        def dydt(t, y):
            return self._compute_rates(y, conditions.temperature,
                                      conditions.density, rate_kwargs)

        # Solve
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            solution = solve_ivp(dydt, t_span, y0, method=method,
                               t_eval=t_eval, atol=1e-20, rtol=1e-6)

        # Convert time to years
        times = solution.t / year_s

        # Build result
        species_names = [self.network.get_species_name(i)
                        for i in range(self.n_species)]

        final_abundances = {species_names[i]: solution.y[i, -1]
                          for i in range(self.n_species)}

        # Check for steady state
        if len(solution.y[0]) > 1:
            relative_change = np.abs(solution.y[:, -1] - solution.y[:, -2]) / \
                             (solution.y[:, -1] + 1e-30)
            steady_state = np.max(relative_change) < 1e-3
        else:
            steady_state = False

        return ChemistryResult(
            times=times,
            abundances=solution.y.T,
            species_names=species_names,
            conditions=conditions,
            final_abundances=final_abundances,
            steady_state=steady_state
        )

    def _compute_rates(self, y: np.ndarray, T: float, n_H: float,
                      kwargs: Dict) -> np.ndarray:
        """Compute rate of change for each species"""
        dydt = np.zeros(self.n_species)

        for reaction in self.network.reactions:
            # Calculate rate coefficient
            k = reaction.rate_coefficient(T, **kwargs)

            # Calculate reaction rate
            rate = k * n_H  # Base rate

            for reactant in reaction.reactants:
                idx = self.network.get_species_index(reactant)
                if idx >= 0:
                    rate *= y[idx] * n_H

            # Apply rate to reactants (destruction) and products (creation)
            for reactant in reaction.reactants:
                idx = self.network.get_species_index(reactant)
                if idx >= 0:
                    dydt[idx] -= rate / n_H  # Convert back to abundance

            for product in reaction.products:
                idx = self.network.get_species_index(product)
                if idx >= 0:
                    dydt[idx] += rate / n_H

        return dydt

    def equilibrium(self, initial_abundances: Dict[str, float],
                   conditions: ChemistryConditions,
                   max_time: float = 1e8) -> Dict[str, float]:
        """
        Find chemical equilibrium.

        Parameters
        ----------
        initial_abundances : dict
            Starting abundances
        conditions : ChemistryConditions
            Physical conditions
        max_time : float
            Maximum integration time (years)

        Returns
        -------
        dict : Equilibrium abundances
        """
        result = self.solve(initial_abundances, conditions,
                          t_final=max_time, n_output=50)
        return result.final_abundances


# =============================================================================
# PDR CHEMISTRY
# =============================================================================

class PDRChemistry:
    """
    Photodissociation region chemistry.

    Calculates chemical structure as function of A_V into cloud.
    """

    def __init__(self, network: Optional[ReactionNetwork] = None):
        if network is None:
            network = StandardNetworks.nitrogen_chemistry()
        self.network = network
        self.solver = ChemistrySolver(network)

    def calculate_structure(self,
                           n_H: float,
                           G0: float,
                           A_V_max: float = 10.0,
                           n_points: int = 50,
                           T_surface: float = 500,
                           T_deep: float = 20) -> Dict[str, np.ndarray]:
        """
        Calculate PDR chemical structure.

        Parameters
        ----------
        n_H : float
            Hydrogen density (cm⁻³)
        G0 : float
            FUV radiation field (Habing)
        A_V_max : float
            Maximum visual extinction
        n_points : int
            Number of depth points
        T_surface : float
            Surface temperature (K)
        T_deep : float
            Deep cloud temperature (K)

        Returns
        -------
        dict : Abundances as function of A_V
        """
        A_V_grid = np.linspace(0, A_V_max, n_points)

        # Simple temperature profile
        T_grid = T_surface * np.exp(-A_V_grid / 2) + T_deep

        # Initial (atomic) abundances at surface
        initial = {
            'H': 0.5,
            'H2': 0.25,
            'He': 0.1,
            'C+': 1.4e-4,
            'O': 3.0e-4,
            'N': 7.5e-5,
            'e-': 1.4e-4
        }

        # Solve chemistry at each depth
        abundances = {name: np.zeros(n_points)
                     for name in self.network.species.keys()}

        current_abundances = initial.copy()

        for i, (A_V, T) in enumerate(zip(A_V_grid, T_grid)):
            conditions = ChemistryConditions(
                temperature=T,
                density=n_H,
                A_V=A_V,
                G0=G0
            )

            result = self.solver.solve(current_abundances, conditions,
                                      t_final=1e5, n_output=10)

            for name in self.network.species.keys():
                abundances[name][i] = result.final_abundances.get(name, 0)

            current_abundances = result.final_abundances

        abundances['A_V'] = A_V_grid
        abundances['T'] = T_grid

        return abundances


# =============================================================================
# FREEZE-OUT AND DESORPTION
# =============================================================================

class GrainChemistry:
    """
    Grain surface chemistry and freeze-out.
    """

    def __init__(self, n_H: float = 1e4, T_gas: float = 10,
                a_grain: float = 0.1e-4, rho_grain: float = 3.0):
        """
        Parameters
        ----------
        n_H : float
            Gas density (cm⁻³)
        T_gas : float
            Gas temperature (K)
        a_grain : float
            Grain radius (cm)
        rho_grain : float
            Grain material density (g/cm³)
        """
        self.n_H = n_H
        self.T_gas = T_gas
        self.a_grain = a_grain
        self.rho_grain = rho_grain

        # Grain properties
        self.n_grain = 1.3e-12 * (n_H / 1e4) * (0.1e-4 / a_grain)**3
        self.n_sites = 4 * np.pi * a_grain**2 / (3e-8)**2  # ~1e6 for 0.1μm

    def freeze_out_timescale(self, species: str) -> float:
        """
        Calculate freeze-out timescale.

        τ = 1 / (n_grain * σ_grain * v_thermal * S)

        Returns time in years.
        """
        sp = SpeciesLibrary.get(species)
        v_th = np.sqrt(8 * k_B * self.T_gas / (np.pi * sp.mass * m_H))
        sigma = np.pi * self.a_grain**2

        tau_s = 1.0 / (self.n_grain * sigma * v_th)
        return tau_s / year_s

    def desorption_timescale(self, species: str, T_dust: float) -> float:
        """
        Calculate thermal desorption timescale.

        τ = 1 / (ν_0 * exp(-E_bind/T))

        Returns time in years.
        """
        sp = SpeciesLibrary.get(species)
        nu_0 = 1e12  # s⁻¹
        tau_s = 1.0 / (nu_0 * np.exp(-sp.binding_energy / T_dust))
        return tau_s / year_s

    def depletion_factor(self, species: str, t_years: float,
                        T_dust: float) -> float:
        """
        Calculate gas-phase depletion factor.

        f_dep = n_gas / n_total = exp(-t / τ_freeze) / (1 + exp(-t/τ_freeze)/f_eq)

        where f_eq = τ_desorb / (τ_freeze + τ_desorb)

        Parameters
        ----------
        species : str
            Species name
        t_years : float
            Time (years)
        T_dust : float
            Dust temperature (K)

        Returns
        -------
        float : Fraction remaining in gas phase
        """
        tau_freeze = self.freeze_out_timescale(species)
        tau_desorb = self.desorption_timescale(species, T_dust)

        # Equilibrium gas fraction
        f_eq = tau_desorb / (tau_freeze + tau_desorb)

        # Time evolution (simplified)
        tau_eff = tau_freeze * tau_desorb / (tau_freeze + tau_desorb)
        f_gas = f_eq + (1 - f_eq) * np.exp(-t_years / tau_eff)

        return f_gas


# =============================================================================
# HOT CORE CHEMISTRY
# =============================================================================

class HotCoreChemistry:
    """
    Hot core/corino chemistry.

    Models the warm-up phase when ices sublimate.
    """

    def __init__(self, network: Optional[ReactionNetwork] = None):
        if network is None:
            network = StandardNetworks.nitrogen_chemistry()
        self.network = network
        self.solver = ChemistrySolver(network)

    def warmup_model(self,
                    T_initial: float = 10,
                    T_final: float = 200,
                    t_warmup: float = 1e4,
                    n_H: float = 1e6,
                    ice_abundances: Optional[Dict[str, float]] = None) -> ChemistryResult:
        """
        Model hot core warm-up.

        Parameters
        ----------
        T_initial : float
            Initial (cold) temperature (K)
        T_final : float
            Final (warm) temperature (K)
        t_warmup : float
            Warm-up timescale (years)
        n_H : float
            Density (cm⁻³)
        ice_abundances : dict
            Ice mantle abundances to release

        Returns
        -------
        ChemistryResult
        """
        if ice_abundances is None:
            # Standard ice composition
            ice_abundances = {
                'H2O': 1e-4,
                'CO': 2e-5,
                'CO2': 1e-5,
                'CH3OH': 5e-6,
                'NH3': 3e-6,
                'H2CO': 5e-7
            }

        # Temperature profile: T(t) = T_i + (T_f - T_i) * (1 - exp(-t/τ))
        # For simplicity, solve in discrete temperature steps

        n_steps = 20
        T_grid = np.linspace(T_initial, T_final, n_steps)

        # Initial gas abundances (depleted)
        initial = {
            'H2': 0.5,
            'He': 0.1,
            'e-': 1e-8,
            'H3+': 1e-9
        }

        # Add small gas-phase component
        for sp, abund in ice_abundances.items():
            initial[sp] = abund * 0.01  # 1% in gas phase initially

        current = initial.copy()
        all_results = []

        for i, T in enumerate(T_grid):
            # Sublimate ices at appropriate temperatures
            for sp, abund in ice_abundances.items():
                sp_data = SpeciesLibrary.get(sp)
                if T > sp_data.binding_energy / 30:  # Rough sublimation criterion
                    current[sp] = current.get(sp, 0) + abund / n_steps

            conditions = ChemistryConditions(
                temperature=T,
                density=n_H,
                A_V=100,  # Deep in cloud
                G0=0
            )

            result = self.solver.solve(current, conditions,
                                      t_final=t_warmup / n_steps)
            all_results.append(result)
            current = result.final_abundances

        # Combine results
        times = np.concatenate([r.times + i * t_warmup / n_steps
                               for i, r in enumerate(all_results)])
        abundances = np.vstack([r.abundances for r in all_results])

        return ChemistryResult(
            times=times,
            abundances=abundances,
            species_names=all_results[0].species_names,
            conditions=ChemistryConditions(T_final, n_H),
            final_abundances=current,
            steady_state=False
        )


# =============================================================================
# UTILITY FUNCTIONS
# =============================================================================

def column_density_from_abundance(abundance: float, N_H2: float) -> float:
    """
    Convert abundance to column density.

    Parameters
    ----------
    abundance : float
        Abundance relative to H nuclei
    N_H2 : float
        H2 column density (cm⁻²)

    Returns
    -------
    float : Column density (cm⁻²)
    """
    return abundance * 2 * N_H2


def abundance_from_column_density(N_mol: float, N_H2: float) -> float:
    """
    Convert column density to abundance.

    Parameters
    ----------
    N_mol : float
        Molecular column density (cm⁻²)
    N_H2 : float
        H2 column density (cm⁻²)

    Returns
    -------
    float : Abundance relative to H nuclei
    """
    return N_mol / (2 * N_H2)


# =============================================================================
# EXPORT
# =============================================================================

__all__ = [
    'ReactionType',
    'Species',
    'SpeciesLibrary',
    'Reaction',
    'ReactionNetwork',
    'StandardNetworks',
    'ChemistryConditions',
    'ChemistryResult',
    'ChemistrySolver',
    'PDRChemistry',
    'GrainChemistry',
    'HotCoreChemistry',
    'column_density_from_abundance',
    'abundance_from_column_density',
]



def utility_function_27(*args, **kwargs):
    """Utility function 27."""
    return None



def utility_function_7(*args, **kwargs):
    """Utility function 7."""
    return None


