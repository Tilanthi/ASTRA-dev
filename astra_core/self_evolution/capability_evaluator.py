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
Capability Evaluator for STAN Self-Evolution

Evaluates the reasoning and discovery capabilities of the system
using the defined baseline tasks. Provides objective scores
without requiring human supervision.
"""

from dataclasses import dataclass, field
from typing import Dict, List, Any, Optional, Tuple
from enum import Enum
import numpy as np
import time
import sys
import os

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

try:
    from .capability_baseline import (
        CapabilityBaseline,
        CapabilityProfile,
        ReasoningTask,
        ReasoningMetric,
    )
except ImportError:
    # Fallback imports
    from capability_baseline import (
        CapabilityBaseline,
        CapabilityProfile,
        ReasoningTask,
        ReasoningMetric,
    )


class CapabilityDomain(Enum):
    """Domains of capability to evaluate"""
    ASTROPHYSICS = "astrophysics"
    CAUSAL_REASONING = "causal_reasoning"
    PATTERN_DISCOVERY = "pattern_discovery"
    ABSTRACT_REASONING = "abstract_reasoning"
    QUANTITATIVE_INFERENCE = "quantitative_inference"
    GENERATIVE_CAPABILITY = "generative_capability"


@dataclass
class EvaluationResult:
    """Result of a capability evaluation"""
    profile: CapabilityProfile
    domain_results: Dict[CapabilityDomain, float]
    test_results: Dict[str, Any]
    execution_time: float
    success: bool
    error_message: Optional[str] = None
    timestamp: float = field(default_factory=time.time)


class CapabilityEvaluator:
    """
    Evaluates system capabilities using objective metrics.

    This provides the feedback signal for evolution by testing
    the system on challenging reasoning tasks.
    """

    def __init__(self, stan_core_path: str = "/shared/ASTRA"):
        self.stan_core_path = stan_core_path
        self.baseline = CapabilityBaseline(stan_core_path)
        self.system = None
        self.evaluation_history: List[EvaluationResult] = []

    def load_system(self) -> bool:
        """
        Load the astra_core system for evaluation.

        Returns:
            True if system loaded successfully
        """
        try:
            # Import astra_core
            sys.path.insert(0, self.stan_core_path)

            from astra_core import create_stan_system

            self.system = create_stan_system(version="unified", mode="astronomy")

            return self.system is not None

        except Exception as e:
            print(f"Error loading system: {e}")
            return False

    def evaluate_full(self, task_filter: Optional[List[str]] = None) -> EvaluationResult:
        """
        Perform full capability evaluation.

        Args:
            task_filter: Optional list of specific tasks to run

        Returns:
            EvaluationResult with complete capability profile
        """
        start_time = time.time()

        try:
            # Ensure system is loaded
            if self.system is None:
                if not self.load_system():
                    return EvaluationResult(
                        profile=CapabilityProfile(scores={}, overall_score=0.0, strengths=[], weaknesses=[]),
                        domain_results={},
                        test_results={},
                        execution_time=0.0,
                        success=False,
                        error_message="Failed to load system"
                    )

            # Run baseline evaluation
            profile = self.baseline.evaluate_capability(self.system, task_filter)

            # Map to domains
            domain_results = self._map_to_domains(profile)

            # Extract test results
            test_results = {
                metric.value: {
                    'score': score.value,
                    'confidence': score.confidence,
                    'details': score.details
                }
                for metric, score in profile.scores.items()
            }

            execution_time = time.time() - start_time

            result = EvaluationResult(
                profile=profile,
                domain_results=domain_results,
                test_results=test_results,
                execution_time=execution_time,
                success=True
            )

            self.evaluation_history.append(result)
            return result

        except Exception as e:
            execution_time = time.time() - start_time
            return EvaluationResult(
                profile=CapabilityProfile(scores={}, overall_score=0.0, strengths=[], weaknesses=[]),
                domain_results={},
                test_results={},
                execution_time=execution_time,
                success=False,
                error_message=str(e)
            )

    def evaluate_domain(self, domain: CapabilityDomain) -> float:
        """
        Evaluate a specific capability domain.

        Args:
            domain: Domain to evaluate

        Returns:
            Domain score (0-1)
        """
        # Map domain to relevant tasks
        domain_to_tasks = {
            CapabilityDomain.ASTROPHYSICS: [
                "spectral_pattern_discovery",
                "multi_scale_inference",
                "hypothesis_generation",
            ],
            CapabilityDomain.CAUSAL_REASONING: [
                "causal_inference",
                "counterfactual_reasoning",
            ],
            CapabilityDomain.PATTERN_DISCOVERY: [
                "spectral_pattern_discovery",
            ],
            CapabilityDomain.ABSTRACT_REASONING: [
                "abstraction_formation",
                "cross_domain_transfer",
            ],
            CapabilityDomain.QUANTITATIVE_INFERENCE: [
                "uncertainty_quantification",
                "causal_inference",
            ],
            CapabilityDomain.GENERATIVE_CAPABILITY: [
                "hypothesis_generation",
                "counterfactual_reasoning",
            ],
        }

        tasks = domain_to_tasks.get(domain, [])

        if not tasks:
            return 0.0

        result = self.evaluate_full(task_filter=tasks)

        if result.success:
            # Return average score for this domain
            domain_scores = [
                result.test_results.get(task, {}).get('score', 0.0)
                for task in tasks
            ]
            return np.mean(domain_scores) if domain_scores else 0.0

        return 0.0

    def _map_to_domains(self, profile: CapabilityProfile) -> Dict[CapabilityDomain, float]:
        """Map capability profile to domain scores"""
        domain_scores = {}

        # Map metrics to domains
        metric_to_domain = {
            ReasoningMetric.PATTERN_DISCOVERY: CapabilityDomain.PATTERN_DISCOVERY,
            ReasoningMetric.INFERENCE_VALIDITY: CapabilityDomain.CAUSAL_REASONING,
            ReasoningMetric.ABSTRACTION_QUALITY: CapabilityDomain.ABSTRACT_REASONING,
            ReasoningMetric.CROSS_DOMAIN_TRANSFER: CapabilityDomain.ABSTRACT_REASONING,
            ReasoningMetric.UNCERTAINTY_CALIBRATION: CapabilityDomain.QUANTITATIVE_INFERENCE,
            ReasoningMetric.HYPOTHESIS_QUALITY: CapabilityDomain.GENERATIVE_CAPABILITY,
        }

        # Aggregate scores by domain
        domain_totals: Dict[CapabilityDomain, List[float]] = {}

        for metric, score in profile.scores.items():
            domain = metric_to_domain.get(metric)
            if domain:
                if domain not in domain_totals:
                    domain_totals[domain] = []
                domain_totals[domain].append(score.value)

        # Compute domain averages
        for domain, scores in domain_totals.items():
            domain_scores[domain] = np.mean(scores) if scores else 0.0

        # Ensure all domains have scores
        for domain in CapabilityDomain:
            if domain not in domain_scores:
                domain_scores[domain] = 0.0

        return domain_scores

    def compare_to_baseline(self, baseline_name: str = "initial") -> Dict[str, Any]:
        """
        Compare current evaluation to a saved baseline.

        Args:
            baseline_name: Name of baseline to compare against

        Returns:
            Comparison results
        """
        baseline = self.baseline.load_baseline(baseline_name)

        if not baseline:
            return {'error': f'Baseline {baseline_name} not found'}

        if not self.evaluation_history:
            return {'error': 'No evaluations performed'}

        current = self.evaluation_history[-1].profile

        comparison = self.baseline.compare_profiles(baseline, current)

        return comparison

    def get_improvement_suggestions(self) -> List[Dict[str, Any]]:
        """
        Get suggestions for capability improvements.

        Returns:
            List of improvement suggestions
        """
        if not self.evaluation_history:
            return []

        profile = self.evaluation_history[-1].profile

        suggestions = []

        # Identify weaknesses
        for weakness in profile.weaknesses:
            score = profile.scores.get(weakness)

            if score:
                suggestion = {
                    'metric': weakness.value,
                    'current_score': score.value,
                    'suggested_mutations': self._get_mutations_for_metric(weakness),
                }
                suggestions.append(suggestion)

        return suggestions

    def _get_mutations_for_metric(self, metric: ReasoningMetric) -> List[str]:
        """Get suggested mutation types for improving a metric"""
        mutation_suggestions = {
            ReasoningMetric.PATTERN_DISCOVERY: [
                "Add multi-scale pattern detection",
                "Implement wavelet-based analysis",
                "Add deep learning pattern recognition",
            ],
            ReasoningMetric.INFERENCE_VALIDITY: [
                "Improve conditional independence tests",
                "Add time-series causal discovery",
                "Implement counterfactual inference",
            ],
            ReasoningMetric.ABSTRACTION_QUALITY: [
                "Add symbolic reasoning layer",
                "Implement principle extraction",
                "Add conceptual abstraction",
            ],
            ReasoningMetric.CROSS_DOMAIN_TRANSFER: [
                "Add analogy detection",
                "Implement cross-domain mapping",
                "Add transfer learning",
            ],
            ReasoningMetric.UNCERTAINTY_CALIBRATION: [
                "Add Bayesian inference",
                "Implement Monte Carlo sampling",
                "Add confidence calibration",
            ],
        }

        return mutation_suggestions.get(metric, [])

    def save_current_as_baseline(self, name: str) -> bool:
        """
        Save current evaluation as a named baseline.

        Args:
            name: Name for the baseline

        Returns:
            True if saved successfully
        """
        if not self.evaluation_history:
            return False

        profile = self.evaluation_history[-1].profile

        self.baseline.save_baseline(name, profile)

        return True

    def get_evaluation_summary(self) -> Dict[str, Any]:
        """
        Get summary of all evaluations.

        Returns:
            Summary statistics
        """
        if not self.evaluation_history:
            return {'evaluations_performed': 0}

        scores = [e.profile.overall_score for e in self.evaluation_history]

        return {
            'evaluations_performed': len(self.evaluation_history),
            'latest_score': scores[-1] if scores else 0.0,
            'best_score': max(scores) if scores else 0.0,
            'average_score': np.mean(scores) if scores else 0.0,
            'improvement_trend': scores[-1] - scores[0] if len(scores) > 1 else 0.0,
            'latest_evaluation': self.evaluation_history[-1].timestamp,
        }


__all__ = [
    'CapabilityDomain',
    'EvaluationResult',
    'CapabilityEvaluator',
]
