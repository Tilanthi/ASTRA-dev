#!/usr/bin/env python3

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
ASTRA Physics Constants
========================

Centralized physical constants with proper units and documentation.
All code should import constants from this file to ensure consistency.

Units: CGS unless otherwise noted
Date: 2026-04-11
"""

import numpy as np

# =============================================================================
# FUNDAMENTAL CONSTANTS (CGS)
# =============================================================================

# Speed of light
C_LIGHT = 2.99792458e10  # cm/s (exact)

# Planck constant
H_PLANCK = 6.62607015e-27  # erg·s (exact)

# Reduced Planck constant
H_BAR = H_PLANCK / (2 * np.pi)  # erg·s

# Gravitational constant
G = 6.67430e-8  # cm³/g/s²

# Boltzmann constant
K_B = 1.380649e-16  # erg/K

# Electron charge
E_CHARGE = 4.80320471e-10  # statC (esu)

# Electron mass
M_E = 9.10938370e-28  # g

# Proton mass
M_P = 1.67262192e-24  # g

# Atomic mass unit
AMU = 1.66053907e-24  # g

# Avogadro's number
N_AVOGADRO = 6.02214076e23  # mol⁻¹

# Stefan-Boltzmann constant
SIGMA_SB = 5.67037442e-5  # erg/cm²/s/K⁴

# Radiation constant (a = 4σ/c)
A_RAD = 4 * SIGMA_SB / C_LIGHT  # erg/cm³/K⁴

# Fine-structure constant
ALPHA_FS = E_CHARGE**2 / (H_BAR * C_LIGHT)  # dimensionless ≈ 1/137

# =============================================================================
# ASTROPHYSICAL CONSTANTS
# =============================================================================

# Solar mass
M_SUN = 1.98847e33  # g
M_SUN_KG = 1.98847e30  # kg

# Solar radius
R_SUN = 6.957e10  # cm
R_SUN_KM = 6.957e5  # km

# Solar luminosity
L_SUN = 3.826e33  # erg/s
L_SUN_WATTS = 3.826e26  # W

# Solar effective temperature
T_SUN = 5772  # K

# Astronomical Unit
AU = 1.495978707e13  # cm
AU_KM = 1.495978707e8  # km

# Parsec
PC = 3.08567758e18  # cm
PC_KM = 3.08567758e13  # km
PC_KPC = 1e3  # kpc per parsec (unit conversion)

# Kiloparsec
KPC = PC * 1e3  # cm

# Megaparsec
MPC = PC * 1e6  # cm

# Year (Julian)
YEAR_SEC = 3.15576e7  # s
YEAR_DAYS = 365.25  # days

# =============================================================================
# INTERSTELLAR MEDIUM (ISM) CONSTANTS
# =============================================================================

# Mean molecular weight (μ)
# These values account for H, He, and metals in different ionization states
#
# References:
# - Draine 2011, "Physics of the Interstellar and Intergalactic Medium"
# - Kauffmann et al. 2008 for molecular clouds

# Fully ionized gas (H II regions, hot ISM)
# For H: μ ≈ 0.6 (mean particle mass in units of m_H)
# Accounts for: ionized H, singly ionized He, free electrons
MU_IONIZED = 0.6  # dimensionless (m_H / m_p)

# Neutral atomic gas (H I regions)
# For H: μ ≈ 1.3
# Accounts for: H, He, no ionization
MU_ATOMIC = 1.3  # dimensionless

# Molecular gas (H₂ regions)
# For H₂: μ ≈ 2.3-2.8 depending on He ionization and metallicity
# Standard value: 2.3 for H₂ + He with 10% He by number
MU_MOLECULAR = 2.3  # dimensionless

# Default value for general ISM calculations
MU_DEFAULT = MU_MOLECULAR

# Mass of hydrogen atom (for convenience)
M_H = 1.6735575e-24  # g
M_H_AMU = 1.00794  # amu

# Mass of H₂ molecule
M_H2 = 2 * M_H  # g

# Typical ISM conditions
T_ISM_TYPICAL = 100  # K (warm neutral medium)
T_CLOUD_TYPICAL = 10  # K (cold molecular cloud)
N_H_TYPICAL = 20  # cm⁻³ (atomic ISM)
N_H2_TYPICAL = 100  # cm⁻³ (molecular cloud)

# =============================================================================
# DUST PROPERTIES
# =============================================================================

# Dust-to-gas mass ratio (solar metallicity)
DUST_TO_GAS_SOLAR = 0.01  # 1% by mass

# Reference dust opacities at λ = 350 μm (Hildebrand 1983)
KAPPA_DUST_350UM = 10.0  # cm²/g (dust)

# Planck Collaboration 2013 values at 353 GHz (850 μm)
KAPPA_DUST_850UM_PLANCK = 0.92  # cm²/g (dust + gas)
KAPPA_DUST_850UM_PLANCK_BETA = 1.62  # Power-law index

# Ossenkopf & Henning (1994) values for coagulated thin mantle dust
KAPPA_DUST_350UM_OH94_THIN = 10.0  # cm²/g at 350 μm
KAPPA_DUST_350UM_OH94_THICK = 4.0  # cm²/g at 350 μm

# =============================================================================
# COSMOLOGY
# =============================================================================

# Hubble constant (km/s/Mpc) - Planck 2018
H0_PLANCK = 67.4  # km/s/Mpc
H0_PLANCK_ERR = 0.5  # km/s/Mpc

# Hubble constant in s⁻¹
H0_S = H0_PLANCK * 1e3 / (MPC / 1e2)  # s⁻¹

# Critical density (g/cm³)
RHO_CRITICAL = 3 * H0_S**2 / (8 * np.pi * G)

# Matter density parameter
OMEGA_M = 0.315

# Dark energy density parameter
OMEGA_LAMBDA = 0.685

# =============================================================================
# CONVERSION FACTORS
# =============================================================================

# Flux density conversions
JANSKY = 1e-23  # erg/s/cm²/Hz
MJANSKY = 1e-29  # erg/s/cm²/Hz
MICROJANSKY = 1e-32  # erg/s/cm²/Hz

# Luminosity conversions
L_SOLAR = L_SUN  # erg/s
L_EDDINGTON_RATIO = 1.26e38  # erg/s per M_sun (for pure H)

# Temperature conversions
EV_TO_K = 1.16045e4  # 1 eV = 11605 K

# Distance modulus to parsecs: d = 10^(DM/5 + 1)

# =============================================================================
# HELPER FUNCTIONS
# =============================================================================

def mean_molecular_weight(ionization_state: str = "molecular") -> float:
    """
    Get appropriate mean molecular weight for gas.

    Parameters
    ----------
    ionization_state : str
        - "ionized": H II regions, hot gas (μ ≈ 0.6)
        - "atomic": H I regions (μ ≈ 1.3)
        - "molecular": H₂ clouds (μ ≈ 2.3)
        - "default": Use molecular (μ ≈ 2.3)

    Returns
    -------
    float
        Mean molecular weight (dimensionless, in units of m_p)

    Examples
    --------
    >>> mean_molecular_weight("ionized")
    0.6
    >>> mean_molecular_weight("molecular")
    2.3
    """
    states = {
        "ionized": MU_IONIZED,
        "atomic": MU_ATOMIC,
        "molecular": MU_MOLECULAR,
        "default": MU_DEFAULT,
    }
    return states.get(ionization_state.lower(), MU_DEFAULT)


def dust_opacity(wavelength_um: float,
                  model: str = "planck",
                  kappa_ref: float = None,
                  beta: float = None) -> float:
    """
    Calculate dust opacity at a given wavelength.

    κ_ν = κ_ref * (λ_ref / λ)^β

    Parameters
    ----------
    wavelength_um : float
        Wavelength in micrometers
    model : str
        - "planck": Planck Collaboration 2013 (κ=0.92 at 850 μm, β=1.62)
        - "oh94_thin": Ossenkopf & Henning 1994, thin ice mantles (κ=10 at 350 μm)
        - "oh94_thick": Ossenkopf & Henning 1994, thick ice mantles (κ=4 at 350 μm)
        - "custom": Use provided kappa_ref and beta
    kappa_ref : float, optional
        Reference opacity for custom model (cm²/g)
    beta : float, optional
        Power-law index for custom model

    Returns
    -------
    float
        Dust opacity in cm²/g (dust + gas)

    Examples
    --------
    >>> dust_opacity(850)  # Planck at 850 μm
    0.92
    >>> dust_opacity(350, model="oh94_thin")
    10.0
    """
    if model == "planck":
        kappa_ref = KAPPA_DUST_850UM_PLANCK
        beta = KAPPA_DUST_850UM_PLANCK_BETA
        lambda_ref = 850.0  # μm
    elif model == "oh94_thin":
        kappa_ref = KAPPA_DUST_350UM_OH94_THIN
        beta = 1.5  # Typical value for OH94 thin mantles
        lambda_ref = 350.0  # μm
    elif model == "oh94_thick":
        kappa_ref = KAPPA_DUST_350UM_OH94_THICK
        beta = 2.0  # Typical value for OH94 thick mantles
        lambda_ref = 350.0  # μm
    elif model == "custom":
        if kappa_ref is None or beta is None:
            raise ValueError("Custom model requires kappa_ref and beta parameters")
        lambda_ref = 850.0  # Default reference
    else:
        raise ValueError(f"Unknown dust model: {model}")

    return kappa_ref * (lambda_ref / wavelength_um) ** beta


def get_constants_summary() -> dict:
    """Return summary of all constants for debugging/documentation."""
    return {
        "fundamental": {
            "c_light_cm_s": C_LIGHT,
            "h_planck_erg_s": H_PLANCK,
            "G_cgs": G,
            "k_B_erg_K": K_B,
        },
        "solar": {
            "M_sun_g": M_SUN,
            "R_sun_cm": R_SUN,
            "L_sun_erg_s": L_SUN,
            "T_sun_K": T_SUN,
        },
        "distance": {
            "AU_cm": AU,
            "pc_cm": PC,
            "kpc_cm": KPC,
            "Mpc_cm": MPC,
        },
        "molecular_weight": {
            "ionized": MU_IONIZED,
            "atomic": MU_ATOMIC,
            "molecular": MU_MOLECULAR,
        },
        "dust": {
            "kappa_850um_planck": KAPPA_DUST_850UM_PLANCK,
            "beta_planck": KAPPA_DUST_850UM_PLANCK_BETA,
        },
        "cosmology": {
            "H0_km_s_Mpc": H0_PLANCK,
            "Omega_m": OMEGA_M,
            "Omega_lambda": OMEGA_LAMBDA,
        },
    }


# =============================================================================
# MODULE INITIALIZATION
# =============================================================================

if __name__ == "__main__":
    # Print constants summary when run directly
    import json
    print(json.dumps(get_constants_summary(), indent=2))
