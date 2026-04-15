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
HII Region Physics

This module provides comprehensive physics for ionized hydrogen regions
(HII regions) including:
- Strömgren sphere calculations
- Ionization equilibrium and structure
- Nebular emission line diagnostics (T_e, n_e from line ratios)
- Recombination cascades and line emissivities
- Free-free (Bremsstrahlung) continuum emission
- Photoionization modeling interface

Physical constants in CGS units throughout.

Date: 2025-12-11
Version: 43.0
"""

import math
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple, Callable
from enum import Enum, auto

# Physical constants (CGS)
C_LIGHT = 2.998e10       # Speed of light (cm/s)
H_PLANCK = 6.626e-27     # Planck constant (erg s)
K_BOLTZMANN = 1.381e-16  # Boltzmann constant (erg/K)
M_ELECTRON = 9.109e-28   # Electron mass (g)
M_PROTON = 1.673e-24     # Proton mass (g)
E_CHARGE = 4.803e-10     # Electron charge (esu)
M_SUN = 1.989e33         # Solar mass (g)
L_SUN = 3.828e33         # Solar luminosity (erg/s)
PC = 3.086e18            # Parsec (cm)
YEAR = 3.156e7           # Year (seconds)

# Ionization energies (eV)
CHI_H = 13.6             # Hydrogen ionization potential
CHI_HE = 24.6            # Helium first ionization
CHI_HE2 = 54.4           # Helium second ionization

# Conversion factors
EV_TO_ERG = 1.602e-12    # eV to erg
EV_TO_K = 11604.5        # eV to Kelvin


class HIIRegionType(Enum):
    """Types of HII regions."""
    ULTRACOMPACT = auto()     # UC HII, < 0.1 pc, n_e > 10^4
    COMPACT = auto()          # Compact, 0.1-1 pc
    CLASSICAL = auto()        # Classical, 1-10 pc
    GIANT = auto()            # Giant HII, 10-100 pc
    SUPERGIANT = auto()       # Supergiant, > 100 pc


class IonizationState(Enum):
    """Ionization-bounded vs density-bounded."""
    IONIZATION_BOUNDED = auto()  # All ionizing photons absorbed
    DENSITY_BOUNDED = auto()     # Ionizing photons escape


@dataclass
class StromgrenParameters:
    """Strömgren sphere parameters."""
    radius: float               # Strömgren radius (cm)
    volume: float               # Ionized volume (cm³)
    ionizing_photon_rate: float  # Q_H (photons/s)
    electron_density: float     # n_e (cm⁻³)
    recombination_rate: float   # α_B (cm³/s)
    recombination_time: float   # t_rec (s)
    ionization_state: IonizationState
    filling_factor: float       # Volume filling factor

    @property
    def radius_pc(self) -> float:
        """Radius in parsecs."""
        return self.radius / PC

    @property
    def recombination_time_yr(self) -> float:
        """Recombination time in years."""
        return self.recombination_time / YEAR


@dataclass
class NebularDiagnostics:
    """Nebular diagnostic results."""
    electron_temperature: float  # T_e (K)
    electron_density: float     # n_e (cm⁻³)
    ionic_abundances: Dict[str, float]  # Ion abundances relative to H
    ionization_correction: Dict[str, float]  # ICFs for total abundances
    total_abundances: Dict[str, float]  # Total element abundances

    # Diagnostic line ratios used
    oiii_ratio: Optional[float]  # [OIII] 4363/5007 (T_e diagnostic)
    nii_ratio: Optional[float]   # [NII] 5755/6583 (T_e diagnostic)
    sii_ratio: Optional[float]   # [SII] 6717/6731 (n_e diagnostic)
    oii_ratio: Optional[float]   # [OII] 3726/3729 (n_e diagnostic)


@dataclass
class RecombinationSpectrum:
    """Hydrogen recombination line spectrum."""
    line_name: str
    wavelength: float           # Wavelength (Angstrom)
    upper_level: int            # Upper principal quantum number
    lower_level: int            # Lower principal quantum number
    emissivity: float           # j_line (erg cm³/s)
    intensity_ratio: float      # Relative to Hβ

    @property
    def wavelength_micron(self) -> float:
        """Wavelength in microns."""
        return self.wavelength / 1e4


@dataclass
class FreeFreeEmission:
    """Free-free (Bremsstrahlung) emission."""
    emission_measure: float     # EM = ∫n_e n_i dl (cm⁻⁶ pc)
    brightness_temperature: float  # T_b at reference frequency (K)
    flux_density: float         # S_ν at reference frequency (Jy)
    spectral_index: float       # α where S_ν ∝ ν^α
    optical_depth: float        # τ_ff at reference frequency
    turnover_frequency: float   # ν where τ = 1 (Hz)


class RecombinationCoefficients:
    """
    Hydrogen recombination coefficients.

    Case A: All Lyman photons escape
    Case B: Lyman photons trapped (optically thick to Lyman series)
    """

    def __init__(self):
        """Initialize recombination coefficient calculator."""
        pass

    def alpha_A(self, temperature: float) -> float:
        """
        Case A total recombination coefficient.

        Includes recombinations to all levels including ground state.

        Args:
            temperature: Electron temperature (K)

        Returns:
            α_A (cm³/s)
        """
        # Fit from Osterbrock & Ferland (2006)
        t4 = temperature / 1e4
        return 4.18e-13 * t4**(-0.72)

    def alpha_B(self, temperature: float) -> float:
        """
        Case B total recombination coefficient.

        Excludes recombinations to ground state (Lyman photons trapped).

        Args:
            temperature: Electron temperature (K)

        Returns:
            α_B (cm³/s)
        """
        # Fit from Osterbrock & Ferland (2006)
        t4 = temperature / 1e4
        return 2.59e-13 * t4**(-0.833 - 0.034 * math.log(t4))

    def alpha_eff_hbeta(self, temperature: float) -> float:
        """
        Effective recombination coefficient for Hβ.

        Args:
            temperature: Electron temperature (K)

        Returns:
            α_eff(Hβ) (cm³/s)
        """
        t4 = temperature / 1e4
        return 3.03e-14 * t4**(-0.874)

    def alpha_eff_halpha(self, temperature: float) -> float:
        """
        Effective recombination coefficient for Hα.

        Args:
            temperature: Electron temperature (K)

        Returns:
            α_eff(Hα) (cm³/s)
        """
        t4 = temperature / 1e4
        return 1.17e-13 * t4**(-0.942)


class StromgrenSphere:
    """
    Strömgren sphere calculations for HII regions.

    The Strömgren sphere is the ionized region around a hot star
    where ionizations balance recombinations.

    R_s = (3 Q_H / 4π α_B n²)^(1/3)
    """

    def __init__(self):
        """Initialize Strömgren sphere calculator."""
        self.recomb = RecombinationCoefficients()

    def ionizing_photon_rate(self, spectral_type: str = None,
                             luminosity: float = None,
                             temperature: float = None) -> float:
        """
        Ionizing photon rate Q_H for given stellar parameters.

        Args:
            spectral_type: Spectral type (O3-B2)
            luminosity: Stellar luminosity (erg/s)
            temperature: Stellar effective temperature (K)

        Returns:
            Q_H (photons/s)
        """
        # Ionizing photon rates for O/B stars (Martins+ 2005, Sternberg+ 2003)
        q_h_table = {
            'O3V': 1e50, 'O4V': 6e49, 'O5V': 4e49, 'O6V': 2e49,
            'O7V': 1e49, 'O8V': 5e48, 'O9V': 2e48, 'O9.5V': 1e48,
            'B0V': 3e47, 'B0.5V': 1e47, 'B1V': 3e46, 'B2V': 5e45
        }

        if spectral_type and spectral_type in q_h_table:
            return q_h_table[spectral_type]

        if temperature:
            # Approximate fit for Q_H vs T_eff
            if temperature > 30000:
                return 10**(0.0003 * temperature + 39)
            else:
                return 0.0

        if luminosity:
            # Rough estimate assuming O star
            return luminosity / (H_PLANCK * C_LIGHT / (912e-8))  # 912 Å photon

        return 1e49  # Default O6V-like star

    def stromgren_radius(self, q_h: float, n_e: float,
                         temperature: float = 1e4,
                         filling_factor: float = 1.0) -> float:
        """
        Calculate Strömgren radius.

        R_s = (3 Q_H / 4π α_B n² f)^(1/3)

        Args:
            q_h: Ionizing photon rate (photons/s)
            n_e: Electron density (cm⁻³)
            temperature: Electron temperature (K)
            filling_factor: Volume filling factor

        Returns:
            Strömgren radius (cm)
        """
        alpha_b = self.recomb.alpha_B(temperature)
        n_eff = n_e * math.sqrt(filling_factor)
        return (3 * q_h / (4 * math.pi * alpha_b * n_eff**2))**(1/3)

    def recombination_time(self, n_e: float, temperature: float = 1e4) -> float:
        """
        Recombination timescale.

        t_rec = 1 / (α_B n_e)

        Args:
            n_e: Electron density (cm⁻³)
            temperature: Electron temperature (K)

        Returns:
            Recombination time (s)
        """
        alpha_b = self.recomb.alpha_B(temperature)
        return 1 / (alpha_b * n_e)

    def expansion_time(self, r_s: float, n_e: float,
                       temperature: float = 1e4) -> float:
        """
        Expansion timescale for HII region.

        t_exp ~ R_s / c_i where c_i is ionized gas sound speed

        Args:
            r_s: Strömgren radius (cm)
            n_e: Electron density (cm⁻³)
            temperature: Electron temperature (K)

        Returns:
            Expansion time (s)
        """
        # Ionized gas sound speed (including He contribution)
        mu_ion = 0.62
        c_i = math.sqrt(K_BOLTZMANN * temperature / (mu_ion * M_PROTON))
        return r_s / c_i

    def compute(self, q_h: float, n_0: float, temperature: float = 1e4,
                filling_factor: float = 1.0,
                ambient_radius: float = None) -> StromgrenParameters:
        """
        Compute complete Strömgren sphere parameters.

        Args:
            q_h: Ionizing photon rate (photons/s)
            n_0: Ambient density (cm⁻³)
            temperature: Electron temperature (K)
            filling_factor: Volume filling factor
            ambient_radius: Available radius (cm), if limited

        Returns:
            StromgrenParameters
        """
        # Electron density (assuming fully ionized H + 10% He)
        n_e = 1.1 * n_0

        # Strömgren radius
        r_s = self.stromgren_radius(q_h, n_e, temperature, filling_factor)

        # Check if ionization-bounded or density-bounded
        if ambient_radius and r_s > ambient_radius:
            ionization_state = IonizationState.DENSITY_BOUNDED
            r_s = ambient_radius
        else:
            ionization_state = IonizationState.IONIZATION_BOUNDED

        # Volume
        volume = (4/3) * math.pi * r_s**3 * filling_factor

        # Timescales
        alpha_b = self.recomb.alpha_B(temperature)
        t_rec = self.recombination_time(n_e, temperature)

        return StromgrenParameters(
            radius=r_s,
            volume=volume,
            ionizing_photon_rate=q_h,
            electron_density=n_e,
            recombination_rate=alpha_b,
            recombination_time=t_rec,
            ionization_state=ionization_state,
            filling_factor=filling_factor
        )


class IonizationEquilibrium:
    """
    Ionization equilibrium calculations.

    Solves photoionization-recombination balance for H and He.
    """

    def __init__(self):
        """Initialize ionization equilibrium solver."""
        self.recomb = RecombinationCoefficients()

    def hydrogen_ionization_fraction(self, ionization_parameter: float,
                                     temperature: float = 1e4) -> float:
        """
        Hydrogen ionization fraction x = n(H+)/n(H).

        Args:
            ionization_parameter: U = Q_H / (4π r² n c)
            temperature: Electron temperature (K)

        Returns:
            Ionization fraction (0-1)
        """
        # For typical HII region conditions, H is nearly fully ionized
        if ionization_parameter > 1e-4:
            return 0.9999
        elif ionization_parameter > 1e-6:
            return 0.99
        else:
            return ionization_parameter * 1e4

    def ionization_parameter(self, q_h: float, n_h: float,
                             radius: float) -> float:
        """
        Dimensionless ionization parameter.

        U = Q_H / (4π r² n_H c)

        Args:
            q_h: Ionizing photon rate (photons/s)
            n_h: Hydrogen density (cm⁻³)
            radius: Distance from source (cm)

        Returns:
            Ionization parameter U
        """
        return q_h / (4 * math.pi * radius**2 * n_h * C_LIGHT)

    def ionization_front_thickness(self, n_h: float,
                                   temperature: float = 1e4) -> float:
        """
        Thickness of ionization front.

        Δr ~ 1 / (n_H σ_H) where σ_H is H photoionization cross-section

        Args:
            n_h: Hydrogen density (cm⁻³)
            temperature: Temperature (K)

        Returns:
            Front thickness (cm)
        """
        # H photoionization cross-section at threshold
        sigma_h = 6.3e-18  # cm²
        return 1 / (n_h * sigma_h)


class NebularDiagnosticsCalculator:
    """
    Nebular emission line diagnostics.

    Derives T_e and n_e from collisionally excited line ratios.
    """

    def __init__(self):
        """Initialize nebular diagnostics calculator."""
        pass

    def oiii_temperature(self, ratio_4363_5007: float) -> float:
        """
        Electron temperature from [OIII] 4363/5007 ratio.

        This ratio is sensitive to T_e because 4363 comes from
        a higher energy level than 4959+5007.

        Args:
            ratio_4363_5007: [OIII] 4363 / ([OIII] 4959 + 5007)

        Returns:
            Electron temperature (K)
        """
        # Empirical fit (valid for T_e ~ 5000-20000 K)
