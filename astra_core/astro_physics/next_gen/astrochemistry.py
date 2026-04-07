"""
Astrochemistry Module

Extended chemical networks for ISM and star formation studies.
Includes UMIST/KIDA rate coefficients, grain surface chemistry,
and isotopologue fractionation.

Date: 2025-12-15
"""

import numpy as np
from typing import List, Dict, Optional, Any, Tuple, Callable
from dataclasses import dataclass, field
from enum import Enum
from abc import ABC, abstractmethod
import warnings

# Physical constants (CGS)
K_BOLTZMANN = 1.381e-16  # erg/K
H_PLANCK = 6.626e-27  # erg s
M_PROTON = 1.673e-24  # g
AMU = 1.661e-24  # g
EV_TO_ERG = 1.602e-12
CM_TO_K = 1.4388  # cm^-1 to K conversion (hc/k)


class ReactionType(Enum):
    """Types of chemical reactions"""
    TWO_BODY = "two_body"
    COSMIC_RAY = "cosmic_ray"
    PHOTODISSOCIATION = "photodissociation"
    GRAIN_SURFACE = "grain_surface"
    THREE_BODY = "three_body"
    COLLIDER = "collider"
    ION_NEUTRAL = "ion_neutral"
    RADIATIVE_ASSOCIATION = "radiative_association"
    DISSOCIATIVE_RECOMBINATION = "dissociative_recombination"


@dataclass
class Species:
    """Chemical species definition"""
    name: str
    mass: float  # amu
    charge: int = 0
    n_atoms: int = 1
    binding_energy: float = 0.0  # K (for grain surface)
    is_grain: bool = False

    def __hash__(self):
        return hash(self.name)


@dataclass
class Reaction:
    """Chemical reaction definition"""
    reactants: Tuple[str, ...]
    products: Tuple[str, ...]
    alpha: float  # Rate coefficient parameter
    beta: float  # Temperature exponent
    gamma: float  # Activation energy (K)
    reaction_type: ReactionType
    temperature_range: Tuple[float, float] = (10.0, 41000.0)
    uncertainty: str = "A"  # UMIST uncertainty class

    def rate_coefficient(self, T: float, n_H: float = 1e4,
                         A_V: float = 1.0, zeta_CR: float = 1.3e-17) -> float:
        """
        Calculate rate coefficient at given conditions.

        Args:
            T: Temperature (K)
            n_H: H number density (cm^-3)
            A_V: Visual extinction (mag)
            zeta_CR: Cosmic ray ionization rate (s^-1)

        Returns:
            Rate coefficient (appropriate units)
        """
        if self.reaction_type == ReactionType.TWO_BODY:
            # k = alpha * (T/300)^beta * exp(-gamma/T)
            return self.alpha * (T / 300.0)**self.beta * np.exp(-self.gamma / T)

        elif self.reaction_type == ReactionType.COSMIC_RAY:
            # k = alpha * zeta
            return self.alpha * (zeta_CR / 1.3e-17)

        elif self.reaction_type == ReactionType.PHOTODISSOCIATION:
            # k = alpha * exp(-gamma * A_V)
            return self.alpha * np.exp(-self.gamma * A_V)

        elif self.reaction_type == ReactionType.ION_NEUTRAL:
            # Langevin rate with temperature correction
            return self.alpha * (T / 300.0)**self.beta

        elif self.reaction_type == ReactionType.DISSOCIATIVE_RECOMBINATION:
            # k = alpha * (T/300)^beta
            return self.alpha * (T / 300.0)**self.beta

        else:
            return self.alpha * (T / 300.0)**self.beta * np.exp(-self.gamma / T)


@dataclass
class ChemicalAbundances:
    """Container for chemical abundances"""
    species: Dict[str, float]  # name -> abundance relative to H
    time: float = 0.0
    temperature: float = 10.0
    density: float = 1e4

    def get(self, name: str, default: float = 0.0) -> float:
        return self.species.get(name, default)


# =============================================================================
# BASE CHEMICAL NETWORK
# =============================================================================

class ChemicalNetwork(ABC):
    """
    Base class for chemical reaction networks.

    Provides ODE integration and abundance tracking.
    """

    def __init__(self):
        """Initialize chemical network"""
        self.species: Dict[str, Species] = {}
        self.reactions: List[Reaction] = []
        self.abundances: Dict[str, float] = {}

        # Physical conditions
        self.temperature = 10.0  # K
        self.density = 1e4  # cm^-3
        self.A_V = 1.0  # mag
        self.zeta_CR = 1.3e-17  # s^-1
        self.G0 = 1.0  # UV field in Habing units

    @abstractmethod
    def load_reactions(self):
        """Load reactions from database"""
        pass

    def add_species(self, species: Species):
        """Add species to network"""
        self.species[species.name] = species

    def add_reaction(self, reaction: Reaction):
        """Add reaction to network"""
        self.reactions.append(reaction)

    def set_initial_abundances(self, abundances: Dict[str, float]):
        """
        Set initial abundances.

        Args:
            abundances: Dict of species name -> abundance relative to H
        """
        self.abundances = abundances.copy()

        # Ensure all species have an abundance
        for name in self.species:
            if name not in self.abundances:
                self.abundances[name] = 0.0

    def get_rates(self, T: float = None) -> Dict[int, float]:
        """
        Get all reaction rates at current conditions.

        Args:
            T: Temperature (uses self.temperature if None)

        Returns:
            Dict of reaction index -> rate coefficient
        """
        T = T or self.temperature
        rates = {}

        for i, rxn in enumerate(self.reactions):
            rates[i] = rxn.rate_coefficient(
                T, self.density, self.A_V, self.zeta_CR
            )

        return rates

    def compute_derivatives(self, abundances: np.ndarray,
                            species_list: List[str]) -> np.ndarray:
        """
        Compute dn/dt for all species.

        Args:
            abundances: Current abundances array
            species_list: Ordered list of species names

        Returns:
            Array of dn/dt values
        """
        n_species = len(species_list)
        dndt = np.zeros(n_species)

        # Map species name to index
        idx_map = {name: i for i, name in enumerate(species_list)}

        # Get rate coefficients
        rates = self.get_rates()

        for i, rxn in enumerate(self.reactions):
            k = rates[i]

            # Calculate reaction rate
            rate = k * self.density  # s^-1 for 1st order

            for reactant in rxn.reactants:
                if reactant in idx_map:
                    idx = idx_map[reactant]
                    rate *= abundances[idx]

            # Update derivatives
            for reactant in rxn.reactants:
                if reactant in idx_map:
                    idx = idx_map[reactant]
                    dndt[idx] -= rate

            for product in rxn.products:
                if product in idx_map:
                    idx = idx_map[product]
                    dndt[idx] += rate

        return dndt

    def integrate(self, t_final: float, dt_output: float = None,
                  method: str = 'BDF') -> Tuple[np.ndarray, np.ndarray]:
        """
        Integrate chemical evolution.

        Args:
            t_final: Final time (s)
            dt_output: Output time step (s)
            method: Integration method

        Returns:
            Tuple of (time_points, concentration_arrays)
        """
        if dt_output is None:
            dt_output = t_final / 100

        t_eval = np.arange(0, t_final, dt_output)

        # Simple Euler integration for now
        n_species = len(self.species)
        concentrations = np.zeros((len(t_eval), n_species))
        concentrations[0] = self.initial_abundances

        for i in range(1, len(t_eval)):
            dt = t_eval[i] - t_eval[i-1]
            dndt = self.compute_derivatives(concentrations[i-1])
            concentrations[i] = concentrations[i-1] + dndt * dt

        return t_eval, concentrations
