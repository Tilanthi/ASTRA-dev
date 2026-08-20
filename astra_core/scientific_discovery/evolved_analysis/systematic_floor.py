"""systematic_floor.py — named per-dataset floors for the absolute-effect gate.

Egent (arXiv 2512.01270) found its propagated per-measurement uncertainties
under-estimated the joint scatter by 2-3x and recommended adding a systematic
floor in quadrature. The transferable point is not the factor (it was measured
on Magellan/MIKE equivalent widths) but the mechanism: propagated statistical
errors are LOWER BOUNDS, and each dataset deserves a named floor.

ASTRA's gate-1 tests |effect| >= EFFECT_MIN and p <= pmax on a correlation /
contrast magnitude. The floor here is an additive effect-space threshold: a
spurious-correlation level induced by known survey systematics that a real
effect must clear. Floors are registered with a reason, never invented
silently; unregistered datasets get 0.0 (no floor claimed, no floor applied).
"""
from __future__ import annotations

# dataset -> {"floor": additive floor in |effect| units, "reason": citation}
SYSTEMATIC_FLOORS = {
    # SDSS model-mag photometry + z_spec: zeropoint / dust-extinction
    # residuals across adjacent bands induce cross-band correlations at the
    # ~1-2 per-cent level (Ivezic et al. 2019, SDSS DR8 calibration residual
    # scatter ~1-2 per cent). 0.01 in correlation units is the conservative
    # registration pending a split-half measurement on the data lake.
    "legacy": {
        "floor": 0.01,
        "reason": "SDSS photometric calibration + spectroscopic selection "
                  "systematics; conservative 0.01 pending split-half measurement",
    },
}


def effect_floor(dataset: str) -> float:
    """Additive systematic floor in |effect| units for ``dataset`` (0.0 if
    the dataset has no registered floor)."""
    spec = SYSTEMATIC_FLOORS.get(dataset or "")
    return float(spec["floor"]) if spec else 0.0
