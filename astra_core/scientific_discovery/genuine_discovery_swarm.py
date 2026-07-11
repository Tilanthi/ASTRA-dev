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

        # Initialize pheromone field with discovery-specific configuration
        field_config = PheromoneFieldConfig(
            field_dimensions=10,  # 10-dimensional domain space
            resolution=50,  # 50 points per dimension
            decay_rate=0.05,  # 5% decay per cycle
            diffusion_rate=0.1,  # 10% diffusion to neighbors
            evaporation_rate=0.02  # 2% evaporation prevents permanent trails
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

        # Convert location to numeric coordinates
        numeric_coords = self._domains_to_coordinates(location)

        # Deposit pheromone in field
        self.pheromone_field.deposit_pheromone(
            coordinates=numeric_coords,
            pheromone_type=pheromone_type.value,
            amount=strength
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

        numeric_coords = self._domains_to_coordinates(location)

        if pheromone_type:
            concentration = self.pheromone_field.sense_pheromones(
                coordinates=numeric_coords,
                pheromone_type=pheromone_type.value
            )
            return {pheromone_type.value: concentration}
        else:
            # Sense all pheromone types
            concentrations = {}
            for ptype in DiscoveryPheromoneType:
                concentration = self.pheromone_field.sense_pheromones(
                    coordinates=numeric_coords,
                    pheromone_type=ptype.value
                )
                concentrations[ptype.value] = concentration
            return concentrations

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

        current_coords = self._domains_to_coordinates(current_location)

        # Compute gradient using pheromone field
        gradient = self.pheromone_field.compute_gradient(current_coords)

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

        # Find areas with high EXPLORATION and NOVELTY pheromones
        # Avoid areas with high FAILURE pheromones
        suggestions = []

        # Analyze pheromone field to find promising regions
        field_analysis = self.pheromone_field.analyze_field()

        # Simple heuristic: suggest domains with moderate exploration pheromones
        # and low failure pheromones
        for location_key, concentration in field_analysis.items():
            if concentration.get("exploration", 0) > 0.3 and concentration.get("failure", 0) < 0.2:
                # Convert location_key back to domain tuple
                domain_tuple = self._coordinates_to_domains(eval(location_key))
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

        field_stats = self.pheromone_field.get_field_statistics()

        return {
            "swarm_enabled": True,
            "total_deposits": total_deposits,
            "deposits_by_type": deposits_by_type,
            "exploration_history_size": len(self.exploration_history),
            "field_coverage": field_stats.get("coverage", 0.0),
            "average_pheromone_concentration": field_stats.get("average_concentration", 0.0)
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

    def _coordinates_to_domains(self, coordinates: np.ndarray) -> Tuple[str, ...]:
        """Convert numeric coordinates back to domain tuple"""
        # This is a simplified inverse - in practice would use domain mapping
        return tuple(f"coord_{i}" for i in range(len(coordinates)))

    def _coordinates_to_domains(self, gradient: np.ndarray) -> Dict[str, float]:
        """Convert gradient to domain attraction strengths"""
        # Simplified conversion
        return {
            f"domain_{i}": float(gradient[i])
            for i in range(len(gradient))
        }


def create_genuine_discovery_swarm(config: Optional[Any] = None) -> GenuineDiscoverySwarm:
    """Factory function to create genuine discovery swarm"""
    return GenuineDiscoverySwarm(config)