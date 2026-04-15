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
Abductive Inference Engine: Inference to Best Explanation

This module implements abductive reasoning - the process of generating and
evaluating explanatory hypotheses for observed phenomena.

Key Features:
- Hypothesis generation from observations
- Multi-criteria explanation scoring (parsimony, coherence, explanatory power)
- Integration with V36 constraints for consistency checking
- Bayesian scoring for probabilistic ranking

Why This Matters for AGI:
- Enables "why did this happen?" reasoning
- Supports scientific discovery by generating testable hypotheses
- Complements deduction (constraints) and induction (Bayesian learning)

Date: 2025-12-10
Version: 39.0
"""

import numpy as np
from typing import Dict, List, Optional, Any, Callable, Tuple, Set
from dataclasses import dataclass, field
from enum import Enum
from abc import ABC, abstractmethod
import hashlib
import json
from collections import defaultdict


class HypothesisType(Enum):
    """Types of explanatory hypotheses"""
    CAUSAL = "causal"              # X caused Y
    MECHANISTIC = "mechanistic"    # Mechanism M explains Y
    STRUCTURAL = "structural"      # Structure S produces pattern P
    COMPOSITIONAL = "compositional"  # Combination of factors
    ANALOGICAL = "analogical"      # Similar to known case K


class ConfidenceLevel(Enum):
    """Confidence levels for explanations"""
    HIGH = "high"        # > 0.8 confidence
    MEDIUM = "medium"    # 0.5-0.8 confidence
    LOW = "low"          # 0.3-0.5 confidence
    SPECULATIVE = "speculative"  # < 0.3 confidence


@dataclass
class Observation:
    """An observation requiring explanation"""
    observation_id: str
    description: str
    data: Dict[str, Any]
    context: Dict[str, Any] = field(default_factory=dict)
    timestamp: float = 0.0
    source: str = ""

    # For numerical observations
    values: Optional[np.ndarray] = None
    uncertainty: Optional[float] = None

    def to_dict(self) -> Dict:
        return {
            'observation_id': self.observation_id,
            'description': self.description,
            'data': self.data,
            'context': self.context,
            'timestamp': self.timestamp,
            'source': self.source
        }


@dataclass
class Hypothesis:
    """A candidate explanatory hypothesis"""
    hypothesis_id: str
    hypothesis_type: HypothesisType
    statement: str
    mechanism: str
    assumptions: List[str]
    predictions: List[str]

    # Scoring
    prior_probability: float = 0.5
    likelihood_given_evidence: float = 0.5
    complexity: int = 1  # Number of entities/relations involved

    # Metadata
    source: str = "generated"  # 'generated', 'retrieved', 'user'
    supporting_evidence: List[str] = field(default_factory=list)
    contradicting_evidence: List[str] = field(default_factory=list)

    def posterior_probability(self) -> float:
        """Simple Bayesian posterior (unnormalized)"""
        return self.prior_probability * self.likelihood_given_evidence

    def parsimony_score(self) -> float:
        """Parsimony favors simpler hypotheses (Occam's razor)"""
        # Higher complexity -> lower parsimony
        return 1.0 / (1.0 + 0.1 * self.complexity)

    def to_dict(self) -> Dict:
        return {
            'hypothesis_id': self.hypothesis_id,
            'type': self.hypothesis_type.value,
            'statement': self.statement,
            'mechanism': self.mechanism,
            'assumptions': self.assumptions,
            'predictions': self.predictions,
            'prior': self.prior_probability,
            'likelihood': self.likelihood_given_evidence,
            'complexity': self.complexity,
            'supporting_evidence': self.supporting_evidence,
            'contradicting_evidence': self.contradicting_evidence
        }


@dataclass
class Explanation:
    """A ranked explanation with full scoring"""
    hypothesis: Hypothesis
    score: float
    confidence_level: ConfidenceLevel

    # Component scores
    parsimony_score: float
    coherence_score: float
    explanatory_power: float
    prior_alignment: float

    # Validation
    constraint_violations: List[str] = field(default_factory=list)
    is_consistent: bool = True

    def to_dict(self) -> Dict:
        return {
            'hypothesis': self.hypothesis.to_dict(),
            'score': self.score,
            'confidence': self.confidence_level.value,
            'parsimony': self.parsimony_score,
            'coherence': self.coherence_score,
            'explanatory_power': self.explanatory_power,
            'prior_alignment': self.prior_alignment,
            'violations': self.constraint_violations,
            'is_consistent': self.is_consistent
        }


@dataclass
class AbductiveResult:
    """Result of abductive inference"""
    observation: Observation
    explanations: List[Explanation]
    best_explanation: Optional[Explanation]
    alternative_explanations: List[Explanation]

    # Meta-information
    n_hypotheses_generated: int
    n_hypotheses_filtered: int
    generation_method: str

    def to_dict(self) -> Dict:
        return {
            'observation': self.observation.to_dict(),
            'best_explanation': self.best_explanation.to_dict() if self.best_explanation else None,
            'n_alternatives': len(self.alternative_explanations),
            'n_generated': self.n_hypotheses_generated,
            'n_filtered': self.n_hypotheses_filtered,
            'method': self.generation_method
        }


class HypothesisGenerator(ABC):
    """Abstract base for hypothesis generators"""

    @abstractmethod
    def generate(self, observation: Observation,
                 context: Dict[str, Any]) -> List[Hypothesis]:
        """Generate candidate hypotheses for an observation"""
        pass


class CausalHypothesisGenerator(HypothesisGenerator):
    """Generate causal hypotheses: X caused Y"""

    def __init__(self, known_causes: Dict[str, List[str]] = None):
        """
        Args:
            known_causes: Dict mapping effect types to known cause types
        """
        self.known_causes = known_causes or self._default_causes()

    def _default_causes(self) -> Dict[str, List[str]]:
        """Default causal knowledge for astronomical domains"""
        return {
            'temperature_change': [
                'stellar_heating', 'shock_heating', 'cosmic_ray_heating',
                'radiative_cooling', 'adiabatic_expansion'
            ],
            'density_enhancement': [
                'gravitational_collapse', 'shock_compression',
                'turbulent_compression', 'magnetic_pressure'
            ],
            'velocity_gradient': [
                'gravitational_infall', 'outflow', 'rotation',
                'turbulence', 'magnetic_braking'
            ],
            'spectral_line_broadening': [
                'thermal_motion', 'turbulence', 'outflow',
                'rotation', 'opacity_broadening'
            ],
            'flux_variation': [
                'variable_source', 'extinction_change', 'lensing',
                'scintillation', 'instrumental'
            ]
        }

    def generate(self, observation: Observation,
                 context: Dict[str, Any]) -> List[Hypothesis]:
        """Generate causal hypotheses"""
        hypotheses = []

        # Identify observation type
        obs_type = self._classify_observation(observation)

        # Get relevant causes
        potential_causes = self.known_causes.get(obs_type, [])

        for i, cause in enumerate(potential_causes):
            h = Hypothesis(
                hypothesis_id=f"causal_{observation.observation_id}_{i}",
                hypothesis_type=HypothesisType.CAUSAL,
                statement=f"{cause} caused {observation.description}",
                mechanism=self._get_mechanism(cause, obs_type),
                assumptions=self._get_assumptions(cause),
                predictions=self._get_predictions(cause, obs_type),
                prior_probability=self._estimate_prior(cause, context),
                complexity=self._estimate_complexity(cause)
            )
            hypotheses.append(h)

        return hypotheses

    def _classify_observation(self, observation: Observation) -> str:
        """Classify observation into known types"""
        desc_lower = observation.description.lower()

        if any(term in desc_lower for term in ['temperature', 'thermal', 'hot', 'cold']):
            return 'temperature_change'
        elif any(term in desc_lower for term in ['density', 'column', 'mass']):
            return 'density_enhancement'
        elif any(term in desc_lower for term in ['velocity', 'speed', 'motion']):
            return 'velocity_gradient'
        elif any(term in desc_lower for term in ['line', 'spectral', 'width']):
            return 'spectral_line_broadening'
        elif any(term in desc_lower for term in ['flux', 'brightness', 'intensity']):
            return 'flux_variation'
        else:
            return 'unknown'

    def _get_mechanism(self, cause: str, obs_type: str) -> str:
        """Get mechanistic description of cause"""
        mechanisms = {
            'stellar_heating': 'UV/X-ray radiation from nearby stars heats gas',
            'shock_heating': 'Supersonic shock waves compress and heat gas',
            'gravitational_collapse': 'Self-gravity causes density increase',
            'turbulent_compression': 'Turbulent motions create local overdensities',
            'outflow': 'Material ejected from central source creates velocity gradient'
        }
        return mechanisms.get(cause, f'{cause} operates via standard physical processes')

    def _get_assumptions(self, cause: str) -> List[str]:
        """Get assumptions required for this cause"""
        assumptions = {
            'stellar_heating': ['nearby_star_present', 'gas_optically_thin'],
            'shock_heating': ['supersonic_motion', 'dissipation_mechanism'],
            'gravitational_collapse': ['jeans_unstable', 'no_support_mechanism'],
            'turbulent_compression': ['turbulent_flow', 'mach_number_sufficient']
        }
        return assumptions.get(cause, ['standard_physics'])

    def _get_predictions(self, cause: str, obs_type: str) -> List[str]:
        """Get testable predictions from this hypothesis"""
        predictions = {
            'stellar_heating': [
                'temperature_gradient_toward_star',
                'ionization_state_increase_toward_star'
            ],
            'shock_heating': [
                'velocity_jump_at_shock_front',
                'compression_ratio_3_to_4'
            ],
            'gravitational_collapse': [
                'infall_velocity_signature',
                'density_profile_r_minus_2'
            ]
        }
        return predictions.get(cause, [f'observable_consistent_with_{cause}'])

    def _estimate_prior(self, cause: str, context: Dict[str, Any]) -> float:
        """Estimate prior probability based on context"""
        # Default prior
        prior = 0.5

        # Adjust based on context
        if 'environment' in context:
            env = context['environment']
            if env == 'star_forming_region' and cause in ['stellar_heating', 'gravitational_collapse']:
                prior *= 1.5
            elif env == 'diffuse_ism' and cause == 'stellar_heating':
                prior *= 0.7

        return min(0.95, max(0.05, prior))

    def _estimate_complexity(self, cause: str) -> int:
        """Estimate complexity of the causal mechanism"""
        complexity = {
            'stellar_heating': 2,  # Star + radiation
            'shock_heating': 3,    # Shock + motion + heating
            'gravitational_collapse': 2,  # Gravity + mass
            'turbulent_compression': 4,   # Turbulence is complex
            'outflow': 3
        }
        return complexity.get(cause, 2)


class MechanisticHypothesisGenerator(HypothesisGenerator):
    """Generate mechanistic hypotheses based on known physics"""

    def __init__(self):
        self.mechanisms = self._build_mechanism_library()

    def _build_mechanism_library(self) -> Dict[str, Dict]:
        """Build library of known mechanisms"""
        return {
            'radiative_transfer': {
                'description': 'Radiation propagation through medium',
                'parameters': ['opacity', 'source_function', 'geometry'],
                'predictions': ['spectral_line_profiles', 'continuum_shape']
            },
            'gravitational_lensing': {
                'description': 'Light bending by massive objects',
                'parameters': ['mass', 'distance', 'alignment'],
                'predictions': ['image_positions', 'magnification', 'time_delays']
            },
            'mhd_turbulence': {
                'description': 'Magneto-hydrodynamic turbulent cascade',
                'parameters': ['magnetic_field', 'velocity_dispersion', 'scale'],
                'predictions': ['structure_functions', 'power_spectrum']
            },
            'chemical_evolution': {
                'description': 'Time-dependent chemical abundances',
                'parameters': ['density', 'temperature', 'uv_field', 'cosmic_rays'],
                'predictions': ['abundance_ratios', 'depletion_patterns']
            }
        }

    def generate(self, observation: Observation,
                 context: Dict[str, Any]) -> List[Hypothesis]:
        """Generate mechanistic hypotheses"""
        hypotheses = []

        for mech_name, mech_info in self.mechanisms.items():
            if self._mechanism_relevant(mech_name, observation, context):
                h = Hypothesis(
                    hypothesis_id=f"mech_{observation.observation_id}_{mech_name}",
                    hypothesis_type=HypothesisType.MECHANISTIC,
                    statement=f"{mech_info['description']} explains {observation.description}",
                    mechanism=mech_name,
                    assumptions=[f"parameter_{p}_within_range" for p in mech_info['parameters']],
                    predictions=mech_info['predictions'],
                    prior_probability=0.5,
                    complexity=len(mech_info['parameters'])
                )
                hypotheses.append(h)

        return hypotheses

    def _mechanism_relevant(self, mechanism: str, observation: Observation,
                           context: Dict[str, Any]) -> bool:
        """Check if mechanism is relevant to observation"""
        desc_lower = observation.description.lower()

        relevance = {
            'radiative_transfer': any(t in desc_lower for t in ['spectrum', 'line', 'emission', 'absorption']),
            'gravitational_lensing': any(t in desc_lower for t in ['lens', 'arc', 'einstein', 'multiple image']),
            'mhd_turbulence': any(t in desc_lower for t in ['turbulence', 'velocity dispersion', 'structure']),
            'chemical_evolution': any(t in desc_lower for t in ['abundance', 'molecule', 'ion', 'chemical'])
        }

        return relevance.get(mechanism, False)


class AnalogicalHypothesisGenerator(HypothesisGenerator):
    """Generate hypotheses by analogy to known cases"""

    def __init__(self, case_library: List[Dict] = None):
        self.case_library = case_library or []

    def add_case(self, case: Dict):
        """Add a case to the library"""
        self.case_library.append(case)

    def generate(self, observation: Observation,
                 context: Dict[str, Any]) -> List[Hypothesis]:
        """Generate analogical hypotheses"""
        hypotheses = []

        # Find similar cases
        similar_cases = self._find_similar_cases(observation)

        for i, (case, similarity) in enumerate(similar_cases[:3]):  # Top 3
            h = Hypothesis(
                hypothesis_id=f"analog_{observation.observation_id}_{i}",
                hypothesis_type=HypothesisType.ANALOGICAL,
                statement=f"This is analogous to {case['name']}",
                mechanism=f"Same mechanism as {case['name']}: {case.get('mechanism', 'unknown')}",
                assumptions=[f"analogy_holds_for_{assumption}" for assumption in case.get('assumptions', [])],
                predictions=[f"similar_to_{case['name']}_{pred}" for pred in case.get('predictions', [])],
                prior_probability=similarity * 0.8,  # Scale by similarity
                complexity=case.get('complexity', 2)
            )
            hypotheses.append(h)

        return hypotheses

    def _find_similar_cases(self, observation: Observation) -> List[Tuple[Dict, float]]:
        """Find similar cases in library"""
        similarities = []

        obs_features = self._extract_features(observation)

        for case in self.case_library:
            case_features = case.get('features', {})
            similarity = self._compute_similarity(obs_features, case_features)
            if similarity > 0.3:  # Minimum threshold
                similarities.append((case, similarity))

        # Sort by similarity (descending)
        similarities.sort(key=lambda x: x[1], reverse=True)
        return similarities

    def _extract_features(self, observation: Observation) -> Dict[str, Any]:
        """Extract features from observation for matching"""
        return {
            'type': self._classify_type(observation),
            'scale': observation.data.get('scale', 'unknown'),
            'domain': observation.context.get('domain', 'unknown')
        }

    def _classify_type(self, observation: Observation) -> str:
        """Classify observation type"""
        desc_lower = observation.description.lower()
        if 'spectrum' in desc_lower:
            return 'spectroscopic'
        elif 'image' in desc_lower:
            return 'imaging'
        elif 'variability' in desc_lower:
            return 'time_series'
        else:
            return 'general'

    def _compute_similarity(self, features1: Dict, features2: Dict) -> float:
        """Compute similarity between feature sets"""
        if not features1 or not features2:
            return 0.0

        matches = sum(1 for k in features1 if features1.get(k) == features2.get(k))
        total = len(set(features1.keys()) | set(features2.keys()))

        return matches / total if total > 0 else 0.0


class ExplanationScorer:
    """Score and rank explanations"""

    def __init__(self, weights: Dict[str, float] = None):
        """
        Args:
            weights: Weights for scoring components
        """
        self.weights = weights or {
            'parsimony': 0.2,
            'coherence': 0.25,
            'explanatory_power': 0.3,
            'prior_alignment': 0.25
        }

    def score(self, hypothesis: Hypothesis, observation: Observation,
              background_knowledge: Dict[str, Any] = None) -> Explanation:
        """Score a hypothesis as an explanation"""

        # Component scores
        parsimony = hypothesis.parsimony_score()
        coherence = self._compute_coherence(hypothesis, background_knowledge or {})
        explanatory_power = self._compute_explanatory_power(hypothesis, observation)
        prior_alignment = self._compute_prior_alignment(hypothesis, background_knowledge or {})

        # Weighted combination
        total_score = (
            self.weights['parsimony'] * parsimony +
            self.weights['coherence'] * coherence +
            self.weights['explanatory_power'] * explanatory_power +
            self.weights['prior_alignment'] * prior_alignment
        )

        # Determine confidence level
        if total_score > 0.8:
            confidence = ConfidenceLevel.HIGH
        elif total_score > 0.5:
            confidence = ConfidenceLevel.MEDIUM
        elif total_score > 0.3:
            confidence = ConfidenceLevel.LOW
        else:
            confidence = ConfidenceLevel.SPECULATIVE

        return Explanation(
            hypothesis=hypothesis,
            score=total_score,
            confidence_level=confidence,
            parsimony_score=parsimony,
            coherence_score=coherence,
            explanatory_power=explanatory_power,
            prior_alignment=prior_alignment
        )

    def _compute_coherence(self, hypothesis: Hypothesis,
                          background: Dict[str, Any]) -> float:
        """Compute coherence with background knowledge"""
        # Check assumptions against background
        coherence = 1.0

        for assumption in hypothesis.assumptions:
            if assumption in background.get('violated_assumptions', []):
                coherence -= 0.2
            elif assumption in background.get('supported_assumptions', []):
                coherence += 0.1

        return max(0.0, min(1.0, coherence))

    def _compute_explanatory_power(self, hypothesis: Hypothesis,
                                   observation: Observation) -> float:
        """Compute how well hypothesis explains observation"""
        # Based on how many aspects of observation are addressed
        base_power = 0.5

        # More predictions = higher explanatory scope
        prediction_bonus = min(0.3, len(hypothesis.predictions) * 0.05)

        # Supporting evidence increases power
        evidence_bonus = min(0.2, len(hypothesis.supporting_evidence) * 0.05)

        # Contradicting evidence decreases power
        contradiction_penalty = min(0.3, len(hypothesis.contradicting_evidence) * 0.1)

        return max(0.0, min(1.0, base_power + prediction_bonus + evidence_bonus - contradiction_penalty))

    def _compute_prior_alignment(self, hypothesis: Hypothesis,
                                 background: Dict[str, Any]) -> float:
        """Compute alignment with prior expectations"""
        # Start with hypothesis's own prior
        alignment = hypothesis.prior_probability

        # Adjust based on domain-specific priors in background
        domain_priors = background.get('domain_priors', {})
        if hypothesis.mechanism in domain_priors:
            alignment = (alignment + domain_priors[hypothesis.mechanism]) / 2

        return alignment


class AbductiveInferenceEngine:
    """
    Main Abductive Inference Engine.

    Orchestrates hypothesis generation, scoring, and selection
    to provide inference to best explanation.
    """

    def __init__(self, constraint_checker: Callable = None):
        """
        Args:
            constraint_checker: Optional function to check V36 constraints
        """
        # Hypothesis generators
        self.generators: List[HypothesisGenerator] = [
            CausalHypothesisGenerator(),
            MechanisticHypothesisGenerator(),
            AnalogicalHypothesisGenerator()
        ]

        # Explanation scorer
        self.scorer = ExplanationScorer()

        # V36 integration
        self.constraint_checker = constraint_checker

        # Cache
        self.explanation_cache: Dict[str, AbductiveResult] = {}

    def add_generator(self, generator: HypothesisGenerator):
        """Add a hypothesis generator"""
        self.generators.append(generator)

    def add_known_case(self, case: Dict):
        """Add a known case for analogical reasoning"""
        for gen in self.generators:
            if isinstance(gen, AnalogicalHypothesisGenerator):
                gen.add_case(case)

    def explain(self, observation: Observation,
                context: Dict[str, Any] = None,
                background_knowledge: Dict[str, Any] = None,
                max_hypotheses: int = 10) -> AbductiveResult:
        """
        Generate and rank explanations for an observation.

        Args:
            observation: The observation to explain
            context: Additional context for generation
            background_knowledge: Domain knowledge for scoring
            max_hypotheses: Maximum hypotheses to consider

        Returns:
            AbductiveResult with ranked explanations
        """
        context = context or {}
        background_knowledge = background_knowledge or {}

        # Check cache
        cache_key = self._cache_key(observation)
        if cache_key in self.explanation_cache:
            return self.explanation_cache[cache_key]  # Return cached explanation
