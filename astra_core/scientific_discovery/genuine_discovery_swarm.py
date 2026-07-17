"""
Genuine Discovery Swarm Intelligence Integration

Implements pheromone-guided exploration for genuine discovery using
DigitalPheromoneField for directed hypothesis space exploration.

This module enables ASTRA to:
- Guide exploration toward promising regions of hypothesis space
- Track successful/failed hypotheses to avoid redundant exploration
- Accelerate cross-domain analogy discovery through pheromone trails
- Implement collective intelligence from shared exploration history

Version: 1.0.0
Date: 2026-07-04
"""

import logging
import numpy as np
from typing import Dict, List, Optional, Any, Tuple
from enum import Enum
from dataclasses import dataclass
from datetime import datetime

logger = logging.getLogger(__name__)

try:
    from astra_core.intelligence.pheromone_dynamics import (
        DigitalPheromoneField,
        PheromoneType,
        PheromoneFieldConfig,
        create_pheromone_field
    )
    SWARM_AVAILABLE = True
except ImportError as e:
    logger.warning(f"Swarm intelligence not available: {e}")
    SWARM_AVAILABLE = False


class DiscoveryPheromoneType(Enum):
    """Pheromone types specific to genuine discovery"""
    EXPLORATION = "exploration"  # Guides exploration of under-explored domains
    SUCCESS = "success"  # Marks genuine discovery locations
    FAILURE = "failure"  # Marks rejected candidates
    ANALOGY = "analogy"  # Marks cross-domain connection opportunities
    NOVELTY = "novelty"  # Marks unexpected/novel findings
    ATTENTION = "attention"  # Marks areas requiring focus
    MECHANISM = "mechanism"  # Marks causal mechanism discoveries


@dataclass
class PheromoneDeposit:
    """Record of pheromone deposit"""
    location: Tuple[str, ...]  # Domain coordinates
    pheromone_type: DiscoveryPheromoneType
    strength: float  # Pheromone strength 0-1
    timestamp: str  # When deposited
    discovery_context: Optional[str] = None  # What led to this deposit


class GenuineDiscoverySwarm:
    """
    Swarm intelligence system for genuine discovery exploration.

    Uses pheromone trails to guide exploration toward promising regions of
    hypothesis space while avoiding redundant exploration of rejected areas.
    """

    def __init__(self, config: Optional[Any] = None):
        if not SWARM_AVAILABLE:
            logger.warning("[Swarm] Swarm capabilities not available, running without pheromone guidance")
            self.enabled = False
            return

        self.enabled = True
        self.config = config

        # Initialize pheromone field with discovery-specific configuration.
        # Kwargs aligned to the REAL PheromoneFieldConfig in
        # astra_core/intelligence/pheromone_dynamics.py (domain_mixture_bins,
        # base_evaporation_rate, max_concentration, default_sense_radius).
        field_config = PheromoneFieldConfig(
            domain_mixture_bins=50,       # resolution: 50 bins per domain axis
            base_evaporation_rate=0.05,   # ~5% decay/evaporation per cycle
            max_concentration=10.0,       # cap pheromone strength
            default_sense_radius=0.1      # sensing neighborhood
        )

        self.pheromone_field = create_pheromone_field(field_config)
        self.deposits: List[PheromoneDeposit] = []
        self.exploration_history: Dict[str, List] = {}  # Track exploration by domain

        logger.info("[Swarm] ✅ Genuine Discovery Swarm initialized with enhanced pheromone field")

    def deposit_pheromone(self, location: Tuple[str, ...], pheromone_type: DiscoveryPheromoneType,
                          strength: float = 1.0, discovery_context: Optional[str] = None):
        """
        Deposit pheromone at discovery location for future guidance.

        Args:
            location: Domain coordinates (tuple of domain names)
            pheromone_type: Type of pheromone to deposit
            strength: Pheromone strength 0-1
            discovery_context: Optional context about what led to this deposit
        """
        if not self.enabled:
            return

        # Create deposit record
        deposit = PheromoneDeposit(
            location=location,
            pheromone_type=pheromone_type,
            strength=strength,
            timestamp=datetime.now().isoformat(),
            discovery_context=discovery_context
        )

        self.deposits.append(deposit)

        # Convert location to a pheromone-field location dict
        field_location = self._domains_to_location(location)
        field_ptype = self._to_field_pheromone_type(pheromone_type)

        # Deposit pheromone in field
        self.pheromone_field.deposit(
            pheromone_type=field_ptype,
            location=field_location,
            strength=strength
        )

        logger.debug(f"[Swarm] Deposited {pheromone_type.value} pheromone at {location} with strength {strength}")

    def sense_pheromones(self, location: Tuple[str, ...], pheromone_type: Optional[DiscoveryPheromoneType] = None) -> Dict[str, float]:
        """
        Sense pheromone concentrations at given location.

        Args:
            location: Domain coordinates to check
            pheromone_type: Specific pheromone type or None for all types

        Returns:
            Dictionary of pheromone type -> concentration
        """
        if not self.enabled:
            return {}

        field_location = self._domains_to_location(location)

        if pheromone_type:
            field_ptype = self._to_field_pheromone_type(pheromone_type)
            concentrations = self.pheromone_field.sense(
                location=field_location,
                pheromone_type=field_ptype
            )
            return concentrations
        else:
            # Sense all pheromone types
            return self.pheromone_field.sense(location=field_location)

    def compute_exploration_gradient(self, current_location: Tuple[str, ...]) -> Dict[str, float]:
        """
        Compute gradient for directed exploration toward promising areas.

        Args:
            current_location: Current domain coordinates

        Returns:
            Dictionary suggesting exploration directions (domain -> attraction strength)
        """
        if not self.enabled:
            return {}

        field_location = self._domains_to_location(current_location)

        # Compute gradient using pheromone field (steepest ascent in success pheromone)
        gradient = self.pheromone_field.sense_gradient(
            location=field_location,
            pheromone_type=PheromoneType.SUCCESS
        )

        # Convert numeric gradient back to domain directions
        domain_directions = self._coordinates_to_domains(gradient)

        return domain_directions

    def get_pheromone_concentration(self, location: Tuple[str, ...], pheromone_type: DiscoveryPheromoneType) -> float:
        """Get concentration of specific pheromone type at location"""
        concentrations = self.sense_pheromones(location, pheromone_type)
        return concentrations.get(pheromone_type.value, 0.0)

    def suggest_exploration_domains(self, num_suggestions: int = 3) -> List[Tuple[str, ...]]:
        """
        Suggest domains for exploration based on pheromone field analysis.

        Args:
            num_suggestions: Number of domain suggestions to return

        Returns:
            List of domain tuples (ordered by attractiveness)
        """
        if not self.enabled:
            # Return random domains if swarm not available
            return [("random", "exploration")]

        # Find areas with high EXPLORATION pheromone and low FAILURE pheromone
        suggestions = []

        # Locate exploration pheromone hot spots via the real field API
        exploration_spots = self.pheromone_field.get_hot_spots(
            pheromone_type=PheromoneType.EXPLORATION,
            threshold=0.3,
            top_k=max(num_suggestions * 3, 10)
        )

        # Filter out hot spots that also have high failure pheromone
        for domain_mixture, _exploration_conc in exploration_spots:
            failure_reading = self.pheromone_field.sense(
                location={'domain_mixture': domain_mixture},
                pheromone_type=PheromoneType.FAILURE
            )
            failure_conc = failure_reading.get(PheromoneType.FAILURE.value, 0.0)
            if failure_conc < 0.2:
                domain_tuple = tuple(domain_mixture.keys())
                suggestions.append(domain_tuple)

                if len(suggestions) >= num_suggestions:
                    break

        return suggestions if suggestions else [("default", "exploration")]

    def update_exploration_history(self, domains: Tuple[str, ...], result: str, outcome: str):
        """
        Update exploration history based on discovery attempt results.

        Args:
            domains: Domains that were explored
            result: Brief description of what was found
            outcome: "success" | "failure" | "partial" | "novel"
        """
        domain_key = str(domains)

        if domain_key not in self.exploration_history:
            self.exploration_history[domain_key] = []

        self.exploration_history[domain_key].append({
            "result": result,
            "outcome": outcome,
            "timestamp": datetime.now().isoformat()
        })

        # Deposit appropriate pheromones based on outcome
        if outcome == "success":
            self.deposit_pheromone(domains, DiscoveryPheromoneType.SUCCESS, strength=0.8)
        elif outcome == "failure":
            self.deposit_pheromone(domains, DiscoveryPheromoneType.FAILURE, strength=0.6)
        elif outcome == "novel":
            self.deposit_pheromone(domains, DiscoveryPheromoneType.NOVELTY, strength=0.7)

    def get_exploration_statistics(self) -> Dict[str, Any]:
        """Get statistics about exploration guided by pheromone field"""
        if not self.enabled:
            return {"swarm_enabled": False}

        total_deposits = len(self.deposits)
        deposits_by_type = {}
        for deposit in self.deposits:
            ptype = deposit.pheromone_type.value
            deposits_by_type[ptype] = deposits_by_type.get(ptype, 0) + 1

        field_stats = self.pheromone_field.stats()
        field_stats_by_type = field_stats.get("field_stats", {})

        # Derive aggregate coverage and average concentration from per-type stats
        means = [fs.get("mean", 0.0) for fs in field_stats_by_type.values()]
        avg_concentration = sum(means) / len(means) if means else 0.0
        nonzero_types = sum(
            1 for fs in field_stats_by_type.values() if fs.get("nonzero_cells", 0) > 0
        )
        coverage = nonzero_types / len(field_stats_by_type) if field_stats_by_type else 0.0

        return {
            "swarm_enabled": True,
            "total_deposits": total_deposits,
            "deposits_by_type": deposits_by_type,
            "exploration_history_size": len(self.exploration_history),
            "field_coverage": coverage,
            "average_pheromone_concentration": avg_concentration
        }

    def _domains_to_coordinates(self, domains: Tuple[str, ...]) -> np.ndarray:
        """Convert domain names to numeric coordinates for pheromone field"""
        # Simple hash-based conversion
        coords = []
        for i, domain in enumerate(domains[:10]):  # Limit to 10 dimensions
            # Use string hash to create coordinate 0-1
            domain_hash = hash(domain) % 1000 / 1000.0
            coords.append(domain_hash)

        return np.array(coords)

    def _coordinates_to_domains(self, coordinates) -> Dict[str, float]:
        """
        Convert a numeric gradient / pheromone reading to domain attraction strengths.

        Handles both numpy arrays/sequences and the dict output of sense_gradient.
        """
        if isinstance(coordinates, dict):
            return {str(k): float(v) for k, v in coordinates.items()}
        return {f"domain_{i}": float(v) for i, v in enumerate(coordinates)}

    def _domains_to_location(self, domains: Tuple[str, ...]) -> Dict[str, Any]:
        """Convert domain names to a pheromone-field location dict."""
        coords = self._domains_to_coordinates(domains)
        cld = float(coords[0]) if len(coords) > 0 else 0.33
        d1 = float(coords[1]) if len(coords) > 1 else 0.33
        d2 = max(0.0, 1.0 - cld - d1)
        total = (cld + d1 + d2) or 1.0
        return {
            'domain_mixture': {
                'CLD': cld / total,
                'D1': d1 / total,
                'D2': d2 / total
            }
        }

    def _to_field_pheromone_type(self, ptype: DiscoveryPheromoneType) -> "PheromoneType":
        """Map a DiscoveryPheromoneType to the pheromone field's PheromoneType enum."""
        try:
            return PheromoneType(ptype.value)
        except ValueError:
            # Types like MECHANISM have no field equivalent; fall back to EXPLORATION
            return PheromoneType.EXPLORATION


def create_genuine_discovery_swarm(config: Optional[Any] = None) -> GenuineDiscoverySwarm:
    """Factory function to create genuine discovery swarm"""
    return GenuineDiscoverySwarm(config)