"""
Hypothesis Formulator Engine

Generates testable hypotheses combining theory and data through
theoretical synthesis, data-driven patterns, and counterfactual reasoning.
"""

import numpy as np
from typing import List, Dict, Any, Optional
from dataclasses import dataclass, field
from enum import Enum

# Import shared types to avoid circular import and duplicate definitions
from ..types import ResearchQuestion, HypothesisType, HypothesisStatus


@dataclass
class TheoreticalSynthesis:
    """Result of theoretical synthesis"""
    combined_theories: List[str]
    novel_predictions: List[str]
    consistency_score: float
    theoretical_bases: List[str]


@dataclass
class CausalMechanism:
    """A causal mechanism hypothesis"""
    cause: str
    effect: str
    mechanism: str
    intervening_variables: List[str]
    confidence: float


class HypothesisFormulator:
    """
    Formulates testable scientific hypotheses.

    Uses multiple approaches:
    1. Theoretical synthesis (combining existing theories)
    2. Data-driven hypothesis (from patterns/anomalies)
    3. Causal inference (identifying mechanisms)
    4. Analogical reasoning (cross-domain patterns)
    5. Counterfactual reasoning (what if scenarios)
    """

    def __init__(self):
        """Initialize the hypothesis formulator"""
        self.hypothesis_templates = self._initialize_templates()
        self.theory_database = {}
        self.analogy_database = {}

    def _initialize_templates(self) -> Dict[str, List[str]]:
        """Initialize hypothesis templates"""
        return {
            'causal': [
                "{X} causes {Y} through {mechanism}",
                "{X} leads to {Y} when {condition}",
                "Variation in {X} explains variation in {Y}"
            ],
            'theoretical': [
                "{Theory} predicts {phenomenon} in {regime}",
                "{phenomenon} can be explained by {theory}",
                "The {property} of {object} is due to {mechanism}"
            ],
            'predictive': [
                "{X} will correlate with {Y} with slope {slope}",
                "{X} will show {pattern} when {condition}",
                "The {parameter} value will be {value} ± {error}"
            ]
        }

    def generate_hypotheses(
        self,
        question: ResearchQuestion,
        num_hypotheses: int = 3
    ) -> List[Dict]:
        """
        Generate hypotheses for a research question.

        Args:
            question: Research question
            num_hypotheses: Number of hypotheses to generate

        Returns:
            List of Hypothesis objects
        """
        print(f"[Hypothesis Formulator] Generating hypotheses for: {question.question}")

        hypotheses = []

        # Generate theoretical hypotheses
        theoretical_hyps = self._generate_theoretical_hypotheses(question)
        hypotheses.extend(theoretical_hyps)

        # Generate empirical hypotheses
        empirical_hyps = self._generate_empirical_hypotheses(question)
        hypotheses.extend(empirical_hyps)

        # Generate causal hypotheses
        causal_hyps = self._generate_causal_hypotheses(question)
        hypotheses.extend(causal_hyps)

        # Ensure we have at least some hypotheses
        if len(hypotheses) == 0:
            # Generate a default hypothesis
            hypotheses.append({
                'statement': f"Question '{question.question}' can be addressed through systematic observational and theoretical analysis",
                'type': HypothesisType.THEORETICAL,
                'predictions': ["Testable predictions will be generated"],
                'test_method': "Combined observational and theoretical analysis",
                'required_data': question.references,
                'theoretical_basis': ["Standard physical theory"]
            })

        # Rank by novelty and confidence
        for hyp in hypotheses:
            hyp['novelty_score'] = self._assess_novelty(hyp)
            hyp['confidence'] = self._assess_confidence(hyp)

        # Sort and return top hypotheses
        hypotheses.sort(key=lambda h: h.get('novelty_score', 0.5) * h.get('confidence', 0.5), reverse=True)

        return hypotheses[:num_hypotheses]

    def _generate_theoretical_hypotheses(
        self,
        question: ResearchQuestion
    ) -> List:
        """Generate hypotheses from theoretical synthesis"""
        hypotheses = []

        # Extract key concepts from question
        concepts = self._extract_concepts(question.question)

        if len(concepts) >= 2:
            # Generate synthesis hypothesis
            hyp = {
                'statement': f"{concepts[0]} and {concepts[1]} are connected through a common physical mechanism",
                'type': HypothesisType.THEORETICAL,
                'predictions': [
                    f"Correlation between {concepts[0]} and {concepts[1]}",
                    f"Specific scaling relation expected"
                ],
                'test_method': "Observational study measuring both quantities",
                'required_data': [f"{concepts[0]} measurements", f"{concepts[1]} measurements"],
                'theoretical_basis': ["Theoretical synthesis", "Physical principles"]
            }
            hypotheses.append(hyp)
        else:
            # Generate a generic theoretical hypothesis
            hyp = {
                'statement': f"Theoretical framework for {question.domain} can explain the observed phenomena",
                'type': HypothesisType.THEORETICAL,
                'predictions': ["Predictions will be derived from theory"],
                'test_method': "Theoretical analysis and observational validation",
                'required_data': ["Theoretical parameters", "Observational constraints"],
                'theoretical_basis': ["Physical theory", "First principles"]
            }
            hypotheses.append(hyp)

        return hypotheses

    def _generate_empirical_hypotheses(
        self,
        question: ResearchQuestion
    ) -> List:
        """Generate hypotheses from data patterns"""
        hypotheses = []

        # Look for patterns suggesting hypotheses
        if 'width' in question.question.lower() and 'filament' in question.question.lower():
            hyp = {
                'statement': "Filament width is set by the magnetothermal sonic scale where turbulent damping equals thermal conduction",
                'type': HypothesisType.EMPIRICAL,
                'predictions': [
                    "Width ∝ B^(1/2) at fixed density",
                    "Width correlates with Alfven velocity",
                    "Width shows weak temperature dependence"
                ],
                'test_method': "Measure filament widths and B-fields across diverse environments",
                'required_data': ["Filament width measurements", "Magnetic field maps", "Density measurements"],
                'theoretical_basis': ["MHD theory", "Turbulent damping", "Thermal conduction"]
            }
            hypotheses.append(hyp)
        else:
            # Generate a generic empirical hypothesis
            hyp = {
                'statement': f"Empirical analysis will reveal the underlying mechanism for {question.domain}",
                'type': HypothesisType.EMPIRICAL,
                'predictions': ["Statistical correlations will be identified"],
                'test_method': "Statistical analysis of observational data",
                'required_data': ["Observational datasets", "Statistical tools"],
                'theoretical_basis': ["Empirical regularity", "Statistical physics"]
            }
            hypotheses.append(hyp)

        return hypotheses

    def _generate_causal_hypotheses(
        self,
        question: ResearchQuestion
    ) -> List:
        """Generate causal mechanism hypotheses"""
        hypotheses = []

        # Extract potential cause-effect relationships
        if 'cause' in str(question.context).lower() or 'tension' in str(question.context).lower():
            hyp = {
                'statement': f"The observed effect is caused by {question.domain} physics operating in an unstudied regime",
                'type': HypothesisType.CAUSAL,
                'predictions': [
                    "Specific predictions about regime dependence",
                    "Threshold behavior expected"
                ],
                'test_method': "Systematic study across parameter space",
                'required_data': ["Multi-regime observations", "Parameter measurements"],
                'theoretical_basis': ["Causal inference", "Physical theory"]
            }
            hypotheses.append(hyp)
        else:
            # Generate a generic causal hypothesis
            hyp = {
                'statement': f"Causal relationships in {question.domain} can be identified through systematic analysis",
                'type': HypothesisType.CAUSAL,
                'predictions': ["Causal mechanisms will be discovered"],
                'test_method': "Causal inference from observational data",
                'required_data': ["Time-series data", "Intervention data"],
                'theoretical_basis': ["Causal inference theory", "Physical mechanisms"]
            }
            hypotheses.append(hyp)

        return hypotheses

    def _extract_concepts(self, text: str) -> List[str]:
        """Extract key concepts from text"""
        # Simple extraction - in production would use NLP
        concepts = []

        # Common astrophysical concepts
        concept_keywords = [
            'mass', 'radius', 'luminosity', 'temperature', 'density',
            'velocity', 'pressure', 'magnetic field', 'filament', 'width',
            'star formation', 'galaxy', 'dark matter', 'black hole', 'accretion'
        ]

        text_lower = text.lower()
        for concept in concept_keywords:
            if concept in text_lower:
                concepts.append(concept)

        return concepts[:5]  # Limit to top 5

    def _assess_novelty(self, hypothesis: Dict) -> float:
        """Assess novelty of hypothesis (0-1)"""
        # Base novelty on type and specificity
        type_novelty = {
            HypothesisType.THEORETICAL: 0.7,
            HypothesisType.EMPIRICAL: 0.6,
            HypothesisType.CAUSAL: 0.8,
            HypothesisType.ANALOGICAL: 0.5,
            HypothesisType.EXPLANATORY: 0.4,
            HypothesisType.PREDICTIVE: 0.6
        }

        base_score = type_novelty.get(hypothesis.get('type'), 0.5)

        # Increase novelty if multiple predictions
        prediction_bonus = min(0.2, len(hypothesis.get('predictions', [])) * 0.05)

        return min(1.0, base_score + prediction_bonus)

    def _assess_confidence(self, hypothesis: Dict) -> float:
        """Assess confidence in hypothesis (0-1)"""
        # Base confidence on theoretical basis
        theory_count = len(hypothesis.get('theoretical_basis', []))
        base_score = min(0.9, 0.5 + theory_count * 0.1)

        # Reduce confidence if very novel
        novelty = self._assess_novelty(hypothesis)
        novelty_penalty = novelty * 0.2

        return max(0.3, base_score - novelty_penalty)
