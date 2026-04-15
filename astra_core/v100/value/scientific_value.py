# Copyright 2024-2026 Glenn J. White (The Open University / RAL Space)
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""
Scientific Value Calculator (SVC)
=================================

Estimates the scientific value of potential discoveries.

Multi-dimensional value assessment:
1. Novelty: How unexpected is this?
2. Impact: How many fields would it affect?
3. Feasibility: How likely to succeed?
4. Leverage: What other questions would it answer?
5. Urgency: Will someone else discover this soon?
6. Training value: What capabilities would we develop?
7. Risk/Reward: What if we fail?

This enables rational allocation of scientific resources.

Author: STAN-XI ASTRO V100 Development Team
Version: 1.0.0
"""

from dataclasses import dataclass, field
from typing import Dict, List, Optional, Any, Tuple
from enum import Enum, auto
import numpy as np
import time


# =============================================================================
# Enumerations
# =============================================================================

class DiscoveryType(Enum):
    """Types of scientific discoveries"""
    NEW_ENTITY = "new_entity"  # New particle, field, object
    NEW_MECHANISM = "new_mechanism"  # New causal mechanism
    NEW_RELATION = "new_relation"  # New relationship between known entities
    PARADIGM_SHIFT = "paradigm_shift"  # Fundamental rethinking
    UNIFICATION = "unification"  # Unifies disparate phenomena
    MEASUREMENT = "measurement"  # Better measurement of known quantity
    CONTRADICTION_RESOLUTION = "contradiction"  # Resolves conflict
    PREDICTION = "prediction"  # Successful prediction of new phenomenon
    EXPLORATION = "exploration"  # Characterizes new regime


class DomainImpact(Enum):
    """Scientific domains"""
    ASTROPHYSICS = "astrophysics"
    COSMOLOGY = "cosmology"
    PLANETARY_SCIENCE = "planetary"
    PARTICLE_PHYSICS = "particle_physics"
    BIOLOGY = "biology"
    DATA_SCIENCE = "data_science"
    INSTRUMENTATION = "instrumentation"


# =============================================================================
# Core Data Structures
# =============================================================================

@dataclass
class ResourceBudget:
    """Resources required for a project"""
    time_months: float = 12.0
    people_fte: float = 1.0
    cost_dollars: float = 100000.0
    telescope_hours: float = 0.0
    computing_hours: float = 0.0


@dataclass
class ValueDimensions:
    """Multi-dimensional value assessment"""
    novelty: float  # [0, 1] How unexpected?
    impact: float  # [0, 1] How many fields affected?
    feasibility: float  # [0, 1] How likely to succeed?
    leverage: float  # [0, 1] What other questions answered?
    urgency: float  # [0, 1] Will others discover it soon?
    training_value: float  # [0, 1] What capabilities developed?
    risk_reward: float  # [0, 1] Risk/reward ratio


@dataclass
class ScientificValue:
    """Complete scientific value assessment"""
    total_score: float  # [0, 100] Overall value
    dimensions: ValueDimensions

    # Components
    discovery_type: DiscoveryType
    affected_domains: List[DomainImpact]
    confidence: float  # [0, 1] In value assessment

    # Comparison
    compared_to_alternatives: Dict[str, float] = field(default_factory=dict)

    # Recommendation
    recommendation: str = ""
    priority: str = ""  # 'high', 'medium', 'low', 'defer'

    # Metadata
    calculated_at: float = field(default_factory=time.time)
    version: int = 1


# =============================================================================
# Scientific Value Calculator
# =============================================================================

class ScientificValueCalculator:
    """
    Calculates multi-dimensional scientific value.

    Uses structured framework to assess:
    - Novelty: Against current knowledge
    - Impact: Across scientific domains
    - Feasibility: Technical and resource constraints
    - Leverage: Enabling other discoveries
    - Urgency: Competitive pressure
    - Training: Skills and infrastructure development
    - Risk/Reward: Potential vs. downside
    """

    def __init__(self):
        self.assessments: Dict[str, ScientificValue] = {}
        self.benchmark_values = self._initialize_benchmarks()

    def _initialize_benchmarks(self) -> Dict[str, float]:
        """Initialize benchmark values for comparison"""
        return {
            'new_particle_discovery': 95,  # Higgs boson
            'gravitational_waves': 90,      # LIGO detection
            'exoplanet_atmosphere': 70,     # JWST characterization
            'standard_candle': 60,          # Improved distance ladder
            'catalog_publication': 40,       # Survey catalog
            'confirmatory_observation': 30, # Confirm existing theory
        }

    def calculate_value(
        self,
        discovery_description: str,
        discovery_type: DiscoveryType,
        affected_domains: List[DomainImpact],
        resources: ResourceBudget,
        current_knowledge: Optional[Dict[str, Any]] = None
    ) -> ScientificValue:
        """
        Calculate multi-dimensional scientific value.

        Parameters
        ----------
        discovery_description : str
            What would be discovered
        discovery_type : DiscoveryType
            Type of discovery
        affected_domains : list
            Scientific domains affected
        resources : ResourceBudget
            Required resources
        current_knowledge : dict, optional
            Current state of knowledge

        Returns
        -------
        ScientificValue with complete assessment
        """
        print(f"SVC: Calculating value for {discovery_type.value}")

        # Assess each dimension
        novelty = self._assess_novelty(discovery_type, current_knowledge)
        impact = self._assess_impact(affected_domains, discovery_type)
        feasibility = self._assess_feasibility(resources, discovery_type)
        leverage = self._assess_leverage(discovery_type, affected_domains)
        urgency = self._assess_urgency(discovery_type, affected_domains)
        training = self._assess_training(discovery_type, resources)
        risk_reward = self._assess_risk_reward(discovery_type, resources)

        dimensions = ValueDimensions(
            novelty=novelty,
            impact=impact,
            feasibility=feasibility,
            leverage=leverage,
            urgency=urgency,
            training_value=training,
            risk_reward=risk_reward
        )

        # Calculate total score (weighted sum)
        weights = {
            'novelty': 0.25,
            'impact': 0.20,
            'feasibility': 0.15,
            'leverage': 0.15,
            'urgency': 0.10,
            'training': 0.10,
            'risk_reward': 0.05,
        }

        total = (
            weights['novelty'] * novelty +
            weights['impact'] * impact +
            weights['feasibility'] * feasibility +
            weights['leverage'] * leverage +
            weights['urgency'] * urgency +
            weights['training'] * training +
            weights['risk_reward'] * risk_reward
        ) * 100

        # Generate recommendation
        priority, recommendation = self._generate_recommendation(total, dimensions, resources)

        return ScientificValue(
            total_score=total,
            dimensions=dimensions,
            discovery_type=discovery_type,
            affected_domains=affected_domains,
            confidence=0.7,
            recommendation=recommendation,
            priority=priority
        )

    def _assess_novelty(
        self,
        discovery_type: DiscoveryType,
        current_knowledge: Optional[Dict[str, Any]]
    ) -> float:
        """Assess novelty of discovery [0, 1]"""
        base_novelty = {
            DiscoveryType.NEW_ENTITY: 0.9,
            DiscoveryType.PARADIGM_SHIFT: 1.0,
            DiscoveryType.NEW_MECHANISM: 0.7,
            DiscoveryType.UNIFICATION: 0.6,
            DiscoveryType.NEW_RELATION: 0.5,
            DiscoveryType.CONTRADICTION_RESOLUTION: 0.4,
            DiscoveryType.PREDICTION: 0.3,
            DiscoveryType.MEASUREMENT: 0.2,
            DiscoveryType.EXPLORATION: 0.5,
        }

        score = base_novelty.get(discovery_type, 0.5)

        # Adjust based on current knowledge
        if current_knowledge:
            known_fraction = current_knowledge.get('known_fraction', 0.5)
            score *= (1 - known_fraction)

        return max(0, min(1, score))

    def _assess_impact(
        self,
        affected_domains: List[DomainImpact],
        discovery_type: DiscoveryType
    ) -> float:
        """Assess impact across domains [0, 1]"""
        if not affected_domains:
            return 0.3

        # Base score from number of domains
        domain_count = len(affected_domains)
        score = min(1.0, 0.2 + 0.2 * domain_count)

        # Bonus for cross-domain impact
        unique_domains = len(set(d.value for d in affected_domains))
        if unique_domains > 1:
            score *= 1.2

        # Bonus for paradigm shift
        if discovery_type == DiscoveryType.PARADIGM_SHIFT:
            score *= 1.5
        elif discovery_type == DiscoveryType.UNIFICATION:
            score *= 1.3

        return max(0, min(1, score))

    def _assess_feasibility(
        self,
        resources: ResourceBudget,
        discovery_type: DiscoveryType
    ) -> float:
        """Assess feasibility of success [0, 1]"""
        score = 0.7  # Base feasibility

        # Adjust based on resource requirements
        if resources.cost_dollars > 1e6:  # > $1M
            score *= 0.7
        elif resources.cost_dollars > 1e5:  # > $100k
            score *= 0.9

        if resources.telescope_hours > 100:
            score *= 0.8

        if resources.time_months > 36:  # > 3 years
            score *= 0.7

        # Adjust based on discovery type
        if discovery_type == DiscoveryType.PARADIGM_SHIFT:
            score *= 0.5  # Harder to achieve paradigm shifts
        elif discovery_type == DiscoveryType.MEASUREMENT:
            score *= 1.2  # Measurements are usually feasible

        return max(0, min(1, score))

    def _assess_leverage(
        self,
        discovery_type: DiscoveryType,
        affected_domains: List[DomainImpact]
    ) -> float:
        """Assess leverage - what other questions would this answer? [0, 1]"""
        score = 0.5

        # Paradigm shifts have high leverage
        if discovery_type == DiscoveryType.PARADIGM_SHIFT:
            score = 0.9
        elif discovery_type == DiscoveryType.UNIFICATION:
            score = 0.8
        elif discovery_type == DiscoveryType.NEW_ENTITY:
            score = 0.7

        # Cross-domain discoveries have more leverage
        if len(affected_domains) > 2:
            score *= 1.2

        return max(0, min(1, score))

    def _assess_urgency(
        self,
        discovery_type: DiscoveryType,
        affected_domains: List[DomainImpact]
    ) -> float:
        """Assess urgency - will someone else discover this soon? [0, 1]"""
        score = 0.5

        # High urgency for hot topics
        if DomainImpact.ASTROPHYSICS in affected_domains:
            # Exoplanets, gravitational waves are competitive
            score = 0.7

        if discovery_type == DiscoveryType.PREDICTION:
            # If we predict it, we should verify it soon
            score = 0.8

        return max(0, min(1, score))

    def _assess_training(
        self,
        discovery_type: DiscoveryType,
        resources: ResourceBudget
    ) -> float:
        """Assess training value - what capabilities would be developed? [0, 1]"""
        score = 0.5

        # New techniques often have high training value
        if discovery_type in [DiscoveryType.NEW_MECHANISM, DiscoveryType.UNIFICATION]:
            score = 0.8

        # Large projects build infrastructure
        if resources.cost_dollars > 5e5:
            score = 0.7

        return max(0, min(1, score))

    def _assess_risk_reward(
        self,
        discovery_type: DiscoveryType,
        resources: ResourceBudget
    ) -> float:
        """Assess risk/reward ratio [0, 1]"""
        # High risk, high reward for novel discoveries
        if discovery_type == DiscoveryType.PARADIGM_SHIFT:
            reward = 1.0
            risk = 0.8
        elif discovery_type == DiscoveryType.NEW_ENTITY:
            reward = 0.9
            risk = 0.6
        elif discovery_type == DiscoveryType.MEASUREMENT:
            reward = 0.4
            risk = 0.1  # Low risk
        else:
            reward = 0.6
            risk = 0.3

        # Risk-adjusted return
        if risk > 0:
            return reward * (1 - risk * 0.5)
        return reward

    def _generate_recommendation(
        self,
        total_score: float,
        dimensions: ValueDimensions,
        resources: ResourceBudget
    ) -> Tuple[str, str]:
        """Generate priority and recommendation"""
        if total_score > 75:
            priority = "high"
            recommendation = "PURSUE - High scientific value. Allocate significant resources."
        elif total_score > 50:
            priority = "medium"
            recommendation = "CONSIDER - Moderate scientific value. Pursue if resources available."
        elif total_score > 30:
            priority = "low"
            recommendation = "DEFER - Lower priority. Consider if no better options."
        else:
            priority = "very_low"
            recommendation = "AVOID - Low scientific value relative to cost."

        return priority, recommendation


# =============================================================================
# Factory Functions
# =============================================================================

def create_scientific_value_calculator() -> ScientificValueCalculator:
    """Create a scientific value calculator"""
    return ScientificValueCalculator()


# =============================================================================
# Convenience Functions
# =============================================================================

def assess_scientific_value(
    discovery_description: str,
    discovery_type: DiscoveryType,
    domains: List[DomainImpact],
    resources: ResourceBudget
) -> ScientificValue:
    """
    Convenience function to assess scientific value.
    """
    calculator = create_scientific_value_calculator()
    return calculator.calculate_value(
        discovery_description=discovery_description,
        discovery_type=discovery_type,
        affected_domains=domains,
        resources=resources
    )


# =============================================================================
# Exports
# =============================================================================

__all__ = [
    'DiscoveryType',
    'DomainImpact',
    'ResourceBudget',
    'ValueDimensions',
    'ScientificValue',
    'ScientificValueCalculator',
    'create_scientific_value_calculator',
    'assess_scientific_value',
]
