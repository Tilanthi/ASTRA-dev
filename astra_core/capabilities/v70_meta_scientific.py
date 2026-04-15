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
V70 Meta-Scientific Reasoner

A framework for reasoning about science itself - what makes good methodology,
which questions are worth asking, how to evaluate epistemic progress, and
how to discover new experimental approaches.

This module enables STAN to:
1. Evaluate and compare scientific methodologies
2. Identify high-value research questions
3. Track epistemic progress and knowledge gaps
4. Discover novel experimental designs
5. Reason about evidence quality and uncertainty
6. Synthesize cross-disciplinary insights
"""

import numpy as np
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Any, Callable, Set, Tuple
from enum import Enum, auto
from abc import ABC, abstractmethod
import logging
from collections import defaultdict
import hashlib
import json

logger = logging.getLogger(__name__)


# =============================================================================
# Enumerations
# =============================================================================

class MethodologyType(Enum):
    """Types of scientific methodology"""
    EXPERIMENTAL = auto()      # Controlled experiments
    OBSERVATIONAL = auto()     # Observational studies
    COMPUTATIONAL = auto()     # Simulation and modeling
    THEORETICAL = auto()       # Mathematical/logical derivation
    META_ANALYSIS = auto()     # Synthesis of studies
    CASE_STUDY = auto()        # In-depth single case
    LONGITUDINAL = auto()      # Time-series observation
    CROSS_SECTIONAL = auto()   # Point-in-time comparison
    BAYESIAN = auto()          # Bayesian inference approach
    MACHINE_LEARNING = auto()  # Data-driven discovery


class EvidenceQuality(Enum):
    """Hierarchy of evidence quality"""
    ANECDOTAL = 1
    CASE_REPORT = 2
    CASE_SERIES = 3
    CROSS_SECTIONAL = 4
    COHORT = 5
    CASE_CONTROL = 6
    RCT = 7                    # Randomized controlled trial
    SYSTEMATIC_REVIEW = 8
    META_ANALYSIS = 9


class QuestionType(Enum):
    """Types of scientific questions"""
    DESCRIPTIVE = auto()       # What is X?
    CAUSAL = auto()            # Does X cause Y?
    MECHANISTIC = auto()       # How does X work?
    PREDICTIVE = auto()        # What will happen if X?
    COMPARATIVE = auto()       # How does X compare to Y?
    EXISTENTIAL = auto()       # Does X exist?
    NORMATIVE = auto()         # What should X be?
    EXPLORATORY = auto()       # What patterns exist in X?


class KnowledgeState(Enum):
    """States of knowledge about a topic"""
    UNKNOWN = auto()           # No information
    HYPOTHESIZED = auto()      # Proposed but untested
    CONTESTED = auto()         # Conflicting evidence
    EMERGING = auto()          # Early evidence accumulating
    ESTABLISHED = auto()       # Strong evidence, consensus
    PARADIGMATIC = auto()      # Foundational assumption
    OVERTURNED = auto()        # Previously established, now rejected


class BiasType(Enum):
    """Types of bias in scientific studies"""
    SELECTION = auto()
    PUBLICATION = auto()
    CONFIRMATION = auto()
    SURVIVORSHIP = auto()
    MEASUREMENT = auto()
    RECALL = auto()
    FUNDING = auto()
    CITATION = auto()
    HAWTHORNE = auto()         # Observer effect


# =============================================================================
# Data Classes
# =============================================================================

@dataclass
class ScientificQuestion:
    """Represents a scientific question"""
    id: str
    question_text: str
    question_type: QuestionType
    domain: str
    sub_domain: Optional[str] = None
    variables: List[str] = field(default_factory=list)
    constraints: Dict[str, Any] = field(default_factory=dict)
    parent_questions: List[str] = field(default_factory=list)
    child_questions: List[str] = field(default_factory=list)
    knowledge_state: KnowledgeState = KnowledgeState.UNKNOWN
    importance_score: float = 0.5
    tractability_score: float = 0.5
    novelty_score: float = 0.5
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class Methodology:
    """Represents a scientific methodology"""
    id: str
    name: str
    methodology_type: MethodologyType
    description: str
    strengths: List[str] = field(default_factory=list)
    weaknesses: List[str] = field(default_factory=list)
    applicable_question_types: List[QuestionType] = field(default_factory=list)
    required_resources: Dict[str, Any] = field(default_factory=dict)
    typical_biases: List[BiasType] = field(default_factory=list)
    validity_internal: float = 0.5
    validity_external: float = 0.5
    precision: float = 0.5
    cost_estimate: float = 0.5  # Normalized 0-1


@dataclass
class Evidence:
    """Represents a piece of scientific evidence"""
    id: str
    source: str
    methodology_used: str
    quality: EvidenceQuality
    supports_hypothesis: Optional[str] = None
    contradicts_hypothesis: Optional[str] = None
    effect_size: Optional[float] = None
    confidence_interval: Optional[Tuple[float, float]] = None
    sample_size: Optional[int] = None
    p_value: Optional[float] = None
    bayesian_factor: Optional[float] = None
    potential_biases: List[BiasType] = field(default_factory=list)
    replication_status: str = "unreplicated"
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class KnowledgeGap:
    """Represents a gap in scientific knowledge"""
    id: str
    description: str
    domain: str
    related_questions: List[str] = field(default_factory=list)
    blocking_factors: List[str] = field(default_factory=list)
    potential_approaches: List[str] = field(default_factory=list)
    estimated_difficulty: float = 0.5
    estimated_impact: float = 0.5
    priority_score: float = 0.0


@dataclass
class ExperimentalDesign:
    """Represents an experimental design"""
    id: str
    name: str
    target_question: str
    methodology: Methodology
    variables: Dict[str, Any] = field(default_factory=dict)
    controls: List[str] = field(default_factory=list)
    sample_requirements: Dict[str, Any] = field(default_factory=dict)
    expected_outcomes: List[str] = field(default_factory=list)
    potential_confounds: List[str] = field(default_factory=list)
    power_analysis: Optional[Dict[str, float]] = None
    estimated_validity: float = 0.5
    novelty_score: float = 0.0


@dataclass
class EpistemicState:
    """Represents the current state of knowledge in a domain"""
    domain: str
    established_facts: Dict[str, Evidence] = field(default_factory=dict)
    active_hypotheses: Dict[str, List[Evidence]] = field(default_factory=dict)
    open_questions: List[ScientificQuestion] = field(default_factory=list)
    knowledge_gaps: List[KnowledgeGap] = field(default_factory=list)
    paradigms: List[str] = field(default_factory=list)
    anomalies: List[str] = field(default_factory=list)
    confidence_map: Dict[str, float] = field(default_factory=dict)


# =============================================================================
# Methodology Evaluator
# =============================================================================

class MethodologyEvaluator:
    """Evaluates and compares scientific methodologies"""

    def __init__(self):
        self.methodology_registry: Dict[str, Methodology] = {}
        self.evaluation_criteria = self._init_criteria()
        self._init_standard_methodologies()

    def _init_criteria(self) -> Dict[str, Callable]:
        """Initialize evaluation criteria"""
        return {
            'internal_validity': self._assess_internal_validity,
            'external_validity': self._assess_external_validity,
            'reliability': self._assess_reliability,
            'objectivity': self._assess_objectivity,
            'precision': self._assess_precision,
            'feasibility': self._assess_feasibility,
            'ethical': self._assess_ethical_considerations,
            'novelty': self._assess_novelty
        }

    def _init_standard_methodologies(self):
        """Initialize standard scientific methodologies"""
        methodologies = [
            Methodology(
                id="rct",
                name="Randomized Controlled Trial",
                methodology_type=MethodologyType.EXPERIMENTAL,
                description="Gold standard for causal inference with random assignment",
                strengths=["Strong causal inference", "Controls confounds", "Replicable"],
                weaknesses=["Expensive", "Ethical constraints", "External validity"],
                applicable_question_types=[QuestionType.CAUSAL, QuestionType.COMPARATIVE],
                typical_biases=[BiasType.SELECTION, BiasType.HAWTHORNE],
                validity_internal=0.95,
                validity_external=0.6,
                precision=0.9,
                cost_estimate=0.8
            ),
            Methodology(
                id="observational_cohort",
                name="Observational Cohort Study",
                methodology_type=MethodologyType.OBSERVATIONAL,
                description="Following groups over time without intervention",
                strengths=["Ethical", "Real-world validity", "Long-term effects"],
                weaknesses=["Confounds", "Attrition", "Time-consuming"],
                applicable_question_types=[QuestionType.CAUSAL, QuestionType.PREDICTIVE],
                typical_biases=[BiasType.SELECTION, BiasType.SURVIVORSHIP],
                validity_internal=0.6,
                validity_external=0.85,
                precision=0.7,
                cost_estimate=0.6
            ),
            Methodology(
                id="bayesian_inference",
                name="Bayesian Statistical Inference",
                methodology_type=MethodologyType.BAYESIAN,
                description="Updating beliefs based on evidence using probability theory",
                strengths=["Incorporates prior knowledge", "Handles uncertainty", "Sequential updating"],
                weaknesses=["Prior sensitivity", "Computational cost", "Subjectivity in priors"],
                applicable_question_types=[QuestionType.PREDICTIVE, QuestionType.CAUSAL],
                typical_biases=[BiasType.CONFIRMATION],
                validity_internal=0.85,
                validity_external=0.75,
                precision=0.9,
                cost_estimate=0.4
            ),
            Methodology(
                id="ml_discovery",
                name="Machine Learning Discovery",
                methodology_type=MethodologyType.MACHINE_LEARNING,
                description="Data-driven pattern discovery using ML algorithms",
                strengths=["Handles complexity", "Scalable", "Pattern detection"],
                weaknesses=["Black box", "Data hungry", "Overfitting risk"],
                applicable_question_types=[QuestionType.EXPLORATORY, QuestionType.PREDICTIVE],
                typical_biases=[BiasType.SELECTION, BiasType.MEASUREMENT],
                validity_internal=0.7,
                validity_external=0.65,
                precision=0.8,
                cost_estimate=0.5
            ),
            Methodology(
                id="theoretical_derivation",
                name="Theoretical Derivation",
                methodology_type=MethodologyType.THEORETICAL,
                description="Mathematical/logical derivation from first principles",
                strengths=["Rigorous", "General", "No empirical constraints"],
                weaknesses=["Assumptions may not hold", "Needs empirical validation"],
                applicable_question_types=[QuestionType.MECHANISTIC, QuestionType.PREDICTIVE],
                typical_biases=[BiasType.CONFIRMATION],
                validity_internal=0.95,
                validity_external=0.5,
                precision=0.95,
                cost_estimate=0.2
            ),
            Methodology(
                id="meta_analysis",
                name="Meta-Analysis",
                methodology_type=MethodologyType.META_ANALYSIS,
                description="Statistical synthesis of multiple studies",
                strengths=["Increased power", "Addresses heterogeneity", "Comprehensive"],
                weaknesses=["Publication bias", "Heterogeneity", "Garbage in garbage out"],
                applicable_question_types=[QuestionType.CAUSAL, QuestionType.COMPARATIVE],
                typical_biases=[BiasType.PUBLICATION, BiasType.CITATION],
                validity_internal=0.85,
                validity_external=0.8,
                precision=0.9,
                cost_estimate=0.3
            ),
            Methodology(
                id="agent_simulation",
                name="Agent-Based Simulation",
                methodology_type=MethodologyType.COMPUTATIONAL,
                description="Modeling complex systems through interacting agents",
                strengths=["Handles emergence", "What-if scenarios", "Complex dynamics"],
                weaknesses=["Validation difficult", "Parameter sensitivity", "Abstraction"],
                applicable_question_types=[QuestionType.MECHANISTIC, QuestionType.PREDICTIVE],
                typical_biases=[BiasType.CONFIRMATION],
                validity_internal=0.75,
                validity_external=0.6,
                precision=0.7,
                cost_estimate=0.4
            ),
        ]

        for m in methodologies:
            self.methodology_registry[m.id] = m

    def register_methodology(self, methodology: Methodology):
        """Register a new methodology"""
        self.methodology_registry[methodology.id] = methodology

    def _assess_internal_validity(self, methodology: Methodology, question: ScientificQuestion) -> float:
        """Assess internal validity for a given question"""
        base_validity = methodology.validity_internal

        # Adjust based on question type match
        if question.question_type in methodology.applicable_question_types:
            base_validity *= 1.1
        else:
            base_validity *= 0.7

        return min(1.0, base_validity)

    def _assess_external_validity(self, methodology: Methodology, question: ScientificQuestion) -> float:
        """Assess external validity/generalizability"""
        return methodology.validity_external

    def _assess_reliability(self, methodology: Methodology, question: ScientificQuestion) -> float:
        """Assess reliability/reproducibility potential"""
        # Experimental and computational tend to be more reproducible
        reliability_by_type = {
            MethodologyType.EXPERIMENTAL: 0.85,
            MethodologyType.COMPUTATIONAL: 0.95,
            MethodologyType.THEORETICAL: 0.98,
            MethodologyType.OBSERVATIONAL: 0.7,
            MethodologyType.META_ANALYSIS: 0.9,
            MethodologyType.CASE_STUDY: 0.5,
            MethodologyType.BAYESIAN: 0.9,
            MethodologyType.MACHINE_LEARNING: 0.75
        }
        return reliability_by_type.get(methodology.methodology_type, 0.5)

    def _assess_objectivity(self, methodology: Methodology, question: ScientificQuestion) -> float:
        """Assess objectivity - freedom from researcher bias"""
        # More structured methods tend to be more objective
        bias_penalty = len(methodology.typical_biases) * 0.05
        return max(0.0, 0.9 - bias_penalty)

    def _assess_precision(self, methodology: Methodology, question: ScientificQuestion) -> float:
        """Assess measurement precision"""
        return methodology.precision

    def _assess_feasibility(self, methodology: Methodology, question: ScientificQuestion) -> float:
        """Assess practical feasibility"""
        # Inverse of cost estimate
        return 1.0 - methodology.cost_estimate

    def _assess_ethical_considerations(self, methodology: Methodology, question: ScientificQuestion) -> float:
        """Assess ethical appropriateness"""
        # Non-intervention methods generally have fewer ethical concerns
        if methodology.methodology_type in [MethodologyType.OBSERVATIONAL,
                                            MethodologyType.COMPUTATIONAL,
                                            MethodologyType.THEORETICAL]:
            return 0.95
        return 0.7

    def _assess_novelty(self, methodology: Methodology, question: ScientificQuestion) -> float:
        """Assess methodological novelty"""
        # Newer approaches may be more novel
        novelty_by_type = {
            MethodologyType.MACHINE_LEARNING: 0.8,
            MethodologyType.BAYESIAN: 0.7,
            MethodologyType.COMPUTATIONAL: 0.65,
            MethodologyType.META_ANALYSIS: 0.5,
            MethodologyType.EXPERIMENTAL: 0.3,
        }
        return novelty_by_type.get(methodology.methodology_type, 0.4)

    def evaluate_methodology(
        self,
        methodology: Methodology,
        question: ScientificQuestion,
        weights: Optional[Dict[str, float]] = None
    ) -> Dict[str, float]:
        """Comprehensively evaluate a methodology for a question"""
        if weights is None:
            weights = {criterion: 1.0 for criterion in self.evaluation_criteria}

        scores = {}
        for criterion, evaluator in self.evaluation_criteria.items():
            scores[criterion] = evaluator(methodology, question)

        # Calculate weighted overall score
        total_weight = sum(weights.values())
        overall = sum(scores[c] * weights.get(c, 1.0) for c in scores) / total_weight
        scores['overall'] = overall

        return scores

    def recommend_methodology(
        self,
        question: ScientificQuestion,
        constraints: Optional[Dict[str, Any]] = None
    ) -> List[Tuple[Methodology, Dict[str, float]]]:
        """Recommend methodologies for a question"""
        candidates = []

        for methodology in self.methodology_registry.values():
            # Apply constraints
            if constraints:
                if 'max_cost' in constraints and methodology.cost_estimate > constraints['max_cost']:
                    continue
                if 'required_types' in constraints:
                    if methodology.methodology_type not in constraints['required_types']:
                        continue

            scores = self.evaluate_methodology(methodology, question)
            candidates.append((methodology, scores))

        # Sort by overall score
        candidates.sort(key=lambda x: x[1]['overall'], reverse=True)
        return candidates


# =============================================================================
# Question Evaluator
# =============================================================================

class QuestionEvaluator:
    """Evaluates scientific questions for importance, tractability, and novelty"""

    def __init__(self):
        self.question_registry: Dict[str, ScientificQuestion] = {}
        self.domain_knowledge: Dict[str, EpistemicState] = {}

    def register_question(self, question: ScientificQuestion):
        """Register a scientific question"""
        self.question_registry[question.id] = question

    def evaluate_importance(self, question: ScientificQuestion) -> float:
        """Evaluate the importance/impact of answering a question"""
        importance = 0.5

        # Questions with many child questions are more foundational
        importance += len(question.child_questions) * 0.05

        # Causal and mechanistic questions tend to be more impactful
        impact_by_type = {
            QuestionType.CAUSAL: 0.2,
            QuestionType.MECHANISTIC: 0.25,
            QuestionType.PREDICTIVE: 0.15,
            QuestionType.EXPLORATORY: 0.1,
            QuestionType.DESCRIPTIVE: 0.05
        }
        importance += impact_by_type.get(question.question_type, 0.0)

        # Unknown states are more important to resolve
        if question.knowledge_state == KnowledgeState.UNKNOWN:
            importance += 0.15
        elif question.knowledge_state == KnowledgeState.CONTESTED:
            importance += 0.2

        return min(1.0, importance)

    def evaluate_tractability(self, question: ScientificQuestion) -> float:
        """Evaluate how tractable/answerable a question is"""
        tractability = 0.5

        # Questions with established parent questions are more tractable
        tractability += len(question.parent_questions) * 0.03

        # Some question types are more tractable than others
        tractability_by_type = {
            QuestionType.DESCRIPTIVE: 0.25,
            QuestionType.COMPARATIVE: 0.15,
            QuestionType.EXISTENTIAL: 0.1,
            QuestionType.PREDICTIVE: 0.0,
            QuestionType.CAUSAL: -0.1,
            QuestionType.MECHANISTIC: -0.15
        }
        tractability += tractability_by_type.get(question.question_type, 0.0)

        # Knowledge state affects tractability
        if question.knowledge_state == KnowledgeState.EMERGING:
            tractability += 0.1
        elif question.knowledge_state == KnowledgeState.CONTESTED:
            tractability -= 0.1

        return max(0.0, min(1.0, tractability))

    def evaluate_novelty(self, question: ScientificQuestion) -> float:
        """Evaluate how novel/unexplored a question is"""
        novelty = 0.5

        # Unknown states are more novel
        if question.knowledge_state == KnowledgeState.UNKNOWN:
            novelty += 0.3
        elif question.knowledge_state == KnowledgeState.HYPOTHESIZED:
            novelty += 0.2
        elif question.knowledge_state == KnowledgeState.ESTABLISHED:
            novelty -= 0.3
        elif question.knowledge_state == KnowledgeState.PARADIGMATIC:
            novelty -= 0.4

        # Fewer child questions suggests unexplored
        if len(question.child_questions) == 0:
            novelty += 0.1

        return max(0.0, min(1.0, novelty))

    def calculate_priority_score(
        self,
        question: ScientificQuestion,
        weights: Optional[Dict[str, float]] = None
    ) -> float:
        """Calculate overall priority score for a question"""
        if weights is None:
            weights = {'importance': 0.4, 'tractability': 0.35, 'novelty': 0.25}

        importance = self.evaluate_importance(question)
        tractability = self.evaluate_tractability(question)
        novelty = self.evaluate_novelty(question)

        priority = (
            importance * weights.get('importance', 0.4) +
            tractability * weights.get('tractability', 0.35) +
            novelty * weights.get('novelty', 0.25)
        )

        return priority

    def identify_high_value_questions(
        self,
        domain: str,
        top_k: int = 10
    ) -> List[Tuple[ScientificQuestion, float]]:
        """Identify highest value questions in a domain"""
        domain_questions = [
            q for q in self.question_registry.values()
            if q.domain == domain
        ]

        scored = [(q, self.calculate_priority_score(q)) for q in domain_questions]
        scored.sort(key=lambda x: x[1], reverse=True)

        return scored[:top_k]


# =============================================================================
# Knowledge Gap Analyzer
# =============================================================================

class KnowledgeGapAnalyzer:
    """Analyzes and identifies knowledge gaps"""

    def __init__(self):
        self.epistemic_states: Dict[str, EpistemicState] = {}
        self.gap_registry: Dict[str, KnowledgeGap] = {}

    def register_epistemic_state(self, state: EpistemicState):
        """Register an epistemic state for a domain"""
        self.epistemic_states[state.domain] = state

    def identify_gaps(self, domain: str) -> List[KnowledgeGap]:
        """Identify knowledge gaps in a domain"""
        if domain not in self.epistemic_states:
            return []

        state = self.epistemic_states[domain]
        gaps = []

        # Gap from unanswered questions
        for question in state.open_questions:
            if question.knowledge_state in [KnowledgeState.UNKNOWN, KnowledgeState.HYPOTHESIZED]:
                gap = KnowledgeGap(
                    id=f"gap_question_{question.id}",
                    description=f"Unanswered: {question.question_text}",
                    domain=domain,
                    related_questions=[question.id],
                    estimated_difficulty=1.0 - question.tractability_score,
                    estimated_impact=question.importance_score
                )
                gap.priority_score = self._calculate_gap_priority(gap)
                gaps.append(gap)

        # Gap from contested hypotheses
        for hypothesis, evidence_list in state.active_hypotheses.items():
            support = sum(1 for e in evidence_list if e.supports_hypothesis)
            contradict = sum(1 for e in evidence_list if e.contradicts_hypothesis)

            if support > 0 and contradict > 0:
                gap = KnowledgeGap(
                    id=f"gap_contested_{hashlib.md5(hypothesis.encode()).hexdigest()[:8]}",
                    description=f"Contested hypothesis: {hypothesis}",
                    domain=domain,
                    blocking_factors=["Conflicting evidence"],
                    estimated_difficulty=0.7,
                    estimated_impact=0.8
                )
                gap.priority_score = self._calculate_gap_priority(gap)
                gaps.append(gap)

        # Gap from anomalies
        for anomaly in state.anomalies:
            gap = KnowledgeGap(
                id=f"gap_anomaly_{hashlib.md5(anomaly.encode()).hexdigest()[:8]}",
                description=f"Unexplained anomaly: {anomaly}",
                domain=domain,
                blocking_factors=["Paradigm limitations"],
                estimated_difficulty=0.85,
                estimated_impact=0.9
            )
            gap.priority_score = self._calculate_gap_priority(gap)
            gaps.append(gap)

        return gaps

    def _calculate_gap_priority(self, gap: KnowledgeGap) -> float:
        """Calculate priority score for a knowledge gap"""
        # Balance impact and inverse of difficulty
        return gap.estimated_impact * 0.6 + (1.0 - gap.estimated_difficulty) * 0.4

    def suggest_approaches(self, gap: KnowledgeGap) -> List[str]:
        """Suggest approaches to address a knowledge gap"""
        approaches = []

        if gap.estimated_difficulty < 0.5:
            approaches.append("Direct empirical investigation")
            approaches.append("Systematic literature review")
        else:
            approaches.append("Interdisciplinary collaboration")
            approaches.append("Novel methodology development")

        if "Conflicting evidence" in gap.blocking_factors:
            approaches.append("Meta-analysis of existing studies")
            approaches.append("Replication studies with improved controls")

        if "Paradigm limitations" in gap.blocking_factors:
            approaches.append("Theoretical framework extension")
            approaches.append("Cross-domain analogical reasoning")

        return approaches


# =============================================================================
# Experimental Design Generator
# =============================================================================

class ExperimentalDesignGenerator:
    """Generates novel experimental designs"""

    def __init__(self, methodology_evaluator: MethodologyEvaluator):
        self.methodology_evaluator = methodology_evaluator
        self.design_templates: Dict[str, Dict] = self._init_templates()
        self.generated_designs: Dict[str, ExperimentalDesign] = {}

    def _init_templates(self) -> Dict[str, Dict]:
        """Initialize design templates"""
        return {
            'ab_test': {
                'methodology_type': MethodologyType.EXPERIMENTAL,
                'variables': {'independent': 1, 'dependent': 1, 'control': 0},
                'groups': ['control', 'treatment'],
                'randomization': True,
                'blinding': 'double'
            },
            'factorial': {
                'methodology_type': MethodologyType.EXPERIMENTAL,
                'variables': {'independent': 2, 'dependent': 1, 'control': 0},
                'groups': ['2x2'],
                'randomization': True,
                'blinding': 'single'
            },
            'time_series': {
                'methodology_type': MethodologyType.LONGITUDINAL,
                'variables': {'independent': 0, 'dependent': 1, 'time': 1},
                'groups': ['single'],
                'randomization': False,
                'blinding': 'none'
            },
            'cross_validation': {
                'methodology_type': MethodologyType.MACHINE_LEARNING,
                'variables': {'features': 'n', 'target': 1},
                'groups': ['k_folds'],
                'randomization': True,
                'blinding': 'none'
            },
            'bayesian_adaptive': {
                'methodology_type': MethodologyType.BAYESIAN,
                'variables': {'independent': 1, 'dependent': 1},
                'groups': ['adaptive'],
                'randomization': True,
                'blinding': 'single',
                'sequential': True
            }
        }

    def generate_design(
        self,
        question: ScientificQuestion,
        constraints: Optional[Dict[str, Any]] = None
    ) -> ExperimentalDesign:
        """Generate an experimental design for a question"""
        # Get methodology recommendations
        recommendations = self.methodology_evaluator.recommend_methodology(
            question, constraints
        )

        if not recommendations:
            raise ValueError("No suitable methodology found")

        best_methodology, scores = recommendations[0]

        # Select appropriate template
        template = self._select_template(question, best_methodology)

        # Generate design
        design = ExperimentalDesign(
            id=f"design_{question.id}_{best_methodology.id}",
            name=f"{question.question_type.name} study for: {question.question_text[:50]}",
            target_question=question.id,
            methodology=best_methodology,
            variables=self._generate_variables(question, template),
            controls=self._generate_controls(question, template),
            sample_requirements=self._calculate_sample_requirements(question),
            expected_outcomes=self._generate_expected_outcomes(question),
            potential_confounds=self._identify_confounds(question),
            power_analysis=self._conduct_power_analysis(question),
            estimated_validity=scores['overall'],
            novelty_score=self._calculate_design_novelty(question, best_methodology)
        )

        self.generated_designs[design.id] = design
        return design

    def _select_template(
        self,
        question: ScientificQuestion,
        methodology: Methodology
    ) -> Dict:
        """Select best design template"""
        type_to_template = {
            MethodologyType.EXPERIMENTAL: 'ab_test',
            MethodologyType.BAYESIAN: 'bayesian_adaptive',
            MethodologyType.MACHINE_LEARNING: 'cross_validation',
            MethodologyType.LONGITUDINAL: 'time_series'
        }

        template_name = type_to_template.get(
            methodology.methodology_type, 'ab_test'
        )
        return self.design_templates[template_name]

    def _generate_variables(
        self,
        question: ScientificQuestion,
        template: Dict
    ) -> Dict[str, Any]:
        """Generate variable definitions"""
        variables = {
            'independent': question.variables[:1] if question.variables else ['treatment'],
            'dependent': question.variables[1:2] if len(question.variables) > 1 else ['outcome'],
            'control': [],
            'covariates': question.variables[2:] if len(question.variables) > 2 else []
        }
        return variables

    def _generate_controls(
        self,
        question: ScientificQuestion,
        template: Dict
    ) -> List[str]:
        """Generate control conditions"""
        controls = []

        if template.get('randomization'):
            controls.append("Random assignment to conditions")
        if template.get('blinding') == 'double':
            controls.append("Double-blind procedure")
        elif template.get('blinding') == 'single':
            controls.append("Single-blind procedure")

        controls.append("Standardized measurement protocol")
        controls.append("Pre-registration of hypotheses")

        return controls

    def _calculate_sample_requirements(
        self,
        question: ScientificQuestion
    ) -> Dict[str, Any]:
        """Calculate sample size requirements"""
        # Basic power analysis assumptions
        base_n = 100

        # Adjust for question type
        multipliers = {
            QuestionType.CAUSAL: 2.0,
            QuestionType.COMPARATIVE: 1.5,
            QuestionType.PREDICTIVE: 1.8,
            QuestionType.DESCRIPTIVE: 0.5
        }

        multiplier = multipliers.get(question.question_type, 1.0)

        return {
            'minimum_n': int(base_n * multiplier),
            'recommended_n': int(base_n * multiplier * 1.5),
            'power_target': 0.8,
            'alpha': 0.05,
            'expected_effect_size': 'medium'
        }

    def _generate_expected_outcomes(
        self,
        question: ScientificQuestion
    ) -> List[str]:
        """Generate expected outcomes"""
        outcomes = []

        if question.question_type == QuestionType.CAUSAL:
            outcomes.append("Evidence for/against causal relationship")
            outcomes.append("Effect size estimate with confidence interval")
        elif question.question_type == QuestionType.PREDICTIVE:
            outcomes.append("Predictive model with validation metrics")
            outcomes.append("Feature importance rankings")
        elif question.question_type == QuestionType.MECHANISTIC:
            outcomes.append("Process model specification")
            outcomes.append("Intermediate step validation")
        else:
            outcomes.append("Descriptive statistics")
            outcomes.append("Pattern identification")

        return outcomes

    def _identify_confounds(
        self,
        question: ScientificQuestion
    ) -> List[str]:
        """Identify potential confounding variables"""
        confounds = [
            "Selection effects",
            "Temporal confounds",
            "Measurement error",
            "Missing data patterns"
        ]

        if question.domain == "crypto":
            confounds.extend([
                "Market manipulation",
                "Regulatory changes",
                "Exchange-specific effects"
            ])
        elif question.domain == "astro":
            confounds.extend([
                "Instrument calibration",
                "Atmospheric effects",
                "Systematic biases"
            ])

        return confounds

    def _conduct_power_analysis(
        self,
        question: ScientificQuestion
    ) -> Dict[str, float]:
        """Conduct statistical power analysis"""
        return {
            'effect_sizes': {
                'small': 0.2,
                'medium': 0.5,
                'large': 0.8
            },
            'power_small': 0.3,
            'power_medium': 0.8,
            'power_large': 0.99,
            'sample_for_80_power': 64
        }

    def _calculate_design_novelty(
        self,
        question: ScientificQuestion,
        methodology: Methodology
    ) -> float:
        """Calculate novelty of the design"""
        novelty = 0.3

        # Novel methodology types
        if methodology.methodology_type in [
            MethodologyType.BAYESIAN,
            MethodologyType.MACHINE_LEARNING
        ]:
            novelty += 0.3

        # Novel question areas
        if question.knowledge_state == KnowledgeState.UNKNOWN:
            novelty += 0.2

        return min(1.0, novelty)


# =============================================================================
# Evidence Synthesizer
# =============================================================================

class EvidenceSynthesizer:
    """Synthesizes evidence across studies"""

    def __init__(self):
        self.evidence_pool: Dict[str, List[Evidence]] = defaultdict(list)

    def add_evidence(self, hypothesis: str, evidence: Evidence):
        """Add evidence for a hypothesis"""
        self.evidence_pool[hypothesis].append(evidence)

    def synthesize(self, hypothesis: str) -> Dict[str, Any]:
        """Synthesize all evidence for a hypothesis"""
        evidence_list = self.evidence_pool.get(hypothesis, [])

        if not evidence_list:
            return {
                'conclusion': 'insufficient_evidence',
                'confidence': 0.0,
                'evidence_count': 0
            }

        # Count support and contradiction
        supporting = [e for e in evidence_list if e.supports_hypothesis == hypothesis]
        contradicting = [e for e in evidence_list if e.contradicts_hypothesis == hypothesis]

        # Weight by evidence quality
        support_weight = sum(e.quality.value for e in supporting)
        contradict_weight = sum(e.quality.value for e in contradicting)

        total_weight = support_weight + contradict_weight
        if total_weight == 0:
            ratio = 0.5
        else:
            ratio = support_weight / total_weight

        # Calculate overall effect size if available
        effect_sizes = [e.effect_size for e in evidence_list if e.effect_size is not None]
        pooled_effect = np.mean(effect_sizes) if effect_sizes else None

        # Determine conclusion
        if ratio > 0.7 and len(supporting) >= 3:
            conclusion = 'supported'
        elif ratio < 0.3 and len(contradicting) >= 3:
            conclusion = 'contradicted'
        elif len(evidence_list) >= 5:
            conclusion = 'contested'
        else:
            conclusion = 'inconclusive'

        # Calculate confidence based on evidence quality and consistency
        quality_scores = [e.quality.value / 9.0 for e in evidence_list]  # Normalize to 0-1
        avg_quality = np.mean(quality_scores)
        consistency = 1.0 - abs(ratio - 0.5) * 2 if len(evidence_list) > 1 else 0.5
        confidence = avg_quality * (1.0 - consistency * 0.3)

        return {
            'conclusion': conclusion,
            'confidence': confidence,
            'support_ratio': ratio,
            'evidence_count': len(evidence_list),
            'supporting_count': len(supporting),
            'contradicting_count': len(contradicting),
            'pooled_effect_size': pooled_effect,
            'average_quality': avg_quality,
            'replication_rate': sum(1 for e in evidence_list if e.replication_status == 'replicated') / len(evidence_list)
        }

    def identify_biases(self, hypothesis: str) -> Dict[str, float]:
        """Identify potential biases in the evidence base"""
        evidence_list = self.evidence_pool.get(hypothesis, [])

        bias_counts: Dict[BiasType, int] = defaultdict(int)
        for evidence in evidence_list:
            for bias in evidence.potential_biases:
                bias_counts[bias] += 1

        n = len(evidence_list) if evidence_list else 1
        return {bias.name: count / n for bias, count in bias_counts.items()}


# =============================================================================
# Meta-Scientific Reasoner
# =============================================================================

class MetaScientificReasoner:
    """
    Main orchestrator for meta-scientific reasoning.
    Integrates all components for comprehensive scientific methodology analysis.
    """

    def __init__(self):
        self.methodology_evaluator = MethodologyEvaluator()
        self.question_evaluator = QuestionEvaluator()
        self.gap_analyzer = KnowledgeGapAnalyzer()
        self.design_generator = ExperimentalDesignGenerator(self.methodology_evaluator)
        self.evidence_synthesizer = EvidenceSynthesizer()

        logger.info("MetaScientificReasoner initialized")

    def analyze_research_question(
        self,
        question_text: str,
        domain: str,
        question_type: QuestionType,
        variables: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """Comprehensive analysis of a research question"""
        # Create question object
        question = ScientificQuestion(
            id=f"q_{hashlib.md5(question_text.encode()).hexdigest()[:8]}",
            question_text=question_text,
            question_type=question_type,
            domain=domain,
            variables=variables or []
        )

        # Register and evaluate
        self.question_evaluator.register_question(question)

        importance = self.question_evaluator.evaluate_importance(question)
        tractability = self.question_evaluator.evaluate_tractability(question)
        novelty = self.question_evaluator.evaluate_novelty(question)
        priority = self.question_evaluator.calculate_priority_score(question)

        # Get methodology recommendations
        methodology_recs = self.methodology_evaluator.recommend_methodology(question)

        # Generate experimental design
        design = self.design_generator.generate_design(question)

        return {
            'question': question,
            'evaluation': {
                'importance': importance,
                'tractability': tractability,
                'novelty': novelty,
                'priority_score': priority
            },
            'recommended_methodologies': [
                {'methodology': m.name, 'scores': s}
                for m, s in methodology_recs[:3]
            ],
            'experimental_design': design,
            'estimated_resources': design.sample_requirements,
            'potential_challenges': design.potential_confounds
        }

    def evaluate_methodology_fitness(
        self,
        methodology_id: str,
        question_text: str,
        domain: str,
        question_type: QuestionType
    ) -> Dict[str, float]:
        """Evaluate how well a methodology fits a question"""
        question = ScientificQuestion(
            id=f"q_{hashlib.md5(question_text.encode()).hexdigest()[:8]}",
            question_text=question_text,
            question_type=question_type,
            domain=domain
        )

        methodology = self.methodology_evaluator.methodology_registry.get(methodology_id)
        if not methodology:
            raise ValueError(f"Unknown methodology: {methodology_id}")

        return self.methodology_evaluator.evaluate_methodology(methodology, question)

    def synthesize_evidence(
        self,
        hypothesis: str,
        evidence_list: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """Synthesize evidence for a hypothesis"""
        for e_dict in evidence_list:
            evidence = Evidence(
                id=e_dict.get('id', str(hash(frozenset(e_dict.items())))),
                source=e_dict.get('source', 'unknown'),
                methodology_used=e_dict.get('methodology', 'unknown'),
                quality=EvidenceQuality[e_dict.get('quality', 'CASE_REPORT').upper()],
                supports_hypothesis=hypothesis if e_dict.get('supports', False) else None,
                contradicts_hypothesis=hypothesis if e_dict.get('contradicts', False) else None,
                effect_size=e_dict.get('effect_size'),
                sample_size=e_dict.get('sample_size'),
                p_value=e_dict.get('p_value')
            )
            self.evidence_synthesizer.add_evidence(hypothesis, evidence)

        synthesis = self.evidence_synthesizer.synthesize(hypothesis)
        biases = self.evidence_synthesizer.identify_biases(hypothesis)

        return {
            'synthesis': synthesis,
            'potential_biases': biases
        }

    def identify_domain_gaps(self, domain: str) -> List[Dict[str, Any]]:
        """Identify knowledge gaps in a domain"""
        gaps = self.gap_analyzer.identify_gaps(domain)

        return [
            {
                'description': gap.description,
                'priority': gap.priority_score,
                'difficulty': gap.estimated_difficulty,
                'impact': gap.estimated_impact,
                'suggested_approaches': self.gap_analyzer.suggest_approaches(gap)
            }
            for gap in sorted(gaps, key=lambda g: g.priority_score, reverse=True)
        ]

    def generate_research_agenda(
        self,
        domain: str,
        focus_areas: Optional[List[str]] = None,
        constraints: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Generate a research agenda for a domain"""
        # Get high-value questions
        high_value_questions = self.question_evaluator.identify_high_value_questions(
            domain, top_k=10
        )

        # Identify gaps
        gaps = self.knowledge_gap_analyzer.identify_gaps(domain)

        return {
            'high_value_questions': high_value_questions[:5],
            'knowledge_gaps': gaps[:3],
            'research_priority': len(gaps) / 10.0
        }


# Factory functions
def create_meta_scientific_reasoner() -> MetaScientificReasoner:
    """Create a meta-scientific reasoner."""
    return MetaScientificReasoner()


def analyze_scientific_question(question: str, domain: str = "") -> Dict[str, Any]:
    """Analyze a scientific question."""
    reasoner = create_meta_scientific_reasoner()
    return reasoner.analyze_question(question, domain)


def recommend_methodology(question: str, domain: str = "") -> Methodology:
    """Recommend a methodology for a scientific question."""
    reasoner = create_meta_scientific_reasoner()
    analysis = reasoner.analyze_question(question, domain)
    # Simplified - return a default methodology
    return Methodology(
        id="methodology_default",
        name="Experimental Method",
        description="Standard experimental approach",
        type=MethodologyType.EXPERIMENTAL,
        steps=[
            "Formulate hypothesis",
            "Design experiment",
            "Collect data",
            "Analyze results",
            "Draw conclusions"
        ]
    )
