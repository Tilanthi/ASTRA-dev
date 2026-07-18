"""Seed registry of falsifiable predictions (curated, cited, code)."""

from ..registry import Registry
from . import perihelion
from . import strong_lensing

# systems available for each system_class (the seed registry ships real data
# for these; production would live-fetch from archives).
SEED_SYSTEMS = {
    "solar_system_planet": ["mercury"],
    "strong_lens_galaxy": ["sdss_j0946+1006"],
}


def seed_registry() -> Registry:
    """Build the curated seed registry."""
    reg = Registry()
    perihelion.register(reg)
    strong_lensing.register(reg)
    return reg


__all__ = ['seed_registry', 'SEED_SYSTEMS']
