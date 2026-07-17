"""
Astronomical Swarm Agents for ASTRO.

Specialised analysis agents that cooperate via a stigmergic shared memory
(after Gordon's notion of stigmergy in ant colonies). Each agent owns a
domain (spectroscopy, photometry, dynamics, imaging) and exposes a typed
`analyze(...)` entry point that builds on the physics modules in this package.

Design:
  * AstroAgent  -- abstract base: identity, domain, a stigmergic memory slot.
  * StigmergicMemory / PheromoneTrail -- the shared-memory coordination medium.
  * SpectroscopicAgent / PhotometricAgent / DynamicalAgent / ImagingAgent --
    concrete agents with verified analysis routines.
"""

import numpy as np
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Tuple
from enum import Enum
from abc import ABC, abstractmethod

# Optional dependencies (this module must import cleanly even if the heavy
# physics modules have issues).
try:
    from .knowledge_graph import (  # noqa: F401
        AstronomicalKnowledgeGraph, AstroNode, AstroEdge,
        AstroNodeType, RelationType, MechanismNode, HypothesisNode)
except Exception:
    AstronomicalKnowledgeGraph = None  # type: ignore

try:
    from .physics import PhysicsEngine, PhysicalConstants  # noqa: F401
except Exception:
    PhysicsEngine = None  # type: ignore
    PhysicalConstants = None  # type: ignore


# CGS
G_CGS = 6.67430e-8
M_SUN = 1.98847e33
C_CGS = 2.99792458e10


class AgentDomain(Enum):
    SPECTROSCOPY = "spectroscopy"
    PHOTOMETRY = "photometry"
    DYNAMICS = "dynamics"
    IMAGING = "imaging"


@dataclass
class PheromoneTrail:
    """A decaying trail of stigmergic markers in a coordinate space."""
    locations: List[Any] = field(default_factory=list)
    strengths: List[float] = field(default_factory=list)
    pheromone_type: str = "discovery"
    decay_rate: float = 0.05

    def deposit(self, location: Any, strength: float = 1.0) -> None:
        self.locations.append(location)
        self.strengths.append(float(strength))

    def read(self) -> List[Tuple[Any, float]]:
        return list(zip(self.locations, self.strengths))

    def evaporate(self) -> None:
        self.strengths = [max(0.0, s * (1.0 - self.decay_rate)) for s in self.strengths]
        keep = [i for i, s in enumerate(self.strengths) if s > 1e-6]
        self.locations = [self.locations[i] for i in keep]
        self.strengths = [self.strengths[i] for i in keep]


class StigmergicMemory:
    """Shared key->value memory agents write to / read from for coordination."""

    def __init__(self):
        self._store: Dict[str, Any] = {}

    def deposit(self, key: str, value: Any, strength: float = 1.0) -> None:
        self._store[key] = value

    def read(self, key: str) -> Optional[Any]:
        return self._store.get(key)

    def keys(self) -> List[str]:
        return list(self._store.keys())


class AstroAgent(ABC):
    """Base astronomical swarm agent."""

    def __init__(self, name: str, domain: AgentDomain,
                 knowledge: Optional["AstronomicalKnowledgeGraph"] = None,
                 memory: Optional[StigmergicMemory] = None):
        self.name = name
        self.domain = domain
        self.knowledge = knowledge
        self.memory = memory or StigmergicMemory()
        self.trail = PheromoneTrail(pheromone_type=domain.value)

    @abstractmethod
    def analyze(self, data: Any) -> Dict[str, Any]:
        ...

    def share(self, key: str, value: Any) -> None:
        self.memory.deposit(key, value)


class SpectroscopicAgent(AstroAgent):
    """Analyses spectra: redshift (peak-to-rest-line matching) and line peaks."""

    def __init__(self, knowledge=None, memory=None):
        super().__init__("SpectroscopicAgent", AgentDomain.SPECTROSCOPY, knowledge, memory)

    def analyze(self, data: Dict[str, Any]) -> Dict[str, Any]:
        wl = np.asarray(data['wavelength_um'], float)
        fl = np.asarray(data['flux'], float)
        rest = data.get('rest_lines_um', [0.6563])        # default Halpha
        return {'redshift': self.estimate_redshift(wl, fl, rest),
                'peaks_um': self.find_peaks(wl, fl)}

    @staticmethod
    def find_peaks(wavelength, flux, prominence: float = 0.1) -> np.ndarray:
        med = np.median(flux)
        thr = med + prominence * (np.max(flux) - med)
        peaks = []
        for i in range(1, len(flux) - 1):
            if flux[i] > thr and flux[i] >= flux[i - 1] and flux[i] > flux[i + 1]:
                peaks.append(wavelength[i])
        return np.array(peaks)

    def estimate_redshift(self, wavelength, flux, rest_lines_um) -> float:
        """Match the brightest observed peak to the nearest rest line:
        z = obs/rest - 1."""
        peaks = self.find_peaks(wavelength, flux)
        if len(peaks) == 0:
            return 0.0
        flux_at_peaks = [float(np.interp(p, wavelength, flux)) for p in peaks]
        brightest = float(peaks[int(np.argmax(flux_at_peaks))])
        rest = min(rest_lines_um, key=lambda r: abs(brightest - r))
        return float(brightest / rest - 1.0)


class PhotometricAgent(AstroAgent):
    """Analyses photometry / SEDs: blackbody T_eff (Wien) and spectral index."""

    def __init__(self, knowledge=None, memory=None):
        super().__init__("PhotometricAgent", AgentDomain.PHOTOMETRY, knowledge, memory)

    def analyze(self, data: Dict[str, Any]) -> Dict[str, Any]:
        wl = np.asarray(data['wavelength_um'], float)
        fl = np.asarray(data['flux_jy'], float)
        return {'teff_K': self.blackbody_temperature(wl, fl),
                'spectral_index': self.spectral_index(wl, fl)}

    @staticmethod
    def blackbody_temperature(wavelength_um, flux_jy) -> float:
        """Effective temperature from the SED peak via Wien's law
        (lambda_peak [um] * T = 2898 um K)."""
        i = int(np.argmax(flux_jy))
        return 2898.0 / max(wavelength_um[i], 1e-3)

    @staticmethod
    def spectral_index(wavelength_um, flux_jy) -> float:
        nu = C_CGS / (wavelength_um * 1e-4)
        m = (flux_jy > 0) & (nu > 0)
        if m.sum() < 2:
            return float('nan')
        slope, _ = np.polyfit(np.log10(nu[m]), np.log10(flux_jy[m]), 1)
        return float(slope)


class DynamicalAgent(AstroAgent):
    """Analyses velocity fields: rotation curves -> enclosed mass."""

    def __init__(self, knowledge=None, memory=None):
        super().__init__("DynamicalAgent", AgentDomain.DYNAMICS, knowledge, memory)

    def analyze(self, data: Dict[str, Any]) -> Dict[str, Any]:
        r = np.asarray(data['radius_cm'], float)
        v = np.asarray(data['velocity_cm_s'], float)
        return {'enclosed_mass_msun': self.enclosed_mass(r, v),
                'v_circular_cm_s': float(np.max(v))}

    @staticmethod
    def enclosed_mass(radius_cm, velocity_cm_s) -> np.ndarray:
        """Enclosed mass M(<r) = v_circ^2 r / G (circular-orbit estimate)."""
        return (velocity_cm_s ** 2) * radius_cm / G_CGS / M_SUN


class ImagingAgent(AstroAgent):
    """Analyses images: source detection by local maxima above a threshold."""

    def __init__(self, knowledge=None, memory=None):
        super().__init__("ImagingAgent", AgentDomain.IMAGING, knowledge, memory)

    def analyze(self, data: Dict[str, Any]) -> Dict[str, Any]:
        image = np.asarray(data['image'], float)
        sigma = data.get('sigma', 5.0)
        sources = self.detect_sources(image, sigma)
        return {'n_sources': len(sources), 'sources': sources}

    @staticmethod
    def detect_sources(image: np.ndarray, sigma: float = 5.0) -> List[Tuple[int, int, float]]:
        med = np.median(image)
        mad = 1.4826 * np.median(np.abs(image - med)) or float(image.std())
        thr = med + sigma * mad
        sources = []
        for i in range(1, image.shape[0] - 1):
            for j in range(1, image.shape[1] - 1):
                v = image[i, j]
                if v > thr and v >= image[i - 1:i + 2, j - 1:j + 2].max():
                    sources.append((int(i), int(j), float(v)))
        return sources


__all__ = [
    'AgentDomain', 'AstroAgent', 'StigmergicMemory', 'PheromoneTrail',
    'SpectroscopicAgent', 'PhotometricAgent', 'DynamicalAgent', 'ImagingAgent',
]
