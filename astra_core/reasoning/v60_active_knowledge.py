"""
V60 Active Knowledge Acquisition

Autonomous hypothesis-driven learning system that:
- Identifies knowledge gaps requiring investigation
- Generates hypotheses to fill those gaps
- Designs experiments to test hypotheses
- Integrates new knowledge coherently

Key innovations:
1. Curiosity-driven exploration prioritizing high-information-gain queries
2. Hypothesis generation using abductive reasoning
3. Experiment design for efficient hypothesis testing
4. Knowledge integration preventing inconsistencies
"""

from dataclasses import dataclass, field
from typing import Dict, List, Optional, Any, Set, Tuple, Callable
from enum import Enum
from abc import ABC, abstractmethod
import numpy as np
from collections import defaultdict
import heapq
import time


class KnowledgeGapType(Enum):
    """Types of knowledge gaps"""
    MISSING_CONCEPT = "missing_concept"
    INCOMPLETE_RELATION = "incomplete_relation"
    UNCERTAIN_VALUE = "uncertain_value"
    CONFLICTING_INFO = "conflicting_info"
    CAUSAL_UNKNOWN = "causal_unknown"
    BOUNDARY_UNKNOWN = "boundary_unknown"


class HypothesisStatus(Enum):
    """Status of a hypothesis"""
    PROPOSED = "proposed"
    TESTING = "testing"
    SUPPORTED = "supported"
    REFUTED = "refuted"
    REVISED = "revised"


class ExperimentType(Enum):
    """Types of experiments"""
    OBSERVATION = "observation"
    INTERVENTION = "intervention"
    COUNTERFACTUAL = "counterfactual"
    COMPARISON = "comparison"
    SIMULATION = "simulation"


class CuriositySource(Enum):
    """Sources of curiosity/exploration drive"""
    INFORMATION_GAIN = "information_gain"
    PREDICTION_ERROR = "prediction_error"
    NOVELTY = "novelty"
    UNCERTAINTY = "uncertainty"
    TASK_RELEVANCE = "task_relevance"


@dataclass
class KnowledgeGap:
    """Identified gap in knowledge"""
    id: str
    gap_type: KnowledgeGapType
    description: str
    context: Dict[str, Any]
    priority: float = 0.5
    information_gain: float = 0.0
    related_concepts: List[str] = field(default_factory=list)
    discovered_at: float = field(default_factory=time.time)
    resolved: bool = False
    resolution: Optional[str] = None


@dataclass
class Hypothesis:
    """A hypothesis about the world"""
    id: str
    statement: str
    gap_id: str
    prior_probability: float
    posterior_probability: float = 0.5
    supporting_evidence: List[Dict[str, Any]] = field(default_factory=list)
    contradicting_evidence: List[Dict[str, Any]] = field(default_factory=list)
    status: HypothesisStatus = HypothesisStatus.PROPOSED
    confidence: float = 0.5
    testable: bool = True
    test_conditions: List[Dict[str, Any]] = field(default_factory=list)
    created_at: float = field(default_factory=time.time)

    def update_probability(self, evidence: Dict[str, Any], likelihood_ratio: float):
        """Bayesian update of hypothesis probability"""
        if likelihood_ratio > 1:
            self.supporting_evidence.append(evidence)
        else:
            self.contradicting_evidence.append(evidence)

        # Bayes update
        prior = self.posterior_probability
        posterior = (likelihood_ratio * prior) / (
            likelihood_ratio * prior + (1 - prior)
        )
        self.posterior_probability = np.clip(posterior, 0.01, 0.99)

        # Update confidence based on evidence count
        total_evidence = len(self.supporting_evidence) + len(self.contradicting_evidence)
        self.confidence = min(0.95, 0.5 + 0.05 * total_evidence)


@dataclass
class Experiment:
    """An experiment to test hypotheses"""
    id: str
    experiment_type: ExperimentType
    hypothesis_ids: List[str]
    design: Dict[str, Any]
    expected_outcomes: Dict[str, float]  # outcome -> probability
    actual_outcome: Optional[str] = None
    information_gain: float = 0.0
    cost: float = 1.0
    status: str = "planned"
    results: Optional[Dict[str, Any]] = None


@dataclass
class KnowledgeIntegration:
    """Result of integrating new knowledge"""
    success: bool
    new_concepts: List[str]
    updated_concepts: List[str]
    resolved_conflicts: List[str]
    remaining_inconsistencies: List[str]


class GapDetector:
    """
    Detects gaps in knowledge base.
    """

    def __init__(self):
        self.known_concepts: Set[str] = set()
        self.known_relations: Dict[str, Set[Tuple[str, str]]] = defaultdict(set)
        self.concept_properties: Dict[str, Dict[str, Any]] = {}
        self.uncertainty_thresholds = {
            'high': 0.3,
            'medium': 0.5,
            'low': 0.7
        }

    def detect_gaps(
        self,
        query_context: Dict[str, Any],
        knowledge_base: Dict[str, Any]
    ) -> List[KnowledgeGap]:
        """Detect knowledge gaps given a query context"""
        gaps = []

        # Check for missing concepts
        gaps.extend(self._detect_missing_concepts(query_context, knowledge_base))

        # Check for incomplete relations
        gaps.extend(self._detect_incomplete_relations(query_context, knowledge_base))

        # Check for uncertain values
        gaps.extend(self._detect_uncertain_values(query_context, knowledge_base))

        # Check for conflicts
        gaps.extend(self._detect_conflicts(query_context, knowledge_base))

        # Prioritize gaps
        for gap in gaps:
            gap.priority = self._compute_priority(gap, query_context)

        return sorted(gaps, key=lambda g: g.priority, reverse=True)

    def _detect_missing_concepts(
        self,
        query_context: Dict[str, Any],
        knowledge_base: Dict[str, Any]
    ) -> List[KnowledgeGap]:
        """Detect referenced but unknown concepts"""
        gaps = []
        referenced = query_context.get('referenced_concepts', [])
        known = set(knowledge_base.get('concepts', {}).keys())

        for concept in referenced:
            if concept not in known:
                gap = KnowledgeGap(
                    id=f"gap_missing_{concept}_{time.time()}",
                    gap_type=KnowledgeGapType.MISSING_CONCEPT,
                    description=f"Unknown concept: {concept}",
                    context={'concept': concept},
                    related_concepts=[c for c in referenced if c != concept]
                )
                gaps.append(gap)

        return gaps

    def _detect_incomplete_relations(
        self,
        query_context: Dict[str, Any],
        knowledge_base: Dict[str, Any]
    ) -> List[KnowledgeGap]:
        """Detect incomplete relational knowledge"""
        gaps = []
        expected_relations = query_context.get('expected_relations', [])
        known_relations = knowledge_base.get('relations', {})

        for relation in expected_relations:
            rel_type = relation.get('type')
            source = relation.get('source')
            target = relation.get('target')

            # Check if relation exists
            if rel_type in known_relations:
                rel_pairs = known_relations[rel_type]
                if (source, target) not in rel_pairs and (source, None) not in rel_pairs:
                    gap = KnowledgeGap(
                        id=f"gap_relation_{rel_type}_{source}_{time.time()}",
                        gap_type=KnowledgeGapType.INCOMPLETE_RELATION,
                        description=f"Unknown relation: {source} {rel_type} ?",
                        context={'relation_type': rel_type, 'source': source},
                        related_concepts=[source]
                    )
                    gaps.append(gap)

        return gaps

    def _detect_uncertain_values(
        self,
        query_context: Dict[str, Any],
        knowledge_base: Dict[str, Any]
    ) -> List[KnowledgeGap]:
        """Detect values with high uncertainty"""
        gaps = []
        concepts = knowledge_base.get('concepts', {})

        for concept_id, concept_data in concepts.items():
            confidence = concept_data.get('confidence', 1.0)

            if confidence < self.uncertainty_thresholds['high']:
                gap = KnowledgeGap(
                    id=f"gap_uncertain_{concept_id}_{time.time()}",
                    gap_type=KnowledgeGapType.UNCERTAIN_VALUE,
                    description=f"High uncertainty for: {concept_id} (conf={confidence:.2f})",
                    context={'concept': concept_id, 'confidence': confidence},
                    information_gain=1.0 - confidence
                )
                gaps.append(gap)

        return gaps

    def _detect_conflicts(
        self,
        query_context: Dict[str, Any],
        knowledge_base: Dict[str, Any]
    ) -> List[KnowledgeGap]:
        """Detect conflicting information"""
        gaps = []
        conflicts = knowledge_base.get('conflicts', [])

        for conflict in conflicts:
            gap = KnowledgeGap(
                id=f"gap_conflict_{time.time()}_{np.random.randint(1000)}",
                gap_type=KnowledgeGapType.CONFLICTING_INFO,
                description=f"Conflict: {conflict.get('description', 'Unknown')}",
                context=conflict,
                priority=0.9  # Conflicts are high priority
            )
            gaps.append(gap)

        return gaps

    def _compute_priority(
        self,
        gap: KnowledgeGap,
        query_context: Dict[str, Any]
    ) -> float:
        """Compute priority score for a gap"""
        base_priority = gap.priority

        # Boost for task relevance
        task_concepts = set(query_context.get('task_concepts', []))
        related = set(gap.related_concepts)
        if task_concepts & related:
            base_priority *= 1.5

        # Boost for information gain
        base_priority += gap.information_gain * 0.3

        # Type-specific adjustments
        type_weights = {
            KnowledgeGapType.CONFLICTING_INFO: 1.3,
            KnowledgeGapType.CAUSAL_UNKNOWN: 1.2,
            KnowledgeGapType.MISSING_CONCEPT: 1.0,
            KnowledgeGapType.INCOMPLETE_RELATION: 0.9,
            KnowledgeGapType.UNCERTAIN_VALUE: 0.8,
            KnowledgeGapType.BOUNDARY_UNKNOWN: 0.7
        }
        base_priority *= type_weights.get(gap.gap_type, 1.0)

        return min(1.0, base_priority)


class HypothesisGenerator:
    """
    Generates hypotheses to explain gaps using abductive reasoning.
    """

    def __init__(self):
        self.hypothesis_templates: Dict[KnowledgeGapType, List[str]] = {
            KnowledgeGapType.MISSING_CONCEPT: [
                "{concept} is a type of {parent_type}",
                "{concept} is related to {related} via {relation}",
                "{concept} has property {property} = {value}"
            ],
            KnowledgeGapType.INCOMPLETE_RELATION: [
                "{source} {relation} {target}",
                "{source} does not {relation} anything",
                "{source} {relation} multiple entities"
            ],
            KnowledgeGapType.UNCERTAIN_VALUE: [
                "The true value of {property} is {value}",
                "{property} varies based on {condition}",
                "{property} is not well-defined"
            ],
            KnowledgeGapType.CONFLICTING_INFO: [
                "Source A is correct about {claim}",
                "Source B is correct about {claim}",
                "Both sources are partially correct",
                "Context determines which is correct"
            ],
            KnowledgeGapType.CAUSAL_UNKNOWN: [
                "{cause} causes {effect}",
                "{effect} has multiple causes including {cause}",
                "The causal relationship is spurious"
            ]
        }

    def generate_hypotheses(
        self,
        gap: KnowledgeGap,
        knowledge_base: Dict[str, Any],
        max_hypotheses: int = 5
    ) -> List[Hypothesis]:
        """Generate hypotheses to fill a knowledge gap"""
        hypotheses = []

        # Get templates for this gap type
        templates = self.hypothesis_templates.get(gap.gap_type, [])

        # Generate from templates
        for i, template in enumerate(templates[:max_hypotheses]):
            statement = self._instantiate_template(template, gap, knowledge_base)

            hypothesis = Hypothesis(
                id=f"hyp_{gap.id}_{i}",
                statement=statement,
                gap_id=gap.id,
                prior_probability=self._compute_prior(statement, gap, knowledge_base),
                testable=self._is_testable(statement),
                test_conditions=self._generate_test_conditions(statement, gap)
            )
            hypotheses.append(hypothesis)

        # Generate analogical hypotheses
        analogical = self._generate_analogical_hypotheses(gap, knowledge_base)
        hypotheses.extend(analogical[:max_hypotheses - len(hypotheses)])

        return hypotheses

    def _instantiate_template(
        self,
        template: str,
        gap: KnowledgeGap,
        knowledge_base: Dict[str, Any]
    ) -> str:
        """Instantiate a hypothesis template with context"""
        context = gap.context.copy()

        # Add knowledge base concepts for substitution
        concepts = list(knowledge_base.get('concepts', {}).keys())
        if concepts and 'related' not in context:
            context['related'] = np.random.choice(concepts) if concepts else 'unknown'

        if 'parent_type' not in context:
            context['parent_type'] = 'entity'

        if 'relation' not in context:
            context['relation'] = 'is_related_to'

        if 'property' not in context:
            context['property'] = 'value'

        if 'value' not in context:
            context['value'] = 'unknown'

        if 'cause' not in context:
            context['cause'] = context.get('concept', 'X')

        if 'effect' not in context:
            context['effect'] = 'Y'

        if 'source' not in context:
            context['source'] = context.get('concept', 'X')

        if 'target' not in context:
            context['target'] = 'unknown'

        if 'claim' not in context:
            context['claim'] = context.get('hypothesis', 'No claim')

        return context
