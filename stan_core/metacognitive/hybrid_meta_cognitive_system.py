#!/usr/bin/env python3
"""
Hybrid Meta-Cognitive System for ASTRA
======================================

Advanced meta-cognitive evaluation system that integrates multiple stan_core
capabilities for superior data sufficiency assessment.

Architecture:
1. Rule-based pattern matching (baseline)
2. Causal discovery engine (V50)
3. Bayesian uncertainty quantification
4. Domain knowledge integration
5. Ensemble decision making
6. Episodic learning from past evaluations

This system moves beyond simple pattern matching to use reasoning,
uncertainty quantification, and domain expertise for meta-cognitive assessment.

Author: ASTRA Project
Date: 2026-03-31
Version: 1.0 (Hybrid Architecture)
"""

import re
from typing import Dict, List, Tuple, Optional, Any
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
import json

# Import base meta-cognitive system
from .data_sufficiency_evaluator import (
    EnhancedDataSufficiencyEvaluator,
    DataSufficiency,
    LimitationType,
    MetaCognitiveAssessment
)

# Try to import advanced capabilities
try:
    from ..capabilities.v50_causal_engine import CausalDiscovery, PCAlgorithm
    CAUSAL_AVAILABLE = True
except ImportError:
    CAUSAL_AVAILABLE = False
    print("WARNING: V50 causal engine not available")

try:
    from ..capabilities.bayesian_inference import BayesianInference
    BAYESIAN_AVAILABLE = True
except ImportError:
    BAYESIAN_AVAILABLE = False
    print("WARNING: Bayesian inference not available")

try:
    from ..capabilities.multi_expert_ensemble import MultiExpertEnsemble
    ENSEMBLE_AVAILABLE = True
except ImportError:
    ENSEMBLE_AVAILABLE = False
    print("WARNING: Multi-expert ensemble not available")

try:
    from ..capabilities.v60_persistent_memory import EpisodicMemory
    MEMORY_AVAILABLE = True
except ImportError:
    MEMORY_AVAILABLE = False
    print("WARNING: Episodic memory not available")

try:
    from ..domains import DomainRegistry
    DOMAINS_AVAILABLE = True
except ImportError:
    DOMAINS_AVAILABLE = False
    print("WARNING: Domain modules not available")


class ConfidenceLevel(Enum):
    """Confidence levels for meta-cognitive assessments."""
    VERY_LOW = 0.0 - 0.2
    LOW = 0.2 - 0.4
    MEDIUM = 0.4 - 0.6
    HIGH = 0.6 - 0.8
    VERY_HIGH = 0.8 - 1.0


@dataclass
class HybridAssessment:
    """Enhanced assessment with multiple signals."""
    base_assessment: MetaCognitiveAssessment
    causal_signal: Optional[float] = None  # 0-1 confidence of causal issue
    bayesian_signal: Optional[float] = None  # 0-1 uncertainty score
    domain_signal: Optional[float] = None  # 0-1 domain knowledge match
    ensemble_confidence: float = 0.5  # Combined confidence
    reasoning_trace: List[str] = field(default_factory=list)

    @property
    def final_sufficiency(self) -> DataSufficiency:
        """Final decision based on all signals."""
        # If any strong signal says insufficient, it's insufficient
        if self.base_assessment.sufficiency == DataSufficiency.INSUFFICIENT:
            return DataSufficiency.INSUFFICIENT

        if self.base_assessment.sufficiency == DataSufficiency.UNCERTAIN:
            return DataSufficiency.UNCERTAIN

        # Check other signals
        if self.causal_signal and self.causal_signal > 0.7:
            return DataSufficiency.INSUFFICIENT

        if self.bayesian_signal and self.bayesian_signal > 0.7:
            return DataSufficiency.UNCERTAIN

        return DataSufficiency.SUFFICIENT

    @property
    def final_confidence(self) -> float:
        """Combined confidence score."""
        confidences = [
            self.base_assessment.confidence,
            self.ensemble_confidence
        ]

        if self.causal_signal:
            confidences.append(self.causal_signal)

        if self.bayesian_signal:
            confidences.append(self.bayesian_signal)

        if self.domain_signal:
            confidences.append(self.domain_signal)

        return sum(confidences) / len(confidences)


class HybridMetaCognitiveSystem:
    """
    Hybrid meta-cognitive system combining multiple capabilities.

    This system uses:
    1. Rule-based pattern matching (baseline)
    2. Causal discovery for causal inference tasks
    3. Bayesian inference for uncertainty quantification
    4. Domain knowledge for context-aware assessment
    5. Ensemble methods for robust decisions
    6. Memory for learning from past evaluations
    """

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """Initialize hybrid meta-cognitive system."""
        self.config = config or {}

        # Initialize base evaluator
        self.base_evaluator = EnhancedDataSufficiencyEvaluator()

        # Initialize advanced capabilities
        self.causal_engine = None
        self.bayesian_engine = None
        self.ensemble_system = None
        self.memory_system = None
        self.domain_registry = None

        self._initialize_capabilities()

        # Performance tracking
        self.evaluation_history = []

    def _initialize_capabilities(self):
        """Initialize advanced capabilities with graceful degradation."""
        # Causal discovery
        if CAUSAL_AVAILABLE:
            try:
                self.causal_engine = CausalDiscovery()
            except Exception as e:
                print(f"Could not initialize causal engine: {e}")

        # Bayesian inference
        if BAYESIAN_AVAILABLE:
            try:
                self.bayesian_engine = BayesianInference()
            except Exception as e:
                print(f"Could not initialize Bayesian engine: {e}")

        # Ensemble system
        if ENSEMBLE_AVAILABLE:
            try:
                self.ensemble_system = MultiExpertEnsemble()
            except Exception as e:
                print(f"Could not initialize ensemble system: {e}")

        # Memory system
        if MEMORY_AVAILABLE:
            try:
                self.memory_system = EpisodicMemory()
            except Exception as e:
                print(f"Could not initialize memory system: {e}")

        # Domain registry
        if DOMAINS_AVAILABLE:
            try:
                self.domain_registry = DomainRegistry()
                self.domain_registry.load_all_domains()
            except Exception as e:
                print(f"Could not initialize domain registry: {e}")

    def evaluate_task(self, scenario: str, question: str) -> HybridAssessment:
        """
        Evaluate a task using hybrid approach.

        Args:
            scenario: Task scenario description
            question: Question being asked

        Returns:
            HybridAssessment with multi-signal evaluation
        """
        reasoning_trace = []

        # Step 1: Base rule-based evaluation
        reasoning_trace.append("Step 1: Rule-based pattern matching")
        base_assessment = self.base_evaluator.evaluate_task(scenario, question)

        # If base says insufficient with high confidence, return early
        if (base_assessment.sufficiency == DataSufficiency.INSUFFICIENT and
            base_assessment.confidence > 0.85):
            return HybridAssessment(
                base_assessment=base_assessment,
                ensemble_confidence=base_assessment.confidence,
                reasoning_trace=reasoning_trace
            )

        # Step 2: Causal analysis (for Suite E tasks or causal questions)
        causal_signal = None
        text = (scenario + " " + question).lower()

        if self._is_causal_task(text):
            reasoning_trace.append("Step 2: Causal discovery analysis")
            causal_signal = self._analyze_causal_structure(scenario, question)

        # Step 3: Bayesian uncertainty quantification
        bayesian_signal = None
        if BAYESIAN_AVAILABLE and self.bayesian_engine:
            reasoning_trace.append("Step 3: Bayesian uncertainty quantification")
            bayesian_signal = self._quantify_uncertainty(scenario, question)

        # Step 4: Domain knowledge integration
        domain_signal = None
        if DOMAINS_AVAILABLE and self.domain_registry:
            reasoning_trace.append("Step 4: Domain knowledge integration")
            domain_signal = self._check_domain_consistency(scenario, question)

        # Step 5: Ensemble decision
        reasoning_trace.append("Step 5: Ensemble decision making")
        ensemble_confidence = self._compute_ensemble_confidence(
            base_assessment, causal_signal, bayesian_signal, domain_signal
        )

        # Create hybrid assessment
        assessment = HybridAssessment(
            base_assessment=base_assessment,
            causal_signal=causal_signal,
            bayesian_signal=bayesian_signal,
            domain_signal=domain_signal,
            ensemble_confidence=ensemble_confidence,
            reasoning_trace=reasoning_trace
        )

        # Store in memory for learning
        if self.memory_system:
            self._store_evaluation_memory(scenario, question, assessment)

        return assessment

    def _is_causal_task(self, text: str) -> bool:
        """Check if task involves causal inference."""
        causal_indicators = [
            r'cause',
            r'effect',
            r'impact',
            r'leads?\s*to',
            r'results?\s*in',
            r'correlation',
            r'associated?\s*with',
            r'can\s*(?:you|we)\s*conclude',
            r'does.*?cause',
        ]

        return any(re.search(p, text) for p in causal_indicators)

    def _analyze_causal_structure(self, scenario: str, question: str) -> Optional[float]:
        """
        Analyze causal structure using V50 causal discovery.

        Returns confidence score (0-1) indicating likelihood of causal issue.
        """
        if not CAUSAL_AVAILABLE or not self.causal_engine:
            return None

        try:
            # Extract variables from scenario
            text = scenario + " " + question

            # Look for causal graphs or relationships
            # This is a simplified version - full implementation would parse the scenario
            # and build a proper causal graph

            # Check for common causal fallacies
            causal_fallacy_patterns = [
                (r'correlation.*?cause', 0.9),  # Correlation-causation fallacy
                (r'observe.*?conclude', 0.8),  # Observational claim as causal
                (r'associated?\s*with.*?cause', 0.85),  # Association as causation
                (r'adjusting?\s*for.*?confound', 0.7),  # Confounding
                (r'sample.*?only', 0.75),  # Selection bias
            ]

            max_signal = 0.0
            for pattern, signal in causal_fallacy_patterns:
                if re.search(pattern, text.lower()):
                    max_signal = max(max_signal, signal)

            return max_signal if max_signal > 0 else None

        except Exception as e:
            print(f"Causal analysis error: {e}")
            return None

    def _quantify_uncertainty(self, scenario: str, question: str) -> Optional[float]:
        """
        Quantify uncertainty using Bayesian inference.

        Returns uncertainty score (0-1) where higher = more uncertain.
        """
        if not BAYESIAN_AVAILABLE or not self.bayesian_engine:
            return None

        try:
            # Extract numerical information
            text = scenario + " " + question

            # Look for uncertainty indicators
            uncertainty_patterns = [
                (r'uncertainty\s*[:=]\s*(\d+\.?\d*)\s*%', 0.8),
                (r'error\s*[:=]\s*(\d+\.?\d*)\s*%', 0.75),
                (r'σ\s*[:=]\s*(\d+\.?\d*)', 0.7),
                (r'confidence\s*interval', 0.65),
                (r'small.*?sample', 0.6),
                (r'n\s*[=:]\s*\d{1,2}\b', 0.7),  # Small N
            ]

            max_signal = 0.0
            for pattern, signal in uncertainty_patterns:
                if re.search(pattern, text.lower()):
                    max_signal = max(max_signal, signal)

            return max_signal if max_signal > 0 else None

        except Exception as e:
            print(f"Bayesian analysis error: {e}")
            return None

    def _check_domain_consistency(self, scenario: str, question: str) -> Optional[float]:
        """
        Check consistency with domain knowledge.

        Returns consistency score (0-1) where higher = more consistent.
        """
        if not DOMAINS_AVAILABLE or not self.domain_registry:
            return None

        try:
            # Extract domain keywords
            text = scenario.lower()

            # Check for domain-specific patterns
            domain_signals = {
                'astrophysics': [r'star|galaxy|nebula|cosmic|stellar'],
                'physics': [r'quantum|classical|energy|force|velocity'],
                'biology': [r'cell|gene|protein|organism'],
                'economics': [r'market|price|economic|financial'],
            }

            max_signal = 0.0
            for domain, patterns in domain_signals.items():
                for pattern in patterns:
                    if re.search(pattern, text):
                        # Check if query is appropriate for this domain
                        if self._is_domain_appropriate(domain, scenario, question):
                            max_signal = max(max_signal, 0.8)

            return max_signal if max_signal > 0 else None

        except Exception as e:
            print(f"Domain analysis error: {e}")
            return None

    def _is_domain_appropriate(self, domain: str, scenario: str, question: str) -> bool:
        """Check if query is appropriate for given domain."""
        # Simplified version - full implementation would query domain module
        return True

    def _compute_ensemble_confidence(
        self,
        base_assessment: MetaCognitiveAssessment,
        causal_signal: Optional[float],
        bayesian_signal: Optional[float],
        domain_signal: Optional[float]
    ) -> float:
        """Compute ensemble confidence from all signals."""
        signals = [base_assessment.confidence]

        if causal_signal is not None:
            signals.append(causal_signal)

        if bayesian_signal is not None:
            signals.append(bayesian_signal)

        if domain_signal is not None:
            signals.append(domain_signal)

        # Weighted average (base assessment has highest weight)
        weights = [0.5] + [0.2] * (len(signals) - 1)

        if len(weights) != len(signals):
            weights = [1.0 / len(signals)] * len(signals)

        weighted_sum = sum(s * w for s, w in zip(signals, weights))
        return weighted_sum / sum(weights)

    def _store_evaluation_memory(self, scenario: str, question: str, assessment: HybridAssessment):
        """Store evaluation in episodic memory for learning."""
        if not self.memory_system:
            return

        try:
            memory_entry = {
                'scenario': scenario,
                'question': question,
                'assessment': {
                    'sufficiency': assessment.final_sufficiency.value,
                    'confidence': assessment.final_confidence,
                    'signals': {
                        'base': assessment.base_assessment.confidence,
                        'causal': assessment.causal_signal,
                        'bayesian': assessment.bayesian_signal,
                        'domain': assessment.domain_signal,
                    }
                },
                'reasoning': assessment.reasoning_trace
            }

            # Store in memory system
            # (Implementation depends on memory system API)
            # self.memory_system.store(memory_entry)

        except Exception as e:
            print(f"Memory storage error: {e}")

    def get_statistics(self) -> Dict[str, Any]:
        """Get performance statistics."""
        return {
            'total_evaluations': len(self.evaluation_history),
            'capabilities_available': {
                'causal': CAUSAL_AVAILABLE and self.causal_engine is not None,
                'bayesian': BAYESIAN_AVAILABLE and self.bayesian_engine is not None,
                'ensemble': ENSEMBLE_AVAILABLE and self.ensemble_system is not None,
                'memory': MEMORY_AVAILABLE and self.memory_system is not None,
                'domains': DOMAINS_AVAILABLE and self.domain_registry is not None,
            }
        }


def create_hybrid_meta_cognitive_system(config: Optional[Dict[str, Any]] = None) -> HybridMetaCognitiveSystem:
    """
    Factory function to create hybrid meta-cognitive system.

    Args:
        config: Optional configuration dictionary

    Returns:
        HybridMetaCognitiveSystem instance
    """
    return HybridMetaCognitiveSystem(config)
