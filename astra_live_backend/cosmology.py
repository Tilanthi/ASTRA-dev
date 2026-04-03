"""
ASTRA Live — Cosmological Models
Real ΛCDM distance calculations for Hubble diagram analysis.
Replaces the crude Hubble law approximation with proper cosmology.
"""
import numpy as np
from scipy import integrate


# Planck 2018 cosmological parameters
PLANCK_2018 = {
    'H0': 67.36,       # km/s/Mpc
    'Omega_m': 0.3153,
    'Omega_L': 0.6847,
    'Omega_k': 0.0,
    'w0': -1.0,        # Dark energy equation of state
    'c': 299792.458,   # km/s
}

# SH0ES 2022 measurement
SH0ES_2022 = {
    'H0': 73.04,
    'sigma': 1.04,
}


def hubble_parameter(z: float, cosmo: dict = None) -> float:
    """H(z) in km/s/Mpc for flat ΛCDM."""
    if cosmo is None:
        cosmo = PLANCK_2018
    H0 = cosmo['H0']
    Om = cosmo['Omega_m']
    OL = cosmo['Omega_L']
    w = cosmo.get('w0', -1.0)
    return H0 * np.sqrt(Om * (1 + z)**3 + OL * (1 + z)**(3 * (1 + w)))


def e_z(z: np.ndarray, cosmo: dict = None) -> np.ndarray:
    """Dimensionless Hubble parameter E(z) = H(z)/H0."""
    if cosmo is None:
        cosmo = PLANCK_2018
    Om = cosmo['Omega_m']
    OL = cosmo['Omega_L']
    w = cosmo.get('w0', -1.0)
    return np.sqrt(Om * (1 + z)**3 + OL * (1 + z)**(3 * (1 + w)))


def comoving_distance(z: float, cosmo: dict = None, n_steps: int = 1000) -> float:
    """Line-of-sight comoving distance in Mpc."""
    if cosmo is None:
        cosmo = PLANCK_2018
    c = cosmo['c']
    H0 = cosmo['H0']

    if z <= 0:
        return 0.0

    zs = np.linspace(0, z, n_steps)
    integrand = 1.0 / e_z(zs, cosmo)
    dc = (c / H0) * np.trapz(integrand, zs)
    return dc


def luminosity_distance(z: float, cosmo: dict = None) -> float:
    """Luminosity distance in Mpc for flat universe."""
    dc = comoving_distance(z, cosmo)
    return dc * (1 + z)


def distance_modulus(z: np.ndarray, cosmo: dict = None) -> np.ndarray:
    """Distance modulus μ = 5·log₁₀(d_L/10pc) for array of redshifts."""
    if cosmo is None:
        cosmo = PLANCK_2018

    z = np.atleast_1d(z).astype(float)
    mu = np.zeros_like(z)

    for i, zi in enumerate(z):
        if zi <= 0:
            mu[i] = 0.0
            continue
        dL = luminosity_distance(zi, cosmo)  # in Mpc
        dL_pc = dL * 1e6  # convert to pc
        mu[i] = 5 * np.log10(dL_pc / 10)  # μ = 5 log₁₀(d_L / 10 pc)

    return mu


def hubble_residual(z: np.ndarray, mb_observed: np.ndarray,
                    cosmo: dict = None) -> np.ndarray:
    """Compute Hubble residuals: Δμ = μ_obs - μ_model."""
    mu_model = distance_modulus(z, cosmo)
    return mb_observed - mu_model


def fit_h0_from_sne(z: np.ndarray, mb: np.ndarray, mb_err: np.ndarray,
                     h0_range: tuple = (60, 80), n_steps: int = 200) -> tuple:
    """
    Fit H0 from Pantheon+ SNe Ia by minimizing χ² of distance modulus.
    Returns (best_H0, chi_squared, H0_uncertainty).
    """
    h0_values = np.linspace(h0_range[0], h0_range[1], n_steps)
    chi2_values = np.zeros_like(h0_values)

    for i, h0 in enumerate(h0_values):
        cosmo = PLANCK_2018.copy()
        cosmo['H0'] = h0
        mu_model = distance_modulus(z, cosmo)
        residuals = mb - mu_model
        chi2_values[i] = np.sum((residuals / mb_err)**2)

    best_idx = np.argmin(chi2_values)
    best_h0 = h0_values[best_idx]
    best_chi2 = chi2_values[best_idx]

    # Estimate uncertainty from χ² curvature
    delta_chi2 = chi2_values - best_chi2
    within_1sigma = h0_values[delta_chi2 < 1.0]
    if len(within_1sigma) > 1:
        h0_err = (within_1sigma[-1] - within_1sigma[0]) / 2
    else:
        h0_err = 0.5  # fallback

    return best_h0, best_chi2, h0_err
