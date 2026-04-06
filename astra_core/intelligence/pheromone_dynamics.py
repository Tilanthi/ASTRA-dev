"""
Digital Pheromone Dynamics for Swarm Intelligence

Implements stigmergic coordination for swarm agents exploring the V36 hypothesis
space, leaving "trails" that guide future exploration.

Integration with V36:
- Pheromone field over domain mixture space
- Guides HybridWorldGenerator toward promising regions
- Tracks successful/failed hypotheses for MechanismDiscoveryEngine
- Accelerates CrossDomainAnalogyEngine toward fruitful comparisons

Date: 2025-11-27
Version: 37.0
"""

import numpy as np
from typing import Dict, List, Optional, Tuple, Any, Callable
from dataclasses import dataclass, field
from enum import Enum
import time
import json


class PheromoneType(Enum):
    """Types of pheromones in the V36 hypothesis space"""
    EXPLORATION = "exploration"        # Marks explored regions
    SUCCESS = "success"                # Marks hypotheses that passed falsification
    FAILURE = "failure"                # Marks hypotheses that violated constraints
    ANALOGY = "analogy"                # Marks discovered cross-domain connections
    NOVELTY = "novelty"                # Marks novel mechanism discoveries
    ATTENTION = "attention"            # Marks regions requiring investigation


@dataclass
class PheromoneDeposit:
    """A single pheromone deposit"""
    deposit_id: str
    pheromone_type: PheromoneType
    location: Tuple[float, ...]
    strength: float
    timestamp: float
    metadata: Dict[str, Any] = field(default_factory=dict)
    decay_rate: float = 0.1


@dataclass
class PheromoneFieldConfig:
    """Configuration for pheromone field"""
    # Dimension specifications
    domain_mixture_bins: int = 20      # Resolution for CLD/D1/D2 mixture space
    template_count: int = 7            # Number of symbolic templates
    role_count: int = 9                # Number of functional roles

    # Decay parameters
    base_evaporation_rate: float = 0.05
    type_specific_rates: Dict[str, float] = None

    # Deposit parameters
    base_deposit_strength: float = 1.0
    max_concentration: float = 10.0

    # Sensing parameters
    default_sense_radius: float = 0.1

    def __post_init__(self):
        if self.type_specific_rates is None:
            self.type_specific_rates = {
                PheromoneType.EXPLORATION.value: 0.1,    # Evaporates faster
                PheromoneType.SUCCESS.value: 0.02,      # Persists longer
                PheromoneType.FAILURE.value: 0.05,      # Medium persistence
                PheromoneType.ANALOGY.value: 0.03,      # Persists longer
                PheromoneType.NOVELTY.value: 0.02,      # Persists longest
                PheromoneType.ATTENTION.value: 0.15     # Evaporates quickly
            }


class DigitalPheromoneField:
    """
    Digital pheromone field over V36 hypothesis space.

    The field has multiple dimensions:
    1. Domain mixture space (3D simplex: CLD, D1, D2 proportions)
    2. Symbolic template space (discrete: 7 templates)
    3. Functional role space (discrete: 9 roles)

    Provides:
    - Pheromone deposit and sensing
    - Time-based evaporation
    - Gradient computation for navigation
    - V36-specific coordinate mappings
    """

    def __init__(self, config: PheromoneFieldConfig = None):
        self.config = config or PheromoneFieldConfig()

        # Initialize pheromone grids
        # Domain mixture field (3D simplex discretized)
        self.domain_field = self._init_domain_field()

        # Template field (discrete)
        self.template_field = np.zeros(
            (self.config.template_count, len(PheromoneType)),
            dtype=np.float32
        )

        # Role field (discrete)
        self.role_field = np.zeros(
            (self.config.role_count, len(PheromoneType)),
            dtype=np.float32
        )

        # Combined field for continuous exploration
        self.combined_field = self._init_combined_field()

        # Deposit history for detailed queries
        self.deposits: Dict[str, PheromoneDeposit] = {}
        self._deposit_counter = 0

        # Last evaporation timestamp
        self._last_evaporation = time.time()

    def _init_domain_field(self) -> np.ndarray:
        """Initialize domain mixture field (simplex discretization)"""
        bins = self.config.domain_mixture_bins
        n_pheromone_types = len(PheromoneType)
        # Use 2D grid (CLD, D1) since D2 = 1 - CLD - D1
        return np.zeros((bins, bins, n_pheromone_types), dtype=np.float32)

    def _init_combined_field(self) -> np.ndarray:
        """Initialize combined continuous field"""
        # Higher dimensional field for general exploration
        # Dimensions: [domain_x, domain_y, template, role, pheromone_type]
        return np.zeros((
            self.config.domain_mixture_bins,
            self.config.domain_mixture_bins,
            self.config.template_count,
            self.config.role_count,
            len(PheromoneType)
        ), dtype=np.float32)

    def _domain_to_indices(self, domain_mixture: Dict[str, float]) -> Tuple[int, int]:
        """Convert domain mixture to grid indices"""
        cld = domain_mixture.get('CLD', 0.33)
        d1 = domain_mixture.get('D1', 0.33)
        # D2 is implicit

        bins = self.config.domain_mixture_bins
        i = min(int(cld * bins), bins - 1)
        j = min(int(d1 * bins), bins - 1)
        return i, j

    def _indices_to_domain(self, i: int, j: int) -> Dict[str, float]:
        """Convert grid indices to domain mixture"""
        bins = self.config.domain_mixture_bins
        cld = (i + 0.5) / bins
        d1 = (j + 0.5) / bins
        d2 = max(0.0, 1.0 - cld - d1)

        # Normalize
        total = cld + d1 + d2
        return {
            'CLD': cld / total,
            'D1': d1 / total,
            'D2': d2 / total
        }

    def _pheromone_type_index(self, ptype: PheromoneType) -> int:
        """Get index for pheromone type"""
        return list(PheromoneType).index(ptype)

    # =========================================================================
    # DEPOSIT OPERATIONS
    # =========================================================================

    def deposit(self, pheromone_type: PheromoneType,
                location: Dict[str, Any],
                strength: float = None,
                metadata: Dict[str, Any] = None) -> str:
        """
        Deposit pheromone at a location.

        Args:
            pheromone_type: Type of pheromone
            location: Dict with 'domain_mixture', 'template', 'role'
            strength: Deposit strength (default from config)
            metadata: Additional metadata

        Returns:
            Deposit ID
        """
        strength = strength or self.config.base_deposit_strength
        ptype_idx = self._pheromone_type_index(pheromone_type)

        # Deposit in domain field
        if 'domain_mixture' in location:
            i, j = self._domain_to_indices(location['domain_mixture'])
            current = self.domain_field[i, j, ptype_idx]
            self.domain_field[i, j, ptype_idx] = min(
                current + strength,
                self.config.max_concentration
            )

        # Deposit in template field
        if 'template' in location:
            template_idx = self._template_to_index(location['template'])
            if template_idx is not None:
                current = self.template_field[template_idx, ptype_idx]
                self.template_field[template_idx, ptype_idx] = min(
                    current + strength,
                    self.config.max_concentration
                )

        # Deposit in role field
        if 'role' in location:
            role_idx = self._role_to_index(location['role'])
            if role_idx is not None:
                current = self.role_field[role_idx, ptype_idx]
                self.role_field[role_idx, ptype_idx] = min(
                    current + strength,
                    self.config.max_concentration
                )

        # Deposit in combined field
        if all(k in location for k in ['domain_mixture', 'template', 'role']):
            i, j = self._domain_to_indices(location['domain_mixture'])
            t = self._template_to_index(location['template']) or 0
            r = self._role_to_index(location['role']) or 0
            current = self.combined_field[i, j, t, r, ptype_idx]
            self.combined_field[i, j, t, r, ptype_idx] = min(
                current + strength,
                self.config.max_concentration
            )

        # Record deposit
        self._deposit_counter += 1
        deposit_id = f"d_{self._deposit_counter}"
        loc_tuple = self._location_to_tuple(location)

        self.deposits[deposit_id] = PheromoneDeposit(
            deposit_id=deposit_id,
            pheromone_type=pheromone_type,
            location=loc_tuple,
            strength=strength,
            timestamp=time.time(),
            metadata=metadata or {},
            decay_rate=self.config.type_specific_rates.get(
                pheromone_type.value, self.config.base_evaporation_rate
            )
        )

        return deposit_id

    def _location_to_tuple(self, location: Dict[str, Any]) -> Tuple:
        """Convert location dict to tuple for storage"""
        parts = []
        if 'domain_mixture' in location:
            dm = location['domain_mixture']
            parts.extend([dm.get('CLD', 0), dm.get('D1', 0), dm.get('D2', 0)])
        if 'template' in location:
            parts.append(self._template_to_index(location['template']))
        if 'role' in location:
            parts.append(self._role_to_index(location['role']))
        return tuple(parts)

    def _template_to_index(self, template: str) -> Optional[int]:
        """Map V36 template to index"""
        template_map = {
            'STABLE_AUTOREGRESSIVE': 0, 'stable_autoregressive': 0,
            'RESPONSIVE_AUTOREGRESSIVE': 1, 'responsive_autoregressive': 1,
            'UNSTABLE_AUTOREGRESSIVE': 2, 'unstable_autoregressive': 2,
            'DELAYED_RESPONSE': 3, 'delayed_response': 3,
            'NONLINEAR_EXPONENTIAL': 4, 'nonlinear_exponential': 4,
            'NONLINEAR_MULTIPLICATIVE': 5, 'nonlinear_multiplicative': 5,
            'REGIME_DEPENDENT': 6, 'regime_dependent': 6
        }
        return template_map.get(template)

    def _role_to_index(self, role: str) -> Optional[int]:
        """Map V36 functional role to index"""
        role_map = {
            'slow_driver': 0, 'fast_responder': 1, 'mid_mediator': 2,
            'nested_mediator': 3, 'regime_detector': 4, 'transmission_driver': 5,
            'behaviour_moderator': 6, 'macro_sentiment': 7, 'policy_pressure': 8
        }
        return role_map.get(role)

    # =========================================================================
    # SENSING OPERATIONS
    # =========================================================================

    def sense(self, location: Dict[str, Any],
              pheromone_type: Optional[PheromoneType] = None,
              radius: float = None) -> Dict[str, float]:
        """
        Sense pheromone concentration at/around a location.

        Args:
            location: Location to sense at
            pheromone_type: Specific type to sense (None for all)
            radius: Sensing radius (0 for exact location)

        Returns:
            Dict of pheromone_type -> concentration
        """
        radius = radius if radius is not None else self.config.default_sense_radius

        # Apply evaporation first
        self._evaporate()

        concentrations = {}

        # Determine which pheromone types to sense
        if pheromone_type:
            ptypes = [pheromone_type]
        else:
            ptypes = list(PheromoneType)

        for ptype in ptypes:
            ptype_idx = self._pheromone_type_index(ptype)
            concentration = 0.0

            # Sense domain field
            if 'domain_mixture' in location:
                i, j = self._domain_to_indices(location['domain_mixture'])
                if radius == 0:
                    concentration += self.domain_field[i, j, ptype_idx]
                else:
                    # Sum in radius
                    bins = self.config.domain_mixture_bins
                    r_bins = max(1, int(radius * bins))
                    for di in range(-r_bins, r_bins + 1):
                        for dj in range(-r_bins, r_bins + 1):
                            ni, nj = i + di, j + dj
                            if 0 <= ni < bins and 0 <= nj < bins:
                                dist = np.sqrt(di*di + dj*dj) / bins
                                if dist <= radius:
                                    weight = 1.0 - dist/radius
                                    concentration += weight * self.domain_field[ni, nj, ptype_idx]

            # Sense template field
            if 'template' in location:
                t_idx = self._template_to_index(location['template'])
                if t_idx is not None:
                    concentration += self.template_field[t_idx, ptype_idx]

            # Sense role field
            if 'role' in location:
                r_idx = self._role_to_index(location['role'])
                if r_idx is not None:
                    concentration += self.role_field[r_idx, ptype_idx]

            concentrations[ptype.value] = concentration

        return concentrations

    def sense_gradient(self, location: Dict[str, Any],
                       pheromone_type: PheromoneType) -> Dict[str, float]:
        """
        Compute pheromone gradient at a location.
        Returns direction of steepest ascent in domain mixture space.
        """
        self._evaporate()

        if 'domain_mixture' not in location:
            return {'CLD': 0, 'D1': 0, 'D2': 0}

        ptype_idx = self._pheromone_type_index(pheromone_type)
        i, j = self._domain_to_indices(location['domain_mixture'])
        bins = self.config.domain_mixture_bins

        # Compute gradient using central differences
        grad_i = 0.0
        grad_j = 0.0

        if i > 0 and i < bins - 1:
            grad_i = (self.domain_field[i+1, j, ptype_idx] -
                     self.domain_field[i-1, j, ptype_idx]) / 2
        elif i == 0:
            grad_i = self.domain_field[i+1, j, ptype_idx] - self.domain_field[i, j, ptype_idx]
        else:
            grad_i = self.domain_field[i, j, ptype_idx] - self.domain_field[i-1, j, ptype_idx]

        if j > 0 and j < bins - 1:
            grad_j = (self.domain_field[i, j+1, ptype_idx] -
                     self.domain_field[i, j-1, ptype_idx]) / 2
        elif j == 0:
            grad_j = self.domain_field[i, j+1, ptype_idx] - self.domain_field[i, j, ptype_idx]
        else:
            grad_j = self.domain_field[i, j, ptype_idx] - self.domain_field[i, j-1, ptype_idx]

        # Convert to domain mixture gradient
        # grad_i corresponds to CLD direction
        # grad_j corresponds to D1 direction
        # D2 = 1 - CLD - D1, so grad_D2 = -grad_i - grad_j
        return {
            'CLD': float(grad_i),
            'D1': float(grad_j),
            'D2': float(-grad_i - grad_j)
        }

    # =========================================================================
    # EVAPORATION
    # =========================================================================

    def _evaporate(self):
        """Apply time-based evaporation to all fields"""
        current_time = time.time()
        elapsed = current_time - self._last_evaporation

        if elapsed < 0.1:  # Don't evaporate too frequently
            return

        self._last_evaporation = current_time

        # Evaporate each pheromone type with its specific rate
        for ptype in PheromoneType:
            ptype_idx = self._pheromone_type_index(ptype)
            rate = self.config.type_specific_rates.get(
                ptype.value, self.config.base_evaporation_rate
            )
            decay_factor = np.exp(-rate * elapsed)

            self.domain_field[:, :, ptype_idx] *= decay_factor
            self.template_field[:, ptype_idx] *= decay_factor
            self.role_field[:, ptype_idx] *= decay_factor
            self.combined_field[:, :, :, :, ptype_idx] *= decay_factor

    def evaporate_manual(self, rate_multiplier: float = 1.0):
        """Manually trigger evaporation with optional rate multiplier"""
        for ptype in PheromoneType:
            ptype_idx = self._pheromone_type_index(ptype)
            rate = self.config.type_specific_rates.get(
                ptype.value, self.config.base_evaporation_rate
            ) * rate_multiplier

            self.domain_field[:, :, ptype_idx] *= (1 - rate)
            self.template_field[:, ptype_idx] *= (1 - rate)
            self.role_field[:, ptype_idx] *= (1 - rate)
            self.combined_field[:, :, :, :, ptype_idx] *= (1 - rate)

    # =========================================================================
    # V36 INTEGRATION
    # =========================================================================

    def deposit_exploration(self, domain_mixture: Dict[str, float],
                            template: str = None, role: str = None,
                            strength: float = 1.0):
        """Deposit exploration pheromone for a visited region"""
        location = {'domain_mixture': domain_mixture}
        if template:
            location['template'] = template
        if role:
            location['role'] = role
        return self.deposit(PheromoneType.EXPLORATION, location, strength)

    def deposit_success(self, domain_mixture: Dict[str, float],
                        template: str = None, role: str = None,
                        strength: float = 2.0, hypothesis_id: str = None):
        """Deposit success pheromone for a hypothesis that passed falsification"""
        location = {'domain_mixture': domain_mixture}
        if template:
            location['template'] = template
        if role:
            location['role'] = role
        metadata = {'hypothesis_id': hypothesis_id} if hypothesis_id else {}
        return self.deposit(PheromoneType.SUCCESS, location, strength, metadata)

    def deposit_failure(self, domain_mixture: Dict[str, float],
                        constraint_id: str = None, severity: str = None,
                        strength: float = 1.5):
        """Deposit failure pheromone for constraint violation"""
        location = {'domain_mixture': domain_mixture}
        metadata = {
            'constraint_id': constraint_id,
            'severity': severity
        }
        return self.deposit(PheromoneType.FAILURE, location, strength, metadata)

    def deposit_analogy(self, domain_a: str, domain_b: str,
                        role_a: str, role_b: str,
                        similarity: float, strength: float = 2.0):
        """Deposit analogy pheromone for discovered cross-domain connection"""
        # Deposit in both domain locations
        dm_a = {domain_a: 1.0, 'CLD': 0, 'D1': 0, 'D2': 0}
        dm_a[domain_a] = 1.0
        dm_b = {domain_b: 1.0, 'CLD': 0, 'D1': 0, 'D2': 0}
        dm_b[domain_b] = 1.0

        metadata = {
            'domain_a': domain_a, 'domain_b': domain_b,
            'role_a': role_a, 'role_b': role_b,
            'similarity': similarity
        }

        self.deposit(PheromoneType.ANALOGY,
                    {'domain_mixture': dm_a, 'role': role_a},
                    strength * similarity, metadata)
        return self.deposit(PheromoneType.ANALOGY,
                           {'domain_mixture': dm_b, 'role': role_b},
                           strength * similarity, metadata)

    def deposit_novelty(self, observation_family: str,
                        domain_mixture: Dict[str, float],
                        strength: float = 3.0):
        """Deposit novelty pheromone for discovered novel mechanism"""
        location = {'domain_mixture': domain_mixture}
        metadata = {'observation_family': observation_family}
        return self.deposit(PheromoneType.NOVELTY, location, strength, metadata)

    def suggest_exploration_direction(self,
                                       current_mixture: Dict[str, float],
                                       strategy: str = 'balanced') -> Dict[str, float]:
        """
        Suggest next exploration direction based on pheromone landscape.

        Strategies:
        - 'balanced': Balance exploration vs exploitation
        - 'explore': Move toward unexplored regions
        - 'exploit': Move toward successful regions
        - 'avoid_failure': Move away from failure regions
        """
        self._evaporate()

        # Get gradients
        success_grad = self.sense_gradient(
            {'domain_mixture': current_mixture}, PheromoneType.SUCCESS
        )
        failure_grad = self.sense_gradient(
            {'domain_mixture': current_mixture}, PheromoneType.FAILURE
        )
        explore_grad = self.sense_gradient(
            {'domain_mixture': current_mixture}, PheromoneType.EXPLORATION
        )

        # Combine based on strategy
        if strategy == 'balanced':
            direction = {
                'CLD': 0.5 * success_grad['CLD'] - 0.3 * explore_grad['CLD'] - 0.2 * failure_grad['CLD'],
                'D1': 0.5 * success_grad['D1'] - 0.3 * explore_grad['D1'] - 0.2 * failure_grad['D1'],
                'D2': 0.5 * success_grad['D2'] - 0.3 * explore_grad['D2'] - 0.2 * failure_grad['D2']
            }
        elif strategy == 'explore':
            direction = {
                'CLD': -explore_grad['CLD'],
                'D1': -explore_grad['D1'],
                'D2': -explore_grad['D2']
            }
        elif strategy == 'exploit':
            direction = success_grad
        elif strategy == 'avoid_failure':
            direction = {
                'CLD': -failure_grad['CLD'],
                'D1': -failure_grad['D1'],
                'D2': -failure_grad['D2']
            }
        else:
            direction = {'CLD': 0, 'D1': 0, 'D2': 0}

        # Normalize
        mag = np.sqrt(sum(v**2 for v in direction.values()))
        if mag > 0:
            direction = {k: v/mag for k, v in direction.items()}

        return direction

    def get_hot_spots(self, pheromone_type: PheromoneType,
                      threshold: float = 0.5,
                      top_k: int = 5) -> List[Tuple[Dict[str, float], float]]:
        """
        Get regions with high pheromone concentration.

        Returns:
            List of (domain_mixture, concentration) tuples
        """
        self._evaporate()

        ptype_idx = self._pheromone_type_index(pheromone_type)
        field = self.domain_field[:, :, ptype_idx]

        spots = []
        bins = self.config.domain_mixture_bins

        for i in range(bins):
            for j in range(bins):
                conc = field[i, j]
                if conc >= threshold:
                    domain = self._indices_to_domain(i, j)
                    spots.append((domain, float(conc)))

        # Sort by concentration
        spots.sort(key=lambda x: x[1], reverse=True)
        return spots[:top_k]

    # =========================================================================
    # SERIALIZATION
    # =========================================================================

    def to_dict(self) -> Dict:
        """Serialize pheromone field to dictionary"""
        return {
            "config": {
                "domain_mixture_bins": self.config.domain_mixture_bins,
                "template_count": self.config.template_count,
                "role_count": self.config.role_count,
                "base_evaporation_rate": self.config.base_evaporation_rate,
                "type_specific_rates": self.config.type_specific_rates,
                "base_deposit_strength": self.config.base_deposit_strength,
                "max_concentration": self.config.max_concentration
            },
            "domain_field": self.domain_field.tolist(),
            "template_field": self.template_field.tolist(),
            "role_field": self.role_field.tolist(),
            "deposits": {
                did: {
                    "deposit_id": d.deposit_id,
                    "pheromone_type": d.pheromone_type.value,
                    "location": d.location,
                    "strength": d.strength,
                    "timestamp": d.timestamp,
                    "metadata": d.metadata,
                    "decay_rate": d.decay_rate
                }
                for did, d in self.deposits.items()
            }
        }

    def save(self, filepath: str):
        """Save pheromone field to file"""
        with open(filepath, 'w') as f:
            json.dump(self.to_dict(), f)

    @classmethod
    def load(cls, filepath: str) -> 'DigitalPheromoneField':
        """Load pheromone field from file"""
        with open(filepath, 'r') as f:
            data = json.load(f)

        config = PheromoneFieldConfig(
            domain_mixture_bins=data["config"]["domain_mixture_bins"],
            template_count=data["config"]["template_count"],
            role_count=data["config"]["role_count"],
            base_evaporation_rate=data["config"]["base_evaporation_rate"],
            type_specific_rates=data["config"]["type_specific_rates"],
            base_deposit_strength=data["config"]["base_deposit_strength"],
            max_concentration=data["config"]["max_concentration"]
        )

        field = cls(config)
        field.domain_field = np.array(data["domain_field"], dtype=np.float32)
        field.template_field = np.array(data["template_field"], dtype=np.float32)
        field.role_field = np.array(data["role_field"], dtype=np.float32)

        for did, ddata in data["deposits"].items():
            field.deposits[did] = PheromoneDeposit(
                deposit_id=ddata["deposit_id"],
                pheromone_type=PheromoneType(ddata["pheromone_type"]),
                location=tuple(ddata["location"]),
                strength=ddata["strength"],
                timestamp=ddata["timestamp"],
                metadata=ddata["metadata"],
                decay_rate=ddata["decay_rate"]
            )

        return field

    def stats(self) -> Dict[str, Any]:
        """Get pheromone field statistics"""
        self._evaporate()

        stats = {
            "total_deposits": len(self.deposits),
            "deposits_by_type": {},
            "field_stats": {}
        }

        for ptype in PheromoneType:
            ptype_idx = self._pheromone_type_index(ptype)

            # Count deposits by type
            count = sum(1 for d in self.deposits.values()
                       if d.pheromone_type == ptype)
            stats["deposits_by_type"][ptype.value] = count

            # Field statistics
            domain_vals = self.domain_field[:, :, ptype_idx]
            stats["field_stats"][ptype.value] = {
                "max": float(np.max(domain_vals)),
                "mean": float(np.mean(domain_vals)),
                "nonzero_cells": int(np.sum(domain_vals > 0.01))
            }

        return stats


# =============================================================================
# EXPORTS
# =============================================================================

__all__ = [
    'DigitalPheromoneField',
    'PheromoneType',
    'PheromoneDeposit',
    'PheromoneFieldConfig'
]
