"""
Multi-scale simulation coupling for ASTRO.

Couples a hierarchy of simulation scales via AMR-style restriction/prolongation
operators (Berger & Colella 1989), provides an adaptive-refinement criterion,
a sub-resolution (subgrid) model suite (turbulent pressure, star formation,
stellar + AGN feedback), and an approximate collisional-ionisation-equilibrium
(CIE) cooling function.

References:
  Berger & Colella (1989), J. Comput. Phys. 82, 64 (AMR);
  McKee & Ostriker (2007), ARA&A 45, 565 (three-phase ISM, subgrid feedback);
  Sutherland & Dopita (1993), ApJS 88, 253 (CIE cooling);
  Kennicutt (1998), ARA&A 36, 189 (Schmidt law).
"""

import numpy as np
from dataclasses import dataclass, field
from typing import Optional


class ScaleCoupler:
    """Restriction (fine -> coarse) and prolongation (coarse -> fine) operators
    for 2D cell-centred AMR (factor-2 refinement). Volume-averaging restriction
    conserves the field total; bilinear prolongation is second-order accurate.
    """

    @staticmethod
    def restrict(fine: np.ndarray) -> np.ndarray:
        """Average each 2x2 block of a (2N, 2M) fine grid -> (N, M) coarse."""
        f = np.asarray(fine, float)
        ny, nx = f.shape
        if ny % 2 or nx % 2:
            raise ValueError("fine grid dimensions must be even")
        return 0.25 * (f[0::2, 0::2] + f[1::2, 0::2] + f[0::2, 1::2] + f[1::2, 1::2])

    @staticmethod
    def prolong(coarse: np.ndarray) -> np.ndarray:
        """Bilinear interpolation (N, M) -> (2N, 2M) with edge replication."""
        c = np.asarray(coarse, float)
        ny, nx = c.shape
        cp = np.pad(c, ((0, 1), (0, 1)), mode='edge')         # (ny+1, nx+1)
        c00 = cp[:ny, :nx]
        c10 = cp[1:ny + 1, :nx]
        c01 = cp[:ny, 1:nx + 1]
        c11 = cp[1:ny + 1, 1:nx + 1]
        fine = np.zeros((2 * ny, 2 * nx))
        fine[0::2, 0::2] = c00
        fine[1::2, 0::2] = 0.5 * (c00 + c10)
        fine[0::2, 1::2] = 0.5 * (c00 + c01)
        fine[1::2, 1::2] = 0.25 * (c00 + c10 + c01 + c11)
        return fine


@dataclass
class ZoomRegion:
    """A rectangular sub-region to be refined at higher resolution."""
    ix0: int
    iy0: int
    nx: int
    ny: int
    level: int = 1                  # refinement level (1 = 2x)


class HierarchicalRefinement:
    """AMR refinement criterion: flag cells where the relative gradient exceeds
    a threshold."""

    def __init__(self, threshold: float = 0.2):
        self.threshold = threshold

    def flags(self, field_grid: np.ndarray) -> np.ndarray:
        gx = np.gradient(field_grid, axis=1)
        gy = np.gradient(field_grid, axis=0)
        rel_grad = np.sqrt(gx ** 2 + gy ** 2) / (np.abs(field_grid).mean() + 1e-30)
        return rel_grad > self.threshold


class TurbulentPressureModel:
    """Turbulent (ram) pressure support: P_turb = rho * sigma^2 (cgs)."""

    def pressure(self, density_g_cm3: float, velocity_dispersion_cm_s: float) -> float:
        return density_g_cm3 * velocity_dispersion_cm_s ** 2


class StarFormationModel:
    """Kennicutt-Schmidt star-formation law (Kennicutt 1998)."""

    NORM = 2.5e-4
    INDEX = 1.4

    def surface_rate(self, sigma_gas_msun_pc2: float) -> float:
        """Sigma_SFR [Msun/yr/kpc^2] = 2.5e-4 * (Sigma_gas [Msun/pc^2])^1.4."""
        return self.NORM * sigma_gas_msun_pc2 ** self.INDEX

    def volumetric_rate_density(self, n_H_cm3: float, t_dyn_s: float = None,
                                efficiency: float = 0.01) -> float:
        """rho_dot* = eps * rho / t_dyn  [g/cm^3/s]."""
        rho = 1.6735575e-24 * n_H_cm3
        if t_dyn_s is None:
            t_dyn_s = 1.0e8 * 3.15e7           # ~100 Myr default dynamical time
        return efficiency * rho / t_dyn_s


class StellarFeedbackModel:
    """Core-collapse supernova feedback: mechanical energy + mass return."""

    SN_ENERGY_ERG = 1.0e51
    MASS_RETURN_MSUN = 10.0
    RATE_PER_SFR = 0.01                # CC SNe / yr per (Msun/yr) SFR

    def energy_rate(self, sfr_msun_yr: float) -> float:
        """Mechanical luminosity (erg/s) from CC SNe."""
        return self.RATE_PER_SFR * sfr_msun_yr * self.SN_ENERGY_ERG / 3.15e7


class AGNFeedbackModel:
    """AGN radiative + mechanical feedback, Eddington-limited."""

    def eddington_luminosity(self, bh_mass_msun: float) -> float:
        """L_Edd = 1.26e38 (M/Msun) erg/s."""
        return 1.26e38 * bh_mass_msun

    def mechanical_power(self, bh_mass_msun: float, edd_ratio: float = 1.0,
                         eta_jet: float = 0.01) -> float:
        """Relativistic-jet mechanical power (erg/s) at eta_jet * L_Edd."""
        return edd_ratio * eta_jet * self.eddington_luminosity(bh_mass_msun)


class CoolingFunction:
    """Approximate CIE volumetric cooling rate Lambda(T) [erg cm^3/s],
    capturing the metal-line peak near 1e5-1e6 K and the bremsstrahlung tail
    (Sutherland & Dopita 1993 / Gnat & Sternberg 2007 shape).

    A smooth piecewise fit, NOT a full multi-species calculation; for research
    use, load a real Sutherland-Dopita or Gnat-Sternberg table.
    """

    @staticmethod
    def lambda_cie(T_K: float, metallicity_solar: float = 1.0) -> float:
        T = max(float(T_K), 10.0)
        logT = np.log10(T)
        if logT < 4.0:
            lam = 1e-27 * T ** 0.6
        elif logT < 5.3:
            lam = 1e-24 * (T / 1e5) ** (-0.6)        # metal-line peak region
        else:
            lam = 1e-23 * (T / 1e6) ** 0.5           # bremsstrahlung
        return float(lam * metallicity_solar)


@dataclass
class MultiScaleSimulation:
    """A base grid + optional zoom region, with base<->zoom coupling hooks."""
    coarse_field: np.ndarray
    coarse_density: np.ndarray
    fine_field: Optional[np.ndarray] = None
    zoom: Optional[ZoomRegion] = None
    coupler: ScaleCoupler = field(default_factory=ScaleCoupler)

    def couple_zoom_to_base(self) -> None:
        """Restrict the fine solution back onto the coarse grid within the zoom
        region (simplified Berger-Oliger flux correction)."""
        if self.fine_field is None or self.zoom is None:
            return
        restricted = self.coupler.restrict(self.fine_field)
        z = self.zoom
        self.coarse_field[z.iy0:z.iy0 + restricted.shape[0],
                          z.ix0:z.ix0 + restricted.shape[1]] = restricted


__all__ = [
    'ScaleCoupler', 'ZoomRegion', 'HierarchicalRefinement', 'MultiScaleSimulation',
    'TurbulentPressureModel', 'StarFormationModel', 'StellarFeedbackModel',
    'AGNFeedbackModel', 'CoolingFunction',
]
