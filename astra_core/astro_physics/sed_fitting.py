"""
Spectral-energy-distribution (SED) building blocks and fitting.

  * FilterLibrary: standard photometric bands with pivot wavelengths (Johnson-
    Cousins UBVRI, 2MASS JHK, Spitzer/IRAC, WISE, Herschel/PACS & SPIRE,
    SCUBA-2) -- reference pivot wavelengths from their instrument papers.
  * ModifiedBlackbody: optically-thin dust MBB, F_nu = (M kappa_nu B_nu)/D^2.
  * StellarPopulation: single-burst SSP approximated by a blackbody at T_eff
    times the bolometric luminosity (a quick template, not a full isochrone).
  * AGNTemplate: quasar SED -- power-law F_nu ~ nu^-alpha plus a 'big blue bump'.
  * CompositeSED: sum of components.
  * SEDFitter: fit a component model to multi-band photometry.

References:
  Bessell & Brett (1988) for UBVRI; Cohen, Wheaton & Megeath (2003) for 2MASS;
  Wright et al. (2010) for WISE; Draine (2006) for dust emissivity.
"""

import numpy as np
from dataclasses import dataclass, field
from typing import Optional, Dict, List
from scipy.optimize import curve_fit

# CGS
H_PLANCK = 6.62607015e-27
K_BOLTZMANN = 1.380649e-16
C_LIGHT = 2.99792458e10
M_SUN = 1.98847e33
PC = 3.0856776e18
JANSKY = 1.0e-23


def planck_Bnu(nu_Hz: float, T_K: float) -> float:
    """Planck specific intensity B_nu (erg s^-1 cm^-2 Hz^-1 sr^-1)."""
    x = H_PLANCK * nu_Hz / (K_BOLTZMANN * T_K)
    return (2 * H_PLANCK * nu_Hz ** 3 / C_LIGHT ** 2) / np.expm1(x)


class FilterLibrary:
    """Reference photometric bands (pivot wavelengths in microns)."""

    BANDS: Dict[str, float] = {
        'U': 0.3656, 'B': 0.4453, 'V': 0.5513, 'R': 0.6577, 'I': 0.8062,
        'J': 1.2345, 'H': 1.6624, 'Ks': 2.1591,
        'IRAC1': 3.550, 'IRAC2': 4.493, 'IRAC3': 5.731, 'IRAC4': 7.872,
        'W1': 3.3526, 'W2': 4.6028, 'W3': 11.5608, 'W4': 22.0883,
        'MIPS24': 23.68, 'PACS70': 70.0, 'PACS100': 100.0, 'PACS160': 160.0,
        'SPIRE250': 250.0, 'SPIRE350': 350.0, 'SPIRE500': 500.0,
        'SCUBA450': 450.0, 'SCUBA850': 850.0, 'ALMA1300': 1300.0,
    }

    @classmethod
    def pivot_um(cls, band: str) -> float:
        return cls.BANDS[band]

    @classmethod
    def all_bands(cls) -> Dict[str, float]:
        return dict(cls.BANDS)


class ModifiedBlackbody:
    """Dust modified blackbody: F_nu = M_dust * kappa_nu * B_nu(T) / D^2 (Jy)."""

    def __init__(self, kappa_0: float = 10.0, beta: float = 1.5, lambda_0_um: float = 350.0):
        self.kappa_0 = kappa_0
        self.beta = beta
        self.lambda_0 = lambda_0_um

    def opacity(self, wavelength_um: float) -> float:
        return self.kappa_0 * (wavelength_um / self.lambda_0) ** (-self.beta)

    def flux_jy(self, wavelength_um: float, T_dust: float, dust_mass_msun: float,
                distance_mpc: float) -> float:
        nu = C_LIGHT / (wavelength_um * 1e-4)
        Bnu = planck_Bnu(nu, T_dust)
        mass_g = dust_mass_msun * M_SUN
        dist_cm = distance_mpc * 1e6 * PC
        return mass_g * self.opacity(wavelength_um) * Bnu / dist_cm ** 2 / JANSKY


class StellarPopulation:
    """Approximate single-burst SSP SED: a blackbody at T_eff with bolometric
    luminosity L = N_stars * <L> ~ stellar mass * (M/L)_bol."""

    def __init__(self, t_eff_K: float = 5800.0, luminosity_lsun: float = 1.0):
        self.Teff = t_eff_K
        self.L = luminosity_lsun * 3.828e33          # erg/s

    def flux_jy(self, wavelength_um: float, distance_mpc: float) -> float:
        nu = C_LIGHT / (wavelength_um * 1e-4)
        # luminosity per Hz: L_nu = pi * B_nu(Teff) * (R^2 / D^2); use L bolometric scaling
        # bolometric L = sigma T^4 * 4 pi R^2 -> R^2 = L/(4 pi sigma T^4)
        sigma = 5.670374e-5
        R2 = self.L / (4 * np.pi * sigma * self.Teff ** 4)
        Bnu = planck_Bnu(nu, self.Teff)
        dist_cm = distance_mpc * 1e6 * PC
        return np.pi * Bnu * R2 / dist_cm ** 2 / JANSKY


class AGNTemplate:
    """Quasar SED: power-law F_nu ~ nu^-alpha with an optional big-blue-bump."""

    def __init__(self, alpha: float = 0.5, norm_jy_at_1um: float = 1e-3,
                 bump_amp: float = 0.0, bump_T: float = 30000.0):
        self.alpha = alpha
        self.norm = norm_jy_at_1um
        self.bump_amp = bump_amp
        self.bump_T = bump_T

    def flux_jy(self, wavelength_um: float) -> float:
        nu = C_LIGHT / (wavelength_um * 1e-4)
        nu_1um = C_LIGHT / 1e-4
        pl = self.norm * (nu / nu_1um) ** (-self.alpha)
        bump = 0.0
        if self.bump_amp > 0:
            bump = self.bump_amp * planck_Bnu(nu, self.bump_T) / planck_Bnu(nu_1um, self.bump_T)
        return pl + bump


class CompositeSED:
    """Sum of SED components evaluated on a wavelength grid (microns -> Jy)."""

    def __init__(self, components: List, distance_mpc: float = 1.0):
        self.components = components
        self.distance = distance_mpc

    def flux_jy(self, wavelength_um) -> np.ndarray:
        wl = np.atleast_1d(wavelength_um)
        total = np.zeros_like(wl, float)
        for c in self.components:
            for i, w in enumerate(wl):
                total[i] += self._component_flux(c, float(w))
        return total

    def _component_flux(self, comp, w_um):
        if hasattr(comp, 'flux_jy'):
            try:
                return comp.flux_jy(w_um, self.distance)
            except TypeError:
                return comp.flux_jy(w_um)
        return 0.0


class SEDFitter:
    """Fit a component model to photometry.

    model: callable(wavelength_um, *params) -> flux_jy
    """

    def __init__(self, model):
        self.model = model

    def fit(self, wavelengths_um, fluxes_jy, p0, flux_err=None):
        wl = np.asarray(wavelengths_um, float)
        fl = np.asarray(fluxes_jy, float)
        try:
            popt, pcov = curve_fit(self.model, wl, fl, p0=p0,
                                   sigma=flux_err, absolute_sigma=(flux_err is not None),
                                   maxfev=20000)
            return {'params': popt, 'errors': np.sqrt(np.diag(pcov)), 'success': True}
        except Exception as e:
            return {'params': p0, 'errors': None, 'success': False, 'error': str(e)}


__all__ = ['FilterLibrary', 'ModifiedBlackbody', 'StellarPopulation',
           'AGNTemplate', 'CompositeSED', 'SEDFitter', 'planck_Bnu']
