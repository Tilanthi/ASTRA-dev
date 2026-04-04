"""
Cosmological Context Module

Galaxy-halo connection, environmental metrics, and large-scale structure.
Includes halo mass functions, HOD models, and CGM modeling.

Date: 2025-12-15
"""

import numpy as np
from typing import List, Dict, Optional, Any, Tuple, Callable
from dataclasses import dataclass, field
from enum import Enum
from abc import ABC, abstractmethod
import warnings

# Physical constants and cosmological parameters
C_LIGHT = 2.998e5  # km/s
H0_FIDUCIAL = 70.0  # km/s/Mpc
OMEGA_M = 0.3
OMEGA_L = 0.7
OMEGA_B = 0.045
SIGMA_8 = 0.8
N_S = 0.96
RHO_CRIT_0 = 2.775e11  # M_sun/Mpc^3 * h^2


@dataclass
class CosmologyParams:
    """Cosmological parameters"""
    H0: float = 70.0  # km/s/Mpc
    Omega_m: float = 0.3
    Omega_L: float = 0.7
    Omega_b: float = 0.045
    sigma_8: float = 0.8
    n_s: float = 0.96

    @property
    def h(self) -> float:
        return self.H0 / 100.0


@dataclass
class HaloProperties:
    """Dark matter halo properties"""
    M_vir: float  # Virial mass (M_sun)
    R_vir: float  # Virial radius (kpc)
    c: float  # Concentration
    z: float  # Redshift
    M_star: float = 0.0  # Stellar mass
    SFR: float = 0.0  # Star formation rate


# =============================================================================
# HALO MASS FUNCTION
# =============================================================================

class HaloMassFunction:
    """
    Halo mass function calculations.

    Supports Press-Schechter, Sheth-Tormen, and Tinker mass functions.
    """

    def __init__(self, cosmo: CosmologyParams = None):
        """
        Initialize halo mass function.

        Args:
            cosmo: Cosmological parameters
        """
        self.cosmo = cosmo or CosmologyParams()

    def sigma(self, M: np.ndarray, z: float = 0) -> np.ndarray:
        """
        Calculate RMS density fluctuation in spheres of mass M.

        Args:
            M: Mass array (M_sun)
            z: Redshift

        Returns:
            sigma(M) array
        """
        # Simplified: sigma ~ M^(-1/6) for CDM
        # Normalize to sigma_8 at 8 h^-1 Mpc

        M_8 = 4/3 * np.pi * (8 / self.cosmo.h)**3 * \
              self.cosmo.Omega_m * RHO_CRIT_0

        sigma = self.cosmo.sigma_8 * (M / M_8)**(-1/6)

        # Growth factor
        D_z = self.growth_factor(z)
        sigma *= D_z

        return sigma

    def growth_factor(self, z: float) -> float:
        """
        Calculate linear growth factor D(z).

        Args:
            z: Redshift

        Returns:
            D(z) normalized to D(0) = 1
        """
        # Approximate growth factor for flat LCDM
        a = 1 / (1 + z)
        Om_z = self.cosmo.Omega_m * (1 + z)**3 / \
               (self.cosmo.Omega_m * (1 + z)**3 + self.cosmo.Omega_L)

        D = a * (Om_z / self.cosmo.Omega_m)**0.55 * \
            (1 + (1 - Om_z) / 70)

        return D

    def nu(self, M: np.ndarray, z: float = 0) -> np.ndarray:
        """
        Calculate peak height nu = delta_c / sigma.

        Args:
            M: Mass array
            z: Redshift

        Returns:
            nu array
        """
        delta_c = 1.686  # Critical overdensity
        return delta_c / self.sigma(M, z)

    def press_schechter(self, M: np.ndarray, z: float = 0) -> np.ndarray:
        """
        Press-Schechter mass function.

        dn/dln(M) = (rho_m / M) * f(nu) * |d ln sigma / d ln M|

        Args:
            M: Mass array (M_sun)
            z: Redshift

        Returns:
            dn/dln(M) (Mpc^-3)
        """
        nu = self.nu(M, z)

        # f(nu) for PS
        f_nu = np.sqrt(2 / np.pi) * nu * np.exp(-nu**2 / 2)

        # d ln sigma / d ln M ~ -1/6 for CDM
        dlns_dlnM = -1/6

        # Mean matter density
        rho_m = self.cosmo.Omega_m * RHO_CRIT_0 * self.cosmo.h**2 * \
                (1 + z)**3

        return rho_m / M * f_nu * np.abs(dlns_dlnM)

    def sheth_tormen(self, M: np.ndarray, z: float = 0,
                     a: float = 0.707, p: float = 0.3) -> np.ndarray:
        """
        Sheth-Tormen mass function.

        Better fit to N-body simulations than PS.

        Args:
            M: Mass array
            z: Redshift
            a, p: ST parameters

        Returns:
            dn/dln(M) (Mpc^-3)
        """
        nu = self.nu(M, z)

        # Normalization
        A = 0.3222

        # f(nu) for ST
        f_nu = A * np.sqrt(2 * a / np.pi) * nu * \
               (1 + (a * nu**2)**(-p)) * np.exp(-a * nu**2 / 2)

        dlns_dlnM = -1/6
        rho_m = self.cosmo.Omega_m * RHO_CRIT_0 * self.cosmo.h**2 * (1 + z)**3

        return rho_m / M * f_nu * np.abs(dlns_dlnM)

    def tinker(self, M: np.ndarray, z: float = 0, Delta: int = 200) -> np.ndarray:
        """
        Tinker et al. (2008) mass function.

        Calibrated to simulations at various overdensities.

        Args:
            M: Mass array
            z: Redshift
            Delta: Overdensity definition

        Returns:
            dn/dln(M) (Mpc^-3)
        """
        # Tinker parameters for Delta=200
        params = {
            200: (0.186, 1.47, 2.57, 1.19),
            300: (0.200, 1.52, 2.25, 1.27),
            400: (0.212, 1.56, 2.05, 1.34),
            800: (0.248, 1.63, 1.58, 1.41),
        }

        if Delta not in params:
            Delta = 200

        A0, a0, b0, c0 = params[Delta]

        # Redshift evolution
        A = A0 * (1 + z)**(-0.14)
        a = a0 * (1 + z)**(-0.06)
        b = b0 * (1 + z)**(-np.exp(-(0.75 / np.log10(Delta/75))**1.2))
        c = c0

        sigma = self.sigma(M, z)

        f_sigma = A * ((sigma / b)**(-a) + 1) * np.exp(-c / sigma**2)

        dlns_dlnM = -1/6
        rho_m = self.cosmo.Omega_m * RHO_CRIT_0 * self.cosmo.h**2 * (1 + z)**3

        return rho_m / M * f_sigma * np.abs(dlns_dlnM)

    def cumulative_number_density(self, M_min: float, z: float = 0,
                                   mf_type: str = 'tinker') -> float:
        """
        Calculate cumulative halo number density n(>M).

        Args:
            M_min: Minimum mass (M_sun)
            z: Redshift
            mf_type: Mass function type

        Returns:
            Number density (Mpc^-3)
        """
        M = np.logspace(np.log10(M_min), 16, 100)

        if mf_type == 'press_schechter':
            dndlnM = self.press_schechter(M, z)
        elif mf_type == 'sheth_tormen':
            dndlnM = self.sheth_tormen(M, z)
        else:
            dndlnM = self.tinker(M, z)

        # Integrate
        return np.trapz(dndlnM, np.log(M))


# =============================================================================
# GALAXY-HALO CONNECTION
# =============================================================================

class GalaxyHaloConnection:
    """
    Models for the galaxy-halo connection.

    Includes abundance matching and HOD models.
    """

    def __init__(self, cosmo: CosmologyParams = None):
        """
        Initialize galaxy-halo connection model.

        Args:
            cosmo: Cosmological parameters
        """
        self.cosmo = cosmo or CosmologyParams()
        self.hmf = HaloMassFunction(cosmo)

    def stellar_mass_halo_mass(self, M_halo: np.ndarray, z: float = 0,
                               model: str = 'behroozi') -> np.ndarray:
        """
        Stellar mass - halo mass relation.

        Args:
            M_halo: Halo mass (M_sun)
            z: Redshift
            model: 'behroozi' or 'moster'

        Returns:
            Stellar mass (M_sun)
        """
        if model == 'behroozi':
            # Behroozi et al. (2013) parameterization
            M1 = 10**(11.514 - 0.1 * z)  # Characteristic halo mass
            epsilon = 0.023 * (1 + z)**(-0.5)  # Normalization
            alpha = -1.779 - 0.1 * z  # Low-mass slope
            delta = 4.394  # High-mass slope modifier
            gamma = 0.547  # Transition width

            x = M_halo / M1

            # Double power-law
            M_star = epsilon * M1 * (x**alpha + x**(alpha * delta))**(-1/delta)

        elif model == 'moster':
            # Moster et al. (2013)
            M1 = 10**(11.59 + 1.195 * z / (1 + z))
            N = 0.0351 - 0.0247 * z / (1 + z)
            beta = 1.376 - 0.826 * z / (1 + z)
            gamma = 0.608 + 0.329 * z / (1 + z)

            M_star = M_halo * 2 * N / ((M_halo / M1)**(-beta) +
                                       (M_halo / M1)**gamma)

        else:
            raise ValueError(f"Unknown model: {model}")

        return M_star

    def hod_central(self, M_halo: np.ndarray, M_min: float = 1e11,
                    sigma_logM: float = 0.2) -> np.ndarray:
        """
        HOD central galaxy occupation.

        Args:
            M_halo: Halo mass array
            M_min: Minimum halo mass for centrals
            sigma_logM: Scatter in log(M)

        Returns:
            Mean number of centrals
        """
        # Error function step
        from scipy.special import erf
        return 0.5 * (1 + erf((np.log10(M_halo) - np.log10(M_min)) /
                             (np.sqrt(2) * sigma_logM)))

    def hod_satellite(self, M_halo: np.ndarray, M1: float = 1e12,
                      alpha: float = 1.0, M_cut: float = 1e11) -> np.ndarray:
        """
        HOD satellite galaxy occupation.

        Args:
            M_halo: Halo mass array
            M1: Characteristic mass for satellites
            alpha: Power-law slope
            M_cut: Cutoff mass

        Returns:
            Mean number of satellites
        """
        N_cen = self.hod_central(M_halo)

        # Power-law with cutoff
        N_sat = N_cen * ((M_halo - M_cut) / M1)**alpha
        N_sat = np.where(M_halo > M_cut, N_sat, 0)

        return N_sat

    def abundance_matching(self, M_star_min: float, z: float = 0) -> float:
        """
        Infer halo mass from stellar mass using abundance matching.

        Args:
            M_star_min: Stellar mass threshold (M_sun)
            z: Redshift

        Returns:
            Corresponding halo mass (M_sun)
        """
        # Iterative matching
        M_halo_test = np.logspace(10, 15, 100)
        M_star_test = self.stellar_mass_halo_mass(M_halo_test, z)

        # Find where M_star = M_star_min
        M_halo = np.interp(M_star_min, M_star_test, M_halo_test)

        return M_halo

    def concentration_mass_relation(self, M_halo: np.ndarray,
                                    z: float = 0) -> np.ndarray:
        """
        NFW concentration-mass relation.

        Args:
            M_halo: Halo mass array
            z: Redshift

        Returns:
            Concentration array
        """
        # Dutton & Maccio (2014)
        a = 0.520 + (0.905 - 0.520) * np.exp(-0.617 * z**1.21)
        b = -0.101 + 0.026 * z

        log_c = a + b * (np.log10(M_halo) - 12)

        return 10**log_c


# =============================================================================
# ENVIRONMENTAL METRICS
# =============================================================================

class EnvironmentalMetrics:
    """
    Galaxy environment characterization metrics.
    """

    def __init__(self):
        """Initialize environmental metrics"""
        pass

    def local_density(self, positions: np.ndarray,
                      n_neighbors: int = 5) -> np.ndarray:
        """
        Calculate local galaxy density using N-th nearest neighbor.

        Args:
            positions: Galaxy positions (N, 3) in Mpc
            n_neighbors: Number of neighbors to consider

        Returns:
            Local density (Mpc^-3)
        """
        from scipy.spatial import cKDTree

        tree = cKDTree(positions)

        # Query for n_neighbors+1 (including self)
        distances, _ = tree.query(positions, k=n_neighbors + 1)

        # Volume to n-th neighbor
        r_n = distances[:, n_neighbors]
        V = 4/3 * np.pi * r_n**3

        # Density
        return n_neighbors / V

    def overdensity(self, positions: np.ndarray, n_neighbors: int = 5,
                    mean_density: float = None) -> np.ndarray:
        """
        Calculate local overdensity delta = rho/rho_mean - 1.

        Args:
            positions: Galaxy positions
            n_neighbors: Number of neighbors
            mean_density: Mean density (calculated if None)

        Returns:
            Overdensity array
        """
        rho = self.local_density(positions, n_neighbors)

        if mean_density is None:
            mean_density = np.median(rho)

        return rho / mean_density - 1

    def distance_to_filament(self, positions: np.ndarray,
                             filament_skeleton: np.ndarray) -> np.ndarray:
        """
        Calculate distance to nearest cosmic filament.

        Args:
            positions: Galaxy positions (N, 3)
            filament_skeleton: Filament points (M, 3)

        Returns:
            Distance to nearest filament point
        """
        from scipy.spatial import cKDTree

        tree = cKDTree(filament_skeleton)
        distances, _ = tree.query(positions, k=1)

        return distances

    def tidal_tensor(self, positions: np.ndarray, masses: np.ndarray,
                     target_position: np.ndarray) -> np.ndarray:
        """
        Calculate tidal tensor at target position.

        Args:
            positions: Mass positions (N, 3)
            masses: Masses (N,)
            target_position: Point to evaluate (3,)

        Returns:
            3x3 tidal tensor
        """
        G = 4.302e-6  # kpc (km/s)^2 / M_sun

        T = np.zeros((3, 3))

        for pos, mass in zip(positions, masses):
            r = target_position - pos
            r_mag = np.linalg.norm(r)

            if r_mag < 1e-10:
                continue

            # Tidal tensor contribution
            for i in range(3):
                for j in range(3):
                    T[i, j] += G * mass * (3 * r[i] * r[j] / r_mag**5 -
                                          (i == j) / r_mag**3)

        return T


# =============================================================================
# CGM MODEL
# =============================================================================

class CGMModel:
    """
    Circumgalactic medium modeling.

    Models gas distribution, temperature, and observables.
    """

    def __init__(self, M_halo: float = 1e12, z: float = 0):
        """
        Initialize CGM model.

        Args:
            M_halo: Halo mass (M_sun)
            z: Redshift
        """
        self.M_halo = M_halo
        self.z = z

        # Virial properties
        self.R_vir = self._virial_radius()
        self.T_vir = self._virial_temperature()

    def _virial_radius(self) -> float:
        """Calculate virial radius (kpc)"""
        # R_vir = (3 * M_halo / (4 * pi * Delta * rho_crit))^(1/3)
        Delta = 200
        rho_crit = RHO_CRIT_0 * 1e-9  # M_sun/kpc^3

        R = (3 * self.M_halo / (4 * np.pi * Delta * rho_crit))**(1/3)
        return R

    def _virial_temperature(self) -> float:
        """Calculate virial temperature (K)"""
        # T_vir = G * M * mu * m_p / (2 * k_B * R_vir)
        G = 4.302e-6  # kpc (km/s)^2 / M_sun
        mu = 0.6  # Ionized gas
        m_p = 1.673e-24  # g
        k_B = 1.381e-16  # erg/K

        v_vir_sq = G * self.M_halo / self.R_vir  # (km/s)^2
        T = mu * m_p * v_vir_sq * 1e10 / (2 * k_B)  # Convert km^2/s^2 to cm^2/s^2

        return T

    def gas_density_profile(self, r: np.ndarray,
                            profile: str = 'beta') -> np.ndarray:
        """
        Gas density profile.

        Args:
            r: Radius array (kpc)
            profile: 'beta' or 'NFW'

        Returns:
            Gas density (cm^-3)
        """
        if profile == 'beta':
            # Beta model
            beta = 0.5
            r_c = 0.1 * self.R_vir  # Core radius

            n_0 = 1e-3  # Central density (cm^-3)
            n = n_0 * (1 + (r / r_c)**2)**(-3 * beta / 2)

        elif profile == 'NFW':
            # Modified NFW for gas
            c = 10  # Concentration
            r_s = self.R_vir / c

            n_0 = 1e-3
            x = r / r_s
            n = n_0 / (x * (1 + x)**2)

        return n

    def temperature_profile(self, r: np.ndarray) -> np.ndarray:
        """
        Gas temperature profile.

        Args:
            r: Radius array (kpc)

        Returns:
            Temperature (K)
        """
        # Isothermal with slight gradient
        T_0 = self.T_vir
        alpha = 0.1  # Temperature gradient

        return T_0 * (r / self.R_vir)**(-alpha)

    def column_density(self, b: float, species: str = 'H') -> float:
        """
        Calculate column density at impact parameter b.

        Args:
            b: Impact parameter (kpc)
            species: 'H', 'OVI', 'CIV', etc.

        Returns:
            Column density (cm^-2)
        """
        # Integrate along line of sight
        z_los = np.linspace(-2 * self.R_vir, 2 * self.R_vir, 1000)
        r = np.sqrt(b**2 + z_los**2)

        n_gas = self.gas_density_profile(r)

        # Ionization correction (simplified)
        if species == 'H':
            f_ion = 1.0  # Fully ionized
        elif species == 'OVI':
            T = self.temperature_profile(r)
            # OVI peaks around 3e5 K
            f_ion = np.exp(-((np.log10(T) - 5.5) / 0.3)**2)
            f_ion *= 0.01  # Oxygen abundance
        else:
            f_ion = 0.01

        N = np.trapz(n_gas * f_ion, z_los * 3.086e21)  # Convert kpc to cm

        return N

    def covering_fraction(self, N_threshold: float,
                          species: str = 'H') -> float:
        """
        Calculate covering fraction above column density threshold.

        Args:
            N_threshold: Column density threshold (cm^-2)
            species: Species to consider

        Returns:
            Covering fraction (0-1)
        """
        # Sample impact parameters
        b = np.linspace(0.01 * self.R_vir, self.R_vir, 50)
        N = np.array([self.column_density(bi, species) for bi in b])

        # Area-weighted covering fraction
        A = np.pi * np.diff(b**2)
        A = np.append(np.pi * b[0]**2, A)

        covered = N > N_threshold
        f_c = np.sum(A[covered]) / np.sum(A)

        return f_c


# =============================================================================
# REIONIZATION MODEL
# =============================================================================

class ReionizationModel:
    """
    Cosmic reionization history model.
    """

    def __init__(self, cosmo: CosmologyParams = None):
        """
        Initialize reionization model.

        Args:
            cosmo: Cosmological parameters
        """
        self.cosmo = cosmo or CosmologyParams()

    def ionization_history(self, z: np.ndarray,
                           model: str = 'tanh') -> np.ndarray:
        """
        Calculate ionization fraction Q_HII(z).

        Args:
            z: Redshift array
            model: 'tanh' or 'physical'

        Returns:
            Ionization fraction array
        """
        if model == 'tanh':
            # Simple tanh model
            z_re = 7.5  # Redshift of reionization midpoint
            Delta_z = 0.5  # Width

            Q = 0.5 * (1 + np.tanh((z_re - z) / Delta_z))

        elif model == 'physical':
            # More physical: balance ionization and recombination
            # Q depends on star formation history and escape fraction

            # Simplified: exponential transition
            z_start = 15
            z_end = 6

            Q = np.where(z > z_start, 0,
                        np.where(z < z_end, 1,
                                (z_start - z) / (z_start - z_end)))

        return Q

    def optical_depth_reionization(self, z_max: float = 30) -> float:
        """
        Calculate optical depth to reionization.

        tau = integral of sigma_T * n_e * c * dt

        Args:
            z_max: Maximum redshift to integrate

        Returns:
            Optical depth
        """
        z = np.linspace(0, z_max, 1000)
        Q = self.ionization_history(z)

        # Comoving electron density
        n_e0 = self.cosmo.Omega_b * RHO_CRIT_0 * self.cosmo.h**2 / 1.67e-24
        n_e0 *= 0.875  # Hydrogen fraction

        # sigma_T
        sigma_T = 6.65e-25  # cm^2

        # dt/dz
        H_z = self.cosmo.H0 * np.sqrt(self.cosmo.Omega_m * (1 + z)**3 +
                                      self.cosmo.Omega_L)
        dtdz = -1 / ((1 + z) * H_z * 3.24e-20)  # Convert to seconds

        # Integrate
        integrand = sigma_T * n_e0 * (1 + z)**3 * Q * C_LIGHT * 1e5 * np.abs(dtdz)
        tau = np.trapz(integrand, z)

        return tau

    def uv_background(self, z: float, model: str = 'HM12') -> float:
        """
        UV background intensity.

        Args:
            z: Redshift
            model: 'HM12' for Haardt & Madau (2012)

        Returns:
            J_21 (10^-21 erg/s/cm^2/Hz/sr)
        """
        if model == 'HM12':
            # Simplified HM12 fit
            if z < 1:
                J_21 = 0.5
            elif z < 3:
                J_21 = 0.5 * np.exp(-(z - 1) / 2)
            elif z < 6:
                J_21 = 0.2 * np.exp(-(z - 3) / 1.5)
            else:
                J_21 = 0.01 * np.exp(-(z - 6) / 0.5)

        return J_21


# =============================================================================
# CONVENIENCE FUNCTIONS
# =============================================================================

def virial_mass_from_velocity(v_c: float, z: float = 0) -> float:
    """
    Estimate halo virial mass from circular velocity.

    Args:
        v_c: Circular velocity (km/s)
        z: Redshift

    Returns:
        Virial mass (M_sun)
    """
    # M_vir = v_c^3 / (10 * G * H(z))
    G = 4.302e-6  # kpc (km/s)^2 / M_sun
    H_z = H0_FIDUCIAL * np.sqrt(OMEGA_M * (1 + z)**3 + OMEGA_L)

    M_vir = v_c**3 / (10 * G * H_z * 1e-3)  # H in km/s/kpc

    return M_vir


def baryon_fraction(M_halo: float) -> float:
    """
    Estimate baryon fraction in halo.

    Args:
        M_halo: Halo mass (M_sun)

    Returns:
        f_baryon / f_cosmic
    """
    # Suppression at low masses due to reionization
    M_c = 1e10  # Characteristic suppression mass
    f = (1 + (M_c / M_halo)**2)**(-0.5)

    return f


# =============================================================================
# EXPORTS
# =============================================================================

__all__ = [
    'CosmologyParams',
    'HaloProperties',
    'HaloMassFunction',
    'GalaxyHaloConnection',
    'EnvironmentalMetrics',
    'CGMModel',
    'ReionizationModel',
    'virial_mass_from_velocity',
    'baryon_fraction',
]


