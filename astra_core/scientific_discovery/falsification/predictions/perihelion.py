"""
Seed falsification records: perihelion precession of Mercury.

Two records, same REAL system (Mercury), different models:
  * GR predicts the unexplained residual advance ~42.98 arcsec/century
    (Will 2018, LRR 21, 4). Observed ~42.98 -> model CONFIRMED (negative control).
  * Newtonian gravity predicts NO unexplained advance (0.0). Observed ~42.98
    -> ANOMALY flagged. This is the historical anomaly that falsified pure
    Newtonian gravity and motivated GR -- the canonical paradigm shift.

Real data (cited):
  * Mercury orbital elements: a = 0.387098 AU, e = 0.205630.
  * Observed residual advance (after subtracting Newtonian planetary
    perturbations): 42.98 +- 0.04 arcsec/century (Clemence 1947; modern
    ephemerides, Pitjeva). GR predicts 42.98. See Will (2018).
"""

import math
from typing import Any, Dict, Tuple

from ..registry import FalsifiablePrediction, SystematicCheck, Registry

# --- CGS/SI constants ---
G = 6.67430e-11           # m^3 kg^-1 s^-2
C = 2.99792458e8          # m/s
AU = 1.495978707e11       # m
ARCSEC_PER_RAD = 206264.806247

# --- REAL cited Mercury data ---
MERCURY: Dict[str, Any] = {
    "a_AU": 0.387098,                 # semi-major axis (real)
    "e": 0.205630,                    # eccentricity (real)
    "M_kg": 1.98847e30,               # solar mass (real)
    "orbits_per_century": 415.2,      # Mercury orbital periods per century (88 d period)
    "observed_residual_arcsec_century": 42.98,   # Clemence 1947 / modern ephemeris
    "observed_sigma": 0.04,
}


def _gr_precession_arcsec_century(inputs: Dict[str, Any]) -> float:
    """General-relativistic perihelion advance (arcsec/century).

    omega = 6 pi G M / (c^2 a (1 - e^2))   rad/orbit   (Will 2018, Eq. 7.54)
    """
    a = inputs["a_AU"] * AU
    e = inputs["e"]
    M = inputs["M_kg"]
    n_orbits = inputs["orbits_per_century"]
    omega_rad_per_orbit = 6.0 * math.pi * G * M / (C ** 2 * a * (1.0 - e ** 2))
    return omega_rad_per_orbit * n_orbits * ARCSEC_PER_RAD


def gr_predict(inputs: Dict[str, Any]) -> Tuple[float, float]:
    value = _gr_precession_arcsec_century(inputs)
    return value, 0.05      # sigma_pred: small input/formula uncertainty


def newton_predict(inputs: Dict[str, Any]) -> Tuple[float, float]:
    """Newtonian gravity predicts no unexplained perihelion advance."""
    return 0.0, 0.0


def mercury_fetch(system_id: str) -> Dict[str, Any]:
    if system_id != "mercury":
        raise KeyError(f"unknown system: {system_id}")
    return dict(MERCURY)


def mercury_observe(system_id: str) -> Tuple[float, float]:
    if system_id != "mercury":
        raise KeyError(f"unknown system: {system_id}")
    return MERCURY["observed_residual_arcsec_century"], MERCURY["observed_sigma"]


# --- named systematics for solar-system perihelion (real, cited) ---
_PERIHELION_SYSTEMATICS = [
    SystematicCheck("solar_quadrupole_J2", 0.025,
                    note="solar J2 contribution ~0.025 arcsec/century (Will 2018)"),
    SystematicCheck("asteroid_perturbations", 0.10,
                    note="residual uncertainty from asteroid masses"),
]


GR_PERIHELION = FalsifiablePrediction(
    id="gr_perihelion_mercury",
    model="GR (post-Newtonian)",
    model_citation="Will 2018, LRR 21, 4 (Eq. 7.54)",
    quantity="perihelion advance",
    units="arcsec/century",
    system_class="solar_system_planet",
    formula_doc="omega = 6 pi G M / (c^2 a (1 - e^2))   rad/orbit",
    predict=gr_predict,
    fetch=mercury_fetch,
    observe=mercury_observe,
    observe_citation="Clemence 1947; modern ephemeris (Pitjeva) ~42.98 arcsec/century",
    systematics=_PERIHELION_SYSTEMATICS,
    min_absolute_effect=0.5,
    anomaly_k_sigma=4.0,
    audit_inputs=MERCURY,
    audit_expected=42.98,
    audit_tolerance=0.6,
)

NEWTON_PERIHELION = FalsifiablePrediction(
    id="newton_perihelion_mercury",
    model="Newtonian gravity (pure)",
    model_citation="Newton Principia; no perihelion-advance term",
    quantity="perihelion advance",
    units="arcsec/century",
    system_class="solar_system_planet",
    formula_doc="omega = 0   (Newtonian gravity predicts no unexplained advance)",
    predict=newton_predict,
    fetch=mercury_fetch,
    observe=mercury_observe,
    observe_citation="Clemence 1947; modern ephemeris ~42.98 arcsec/century",
    systematics=_PERIHELION_SYSTEMATICS,
    min_absolute_effect=0.5,
    anomaly_k_sigma=4.0,
    audit_inputs=MERCURY,
    audit_expected=0.0,
    audit_tolerance=1e-6,
)


def register(registry: Registry) -> None:
    registry.register(GR_PERIHELION)
    registry.register(NEWTON_PERIHELION)


__all__ = ['GR_PERIHELION', 'NEWTON_PERIHELION', 'register']
