"""
Evaluation Metrics for Ablation Studies

Defines metrics to evaluate the impact of ablations on ASTRA's performance.
"""

from dataclasses import dataclass, field
from typing import List, Dict, Any, Callable, Optional
from enum import Enum
import re
import json
from datetime import datetime


class MetricCategory(Enum):
    """Categories of evaluation metrics"""
    HYPOTHIS_GENERATION = "hypothesis_generation"
    SCIENTIFIC_ACCURACY = "scientific_accuracy"
    REASONING_QUALITY = "reasoning_quality"
    CROSS_DOMAIN_SYNTHESIS = "cross_domain_synthesis"
    EFFICIENCY = "efficiency"
    ROBUSTNESS = "robustness"


@dataclass
class EvaluationMetric:
    """Definition of an evaluation metric"""
    name: str
    description: str
    category: MetricCategory
    higher_is_better: bool = True
    weight: float = 1.0

    # Evaluation function
    evaluate_fn: Optional[Callable] = None


@dataclass
class QueryResult:
    """Result of processing a query"""
    query: str
    answer: str
    reasoning_trace: List[str] = field(default_factory=list)
    confidence: float = 0.0
    sources: List[str] = field(default_factory=list)
    processing_time: float = 0.0
    error: Optional[str] = None


@dataclass
class MetricScore:
    """Score for a single metric"""
    metric_name: str
    value: float
    normalized_value: float  # 0-1 scale
    details: Dict[str, Any] = field(default_factory=dict)


@dataclass
class AblationEvaluation:
    """Complete evaluation of an ablation"""
    ablation_name: str
    query_results: List[QueryResult] = field(default_factory=list)
    metric_scores: List[MetricScore] = field(default_factory=list)
    overall_score: float = 0.0
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())


class HypothesisGenerationMetrics:
    """Metrics for evaluating hypothesis generation quality"""

    @staticmethod
    def novelty_score(result: QueryResult) -> float:
        """Score: Novelty of generated hypotheses (0-1)"""
        # Check for novel concepts/ideas beyond standard literature
        answer_lower = result.answer.lower()

        novelty_indicators = [
            "novel", "new", "previously unobserved", "unexpected",
            "counterintuitive", "surprising", "innovative"
        ]

        score = 0.0
        for indicator in novelty_indicators:
            if indicator in answer_lower:
                score += 0.15

        return min(score, 1.0)

    @staticmethod
    def feasibility_score(result: QueryResult) -> float:
        """Score: Feasibility of proposed hypotheses (0-1)"""
        # Check for testable predictions, methodology
        answer_lower = result.answer.lower()

        feasibility_indicators = [
            "testable", "observable", "measurable", "falsifiable",
            "prediction", "observable signature", "can be tested"
        ]

        score = 0.0
        for indicator in feasibility_indicators:
            if indicator in answer_lower:
                score += 0.2

        return min(score, 1.0)

    @staticmethod
    def specificity_score(result: QueryResult) -> float:
        """Score: Specificity of hypotheses (0-1)"""
        # Check for quantitative predictions, specific mechanisms
        answer_lower = result.answer.lower()

        # Check for numbers/quantities
        has_numbers = bool(re.search(r'\d+\.?\d*\s*(erg|ev|k|kms|msun)', answer_lower))

        # Check for specific mechanisms
        mechanism_indicators = [
            "mechanism", "process", "caused by", "due to",
            "results from", "arises from"
        ]

        score = 0.3 if has_numbers else 0.0
        for indicator in mechanism_indicators:
            if indicator in answer_lower:
                score += 0.2

        return min(score, 1.0)


class ScientificAccuracyMetrics:
    """Metrics for evaluating scientific accuracy"""

    @staticmethod
    def factual_correctness(result: QueryResult, knowledge_base: Dict) -> float:
        """Score: Factual correctness of claims (0-1)"""
        # This would use hallucination register in production
        # For now, check for obvious factual errors
        answer_lower = result.answer.lower()

        # Check for physically implausible claims
        error_indicators = [
            "faster than light", "infinite density", "negative mass",
            "violates conservation", "impossible"
        ]

        score = 1.0
        for indicator in error_indicators:
            if indicator in answer_lower:
                score -= 0.3

        return max(score, 0.0)

    @staticmethod
    def consistency_with_physics(result: QueryResult) -> float:
        """Score: Consistency with known physics (0-1)"""
        # Check for references to physical laws/constants
        answer_lower = result.answer.lower()

        physics_indicators = [
            "conservation of", "thermodynamics", "maxwell's equations",
            "schrodinger equation", "general relativity", "newton's laws",
            "boltzmann", "planck", "einstein"
        ]

        score = 0.0
        for indicator in physics_indicators:
            if indicator in answer_lower:
                score += 0.15

        return min(score, 1.0)

    @staticmethod
    def citation_quality(result: QueryResult) -> float:
        """Score: Quality of citations/references (0-1)"""
        # Check for proper citations
        if not result.sources:
            return 0.3  # No citations

        # More sources = better (diminishing returns)
        score = min(len(result.sources) * 0.15, 1.0)
        return score


class ReasoningQualityMetrics:
    """Metrics for evaluating reasoning quality"""

    @staticmethod
    def logical_coherence(result: QueryResult) -> float:
        """Score: Logical coherence of reasoning (0-1)"""
        # Check for logical connectors
        answer_lower = result.answer.lower()

        logical_indicators = [
            "therefore", "thus", "consequently", "however", "nevertheless",
            "in contrast", "moreover", "furthermore", "because", "since"
        ]

        score = 0.0
        for indicator in logical_indicators:
            if indicator in answer_lower:
                score += 0.1

        return min(score, 1.0)

    @staticmethod
    def reasoning_depth(result: QueryResult) -> float:
        """Score: Depth of reasoning chain (0-1)"""
        # Check for multi-step reasoning
        if not result.reasoning_trace:
            return 0.3

        # More reasoning steps = deeper reasoning
        score = min(len(result.reasoning_trace) * 0.15, 1.0)
        return score

    @staticmethod
    def inference_quality(result: QueryResult) -> float:
        """Score: Quality of inferences made (0-1)"""
        # Check for explicit inferences
        answer_lower = result.answer.lower()

        inference_indicators = [
            "infers", "implies", "suggests that", "indicates",
            "leads to", "results in", "can be inferred"
        ]

        score = 0.0
        for indicator in inference_indicators:
            if indicator in answer_lower:
                score += 0.15

        return min(score, 1.0)


class CrossDomainSynthesisMetrics:
    """Metrics for evaluating cross-domain synthesis"""

    @staticmethod
    def domain_breadth(result: QueryResult) -> float:
        """Score: Number of domains integrated (0-1)"""
        # Check for references to multiple domains
        domains = [
            "ism", "star formation", "exoplanet", "cosmology",
            "high energy", "galactic", "solar system", "time domain",
            "gravitational wave"
        ]

        answer_lower = result.answer.lower()
        found_domains = sum(1 for d in domains if d in answer_lower)

        return min(found_domains * 0.15, 1.0)

    @staticmethod
    def synthesis_quality(result: QueryResult) -> float:
        """Score: Quality of cross-domain connections (0-1)"""
        # Check for explicit synthesis
        answer_lower = result.answer.lower()

        synthesis_indicators = [
            "combines", "integrates", "synthesizes", "bridges",
            "connects", "links", "unifies", "relationship between"
        ]

        score = 0.0
        for indicator in synthesis_indicators:
            if indicator in answer_lower:
                score += 0.15

        return min(score, 1.0)

    @staticmethod
    def analogy_quality(result: QueryResult) -> float:
        """Score: Quality of analogical reasoning (0-1)"""
        # Check for analogies
        answer_lower = result.answer.lower()

        analogy_indicators = [
            "analogous to", "similar to", "like", "resembles",
            "parallel to", "compared to", "analogy"
        ]

        score = 0.0
        for indicator in analogy_indicators:
            if indicator in answer_lower:
                score += 0.2

        return min(score, 1.0)


class EfficiencyMetrics:
    """Metrics for evaluating efficiency"""

    @staticmethod
    def processing_time(result: QueryResult) -> float:
        """Score: Processing time (inverse, normalized)"""
        # Faster is better, but with diminishing returns
        # Target: < 5 seconds for complex queries
        target_time = 5.0
        if result.processing_time <= target_time:
            return 1.0
        else:
            return max(0.0, 1.0 - (result.processing_time - target_time) / 10.0)

    @staticmethod
    def memory_efficiency(result: QueryResult) -> float:
        """Score: Memory efficiency (placeholder)"""
        # Would track actual memory usage in production
        # For now, assume reasonable efficiency
        return 0.8


class RobustnessMetrics:
    """Metrics for evaluating robustness"""

    @staticmethod
    def error_recovery(result: QueryResult) -> float:
        """Score: Ability to recover from errors (0-1)"""
        if result.error:
            # Check if system recovered and still provided useful answer
            if result.answer and len(result.answer) > 100:
                return 0.6  # Partial recovery
            return 0.2  # Failed to recover
        return 1.0

    @staticmethod
    def confidence_calibration(result: QueryResult) -> float:
        """Score: Confidence calibration accuracy (0-1)"""
        # Check if confidence matches answer quality
        if not result.reasoning_trace and result.confidence > 0.7:
            return 0.5  # Overconfident
        if result.reasoning_trace and result.confidence < 0.3:
            return 0.5  # Underconfident
        return 0.8


def get_all_metrics() -> List[EvaluationMetric]:
    """Get all evaluation metrics"""
    metrics = [
        # Hypothesis Generation
        EvaluationMetric(
            name="novelty",
            description="Novelty of generated hypotheses",
            category=MetricCategory.HYPOTHIS_GENERATION,
            weight=1.0
        ),
        EvaluationMetric(
            name="feasibility",
            description="Feasibility of proposed hypotheses",
            category=MetricCategory.HYPOTHIS_GENERATION,
            weight=1.2
        ),
        EvaluationMetric(
            name="specificity",
            description="Specificity of hypotheses",
            category=MetricCategory.HYPOTHIS_GENERATION,
            weight=1.0
        ),

        # Scientific Accuracy
        EvaluationMetric(
            name="factual_correctness",
            description="Factual correctness of claims",
            category=MetricCategory.SCIENTIFIC_ACCURACY,
            weight=1.5
        ),
        EvaluationMetric(
            name="physics_consistency",
            description="Consistency with known physics",
            category=MetricCategory.SCIENTIFIC_ACCURACY,
            weight=1.3
        ),
        EvaluationMetric(
            name="citation_quality",
            description="Quality of citations",
            category=MetricCategory.SCIENTIFIC_ACCURACY,
            weight=0.8
        ),

        # Reasoning Quality
        EvaluationMetric(
            name="logical_coherence",
            description="Logical coherence",
            category=MetricCategory.REASONING_QUALITY,
            weight=1.2
        ),
        EvaluationMetric(
            name="reasoning_depth",
            description="Depth of reasoning",
            category=MetricCategory.REASONING_QUALITY,
            weight=1.0
        ),
        EvaluationMetric(
            name="inference_quality",
            description="Quality of inferences",
            category=MetricCategory.REASONING_QUALITY,
            weight=1.1
        ),

        # Cross-Domain Synthesis
        EvaluationMetric(
            name="domain_breadth",
            description="Number of domains integrated",
            category=MetricCategory.CROSS_DOMAIN_SYNTHESIS,
            weight=1.0
        ),
        EvaluationMetric(
            name="synthesis_quality",
            description="Quality of cross-domain connections",
            category=MetricCategory.CROSS_DOMAIN_SYNTHESIS,
            weight=1.2
        ),
        EvaluationMetric(
            name="analogy_quality",
            description="Quality of analogical reasoning",
            category=MetricCategory.CROSS_DOMAIN_SYNTHESIS,
            weight=0.8
        ),

        # Efficiency
        EvaluationMetric(
            name="processing_time",
            description="Processing efficiency",
            category=MetricCategory.EFFICIENCY,
            weight=0.5
        ),

        # Robustness
        EvaluationMetric(
            name="error_recovery",
            description="Error recovery capability",
            category=MetricCategory.ROBUSTNESS,
            weight=0.7
        ),
        EvaluationMetric(
            name="confidence_calibration",
            description="Confidence calibration",
            category=MetricCategory.ROBUSTNESS,
            weight=0.5
        ),
    ]

    return metrics


def evaluate_result(result: QueryResult, metrics: Optional[List[EvaluationMetric]] = None) -> List[MetricScore]:
    """Evaluate a query result against all metrics"""
    if metrics is None:
        metrics = get_all_metrics()

    scores = []

    for metric in metrics:
        # Compute score based on metric category
        if metric.category == MetricCategory.HYPOTHIS_GENERATION:
            if metric.name == "novelty":
                value = HypothesisGenerationMetrics.novelty_score(result)
            elif metric.name == "feasibility":
                value = HypothesisGenerationMetrics.feasibility_score(result)
            elif metric.name == "specificity":
                value = HypothesisGenerationMetrics.specificity_score(result)
            else:
                value = 0.5

        elif metric.category == MetricCategory.SCIENTIFIC_ACCURACY:
            if metric.name == "factual_correctness":
                value = ScientificAccuracyMetrics.factual_correctness(result, {})
            elif metric.name == "physics_consistency":
                value = ScientificAccuracyMetrics.consistency_with_physics(result)
            elif metric.name == "citation_quality":
                value = ScientificAccuracyMetrics.citation_quality(result)
            else:
                value = 0.5

        elif metric.category == MetricCategory.REASONING_QUALITY:
            if metric.name == "logical_coherence":
                value = ReasoningQualityMetrics.logical_coherence(result)
            elif metric.name == "reasoning_depth":
                value = ReasoningQualityMetrics.reasoning_depth(result)
            elif metric.name == "inference_quality":
                value = ReasoningQualityMetrics.inference_quality(result)
            else:
                value = 0.5

        elif metric.category == MetricCategory.CROSS_DOMAIN_SYNTHESIS:
            if metric.name == "domain_breadth":
                value = CrossDomainSynthesisMetrics.domain_breadth(result)
            elif metric.name == "synthesis_quality":
                value = CrossDomainSynthesisMetrics.synthesis_quality(result)
            elif metric.name == "analogy_quality":
                value = CrossDomainSynthesisMetrics.analogy_quality(result)
            else:
                value = 0.5

        elif metric.category == MetricCategory.EFFICIENCY:
            if metric.name == "processing_time":
                value = EfficiencyMetrics.processing_time(result)
            else:
                value = 0.8

        elif metric.category == MetricCategory.ROBUSTNESS:
            if metric.name == "error_recovery":
                value = RobustnessMetrics.error_recovery(result)
            elif metric.name == "confidence_calibration":
                value = RobustnessMetrics.confidence_calibration(result)
            else:
                value = 0.8

        else:
            value = 0.5

        scores.append(MetricScore(
            metric_name=metric.name,
            value=value,
            normalized_value=value,  # Already 0-1 scale
            details={"category": metric.category.value}
        ))

    return scores


def compute_overall_score(metric_scores: List[MetricScore], metrics: Optional[List[EvaluationMetric]] = None) -> float:
    """Compute weighted overall score from metric scores"""
    if metrics is None:
        metrics = get_all_metrics()

    metric_dict = {m.name: m for m in metrics}
    total_weight = 0.0
    weighted_sum = 0.0

    for score in metric_scores:
        metric = metric_dict.get(score.metric_name)
        if metric:
            weighted_sum += score.normalized_value * metric.weight
            total_weight += metric.weight

    if total_weight == 0:
        return 0.0

    return weighted_sum / total_weight
