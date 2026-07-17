#!/usr/bin/env python3
"""
Radiative Transfer: non-LTE molecular-line (CO) + dust continuum.

Implements:
  * CO rigid-rotor spectroscopy (level energies E_J = h B J(J+1), line
    frequencies nu(J->J-1) = 2 B J - 4 D J^3, Einstein A from the dipole
    moment).
  * Non-LTE statistical equilibrium via the RADEX escape-probability method
    (van der Tak et al. 2007, A&A 468, 627) using CO-H2 collisional rate
    coefficients. The default rate set is representative; for production work,
    load the real Yang et al. (2010, ApJ 718, 1062) / LAMDA (Schöier et al.
    2005, A&A 432, 369) table and pass it to StatisticalEquilibriumSolver.
  * Gaussian line profiles in (Rayleigh-Jeans) brightness temperature.
  * Dust continuum RT: modified-blackbody slab (Draine, "Physics of the ISM
    and Intergalactic Medium").
  * A PDR (photodissociation-region) interface with the A_V <-> N_H mapping
    (Bohlin et al. 1978) for coupling to PDR chemistry.

CGS units throughout. Line optical depth follows Mangum & Shirley (2015,
PASP 127, 266).
"""

import numpy as np
from dataclasses import dataclass
from typing import Dict, Optional

# --- Physical constants (CGS) ---
H_PLANCK = 6.62607015e-27      # erg s
K_BOLTZMANN = 1.380649e-16     # erg/K
C_LIGHT = 2.99792458e10        # cm/s
M_SUN = 1.98847e33             # g
PC = 3.0856776e18              # cm
T_CMB = 2.725                  # K (cosmic microwave background)

# --- CO molecular constants ---
CO_B = 5.7635968e10            # rotational constant B (Hz) = 57.635968 GHz
CO_D = 1.83495e5               # centrifugal distortion D (Hz) = 183.495 kHz
CO_MU_CGS = 0.1098e-18         # dipole moment (esu cm); 0.1098 D


def co_energy_K(J: int) -> float:
    """CO rigid-rotor level energy E_J / k_B (Kelvin)."""
    return (H_PLANCK * CO_B / K_BOLTZMANN) * J * (J + 1) \
        - (H_PLANCK * CO_D / K_BOLTZMANN) * (J ** 2) * (J + 1) ** 2


def co_line_frequency_Hz(J_upper: int) -> float:
    """CO rotational line frequency nu(J -> J-1) = 2 B J - 4 D J^3  (Hz)."""
    J = J_upper
    return 2.0 * CO_B * J - 4.0 * CO_D * J ** 3


def co_einstein_A(J_upper: int) -> float:
    """Einstein A(J -> J-1) for CO (s^-1).

    A = (64 pi^4 nu^3 mu^2 / (3 h c^3)) * J/(2J+1)   (cgs).
    """
    J = J_upper
    nu = co_line_frequency_Hz(J)
    honl_london = J / (2 * J + 1)
    return (64.0 * np.pi ** 4 * nu ** 3 * CO_MU_CGS ** 2) \
        / (3.0 * H_PLANCK * C_LIGHT ** 3) * honl_london


def planck_J(nu_Hz: float, T_K: float) -> float:
    """Planck function in RJ-equivalent temperature form (Kelvin):
       J(T) = (h nu / k) / (exp(h nu / k T) - 1) = B_nu c^2 / (2 k nu^2).
    """
    if T_K <= 0:
        return 0.0
    x = H_PLANCK * nu_Hz / (K_BOLTZMANN * T_K)
    if x > 700:
        return 0.0
    return (H_PLANCK * nu_Hz / K_BOLTZMANN) / np.expm1(x)


class COProperties:
    """Tabulated CO rigid-rotor properties for J = 0..J_max."""

    def __init__(self, j_max: int = 10):
        self.j_max = j_max
        self.J = np.arange(j_max + 1)
        self.energy_K = np.array([co_energy_K(int(J)) for J in self.J])
        self.g = (2 * self.J + 1).astype(float)              # degeneracy 2J+1
        self.nu = {u: co_line_frequency_Hz(u) for u in range(1, j_max + 1)}
        self.A = {u: co_einstein_A(u) for u in range(1, j_max + 1)}


def default_co_h2_rates(j_max: int = 10) -> Dict[int, float]:
    """Representative CO-H2 Delta J = -1 de-excitation rate coefficients
    q(J_upper -> J_upper-1) in cm^3/s (order-of-magnitude from LAMDA /
    Yang+2010, ~2-3e-11 cm^3/s at molecular-cloud temperatures). For research
    use, load the real Yang+2010 table instead of this placeholder set.
    """
    base = {1: 3.3e-11, 2: 2.8e-11, 3: 2.5e-11, 4: 2.2e-11, 5: 1.9e-11,
            6: 1.7e-11, 7: 1.5e-11, 8: 1.3e-11, 9: 1.1e-11, 10: 1.0e-11}
    return {u: base.get(u, 1.0e-11) for u in range(1, j_max + 1)}


class StatisticalEquilibriumSolver:
    """RADEX-style escape-probability non-LTE solver for CO.

    Statistical equilibrium with the uniform-slab escape probability
        beta(tau) = (1 - exp(-tau)) / tau
    and mean line intensity  Jbar = beta*J(T_bg) + (1-beta)*J(T_ex), iterated
    to convergence (van der Tak+ 2007).

    Args:
        T_kin:   kinetic (gas) temperature (K)
        n_H2:    H2 volume density (cm^-3)
        N_CO:    CO column density (cm^-2)
        dv_cm_s: FWHM line width (cm/s)
        T_bg:    background radiation temperature (K; default CMB)
    """

    def __init__(self, co: Optional[COProperties] = None, j_max: int = 10,
                 collision_rates: Optional[Dict[int, float]] = None):
        self.co = co or COProperties(j_max)
        self.j_max = self.co.j_max
        self.q = collision_rates or default_co_h2_rates(self.j_max)

    def _collisional_rate_matrix(self, T_kin):
        co = self.co
        C = {}
        for u in range(1, self.j_max + 1):
            l = u - 1
            q_ul = self.q[u]
            dE = co.energy_K[u] - co.energy_K[l]
            C[(u, l)] = q_ul                                  # de-excitation
            C[(l, u)] = q_ul * (co.g[u] / co.g[l]) * np.exp(-dE / T_kin)  # excitation (LTE)
        return C

    def solve(self, T_kin: float, n_H2: float, N_CO: float, dv_cm_s: float,
              T_bg: float = T_CMB, n_iter: int = 200, tol: float = 1e-7):
        co = self.co
        nJ = self.j_max + 1
        # Boltzmann initial populations at T_kin
        n = co.g * np.exp(-co.energy_K / T_kin)
        n /= n.sum()
        C = self._collisional_rate_matrix(T_kin)
        # Work in the Rayleigh-Jeans temperature convention. The stimulated
        # rate = (A/T0) * Jbar  where T0 = h nu/k and Jbar = (1-beta) J(T_ex)
        # + beta J(T_bg) (mean line intensity in K). This is equivalent to the
        # Einstein-B x specific-intensity form (B^I J_nu) and avoids mixing the
        # energy-density B with a temperature field.
        T0 = {u: H_PLANCK * co.nu[u] / K_BOLTZMANN for u in range(1, self.j_max + 1)}

        Tex, tau = {}, {}
        for _ in range(n_iter):
            beta, Jbar = {}, {}
            for u in range(1, self.j_max + 1):
                l = u - 1
                arg = (n[l] * co.g[u]) / (n[u] * co.g[l]) if n[u] > 0 else 1e300
                Tex[u] = T0[u] / np.log(arg) if arg > 1.0 else 1e-3
                N_l, N_u = n[l] * N_CO, n[u] * N_CO
                tau[u] = (co.A[u] * C_LIGHT ** 3) / (8 * np.pi * co.nu[u] ** 3 * dv_cm_s) \
                    * (N_l * co.g[u] / co.g[l] - N_u)
                t = tau[u]
                beta[u] = (1.0 - np.exp(-t)) / t if abs(t) > 1e-6 else 1.0
                Jbar[u] = ((1.0 - beta[u]) * planck_J(co.nu[u], Tex[u])
                           + beta[u] * planck_J(co.nu[u], T_bg))
            # SE linear system M n = 0  (+ normalization)
            M = np.zeros((nJ, nJ))
            for u in range(1, self.j_max + 1):
                l = u - 1
                C_ul = C[(u, l)] * n_H2
                C_lu = C[(l, u)] * n_H2
                stim_u = (co.A[u] / T0[u]) * Jbar[u]           # stimulated u -> l
                stim_l = (co.g[u] / co.g[l]) * stim_u          # absorption l -> u
                up = co.A[u] + stim_u + C_ul                   # u -> l total rate
                dn = stim_l + C_lu                             # l -> u total rate
                M[u, l] += dn
                M[u, u] -= up
                M[l, u] += up
                M[l, l] -= dn
            M[-1, :] = 1.0
            rhs = np.zeros(nJ)
            rhs[-1] = 1.0
            try:
                n_new = np.linalg.solve(M, rhs)
            except np.linalg.LinAlgError:
                break
            n_new = np.clip(n_new, 0.0, None)
            s = n_new.sum()
            if s <= 0:
                break
            n_new /= s
            if np.max(np.abs(n_new - n)) < tol:
                n = n_new
                break
            n = n_new
        return {'populations': n, 'T_ex': Tex, 'tau': tau,
                'T_kin': T_kin, 'n_H2': n_H2, 'N_CO': N_CO, 'dv': dv_cm_s}


class LineProfileSynthesizer:
    """Synthesize line intensities (brightness temperature) from a solution."""

    def __init__(self, co: Optional[COProperties] = None, j_max: int = 10):
        self.co = co or COProperties(j_max)

    def line_brightness_K(self, se_result: dict, J_upper: int) -> float:
        """Main-beam radiation temperature T_R (K) for transition J_upper -> J-1.
        T_R = [J(T_ex) - J(T_bg)] * (1 - exp(-tau))."""
        u = J_upper
        Tex = se_result['T_ex'][u]
        tau = se_result['tau'][u]
        nu = self.co.nu[u]
        return (planck_J(nu, Tex) - planck_J(nu, T_CMB)) * (1.0 - np.exp(-tau))


class DustContinuumRT:
    """Dust continuum radiative transfer: modified-blackbody isothermal slab.

    kappa_nu = kappa_0 (nu/nu_0)^beta = kappa_0 (lambda_0/lambda)^beta  (cm^2/g dust)
    (Draine, Physics of the ISM and IGM; Hildebrand 1983).
    """

    def __init__(self, kappa_0: float = 10.0, beta: float = 1.5, lambda_0_um: float = 350.0):
        self.kappa_0 = kappa_0
        self.beta = beta
        self.lambda_0 = lambda_0_um

    def opacity(self, wavelength_um: float) -> float:
        return self.kappa_0 * (wavelength_um / self.lambda_0) ** (-self.beta)

    def optical_depth(self, column_gas_msun_pc2: float, wavelength_um: float = 350.0,
                      dust_to_gas: float = 0.01) -> float:
        sigma_gas = column_gas_msun_pc2 * M_SUN / PC ** 2          # g/cm^2
        sigma_dust = sigma_gas * dust_to_gas
        return sigma_dust * self.opacity(wavelength_um)

    def brightness_K(self, T_dust: float, column_gas_msun_pc2: float,
                     wavelength_um: float = 350.0, dust_to_gas: float = 0.01) -> float:
        """Dust RJ brightness temperature (K)."""
        tau = self.optical_depth(column_gas_msun_pc2, wavelength_um, dust_to_gas)
        nu = C_LIGHT / (wavelength_um * 1e-4)
        return (planck_J(nu, T_dust) - planck_J(nu, T_CMB)) * (1.0 - np.exp(-tau))


class PDRInterface:
    """Photodissociation-region (PDR) coupling interface.

    Provides the standard A_V <-> N_H mapping (Bohlin, Savage & Drake 1978,
    ApJ 224, 132: N(H)/E(B-V) = 5.8e21 cm^-2 mag^-1, R_V=3.1) and the
    reference depths for the H/H2 and C+/C/CO transitions (Hollenbach &
    Tielens 1999, Rev. Mod. Phys. 71, 173). Chemistry coupling would compute
    the CO abundance profile that feeds the line-transfer column N_CO.
    """

    def __init__(self, NH_per_Av: float = 1.87e21):
        """NH_per_Av: H-nucleus column per magnitude of visual extinction
        (1.87e21 for R_V=3.1; use ~2.1e21 including He)."""
        self.NH_per_Av = NH_per_Av

    def Av_from_column(self, N_H: float) -> float:
        return N_H / self.NH_per_Av

    def column_from_Av(self, Av: float) -> float:
        return Av * self.NH_per_Av

    @staticmethod
    def reference_transition_depths() -> dict:
        """Approximate A_V at which species become self-shielded / abundant
        (Hollenbach & Tielens 1999; Sternberg+2014)."""
        return {'H2_formation': 0.1, 'C+_to_C': 0.5, 'C_to_CO': 1.5, 'CO_fully_molecular': 2.5}


__all__ = [
    'COProperties', 'StatisticalEquilibriumSolver', 'LineProfileSynthesizer',
    'DustContinuumRT', 'PDRInterface',
    'planck_J', 'co_energy_K', 'co_line_frequency_Hz', 'co_einstein_A',
    'default_co_h2_rates',
]
