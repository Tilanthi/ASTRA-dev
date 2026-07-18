"""Seed registry of falsifiable predictions (curated, cited, code)."""

from ..registry import Registry
from . import perihelion
from . import strong_lensing
from . import mt_spatial

SEED_SYSTEMS = {
    "solar_system_planet": ["mercury"],
    "strong_lens_galaxy": ["sdss_j0946+1006"],
    "gould_belt_cloud": ["ic5146"],
}


def seed_registry() -> Registry:
    """Build the curated seed registry."""
    reg = Registry()
    perihelion.register(reg)
    strong_lensing.register(reg)
    mt_spatial.register(reg)
    return reg


__all__ = ['seed_registry', 'SEED_SYSTEMS']
