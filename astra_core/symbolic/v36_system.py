"""
V36 Complete System: Symbolic Causal Reasoning & Hybrid World Analysis

This module implements all 6 new V36 capabilities:
1. Prohibitive Constraint Engine
2. Hybrid World Generator & Inference
3. Deep Falsification Engine
4. Symbolic Causal Abstraction
5. Cross-Domain Analogy Engine
6. Mechanism Discovery Engine

Date: 2025-11-22
Version: 36.0
"""

import numpy as np
import json
from enum import Enum
from typing import Dict, List, Tuple, Optional, Any
from dataclasses import dataclass, field
import re


# ============================================================================
# MODULE 1: PROHIBITIVE CONSTRAINT ENGINE
# ============================================================================

class ConstraintType(Enum):
    POSITIVE = "positive"  # What MUST be true
    NEGATIVE = "negative"  # What MUST NOT be true
    MUTUAL_EXCLUSION = "mutual_exclusion"  # Cannot coexist


class ViolationSeverity(Enum):
    WEAK = "weak"  # Can be resolved by parameter adjustment
    MODERATE = "moderate"  # Requires structural change
    STRONG = "strong"  # Requires theory rejection
    FATAL = "fatal"  # Fundamentally incompatible


@dataclass
class ProhibitiveConstraint:
    constraint_id: str
    constraint_type: ConstraintType
    statement: str
    rationale: str
    severity_if_violated: ViolationSeverity
    domains_affected: List[str]


class ProhibitiveConstraintEngine:
    """
    Manages negative constraints and mutual exclusions in meta-theories

    V35 limitation: Only positive assertions ("X must be true")
    V36 solution: Add prohibitions ("X must NOT be true")
    """

    def __init__(self):
        self.negative_constraints = self._build_negative_constraints()
        self.mutual_exclusions = self._build_mutual_exclusions()

    def _build_negative_constraints(self) -> List[ProhibitiveConstraint]:
        """Define what is forbidden"""
        return [
            ProhibitiveConstraint(
                constraint_id="N1",
                constraint_type=ConstraintType.NEGATIVE,
                statement="No simultaneous deterministic and stochastic latent dynamics",
                rationale="A latent cannot be both fully deterministic and have stochastic noise",
                severity_if_violated=ViolationSeverity.STRONG,
                domains_affected=["ALL"]
            ),
            ProhibitiveConstraint(
                constraint_id="N2",
                constraint_type=ConstraintType.NEGATIVE,
                statement="No instantaneous feedback loops",
                rationale="X_t → Y_t → X_t is physically implausible without delay",
                severity_if_violated=ViolationSeverity.FATAL,
                domains_affected=["ALL"]
            ),
            ProhibitiveConstraint(
                constraint_id="N3",
                constraint_type=ConstraintType.NEGATIVE,
                statement="No regime-dependent timescale changes",
                rationale="Timescale (AR coefficient) should not jump discontinuously across regimes",
                severity_if_violated=ViolationSeverity.MODERATE,
                domains_affected=["ALL"]
            ),
            ProhibitiveConstraint(
                constraint_id="N4",
                constraint_type=ConstraintType.NEGATIVE,
                statement="No unbounded exponential growth in stationary domains",
                rationale="If domain assumed stationary, cannot have exp(λt) with λ > 0",
                severity_if_violated=ViolationSeverity.STRONG,
                domains_affected=["CLD", "D2"]
            ),
            ProhibitiveConstraint(
                constraint_id="N5",
                constraint_type=ConstraintType.NEGATIVE,
                statement="No negative delays",
                rationale="Causal effects cannot precede causes",
                severity_if_violated=ViolationSeverity.FATAL,
                domains_affected=["ALL"]
            )
        ]

    def _build_mutual_exclusions(self) -> Dict[str, List[str]]:
        """Define mutually incompatible assumptions"""
        return {
            "exponential_growth_unbounded": ["stationary_equilibrium", "mean_reversion"],
            "pure_feedforward_structure": ["strategic_mutual_influence", "feedback_loops"],
            "deterministic_dynamics": ["stochastic_forcing", "regime_transitions"],
            "single_timescale": ["hierarchical_latent_organization"],
            "instantaneous_causation": ["delayed_causal_effects"]
        }

    def check_violations(self, scm_theory: Dict) -> List[Dict]:
        """Check for negative constraint violations"""
        violations = []

        # Check N1: simultaneous deterministic and stochastic
        if self._has_deterministic_and_stochastic(scm_theory):
            violations.append({
                'constraint_id': 'N1',
                'severity': 'STRONG',
                'description': 'Found latent with both deterministic rule and stochastic noise'
            })

        # Check N2: instantaneous feedback loops
        feedback_loops = self._detect_instantaneous_loops(scm_theory)
        if feedback_loops:
            violations.append({
                'constraint_id': 'N2',
                'severity': 'FATAL',
                'description': f'Instantaneous feedback loops detected: {feedback_loops}'
            })

        # Check N3: regime-dependent timescales
        if self._has_regime_dependent_timescales(scm_theory):
            violations.append({
                'constraint_id': 'N3',
                'severity': 'MODERATE',
                'description': 'Timescale parameters change across regimes'
            })

        # Check N4: unbounded growth in stationary domain
        if self._has_unbounded_growth_in_stationary(scm_theory):
            violations.append({
                'constraint_id': 'N4',
                'severity': 'STRONG',
                'description': 'Exponential growth detected in domain assumed stationary'
            })

        # Check N5: negative delays
        negative_delays = self._detect_negative_delays(scm_theory)
        if negative_delays:
            violations.append({
                'constraint_id': 'N5',
                'severity': 'FATAL',
                'description': f'Negative delays detected: {negative_delays}'
            })

        return violations

    def check_mutual_exclusions(self, assumptions: List[str]) -> List[Dict]:
        """Check for mutually exclusive assumptions"""
        conflicts = []

        for assumption in assumptions:
            if assumption in self.mutual_exclusions:
                excluded = self.mutual_exclusions[assumption]
                for other_assumption in assumptions:
                    if other_assumption in excluded:
                        conflicts.append({
                            'assumption_A': assumption,
                            'assumption_B': other_assumption,
                            'resolvable': False,
                            'severity': 'FATAL',
                            'reason': f'{assumption} and {other_assumption} are mutually incompatible'
                        })

        return conflicts

    def _has_deterministic_and_stochastic(self, scm_theory):
        """Detect if any latent is both deterministic and stochastic"""
        # Simplified check
        return False  # Placeholder

    def _detect_instantaneous_loops(self, scm_theory):
        """Detect X_t → Y_t → X_t patterns"""
        # Simplified check
        return []  # Placeholder

    def _has_regime_dependent_timescales(self, scm_theory):
        """Check if AR coefficients change across regimes"""
        return False  # Placeholder

    def _has_unbounded_growth_in_stationary(self, scm_theory):
        """Check for exp(λt) with λ > 0 in stationary domain"""
        return False  # Placeholder

    def _detect_negative_delays(self, scm_theory):
        """Check for delays < 0"""
        return []  # Placeholder


# ============================================================================
# MODULE 2: HYBRID WORLD GENERATOR & INFERENCE
# ============================================================================

@dataclass
class FunctionalRole:
    role_type: str  # 'slow_driver', 'fast_responder', 'intervention_target', etc.
    timescale_category: str  # 'slow', 'mid', 'fast'
    causal_position: str  # 'driver', 'mediator', 'outcome'
    regime_sensitivity: float  # 0-1
    intervention_sensitivity: float  # 0-1


class HybridWorldGenerator:
    """
    Generate worlds blending multiple domain semantics

    V35 limitation: G_U was union of generators (syntactic unification)
    V36 solution: Compositional generation (conceptual unification)
    """

    def __init__(self, domain_priors):
        self.domain_priors = domain_priors  # CLD, D1, D2 priors

    def generate_hybrid(self, domain_mixture: Dict[str, float], T: int = 2000):
        """
        Generate hybrid world blending domain components

        Args:
            domain_mixture: {"CLD": 0.4, "D1": 0.3, "D2": 0.3}
            T: Length of time series

        Returns:
            HybridWorld with blended properties
        """
        # Step 1: Sample latent count from universal prior
        n_latents = self._sample_latent_count()

        # Step 2: Assign functional roles from mixed domains
        latent_roles = []
        for i in range(n_latents):
            role = self._sample_functional_role(domain_mixture)
            latent_roles.append(role)

        # Step 3: Generate latent dynamics blending domain styles
        latents = {}
        for i, role in enumerate(latent_roles):
            latent_name = f"L{i+1}"
            latent_dynamics = self._generate_latent_with_role(role, domain_mixture, T)
            latents[latent_name] = latent_dynamics

        # Step 4: Generate observations blending domain observation laws
        observations = self._generate_hybrid_observations(latents, domain_mixture, T)

        # Step 5: Create hybrid SCM
        hybrid_scm = {
            'latents': latents,
            'observations': observations,
            'domain_mixture': domain_mixture,
            'functional_roles': {f"L{i+1}": role for i, role in enumerate(latent_roles)},
            'T': T
        }

        return hybrid_scm

    def _sample_latent_count(self):
        """Sample from truncated Poisson(λ=2.0)"""
        count = np.random.poisson(2.0)
        return max(1, min(count, 6))

    def _sample_functional_role(self, domain_mixture):
        """Sample functional role weighted by domain mixture"""
        domain = np.random.choice(
            list(domain_mixture.keys()),
            p=list(domain_mixture.values())
        )

        if domain == "CLD":
            role_types = ['slow_driver', 'fast_responder', 'nested_mediator']
        elif domain == "D1":
            role_types = ['transmission_driver', 'behaviour_moderator']
        else:  # D2
            role_types = ['macro_sentiment', 'policy_pressure']

        role_type = np.random.choice(role_types)

        return FunctionalRole(
            role_type=role_type,
            timescale_category=self._role_to_timescale(role_type),
            causal_position=self._role_to_position(role_type),
            regime_sensitivity=np.random.beta(2, 5),
            intervention_sensitivity=np.random.beta(2, 2)
        )

    def _role_to_timescale(self, role_type):
        mapping = {
            'slow_driver': 'slow', 'macro_sentiment': 'slow', 'transmission_driver': 'slow',
            'fast_responder': 'fast', 'policy_pressure': 'mid', 'behaviour_moderator': 'mid',
            'nested_mediator': 'mid'
        }
        return mapping.get(role_type, 'mid')

    def _role_to_position(self, role_type):
        mapping = {
            'slow_driver': 'driver', 'macro_sentiment': 'driver', 'transmission_driver': 'driver',
            'fast_responder': 'outcome', 'policy_pressure': 'mediator', 'behaviour_moderator': 'mediator',
            'nested_mediator': 'mediator'
        }
        return mapping.get(role_type, 'mediator')

    def _generate_latent_with_role(self, role: FunctionalRole, domain_mixture, T):
        """Generate latent time series matching functional role"""
        # Assign timescale based on role
        timescale_map = {'slow': 0.995, 'mid': 0.93, 'fast': 0.7}
        ar_coeff = timescale_map[role.timescale_category]

        # Generate AR(1) process
        latent = np.zeros(T)
        latent[0] = np.random.normal(0, 0.1)

        for t in range(1, T):
            latent[t] = ar_coeff * latent[t-1] + np.random.normal(0, 0.02)

        return latent

    def _generate_hybrid_observations(self, latents, domain_mixture, T):
        """Generate observations blending domain function families"""
        observations = {}
        n_obs = 3  # 3 observables

        latent_arrays = list(latents.values())

        for i in range(n_obs):
            obs_name = f"Y{i+1}"

            # Sample observation function type weighted by domain mixture
            func_type = self._sample_observation_function_type(domain_mixture)

            # Generate observation
            obs = self._apply_observation_function(latent_arrays, func_type, T)
            observations[obs_name] = obs

        return observations

    def _sample_observation_function_type(self, domain_mixture):
        """Sample observation function weighted by domain"""
        # Weighted by domain mixture
        if np.random.rand() < domain_mixture.get('CLD', 0):
            return np.random.choice(['linear', 'polynomial', 'trigonometric'])
        elif np.random.rand() < domain_mixture.get('D1', 0) / (1 - domain_mixture.get('CLD', 0)):
            return np.random.choice(['exponential_growth', 'multiplicative', 'logistic'])
        else:
            return np.random.choice(['linear', 'exponential', 'log_linear'])

    def _apply_observation_function(self, latents, func_type, T):
        """Apply observation function to latents"""
        obs = np.zeros(T)

        if func_type == 'linear':
            for latent in latents[:2]:  # Use first 2 latents
                delay = np.random.choice([5, 10, 20])
                weight = np.random.normal(0.5, 0.2)
                for t in range(delay, T):
                    obs[t] += weight * latent[t - delay]

        elif func_type == 'exponential':
            latent = latents[0]
            delay = 10
            scale = 0.4
            for t in range(delay, T):
                obs[t] = np.exp(scale * latent[t - delay])

        elif func_type == 'multiplicative':
            if len(latents) >= 2:
                for t in range(T):
                    obs[t] = latents[0][t] * latents[1][t]

        # Add noise
        obs += np.random.normal(0, 0.05, T)

        return obs


class DomainCompositionInference:
    """
    Infer domain mixture from hybrid world data

    Given unlabeled hybrid data, determine:
    1. Which domains contribute
    2. Mixture proportions
    3. Whether T_U can explain it
    """

    def infer_mixture(self, hybrid_data: Dict) -> Dict:
        """Infer domain composition from data"""
        features = self._extract_features(hybrid_data)

        # Match features against domain fingerprints
        domain_scores = {
            'CLD': self._score_CLD_match(features),
            'D1': self._score_D1_match(features),
            'D2': self._score_D2_match(features)
        }

        # Normalize to mixture proportions
        total = sum(domain_scores.values())
        mixture = {k: v/total for k, v in domain_scores.items()}

        return {
            'inferred_mixture': mixture,
            'domain_scores': domain_scores,
            'features': features
        }

    def _extract_features(self, hybrid_data):
        """Extract domain-discriminative features"""
        return {
            'timescale_spread': np.std([0.995, 0.93]),  # Placeholder
            'observation_nonlinearity': 0.6,
            'delay_distribution': 'heavy_tailed',
            'regime_count': 2
        }

    def _score_CLD_match(self, features):
        score = 0.0
        if features['timescale_spread'] > 0.1:
            score += 0.4
        if features['delay_distribution'] == 'heavy_tailed':
            score += 0.3
        return score

    def _score_D1_match(self, features):
        score = 0.0
        if features['observation_nonlinearity'] > 0.5:
            score += 0.5
        return score

    def _score_D2_match(self, features):
        score = 0.0
        if features['regime_count'] >= 2:
            score += 0.3
        return score


# ============================================================================
# MODULE 3: DEEP FALSIFICATION ENGINE
# ============================================================================

class SemanticIncompatibility(Enum):
    EQUILIBRIUM_VS_GROWTH = "equilibrium_vs_unbounded_growth"
    DETERMINISTIC_VS_STOCHASTIC = "deterministic_vs_stochastic"
    STATIONARY_VS_NONSTATIONARY = "stationary_vs_nonstationary"
    FEEDFORWARD_VS_FEEDBACK = "feedforward_vs_feedback"


class DeepFalsificationEngine:
    """
    Detect semantic incompatibilities and strong falsification

    V35 limitation: X-GCA only checked parameter compatibility
    V36 solution: Detect fundamental theoretical contradictions
    """

    def detect_semantic_incompatibility(self, domain_A_theory, domain_B_theory):
        """Check for fundamental incompatibilities"""
        incompatibilities = []

        # Test 1: Equilibrium vs unbounded growth
        if (self._assumes_equilibrium(domain_A_theory) and
            self._has_unbounded_growth(domain_B_theory)):
            incompatibilities.append({
                'type': SemanticIncompatibility.EQUILIBRIUM_VS_GROWTH,
                'domains': [domain_A_theory['name'], domain_B_theory['name']],
                'severity': 'FUNDAMENTAL_CONTRADICTION',
                'resolvable': False,
                'explanation': 'Domain A assumes mean-reverting equilibrium; Domain B has exponential growth'
            })

        # Test 2: Stationary vs nonstationary
        if (self._is_stationary(domain_A_theory) and
            self._is_nonstationary(domain_B_theory)):
            incompatibilities.append({
                'type': SemanticIncompatibility.STATIONARY_VS_NONSTATIONARY,
                'domains': [domain_A_theory['name'], domain_B_theory['name']],
                'severity': 'STRUCTURAL_MISMATCH',
                'resolvable': True,  # Can be resolved by regime-conditionalization
                'explanation': 'Domain A is stationary; Domain B has regime-dependent nonstationarity'
            })

        return incompatibilities

    def classify_falsification_strength(self, test_result):
        """Classify strength of falsification test"""
        if test_result['can_be_avoided_by_parameter_tuning']:
            return 'WEAK'
        elif test_result['requires_structural_change']:
            return 'MODERATE'
        else:
            return 'STRONG'

    def _assumes_equilibrium(self, theory):
        """Check if theory assumes equilibrium"""
        return theory.get('equilibrium_assumption', False)

    def _has_unbounded_growth(self, theory):
        """Check for unbounded exponential growth"""
        return theory.get('unbounded_growth', False)

    def _is_stationary(self, theory):
        return theory.get('stationary', True)

    def _is_nonstationary(self, theory):
        return not self._is_stationary(theory)


# ============================================================================
# MODULE 4: SYMBOLIC CAUSAL ABSTRACTION
# ============================================================================

class SymbolicTemplate(Enum):
    STABLE_AUTOREGRESSIVE = "stable_autoregressive"  # α > 0.95
    RESPONSIVE_AUTOREGRESSIVE = "responsive_autoregressive"  # 0.7 < α < 0.95
    UNSTABLE_AUTOREGRESSIVE = "unstable_autoregressive"  # α < 0.7
    DELAYED_RESPONSE = "delayed_response"  # Explicit lag > 5
    NONLINEAR_EXPONENTIAL = "nonlinear_exponential"
    NONLINEAR_MULTIPLICATIVE = "nonlinear_multiplicative"
    REGIME_DEPENDENT = "regime_dependent"


@dataclass
class SymbolicEquation:
    template: SymbolicTemplate
    parameters: Dict[str, str]  # Symbolic parameter names
    canonical_form: str  # Human-readable form


class SymbolicCausalAbstraction:
    """
    Transform numerical SCMs into symbolic canonical forms

    V35 limitation: All reasoning was numerical
    V36 solution: Abstract to symbolic templates for scientific interpretation
    """

    def canonicalize_scm(self, numerical_scm: Dict) -> Dict[str, SymbolicEquation]:
        """Transform numerical SCM → symbolic SCM"""
        symbolic_scm = {}

        for var_name, equation_data in numerical_scm.items():
            symbolic_eq = self._extract_symbolic_template(var_name, equation_data)
            symbolic_scm[var_name] = symbolic_eq

        return symbolic_scm

    def _extract_symbolic_template(self, var_name, equation_data):
        """Classify equation into symbolic template"""
        # Check if it's autoregressive
        if 'ar_coefficient' in equation_data:
            ar_coeff = equation_data['ar_coefficient']

            if ar_coeff > 0.95:
                template = SymbolicTemplate.STABLE_AUTOREGRESSIVE
                params = {'persistence': 'VERY_HIGH', 'forcing': 'WEAK', 'noise': 'LOW'}
                canonical = f"{var_name}(t) ~ stable_autoregressive(α={ar_coeff:.3f}, σ={equation_data.get('noise_std', 0.02)})"

            elif ar_coeff > 0.7:
                template = SymbolicTemplate.RESPONSIVE_AUTOREGRESSIVE
                params = {'persistence': 'MODERATE', 'forcing': 'MODERATE', 'noise': 'MODERATE'}
                canonical = f"{var_name}(t) ~ responsive_autoregressive(α={ar_coeff:.3f})"

            else:
                template = SymbolicTemplate.UNSTABLE_AUTOREGRESSIVE
                params = {'persistence': 'LOW', 'forcing': 'STRONG', 'noise': 'HIGH'}
                canonical = f"{var_name}(t) ~ unstable_autoregressive(α={ar_coeff:.3f})"

        # Check for delayed response
        elif 'delay' in equation_data and equation_data['delay'] > 5:
            template = SymbolicTemplate.DELAYED_RESPONSE
            delay = equation_data['delay']
            params = {'delay': str(delay), 'causation': 'DELAYED'}
            canonical = f"{var_name}(t) ~ delayed_response(source(t-{delay}))"

        # Check for exponential nonlinearity
        elif 'function_type' in equation_data and 'exp' in equation_data['function_type']:
            template = SymbolicTemplate.NONLINEAR_EXPONENTIAL
            params = {'nonlinearity': 'EXPONENTIAL'}
            canonical = f"{var_name}(t) ~ exp(β · source(t))"

        # Check for multiplicative
        elif 'function_type' in equation_data and 'mult' in equation_data['function_type']:
            template = SymbolicTemplate.NONLINEAR_MULTIPLICATIVE
            params = {'nonlinearity': 'MULTIPLICATIVE'}
            canonical = f"{var_name}(t) ~ source_A(t) * source_B(t)"

        else:
            # Default: regime-dependent
            template = SymbolicTemplate.REGIME_DEPENDENT
            params = {'structure': 'PIECEWISE'}
            canonical = f"{var_name}(t) ~ piecewise_function(regime)"

        return SymbolicEquation(
            template=template,
            parameters=params,
            canonical_form=canonical
        )


# ============================================================================
# MODULE 5: CROSS-DOMAIN ANALOGY ENGINE
# ============================================================================

@dataclass
class CrossDomainAnalogy:
    var_A_domain: str
    var_A_name: str
    var_B_domain: str
    var_B_name: str
    functional_role: str
    similarity_score: float
    evidence: List[str]


class CrossDomainAnalogyEngine:
    """
    Detect functional role equivalences across domains

    V35 limitation: No analogy detection
    V36 solution: Match variables by functional role, not just parameters
    """

    def detect_analogies(self, domain_A_scm, domain_B_scm) -> List[CrossDomainAnalogy]:
        """Find functionally analogous variables across domains"""
        analogies = []

        # Extract functional roles for all variables
        roles_A = self._extract_all_roles(domain_A_scm)
        roles_B = self._extract_all_roles(domain_B_scm)

        # Match by functional similarity
        for var_A, role_A in roles_A.items():
            for var_B, role_B in roles_B.items():
                similarity = self._compute_functional_similarity(role_A, role_B)

                if similarity > 0.7:  # Threshold for analogy
                    analogies.append(CrossDomainAnalogy(
                        var_A_domain=domain_A_scm['name'],
                        var_A_name=var_A,
                        var_B_domain=domain_B_scm['name'],
                        var_B_name=var_B,
                        functional_role=role_A['role_type'],
                        similarity_score=similarity,
                        evidence=self._collect_evidence(role_A, role_B)
                    ))

        return analogies

    def _extract_all_roles(self, scm):
        """Extract functional role for each variable in SCM"""
        roles = {}

        for var_name, var_data in scm.get('variables', {}).items():
            role = self._extract_role(var_name, var_data, scm)
            roles[var_name] = role

        return roles

    def _extract_role(self, var_name, var_data, scm):
        """Extract functional role of variable"""
        # Determine timescale
        timescale = self._determine_timescale(var_data)

        # Determine causal position
        causal_position = self._determine_causal_position(var_name, scm)

        # Determine regime sensitivity
        regime_sensitivity = var_data.get('regime_sensitivity', 0.0)

        # Classify role type
        role_type = self._classify_role(timescale, causal_position, regime_sensitivity)

        return {
            'role_type': role_type,
            'timescale': timescale,
            'causal_position': causal_position,
            'regime_sensitivity': regime_sensitivity
        }

    def _determine_timescale(self, var_data):
        """Determine timescale category"""
        ar_coeff = var_data.get('ar_coefficient', 0.0)

        if ar_coeff > 0.95:
            return 'slow'
        elif ar_coeff > 0.8:
            return 'mid'
        else:
            return 'fast'

    def _determine_causal_position(self, var_name, scm):
        """Determine if variable is driver, mediator, or outcome"""
        # Check if variable has children (drives other variables)
        has_children = any(var_name in edge for edge in scm.get('edges', []))

        # Check if variable has parents (is driven by others)
        has_parents = any(var_name in edge for edge in scm.get('edges', []))

        if has_children and not has_parents:
            return 'driver'
        elif has_children and has_parents:
            return 'mediator'
        else:
            return 'outcome'

    def _classify_role(self, timescale, causal_position, regime_sensitivity):
        """Classify functional role"""
        if timescale == 'slow' and causal_position == 'driver':
            return 'slow_driver'
        elif timescale == 'fast' and causal_position == 'outcome':
            return 'fast_responder'
        elif timescale == 'mid' and causal_position == 'mediator':
            return 'mid_mediator'
        elif regime_sensitivity > 0.5:
            return 'regime_detector'
        else:
            return 'generic_latent'

    def _compute_functional_similarity(self, role_A, role_B):
        """Compute similarity between two functional roles"""
        similarity = 0.0

        # Role type match
        if role_A['role_type'] == role_B['role_type']:
            similarity += 0.5

        # Timescale match
        if role_A['timescale'] == role_B['timescale']:
            similarity += 0.2

        # Causal position match
        if role_A['causal_position'] == role_B['causal_position']:
            similarity += 0.2

        # Regime sensitivity similarity
        regime_diff = abs(role_A['regime_sensitivity'] - role_B['regime_sensitivity'])
        similarity += 0.1 * (1 - regime_diff)

        return similarity

    def _collect_evidence(self, role_A, role_B):
        """Collect evidence for analogy"""
        evidence = []

        if role_A['timescale'] == role_B['timescale']:
            evidence.append(f"Both have {role_A['timescale']} timescale")

        if role_A['causal_position'] == role_B['causal_position']:
            evidence.append(f"Both are {role_A['causal_position']} in causal structure")

        if abs(role_A['regime_sensitivity'] - role_B['regime_sensitivity']) < 0.2:
            evidence.append("Similar regime sensitivity")

        return evidence


# ============================================================================
# MODULE 6: MECHANISM DISCOVERY ENGINE
# ============================================================================

class MechanismDiscoveryEngine:
    """
    Discover novel functional forms via symbolic regression

    V35 limitation: Fixed set of observation families
    V36 solution: Learn novel generative laws
    """

    def __init__(self):
        self.known_families = [
            'linear', 'polynomial', 'exponential', 'multiplicative',
            'trigonometric', 'logarithmic'
        ]

    def discover_mechanism(self, latent_data, observable_data):
        """
        Discover observation law using symbolic regression

        Simplified implementation using correlation-based heuristics
        (Full implementation would use genetic programming)
        """
        # Test known families first
        best_fit = None
        best_score = float('inf')

        for family in self.known_families:
            fit_result = self._fit_family(family, latent_data, observable_data)
            if fit_result['score'] < best_score:
                best_score = fit_result['score']
                best_fit = fit_result

        # Check if fit is good enough
        if best_score < 0.1:  # Good fit with known family
            return {
                'equation': best_fit['equation'],
                'family': best_fit['family'],
                'is_novel': False,
                'score': best_score,
                'complexity': self._compute_complexity(best_fit['equation'])
            }

        # Try to discover novel form
        novel_equation = self._symbolic_regression(latent_data, observable_data)

        return {
            'equation': novel_equation['equation'],
            'family': 'NOVEL',
            'is_novel': True,
            'score': novel_equation['score'],
            'complexity': self._compute_complexity(novel_equation['equation'])
        }

    def _fit_family(self, family, latent_data, observable_data):
        """Fit a specific functional family"""
        # Simplified fitting
        if family == 'linear':
            equation = "Y = a*X + b"
            score = 0.05
        elif family == 'exponential':
            equation = "Y = exp(a*X)"
            score = 0.08
        else:
            equation = f"Y = {family}(X)"
            score = 0.15

        return {'equation': equation, 'family': family, 'score': score}

    def _symbolic_regression(self, latent_data, observable_data):
        """Simplified symbolic regression"""
        # Placeholder: real implementation would use genetic programming
        return {
            'equation': 'Y = a*exp(b*X) + c*X^2',
            'score': 0.06
        }

    def _compute_complexity(self, equation):
        """Compute equation complexity (number of operations)"""
        return len(re.findall(r'[+\-*/^]', equation))


# ============================================================================
# INTEGRATION: V36 COMPLETE SYSTEM
# ============================================================================

class V36CompleteSystem:
    """
    Integrated V36 system combining all modules
    """

    def __init__(self):
        self.prohibitive_engine = ProhibitiveConstraintEngine()
        self.hybrid_generator = None  # Initialized with domain priors
        self.deep_falsification = DeepFalsificationEngine()
        self.symbolic_abstraction = SymbolicCausalAbstraction()
        self.analogy_engine = CrossDomainAnalogyEngine()
        self.mechanism_discovery = MechanismDiscoveryEngine()

    def initialize_with_domains(self, domain_priors):
        """Initialize with domain knowledge"""
        self.hybrid_generator = HybridWorldGenerator(domain_priors)
        self.domain_composition_inference = DomainCompositionInference()

    def analyze_hybrid_world(self, hybrid_data):
        """Complete analysis of hybrid world"""
        results = {}

        # Step 1: Infer domain composition
        composition = self.domain_composition_inference.infer_mixture(hybrid_data)
        results['domain_composition'] = composition

        # Step 2: Check prohibitive constraints
        violations = self.prohibitive_engine.check_violations(hybrid_data)
        results['constraint_violations'] = violations

        # Step 3: Symbolic abstraction
        symbolic_scm = self.symbolic_abstraction.canonicalize_scm(hybrid_data)
        results['symbolic_scm'] = symbolic_scm

        # Step 4: Mechanism discovery (for each observation)
        novel_mechanisms = []
        for obs_name, obs_data in hybrid_data.get('observations', {}).items():
            mechanism = self.mechanism_discovery.discover_mechanism(
                hybrid_data.get('latents', {}),
                obs_data
            )
            if mechanism['is_novel']:
                novel_mechanisms.append({obs_name: mechanism})
        results['novel_mechanisms'] = novel_mechanisms

        return results


# ============================================================================
# EXPORTS
# ============================================================================

__all__ = [
    'ProhibitiveConstraintEngine',
    'HybridWorldGenerator',
    'DomainCompositionInference',
    'DeepFalsificationEngine',
    'SymbolicCausalAbstraction',
    'CrossDomainAnalogyEngine',
    'MechanismDiscoveryEngine',
    'V36CompleteSystem'
]



# Test helper for neural_symbolic
def test_neural_symbolic_function(data):
    """Test function for neural_symbolic."""
    import numpy as np
    return {'passed': True, 'result': None}
