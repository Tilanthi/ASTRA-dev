"""
Hypothesis Generation & Testing Engine for STAN V40

Implements iterative hypothesis refinement:
1. Generate multiple hypotheses
2. Design mental experiments to distinguish
3. Evaluate evidence for/against each
4. Refine or eliminate hypotheses
5. Repeat until convergence

Target: +10-15% on causal/comparative reasoning

Date: 2025-12-11
Version: 40.0
"""

import re
import math
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Any, Tuple, Set, Callable
from enum import Enum
from abc import ABC, abstractmethod
import random


class HypothesisStatus(Enum):
    """Status of a hypothesis"""
    ACTIVE = "active"           # Under consideration
    SUPPORTED = "supported"     # Strong evidence for
    WEAKENED = "weakened"       # Evidence against
    ELIMINATED = "eliminated"   # Ruled out
    CONFIRMED = "confirmed"     # Accepted as answer


class EvidenceType(Enum):
    """Types of evidence"""
    SUPPORTING = "supporting"   # Supports hypothesis
    CONTRADICTING = "contradicting"  # Contradicts hypothesis
    NEUTRAL = "neutral"         # Neither supports nor contradicts
    DISCRIMINATING = "discriminating"  # Distinguishes between hypotheses


@dataclass
class Evidence:
    """A piece of evidence"""
    description: str
    evidence_type: EvidenceType
    strength: float  # 0.0 to 1.0
    source: str = ""  # Where evidence came from
    applies_to: List[str] = field(default_factory=list)  # Hypothesis IDs

    def to_dict(self) -> Dict:
        return {
            'description': self.description,
            'type': self.evidence_type.value,
            'strength': self.strength,
            'source': self.source
        }


@dataclass
class Hypothesis:
    """A hypothesis about the answer"""
    id: str
    statement: str
    explanation: str = ""

    # Probability and status
    prior_probability: float = 0.5
    posterior_probability: float = 0.5
    status: HypothesisStatus = HypothesisStatus.ACTIVE

    # Evidence tracking
    supporting_evidence: List[Evidence] = field(default_factory=list)
    contradicting_evidence: List[Evidence] = field(default_factory=list)

    # Metadata
    source: str = ""  # How hypothesis was generated
    confidence: float = 0.5
    reasoning_trace: List[str] = field(default_factory=list)

    def add_evidence(self, evidence: Evidence) -> None:
        """Add evidence and update probability"""
        if evidence.evidence_type == EvidenceType.SUPPORTING:
            self.supporting_evidence.append(evidence)
            self._update_probability(evidence.strength, is_supporting=True)
        elif evidence.evidence_type == EvidenceType.CONTRADICTING:
            self.contradicting_evidence.append(evidence)
            self._update_probability(evidence.strength, is_supporting=False)

    def _update_probability(self, evidence_strength: float,
                           is_supporting: bool) -> None:
        """Bayesian update of probability"""
        # Likelihood ratio based on evidence strength
        if is_supporting:
            likelihood_ratio = 1.0 + evidence_strength * 2
        else:
            likelihood_ratio = 1.0 / (1.0 + evidence_strength * 2)

        # Bayesian update
        prior_odds = self.posterior_probability / (1 - self.posterior_probability + 1e-10)
        posterior_odds = prior_odds * likelihood_ratio
        self.posterior_probability = posterior_odds / (1 + posterior_odds)

        # Update status
        if self.posterior_probability > 0.8:
            self.status = HypothesisStatus.SUPPORTED
        elif self.posterior_probability < 0.2:
            self.status = HypothesisStatus.WEAKENED
        elif self.posterior_probability < 0.05:
            self.status = HypothesisStatus.ELIMINATED

    def to_dict(self) -> Dict:
        return {
            'id': self.id,
            'statement': self.statement,
            'probability': self.posterior_probability,
            'status': self.status.value,
            'supporting_count': len(self.supporting_evidence),
            'contradicting_count': len(self.contradicting_evidence)
        }


@dataclass
class MentalExperiment:
    """A mental experiment to test hypotheses"""
    description: str
    target_hypotheses: List[str]  # Hypothesis IDs to discriminate

    # Expected outcomes
    outcomes: Dict[str, Dict[str, float]]  # outcome -> {hyp_id: probability}

    # Results
    executed: bool = False
    result: Optional[str] = None
    evidence_generated: List[Evidence] = field(default_factory=list)

    def expected_information_gain(self) -> float:
        """Calculate expected information gain from this experiment"""
        if not self.outcomes:
            return 0.0

        total_gain = 0.0
        for outcome, probs in self.outcomes.items():
            # Entropy reduction
            p_outcome = sum(probs.values()) / len(probs)
            if p_outcome > 0:
                # Information gain = reduction in uncertainty
                gain = sum(p * math.log2(1/p + 1e-10) for p in probs.values() if p > 0)
                total_gain += p_outcome * gain

        return total_gain


@dataclass
class HypothesisTest:
    """A test applied to hypotheses"""
    name: str
    test_type: str  # consistency, plausibility, evidence
    hypotheses_tested: List[str]
    results: Dict[str, bool]  # hypothesis_id -> passed
    reasoning: str = ""


class HypothesisGenerator(ABC):
    """Base class for hypothesis generators"""

    @abstractmethod
    def generate(self, problem: str, context: Dict) -> List[Hypothesis]:
        """Generate hypotheses for a problem"""
        pass


class DirectAnswerGenerator(HypothesisGenerator):
    """Generate hypotheses from direct answer patterns"""

    def generate(self, problem: str, context: Dict) -> List[Hypothesis]:
        hypotheses = []
        p_lower = problem.lower()

        # Multiple choice extraction
        mc_pattern = r'([A-G])\)\s*([^A-G\n]+)'
        matches = re.findall(mc_pattern, problem)

        for i, (letter, text) in enumerate(matches):
            hypotheses.append(Hypothesis(
                id=f"mc_{letter}",
                statement=f"The answer is {letter}",
                explanation=text.strip()[:200],
                prior_probability=1.0 / len(matches) if matches else 0.25,
                source="multiple_choice_extraction"
            ))

        # Yes/No question
        if 'is it' in p_lower or 'does' in p_lower or 'can' in p_lower:
            hypotheses.extend([
                Hypothesis(
                    id="yes",
                    statement="Yes",
                    prior_probability=0.5,
                    source="yes_no_pattern"
                ),
                Hypothesis(
                    id="no",
                    statement="No",
                    prior_probability=0.5,
                    source="yes_no_pattern"
                )
            ])

        return hypotheses


class AnalogicalGenerator(HypothesisGenerator):
    """Generate hypotheses from analogical reasoning"""

    def __init__(self, knowledge_base: Dict[str, Any] = None):
        self.knowledge_base = knowledge_base or {}

    def generate(self, problem: str, context: Dict) -> List[Hypothesis]:
        hypotheses = []

        # Look for similar problems in context
        similar_problems = context.get('similar_problems', [])

        for i, similar in enumerate(similar_problems[:3]):
            if similar.get('answer'):
                hypotheses.append(Hypothesis(
                    id=f"analogical_{i}",
                    statement=similar['answer'],
                    explanation=f"By analogy with: {similar.get('problem', '')[:100]}",
                    prior_probability=similar.get('similarity', 0.5),
                    source="analogical_reasoning"
                ))

        return hypotheses


class DeductiveGenerator(HypothesisGenerator):
    """Generate hypotheses through deductive reasoning"""

    def generate(self, problem: str, context: Dict) -> List[Hypothesis]:
        hypotheses = []

        # Extract constraints and deduce possible answers
        constraints = context.get('constraints', [])
        domain = context.get('domain', {})

        # If numeric constraints exist
        numeric_matches = re.findall(r'(\d+\.?\d*)', problem)
        if numeric_matches:
            # Generate hypotheses around found numbers
            for num_str in numeric_matches[:2]:
                num = float(num_str)
                hypotheses.append(Hypothesis(
                    id=f"numeric_{num_str}",
                    statement=str(num),
                    prior_probability=0.3,
                    source="numeric_extraction"
                ))

        return hypotheses


class HypothesisEngine:
    """
    Main hypothesis generation and testing engine.

    Implements iterative refinement:
    1. Generate initial hypotheses
    2. Design tests to discriminate
    3. Execute tests and gather evidence
    4. Update probabilities
    5. Eliminate unlikely hypotheses
    6. Repeat until convergence or budget exhausted
    """

    def __init__(self, max_iterations: int = 5,
                 convergence_threshold: float = 0.9):
        self.max_iterations = max_iterations
        self.convergence_threshold = convergence_threshold

        # Generators
        self.generators: List[HypothesisGenerator] = [
            DirectAnswerGenerator(),
            AnalogicalGenerator(),
            DeductiveGenerator(),
        ]

        # Statistics
        self.hypotheses_generated = 0
        self.tests_executed = 0
        self.convergences = 0

    def generate_hypotheses(self, problem: str,
                           context: Dict = None) -> List[Hypothesis]:
        """Generate hypotheses for the given problem."""
        if context is None:
            context = {}
        return []
