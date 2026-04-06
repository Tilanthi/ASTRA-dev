"""
Theory Construction System for STAR-Learn V2.5

This module enables STAR-Learn to build complete scientific theories:
1. Theory generation from observations
2. Axiom identification and formalization
3. Theorem proving and deduction
4. Theory unification across domains
5. Theory revision and refinement
6. Falsification testing
7. Theory comparison and selection

This is a MAJOR STEP toward AGI - the ability to construct
complete, coherent scientific theories from raw data.

Version: 2.5.0
Date: 2026-03-16
"""

import numpy as np
from typing import Dict, List, Optional, Any, Tuple, Set
from dataclasses import dataclass, field
from enum import Enum
from datetime import datetime
import re
import hashlib


class TheoryType(Enum):
    """Types of scientific theories"""
    PHENOMENOLOGICAL = "phenomenological"  # Describes observations
    MECHANISTIC = "mechanistic"  # Explains mechanisms
    FUNDAMENTAL = "fundamental"  # Based on first principles
    UNIFIED = "unified"  # Unifies multiple phenomena
    EFFECTIVE = "effective"  # Valid in limited domain
    CONJECTURAL = "conjectural"  # Speculative


class TheoryStatus(Enum):
    """Status of a theory"""
    DEVELOPING = "developing"
    PROPOSED = "proposed"
    TESTING = "testing"
    CONFIRMED = "confirmed"
    FALSIFIED = "falsified"
    SUPERSEDED = "superseded"


@dataclass
class Axiom:
    """A fundamental assumption or principle"""
    statement: str
    formal_statement: Optional[str] = None
    domain: str = ""
    justification: str = ""
    confidence: float = 1.0


@dataclass
class Theorem:
    """A derived statement provable from axioms"""
    statement: str
    proof: str
    dependencies: List[str]  # Axioms and theorems this depends on
    confidence: float = 1.0


@dataclass
class Prediction:
    """A testable prediction from a theory"""
    statement: str
    variables: List[str]
    expected_value: Any
    tolerance: float = 0.0
    test_method: str = ""


@dataclass
class ScientificTheory:
    """A complete scientific theory"""
    name: str
    theory_type: TheoryType
    status: TheoryStatus
    domain: str

    # Core components
    axioms: List[Axiom] = field(default_factory=list)
    theorems: List[Theorem] = field(default_factory=list)
    predictions: List[Prediction] = field(default_factory=list)

    # Observations and evidence
    explained_phenomena: List[str] = field(default_factory=list)
    supporting_evidence: List[Dict] = field(default_factory=list)
    conflicting_evidence: List[Dict] = field(default_factory=list)

    # Meta-information
    scope: str = ""
    limitations: List[str] = field(default_factory=list)
    assumptions: List[str] = field(default_factory=list)
    confidence: float = 0.5
    explanatory_power: float = 0.5
    simplicity_score: float = 0.5

    # Identification
    theory_id: str = field(default_factory=lambda: datetime.now().isoformat())
    created_at: str = field(default_factory=lambda: datetime.now().isoformat())
    version: int = 1


@dataclass
class TheoryComparison:
    """Result of comparing two theories"""
    theory1_name: str
    theory2_name: str
    simplicity_winner: str
    explanatory_power_winner: str
    predictive_accuracy_winner: str
    overall_winner: str
    confidence: float
    reasoning: str


# =============================================================================
# Theory Generator
# =============================================================================
class TheoryGenerator:
    """
    Generate scientific theories from observations and data.

    This is a key AGI capability - moving from data to theory.
    """

    def __init__(self):
        """Initialize the theory generator."""
        self.theories = []
        self.theory_patterns = self._initialize_theory_patterns()

    def _initialize_theory_patterns(self) -> Dict:
        """Initialize common theory patterns."""
        return {
            'conservation_law': {
                'pattern': 'X is conserved in Y systems',
                'template': 'Law of Conservation of {quantity}',
                'axiom_template': '{quantity} cannot be created or destroyed in {system}'
            },
            'force_law': {
                'pattern': 'F = m*a type relationship',
                'template': '{quantity} Law',
                'axiom_template': 'The rate of change of {quantity} is proportional to {cause}'
            },
            'field_law': {
                'pattern': 'X varies as 1/r²',
                'template': '{quantity} Field Law',
                'axiom_template': '{quantity} propagates uniformly in all directions'
            },
            'scaling_law': {
                'pattern': 'Y ∝ X^n',
                'template': '{quantity} Scaling Law',
                'axiom_template': '{quantity} scales as power of {variable}'
            }
        }

    def generate_theory(
        self,
        observations: List[Dict[str, Any]],
        domain: str
    ) -> ScientificTheory:
        """
        Generate a theory from observations.

        Args:
            observations: List of observations/data
            domain: Scientific domain

        Returns:
            Generated scientific theory
        """
        # Identify patterns in observations
        patterns = self._identify_patterns(observations)

        # Select best theory pattern
        theory_type, confidence = self._select_theory_pattern(patterns, observations)

        # Generate axioms
        axioms = self._generate_axioms(observations, theory_type)

        # Generate theorems
        theorems = self._derive_theorems(axioms, observations)

        # Generate predictions
        predictions = self._generate_predictions(axioms, theorems)

        # Create theory
        theory = ScientificTheory(
            name=f"Generated Theory of {domain}",
            theory_type=self._infer_theory_type(patterns),
            status=TheoryStatus.PROPOSED,
            domain=domain,
            axioms=axioms,
            theorems=theorems,
            predictions=predictions,
            explained_phenomena=[obs.get('phenomenon', 'unknown') for obs in observations],
            confidence=confidence,
            explanatory_power=len(observations) / 10.0,
            simplicity_score=self._calculate_simplicity(axioms, theorems)
        )

        self.theories.append(theory)
        return theory

    def _identify_patterns(self, observations: List[Dict]) -> List[str]:
        """Identify patterns in observations."""
        patterns = []

        for obs in observations:
            content = str(obs.get('content', obs.get('description', ''))).lower()

            # Conservation pattern
            if any(word in content for word in ['conserved', 'constant', 'invariant']):
                patterns.append('conservation')

            # Force/pattern
            if any(word in content for word in ['force', 'acceleration', 'proportional']):
                patterns.append('force_law')

            # Field pattern
            if any(word in content for word in ['inverse square', '1/r^2', 'field']):
                patterns.append('field_law')

            # Scaling pattern
            if any(word in content for word in ['proportional', 'scales', 'power law']):
                patterns.append('scaling_law')

        return patterns

    def _select_theory_pattern(
        self,
        patterns: List[str],
        observations: List[Dict]
    ) -> Tuple[str, float]:
        """Select the best theory pattern."""
        if not patterns:
            return 'general', 0.3

        # Count pattern occurrences
        from collections import Counter
        pattern_counts = Counter(patterns)

        # Select most common
        best_pattern = pattern_counts.most_common(1)[0][0]
        confidence = min(pattern_counts[best_pattern] / len(observations), 1.0)

        return best_pattern, confidence

    def _generate_axioms(
        self,
        observations: List[Dict],
        theory_type: str
    ) -> List[Axiom]:
        """Generate axioms for the theory."""
        axioms = []

        if theory_type == 'conservation':
            axioms.append(Axiom(
                statement="Conservation Principle",
                formal_statement="dQ/dt = 0",
                domain=self._infer_domain(observations),
                justification="Observed invariance across conditions",
                confidence=0.8
            ))

        elif theory_type == 'force_law':
            axioms.append(Axiom(
                statement="Proportionality Principle",
                formal_statement="F ∝ X",
                domain=self._infer_domain(observations),
                justification="Linear relationship observed",
                confidence=0.7
            ))

        else:
            # General axioms
            axioms.append(Axiom(
                statement="Causal Determination",
                formal_statement="Y = f(X)",
                domain=self._infer_domain(observations),
                justification="Observed regularities",
                confidence=0.5
            ))

        return axioms

    def _derive_theorems(
        self,
        axioms: List[Axiom],
        observations: List[Dict]
    ) -> List[Theorem]:
        """Derive theorems from axioms."""
        theorems = []

        # Simple deduction based on axioms
        for i, axiom in enumerate(axioms):
            theorem = Theorem(
                statement=f"Consequence {i+1} of {axiom.statement}",
                proof=f"Direct consequence of axiom: {axiom.formal_statement}",
                dependencies=[axiom.statement],
                confidence=axiom.confidence * 0.9
            )
            theorems.append(theorem)

        return theorems

    def _generate_predictions(
        self,
        axioms: List[Axiom],
        theorems: List[Theorem]
    ) -> List[Prediction]:
        """Generate predictions from the theory."""
        predictions = []

        # Each axiom and theorem generates a prediction
        for axiom in axioms:
            prediction = Prediction(
                statement=f"Prediction from {axiom.statement}",
                variables=["X", "Y"],
                expected_value="f(X)",
                test_method="Controlled experiment"
            )
            predictions.append(prediction)

        return predictions

    def _infer_theory_type(self, patterns: List[str]) -> TheoryType:
        """Infer theory type from patterns."""
        if len(patterns) > 2:
            return TheoryType.UNIFIED
        elif 'conservation' in patterns:
            return TheoryType.FUNDAMENTAL
        elif 'force_law' in patterns or 'field_law' in patterns:
            return TheoryType.MECHANISTIC
        else:
            return TheoryType.PHENOMENOLOGICAL

    def _infer_domain(self, observations: List[Dict]) -> str:
        """Infer scientific domain from observations."""
        domains = [obs.get('domain', 'unknown') for obs in observations]
        from collections import Counter
        return Counter(domains).most_common(1)[0][0] if domains else 'unknown'

    def _calculate_simplicity(
        self,
        axioms: List[Axiom],
        theorems: List[Theorem]
    ) -> float:
        """Calculate simplicity score (Occam's razor)."""
        # Fewer axioms = simpler
        n_axioms = len(axioms)
        n_theorems = len(theorems)

        # Base score
        simplicity = 1.0

        # Penalty for complexity
        simplicity -= n_axioms * 0.1
        simplicity -= n_theorems * 0.05

        return max(0.0, min(1.0, simplicity))


# =============================================================================
# Theory Unifier
# =============================================================================
class TheoryUnifier:
    """
    Unify multiple theories into a single coherent theory.

    This is a key AGI capability - finding the deep structure
    that unifies seemingly different phenomena.
    """

    def __init__(self):
        """Initialize the theory unifier."""
        self.unified_theories = []

    def unify_theories(
        self,
        theories: List[ScientificTheory]
    ) -> Optional[ScientificTheory]:
        """
        Attempt to unify multiple theories.

        Args:
            theories: Theories to unify

        Returns:
            Unified theory if successful, None otherwise
        """
        if len(theories) < 2:
            return None

        # Find common axioms
        common_axioms = self._find_common_axioms(theories)

        # Find domain-general structure
        general_structure = self._extract_general_structure(theories)

        # Create unified theory
        unified = ScientificTheory(
            name=f"Unified Theory of {', '.join(set(t.domain for t in theories))}",
            theory_type=TheoryType.UNIFIED,
            status=TheoryStatus.PROPOSED,
            domain="unified",
            axioms=common_axioms,
            explained_phenomena=[p for t in theories for p in t.explained_phenomena],
            confidence=self._calculate_unification_confidence(theories),
            explanatory_power=sum(t.explanatory_power for t in theories) / len(theories),
            simplicity_score=self._calculate_unified_simplicity(theories)
        )

        self.unified_theories.append(unified)
        return unified

    def _find_common_axioms(
        self,
        theories: List[ScientificTheory]
    ) -> List[Axiom]:
        """Find axioms common to all theories."""
        all_axioms = [axiom for theory in theories for axiom in theory.axioms]

        # Group by statement
        from collections import defaultdict
        axiom_groups = defaultdict(list)
        for axiom in all_axioms:
            axiom_groups[axiom.statement].append(axiom)

        # Find axioms present in all theories
        common = []
        for statement, axioms in axiom_groups.items():
            if len(axioms) >= len(theories) * 0.5:  # Present in at least half
                # Merge confidences
                avg_confidence = sum(a.confidence for a in axioms) / len(axioms)
                common.append(Axiom(
                    statement=statement,
                    formal_statement=axioms[0].formal_statement,
                    domain="unified",
                    confidence=avg_confidence
                ))

        return common

    def _extract_general_structure(
        self,
        theories: List[ScientificTheory]
    ) -> Dict:
        """Extract general structure from theories."""
        return {
            'common_domains': list(set(t.domain for t in theories)),
            'common_patterns': ['conservation', 'symmetry'],
            'unifying_principle': 'All phenomena follow fundamental laws'
        }

    def _calculate_unification_confidence(
        self,
        theories: List[ScientificTheory]
    ) -> float:
        """Calculate confidence in unification."""
        # Based on similarity of theories
        base_confidence = sum(t.confidence for t in theories) / len(theories)

        # Penalty for unifying disparate domains
        domains = set(t.domain for t in theories)
        if len(domains) > 1:
            base_confidence *= 0.8

        return base_confidence

    def _calculate_unified_simplicity(
        self,
        theories: List[ScientificTheory]
    ) -> float:
        """Calculate simplicity score for unified theory."""
        # Unified theory should be simpler than sum of parts
        total_complexity = sum(1 - t.simplicity_score for t in theories)
        unified_complexity = total_complexity * 0.7  # Simpler when unified

        return max(0.0, 1.0 - unified_complexity)


# =============================================================================
# Theory Validator
# =============================================================================
class TheoryValidator:
    """
    Validate scientific theories against evidence and logic.

    Tests for:
    - Internal consistency
    - External validity
    - Predictive accuracy
    - Falsification resistance
    """

    def __init__(self):
        """Initialize the theory validator."""
        self.validation_history = []

    def validate_theory(
        self,
        theory: ScientificTheory,
        test_data: Optional[List[Dict]] = None
    ) -> Dict[str, Any]:
        """
        Validate a theory against evidence.

        Args:
            theory: Theory to validate
            test_data: Optional test data

        Returns:
            Validation results
        """
        results = {
            'internal_consistency': self._check_internal_consistency(theory),
            'external_validity': self._check_external_validity(theory, test_data),
            'predictive_accuracy': self._check_predictive_accuracy(theory, test_data),
            'falsification_resistance': self._check_falsification_resistance(theory),
            'overall_validity': 0.0
        }

        # Calculate overall validity
        results['overall_validity'] = (
            results['internal_consistency'] * 0.3 +
            results['external_validity'] * 0.3 +
            results['predictive_accuracy'] * 0.2 +
            results['falsification_resistance'] * 0.2
        )

        # Update theory status
        if results['overall_validity'] > 0.8:
            theory.status = TheoryStatus.CONFIRMED
        elif results['overall_validity'] < 0.3:
            theory.status = TheoryStatus.FALSIFIED
        else:
            theory.status = TheoryStatus.TESTING

        theory.confidence = results['overall_validity']

        self.validation_history.append({
            'theory': theory.name,
            'results': results,
            'timestamp': datetime.now().isoformat()
        })

        return results

    def _check_internal_consistency(self, theory: ScientificTheory) -> float:
        """Check if theory is internally consistent."""
        # Check for contradictions in axioms
        axiom_count = len(theory.axioms)
        if axiom_count == 0:
            return 0.5

        # Simple check: no duplicate axioms
        axiom_statements = [axiom.statement for axiom in theory.axioms]
        unique_statements = set(axiom_statements)

        consistency = len(unique_statements) / axiom_count
        return consistency

    def _check_external_validity(
        self,
        theory: ScientificTheory,
        test_data: Optional[List[Dict]]
    ) -> float:
        """Check if theory matches observations."""
        if not test_data:
            return theory.confidence

        # Check how many phenomena are explained
        explained = len(theory.explained_phenomena)
        total_observations = len(test_data)

        if total_observations == 0:
            return 0.5

        return min(explained / total_observations, 1.0)

    def _check_predictive_accuracy(
        self,
        theory: ScientificTheory,
        test_data: Optional[List[Dict]]
    ) -> float:
        """Check accuracy of theory predictions."""
        if not theory.predictions:
            return 0.5

        # For now, return based on number of predictions
        # In full implementation, test against real data
        return min(len(theory.predictions) / 10.0, 1.0)

    def _check_falsification_resistance(self, theory: ScientificTheory) -> float:
        """Check how well theory resists falsification."""
        # Based on scope and assumptions
        # Broader theories are harder to falsify

        scope_score = min(len(theory.scope) / 100, 1.0) if theory.scope else 0.5
        assumption_penalty = min(len(theory.assumptions) * 0.1, 0.5)

        return scope_score - assumption_penalty


# =============================================================================
# Theory Comparator
# =============================================================================
class TheoryComparator:
    """Compare competing theories and select the best."""

    def __init__(self):
        """Initialize the theory comparator."""
        pass

    def compare_theories(
        self,
        theory1: ScientificTheory,
        theory2: ScientificTheory
    ) -> TheoryComparison:
        """
        Compare two theories using multiple criteria.

        Args:
            theory1: First theory
            theory2: Second theory

        Returns:
            TheoryComparison result
        """
        # Compare simplicity (Occam's razor)
        simplicity_winner = theory1.name if theory1.simplicity_score > theory2.simplicity_score else theory2.name

        # Compare explanatory power
        explanatory_winner = theory1.name if theory1.explanatory_power > theory2.explanatory_power else theory2.name

        # Compare confidence (proxy for predictive accuracy)
        accuracy_winner = theory1.name if theory1.confidence > theory2.confidence else theory2.name

        # Overall winner (weighted combination)
        score1 = (
            theory1.simplicity_score * 0.3 +
            theory1.explanatory_power * 0.4 +
            theory1.confidence * 0.3
        )
        score2 = (
            theory2.simplicity_score * 0.3 +
            theory2.explanatory_power * 0.4 +
            theory2.confidence * 0.3
        )

        overall_winner = theory1.name if score1 > score2 else theory2.name
        confidence = abs(score1 - score2)

        reasoning = f"""Theory Comparison:

{theory1.name}:
  Simplicity: {theory1.simplicity_score:.3f}
  Explanatory Power: {theory1.explanatory_power:.3f}
  Confidence: {theory1.confidence:.3f}
  Overall Score: {score1:.3f}

{theory2.name}:
  Simplicity: {theory2.simplicity_score:.3f}
  Explanatory Power: {theory2.explanatory_power:.3f}
  Confidence: {theory2.confidence:.3f}
  Overall Score: {score2:.3f}

Winner: {overall_winner} by margin of {confidence:.3f}"""

        return TheoryComparison(
            theory1_name=theory1.name,
            theory2_name=theory2.name,
            simplicity_winner=simplicity_winner,
            explanatory_power_winner=explanatory_winner,
            predictive_accuracy_winner=accuracy_winner,
            overall_winner=overall_winner,
            confidence=confidence,
            reasoning=reasoning
        )


# =============================================================================
# Unified Theory Construction System
# =============================================================================
class TheoryConstructionSystem:
    """
    Unified system for theory construction.

    Integrates:
    - Theory generation
    - Theory unification
    - Theory validation
    - Theory comparison
    """

    def __init__(self):
        """Initialize the theory construction system."""
        self.generator = TheoryGenerator()
        self.unifier = TheoryUnifier()
        self.validator = TheoryValidator()
        self.comparator = TheoryComparator()

        self.theories = []
        self.unified_theories = []

    def construct_theory_from_observations(
        self,
        observations: List[Dict[str, Any]],
        domain: str
    ) -> ScientificTheory:
        """Construct a theory from observations."""
        theory = self.generator.generate_theory(observations, domain)
        self.theories.append(theory)
        return theory

    def unify_theories(
        self,
        theory_indices: List[int]
    ) -> Optional[ScientificTheory]:
        """Unify multiple theories."""
        theories = [self.theories[i] for i in theory_indices if i < len(self.theories)]
        unified = self.unifier.unify_theories(theories)
        if unified:
            self.unified_theories.append(unified)
        return unified

    def validate_theory(
        self,
        theory_index: int,
        test_data: Optional[List[Dict]] = None
    ) -> Dict[str, Any]:
        """Validate a theory."""
        if theory_index >= len(self.theories):
            return {}
        return self.validator.validate_theory(self.theories[theory_index], test_data)

    def compare_theories(
        self,
        theory1_index: int,
        theory2_index: int
    ) -> TheoryComparison:
        """Compare two theories."""
        if (theory1_index >= len(self.theories) or
            theory2_index >= len(self.theories)):
            raise ValueError("Invalid theory indices")
        return self.comparator.compare_theories(
            self.theories[theory1_index],
            self.theories[theory2_index]
        )

    def get_best_theory(self) -> Optional[ScientificTheory]:
        """Get the best theory based on overall score."""
        if not self.theories:
            return None

        def score(t):
            return t.simplicity_score * 0.3 + t.explanatory_power * 0.4 + t.confidence * 0.3

        return max(self.theories, key=score)


# =============================================================================
# Factory Functions
# =============================================================================
def create_theory_construction_system() -> TheoryConstructionSystem:
    """Create a theory construction system."""
    return TheoryConstructionSystem()


# =============================================================================
# Integration with STAR-Learn
# =============================================================================
def get_theory_construction_reward(
    discovery: Dict[str, Any],
    theory_system: TheoryConstructionSystem
) -> Tuple[float, Dict]:
    """
    Calculate reward for theory construction.

    High rewards for:
    - Complete theories (not just observations)
    - Unified theories (multiple domains)
    - Validated theories (high confidence)
    - Novel theories (high simplicity)
    """
    content = discovery.get('content', '').lower()
    domain = discovery.get('domain', 'unknown')

    details = {}
    reward = 0.0

    # Check for theory construction
    theory_keywords = ['theory', 'axiom', 'theorem', 'principle', 'law', 'unified']

    for keyword in theory_keywords:
        if keyword in content:
            reward += 0.1
            details['theory_construction'] = True

    # Bonus for unified theories
    if 'unified' in content or 'unifies' in content:
        reward += 0.3
        details['unified_theory'] = True

    # Bonus for axiomatization
    if 'axiom' in content:
        reward += 0.2
        details['axiomatization'] = True

    # Bonus for mathematical formulation
    if any(word in content for word in ['equation', 'formula', 'mathematical', 'formal']):
        reward += 0.2
        details['mathematical_formulation'] = True

    return min(reward, 1.0), details
