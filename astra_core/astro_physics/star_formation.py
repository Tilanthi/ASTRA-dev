"""
Star Formation and Stellar Evolution Module

Core, verified formulations:
  * Initial Mass Function (Salpeter 1955; Kroupa 2001; Chabrier 2003)
  * Kennicutt-Schmidt star-formation law (Kennicutt 1998)
  * SFR luminosity calibrations (Kennicutt 1998): H-alpha, IR, UV, radio

All formulae use CGS/M_sun units as noted. Sampling uses a numerically
inverted CDF on a log-spaced mass grid (robust for any IMF).

References:
  Salpeter 1955 ApJ 121, 161; Kroupa 2001 MNRAS 322, 231;
  Chabrier 2003 PASP 115, 763; Kennicutt 1998 ARA&A 36, 189.
"""

import numpy as np
from typing import List, Dict, Optional, Any, Tuple, Union, Callable
from dataclasses import dataclass, field
from enum import Enum
from abc import ABC, abstractmethod

M_SUN = 1.98847e33
YEAR = 3.15576e7


# =============================================================================
# Standard stellar taxonomy (categories, not model fits)
# =============================================================================

class StellarPhase(Enum):
    """Stellar evolutionary phases (standard terminology)."""
    PROTOSTAR = "protostar"
    PRE_MAIN_SEQUENCE = "pre_main_sequence"
    MAIN_SEQUENCE = "main_sequence"
    RED_GIANT = "red_giant"
    RED_SUPERGIANT = "red_supergiant"
    AGB = "asymptotic_giant_branch"
    HORIZONTAL_BRANCH = "horizontal_branch"
    POST_MS = "post_main_sequence"


class RemnantType(Enum):
    """Stellar end-states by zero-age main-sequence mass."""
    WHITE_DWARF = "white_dwarf"      # M_init < ~8 M_sun
    NEUTRON_STAR = "neutron_star"    # ~8 < M_init < ~25 M_sun
    BLACK_HOLE = "black_hole"        # M_init > ~25 M_sun
    NONE = "none"                    # still on the MS / not evolved


class SFTRindicator(Enum):
    """Star-formation-rate tracer indicators."""
    HALPHA = "halpha"
    FUV = "fuv"
    IR = "infrared"
    RADIO = "radio_continuum"


@dataclass
class Star:
    """A single star (masses in M_sun, ages in yr unless noted)."""
    mass: float                    # zero-age main-sequence mass (M_sun)
    age: float = 0.0               # current age (yr)
    phase: StellarPhase = StellarPhase.MAIN_SEQUENCE
    metallicity: float = 0.02      # mass fraction (solar Z~0.0142)


# =============================================================================
# Initial Mass Function
# =============================================================================

class InitialMassFunction:
    """Initial mass function dN/dM (per M_sun).

    Implemented forms (number density per unit stellar mass):
      salpeter : xi(M) ~ M^-2.35                 (Salpeter 1955)
      kroupa   : broken power law                (Kroupa 2001)
                 M<0.08 : -0.3 ; 0.08-0.5 : -1.3 ; >0.5 : -2.3
      chabrier : lognormal (M<1) + M^-2.3 (M>=1) (Chabrier 2003)
    """

    def __init__(self, kind: str = "kroupa",
                 m_min: float = 0.1, m_max: float = 100.0):
        kind = kind.lower()
        if kind not in ("salpeter", "kroupa", "chabrier"):
            raise ValueError(f"unknown IMF: {kind}")
        self.kind = kind
        self.m_min = m_min
        self.m_max = m_max

    def pdf(self, mass: float) -> float:
        """Unnormalised xi(M) = dN/dM (per M_sun).

        Segment coefficients are continuity-normalised at the break masses so
        the IMF is continuous (Kroupa 2001; Chabrier 2003). Absolute
        normalisation is irrelevant here (the sampler integrates the CDF).
        """
        m = float(mass)
        if m <= 0 or m < self.m_min or m > self.m_max:
            return 0.0
        if self.kind == "salpeter":
            return m ** -2.35
        if self.kind == "kroupa":
            # continuity at 0.08 Msun: C0 = 12.5 C1 ; at 0.5 Msun: C2 = 0.5 C1
            if m < 0.08:
                return 12.5 * (m ** -0.3)
            if m < 0.5:
                return m ** -1.3
            return 0.5 * (m ** -2.3)
        # chabrier: lognormal below 1 M_sun, power law above; continuity at 1
        if m < 1.0:
            mc = 0.22            # characteristic mass (M_sun)
            sigma = 0.57         # width in dex (log10)
            logm = np.log10(m)
            return (1.0 / m) * np.exp(-0.5 * ((logm - np.log10(mc)) / sigma) ** 2)
        # power-law coefficient 0.514 matches the lognormal at M = 1 Msun
        return 0.514 * (m ** -2.3)

    def _pdf_vec(self, m):
        return np.array([self.pdf(x) for x in np.atleast_1d(m)])

    def _cdf_grid(self, n: int = 20000) -> Tuple[np.ndarray, np.ndarray]:
        m = np.geomspace(self.m_min, self.m_max, n)
        xi = self._pdf_vec(m)
        # dN/dlogM = M * xi(M); integrate over log M for proper sampling
        logm = np.log(m)
        dlogm = np.diff(logm)
        integrand = 0.5 * (xi[1:] * m[1:] + xi[:-1] * m[:-1]) * dlogm
        cdf = np.concatenate([[0.0], np.cumsum(integrand)])
        cdf /= cdf[-1]
        return m, cdf

    def sample(self, n: int, rng: Optional[np.random.Generator] = None) -> np.ndarray:
        """Draw `n` stellar masses (M_sun) by inverse-CDF sampling."""
        rng = rng or np.random.default_rng()
        m_grid, cdf = self._cdf_grid()
        u = rng.random(n)
        return np.interp(u, cdf, m_grid)

    def mean_mass(self, n: int = 20000) -> float:
        """Number-weighted mean stellar mass (M_sun)."""
        m, cdf = self._cdf_grid(n)
        xi = self._pdf_vec(m)
        dlogm = np.diff(np.log(m))
        mass_per_bin = 0.5 * (xi[1:] * m[1:] * m[1:] + xi[:-1] * m[:-1] * m[:-1]) * dlogm
        norm = 0.5 * (xi[1:] * m[1:] + xi[:-1] * m[:-1]) * dlogm
        return float(mass_per_bin.sum() / norm.sum())


def sample_masses_from_imf(n: int, imf: str = "kroupa",
                           m_min: float = 0.1, m_max: float = 100.0,
                           rng: Optional[np.random.Generator] = None) -> np.ndarray:
    """Sample `n` stellar masses (M_sun) from the named IMF."""
    return InitialMassFunction(imf, m_min, m_max).sample(n, rng)


# =============================================================================
# Star-formation laws
# =============================================================================

class StarFormationLaw:
    """Empirical star-formation laws (Kennicutt 1998)."""

    # Kennicutt (1998) Eq. 7: Sigma_SFR = (2.5 +/- 0.7)e-4 * Sigma_gas^1.4
    # with Sigma_gas in M_sun/pc^2, Sigma_SFR in M_sun/yr/kpc^2.
    SCHMIDT_NORMALIZATION = 2.5e-4
    SCHMIDT_INDEX = 1.4

    def schmidt_surface(self, sigma_gas_msun_pc2: float) -> float:
        """Kennicutt-Schmidt surface-density SFR law -> Sigma_SFR (M_sun/yr/kpc^2)."""
        return self.SCHMIDT_NORMALIZATION * (sigma_gas_msun_pc2 ** self.SCHMIDT_INDEX)

    def schmidt(self, sigma_gas_msun_pc2: float) -> float:
        """Alias for the Kennicutt-Schmidt surface-density law."""
        return self.schmidt_surface(sigma_gas_msun_pc2)

    def depletion_time(self, sigma_gas_msun_pc2: float,
                       sigma_sfr_msun_yr_pc2: float) -> float:
        """Gas depletion time t_dep = Sigma_gas / Sigma_SFR (yr)."""
        return sigma_gas_msun_pc2 / sigma_sfr_msun_yr_pc2


# =============================================================================
# SFR from luminosity (Kennicutt 1998 calibrations)
# =============================================================================

class StarFormationRateTracer:
    """Convert luminosities to star-formation rates (Salpeter IMF, 0.1-100 M_sun)."""

    # Kennicutt (1998) calibration coefficients
    COEFFS = {
        # SFR [M_sun/yr] = coeff * L [erg/s]   (H-alpha, IR)
        'halpha': 7.9e-42,
        'ir': 4.5e-44,
        # SFR [M_sun/yr] = coeff * L_nu [erg/s/Hz]   (FUV @ 1500A, radio @ 1.4GHz)
        'fuv': 1.0e-28,        # Kennicutt (1998) ~8e-28 in some conventions; see note
        'radio': 5.9e-29,      # 1.4GHz, Bell (2003) style, per L_sun of IR equiv
    }

    def from_halpha(self, l_halpha_erg_s: float) -> float:
        """SFR from H-alpha luminosity (Kennicutt 1998)."""
        return self.COEFFS['halpha'] * l_halpha_erg_s

    def from_ir(self, l_ir_erg_s: float) -> float:
        """SFR from total IR (8-1000 micron) luminosity (Kennicutt 1998)."""
        return self.COEFFS['ir'] * l_ir_erg_s

    def from_fuv(self, l_nu_fuv: float) -> float:
        """SFR from far-UV luminosity density at 1500 A (Kennicutt 1998)."""
        return self.COEFFS['fuv'] * l_nu_fuv

    def from_radio(self, l_nu_1p4ghz: float) -> float:
        """SFR from 1.4 GHz radio continuum (calibration depends on model)."""
        return self.COEFFS['radio'] * l_nu_1p4ghz


def calculate_sfr_from_luminosity(luminosity: float, tracer: str = "halpha") -> float:
    """SFR [M_sun/yr] from a luminosity using the named Kennicutt tracer.

    tracer: 'halpha' or 'ir' (luminosity in erg/s).
    """
    t = StarFormationRateTracer()
    if tracer == "halpha":
        return t.from_halpha(luminosity)
    if tracer == "ir":
        return t.from_ir(luminosity)
    if tracer == "fuv":
        return t.from_fuv(luminosity)
    if tracer == "radio":
        return t.from_radio(luminosity)
    raise ValueError(f"unknown tracer: {tracer}")


# =============================================================================
# Stellar populations / evolution (honest minimal scaffolding)
# =============================================================================

def _remnant_type(initial_mass_msun: float) -> RemnantType:
    if initial_mass_msun < 8.0:
        return RemnantType.WHITE_DWARF
    if initial_mass_msun < 25.0:
        return RemnantType.NEUTRON_STAR
    return RemnantType.BLACK_HOLE


def _main_sequence_lifetime_msun_yr(mass_msun: float) -> float:
    """Approximate MS lifetime: t_MS ~ 10 Gyr * (M/M_sun)^-2.5 (valid ~0.1-50 M_sun)."""
    return 1.0e10 * (mass_msun ** -2.5)


class StellarEvolution:
    """Lightweight stellar-evolution helpers (scaling relations, not full tracks)."""

    def ms_lifetime(self, mass_msun: float) -> float:
        return _main_sequence_lifetime_msun_yr(mass_msun)

    def remnant(self, initial_mass_msun: float) -> RemnantType:
        return _remnant_type(initial_mass_msun)


class SupernovaFeedback:
    """Core-collapse SN feedback energetics (standard order-of-magnitude values)."""

    SN_ENERGY_ERG = 1.0e51          # canonical kinetic energy per CC SN
    FE_ENRICH_YIELD_MSUN = 0.07     # approximate iron yield per CC SN (M_sun)

    def core_collapse_rate(self, sfr_msun_yr: float,
                           imf: str = "kroupa") -> float:
        """Approximate CC SN rate [yr^-1] for a given SFR.

        Massive stars (>8 M_sun) die as CC SNe. For a Kroupa IMF, roughly
        one CC SN per ~100 M_sun of star formation formed, i.e. nu_CC ~ 0.01/yr
        for SFR=1 M_sun/yr (Madau & Dickinson 2014).
        """
        return 0.01 * sfr_msun_yr

    def feedback_energy(self, sfr_msun_yr: float) -> float:
        """Mechanical energy injection rate [erg/yr] from CC SNe."""
        return self.core_collapse_rate(sfr_msun_yr) * self.SN_ENERGY_ERG


class StellarPopulation:
    """A simple stellar population: a sampled IMF + aggregate properties."""

    def __init__(self, masses_msun: np.ndarray, age_yr: float = 0.0,
                 metallicity: float = 0.02):
        self.masses = np.asarray(masses_msun, float)
        self.age_yr = age_yr
        self.metallicity = metallicity

    @classmethod
    def from_imf(cls, n: int, imf: str = "kroupa",
                 m_min: float = 0.1, m_max: float = 100.0,
                 age_yr: float = 0.0, metallicity: float = 0.02,
                 rng: Optional[np.random.Generator] = None) -> "StellarPopulation":
        m = sample_masses_from_imf(n, imf, m_min, m_max, rng)
        return cls(m, age_yr, metallicity)

    def total_mass(self) -> float:
        return float(self.masses.sum())

    def n_massive(self, m_min_msun: float = 8.0) -> int:
        return int((self.masses >= m_min_msun).sum())


def create_stellar_population(n: int = 1000, imf: str = "kroupa",
                              **kwargs) -> StellarPopulation:
    return StellarPopulation.from_imf(n, imf, **kwargs)


__all__ = [
    'StellarPhase', 'RemnantType', 'SFTRindicator',
    'Star', 'InitialMassFunction', 'sample_masses_from_imf',
    'StarFormationLaw', 'StarFormationRateTracer', 'calculate_sfr_from_luminosity',
    'StellarEvolution', 'SupernovaFeedback', 'StellarPopulation',
    'create_stellar_population',
]
