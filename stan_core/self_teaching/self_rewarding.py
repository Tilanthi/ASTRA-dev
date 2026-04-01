"""
Self-Rewarding Engine for STAR-Learn

Implements intrinsic reward calculation for autonomous self-teaching.
Rewards are based on:
- Novelty detection (new discoveries) - Enhanced with embeddings
- Complexity bonus (understanding complex phenomena)
- Prediction accuracy (model validation)
- Cross-domain transfer (applying knowledge broadly)
- Conservation law discovery (finding invariants)
- Falsification power (experimental design)
- Scientific data validation (real-world data)
- Literature alignment (arXiv integration)
- Swarm coordination (multi-agent collaboration)

This engine provides the "self-rewarding" component that enables
autonomous learning without external supervision.

Version: 2.0.0 (Enhanced with embeddings, scientific data, arXiv, swarm)
Date: 2026-03-16
"""

import numpy as np
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, field
from enum import Enum
import json
from datetime import datetime

# Import enhanced modules
try:
    from .embedding_novelty import EnhancedRewardCalculator
    EMBEDDING_AVAILABLE = True
except ImportError:
    EMBEDDING_AVAILABLE = False

try:
    from .scientific_data import (
        PhysicsDataLibrary, PhysicalLawDiscovery,
        get_scientific_discovery_reward
    )
    SCIENTIFIC_DATA_AVAILABLE = True
except ImportError:
    SCIENTIFIC_DATA_AVAILABLE = False

try:
    from .arxiv_integration import (
        ContinuousLearningSystem,
        get_literature_learning_reward
    )
    ARXIV_AVAILABLE = True
except ImportError:
    ARXIV_AVAILABLE = False

try:
    from .multi_agent_swarm import MultiAgentSwarm
    SWARM_AVAILABLE = True
except ImportError:
    SWARM_AVAILABLE = False


class RewardComponent(Enum):
    """Components of the intrinsic reward system"""
    NOVELTY = "novelty"  # Reward for discovering something new
    COMPLEXITY = "complexity"  # Reward for understanding complex phenomena
    PREDICTION = "prediction"  # Reward for accurate predictions
    TRANSFER = "transfer"  # Reward for cross-domain knowledge application
    CONSERVATION = "conservation"  # Reward for discovering invariants
    FALSIFICATION = "falsification"  # Reward for experimental design
    CAUSALITY = "causality"  # Reward for discovering causal mechanisms
    COHERENCE = "coherence"  # Reward for building coherent theories
    EFFICIENCY = "efficiency"  # Reward for elegant solutions
    SURPRISE = "surprise"  # Reward for unexpected but valid insights


@dataclass
class IntrinsicReward:
    """
    Represents the intrinsic reward for a discovery or solution.

    The total reward is a weighted sum of components, with normalization
    and exploration bonuses to encourage diverse discovery.
    """
    total_reward: float
    components: Dict[RewardComponent, float] = field(default_factory=dict)
    novelty_score: float = 0.0
    complexity_score: float = 0.0
    prediction_score: float = 0.0
    transfer_score: float = 0.0

    # Metadata
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())
    discovery_type: str = "unknown"
    confidence: float = 0.0

    def get_component_breakdown(self) -> Dict[str, float]:
        """Get detailed breakdown of reward components."""
        return {
            comp.value: value
            for comp, value in self.components.items()
        }

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            'total_reward': self.total_reward,
            'components': self.get_component_breakdown(),
            'novelty_score': self.novelty_score,
            'complexity_score': self.complexity_score,
            'prediction_score': self.prediction_score,
            'transfer_score': self.transfer_score,
            'timestamp': self.timestamp,
            'discovery_type': self.discovery_type,
            'confidence': self.confidence
        }


@dataclass
class RewardConfig:
    """Configuration for the self-rewarding engine"""
    # Component weights (should sum to 1.0)
    novelty_weight: float = 0.25
    complexity_weight: float = 0.15
    prediction_weight: float = 0.20
    transfer_weight: float = 0.15
    conservation_weight: float = 0.10
    falsification_weight: float = 0.05
    causality_weight: float = 0.05
    coherence_weight: float = 0.03
    efficiency_weight: float = 0.01
    surprise_weight: float = 0.01

    # Exploration parameters
    exploration_bonus: float = 0.1  # Bonus for exploring new domains
    diversity_penalty: float = 0.05  # Penalty for repetitive discoveries
    decay_rate: float = 0.99  # Reward decay over time (encourages continuous discovery)

    # Thresholds
    min_novelty_threshold: float = 0.3  # Minimum novelty for reward
    max_reward: float = 10.0  # Maximum single discovery reward

    # Domain-specific modifiers
    domain_multipliers: Dict[str, float] = field(default_factory=lambda: {
        'astrophysics': 1.2,
        'causality': 1.1,
        'mathematics': 1.0,
        'physics': 1.1,
        'biology': 1.0,
        'chemistry': 1.0
    })

    # Enhanced features (V2.0)
    use_embeddings: bool = True  # Use embedding-based novelty detection
    use_scientific_data: bool = True  # Validate against real scientific data
    use_arxiv_integration: bool = True  # Align with scientific literature
    use_swarm_coordination: bool = True  # Multi-agent collaboration


class SelfRewardingEngine:
    """
    Self-Rewarding Engine for autonomous learning.

    Calculates intrinsic rewards based on multiple components to guide
    the self-teaching process without external supervision.
    """

    def __init__(self, config: Optional[RewardConfig] = None):
        """
        Initialize the self-rewarding engine.

        Args:
            config: Reward configuration
        """
        self.config = config or RewardConfig()

        # Track reward history for adaptive adjustment
        self.reward_history = []
        self.component_averages = {comp: 0.5 for comp in RewardComponent}

        # Domain exploration tracking
        self.explored_domains = set()
        self.discovery_signatures = []

        # Running statistics
        self.total_rewards_issued = 0.0
        self.num_discoveries = 0

        # Enhanced modules (V2.0)
        self.enhanced_calculator = None
        self.data_library = None
        self.law_discovery = None
        self.arxiv_system = None
        self.swarm_system = None

        # Initialize enhanced modules if available
        if self.config.use_embeddings and EMBEDDING_AVAILABLE:
            self.enhanced_calculator = EnhancedRewardCalculator()

        if self.config.use_scientific_data and SCIENTIFIC_DATA_AVAILABLE:
            self.data_library = PhysicsDataLibrary()
            self.law_discovery = PhysicalLawDiscovery()

        if self.config.use_arxiv_integration and ARXIV_AVAILABLE:
            self.arxiv_system = ContinuousLearningSystem()

    def calculate_reward(
        self,
        discovery: Dict[str, Any],
        context: Optional[Dict[str, Any]] = None
    ) -> IntrinsicReward:
        """
        Calculate intrinsic reward for a discovery.

        Args:
            discovery: Discovery information with fields:
                - content: The discovery content
                - domain: Scientific domain
                - confidence: Confidence in discovery
                - evidence: Supporting evidence
                - predictions: Testable predictions (optional)
                - causal_mechanisms: Causal relationships (optional)
            context: Additional context (current state, etc.)

        Returns:
            IntrinsicReward with detailed breakdown
        """
        context = context or {}

        # Extract discovery information
        content = discovery.get('content', '')
        domain = discovery.get('domain', 'unknown')
        confidence = discovery.get('confidence', 0.5)

        # Calculate each component
        components = {}

        # 1. Novelty Component
        novelty_score = self._calculate_novelty(discovery, context)
        components[RewardComponent.NOVELTY] = novelty_score

        # 2. Complexity Component
        complexity_score = self._calculate_complexity(discovery, context)
        components[RewardComponent.COMPLEXITY] = complexity_score

        # 3. Prediction Component
        prediction_score = self._calculate_prediction_reward(discovery, context)
        components[RewardComponent.PREDICTION] = prediction_score

        # 4. Transfer Component
        transfer_score = self._calculate_transfer_reward(discovery, context)
        components[RewardComponent.TRANSFER] = transfer_score

        # 5. Conservation Component
        conservation_score = self._calculate_conservation_reward(discovery, context)
        components[RewardComponent.CONSERVATION] = conservation_score

        # 6. Falsification Component
        falsification_score = self._calculate_falsification_reward(discovery, context)
        components[RewardComponent.FALSIFICATION] = falsification_score

        # 7. Causality Component
        causality_score = self._calculate_causality_reward(discovery, context)
        components[RewardComponent.CAUSALITY] = causality_score

        # 8. Coherence Component
        coherence_score = self._calculate_coherence_reward(discovery, context)
        components[RewardComponent.COHERENCE] = coherence_score

        # 9. Efficiency Component
        efficiency_score = self._calculate_efficiency_reward(discovery, context)
        components[RewardComponent.EFFICIENCY] = efficiency_score

        # 10. Surprise Component
        surprise_score = self._calculate_surprise_reward(discovery, context)
        components[RewardComponent.SURPRISE] = surprise_score

        # Calculate weighted total
        total = self._calculate_weighted_total(components, domain)

        # Calculate enhanced rewards (V2.0)
        enhanced_total, enhanced_breakdown = self.calculate_enhanced_rewards(
            discovery, context
        )
        total += enhanced_total * 0.5  # Weight enhanced rewards at 50%

        # Apply exploration bonus
        exploration_bonus = self._calculate_exploration_bonus(domain, discovery)
        total += exploration_bonus

        # Apply diversity penalty
        diversity_penalty = self._calculate_diversity_penalty(discovery)
        total -= diversity_penalty

        # Cap maximum reward
        total = min(total, self.config.max_reward)

        # Create reward object
        reward = IntrinsicReward(
            total_reward=total,
            components=components,
            novelty_score=novelty_score,
            complexity_score=complexity_score,
            prediction_score=prediction_score,
            transfer_score=transfer_score,
            discovery_type=domain,
            confidence=confidence
        )

        # Update tracking
        self._update_tracking(reward, discovery)

        return reward

    def _calculate_novelty(self, discovery: Dict, context: Dict) -> float:
        """
        Calculate novelty score based on how new the discovery is.

        Novelty is measured by:
        1. Semantic distance from previous discoveries (enhanced with embeddings)
        2. New concepts introduced
        3. New relationships identified
        """
        content = discovery.get('content', '')

        # Use enhanced embedding-based novelty if available
        if self.enhanced_calculator and self.config.use_embeddings:
            novelty, details = self.enhanced_calculator.calculate_enhanced_novelty(
                discovery,
                use_embeddings=True
            )
        else:
            # Fallback to simple word overlap
            max_similarity = 0.0
            for prev_sig in self.discovery_signatures[-100:]:
                similarity = self._semantic_similarity(content, prev_sig['content'])
                max_similarity = max(max_similarity, similarity)
            novelty = 1.0 - max_similarity

        # Boost for discovering new concepts
        if discovery.get('new_concepts'):
            novelty += 0.2 * len(discovery['new_concepts'])

        # Ensure minimum threshold
        if novelty < self.config.min_novelty_threshold:
            novelty = 0.0

        return min(novelty, 1.0)

    def _calculate_complexity(self, discovery: Dict, context: Dict) -> float:
        """
        Calculate complexity score based on the complexity of the discovery.

        Complexity is measured by:
        1. Number of interacting components
        2. Hierarchical depth of explanation
        3. Mathematical sophistication required
        """
        complexity = 0.5  # Base complexity

        # More components = more complex
        if 'components' in discovery:
            complexity += 0.1 * min(len(discovery['components']), 10)

        # Hierarchical depth
        if 'hierarchy_depth' in discovery:
            complexity += 0.05 * discovery['hierarchy_depth']

        # Mathematical sophistication
        if discovery.get('has_equations'):
            complexity += 0.2

        # Multi-scale phenomena
        if discovery.get('multi_scale'):
            complexity += 0.15

        # Non-linear relationships
        if discovery.get('non_linear'):
            complexity += 0.1

        return min(complexity, 1.0)

    def _calculate_prediction_reward(self, discovery: Dict, context: Dict) -> float:
        """
        Calculate reward for predictive power.

        Reward based on:
        1. Number of testable predictions
        2. Precision of predictions
        3. Novel predictions (not obvious from existing theory)
        """
        predictions = discovery.get('predictions', [])

        if not predictions:
            return 0.0

        # Base reward for having predictions
        reward = 0.3

        # Reward for more predictions
        reward += 0.1 * min(len(predictions), 10)

        # Reward for quantitative predictions
        quantitative = sum(1 for p in predictions if p.get('quantitative'))
        reward += 0.05 * quantitative

        # Reward for novel predictions
        novel = sum(1 for p in predictions if p.get('novel'))
        reward += 0.1 * novel

        # Reward for precise predictions (with confidence intervals)
        precise = sum(1 for p in predictions if p.get('confidence_interval'))
        reward += 0.05 * precise

        return min(reward, 1.0)

    def _calculate_transfer_reward(self, discovery: Dict, context: Dict) -> float:
        """
        Calculate reward for cross-domain knowledge transfer.

        Reward based on:
        1. Number of domains connected
        2. Novelty of connections
        3. Synthesis quality
        """
        domains = discovery.get('connected_domains', [])

        if len(domains) < 2:
            return 0.0

        # Base reward for connecting domains
        reward = 0.3

        # Reward for more domains
        reward += 0.1 * min(len(domains) - 1, 5)

        # Check for novel connections
        existing_connections = set()
        for prev in self.discovery_signatures[-50:]:
            if 'connected_domains' in prev:
                doms = tuple(sorted(prev['connected_domains']))
                existing_connections.add(doms)

        current = tuple(sorted(domains))
        if current not in existing_connections:
            reward += 0.3  # Bonus for novel connection

        return min(reward, 1.0)

    def _calculate_conservation_reward(self, discovery: Dict, context: Dict) -> float:
        """
        Calculate reward for discovering conservation laws/invariants.

        Conservation laws are fundamental to physics and highly valuable.
        """
        if not discovery.get('conservation_law'):
            return 0.0

        reward = 0.5  # Base reward for discovering a conservation law

        # Bonus for mathematical invariants
        if discovery.get('mathematical_invariant'):
            reward += 0.3

        # Bonus for universality (applies across conditions)
        if discovery.get('universal'):
            reward += 0.2

        return min(reward, 1.0)

    def _calculate_falsification_reward(self, discovery: Dict, context: Dict) -> float:
        """
        Calculate reward for experimental design that enables falsification.

        Good science requires testable hypotheses.
        """
        if not discovery.get('experimental_design'):
            return 0.0

        design = discovery['experimental_design']

        reward = 0.3  # Base reward

        # Reward for clear falsification criteria
        if design.get('falsification_criteria'):
            reward += 0.2

        # Reward for controlled experiments
        if design.get('controlled'):
            reward += 0.2

        # Reward for measurable outcomes
        if design.get('measurable_outcomes'):
            reward += 0.2

        # Reward for feasible experiments
        if design.get('feasible'):
            reward += 0.1

        return min(reward, 1.0)

    def _calculate_causality_reward(self, discovery: Dict, context: Dict) -> float:
        """
        Calculate reward for discovering causal mechanisms.

        Causal understanding is superior to mere correlation.
        """
        if not discovery.get('causal_mechanisms'):
            return 0.0

        mechanisms = discovery['causal_mechanisms']

        reward = 0.3  # Base reward

        # Reward for number of mechanisms
        reward += 0.1 * min(len(mechanisms), 5)

        # Reward for mechanistic depth
        if discovery.get('mechanism_depth'):
            reward += 0.1 * discovery['mechanism_depth']

        # Reward for intervention potential
        if discovery.get('intervention_possible'):
            reward += 0.2

        # Reward for counterfactual validity
        if discovery.get('counterfactual_valid'):
            reward += 0.2

        return min(reward, 1.0)

    def _calculate_coherence_reward(self, discovery: Dict, context: Dict) -> float:
        """
        Calculate reward for theoretical coherence.

        Coherent theories are internally consistent and integrate well
        with existing knowledge.
        """
        coherence = 0.5  # Base coherence

        # Check internal consistency
        if discovery.get('internally_consistent'):
            coherence += 0.2

        # Check integration with existing knowledge
        if discovery.get('integrates_existing'):
            coherence += 0.2

        # Check explanatory unity
        if discovery.get('unified_explanation'):
            coherence += 0.1

        return min(coherence, 1.0)

    def _calculate_efficiency_reward(self, discovery: Dict, context: Dict) -> float:
        """
        Calculate reward for elegant/efficient solutions.

        Scientific elegance often correlates with truth.
        """
        efficiency = 0.5  # Base efficiency

        # Reward for simplicity (Occam's razor)
        if discovery.get('simple'):
            efficiency += 0.2

        # Reward for generality (explains many phenomena)
        if discovery.get('general'):
            efficiency += 0.2

        # Reward for minimal assumptions
        n_assumptions = discovery.get('n_assumptions', 10)
        efficiency += 0.1 * max(0, (5 - n_assumptions) / 5)

        return min(max(efficiency, 0), 1.0)

    def _calculate_surprise_reward(self, discovery: Dict, context: Dict) -> float:
        """
        Calculate reward for surprising but valid insights.

        Unexpected insights that prove true are highly valuable.
        """
        # Surprise is based on deviation from expectations
        # while maintaining validity

        if not discovery.get('surprising'):
            return 0.0

        surprise = 0.3  # Base surprise reward

        # Higher reward if surprising but valid
        if discovery.get('validated_surprise'):
            surprise += 0.4

        # Reward for paradigm-shifting potential
        if discovery.get('paradigm_shifting'):
            surprise += 0.3

        return min(surprise, 1.0)

    def _calculate_weighted_total(
        self,
        components: Dict[RewardComponent, float],
        domain: str
    ) -> float:
        """Calculate weighted total with domain multiplier."""
        total = 0.0

        weights = {
            RewardComponent.NOVELTY: self.config.novelty_weight,
            RewardComponent.COMPLEXITY: self.config.complexity_weight,
            RewardComponent.PREDICTION: self.config.prediction_weight,
            RewardComponent.TRANSFER: self.config.transfer_weight,
            RewardComponent.CONSERVATION: self.config.conservation_weight,
            RewardComponent.FALSIFICATION: self.config.falsification_weight,
            RewardComponent.CAUSALITY: self.config.causality_weight,
            RewardComponent.COHERENCE: self.config.coherence_weight,
            RewardComponent.EFFICIENCY: self.config.efficiency_weight,
            RewardComponent.SURPRISE: self.config.surprise_weight,
        }

        for comp, value in components.items():
            total += weights.get(comp, 0) * value

        # Apply domain multiplier
        domain_mult = self.config.domain_multipliers.get(domain, 1.0)
        total *= domain_mult

        return total

    def _calculate_exploration_bonus(self, domain: str, discovery: Dict) -> float:
        """Calculate exploration bonus for new domains."""
        if domain not in self.explored_domains:
            return self.config.exploration_bonus
        return 0.0

    def _calculate_diversity_penalty(self, discovery: Dict) -> float:
        """Calculate penalty for repetitive discoveries."""
        content = discovery.get('content', '')

        # Check for very similar recent discoveries
        for prev in self.discovery_signatures[-20:]:
            similarity = self._semantic_similarity(content, prev['content'])
            if similarity > 0.9:
                return self.config.diversity_penalty

        return 0.0

    def _semantic_similarity(self, text1: str, text2: str) -> float:
        """
        Calculate semantic similarity between two texts.

        Simple word-overlap based similarity.
        In production, use embeddings.
        """
        words1 = set(text1.lower().split())
        words2 = set(text2.lower().split())

        if not words1 or not words2:
            return 0.0

        intersection = words1.intersection(words2)
        union = words1.union(words2)

        return len(intersection) / len(union) if union else 0.0

    # =============================================================================
    # Enhanced Reward Calculation (V2.0)
    # =============================================================================

    def calculate_enhanced_rewards(
        self,
        discovery: Dict[str, Any],
        context: Optional[Dict[str, Any]] = None
    ) -> Tuple[float, Dict[str, float]]:
        """
        Calculate enhanced rewards from all V2.0 modules.

        This integrates:
        - Scientific data validation
        - arXiv literature alignment
        - Multi-agent swarm coordination
        - Enhanced novelty with embeddings
        - Conservation law discovery
        - Cross-domain transfer bonuses

        Returns:
            (enhanced_reward, breakdown_dict)
        """
        enhanced_rewards = {}
        total_enhanced = 0.0

        # 1. Scientific Data Validation
        if self.law_discovery and self.config.use_scientific_data:
            data_reward, data_details = get_scientific_discovery_reward(
                discovery, self.law_discovery
            )
            enhanced_rewards['scientific_data'] = data_reward
            total_enhanced += data_reward

        # 2. arXiv Literature Alignment
        if self.arxiv_system and self.config.use_arxiv_integration:
            lit_reward, lit_details = get_literature_learning_reward(
                discovery, self.arxiv_system
            )
            enhanced_rewards['literature_alignment'] = lit_reward
            total_enhanced += lit_reward

        # 3. Conservation Law Discovery (Enhanced)
        if self.enhanced_calculator and self.config.use_embeddings:
            conservation_reward, cons_details = \
                self.enhanced_calculator.check_conservation_discovery(discovery)
            enhanced_rewards['conservation_law'] = conservation_reward
            total_enhanced += conservation_reward

        # 4. Cross-Domain Transfer (Enhanced)
        if self.enhanced_calculator and self.config.use_embeddings:
            transfer_reward, transfer_details = \
                self.enhanced_calculator.calculate_cross_domain_transfer_bonus(discovery)
            enhanced_rewards['cross_domain_transfer'] = transfer_reward
            total_enhanced += transfer_reward

        # Normalize to 0-1 range
        total_enhanced = min(total_enhanced / 2.0, 1.0)  # Assume max ~2.0

        return total_enhanced, enhanced_rewards

    def perform_literature_learning(
        self,
        domains: List[str] = None,
        n_papers: int = 10
    ) -> Dict[str, Any]:
        """
        Perform continuous learning from scientific literature.

        Updates the arXiv integration system with new papers.
        """
        if not self.arxiv_system:
            return {'error': 'arXiv integration not available'}

        return self.arxiv_system.learn_from_literature(domains=domains, n_papers=n_papers)

    def discover_scientific_laws(
        self,
        dataset_name: str
    ) -> List[Dict]:
        """
        Discover physical laws from scientific datasets.

        Returns discovered laws with confidence scores.
        """
        if not self.data_library or not self.law_discovery:
            return [{'error': 'Scientific data modules not available'}]

        dataset = self.data_library.get_dataset(dataset_name)
        if not dataset:
            return [{'error': f'Dataset {dataset_name} not found'}]

        laws = self.law_discovery.discover_all_laws(dataset)

        return [
            {
                'name': law.name,
                'type': law.law_type.value,
                'equation': law.equation,
                'confidence': law.confidence,
                'domain': law.domain
            }
            for law in laws
        ]

    def get_available_datasets(self) -> List[str]:
        """Get list of available scientific datasets."""
        if not self.data_library:
            return []
        return self.data_library.list_datasets()

    def get_literature_concepts(self, query: str) -> List[Dict]:
        """Search for concepts in learned literature."""
        if not self.arxiv_system:
            return []

        concepts = self.arxiv_system.search_concepts(query)

        return [
            {
                'name': c.name,
                'definition': c.definition,
                'domain': c.domain,
                'confidence': c.confidence
            }
            for c in concepts
        ]

    def get_trending_research_topics(self, top_n: int = 5) -> List[Dict]:
        """Get trending research topics from arXiv."""
        if not self.arxiv_system:
            return []

        trends = self.arxiv_system.get_trending_topics(top_n=top_n)

        return [
            {
                'topic': t.topic,
                'growth_rate': t.growth_rate,
                'papers_count': t.papers_count
            }
            for t in trends
        ]

    def _update_tracking(self, reward: IntrinsicReward, discovery: Dict):
        """Update tracking statistics."""
        self.reward_history.append(reward)
        self.total_rewards_issued += reward.total_reward
        self.num_discoveries += 1

        # Track explored domains
        self.explored_domains.add(reward.discovery_type)

        # Store discovery signature
        self.discovery_signatures.append({
            'content': discovery.get('content', ''),
            'domain': reward.discovery_type,
            'timestamp': reward.timestamp,
            'reward': reward.total_reward
        })

        # Limit signature history
        if len(self.discovery_signatures) > 1000:
            self.discovery_signatures = self.discovery_signatures[-1000:]

        # Update component averages
        for comp, value in reward.components.items():
            current_avg = self.component_averages.get(comp, 0.5)
            self.component_averages[comp] = 0.95 * current_avg + 0.05 * value

    def get_statistics(self) -> Dict[str, Any]:
        """Get reward engine statistics."""
        if not self.reward_history:
            return {
                'total_rewards_issued': 0,
                'num_discoveries': 0,
                'average_reward': 0,
                'max_reward': 0,
                'explored_domains': list(self.explored_domains)
            }

        rewards = [r.total_reward for r in self.reward_history]

        return {
            'total_rewards_issued': self.total_rewards_issued,
            'num_discoveries': self.num_discoveries,
            'average_reward': np.mean(rewards),
            'max_reward': np.max(rewards),
            'min_reward': np.min(rewards),
            'std_reward': np.std(rewards),
            'explored_domains': list(self.explored_domains),
            'component_averages': {
                comp.value: val
                for comp, val in self.component_averages.items()
            }
        }

    def reset(self):
        """Reset the reward engine state."""
        self.reward_history = []
        self.component_averages = {comp: 0.5 for comp in RewardComponent}
        self.explored_domains = set()
        self.discovery_signatures = []
        self.total_rewards_issued = 0.0
        self.num_discoveries = 0


def create_self_rewarding_engine(config: Optional[Dict] = None) -> SelfRewardingEngine:
    """
    Factory function to create a self-rewarding engine.

    Args:
        config: Optional configuration dict

    Returns:
        Configured SelfRewardingEngine
    """
    if config:
        reward_config = RewardConfig(**config)
    else:
        reward_config = RewardConfig()

    return SelfRewardingEngine(reward_config)
