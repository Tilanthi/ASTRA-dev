"""
Adaptive Decision Engine - Novelty-Driven Adaptive Decision Making

This module enables ASTRA to make adaptive, creative decisions outside predetermined
workflows through:

1. Novelty-driven exploration
2. Curiosity-based objective selection
3. Adaptive strategy selection
4. Creative behavior generation
5. Risk-aware decision making
6. Multi-criteria optimization

Phase 3 Implementation: Adaptive Decision-Making
Date: 2026-06-27
"""

import numpy as np
from typing import Dict, List, Optional, Any, Tuple, Callable, Set
from dataclasses import dataclass, field
from enum import Enum
import time
import logging
import random
from collections import defaultdict
from datetime import datetime

logger = logging.getLogger(__name__)


class DecisionStrategy(Enum):
    """Strategies for adaptive decision making"""
    NOVELTY_SEEKING = "novelty_seeking"           # Prioritize novel options
    CURiosity_DRIVEN = "curiosity_driven"         # Follow curiosity signals
    RISK_AWARE = "risk_aware"                     # Balance risk/reward
    EXPLORATION_EXPLOITATION = "exploration_exploitation"  # Balance explore/exploit
    MULTI_OBJECTIVE = "multi_objective"           # Optimize multiple objectives
    CREATIVE_SYNTHESIS = "creative_synthesis"     # Combine ideas creatively


class NoveltyType(Enum):
    """Types of novelty"""
    CONCEPTUAL = "conceptual"                     # New concepts
    METHODOLOGICAL = "methodological"             # New methods
    OBSERVATIONAL = "observational"              # New observations
    THEORETICAL = "theoretical"                  # New theories
    INTEGRATIVE = "integrative"                   # New combinations


class RiskLevel(Enum):
    """Risk levels for decisions"""
    MINIMAL = "minimal"                           # Very low risk
    LOW = "low"                                   # Low risk
    MODERATE = "moderate"                         # Moderate risk
    HIGH = "high"                                 # High risk
    EXTREME = "extreme"                           # Very high risk


@dataclass
class DecisionOption:
    """An option for decision making"""
    option_id: str
    description: str
    expected_value: float = 0.5
    novelty_score: float = 0.5
    risk_level: RiskLevel = RiskLevel.MODERATE
    feasibility: float = 0.5
    confidence: float = 0.5
    multi_criteria_scores: Dict[str, float] = field(default_factory=dict)
    prerequisites: List[str] = field(default_factory=list)
    potential_outcomes: List[str] = field(default_factory=list)


@dataclass
class AdaptiveDecision:
    """An adaptive decision with rationale"""
    decision_id: str
    selected_option: DecisionOption
    strategy_used: DecisionStrategy
    rationale: str
    confidence: float
    expected_outcomes: List[str]
    risk_assessment: Dict[str, Any]
    alternative_considered: List[str]
    timestamp: str


@dataclass
class CuriositySignal:
    """A curiosity signal driving exploration"""
    signal_id: str
    topic: str
    domain: str
    intensity: float  # 0-1
    novelty_type: NoveltyType
    potential_value: float
    exploration_cost: float
    expected_learning: float


class AdaptiveDecisionEngine:
    """
    Enable adaptive, creative decision-making outside predetermined workflows.

    Key capabilities:
    - Novelty-driven exploration
    - Curiosity-based objective selection
    - Adaptive strategy selection
    - Multi-criteria optimization
    - Risk-aware decision making
    """

    def __init__(self, autonomy_level: float = 0.7):
        """
        Initialize Adaptive Decision Engine

        Args:
            autonomy_level: Level of autonomous decision-making (0.0-1.0)
        """
        logger.info(f"[AdaptiveDecision] Initializing engine with autonomy {autonomy_level}")

        self.autonomy_level = autonomy_level

        # Decision history
        self.decision_history: List[AdaptiveDecision] = []

        # Curiosity signals
        self.curiosity_signals: List[CuriositySignal] = []
        self.curiosity_decay_rate = 0.95

        # Novelty tracking
        self.explored_concepts: Set[str] = set()
        self.novelty_threshold = 0.6

        # Strategy performance
        self.strategy_performance: Dict[DecisionStrategy, float] = {
            strategy: 0.7 for strategy in DecisionStrategy
        }

        # Risk tolerance (adaptive)
        self.risk_tolerance = 0.5

        # Statistics
        self.stats = {
            'decisions_made': 0,
            'novel_options_selected': 0,
            'curiosity_signals_generated': 0,
            'strategies_used': defaultdict(int)
        }

        logger.info("[AdaptiveDecision] Engine initialized")

    def make_adaptive_decision(
        self,
        context: Dict[str, Any],
        options: List[DecisionOption],
        constraints: Optional[Dict[str, Any]] = None
    ) -> AdaptiveDecision:
        """
        Make adaptive decision based on context and options

        Args:
            context: Current context and state
            options: Available decision options
            constraints: Decision constraints

        Returns:
            Adaptive decision with rationale
        """
        logger.info(f"[AdaptiveDecision] Making adaptive decision from {len(options)} options")

        # Select appropriate strategy
        strategy = self._select_strategy(context, options)

        # Apply strategy to select option
        selected_option = self._apply_strategy(strategy, options, context)

        # Generate rationale
        rationale = self._generate_rationale(selected_option, strategy, context)

        # Assess risk
        risk_assessment = self._assess_risk(selected_option, context)

        # Generate expected outcomes
        expected_outcomes = self._predict_outcomes(selected_option, context)

        # Calculate confidence
        confidence = self._calculate_decision_confidence(
            selected_option, strategy, context
        )

        # Create decision
        decision = AdaptiveDecision(
            decision_id=f"decision_{int(time.time())}_{len(self.decision_history)}",
            selected_option=selected_option,
            strategy_used=strategy,
            rationale=rationale,
            confidence=confidence,
            expected_outcomes=expected_outcomes,
            risk_assessment=risk_assessment,
            alternative_considered=[opt.description for opt in options if opt != selected_option],
            timestamp=datetime.now().isoformat()
        )

        self.decision_history.append(decision)
        self.stats['decisions_made'] += 1
        self.stats['strategies_used'][strategy] += 1

        # Update novelty tracking
        if selected_option.novelty_score > self.novelty_threshold:
            self.stats['novel_options_selected'] += 1

        logger.info(f"[AdaptiveDecision] Decision made: {selected_option.description[:60]}...")

        return decision

    def _select_strategy(
        self,
        context: Dict,
        options: List[DecisionOption]
    ) -> DecisionStrategy:
        """Select appropriate decision strategy"""
        # Analyze context to determine best strategy

        # Check for novelty preference
        avg_novelty = np.mean([opt.novelty_score for opt in options])
        if avg_novelty > 0.7:
            return DecisionStrategy.NOVELTY_SEEKING

        # Check for uncertainty
        uncertainty = context.get('uncertainty', 0.5)
        if uncertainty > 0.7:
            return DecisionStrategy.EXPLORATION_EXPLOITATION

        # Check for multiple objectives
        if any(opt.multi_criteria_scores for opt in options):
            return DecisionStrategy.MULTI_OBJECTIVE

        # Check for high-stakes decision
        high_stakes = context.get('high_stakes', False)
        if high_stakes:
            return DecisionStrategy.RISK_AWARE

        # Default to curiosity-driven
        return DecisionStrategy.CURiosity_DRIVEN

    def _apply_strategy(
        self,
        strategy: DecisionStrategy,
        options: List[DecisionOption],
        context: Dict
    ) -> DecisionOption:
        """Apply strategy to select best option"""

        if strategy == DecisionStrategy.NOVELTY_SEEKING:
            return self._novelty_seeking_selection(options, context)
        elif strategy == DecisionStrategy.CURiosity_DRIVEN:
            return self._curiosity_driven_selection(options, context)
        elif strategy == DecisionStrategy.RISK_AWARE:
            return self._risk_aware_selection(options, context)
        elif strategy == DecisionStrategy.EXPLORATION_EXPLOITATION:
            return self._exploration_exploitation_selection(options, context)
        elif strategy == DecisionStrategy.MULTI_OBJECTIVE:
            return self._multi_objective_selection(options, context)
        elif strategy == DecisionStrategy.CREATIVE_SYNTHESIS:
            return self._creative_synthesis_selection(options, context)
        else:
            # Default to expected value
            return max(options, key=lambda opt: opt.expected_value)

    def _novelty_seeking_selection(
        self,
        options: List[DecisionOption],
        context: Dict
    ) -> DecisionOption:
        """Select option with highest novelty"""
        # Score options by novelty with other factors
        scored_options = []
        for opt in options:
            score = (
                opt.novelty_score * 0.7 +
                opt.expected_value * 0.2 +
                opt.feasibility * 0.1
            )
            scored_options.append((score, opt))

        scored_options.sort(key=lambda x: x[0], reverse=True)
        return scored_options[0][1]

    def _curiosity_driven_selection(
        self,
        options: List[DecisionOption],
        context: Dict
    ) -> DecisionOption:
        """Select option based on curiosity signals"""
        if not self.curiosity_signals:
            # Fallback to novelty-seeking
            return self._novelty_seeking_selection(options, context)

        # Match options to curiosity signals
        scored_options = []
        for opt in options:
            curiosity_match = 0.0
            for signal in self.curiosity_signals:
                if signal.topic.lower() in opt.description.lower():
                    curiosity_match += signal.intensity

            score = (
                curiosity_match * 0.6 +
                opt.novelty_score * 0.3 +
                opt.expected_value * 0.1
            )
            scored_options.append((score, opt))

        scored_options.sort(key=lambda x: x[0], reverse=True)
        return scored_options[0][1]

    def _risk_aware_selection(
        self,
        options: List[DecisionOption],
        context: Dict
    ) -> DecisionOption:
        """Select option balancing risk and reward"""
        # Score options by risk-adjusted value
        scored_options = []
        for opt in options:
            # Risk penalty
            risk_penalty = {
                RiskLevel.MINIMAL: 0.0,
                RiskLevel.LOW: 0.1,
                RiskLevel.MODERATE: 0.2,
                RiskLevel.HIGH: 0.4,
                RiskLevel.EXTREME: 0.7
            }[opt.risk_level]

            # Risk-adjusted score
            score = (
                opt.expected_value * (1 - risk_penalty) * 0.7 +
                opt.feasibility * 0.2 +
                opt.confidence * 0.1
            )
            scored_options.append((score, opt))

        scored_options.sort(key=lambda x: x[0], reverse=True)
        return scored_options[0][1]

    def _exploration_exploitation_selection(
        self,
        options: List[DecisionOption],
        context: Dict
    ) -> DecisionOption:
        """Balance exploration (novel) vs exploitation (known) options"""
        # Calculate exploration/exploitation balance
        exploration_ratio = context.get('exploration_ratio', 0.3)

        # Separate exploration and exploitation options
        exploration_opts = [opt for opt in options if opt.novelty_score > 0.6]
        exploitation_opts = [opt for opt in options if opt.novelty_score <= 0.6]

        # Decide based on exploration ratio
        if np.random.random() < exploration_ratio and exploration_opts:
            return max(exploration_opts, key=lambda opt: opt.novelty_score)
        elif exploitation_opts:
            return max(exploitation_opts, key=lambda opt: opt.expected_value)
        else:
            return max(options, key=lambda opt: opt.expected_value)

    def _multi_objective_selection(
        self,
        options: List[DecisionOption],
        context: Dict
    ) -> DecisionOption:
        """Select option optimizing multiple objectives"""
        # Use multi-criteria scores if available
        scored_options = []
        for opt in options:
            if opt.multi_criteria_scores:
                # Weighted sum of criteria
                weights = context.get('criteria_weights', {})
                score = sum(
                    opt.multi_criteria_scores.get(criterion, 0) * weight
                    for criterion, weight in weights.items()
                )
                if not weights:  # Equal weights if none specified
                    score = np.mean(list(opt.multi_criteria_scores.values()))
            else:
                # Fallback to combined score
                score = (
                    opt.expected_value * 0.4 +
                    opt.novelty_score * 0.3 +
                    opt.feasibility * 0.3
                )

            scored_options.append((score, opt))

        scored_options.sort(key=lambda x: x[0], reverse=True)
        return scored_options[0][1]

    def _creative_synthesis_selection(
        self,
        options: List[DecisionOption],
        context: Dict
    ) -> DecisionOption:
        """Select option that creatively combines elements"""
        # Look for options that combine multiple domains/methods
        scored_options = []
        for opt in options:
            # Score based on diversity of elements
            diversity_score = len(set(opt.description.lower().split())) / 50.0
            synthesis_score = (
                opt.novelty_score * 0.4 +
                min(diversity_score, 1.0) * 0.4 +
                opt.expected_value * 0.2
            )
            scored_options.append((synthesis_score, opt))

        scored_options.sort(key=lambda x: x[0], reverse=True)
        return scored_options[0][1]

    def _generate_rationale(
        self,
        option: DecisionOption,
        strategy: DecisionStrategy,
        context: Dict
    ) -> str:
        """Generate rationale for decision"""
        rationale_parts = []

        # Strategy-based rationale
        strategy_rationales = {
            DecisionStrategy.NOVELTY_SEEKING: f"Selected for novelty (score: {option.novelty_score:.2f})",
            DecisionStrategy.CURiosity_DRIVEN: f"Selected based on curiosity signals",
            DecisionStrategy.RISK_AWARE: f"Selected for optimal risk-reward balance (risk: {option.risk_level.value})",
            DecisionStrategy.EXPLORATION_EXPLOITATION: f"Selected balancing exploration and exploitation",
            DecisionStrategy.MULTI_OBJECTIVE: f"Selected optimizing multiple criteria",
            DecisionStrategy.CREATIVE_SYNTHESIS: f"Selected for creative synthesis potential"
        }

        rationale_parts.append(strategy_rationales.get(strategy, "Selected based on adaptive analysis"))

        # Add expected value rationale
        rationale_parts.append(f"Expected value: {option.expected_value:.2f}")

        # Add feasibility rationale
        if option.feasibility < 0.5:
            rationale_parts.append(f"Note: Lower feasibility ({option.feasibility:.2f}) requires careful planning")

        # Add confidence rationale
        rationale_parts.append(f"Confidence: {option.confidence:.2f}")

        return ". ".join(rationale_parts) + "."

    def _assess_risk(
        self,
        option: DecisionOption,
        context: Dict
    ) -> Dict[str, Any]:
        """Assess risk of selected option"""
        return {
            'risk_level': option.risk_level.value,
            'risk_factors': self._identify_risk_factors(option),
            'mitigation_strategies': self._suggest_mitigations(option),
            'probability_of_failure': self._estimate_failure_probability(option)
        }

    def _identify_risk_factors(self, option: DecisionOption) -> List[str]:
        """Identify risk factors for option"""
        risk_factors = []

        if option.novelty_score > 0.8:
            risk_factors.append("High novelty introduces uncertainty")

        if option.feasibility < 0.5:
            risk_factors.append("Low feasibility increases execution risk")

        if option.risk_level in [RiskLevel.HIGH, RiskLevel.EXTREME]:
            risk_factors.append("High inherent risk level")

        if option.confidence < 0.5:
            risk_factors.append("Low confidence in outcome prediction")

        return risk_factors

    def _suggest_mitigations(self, option: DecisionOption) -> List[str]:
        """Suggest risk mitigation strategies"""
        mitigations = []

        if option.feasibility < 0.7:
            mitigations.append("Conduct feasibility study before full implementation")

        if option.novelty_score > 0.7:
            mitigations.append("Start with pilot test to validate approach")

        if option.risk_level != RiskLevel.MINIMAL:
            mitigations.append("Implement contingency plans")

        return mitigations

    def _estimate_failure_probability(self, option: DecisionOption) -> float:
        """Estimate probability of failure"""
        # Base failure probability
        failure_prob = 0.1

        # Adjust for various factors
        if option.novelty_score > 0.8:
            failure_prob += 0.2

        if option.feasibility < 0.5:
            failure_prob += 0.3

        if option.risk_level in [RiskLevel.HIGH, RiskLevel.EXTREME]:
            failure_prob += 0.2

        if option.confidence < 0.5:
            failure_prob += 0.1

        return min(0.9, failure_prob)

    def _predict_outcomes(
        self,
        option: DecisionOption,
        context: Dict
    ) -> List[str]:
        """Predict potential outcomes"""
        outcomes = []

        # Best case
        outcomes.append(f"Best case: {option.description} succeeds with high impact")

        # Expected case
        outcomes.append(f"Expected case: {option.description} achieves moderate results")

        # Worst case
        if option.risk_level != RiskLevel.MINIMAL:
            outcomes.append(f"Worst case: {option.description} fails or requires significant revision")

        return outcomes

    def _calculate_decision_confidence(
        self,
        option: DecisionOption,
        strategy: DecisionStrategy,
        context: Dict
    ) -> float:
        """Calculate confidence in decision"""
        # Base confidence
        confidence = option.confidence

        # Adjust for strategy performance
        strategy_perf = self.strategy_performance.get(strategy, 0.7)
        confidence = confidence * 0.7 + strategy_perf * 0.3

        # Adjust for autonomy level
        confidence = confidence * (0.8 + 0.2 * self.autonomy_level)

        return min(1.0, confidence)

    def generate_curiosity_signal(
        self,
        topic: str,
        domain: str,
        intensity: float = 0.7,
        novelty_type: NoveltyType = NoveltyType.CONCEPTUAL
    ) -> CuriositySignal:
        """
        Generate a curiosity signal for exploration

        Args:
            topic: Topic of curiosity
            domain: Scientific domain
            intensity: Intensity of curiosity (0-1)
            novelty_type: Type of novelty sought

        Returns:
            Curiosity signal
        """
        signal = CuriositySignal(
            signal_id=f"curiosity_{int(time.time())}_{len(self.curiosity_signals)}",
            topic=topic,
            domain=domain,
            intensity=intensity,
            novelty_type=novelty_type,
            potential_value=np.random.uniform(0.5, 0.9),
            exploration_cost=np.random.uniform(0.1, 0.4),
            expected_learning=np.random.uniform(0.6, 0.95)
        )

        self.curiosity_signals.append(signal)
        self.stats['curiosity_signals_generated'] += 1

        logger.info(f"[AdaptiveDecision] Curiosity signal generated: {topic} ({intensity:.2f})")

        return signal

    def decay_curiosity_signals(self):
        """Decay curiosity signals over time"""
        self.curiosity_signals = [
            signal for signal in self.curiosity_signals
            if signal.intensity * self.curiosity_decay_rate > 0.3
        ]

        # Decay intensities
        for signal in self.curiosity_signals:
            signal.intensity *= self.curiosity_decay_rate

    def explore_novel_behavior(
        self,
        domain: str,
        current_context: Dict
    ) -> Dict[str, Any]:
        """
        Explore novel behavior outside current patterns

        Args:
            domain: Domain to explore
            current_context: Current context and state

        Returns:
            Exploration results with novel behaviors
        """
        logger.info(f"[AdaptiveDecision] Exploring novel behavior in {domain}")

        # Generate novel behavior options
        novel_behaviors = self._generate_novel_behaviors(domain, current_context)

        # Select behavior using adaptive decision
        options = [
            DecisionOption(
                option_id=f"behavior_{i}",
                description=behavior['description'],
                novelty_score=behavior['novelty'],
                expected_value=behavior['value'],
                feasibility=behavior['feasibility']
            )
            for i, behavior in enumerate(novel_behaviors)
        ]

        decision = self.make_adaptive_decision(
            context=current_context,
            options=options
        )

        # Return exploration results
        return {
            'selected_behavior': decision.selected_option.description,
            'rationale': decision.rationale,
            'confidence': decision.confidence,
            'novel_behaviors_considered': len(novel_behaviors),
            'domain': domain
        }

    def _generate_novel_behaviors(
        self,
        domain: str,
        context: Dict
    ) -> List[Dict]:
        """Generate novel behavior options"""
        behaviors = []

        # Domain-specific novel behaviors
        if domain == 'astrophysics':
            behaviors = [
                {
                    'description': 'Apply machine learning to filament structure classification',
                    'novelty': 0.8,
                    'value': 0.7,
                    'feasibility': 0.6
                },
                {
                    'description': 'Investigate non-MHD effects in molecular clouds',
                    'novelty': 0.7,
                    'value': 0.8,
                    'feasibility': 0.5
                },
                {
                    'description': 'Explore connection between filaments and star formation efficiency',
                    'novelty': 0.6,
                    'value': 0.9,
                    'feasibility': 0.7
                }
            ]
        elif domain == 'astronomy':
            behaviors = [
                {
                    'description': 'Develop new periodicity detection algorithm',
                    'novelty': 0.8,
                    'value': 0.7,
                    'feasibility': 0.6
                },
                {
                    'description': 'Apply graph theory to galaxy clustering analysis',
                    'novelty': 0.7,
                    'value': 0.8,
                    'feasibility': 0.5
                }
            ]
        else:
            behaviors = [
                {
                    'description': f'Explore novel methodology in {domain}',
                    'novelty': 0.7,
                    'value': 0.6,
                    'feasibility': 0.5
                }
            ]

        return behaviors

    def update_strategy_performance(self, strategy: DecisionStrategy, performance: float):
        """Update strategy performance based on results"""
        current_perf = self.strategy_performance.get(strategy, 0.7)
        # Moving average update
        self.strategy_performance[strategy] = 0.8 * current_perf + 0.2 * performance

    def adjust_risk_tolerance(self, recent_outcomes: List[float]):
        """Adjust risk tolerance based on recent outcomes"""
        if recent_outcomes:
            avg_outcome = np.mean(recent_outcomes)
            if avg_outcome > 0.7:
                # Good outcomes, increase risk tolerance
                self.risk_tolerance = min(1.0, self.risk_tolerance + 0.05)
            elif avg_outcome < 0.4:
                # Poor outcomes, decrease risk tolerance
                self.risk_tolerance = max(0.1, self.risk_tolerance - 0.05)

    def get_status(self) -> Dict:
        """Get engine status"""
        return {
            'decisions_made': self.stats['decisions_made'],
            'novel_options_selected': self.stats['novel_options_selected'],
            'curiosity_signals': len(self.curiosity_signals),
            'autonomy_level': self.autonomy_level,
            'risk_tolerance': self.risk_tolerance,
            'strategies_used': dict(self.stats['strategies_used']),
            'strategy_performance': {
                strategy.value: perf
                for strategy, perf in self.strategy_performance.items()
            }
        }


# Factory functions

def create_adaptive_decision_engine(
    autonomy_level: float = 0.7
) -> AdaptiveDecisionEngine:
    """Factory function to create adaptive decision engine"""
    return AdaptiveDecisionEngine(autonomy_level=autonomy_level)


def make_autonomous_decision(
    context: Dict[str, Any],
    options: List[Dict[str, Any]],
    autonomy_level: float = 0.7
) -> Dict:
    """
    Convenience function to make autonomous decision

    Args:
        context: Current context
        options: Decision options (dict format)
        autonomy_level: Level of autonomy

    Returns:
        Decision result
    """
    engine = create_adaptive_decision_engine(autonomy_level)

    # Convert dict options to DecisionOption objects
    decision_options = []
    for i, opt_dict in enumerate(options):
        option = DecisionOption(
            option_id=f"option_{i}",
            description=opt_dict.get('description', ''),
            expected_value=opt_dict.get('expected_value', 0.5),
            novelty_score=opt_dict.get('novelty_score', 0.5),
            risk_level=RiskLevel(opt_dict.get('risk_level', 'moderate')),
            feasibility=opt_dict.get('feasibility', 0.5),
            confidence=opt_dict.get('confidence', 0.5)
        )
        decision_options.append(option)

    decision = engine.make_adaptive_decision(context, decision_options)

    return {
        'selected_option': decision.selected_option.description,
        'strategy': decision.strategy_used.value,
        'rationale': decision.rationale,
        'confidence': decision.confidence,
        'risk_assessment': decision.risk_assessment
    }