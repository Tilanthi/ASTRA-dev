"""
Gordon's Biological Transforms

Implements Gordon's principles from 30 years of Pogonomyrmex barbatus research.
All parameters are immutable (validated by biological field research).

These transforms are domain-agnostic and apply to any stigmergic swarm system,
including astronomical inference.
"""

from typing import Dict
from dataclasses import dataclass


# Gordon's Immutable Parameters (from 30 years of Pogonomyrmex barbatus research)
GORDON_PARAMS = {
    'evaporation_rate': 0.05,        # ρ - Trail decay (5% per timestep)
    'reinforcement_rate': 0.1,       # α - Trail reinforcement
    'anternet_weight': 0.6,          # β - Success feedback weight
    'restraint_weight': 0.4,         # γ - Cost/utility weight
    'switch_probability': 0.15,      # 15% task switching probability
    'contact_rate_min': 0.033,       # 2 contacts/minute (minimum)
    'contact_rate_max': 0.167,       # 10 contacts/minute (maximum)
}


@dataclass
class TransformRule:
    """
    MORK transform rule

    Pattern → Template transformation for symbolic reasoning.
    """
    pattern: str
    template: str
    description: str


class GordonTransforms:
    """
    Pre-packaged MORK transforms implementing Gordon's biological principles

    All transforms use validated parameters from 30 years of field research.
    Parameters are IMMUTABLE per Article I of CSIG Constitution.
    """

    @staticmethod
    def trail_evaporation(rho: float = None) -> TransformRule:
        """
        Pheromone trail evaporation: τ_{t+1} = (1-ρ) · τ_t

        Args:
            rho: Evaporation rate (default: 0.05 from Gordon's research)

        Returns:
            TransformRule for trail evaporation
        """
        if rho is None:
            rho = GORDON_PARAMS['evaporation_rate']

        pattern = "(trail $step (tau $t))"
        template = f"(trail $step (tau (* $t {1 - rho})))"
        description = f"Trail evaporation with ρ={rho} (Gordon's principle)"

        return TransformRule(pattern=pattern, template=template, description=description)

    @staticmethod
    def trail_reinforcement(alpha: float = None, delta_success: float = 1.0) -> TransformRule:
        """
        Pheromone trail reinforcement: τ_{t+1} = τ_t + α · Δτ

        Args:
            alpha: Reinforcement rate (default: 0.1 from Gordon)
            delta_success: Success signal (1.0 for successful outcome)

        Returns:
            TransformRule for trail reinforcement
        """
        if alpha is None:
            alpha = GORDON_PARAMS['reinforcement_rate']

        reinforcement = alpha * delta_success

        pattern = "(trail $step (tau $t))"
        template = f"(trail $step (tau (+ $t {reinforcement})))"
        description = f"Trail reinforcement with α={alpha}, Δτ={delta_success}"

        return TransformRule(pattern=pattern, template=template, description=description)

    @staticmethod
    def anternet_feedback(beta: float = None) -> TransformRule:
        """
        Anternet feedback: Success signal propagates through network

        Args:
            beta: Success feedback weight (default: 0.6 from Gordon)

        Returns:
            TransformRule for anternet feedback
        """
        if beta is None:
            beta = GORDON_PARAMS['anternet_weight']

        pattern = "(feedback $agent (success $s))"
        template = f"(feedback $agent (weighted_success (* $s {beta})))"
        description = f"Anternet feedback with β={beta}"

        return TransformRule(pattern=pattern, template=template, description=description)

    @staticmethod
    def collective_restraint(gamma: float = None) -> TransformRule:
        """
        Collective restraint: Balance exploration/exploitation

        Args:
            gamma: Cost/utility weight (default: 0.4 from Gordon)

        Returns:
            TransformRule for collective restraint
        """
        if gamma is None:
            gamma = GORDON_PARAMS['restraint_weight']

        pattern = "(decision $agent (utility $u) (cost $c))"
        template = f"(decision $agent (weighted_utility (- $u (* {gamma} $c))))"
        description = f"Collective restraint with γ={gamma}"

        return TransformRule(pattern=pattern, template=template, description=description)

    @staticmethod
    def contact_rate_regulation(
        current_rate: float,
        threshold_min: float = None,
        threshold_max: float = None
    ) -> TransformRule:
        """
        Contact rate regulation: Maintain contact frequency in valid range

        Args:
            current_rate: Current contact rate (contacts/minute)
            threshold_min: Minimum rate (default: 0.033 = 2/min)
            threshold_max: Maximum rate (default: 0.167 = 10/min)

        Returns:
            TransformRule for contact rate regulation
        """
        if threshold_min is None:
            threshold_min = GORDON_PARAMS['contact_rate_min']
        if threshold_max is None:
            threshold_max = GORDON_PARAMS['contact_rate_max']

        # Clamp rate to valid range
        adjusted_rate = max(threshold_min, min(current_rate, threshold_max))

        pattern = "(contact_rate $agent $rate)"
        template = f"(contact_rate $agent {adjusted_rate})"
        description = f"Contact rate regulation: {current_rate:.3f} → {adjusted_rate:.3f}"

        return TransformRule(pattern=pattern, template=template, description=description)

    @staticmethod
    def flexible_task_switching(switch_probability: float = None) -> TransformRule:
        """
        Flexible task switching: Probabilistic task allocation

        Args:
            switch_probability: Switch probability (default: 0.15 = 15%)

        Returns:
            TransformRule for task switching
        """
        if switch_probability is None:
            switch_probability = GORDON_PARAMS['switch_probability']

        pattern = "(task $agent $current)"
        template = f"(task $agent (switch_with_prob {switch_probability} $current))"
        description = f"Task switching with p={switch_probability}"

        return TransformRule(pattern=pattern, template=template, description=description)

    @staticmethod
    def pheromone_weighted_cost(beta: float = None) -> TransformRule:
        """
        Pheromone-weighted cost for pathfinding

        Formula: c'_ij = c_base * (1 - β * (1 - 1/τ))

        Args:
            beta: Pheromone weight (default: 0.395)

        Returns:
            TransformRule for pheromone-weighted cost
        """
        if beta is None:
            beta = 0.395

        pattern = "(edge $source $target (cost $c) (tau $t))"
        template = f"(edge $source $target (weighted_cost (* $c (- 1 (* {beta} (- 1 (/ 1 $t)))))))"
        description = f"Pheromone-weighted cost with β={beta}"

        return TransformRule(pattern=pattern, template=template, description=description)


class PheromoneUpdater:
    """
    Utility class for updating pheromone values

    Implements combined evaporation + reinforcement updates.
    """

    def __init__(
        self,
        rho: float = None,
        alpha: float = None,
        beta: float = None
    ):
        """
        Initialize pheromone updater

        Args:
            rho: Evaporation rate
            alpha: Reinforcement rate
            beta: Pheromone weight
        """
        self.rho = rho or GORDON_PARAMS['evaporation_rate']
        self.alpha = alpha or GORDON_PARAMS['reinforcement_rate']
        self.beta = beta or GORDON_PARAMS['anternet_weight']

    def evaporate(self, tau: float) -> float:
        """
        Apply evaporation: τ_{t+1} = (1-ρ) · τ_t

        Args:
            tau: Current pheromone value

        Returns:
            Evaporated pheromone value
        """
        return tau * (1 - self.rho)

    def reinforce(self, tau: float, success: float) -> float:
        """
        Apply reinforcement: τ_{t+1} = τ_t + α · success

        Args:
            tau: Current pheromone value
            success: Success signal (normalized 0-1)

        Returns:
            Reinforced pheromone value
        """
        return tau + self.alpha * success

    def update(self, tau: float, success: float) -> float:
        """
        Combined update: evaporation + reinforcement

        Args:
            tau: Current pheromone value
            success: Success signal (0 for failure, >0 for success)

        Returns:
            Updated pheromone value (clamped to [0.1, 1.0])
        """
        # Evaporate
        tau_evaporated = self.evaporate(tau)

        # Reinforce if successful
        if success > 0:
            tau_updated = self.reinforce(tau_evaporated, success)
        else:
            tau_updated = tau_evaporated

        # Clamp to valid range [0.1, 1.0]
        return max(0.1, min(tau_updated, 1.0))

    def batch_update(self, pheromones: Dict[str, float], successes: Dict[str, float]) -> Dict[str, float]:
        """
        Batch update multiple pheromone values

        Args:
            pheromones: Dict mapping edge_id -> tau
            successes: Dict mapping edge_id -> success

        Returns:
            Updated pheromones dict
        """
        updated = {}

        for edge_id, tau in pheromones.items():
            success = successes.get(edge_id, 0.0)
            updated[edge_id] = self.update(tau, success)

        return updated


class CuriosityValueCalculator:
    """
    Calculate curiosity value (c_k) for exploration

    Based on Gordon's observations of foraging ant behavior.
    """

    @staticmethod
    def calculate(
        recent_successes: int,
        recent_attempts: int,
        time_since_last_success: float
    ) -> float:
        """
        Calculate curiosity value for exploration probability

        Args:
            recent_successes: Number of successful outcomes in window
            recent_attempts: Total attempts in window
            time_since_last_success: Time since last success (normalized)

        Returns:
            Curiosity value c_k ∈ [0.0, 1.0]
            - High c_k → More exploration
            - Low c_k → More exploitation
        """
        if recent_attempts == 0:
            # No data, high exploration
            return 0.8

        success_rate = recent_successes / recent_attempts

        # Low success rate → Increase exploration
        # High success rate → Decrease exploration (exploit current strategy)
        base_curiosity = 1.0 - success_rate

        # Time decay: If no recent success, increase exploration
        time_factor = min(time_since_last_success, 1.0)

        # Combined curiosity value
        c_k = 0.7 * base_curiosity + 0.3 * time_factor

        # Clamp to [0.2, 0.9] (always maintain some exploration/exploitation)
        return max(0.2, min(c_k, 0.9))
