#!/usr/bin/env python3
"""
Radiative Transfer Solver Module for ASTRO-SWARM
=================================================

Comprehensive radiative transfer calculations for molecular line and
continuum emission in astrophysical environments.

Capabilities:
1. Non-LTE molecular excitation (RADEX-like statistical equilibrium)
2. Escape probability methods (uniform sphere, expanding sphere, slab)
3. Multi-layer radiative transfer
4. Line profile synthesis with turbulence
5. Dust continuum + line combination
6. PDR interface layer

Key References:
- van der Tak et al. 2007 (RADEX)
- Sobolev 1960 (escape probability)
- Rybicki & Lightman 1979 (RT fundamentals)
- Draine 2011 (ISM physics)

Author: Claude Code (ASTRO-SWARM)
Date: 2024-11
"""

import numpy as np
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple, Any, Callable
from enum import Enum
from abc import ABC, abstractmethod
from scipy.integrate import quad, odeint, solve_ivp
from scipy.optimize import fsolve, brentq
from scipy.interpolate import interp1d
from scipy.special import expn
import warnings

# Physical Constants (CGS)
k_B = 1.38e-16          # Boltzmann constant (erg/K)
h_planck = 6.626e-27    # Planck constant (erg s)
c_light = 2.998e10      # Speed of light (cm/s)
m_H = 1.67e-24          # Hydrogen mass (g)
T_CMB = 2.7255          # CMB temperature (K)


# =============================================================================
# ESCAPE PROBABILITY GEOMETRIES
# =============================================================================

class EscapeGeometry(Enum):
    """Geometry for escape probability calculation"""
    UNIFORM_SPHERE = "uniform_sphere"
    EXPANDING_SPHERE = "expanding_sphere"  # LVG/Sobolev
    PLANE_PARALLEL = "plane_parallel"      # Slab geometry
    STATIC_SPHERE = "static_sphere"


def escape_probability(tau: float, geometry: EscapeGeometry) -> float:
    """
    Calculate photon escape probability for given optical depth and geometry.

    Parameters
    ----------
    tau : float
        Line-center optical depth
    geometry : EscapeGeometry
        Geometry assumption

    Returns
    -------
    beta : float
        Escape probability (0 to 1)
    """
    tau = np.abs(tau)

    if tau < 1e-10:
        return 1.0

    if geometry == EscapeGeometry.UNIFORM_SPHERE:
        # Uniform sphere: beta = 1.5/tau * (1 - 2/tau^2 + (2/tau + 2/tau^2)*exp(-tau))
        if tau < 0.01:
            return 1.0 - tau/2.0 + tau**2/6.0
        elif tau > 50:
            return 1.5 / tau
        else:
            return 1.5/tau * (1.0 - 2.0/tau**2 + (2.0/tau + 2.0/tau**2) * np.exp(-tau))

    elif geometry == EscapeGeometry.EXPANDING_SPHERE:
        # LVG/Sobolev approximation: beta = (1 - exp(-tau)) / tau
        if tau < 0.01:
            return 1.0 - tau/2.0 + tau**2/6.0
        else:
            return (1.0 - np.exp(-tau)) / tau

    elif geometry == EscapeGeometry.PLANE_PARALLEL:
        # Plane-parallel slab: beta = (1 - exp(-3*tau)) / (3*tau)
        if tau < 0.01:
            return 1.0 - 1.5*tau + 1.5*tau**2
        else:
            return (1.0 - np.exp(-3.0*tau)) / (3.0*tau)

    elif geometry == EscapeGeometry.STATIC_SPHERE:
        # Static sphere with thermal broadening
        if tau < 0.01:
            return 1.0 - tau/2.0
        elif tau > 50:
            return 1.0 / (tau * np.sqrt(np.log(tau/np.sqrt(np.pi))))
        else:
            return 1.5/tau * (1.0 - 2.0/tau**2 + (2.0/tau + 2.0/tau**2) * np.exp(-tau))

    return 1.0


# =============================================================================
# MOLECULAR LEVEL POPULATIONS
# =============================================================================

@dataclass
class MolecularLevel:
    """Properties of a molecular energy level"""
    J: int                      # Rotational quantum number
    energy: float               # Energy above ground (K)
    weight: float               # Statistical weight (2J+1 for linear)


@dataclass
class CollisionRates:
    """Collision rate coefficients"""
    partner: str                # Collision partner (H2, He, e-, H)
    temperatures: np.ndarray    # Temperature grid (K)
    rates: np.ndarray          # Rate coefficients (cm³/s), shape (n_temps, n_trans)
    transitions: List[Tuple[int, int]]  # (upper, lower) level indices


@dataclass
class MolecularData:
    """Complete molecular data for RT calculations"""
    name: str
    levels: List[MolecularLevel]
    einstein_A: np.ndarray      # Einstein A coefficients (s⁻¹)
    frequencies: np.ndarray     # Transition frequencies (Hz)
    collision_rates: List[CollisionRates]

    @property
    def n_levels(self) -> int:
        return len(self.levels)

    def get_collision_rate(self, upper: int, lower: int, T_kin: float,
                           collider: str = 'H2') -> float:
        """
        Get collisional rate coefficient for a transition.

        Args:
            upper: Upper level index
            lower: Lower level index
            T_kin: Kinetic temperature (K)
            collider: Collider species ('H2', 'He', 'H', etc.)

        Returns:
            Collisional rate coefficient (cm³/s)
        """
        # Find the appropriate collision rates
        for cr in self.collision_rates:
            if cr.collider == collider:
                # Interpolate in temperature
                return np.interp(T_kin, cr.temperatures, cr.coefficients[upper, lower])

        # Default: return 0 if no data available
        return 0.0

    def level_population(self, T_kin: float, density: float,
                        collider: str = 'H2') -> np.ndarray:
        """
        Calculate level populations using statistical equilibrium.

        Args:
            T_kin: Kinetic temperature (K)
            density: Gas density (cm⁻³)
            collider: Collider species

        Returns:
            Level populations (normalized to sum to 1)
        """
        n_levels = self.n_levels
        populations = np.ones(n_levels) / n_levels  # Start with equal populations

        # Simplified iterative solution
        for _ in range(100):
            new_populations = populations.copy()
            for i in range(n_levels):
                for j in range(n_levels):
                    if i == j:
                        continue

                    # Radiative rates
                    if i > j:
                        rate = self.einstein_A[i, j]
                    else:
                        rate = 0

                    # Collisional rates
                    rate += density * self.get_collision_rate(i, j, T_kin, collider)

                    # Update populations (simplified)
                    new_populations[i] += rate * populations[j]

            # Normalize
            new_populations /= np.sum(new_populations)

            # Check convergence
            if np.max(np.abs(new_populations - populations)) < 1e-6:
                break

            populations = new_populations

        return populations
