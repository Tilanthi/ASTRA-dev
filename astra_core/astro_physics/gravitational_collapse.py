"""
Gravitational collapse analysis (ISM / star-formation physics).

Standard textbook formulations in CGS units. All densities are MASS densities
(g/cm^3) unless a method explicitly takes a number density `n` (cm^-3).

References:
  Jeans (1902); Bonnor (1956); Spitzer "Physical Processes in the ISM";
  Stahler & Palla "The Formation of Stars"; Bondi (1952) for Bondi accretion.

Constants (CGS):
  G      = 6.67430e-8   cm^3 g^-1 s^-2
  k_B    = 1.380649e-16 erg K^-1
  m_H    = 1.6735575e-24 g
  M_sun  = 1.98847e33   g
  pc     = 3.0856776e18 cm
"""

import math
from typing import Dict, Optional

# --- Physical constants (CGS) ---
G = 6.67430e-8           # gravitational constant
K_B = 1.380649e-16       # Boltzmann constant
M_H = 1.6735575e-24      # atomic hydrogen mass
M_SUN = 1.98847e33       # solar mass
PARSEC = 3.0856776e18    # parsec in cm

# Mean molecular weight per free particle. mu=2.33 is standard for fully
# molecular gas of cosmic composition (He/H = 0.1 by number).
MU_MOLECULAR = 2.33
MU_ATOMIC = 1.27


def _sound_speed(T: float, mu: float = MU_MOLECULAR) -> float:
    """Isothermal sound speed c_s = sqrt(k_B T / (mu m_H))  [cm/s]."""
    return math.sqrt(K_B * T / (mu * M_H))


class JeansAnalysis:
    """Jeans length / mass for thermal (isothermal) support."""

    def jeans_length_thermal(self, temperature: float, density: float,
                             mu: float = MU_MOLECULAR) -> float:
        """
        Thermal Jeans length  lambda_J = c_s * sqrt(pi / (G rho))   [cm].

        Args:
            temperature: gas temperature (K)
            density: MASS density rho (g/cm^3)
            mu: mean molecular weight (default 2.33, molecular gas)
        """
        c_s = _sound_speed(temperature, mu)
        return c_s * math.sqrt(math.pi / (G * density))

    def jeans_mass_thermal(self, temperature: float, density: float,
                           mu: float = MU_MOLECULAR) -> float:
        """
        Thermal Jeans mass  M_J = (pi^(5/2)/6) c_s^3 / (G^(3/2) rho^(1/2))  [g].

        Mass contained within a sphere of radius lambda_J/2 for a uniform
        isothermal medium of mass density `density`.

        Args:
            temperature: gas temperature (K)
            density: MASS density rho (g/cm^3)
            mu: mean molecular weight (default 2.33, molecular gas)
        """
        c_s = _sound_speed(temperature, mu)
        coeff = (math.pi ** 2.5) / 6.0  # ~2.928
        return coeff * (c_s ** 3) / ((G ** 1.5) * math.sqrt(density))

    def jeans_mass_from_number_density(self, temperature: float, n: float,
                                       mu: float = MU_MOLECULAR) -> float:
        """Jeans mass taking a NUMBER density n (cm^-3). rho = mu m_H n."""
        rho = mu * M_H * n
        return self.jeans_mass_thermal(temperature, rho, mu)

    def jeans_length_pc(self, temperature: float, density: float,
                        mu: float = MU_MOLECULAR) -> float:
        """Convenience: Jeans length in parsec."""
        return self.jeans_length_thermal(temperature, density, mu) / PARSEC

    def jeans_mass_msun(self, temperature: float, density: float,
                        mu: float = MU_MOLECULAR) -> float:
        """Convenience: Jeans mass in solar masses."""
        return self.jeans_mass_thermal(temperature, density, mu) / M_SUN


class VirialAnalysis:
    """Virial equilibrium of a self-gravitating (uniform-sphere) cloud."""

    def virial_mass(self, radius_cm: float, sigma_1d: float) -> float:
        """
        Virial mass  M_vir = 5 sigma^2 R / G   [g].

        Args:
            radius_cm: cloud radius (cm)
            sigma_1d: one-dimensional velocity dispersion (cm/s)
        """
        return 5.0 * (sigma_1d ** 2) * radius_cm / G

    def virial_parameter(self, mass_g: float, radius_cm: float,
                         sigma_1d: float) -> float:
        """
        virial parameter alpha = 5 sigma^2 R / (G M)  (dimensionless).
        alpha < ~1 => gravitationally bound; alpha > ~2 => unbound.
        """
        return 5.0 * (sigma_1d ** 2) * radius_cm / (G * mass_g)

    def virial_mass_msun(self, radius_pc: float, sigma_km_s: float) -> float:
        """Convenience: virial mass (solar masses) from radius (pc) and sigma (km/s)."""
        return self.virial_mass(radius_pc * PARSEC, sigma_km_s * 1e5) / M_SUN


class FreefallCollapse:
    """Free-fall (pressure-less) gravitational collapse timescale."""

    def freefall_time(self, density: float) -> float:
        """
        Free-fall time  t_ff = sqrt(3 pi / (16 G rho))   [s].

        Args:
            density: initial (uniform) MASS density rho (g/cm^3)
        """
        return math.sqrt(3.0 * math.pi / (16.0 * G * density))

    def freefall_time_myr(self, density: float) -> float:
        """Convenience: free-fall time in Myr."""
        return self.freefall_time(density) / (1e6 * 365.25 * 86400.0)


class FragmentationCriterion:
    """
    Jeans-type gravitational fragmentation criteria.

    A region is gravitationally unstable to fragmentation when its mass
    exceeds the local Jeans mass (Jeans number > 1).
    """

    def __init__(self):
        self._jeans = JeansAnalysis()

    def jeans_number(self, mass_g: float, temperature: float, density: float,
                     mu: float = MU_MOLECULAR) -> float:
        """Ratio M / M_J. >1 => unstable (exceeds Jeans mass)."""
        m_j = self._jeans.jeans_mass_thermal(temperature, density, mu)
        return mass_g / m_j

    def is_gravitationally_unstable(self, mass_g: float, temperature: float,
                                    density: float, mu: float = MU_MOLECULAR) -> bool:
        """True if the region's mass exceeds its Jeans mass."""
        return self.jeans_number(mass_g, temperature, density, mu) > 1.0

    def expected_core_count(self, mass_g: float, temperature: float,
                            density: float, mu: float = MU_MOLECULAR) -> float:
        """Approximate number of Jeans-mass fragments: N ~ M / M_J."""
        return self.jeans_number(mass_g, temperature, density, mu)


class AccretionRates:
    """Bondi-Hoyle-Lyttleton accretion onto a point mass."""

    def bondi_hoyle_rate(self, mass_g: float, density: float,
                         c_s: float, v_rel: float,
                         gamma: float = 1.0, lambd: float = 1.12) -> float:
        """
        Bondi accretion rate
            Mdot = 4 pi lambda (G M)^2 rho_inf / (c_s^2 + v_rel^2)^(3/2)   [g/s]

        Args:
            mass_g: accretor mass (g)
            density: ambient MASS density rho_inf (g/cm^3)
            c_s: ambient sound speed (cm/s)
            v_rel: relative bulk velocity of accretor w.r.t. gas (cm/s)
            gamma: adiabatic index (1 for isothermal); lambda is the
                   corresponding Bondi lambda (1.12 for isothermal)
            lambd: Bondi dimensionless coefficient (~1.12 isothermal, 0.25 gamma=5/3)
        """
        denom = (c_s ** 2 + v_rel ** 2) ** 1.5
        return 4.0 * math.pi * lambd * (G * mass_g) ** 2 * density / denom

    def bondi_radius(self, mass_g: float, c_s: float) -> float:
        """Bondi radius R_B = G M / c_s^2   [cm]."""
        return G * mass_g / (c_s ** 2)


# --- Factory functions (consumer-expected names) ---
def get_jeans_analyzer() -> JeansAnalysis:
    return JeansAnalysis()


def get_virial_analyzer() -> VirialAnalysis:
    return VirialAnalysis()


__all__ = [
    'JeansAnalysis', 'VirialAnalysis', 'FreefallCollapse',
    'FragmentationCriterion', 'AccretionRates',
    'get_jeans_analyzer', 'get_virial_analyzer',
    'G', 'K_B', 'M_H', 'M_SUN', 'PARSEC',
]
