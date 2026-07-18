"""
Seed falsification record: SIS Einstein-radius self-consistency for a real
strong gravitational lens.

Record: Singular Isothermal Sphere (SIS) predicts the Einstein radius from the
stellar velocity dispersion:
    theta_E = 4 pi (sigma/c)^2 (D_ls / D_s)
Tested against the observed Einstein radius from HST imaging for the "double
Einstein ring" lens SDSS J0946+1006 (Gavazzi+ 2008). The density slope
g' = 2.00 +- 0.03 for this system (nearly perfectly isothermal), so the SIS
model should be CONFIRMED (model-confirmed negative control for strong lensing).

Real cited data (Gavazzi et al. 2008, ApJ 677, 1046; arXiv:0801.1555):
  z_l = 0.222, z_s1 = 0.609, theta_E1 = 1.43 +- 0.01 arcsec,
  sigma_SIE = 287 +- 5 km/s, g' = 2.00 +- 0.03.

Angular-diameter distances computed in a flat Lambda-CDM cosmology
(H0 = 70 km/s/Mpc, Omega_m = 0.3, Omega_Lambda = 0.7) via scipy.integrate.quad.
"""

import math
import numpy as np
from scipy.integrate import quad
from typing import Any, Dict, Tuple

from ..registry import FalsifiablePrediction, SystematicCheck, Registry

C = 2.99792458e8           # m/s
ARCSEC_PER_RAD = 206264.806247


# --- flat Lambda-CDM angular-diameter distance -----------------------------

def _comoving_distance_Mpc(z: float, H0: float = 70.0, Om: float = 0.3,
                           OL: float = 0.7) -> float:
    c_km_s = 2.99792458e5
    def inv_E(zp):
        return 1.0 / math.sqrt(Om * (1.0 + zp) ** 3 + OL)
    integral, _ = quad(inv_E, 0.0, z)
    return c_km_s / H0 * integral


def _D_A_Mpc(z_observer: float, z_source: float) -> float:
    chi_obs = _comoving_distance_Mpc(z_observer)
    chi_src = _comoving_distance_Mpc(z_source)
    return (chi_src - chi_obs) / (1.0 + z_source)


# --- real cited data for SDSS J0946+1006 (Gavazzi+ 2008) -------------------

J0946 = {
    "z_lens": 0.222,
    "z_source": 0.609,
    "sigma_SIE_km_s": 287.0,
    "sigma_SIE_err_km_s": 5.0,
    "theta_E_obs_arcsec": 1.43,
    "theta_E_obs_err_arcsec": 0.01,
}


def sis_predict(inputs: Dict[str, Any]) -> Tuple[float, float]:
    """SIS Einstein-radius prediction: theta_E = 4 pi (sigma/c)^2 (D_ls/D_s)."""
    sigma_m_s = inputs["sigma_SIE_km_s"] * 1e3          # km/s -> m/s
    z_l = inputs["z_lens"]
    z_s = inputs["z_source"]
    D_ls = _D_A_Mpc(z_l, z_s)
    D_s = _D_A_Mpc(0.0, z_s)
    theta_E_rad = 4.0 * math.pi * (sigma_m_s / C) ** 2 * (D_ls / D_s)
    theta_E_arcsec = theta_E_rad * ARCSEC_PER_RAD
    sigma_pred = theta_E_arcsec * 2.0 * (inputs["sigma_SIE_err_km_s"]
                                         / inputs["sigma_SIE_km_s"])
    return theta_E_arcsec, sigma_pred


def j0946_fetch(system_id: str) -> Dict[str, Any]:
    if system_id != "sdss_j0946+1006":
        raise KeyError(f"unknown system: {system_id}")
    return dict(J0946)


def j0946_observe(system_id: str) -> Tuple[float, float]:
    if system_id != "sdss_j0946+1006":
        raise KeyError(f"unknown system: {system_id}")
    return J0946["theta_E_obs_arcsec"], J0946["theta_E_obs_err_arcsec"]


# --- systematics for strong-lens Einstein radius ---
_LENS_SYSTEMATICS = [
    SystematicCheck("mass_sheet_degeneracy", 0.05,
                    note="mass-sheet degeneracy ~few% in theta_E (Schneider 2014)"),
    SystematicCheck("slope_deviation_from_isothermal", 0.04,
                    note="g' = 2.00 +- 0.03; deviation contributes ~3%"),
    SystematicCheck("line_of_sight_structure", 0.02,
                    note="LOS structure / external convergence"),
]


SIS_EINSTEIN_RADIUS = FalsifiablePrediction(
    id="sis_einstein_radius_j0946",
    model="SIS (singular isothermal sphere)",
    model_citation="Schneider, Ehlers & Falco 1992, 'Gravitational Lensing'; "
                   "Bolton et al. 2008, ApJ 682, 964",
    quantity="Einstein radius",
    units="arcsec",
    system_class="strong_lens_galaxy",
    formula_doc="theta_E = 4 pi (sigma/c)^2 (D_ls / D_s)",
    predict=sis_predict,
    fetch=j0946_fetch,
    observe=j0946_observe,
    observe_citation="Gavazzi et al. 2008, ApJ 677, 1046 (arXiv:0801.1555): "
                     "theta_E1 = 1.43 +- 0.01 arcsec",
    systematics=_LENS_SYSTEMATICS,
    min_absolute_effect=0.10,       # arcsec; deviations < 0.1" are uninteresting
    anomaly_k_sigma=4.0,
    audit_inputs=J0946,
    audit_expected=1.40,            # hand-computed SIS prediction for these inputs
    audit_tolerance=0.08,
)


def register(registry: Registry) -> None:
    registry.register(SIS_EINSTEIN_RADIUS)


__all__ = ['SIS_EINSTEIN_RADIUS', 'register']
