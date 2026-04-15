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
Theory Synthesis Module for STAN V41

Composes discovered patterns, laws, and relationships into unified theories.
Implements hierarchical law discovery, consistency checking, and theory unification.

Key capabilities:
- Pattern-to-Law promotion: Recurring patterns become candidate laws
- Hierarchical theory construction: Laws combine into theories
- Consistency checking: Detect contradictions across discovered rules
- Theory unification: Merge compatible theories
- Predictive extension: Generate novel predictions from theories
"""

from dataclasses import dataclass, field
from typing import Dict, List, Set, Optional, Any, Callable, Tuple
from enum import Enum, auto
from datetime import datetime
import uuid
import math
from collections import defaultdict


class PatternType(Enum):
    """Types of discovered patterns"""
    CORRELATION = auto()      # Statistical association
    CAUSAL = auto()           # Cause-effect relationship
    TEMPORAL = auto()         # Time-ordered sequence
    STRUCTURAL = auto()       # Organizational pattern
    FUNCTIONAL = auto()       # Input-output relationship
    INVARIANT = auto()        # Conserved quantity
    SYMMETRY = auto()         # Transformation invariance
    SCALING = auto()          # Power-law relationship
    PERIODIC = auto()         # Cyclic pattern
    THRESHOLD = auto()        # Phase transition


class LawStatus(Enum):
    """Status of a discovered law"""
    HYPOTHETICAL = auto()     # Newly proposed
    CANDIDATE = auto()        # Passed initial tests
    VALIDATED = auto()        # Strong empirical support
    ESTABLISHED = auto()      # Widely confirmed
    SUPERSEDED = auto()       # Replaced by better law
    REFUTED = auto()          # Contradicted by evidence


class TheoryStatus(Enum):
    """Status of a theory"""
    NASCENT = auto()          # Just formed
    DEVELOPING = auto()       # Accumulating laws
    MATURE = auto()           # Stable set of laws
    COMPETING = auto()        # Rival theories exist
    UNIFIED = auto()          # Merged with other theory
    ABANDONED = auto()        # No longer viable


class ConsistencyLevel(Enum):
    """Level of consistency between elements"""
    CONSISTENT = auto()       # No conflicts
    COMPATIBLE = auto()       # Consistent under conditions
    INDEPENDENT = auto()      # No logical connection
    TENSION = auto()          # Minor conflicts
    CONTRADICTORY = auto()    # Direct contradiction


@dataclass
class Pattern:
    """A discovered pattern in data or phenomena"""
    pattern_id: str
    pattern_type: PatternType
    description: str

    # Pattern specification
    variables: List[str]                # Variables involved
    relationship: str                   # Mathematical/logical form
    conditions: List[str]               # When pattern holds

    # Evidence
    observations: int = 0               # Supporting observations
    domains: List[str] = field(default_factory=list)  # Where observed
    confidence: float = 0.5

    # Metadata
    discovered_at: datetime = field(default_factory=datetime.now)
    source_module: str = ""

    def __post_init__(self):
        if not self.pattern_id:
            self.pattern_id = f"PAT-{uuid.uuid4().hex[:8]}"


@dataclass
class Law:
    """A proposed scientific law derived from patterns"""
    law_id: str
    name: str
    status: LawStatus

    # Formal specification
    statement: str                      # Verbal statement
    mathematical_form: Optional[str]    # Equation if applicable
    variables: Dict[str, str]           # Variable: Description
    constants: Dict[str, float]         # Named constants

    # Scope and conditions
    domain: str                         # Primary domain
    boundary_conditions: List[str]      # When law applies
    exceptions: List[str]               # Known exceptions

    # Provenance
    source_patterns: List[str]          # Pattern IDs that led to law
    derivation: str                     # How law was derived

    # Validation
    predictions_made: int = 0
    predictions_confirmed: int = 0
    confirmations: List[str] = field(default_factory=list)
    falsifications: List[str] = field(default_factory=list)

    # Metrics
    generality: float = 0.5             # Breadth of applicability
    precision: float = 0.5              # Quantitative accuracy
    simplicity: float = 0.5             # Occam score

    created_at: datetime = field(default_factory=datetime.now)
    last_updated: datetime = field(default_factory=datetime.now)

    def __post_init__(self):
        if not self.law_id:
            self.law_id = f"LAW-{uuid.uuid4().hex[:8]}"

    @property
    def confirmation_rate(self) -> float:
        if self.predictions_made == 0:
            return 0.0
        return self.predictions_confirmed / self.predictions_made

    @property
    def composite_score(self) -> float:
        """Overall quality score"""
        return (
            0.4 * self.confirmation_rate +
            0.25 * self.generality +
            0.2 * self.precision +
            0.15 * self.simplicity
        )


@dataclass
class Theory:
    """A coherent set of laws explaining a domain"""
    theory_id: str
    name: str
    status: TheoryStatus

    # Core content
    description: str
    domain: str                         # Primary explanatory domain
    core_laws: List[str]                # Law IDs - fundamental
    auxiliary_laws: List[str]           # Law IDs - supporting

    # Theoretical structure
    axioms: List[str]                   # Foundational assumptions
    definitions: Dict[str, str]         # Key terms defined
    ontology: Dict[str, List[str]]      # Entity types and relations

    # Explanatory power
    phenomena_explained: List[str]
    predictions: List[str]              # Novel predictions
    unifications: List[str]             # Connections made

    # Competitors and relations
    competing_theories: List[str]       # Theory IDs
    subsumed_theories: List[str]        # Theories this replaces
    parent_theory: Optional[str] = None # If this is a sub-theory

    # Metrics
    coherence: float = 0.5              # Internal consistency
    coverage: float = 0.5               # Phenomena explained
    parsimony: float = 0.5              # Simplicity
    fertility: float = 0.5              # New predictions enabled

    created_at: datetime = field(default_factory=datetime.now)
    last_updated: datetime = field(default_factory=datetime.now)

    def __post_init__(self):
        if not self.theory_id:
            self.theory_id = f"THY-{uuid.uuid4().hex[:8]}"

    @property
    def composite_score(self) -> float:
        """Overall theory quality"""
        return (
            0.3 * self.coherence +
            0.25 * self.coverage +
            0.25 * self.fertility +
            0.2 * self.parsimony
        )


@dataclass
class ConsistencyReport:
    """Report on consistency between laws or theories"""
    element1_id: str
    element2_id: str
    level: ConsistencyLevel

    # Details
    conflicts: List[str]                # Specific conflicts found
    resolutions: List[str]              # Possible resolutions
    conditions_for_compatibility: List[str]

    # Analysis
    conflict_severity: float = 0.0      # 0 = none, 1 = fatal
    resolution_difficulty: float = 0.5

    analyzed_at: datetime = field(default_factory=datetime.now)


@dataclass
class Prediction:
    """A prediction derived from a theory"""
    prediction_id: str
    source_theory: str                  # Theory ID
    source_laws: List[str]              # Law IDs used

    # Prediction content
    statement: str
    quantitative_form: Optional[str]    # Mathematical prediction
    predicted_value: Optional[float]
    uncertainty: Optional[float]

    # Testability
    test_conditions: List[str]
    required_observations: List[str]
    falsification_criteria: str

    # Status
    is_novel: bool = True               # Not used in theory construction
    is_tested: bool = False
    is_confirmed: Optional[bool] = None
    observed_value: Optional[float] = None

    created_at: datetime = field(default_factory=datetime.now)

    def __post_init__(self):
        if not self.prediction_id:
            self.prediction_id = f"PRD-{uuid.uuid4().hex[:8]}"


class PatternToLawPromoter:
    """Promotes recurring patterns to candidate laws"""

    def __init__(self, min_observations: int = 5, min_confidence: float = 0.7):
        self.min_observations = min_observations
        self.min_confidence = min_confidence

    def evaluate_pattern(self, pattern: Pattern) -> Tuple[bool, float, str]:
        """
        Evaluate if pattern should be promoted to law.
        Returns: (should_promote, score, rationale)
        """
        score = 0.0
        factors = []

        # Observation count
        obs_score = min(1.0, pattern.observations / (self.min_observations * 2))
        score += 0.3 * obs_score
        factors.append(f"Observations: {pattern.observations} (score: {obs_score:.2f})")

        # Confidence
        conf_score = pattern.confidence
        score += 0.3 * conf_score
        factors.append(f"Confidence: {pattern.confidence:.2f}")

        # Domain generality
        domain_score = min(1.0, len(pattern.domains) / 3)
        score += 0.2 * domain_score
        factors.append(f"Domains: {len(pattern.domains)} (score: {domain_score:.2f})")

        # Pattern type bonus
        type_bonus = {
            PatternType.INVARIANT: 0.2,
            PatternType.CAUSAL: 0.15,
            PatternType.SCALING: 0.1,
            PatternType.SYMMETRY: 0.15,
        }.get(pattern.pattern_type, 0.05)
        score += type_bonus
        factors.append(f"Type bonus: {type_bonus:.2f}")

        should_promote = (
            pattern.observations >= self.min_observations and
            pattern.confidence >= self.min_confidence and
            score >= 0.6
        )

        rationale = "; ".join(factors)
        return should_promote, score, rationale

    def promote_to_law(self, pattern: Pattern, name: str = None) -> Law:
        """Convert a pattern to a candidate law"""
        return Law(
            law_id="",
            name=name or f"Law of {pattern.description[:30]}",
            status=LawStatus.CANDIDATE,
            statement=f"Under conditions {pattern.conditions}, {pattern.relationship}",
            mathematical_form=pattern.relationship if self._is_mathematical(pattern.relationship) else None,
            variables={v: f"Variable {v}" for v in pattern.variables},
            constants={},
            domain=pattern.domains[0] if pattern.domains else "general",
            boundary_conditions=pattern.conditions,
            exceptions=[],
            source_patterns=[pattern.pattern_id],
            derivation=f"Promoted from pattern {pattern.pattern_id} with {pattern.observations} observations",
            predictions_made=0,
            predictions_confirmed=0,
            generality=min(1.0, len(pattern.domains) / 5),
            precision=pattern.confidence,
            simplicity=self._estimate_simplicity(pattern.relationship)
        )

    def _is_mathematical(self, relationship: str) -> bool:
        """Check if relationship is mathematical"""
        math_indicators = ['=', '∝', '~', '<', '>', '+', '-', '*', '/', '^']
        return any(ind in relationship for ind in math_indicators)

    def _estimate_simplicity(self, relationship: str) -> float:
        """Estimate simplicity based on complexity of relationship"""
        # Count operators and terms as complexity measure
        complexity = len(relationship.split()) + relationship.count('(')
        return max(0.1, 1.0 - complexity / 20)


class LawToTheoryComposer:
    """Composes related laws into unified theories"""

    def __init__(self):
        self.laws: Dict[str, Law] = {}
        self.theories: Dict[str, Theory] = {}

    def add_law(self, law: Law):
        """Add a law to the composer"""
        self.laws[law.law_id] = law

    def find_related_laws(self, law: Law, min_similarity: float = 0.3) -> List[Tuple[str, float]]:
        """Find laws related to the given law"""
        related = []

        for other_id, other in self.laws.items():
            if other_id == law.law_id:
                continue

            similarity = self._compute_law_similarity(law, other)
            if similarity >= min_similarity:
                related.append((other_id, similarity))

        return sorted(related, key=lambda x: x[1], reverse=True)

    def _compute_law_similarity(self, law1: Law, law2: Law) -> float:
        """Compute similarity between two laws"""
        score = 0.0

        # Domain overlap
        if law1.domain == law2.domain:
            score += 0.3

        # Variable overlap
        vars1 = set(law1.variables.keys())
        vars2 = set(law2.variables.keys())
        if vars1 and vars2:
            overlap = len(vars1 & vars2) / len(vars1 | vars2)
            score += 0.4 * overlap

        # Pattern source overlap
        pats1 = set(law1.source_patterns)
        pats2 = set(law2.source_patterns)
        if pats1 and pats2:
            pat_overlap = len(pats1 & pats2) / len(pats1 | pats2)
            score += 0.3 * pat_overlap

        return score

    def compose_theory(
        self,
        core_law_ids: List[str],
        name: str,
        domain: str,
        description: str
    ) -> Theory:
        """Compose a theory from a set of core laws"""
        core_laws = [self.laws[lid] for lid in core_law_ids if lid in self.laws]

        # Collect variables and build ontology
        all_variables = {}
        for law in core_laws:
            all_variables.update(law.variables)

        # Identify auxiliary laws (related but not core)
        auxiliary_ids = set()
        for law in core_laws:
            related = self.find_related_laws(law, min_similarity=0.4)
            for rel_id, _ in related:
                if rel_id not in core_law_ids:
                    auxiliary_ids.add(rel_id)

        # Build axioms from core laws
        axioms = [law.statement for law in core_laws if law.status in
                  [LawStatus.ESTABLISHED, LawStatus.VALIDATED]]

        # Compute metrics
        coherence = self._compute_coherence(core_laws)
        coverage = self._estimate_coverage(core_laws, domain)

        theory = Theory(
            theory_id="",
            name=name,
            status=TheoryStatus.NASCENT,
            description=description,
            domain=domain,
            core_laws=core_law_ids,
            auxiliary_laws=list(auxiliary_ids),
            axioms=axioms,
            definitions=all_variables,
            ontology={domain: list(all_variables.keys())},
            phenomena_explained=[],
            predictions=[],
            unifications=[],
            competing_theories=[],
            subsumed_theories=[],
            coherence=coherence,
            coverage=coverage,
            parsimony=self._estimate_parsimony(core_laws),
            fertility=0.5  # Initial estimate
        )

        self.theories[theory.theory_id] = theory
        return theory

    def _compute_coherence(self, laws: List[Law]) -> float:
        """Compute internal coherence of law set"""
        if len(laws) < 2:
            return 1.0

        # Check for contradictions
        total_pairs = len(laws) * (len(laws) - 1) / 2
        compatible_pairs = 0

        for i, law1 in enumerate(laws):
            for law2 in laws[i+1:]:
                if self._are_compatible(law1, law2):
                    compatible_pairs += 1

        return compatible_pairs / total_pairs if total_pairs > 0 else 1.0

    def _are_compatible(self, law1: Law, law2: Law) -> bool:
        """Check if two laws are logically compatible"""
        # Simple heuristic: same domain but different predictions = potential conflict
        if law1.domain == law2.domain:
            shared_vars = set(law1.variables.keys()) & set(law2.variables.keys())
            if shared_vars:
                # If both have mathematical forms, check for contradiction
                if law1.mathematical_form and law2.mathematical_form:
                    # Simplified: assume compatible unless obviously contradictory
                    return True
        return True

    def _estimate_coverage(self, laws: List[Law], domain: str) -> float:
        """Estimate phenomena coverage"""
        # Based on number of validated laws and their generality
        if not laws:
            return 0.0

        validated = [l for l in laws if l.status in [LawStatus.VALIDATED, LawStatus.ESTABLISHED]]
        coverage = sum(l.generality for l in validated) / len(laws)
        return min(1.0, coverage)

    def _estimate_parsimony(self, laws: List[Law]) -> float:
        """Estimate theory parsimony"""
        if not laws:
            return 1.0
        return sum(l.simplicity for l in laws) / len(laws)


class ConsistencyChecker:
    """Checks consistency between laws and theories"""

    def __init__(self):
        self.laws: Dict[str, Law] = {}
        self.theories: Dict[str, Theory] = {}

    def check_law_consistency(self, law1: Law, law2: Law) -> ConsistencyReport:
        """Check consistency between two laws"""
        conflicts = []
        resolutions = []

        # Check domain conflict
        if law1.domain == law2.domain:
            # Same domain - check for contradictions
            shared_vars = set(law1.variables.keys()) & set(law2.variables.keys())

            if shared_vars:
                # Check if mathematical forms contradict
                if law1.mathematical_form and law2.mathematical_form:
                    if self._forms_contradict(law1.mathematical_form, law2.mathematical_form):
                        conflicts.append(f"Mathematical forms may contradict for variables {shared_vars}")
                        resolutions.append("Identify boundary conditions where each applies")

                # Check boundary conditions
                boundary_conflict = self._check_boundary_conflict(
                    law1.boundary_conditions, law2.boundary_conditions
                )
                if boundary_conflict:
                    conflicts.append(boundary_conflict)

        # Check exceptions
        for exc in law1.exceptions:
            if exc in law2.boundary_conditions:
                conflicts.append(f"Law1 exception '{exc}' is Law2 boundary condition")
                resolutions.append("Clarify scope of each law")

        # Determine consistency level
        if not conflicts:
            level = ConsistencyLevel.CONSISTENT
            severity = 0.0
        elif all("may" in c or "potential" in c for c in conflicts):
            level = ConsistencyLevel.TENSION
            severity = 0.3
        else:
            level = ConsistencyLevel.CONTRADICTORY
            severity = 0.8

        return ConsistencyReport(
            element1_id=law1.law_id,
            element2_id=law2.law_id,
            level=level,
            conflicts=conflicts,
            resolutions=resolutions,
            conditions_for_compatibility=law1.boundary_conditions + law2.boundary_conditions,
            conflict_severity=severity,
            resolution_difficulty=severity * 0.8
        )

    def check_theory_consistency(self, theory1: Theory, theory2: Theory) -> ConsistencyReport:
        """Check consistency between two theories"""
        conflicts = []
        resolutions = []

        # Check axiom conflicts
        for ax1 in theory1.axioms:
            for ax2 in theory2.axioms:
                if self._axioms_conflict(ax1, ax2):
                    conflicts.append(f"Axiom conflict: '{ax1[:50]}' vs '{ax2[:50]}'")
                    resolutions.append("Identify meta-level reconciliation")

        # Check ontology conflicts
        shared_entities = set(theory1.ontology.keys()) & set(theory2.ontology.keys())
        for entity in shared_entities:
            props1 = set(theory1.ontology[entity])
            props2 = set(theory2.ontology[entity])
            if props1 != props2:
                conflicts.append(f"Different properties for {entity}: {props1} vs {props2}")
                resolutions.append(f"Unify {entity} definition")

        # Determine level
        if not conflicts:
            level = ConsistencyLevel.CONSISTENT
            severity = 0.0
        elif len(conflicts) <= 2:
            level = ConsistencyLevel.TENSION
            severity = 0.4
        else:
            level = ConsistencyLevel.CONTRADICTORY
            severity = 0.9

        return ConsistencyReport(
            element1_id=theory1.theory_id,
            element2_id=theory2.theory_id,
            level=level,
            conflicts=conflicts,
            resolutions=resolutions,
            conditions_for_compatibility=[],
            conflict_severity=severity,
            resolution_difficulty=severity
        )

    def _forms_contradict(self, form1: str, form2: str) -> bool:
        """Check if two mathematical forms contradict"""
        # Simplified heuristic
        # In real implementation, would use symbolic math
        return False

    def _check_boundary_conflict(self, bounds1: List[str], bounds2: List[str]) -> Optional[str]:
        """Check for conflicting boundary conditions"""
        for b1 in bounds1:
            for b2 in bounds2:
                # Simple negation check
                if b1.startswith("not ") and b1[4:] == b2:
                    return f"Conflicting boundaries: '{b1}' vs '{b2}'"
                if b2.startswith("not ") and b2[4:] == b1:
                    return f"Conflicting boundaries: '{b1}' vs '{b2}'"
        return None

    def _axioms_conflict(self, ax1: str, ax2: str) -> bool:
        """Check if two axioms conflict"""
        # Simple negation check
        ax1_lower = ax1.lower()
        ax2_lower = ax2.lower()

        negations = [
            ("always", "never"),
            ("all", "no"),
            ("increases", "decreases"),
            ("positive", "negative")
        ]

        for pos, neg in negations:
            if pos in ax1_lower and neg in ax2_lower:
                return True
            if neg in ax1_lower and pos in ax2_lower:
                return True

        return False


class TheoryUnifier:
    """Unifies compatible theories into more general frameworks"""

    def __init__(self, consistency_checker: ConsistencyChecker):
        self.consistency_checker = consistency_checker
        self.theories: Dict[str, Theory] = {}

    def evaluate_unification_potential(
        self,
        theory1: Theory,
        theory2: Theory
    ) -> Tuple[float, List[str], List[str]]:
        """
        Evaluate if two theories can be unified.
        Returns: (unification_score, shared_concepts, obstacles)
        """
        # Check consistency
        report = self.consistency_checker.check_theory_consistency(theory1, theory2)

        if report.level == ConsistencyLevel.CONTRADICTORY:
            return 0.0, [], ["Fundamental contradiction: " + "; ".join(report.conflicts)]

        # Find shared concepts
        shared_laws = set(theory1.core_laws) & set(theory2.core_laws)
        shared_aux = set(theory1.auxiliary_laws) & set(theory2.auxiliary_laws)
        shared_entities = set(theory1.ontology.keys()) & set(theory2.ontology.keys())

        shared_concepts = [
            f"Shared laws: {len(shared_laws)}",
            f"Shared auxiliary: {len(shared_aux)}",
            f"Shared entities: {list(shared_entities)}"
        ]

        # Compute unification score
        law_overlap = len(shared_laws) / max(len(theory1.core_laws), len(theory2.core_laws), 1)
        entity_overlap = len(shared_entities) / max(len(theory1.ontology), len(theory2.ontology), 1)

        consistency_factor = {
            ConsistencyLevel.CONSISTENT: 1.0,
            ConsistencyLevel.COMPATIBLE: 0.9,
            ConsistencyLevel.INDEPENDENT: 0.5,
            ConsistencyLevel.TENSION: 0.3,
            ConsistencyLevel.CONTRADICTORY: 0.0
        }[report.level]

        score = (0.4 * law_overlap + 0.3 * entity_overlap + 0.3 * consistency_factor)

        obstacles = report.conflicts if report.conflicts else []

        return score, shared_concepts, obstacles

    def unify_theories(
        self,
        theory1: Theory,
        theory2: Theory,
        unified_name: str,
        description: str
    ) -> Optional[Theory]:
        """
        Attempt to unify two theories.
        Returns unified theory or None if unification fails.
        """
        score, shared, obstacles = self.evaluate_unification_potential(theory1, theory2)

        if score < 0.3:
            return None

        # Merge laws
        core_laws = list(set(theory1.core_laws) | set(theory2.core_laws))
        auxiliary_laws = list(set(theory1.auxiliary_laws) | set(theory2.auxiliary_laws))

        # Merge axioms (deduplicate)
        axioms = list(set(theory1.axioms) | set(theory2.axioms))

        # Merge definitions
        definitions = {**theory1.definitions, **theory2.definitions}

        # Merge ontology
        ontology = {}
        all_entities = set(theory1.ontology.keys()) | set(theory2.ontology.keys())
        for entity in all_entities:
            props1 = set(theory1.ontology.get(entity, []))
            props2 = set(theory2.ontology.get(entity, []))
            ontology[entity] = list(props1 | props2)

        # Merge phenomena and predictions
        phenomena = list(set(theory1.phenomena_explained) | set(theory2.phenomena_explained))
        predictions = list(set(theory1.predictions) | set(theory2.predictions))

        unified = Theory(
            theory_id="",
            name=unified_name,
            status=TheoryStatus.UNIFIED,
            description=description,
            domain=f"{theory1.domain}+{theory2.domain}",
            core_laws=core_laws,
            auxiliary_laws=auxiliary_laws,
            axioms=axioms,
            definitions=definitions,
            ontology=ontology,
            phenomena_explained=phenomena,
            predictions=predictions,
            unifications=[f"Unified from {theory1.name} and {theory2.name}"] + shared,
            competing_theories=[],
            subsumed_theories=[theory1.theory_id, theory2.theory_id],
            coherence=(theory1.coherence + theory2.coherence) / 2 * score,
            coverage=max(theory1.coverage, theory2.coverage),
            parsimony=(theory1.parsimony + theory2.parsimony) / 2,
            fertility=max(theory1.fertility, theory2.fertility)
        )

        # Update original theories
        theory1.status = TheoryStatus.UNIFIED
        theory2.status = TheoryStatus.UNIFIED

        return unified


class PredictionGenerator:
    """Generates novel predictions from theories"""

    def __init__(self):
        self.predictions: Dict[str, Prediction] = {}

    def generate_predictions(
        self,
        theory: Theory,
        laws: Dict[str, Law],
        num_predictions: int = 5
    ) -> List[Prediction]:
        """Generate novel predictions from a theory"""
        predictions = []

        core_laws = [laws[lid] for lid in theory.core_laws if lid in laws]

        for law in core_laws:
            # Generate prediction from each law
            pred = self._prediction_from_law(law, theory)
            if pred:
                predictions.append(pred)

        # Generate cross-law predictions
        if len(core_laws) >= 2:
            for i, law1 in enumerate(core_laws):
                for law2 in core_laws[i+1:]:
                    combined_pred = self._combined_prediction(law1, law2, theory)
                    if combined_pred:
                        predictions.append(combined_pred)

        # Limit and store
        predictions = predictions[:num_predictions]
        for pred in predictions:
            self.predictions[pred.prediction_id] = pred

        return predictions

    def _prediction_from_law(self, law: Law, theory: Theory) -> Optional[Prediction]:
        """Generate a prediction from a single law"""
        if not law.mathematical_form:
            return None

        # Create prediction by extending law to new conditions
        test_conditions = [f"Extend {cond} to extreme values" for cond in law.boundary_conditions[:2]]

        return Prediction(
            prediction_id="",
            source_theory=theory.theory_id,
            source_laws=[law.law_id],
            statement=f"If {law.name} holds, then under extended conditions: {law.statement}",
            quantitative_form=law.mathematical_form,
            predicted_value=None,
            uncertainty=None,
            test_conditions=test_conditions,
            required_observations=[f"Measure {var}" for var in list(law.variables.keys())[:3]],
            falsification_criteria=f"Deviation > 3σ from {law.mathematical_form}",
            is_novel=True
        )

    def _combined_prediction(
        self,
        law1: Law,
        law2: Law,
        theory: Theory
    ) -> Optional[Prediction]:
        """Generate prediction from combining two laws"""
        # Find shared variables
        shared = set(law1.variables.keys()) & set(law2.variables.keys())
        if not shared:
            return None

        shared_var = list(shared)[0]

        return Prediction(
            prediction_id="",
            source_theory=theory.theory_id,
            source_laws=[law1.law_id, law2.law_id],
            statement=f"Combining {law1.name} and {law2.name} via {shared_var} implies novel relationship",
            quantitative_form=None,
            predicted_value=None,
            uncertainty=None,
            test_conditions=[f"Vary {shared_var} while measuring effects"],
            required_observations=[f"Measure outcomes of both laws simultaneously"],
            falsification_criteria=f"Laws inconsistent when {shared_var} varied",
            is_novel=True
        )


class TheorySynthesizer:
    """
    Main theory synthesis engine.
    Coordinates pattern promotion, law composition, consistency checking,
    theory unification, and prediction generation.
    """

    def __init__(self):
        self.patterns: Dict[str, Pattern] = {}
        self.laws: Dict[str, Law] = {}
        self.theories: Dict[str, Theory] = {}
        self.predictions: Dict[str, Prediction] = {}

        # Sub-components
        self.promoter = PatternToLawPromoter()
        self.composer = LawToTheoryComposer()
        self.consistency_checker = ConsistencyChecker()
        self.unifier = TheoryUnifier(self.consistency_checker)
        self.prediction_generator = PredictionGenerator()

        # Event callbacks
        self._callbacks: Dict[str, List[Callable]] = defaultdict(list)

    def on(self, event: str, callback: Callable):
        """Register event callback"""
        self._callbacks[event].append(callback)

    def _emit(self, event: str, data: Any):
        """Emit event to callbacks"""
        for callback in self._callbacks[event]:
            callback(data)

    # Pattern management
    def add_pattern(self, pattern: Pattern) -> str:
        """Add a discovered pattern"""
        self.patterns[pattern.pattern_id] = pattern
        self._emit("pattern_added", pattern)

        # Check for automatic promotion
        should_promote, score, rationale = self.promoter.evaluate_pattern(pattern)
        if should_promote:
            self._emit("pattern_promotion_candidate", {
                "pattern": pattern,
                "score": score,
                "rationale": rationale
            })

        return pattern.pattern_id

    def promote_pattern(self, pattern_id: str, law_name: str = None) -> Optional[Law]:
        """Promote a pattern to a law"""
        pattern = self.patterns.get(pattern_id)
        if not pattern:
            return None

        law = self.promoter.promote_to_law(pattern, law_name)
        self.laws[law.law_id] = law
        self.composer.add_law(law)

        self._emit("law_created", law)
        return law

    # Law management
    def add_law(self, law: Law) -> str:
        """Add a law directly"""
        self.laws[law.law_id] = law
        self.composer.add_law(law)
        self._emit("law_added", law)
        return law.law_id

    def validate_law(self, law_id: str, observation: str, confirms: bool):
        """Record validation result for a law"""
        law = self.laws.get(law_id)
        if not law:
            return

        law.predictions_made += 1
        if confirms:
            law.predictions_confirmed += 1
            law.confirmations.append(observation)

            # Update status based on confirmation rate
            if law.predictions_made >= 10 and law.confirmation_rate >= 0.9:
                law.status = LawStatus.VALIDATED
            elif law.predictions_made >= 50 and law.confirmation_rate >= 0.95:
                law.status = LawStatus.ESTABLISHED
        else:
            law.falsifications.append(observation)

            # Check for refutation
            if law.predictions_made >= 5 and law.confirmation_rate < 0.3:
                law.status = LawStatus.REFUTED

        law.last_updated = datetime.now()
        self._emit("law_validated", {"law": law, "confirms": confirms})

    # Theory management
    def compose_theory(
        self,
        law_ids: List[str],
        name: str,
        domain: str,
        description: str
    ) -> Theory:
        """Compose a new theory from laws"""
        theory = self.composer.compose_theory(law_ids, name, domain, description)
        self.theories[theory.theory_id] = theory
        self._emit("theory_created", theory)
        return theory

    def unify_theories(
        self,
        theory1_id: str,
        theory2_id: str,
        unified_name: str,
        description: str
    ) -> Optional[Theory]:
        """Attempt to unify two theories"""
        theory1 = self.theories.get(theory1_id)
        theory2 = self.theories.get(theory2_id)

        if not theory1 or not theory2:
            return None

        unified = self.unifier.unify_theories(theory1, theory2, unified_name, description)

        if unified:
            self.theories[unified.theory_id] = unified
            self._emit("theory_unified", {
                "unified": unified,
                "source1": theory1,
                "source2": theory2
            })

        return unified

    # Consistency checking
    def check_global_consistency(self) -> List[ConsistencyReport]:
        """Check consistency across all laws and theories"""
        reports = []

        # Check law pairs
        law_list = list(self.laws.values())
        for i, law1 in enumerate(law_list):
            for law2 in law_list[i+1:]:
                report = self.consistency_checker.check_law_consistency(law1, law2)
                if report.level != ConsistencyLevel.CONSISTENT:
                    reports.append(report)

        # Check theory pairs
        theory_list = list(self.theories.values())
        for i, thy1 in enumerate(theory_list):
            for thy2 in theory_list[i+1:]:
                report = self.consistency_checker.check_theory_consistency(thy1, thy2)
                if report.level != ConsistencyLevel.CONSISTENT:
                    reports.append(report)

        self._emit("consistency_check_complete", reports)
        return reports

    # Prediction generation
    def generate_predictions(
        self,
        theory_id: str,
        num_predictions: int = 5
    ) -> List[Prediction]:
        """Generate predictions from a theory"""
        theory = self.theories.get(theory_id)
        if not theory:
            return []

        predictions = self.prediction_generator.generate_predictions(
            theory, self.laws, num_predictions
        )

        for pred in predictions:
            self.predictions[pred.prediction_id] = pred
            theory.predictions.append(pred.prediction_id)

        self._emit("predictions_generated", predictions)
        return predictions

    def test_prediction(
        self,
        prediction_id: str,
        observed_value: float,
        tolerance: float = 0.1
    ) -> Tuple[bool, str]:
        """Test a prediction against observation"""
        pred = self.predictions.get(prediction_id)
        if not pred:
            return False, "Prediction not found"

        pred.is_tested = True
        pred.observed_value = observed_value

        if pred.predicted_value is not None:
            error = abs(observed_value - pred.predicted_value)
            relative_error = error / abs(pred.predicted_value) if pred.predicted_value != 0 else error

            pred.is_confirmed = relative_error <= tolerance
            result = "Confirmed" if pred.is_confirmed else "Refuted"
        else:
            # Qualitative prediction
            pred.is_confirmed = True  # Assume confirmed if observed
            result = "Observed"

        # Update source laws
        for law_id in pred.source_laws:
            if law_id in self.laws:
                self.validate_law(law_id, f"Prediction {prediction_id}", pred.is_confirmed)

        self._emit("prediction_tested", pred)
        return pred.is_confirmed, result

    # Synthesis summary
    def get_synthesis_summary(self) -> Dict[str, Any]:
        """Get summary of synthesized knowledge"""
        return {
            "patterns": {
                "total": len(self.patterns),
                "by_type": self._count_by_type(self.patterns, "pattern_type")
            },
            "laws": {
                "total": len(self.laws),
                "by_status": self._count_by_type(self.laws, "status"),
                "avg_confirmation_rate": self._avg_confirmation_rate()
            },
            "theories": {
                "total": len(self.theories),
                "by_status": self._count_by_type(self.theories, "status"),
                "avg_coherence": self._avg_theory_metric("coherence")
            },
            "predictions": {
                "total": len(self.predictions),
                "tested": sum(1 for p in self.predictions.values() if p.is_tested),
                "confirmed": sum(1 for p in self.predictions.values() if p.is_confirmed)
            }
        }

    def _count_by_type(self, items: Dict, attr: str) -> Dict[str, int]:
        counts = defaultdict(int)
        for item in items.values():
            key = getattr(item, attr)
            if hasattr(key, "name"):
                key = key.name
            counts[str(key)] += 1
        return dict(counts)

    def _avg_confirmation_rate(self) -> float:
        rates = [l.confirmation_rate for l in self.laws.values() if l.predictions_made > 0]
        return sum(rates) / len(rates) if rates else 0.0

    def _avg_theory_metric(self, metric: str) -> float:
        values = [getattr(t, metric) for t in self.theories.values()]
        return sum(values) / len(values) if values else 0.0


# Singleton instance
_theory_synthesizer: Optional[TheorySynthesizer] = None


def get_theory_synthesizer() -> TheorySynthesizer:
    """Get or create the global theory synthesizer"""
    global _theory_synthesizer
    if _theory_synthesizer is None:
        _theory_synthesizer = TheorySynthesizer()
    return _theory_synthesizer
