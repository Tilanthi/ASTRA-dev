"""
Abductive Inference Engine for STAN V39

Implements inference to the best explanation (IBE) - generating and ranking
explanatory hypotheses for observed phenomena.

Core capabilities:
- Hypothesis generation from unexpected observations
- Multi-criteria explanation scoring (parsimony, coherence, explanatory power)
- Integration with Bayesian priors and symbolic constraints
- Iterative refinement of explanations

Date: 2025-12-10
Version: 39.0
"""

import numpy as np
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Any, Tuple, Callable, Set
from enum import Enum
from abc import ABC, abstractmethod
import json
import hashlib
from collections import defaultdict


class HypothesisType(Enum):
    """Types of explanatory hypotheses"""
    CAUSAL = "causal"                    # X caused Y
    MECHANISTIC = "mechanistic"          # How X produces Y
    STRUCTURAL = "structural"            # Hidden structure explains pattern
    COMPOSITIONAL = "compositional"      # Mixture of factors
    COUNTERFACTUAL = "counterfactual"    # What would have happened
    ANALOGICAL = "analogical"            # Similar to known case


class ExplanationQuality(Enum):
    """Quality levels for explanations"""
    EXCELLENT = "excellent"      # Score > 0.8
    GOOD = "good"                # Score 0.6-0.8
    MODERATE = "moderate"        # Score 0.4-0.6
    WEAK = "weak"                # Score 0.2-0.4
    POOR = "poor"                # Score < 0.2


@dataclass
class Observation:
    """An observed phenomenon requiring explanation"""
    observation_id: str
    description: str
    data: Dict[str, Any]
    context: Dict[str, Any] = field(default_factory=dict)
    timestamp: float = 0.0
    surprise_level: float = 0.0  # How unexpected (0-1)
    domain: str = "unknown"

    def to_dict(self) -> Dict:
        return {
            'observation_id': self.observation_id,
            'description': self.description,
            'data': self.data,
            'context': self.context,
            'surprise_level': self.surprise_level,
            'domain': self.domain
        }


@dataclass
class Hypothesis:
    """An explanatory hypothesis"""
    hypothesis_id: str
    hypothesis_type: HypothesisType
    description: str
    explains: List[str]  # observation_ids this explains
    assumptions: List[str]
    predictions: List[Dict[str, Any]]  # Testable predictions
    mechanism: Optional[str] = None
    parent_hypotheses: List[str] = field(default_factory=list)  # For refinement tracking
    confidence: float = 0.5

    # Scoring components
    parsimony_score: float = 0.5
    coherence_score: float = 0.5
    explanatory_power: float = 0.5
    predictive_accuracy: float = 0.5

    metadata: Dict[str, Any] = field(default_factory=dict)

    def overall_score(self, weights: Dict[str, float] = None) -> float:
        """Compute weighted overall score"""
        if weights is None:
            weights = {
                'parsimony': 0.2,
                'coherence': 0.3,
                'explanatory_power': 0.3,
                'predictive_accuracy': 0.2
            }

        return (
            weights.get('parsimony', 0.2) * self.parsimony_score +
            weights.get('coherence', 0.3) * self.coherence_score +
            weights.get('explanatory_power', 0.3) * self.explanatory_power +
            weights.get('predictive_accuracy', 0.2) * self.predictive_accuracy
        )

    def quality_level(self) -> ExplanationQuality:
        """Get qualitative quality level"""
        score = self.overall_score()
        if score > 0.8:
            return ExplanationQuality.EXCELLENT
        elif score > 0.6:
            return ExplanationQuality.GOOD
        elif score > 0.4:
            return ExplanationQuality.MODERATE
        elif score > 0.2:
            return ExplanationQuality.WEAK
        else:
            return ExplanationQuality.POOR

    def to_dict(self) -> Dict:
        return {
            'hypothesis_id': self.hypothesis_id,
            'type': self.hypothesis_type.value,
            'description': self.description,
            'explains': self.explains,
            'assumptions': self.assumptions,
            'predictions': self.predictions,
            'mechanism': self.mechanism,
            'scores': {
                'parsimony': self.parsimony_score,
                'coherence': self.coherence_score,
                'explanatory_power': self.explanatory_power,
                'predictive_accuracy': self.predictive_accuracy,
                'overall': self.overall_score()
            },
            'quality': self.quality_level().value,
            'confidence': self.confidence
        }


@dataclass
class Evidence:
    """Evidence for or against a hypothesis"""
    evidence_id: str
    hypothesis_id: str
    evidence_type: str  # 'supports', 'contradicts', 'neutral'
    strength: float  # 0-1
    description: str
    data: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict:
        return {
            'evidence_id': self.evidence_id,
            'hypothesis_id': self.hypothesis_id,
            'type': self.evidence_type,
            'strength': self.strength,
            'description': self.description
        }


class HypothesisGenerator(ABC):
    """Abstract base class for hypothesis generators"""

    @abstractmethod
    def generate(self, observation: Observation,
                 context: Dict[str, Any]) -> List[Hypothesis]:
        """Generate hypotheses for an observation"""
        pass


class CausalHypothesisGenerator(HypothesisGenerator):
    """Generates causal hypotheses based on known causal patterns"""

    def __init__(self, causal_templates: List[Dict] = None):
        self.causal_templates = causal_templates or self._default_templates()
        self.hypothesis_counter = 0

    def _default_templates(self) -> List[Dict]:
        """Default causal templates from T_U'"""
        return [
            {
                'name': 'direct_cause',
                'pattern': 'X directly causes Y',
                'assumptions': ['temporal_precedence', 'no_confounding'],
                'mechanism': 'X → Y'
            },
            {
                'name': 'mediated_cause',
                'pattern': 'X causes Y through mediator M',
                'assumptions': ['temporal_order', 'mediator_on_path'],
                'mechanism': 'X → M → Y'
            },
            {
                'name': 'common_cause',
                'pattern': 'Hidden Z causes both X and Y',
                'assumptions': ['latent_confounder'],
                'mechanism': 'X ← Z → Y'
            },
            {
                'name': 'feedback_loop',
                'pattern': 'X and Y mutually influence with delay',
                'assumptions': ['delayed_feedback', 'stability'],
                'mechanism': 'X ⇄ Y (delayed)'
            },
            {
                'name': 'regime_dependent',
                'pattern': 'Causal relationship changes across regimes',
                'assumptions': ['regime_existence', 'regime_distinguishable'],
                'mechanism': 'X →[R] Y'
            },
            {
                'name': 'threshold_effect',
                'pattern': 'X causes Y only above threshold',
                'assumptions': ['threshold_exists', 'monotonic_above_threshold'],
                'mechanism': 'X →[>θ] Y'
            }
        ]

    def generate(self, observation: Observation,
                 context: Dict[str, Any]) -> List[Hypothesis]:
        """Generate causal hypotheses for observation"""
        hypotheses = []

        # Extract variables from observation
        variables = self._extract_variables(observation)

        for template in self.causal_templates:
            # Check if template is applicable
            if self._template_applicable(template, observation, context):
                hypothesis = self._instantiate_template(
                    template, observation, variables, context
                )
                if hypothesis:
                    hypotheses.append(hypothesis)

        return hypotheses

    def _extract_variables(self, observation: Observation) -> List[str]:
        """Extract variable names from observation"""
        variables = []
        if 'variables' in observation.data:
            variables = list(observation.data['variables'].keys())
        elif 'time_series' in observation.data:
            variables = list(observation.data['time_series'].keys())
        return variables

    def _template_applicable(self, template: Dict,
                            observation: Observation,
                            context: Dict) -> bool:
        """Check if template can explain observation"""
        # Simple heuristic checks
        template_name = template['name']

        if template_name == 'feedback_loop':
            # Need at least 2 variables with correlation
            return len(self._extract_variables(observation)) >= 2

        if template_name == 'regime_dependent':
            # Need evidence of regime changes
            return observation.data.get('has_regime_changes', False)

        return True  # Default: try all templates

    def _instantiate_template(self, template: Dict,
                              observation: Observation,
                              variables: List[str],
                              context: Dict) -> Optional[Hypothesis]:
        """Create hypothesis from template"""
        self.hypothesis_counter += 1

        # Generate predictions based on template
        predictions = self._generate_predictions(template, variables)

        return Hypothesis(
            hypothesis_id=f"H_causal_{self.hypothesis_counter}",
            hypothesis_type=HypothesisType.CAUSAL,
            description=f"{template['pattern']} (variables: {', '.join(variables[:3])})",
            explains=[observation.observation_id],
            assumptions=template['assumptions'],
            predictions=predictions,
            mechanism=template['mechanism'],
            parsimony_score=self._compute_parsimony(template),
            metadata={'template': template['name']}
        )

    def _generate_predictions(self, template: Dict,
                             variables: List[str]) -> List[Dict]:
        """Generate testable predictions from template"""
        predictions = []

        template_name = template['name']

        if template_name == 'direct_cause' and len(variables) >= 2:
            predictions.append({
                'prediction': f'Intervening on {variables[0]} changes {variables[1]}',
                'test_type': 'intervention',
                'expected_direction': 'positive_correlation'
            })

        if template_name == 'common_cause' and len(variables) >= 2:
            predictions.append({
                'prediction': f'Conditioning on latent removes {variables[0]}-{variables[1]} correlation',
                'test_type': 'conditional_independence',
                'expected_result': 'independence'
            })

        if template_name == 'feedback_loop':
            predictions.append({
                'prediction': 'Lagged cross-correlation should be bidirectional',
                'test_type': 'granger_causality',
                'expected_result': 'bidirectional'
            })

        return predictions

    def _compute_parsimony(self, template: Dict) -> float:
        """Compute parsimony score (simpler = higher)"""
        n_assumptions = len(template.get('assumptions', []))
        mechanism = template.get('mechanism', '')
        n_arrows = mechanism.count('→') + mechanism.count('←') + mechanism.count('⇄')

        # Simpler mechanisms score higher
        complexity = n_assumptions * 0.1 + n_arrows * 0.15
        return max(0.1, 1.0 - complexity)


class MechanisticHypothesisGenerator(HypothesisGenerator):
    """Generates mechanistic hypotheses explaining how effects arise"""

    def __init__(self, mechanism_library: List[Dict] = None):
        self.mechanism_library = mechanism_library or self._default_mechanisms()
        self.hypothesis_counter = 0

    def _default_mechanisms(self) -> List[Dict]:
        """Default mechanistic patterns"""
        return [
            {
                'name': 'autoregressive',
                'pattern': 'Current state depends on past states',
                'equation': 'X_t = α*X_{t-1} + ε',
                'parameters': ['alpha'],
                'domains': ['ALL']
            },
            {
                'name': 'exponential_growth',
                'pattern': 'Exponential dynamics with rate λ',
                'equation': 'X_t = X_0 * exp(λ*t)',
                'parameters': ['lambda', 'x0'],
                'domains': ['D1', 'D2']
            },
            {
                'name': 'mean_reversion',
                'pattern': 'Reversion to long-term mean',
                'equation': 'X_t = μ + φ*(X_{t-1} - μ) + ε',
                'parameters': ['mu', 'phi'],
                'domains': ['CLD', 'D2']
            },
            {
                'name': 'multiplicative_interaction',
                'pattern': 'Variables interact multiplicatively',
                'equation': 'Y = X1 * X2 * β',
                'parameters': ['beta'],
                'domains': ['ALL']
            },
            {
                'name': 'threshold_activation',
                'pattern': 'Effect activates above threshold',
                'equation': 'Y = β*(X - θ) if X > θ else 0',
                'parameters': ['beta', 'theta'],
                'domains': ['D1', 'CLD']
            },
            {
                'name': 'delayed_response',
                'pattern': 'Effect occurs after delay τ',
                'equation': 'Y_t = f(X_{t-τ})',
                'parameters': ['tau'],
                'domains': ['ALL']
            }
        ]

    def generate(self, observation: Observation,
                 context: Dict[str, Any]) -> List[Hypothesis]:
        """Generate mechanistic hypotheses"""
        hypotheses = []
        domain = observation.domain

        for mechanism in self.mechanism_library:
            # Check domain applicability
            if domain in mechanism['domains'] or 'ALL' in mechanism['domains']:
                hypothesis = self._create_mechanistic_hypothesis(
                    mechanism, observation, context
                )
                if hypothesis:
                    hypotheses.append(hypothesis)

        return hypotheses

    def _create_mechanistic_hypothesis(self, mechanism: Dict,
                                        observation: Observation,
                                        context: Dict) -> Optional[Hypothesis]:
        """Create mechanistic hypothesis"""
        self.hypothesis_counter += 1

        predictions = [{
            'prediction': f"Data should fit {mechanism['equation']}",
            'test_type': 'curve_fitting',
            'expected_r_squared': 0.7
        }]

        return Hypothesis(
            hypothesis_id=f"H_mech_{self.hypothesis_counter}",
            hypothesis_type=HypothesisType.MECHANISTIC,
            description=mechanism['pattern'],
            explains=[observation.observation_id],
            assumptions=[f"Parameter {p} exists" for p in mechanism['parameters']],
            predictions=predictions,
            mechanism=mechanism['equation'],
            parsimony_score=1.0 / (1 + len(mechanism['parameters'])),
            metadata={'mechanism_name': mechanism['name']}
        )


class AnalogicalHypothesisGenerator(HypothesisGenerator):
    """Generates hypotheses by analogy to known cases"""

    def __init__(self):
        self.known_cases: List[Dict] = []
        self.hypothesis_counter = 0

    def add_known_case(self, case: Dict):
        """Add a known case for analogical reasoning"""
        self.known_cases.append(case)

    def generate(self, observation: Observation,
                 context: Dict[str, Any]) -> List[Hypothesis]:
        """Generate hypotheses by analogy"""
        hypotheses = []

        for case in self.known_cases:
            similarity = self._compute_similarity(observation, case)
            if similarity > 0.5:  # Threshold for analogical transfer
                hypothesis = self._transfer_from_case(
                    observation, case, similarity
                )
                hypotheses.append(hypothesis)

        return hypotheses

    def _compute_similarity(self, observation: Observation,
                           case: Dict) -> float:
        """Compute structural similarity between observation and case"""
        score = 0.0
        count = 0

        # Compare domains
        if observation.domain == case.get('domain', ''):
            score += 0.3
        count += 1

        # Compare variable count
        obs_vars = len(observation.data.get('variables', {}))
        case_vars = case.get('n_variables', 0)
        if obs_vars > 0 and case_vars > 0:
            var_ratio = min(obs_vars, case_vars) / max(obs_vars, case_vars)
            score += 0.3 * var_ratio
        count += 1

        # Compare structural features
        obs_features = set(observation.data.get('features', []))
        case_features = set(case.get('features', []))
        if obs_features and case_features:
            jaccard = len(obs_features & case_features) / len(obs_features | case_features)
            score += 0.4 * jaccard
        count += 1

        return score / count if count > 0 else 0.0

    def _transfer_from_case(self, observation: Observation,
                           case: Dict, similarity: float) -> Hypothesis:
        """Create hypothesis by transferring explanation from similar case"""
        self.hypothesis_counter += 1

        return Hypothesis(
            hypothesis_id=f"H_analog_{self.hypothesis_counter}",
            hypothesis_type=HypothesisType.ANALOGICAL,
            description=f"By analogy to {case.get('name', 'known case')}: {case.get('explanation', '')}",
            explains=[observation.observation_id],
            assumptions=['structural_similarity', 'transferability'],
            predictions=case.get('predictions', []),
            mechanism=case.get('mechanism'),
            coherence_score=similarity,
            parsimony_score=0.7,  # Analogies are moderately parsimonious
            metadata={
                'source_case': case.get('name'),
                'similarity': similarity
            }
        )


class ExplanationScorer:
    """Scores explanatory hypotheses on multiple criteria"""

    def __init__(self, prior_beliefs: Dict[str, float] = None,
                 constraints: List[Dict] = None):
        self.prior_beliefs = prior_beliefs or {}
        self.constraints = constraints or []

    def score_parsimony(self, hypothesis: Hypothesis) -> float:
        """
        Score parsimony (Occam's razor).
        Simpler explanations with fewer assumptions score higher.
        """
        n_assumptions = len(hypothesis.assumptions)
        n_predictions = len(hypothesis.predictions)

        # Fewer assumptions = higher parsimony
        assumption_penalty = 0.1 * n_assumptions

        # More predictions from fewer assumptions = higher parsimony
        if n_assumptions > 0:
            predictive_ratio = n_predictions / n_assumptions
            prediction_bonus = min(0.3, 0.1 * predictive_ratio)
        else:
            prediction_bonus = 0.2

        return max(0.1, min(1.0, 1.0 - assumption_penalty + prediction_bonus))

    def score_coherence(self, hypothesis: Hypothesis,
                       existing_beliefs: Dict[str, Any] = None) -> float:
        """
        Score coherence with existing beliefs and constraints.
        Explanations consistent with prior knowledge score higher.
        """
        if existing_beliefs is None:
            existing_beliefs = self.prior_beliefs

        coherence = 0.5  # Base coherence

        # Check consistency with prior beliefs
        for belief, strength in existing_beliefs.items():
            if belief in hypothesis.assumptions:
                coherence += 0.1 * strength
            # Check for contradictions
            if f"not_{belief}" in hypothesis.assumptions:
                coherence -= 0.2 * strength

        # Check constraint satisfaction
        for constraint in self.constraints:
            if self._violates_constraint(hypothesis, constraint):
                coherence -= 0.3 * constraint.get('severity', 0.5)

        return max(0.0, min(1.0, coherence))

    def score_explanatory_power(self, hypothesis: Hypothesis,
                                observations: List[Observation]) -> float:
        """
        Score explanatory power.
        Explanations that account for more observations score higher.
        """
        explained = set(hypothesis.explains)
        total_obs = set(o.observation_id for o in observations)

        if not total_obs:
            return 0.5

        coverage = len(explained & total_obs) / len(total_obs)

        # Bonus for explaining surprising observations
        surprise_bonus = 0.0
        for obs in observations:
            if obs.observation_id in explained:
                surprise_bonus += 0.1 * obs.surprise_level

        return min(1.0, coverage + surprise_bonus)

    def score_predictive_accuracy(self, hypothesis: Hypothesis,
                                   test_results: List[Dict] = None) -> float:
        """
        Score predictive accuracy based on tested predictions.
        """
        if not test_results:
            return 0.5  # No data, neutral score

        predictions = {p.get('prediction', ''): p for p in hypothesis.predictions}

        correct = 0
        total = 0

        for result in test_results:
            pred_id = result.get('prediction_id', '')
            if pred_id in predictions:
                total += 1
                if result.get('correct', False):
                    correct += 1

        if total == 0:
            return 0.5

        return correct / total

    def _violates_constraint(self, hypothesis: Hypothesis,
                            constraint: Dict) -> bool:
        """Check if hypothesis violates a constraint"""
        constraint_type = constraint.get('type', '')

        if constraint_type == 'mutual_exclusion':
            excluded = set(constraint.get('excluded', []))
            assumptions = set(hypothesis.assumptions)
            # Violation if both mutually exclusive assumptions present
            if len(excluded & assumptions) > 1:
                return True

        if constraint_type == 'required':
            required = constraint.get('required', [])
            if any(r not in hypothesis.assumptions for r in required):
                return True

        return False

    def full_score(self, hypothesis: Hypothesis,
                   observations: List[Observation],
                   test_results: List[Dict] = None,
                   weights: Dict[str, float] = None) -> Dict[str, float]:
        """Compute full scoring breakdown"""

        hypothesis.parsimony_score = self.score_parsimony(hypothesis)
        hypothesis.coherence_score = self.score_coherence(hypothesis)
        hypothesis.explanatory_power = self.score_explanatory_power(
            hypothesis, observations
        )
        hypothesis.predictive_accuracy = self.score_predictive_accuracy(
            hypothesis, test_results
        )

        return {
            'parsimony': hypothesis.parsimony_score,
            'coherence': hypothesis.coherence_score,
            'explanatory_power': hypothesis.explanatory_power,
            'predictive_accuracy': hypothesis.predictive_accuracy,
            'overall': hypothesis.overall_score(weights)
        }


class AbductiveInferenceEngine:
    """
    Main engine for abductive inference (inference to best explanation).

    Integrates multiple hypothesis generators and scoring mechanisms
    to identify the best explanation for observed phenomena.
    """

    def __init__(self,
                 prior_beliefs: Dict[str, float] = None,
                 constraints: List[Dict] = None):
        # Hypothesis generators
        self.generators: List[HypothesisGenerator] = [
            CausalHypothesisGenerator(),
            MechanisticHypothesisGenerator(),
            AnalogicalHypothesisGenerator()
        ]

        # Scorer
        self.scorer = ExplanationScorer(prior_beliefs, constraints)

        # State
        self.observations: Dict[str, Observation] = {}
        self.hypotheses: Dict[str, Hypothesis] = {}
        self.evidence: Dict[str, List[Evidence]] = defaultdict(list)
        self.best_explanations: Dict[str, Hypothesis] = {}  # obs_id -> best hypothesis

        # Configuration
        self.max_hypotheses_per_observation = 10
        self.min_score_threshold = 0.3

    def add_generator(self, generator: HypothesisGenerator):
        """Add a custom hypothesis generator"""
        self.generators.append(generator)

    def observe(self, observation: Observation) -> str:
        """Register a new observation requiring explanation"""
        self.observations[observation.observation_id] = observation
        return observation.observation_id

    def generate_explanations(self, observation_id: str,
                              context: Dict[str, Any] = None) -> List[Hypothesis]:
        """
        Generate candidate explanations for an observation.

        Args:
            observation_id: ID of observation to explain
            context: Additional context for generation

        Returns:
            List of candidate hypotheses
        """
        if observation_id not in self.observations:
            return []

        observation = self.observations[observation_id]
        context = context or {}

        # Generate hypotheses from all generators
        all_hypotheses = []
        for generator in self.generators:
            try:
                hypotheses = generator.generate(observation, context)
                all_hypotheses.extend(hypotheses)
            except Exception as e:
                # Log but continue with other generators
                pass

        # Score all hypotheses
        for hypothesis in all_hypotheses:
            self.scorer.full_score(hypothesis, [observation])

        # Sort by score and keep top candidates
        all_hypotheses.sort(key=lambda h: h.overall_score(), reverse=True)
        top_hypotheses = all_hypotheses[:self.max_hypotheses_per_observation]

        # Store hypotheses
        for h in top_hypotheses:
            self.hypotheses[h.hypothesis_id] = h

        return top_hypotheses

    def score_explanation(self, hypothesis_id: str,
                          additional_evidence: List[Evidence] = None) -> float:
        """
        Score an explanation given current evidence.

        Args:
            hypothesis_id: ID of hypothesis to score
            additional_evidence: New evidence to incorporate

        Returns:
            Updated overall score
        """
        if hypothesis_id not in self.hypotheses:
            return 0.0

        hypothesis = self.hypotheses[hypothesis_id]

        # Add new evidence
        if additional_evidence:
            for ev in additional_evidence:
                self.evidence[hypothesis_id].append(ev)

        # Collect all evidence for this hypothesis
        all_evidence = self.evidence[hypothesis_id]

        # Update scores based on evidence
        supporting = [e for e in all_evidence if e.evidence_type == 'supports']
        contradicting = [e for e in all_evidence if e.evidence_type == 'contradicts']

        # Adjust confidence based on evidence
        support_strength = sum(e.strength for e in supporting) / max(1, len(supporting))
        contra_strength = sum(e.strength for e in contradicting) / max(1, len(contradicting))

        if supporting or contradicting:
            evidence_factor = (support_strength - 0.5 * contra_strength)
            hypothesis.confidence = max(0.1, min(0.95, 0.5 + 0.5 * evidence_factor))

        # Get observations this hypothesis explains
        observations = [self.observations[oid] for oid in hypothesis.explains
                       if oid in self.observations]

        # Re-score with evidence
        self.scorer.full_score(hypothesis, observations)

        return hypothesis.overall_score()

    def select_best_explanation(self, observation_id: str,
                                 candidates: List[Hypothesis] = None) -> Optional[Hypothesis]:
        """
        Select the best explanation for an observation.

        Uses inference to best explanation (IBE) criteria.

        Args:
            observation_id: Observation to explain
            candidates: Candidate hypotheses (if None, generates them)

        Returns:
            Best explanation or None if no good explanation found
        """
        if candidates is None:
            candidates = self.generate_explanations(observation_id)

        if not candidates:
            return None

        # Filter by minimum threshold
        viable = [h for h in candidates if h.overall_score() >= self.min_score_threshold]

        if not viable:
            # Return best even if below threshold
            return max(candidates, key=lambda h: h.overall_score())

        # Select best
        best = max(viable, key=lambda h: h.overall_score())
        self.best_explanations[observation_id] = best

        return best

    def refine_hypothesis(self, hypothesis_id: str,
                          refinement: Dict[str, Any]) -> Hypothesis:
        """
        Refine an existing hypothesis based on new information.

        Args:
            hypothesis_id: Hypothesis to refine
            refinement: Refinement information

        Returns:
            New refined hypothesis
        """
        if hypothesis_id not in self.hypotheses:
            raise ValueError(f"Unknown hypothesis: {hypothesis_id}")

        original = self.hypotheses[hypothesis_id]

        # Create refined hypothesis
        new_id = f"{hypothesis_id}_refined"
        refined = Hypothesis(
            hypothesis_id=new_id,
            hypothesis_type=original.hypothesis_type,
            description=refinement.get('description', original.description),
            explains=original.explains.copy(),
            assumptions=refinement.get('assumptions', original.assumptions.copy()),
            predictions=refinement.get('predictions', original.predictions.copy()),
            mechanism=refinement.get('mechanism', original.mechanism),
            parent_hypotheses=[hypothesis_id],
            confidence=original.confidence
        )

        # Score refined hypothesis
        observations = [self.observations[oid] for oid in refined.explains
                       if oid in self.observations]
        self.scorer.full_score(refined, observations)

        self.hypotheses[new_id] = refined
        return refined

    def compare_explanations(self, hypothesis_ids: List[str]) -> Dict[str, Any]:
        """
        Compare multiple explanations.

        Returns:
            Comparison results with rankings
        """
        hypotheses = [self.hypotheses[hid] for hid in hypothesis_ids
                     if hid in self.hypotheses]

        if not hypotheses:
            return {'error': 'No valid hypotheses found'}

        # Rank by each criterion
        rankings = {
            'overall': sorted(hypotheses, key=lambda h: h.overall_score(), reverse=True),
            'parsimony': sorted(hypotheses, key=lambda h: h.parsimony_score, reverse=True),
            'coherence': sorted(hypotheses, key=lambda h: h.coherence_score, reverse=True),
            'explanatory_power': sorted(hypotheses, key=lambda h: h.explanatory_power, reverse=True),
            'predictive': sorted(hypotheses, key=lambda h: h.predictive_accuracy, reverse=True)
        }

        return {
            'rankings': {
                criterion: [h.hypothesis_id for h in ranked]
                for criterion, ranked in rankings.items()
            },
            'best_overall': rankings['overall'][0].to_dict() if rankings['overall'] else None,
            'scores': {
                h.hypothesis_id: h.to_dict()['scores']
                for h in hypotheses
            }
        }

    def explain(self, observation: Observation,
                context: Dict[str, Any] = None) -> Dict[str, Any]:
        """
        Main entry point: Generate, score, and select best explanation.

        Args:
            observation: Observation to explain
            context: Additional context

        Returns:
            Explanation result with best hypothesis and alternatives
        """
        # Register observation
        obs_id = self.observe(observation)

        # Generate candidates
        candidates = self.generate_explanations(obs_id, context)

        # Select best
        best = self.select_best_explanation(obs_id, candidates)

        return {
            'observation_id': obs_id,
            'best_explanation': best.to_dict() if best else None,
            'alternatives': [h.to_dict() for h in candidates[1:5]] if len(candidates) > 1 else [],
            'n_candidates_generated': len(candidates),
            'explanation_quality': best.quality_level().value if best else 'none'
        }

    def get_predictions_to_test(self, hypothesis_id: str) -> List[Dict]:
        """Get untested predictions from a hypothesis"""
        if hypothesis_id not in self.hypotheses:
            return []

        hypothesis = self.hypotheses[hypothesis_id]
        tested_preds = set()

        for ev in self.evidence[hypothesis_id]:
            if 'prediction_id' in ev.data:
                tested_preds.add(ev.data['prediction_id'])

        return [p for p in hypothesis.predictions
                if p.get('prediction', '') not in tested_preds]

    def update_from_test(self, hypothesis_id: str,
                         prediction: str, result: bool,
                         confidence: float = 0.8) -> float:
        """
        Update hypothesis score based on prediction test result.

        Args:
            hypothesis_id: Hypothesis being tested
            prediction: The prediction that was tested
            result: Whether prediction was correct
            confidence: Confidence in test result

        Returns:
            Updated hypothesis score
        """
        evidence_type = 'supports' if result else 'contradicts'

        evidence = Evidence(
            evidence_id=f"ev_{hypothesis_id}_{len(self.evidence[hypothesis_id])}",
            hypothesis_id=hypothesis_id,
            evidence_type=evidence_type,
            strength=confidence,
            description=f"Prediction '{prediction}' was {'correct' if result else 'incorrect'}",
            data={'prediction_id': prediction, 'result': result}
        )

        return self.score_explanation(hypothesis_id, [evidence])

    def stats(self) -> Dict[str, Any]:
        """Get engine statistics"""
        return {
            'n_observations': len(self.observations),
            'n_hypotheses': len(self.hypotheses),
            'n_explained': len(self.best_explanations),
            'n_generators': len(self.generators),
            'hypotheses_by_type': {
                ht.value: sum(1 for h in self.hypotheses.values()
                             if h.hypothesis_type == ht)
                for ht in HypothesisType
            },
            'average_score': np.mean([h.overall_score()
                                      for h in self.hypotheses.values()])
                            if self.hypotheses else 0.0
        }

    def to_dict(self) -> Dict:
        """Serialize engine state"""
        return {
            'observations': {oid: o.to_dict()
                           for oid, o in self.observations.items()},
            'hypotheses': {hid: h.to_dict()
                          for hid, h in self.hypotheses.items()},
            'best_explanations': {oid: h.hypothesis_id
                                 for oid, h in self.best_explanations.items()},
            'stats': self.stats()
        }

    def save(self, filepath: str):
        """Save engine state to file"""
        with open(filepath, 'w') as f:
            json.dump(self.to_dict(), f, indent=2)


# =============================================================================
# EXPORTS
# =============================================================================

__all__ = [
    'AbductiveInferenceEngine',
    'Observation',
    'Hypothesis',
    'Evidence',
    'HypothesisType',
    'ExplanationQuality',
    'HypothesisGenerator',
    'CausalHypothesisGenerator',
    'MechanisticHypothesisGenerator',
    'AnalogicalHypothesisGenerator',
    'ExplanationScorer'
]


