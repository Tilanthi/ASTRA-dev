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
V70 Hypothesis Space Generator

A framework for systematically generating, exploring, and evaluating hypothesis
spaces. Enables creative scientific hypothesis generation while maintaining
logical consistency and empirical grounding.

This module enables STAN to:
1. Generate novel hypotheses from data and prior knowledge
2. Define and explore structured hypothesis spaces
3. Rank hypotheses by plausibility, novelty, and testability
4. Combine hypotheses compositionally
5. Identify gaps in hypothesis coverage
6. Prune implausible hypotheses efficiently
"""

import numpy as np
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Any, Callable, Tuple, Set, Iterator
from enum import Enum, auto
from abc import ABC, abstractmethod
import logging
from collections import defaultdict
import hashlib
import itertools

logger = logging.getLogger(__name__)


# =============================================================================
# Enumerations
# =============================================================================

class HypothesisType(Enum):
    """Types of scientific hypotheses"""
    CAUSAL = auto()          # X causes Y
    CORRELATIONAL = auto()   # X correlates with Y
    MECHANISTIC = auto()     # X works via mechanism M
    EXISTENTIAL = auto()     # X exists
    COMPARATIVE = auto()     # X > Y in property P
    CONDITIONAL = auto()     # If X then Y
    TEMPORAL = auto()        # X precedes/follows Y
    STRUCTURAL = auto()      # X has structure S


class HypothesisStatus(Enum):
    """Status of a hypothesis"""
    GENERATED = auto()       # Just created
    PLAUSIBLE = auto()       # Passes initial checks
    TESTABLE = auto()        # Can be empirically tested
    TESTED = auto()          # Has been tested
    SUPPORTED = auto()       # Evidence supports
    REFUTED = auto()         # Evidence refutes
    INCONCLUSIVE = auto()    # Evidence inconclusive


class GenerationStrategy(Enum):
    """Strategies for hypothesis generation"""
    COMBINATORIAL = auto()   # Combine elements systematically
    ANALOGICAL = auto()      # From analogies
    ABDUCTIVE = auto()       # Best explanation for observations
    MUTATION = auto()        # Modify existing hypotheses
    INTERPOLATION = auto()   # Fill gaps in knowledge
    EXTRAPOLATION = auto()   # Extend beyond known


class PruningCriterion(Enum):
    """Criteria for pruning hypotheses"""
    IMPLAUSIBILITY = auto()  # Too unlikely
    UNFALSIFIABILITY = auto()  # Can't be tested
    REDUNDANCY = auto()      # Already covered
    INCONSISTENCY = auto()   # Logical contradiction
    COMPLEXITY = auto()      # Too complex (Occam's razor)


# =============================================================================
# Data Classes
# =============================================================================

@dataclass
class Variable:
    """A variable in a hypothesis"""
    id: str
    name: str
    var_type: str  # continuous, categorical, binary
    domain: Optional[Tuple[float, float]] = None
    categories: Optional[List[str]] = None
    observed_values: Optional[np.ndarray] = None


@dataclass
class Relation:
    """A relation between variables"""
    id: str
    name: str
    source_vars: List[str]
    target_vars: List[str]
    relation_type: str  # causal, correlational, etc.
    strength: Optional[float] = None
    direction: Optional[str] = None  # positive, negative, nonlinear


@dataclass
class Hypothesis:
    """A scientific hypothesis"""
    id: str
    statement: str
    hypothesis_type: HypothesisType
    variables: List[str] = field(default_factory=list)
    relations: List[str] = field(default_factory=list)
    conditions: List[str] = field(default_factory=list)
    status: HypothesisStatus = HypothesisStatus.GENERATED

    # Evaluation scores
    plausibility: float = 0.5
    novelty: float = 0.5
    testability: float = 0.5
    complexity: float = 0.5
    evidence_score: float = 0.0

    # Metadata
    generation_strategy: Optional[GenerationStrategy] = None
    parent_hypotheses: List[str] = field(default_factory=list)
    evidence: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class HypothesisSpace:
    """A structured space of hypotheses"""
    id: str
    name: str
    description: str
    dimensions: List[str] = field(default_factory=list)
    constraints: List[str] = field(default_factory=list)
    hypotheses: Dict[str, Hypothesis] = field(default_factory=dict)
    coverage_map: Dict[str, List[str]] = field(default_factory=dict)


@dataclass
class EvidenceItem:
    """A piece of evidence for/against hypotheses"""
    id: str
    description: str
    source: str
    supports: List[str] = field(default_factory=list)  # hypothesis IDs
    contradicts: List[str] = field(default_factory=list)
    strength: float = 1.0
    reliability: float = 1.0


@dataclass
class HypothesisCluster:
    """A cluster of related hypotheses"""
    id: str
    name: str
    hypotheses: List[str] = field(default_factory=list)
    common_theme: str = ""
    diversity_score: float = 0.0
    centroid_hypothesis: Optional[str] = None


# =============================================================================
# Variable Registry
# =============================================================================

class VariableRegistry:
    """Registry of variables for hypothesis generation"""

    def __init__(self):
        self.variables: Dict[str, Variable] = {}
        self.variable_groups: Dict[str, List[str]] = defaultdict(list)

    def register_variable(
        self,
        name: str,
        var_type: str,
        group: Optional[str] = None,
        **kwargs
    ) -> Variable:
        """Register a variable"""
        var_id = f"var_{name}_{len(self.variables)}"

        var = Variable(
            id=var_id,
            name=name,
            var_type=var_type,
            domain=kwargs.get('domain'),
            categories=kwargs.get('categories'),
            observed_values=kwargs.get('values')
        )

        self.variables[var_id] = var
        if group:
            self.variable_groups[group].append(var_id)

        return var

    def get_variables_by_type(self, var_type: str) -> List[Variable]:
        """Get all variables of a type"""
        return [v for v in self.variables.values() if v.var_type == var_type]

    def get_variables_by_group(self, group: str) -> List[Variable]:
        """Get all variables in a group"""
        return [self.variables[vid] for vid in self.variable_groups.get(group, [])]

    def get_compatible_pairs(self) -> List[Tuple[Variable, Variable]]:
        """Get pairs of variables that can be related"""
        pairs = []
        vars_list = list(self.variables.values())

        for i, v1 in enumerate(vars_list):
            for v2 in vars_list[i+1:]:
                # Same type or one continuous/one categorical
                if v1.var_type == v2.var_type or \
                   {v1.var_type, v2.var_type} == {'continuous', 'categorical'}:
                    pairs.append((v1, v2))

        return pairs


# =============================================================================
# Hypothesis Generator
# =============================================================================

class HypothesisGenerator:
    """Generates hypotheses using various strategies"""

    def __init__(self, variable_registry: VariableRegistry):
        self.variable_registry = variable_registry
        self.generated_hypotheses: Dict[str, Hypothesis] = {}
        self.hypothesis_counter = 0

    def generate(
        self,
        strategy: GenerationStrategy,
        constraints: Optional[Dict[str, Any]] = None,
        n_hypotheses: int = 10
    ) -> List[Hypothesis]:
        """Generate hypotheses using specified strategy"""
        generators = {
            GenerationStrategy.COMBINATORIAL: self._generate_combinatorial,
            GenerationStrategy.ABDUCTIVE: self._generate_abductive,
            GenerationStrategy.MUTATION: self._generate_mutation,
            GenerationStrategy.INTERPOLATION: self._generate_interpolation,
            GenerationStrategy.EXTRAPOLATION: self._generate_extrapolation
        }

        generator = generators.get(strategy, self._generate_combinatorial)
        hypotheses = list(generator(constraints, n_hypotheses))

        for h in hypotheses:
            h.generation_strategy = strategy
            self.generated_hypotheses[h.id] = h

        return hypotheses

    def _generate_combinatorial(
        self,
        constraints: Optional[Dict[str, Any]],
        n_hypotheses: int
    ) -> Iterator[Hypothesis]:
        """Generate hypotheses by combining variables"""
        pairs = self.variable_registry.get_compatible_pairs()

        # Generate different hypothesis types for each pair
        count = 0
        for v1, v2 in pairs:
            if count >= n_hypotheses:
                break

            # Causal hypothesis
            yield self._create_hypothesis(
                f"{v1.name} causes changes in {v2.name}",
                HypothesisType.CAUSAL,
                [v1.id, v2.id]
            )
            count += 1

            if count >= n_hypotheses:
                break

            # Reverse causal
            yield self._create_hypothesis(
                f"{v2.name} causes changes in {v1.name}",
                HypothesisType.CAUSAL,
                [v2.id, v1.id]
            )
            count += 1

            if count >= n_hypotheses:
                break

            # Correlational
            yield self._create_hypothesis(
                f"{v1.name} and {v2.name} are correlated",
                HypothesisType.CORRELATIONAL,
                [v1.id, v2.id]
            )
            count += 1

    def _generate_abductive(
        self,
        constraints: Optional[Dict[str, Any]],
        n_hypotheses: int
    ) -> Iterator[Hypothesis]:
        """Generate hypotheses as best explanations for observations"""
        observations = constraints.get('observations', []) if constraints else []

        if not observations:
            # Generate based on variable relationships
            for v in list(self.variable_registry.variables.values())[:n_hypotheses]:
                yield self._create_hypothesis(
                    f"There exists an underlying mechanism affecting {v.name}",
                    HypothesisType.MECHANISTIC,
                    [v.id]
                )
        else:
            # Generate explanations for each observation
            for obs in observations[:n_hypotheses]:
                yield self._create_hypothesis(
                    f"The observation '{obs}' is explained by a causal mechanism",
                    HypothesisType.MECHANISTIC,
                    [],
                    conditions=[obs]
                )

    def _generate_mutation(
        self,
        constraints: Optional[Dict[str, Any]],
        n_hypotheses: int
    ) -> Iterator[Hypothesis]:
        """Generate hypotheses by mutating existing ones"""
        base_hypotheses = constraints.get('base_hypotheses', []) if constraints else []

        if not base_hypotheses:
            base_hypotheses = list(self.generated_hypotheses.values())[:5]

        count = 0
        for base in base_hypotheses:
            if count >= n_hypotheses:
                break

            # Negate the hypothesis
            yield self._create_hypothesis(
                f"NOT: {base.statement}",
                base.hypothesis_type,
                base.variables,
                parent_hypotheses=[base.id]
            )
            count += 1

            if count >= n_hypotheses:
                break

            # Strengthen the hypothesis
            yield self._create_hypothesis(
                f"STRONG: {base.statement}",
                base.hypothesis_type,
                base.variables,
                parent_hypotheses=[base.id]
            )
            count += 1

            if count >= n_hypotheses:
                break

            # Add condition
            yield self._create_hypothesis(
                f"CONDITIONAL: {base.statement} (under certain conditions)",
                HypothesisType.CONDITIONAL,
                base.variables,
                parent_hypotheses=[base.id]
            )
            count += 1

    def _generate_interpolation(
        self,
        constraints: Optional[Dict[str, Any]],
        n_hypotheses: int
    ) -> Iterator[Hypothesis]:
        """Generate hypotheses filling gaps between known facts"""
        known_facts = constraints.get('known_facts', []) if constraints else []

        if len(known_facts) < 2:
            # Generate gap-filling hypotheses based on variables
            vars_list = list(self.variable_registry.variables.values())
            for i in range(min(n_hypotheses, len(vars_list) - 1)):
                v1, v2 = vars_list[i], vars_list[i + 1]
                yield self._create_hypothesis(
                    f"There is an intermediate variable connecting {v1.name} and {v2.name}",
                    HypothesisType.MECHANISTIC,
                    [v1.id, v2.id]
                )
        else:
            # Interpolate between known facts
            for i in range(min(n_hypotheses, len(known_facts) - 1)):
                yield self._create_hypothesis(
                    f"There is a connection between '{known_facts[i]}' and '{known_facts[i+1]}'",
                    HypothesisType.STRUCTURAL,
                    []
                )

    def _generate_extrapolation(
        self,
        constraints: Optional[Dict[str, Any]],
        n_hypotheses: int
    ) -> Iterator[Hypothesis]:
        """Generate hypotheses extending beyond known patterns"""
        patterns = constraints.get('patterns', []) if constraints else []

        if not patterns:
            # Generate trend-based extrapolations
            for v in list(self.variable_registry.variables.values())[:n_hypotheses]:
                yield self._create_hypothesis(
                    f"{v.name} will continue to follow its current trend",
                    HypothesisType.TEMPORAL,
                    [v.id]
                )
        else:
            # Extrapolate each pattern
            for pattern in patterns[:n_hypotheses]:
                yield self._create_hypothesis(
                    f"The pattern '{pattern}' will extend to new domains",
                    HypothesisType.STRUCTURAL,
                    []
                )

    def _create_hypothesis(
        self,
        statement: str,
        h_type: HypothesisType,
        variables: List[str],
        conditions: Optional[List[str]] = None,
        parent_hypotheses: Optional[List[str]] = None
    ) -> Hypothesis:
        """Create a new hypothesis"""
        self.hypothesis_counter += 1
        h_id = f"h_{self.hypothesis_counter}"

        return Hypothesis(
            id=h_id,
            statement=statement,
            hypothesis_type=h_type,
            variables=variables,
            conditions=conditions or [],
            parent_hypotheses=parent_hypotheses or []
        )


# =============================================================================
# Hypothesis Evaluator
# =============================================================================

class HypothesisEvaluator:
    """Evaluates hypotheses on multiple criteria"""

    def __init__(self):
        self.evaluation_functions: Dict[str, Callable] = {
            'plausibility': self._evaluate_plausibility,
            'novelty': self._evaluate_novelty,
            'testability': self._evaluate_testability,
            'complexity': self._evaluate_complexity
        }
        self.known_hypotheses: Set[str] = set()
        self.evidence_items: Dict[str, EvidenceItem] = {}

    def evaluate(self, hypothesis: Hypothesis) -> Dict[str, float]:
        """Comprehensive evaluation of a hypothesis"""
        scores = {}
        for criterion, evaluator in self.evaluation_functions.items():
            scores[criterion] = evaluator(hypothesis)
            setattr(hypothesis, criterion, scores[criterion])

        # Update evidence score
        hypothesis.evidence_score = self._evaluate_evidence(hypothesis)
        scores['evidence'] = hypothesis.evidence_score

        # Overall score
        scores['overall'] = self._compute_overall_score(scores)

        return scores

    def _evaluate_plausibility(self, hypothesis: Hypothesis) -> float:
        """Evaluate prior plausibility"""
        plausibility = 0.5

        # Simpler hypotheses are more plausible
        n_vars = len(hypothesis.variables)
        if n_vars <= 2:
            plausibility += 0.2
        elif n_vars > 5:
            plausibility -= 0.2

        # Conditional hypotheses are often more plausible
        if hypothesis.hypothesis_type == HypothesisType.CONDITIONAL:
            plausibility += 0.1

        # Hypotheses with parent support
        if hypothesis.parent_hypotheses:
            plausibility += 0.1

        return max(0.0, min(1.0, plausibility))

    def _evaluate_novelty(self, hypothesis: Hypothesis) -> float:
        """Evaluate novelty/originality"""
        # Check if similar hypothesis exists
        statement_hash = hashlib.md5(hypothesis.statement.lower().encode()).hexdigest()

        if statement_hash in self.known_hypotheses:
            return 0.1  # Very low novelty

        # Check for similar statements
        novelty = 0.7
        statement_words = set(hypothesis.statement.lower().split())

        for known in self.known_hypotheses:
            # Simple word overlap check
            overlap = len(statement_words & set(known.split())) / len(statement_words)
            if overlap > 0.7:
                novelty -= 0.2

        self.known_hypotheses.add(hypothesis.statement.lower())

        return max(0.0, min(1.0, novelty))

    def _evaluate_testability(self, hypothesis: Hypothesis) -> float:
        """Evaluate how testable the hypothesis is"""
        testability = 0.5

        # Hypotheses with concrete variables are more testable
        if hypothesis.variables:
            testability += 0.1 * min(len(hypothesis.variables), 3)

        # Causal and correlational are typically testable
        if hypothesis.hypothesis_type in [HypothesisType.CAUSAL, HypothesisType.CORRELATIONAL]:
            testability += 0.2

        # Existential hypotheses can be hard to test
        if hypothesis.hypothesis_type == HypothesisType.EXISTENTIAL:
            testability -= 0.1

        # Conditional hypotheses are testable
        if hypothesis.hypothesis_type == HypothesisType.CONDITIONAL:
            testability += 0.15

        return max(0.0, min(1.0, testability))

    def _evaluate_complexity(self, hypothesis: Hypothesis) -> float:
        """Evaluate complexity (lower is simpler, better by Occam's razor)"""
        complexity = 0.3

        # More variables = more complex
        complexity += 0.1 * len(hypothesis.variables)

        # More conditions = more complex
        complexity += 0.1 * len(hypothesis.conditions)

        # Statement length
        complexity += 0.01 * len(hypothesis.statement.split())

        return max(0.0, min(1.0, complexity))

    def _evaluate_evidence(self, hypothesis: Hypothesis) -> float:
        """Evaluate based on available evidence"""
        support = 0.0
        contradiction = 0.0

        for evidence in self.evidence_items.values():
            if hypothesis.id in evidence.supports:
                support += evidence.strength * evidence.reliability
            if hypothesis.id in evidence.contradicts:
                contradiction += evidence.strength * evidence.reliability

        if support + contradiction == 0:
            return 0.0  # No evidence

        return (support - contradiction) / (support + contradiction + 1)

    def _compute_overall_score(self, scores: Dict[str, float]) -> float:
        """Compute overall hypothesis score"""
        weights = {
            'plausibility': 0.25,
            'novelty': 0.2,
            'testability': 0.3,
            'complexity': -0.15,  # Negative because lower is better
            'evidence': 0.1
        }

        total = sum(
            scores.get(k, 0) * w
            for k, w in weights.items()
        )

        return max(0.0, min(1.0, total + 0.15))  # Offset for negative complexity

    def add_evidence(self, evidence: EvidenceItem):
        """Add evidence item"""
        self.evidence_items[evidence.id] = evidence


# =============================================================================
# Hypothesis Space Explorer
# =============================================================================

class HypothesisSpaceExplorer:
    """Explores and manages hypothesis spaces"""

    def __init__(
        self,
        generator: HypothesisGenerator,
        evaluator: HypothesisEvaluator
    ):
        self.generator = generator
        self.evaluator = evaluator
        self.spaces: Dict[str, HypothesisSpace] = {}
        self.clusters: Dict[str, HypothesisCluster] = {}

    def create_space(
        self,
        name: str,
        dimensions: List[str],
        constraints: Optional[List[str]] = None
    ) -> HypothesisSpace:
        """Create a new hypothesis space"""
        space_id = f"space_{name}_{len(self.spaces)}"

        space = HypothesisSpace(
            id=space_id,
            name=name,
            description=f"Hypothesis space for {name}",
            dimensions=dimensions,
            constraints=constraints or []
        )

        self.spaces[space_id] = space
        return space

    def populate_space(
        self,
        space: HypothesisSpace,
        strategy: GenerationStrategy = GenerationStrategy.COMBINATORIAL,
        n_hypotheses: int = 20
    ) -> List[Hypothesis]:
        """Populate a hypothesis space with generated hypotheses"""
        hypotheses = self.generator.generate(
            strategy,
            constraints={'dimensions': space.dimensions},
            n_hypotheses=n_hypotheses
        )

        for h in hypotheses:
            # Evaluate each hypothesis
            self.evaluator.evaluate(h)
            space.hypotheses[h.id] = h

            # Update coverage map
            for var in h.variables:
                if var not in space.coverage_map:
                    space.coverage_map[var] = []
                space.coverage_map[var].append(h.id)

        return hypotheses

    def prune_space(
        self,
        space: HypothesisSpace,
        criterion: PruningCriterion,
        threshold: float = 0.3
    ) -> List[str]:
        """Prune hypotheses from space based on criterion"""
        pruned = []

        for h_id, hypothesis in list(space.hypotheses.items()):
            should_prune = False

            if criterion == PruningCriterion.IMPLAUSIBILITY:
                should_prune = hypothesis.plausibility < threshold

            elif criterion == PruningCriterion.UNFALSIFIABILITY:
                should_prune = hypothesis.testability < threshold

            elif criterion == PruningCriterion.COMPLEXITY:
                should_prune = hypothesis.complexity > (1 - threshold)

            elif criterion == PruningCriterion.REDUNDANCY:
                # Check for similar hypotheses
                for other_id, other in space.hypotheses.items():
                    if other_id != h_id:
                        similarity = self._compute_similarity(hypothesis, other)
                        if similarity > 0.9 and hypothesis.plausibility < other.plausibility:
                            should_prune = True
                            break

            if should_prune:
                del space.hypotheses[h_id]
                pruned.append(h_id)

        return pruned

    def _compute_similarity(self, h1: Hypothesis, h2: Hypothesis) -> float:
        """Compute similarity between hypotheses"""
        # Variable overlap
        vars1 = set(h1.variables)
        vars2 = set(h2.variables)
        var_overlap = len(vars1 & vars2) / len(vars1 | vars2) if vars1 | vars2 else 0

        # Type match
        type_match = 1.0 if h1.hypothesis_type == h2.hypothesis_type else 0.5

        # Statement similarity (simple)
        words1 = set(h1.statement.lower().split())
        words2 = set(h2.statement.lower().split())
        word_overlap = len(words1 & words2) / len(words1 | words2) if words1 | words2 else 0

        return 0.4 * var_overlap + 0.2 * type_match + 0.4 * word_overlap

    def find_gaps(self, space: HypothesisSpace) -> List[str]:
        """Find gaps in hypothesis coverage"""
        gaps = []

        # Check variable coverage
        all_vars = set(self.generator.variable_registry.variables.keys())
        covered_vars = set(space.coverage_map.keys())
        uncovered = all_vars - covered_vars

        for var in uncovered:
            gaps.append(f"No hypotheses cover variable: {var}")

        # Check hypothesis type coverage
        type_counts = defaultdict(int)
        for h in space.hypotheses.values():
            type_counts[h.hypothesis_type] += 1

        for h_type in HypothesisType:
            if type_counts[h_type] == 0:
                gaps.append(f"No hypotheses of type: {h_type.name}")

        return gaps

    def cluster_hypotheses(
        self,
        space: HypothesisSpace,
        n_clusters: int = 5
    ) -> List[HypothesisCluster]:
        """Cluster hypotheses by similarity"""
        hypotheses = list(space.hypotheses.values())
        if len(hypotheses) < n_clusters:
            n_clusters = max(1, len(hypotheses))

        # Simple clustering based on hypothesis type and variables
        type_groups: Dict[HypothesisType, List[Hypothesis]] = defaultdict(list)
        for h in hypotheses:
            type_groups[h.hypothesis_type].append(h)

        clusters = []
        cluster_id = 0

        for h_type, group in type_groups.items():
            if not group:
                continue

            cluster = HypothesisCluster(
                id=f"cluster_{cluster_id}",
                name=f"{h_type.name} hypotheses",
                hypotheses=[h.id for h in group],
                common_theme=h_type.name
            )

            # Compute diversity
            if len(group) > 1:
                similarities = []
                for i, h1 in enumerate(group):
                    for h2 in group[i+1:]:
                        similarities.append(self._compute_similarity(h1, h2))
                cluster.diversity_score = 1.0 - np.mean(similarities) if similarities else 1.0

            # Find centroid (highest scoring)
            best_h = max(group, key=lambda h: h.plausibility)
            cluster.centroid_hypothesis = best_h.id

            clusters.append(cluster)
            self.clusters[cluster.id] = cluster
            cluster_id += 1

        return clusters

    def get_top_hypotheses(
        self,
        space: HypothesisSpace,
        criterion: str = 'overall',
        n: int = 10
    ) -> List[Hypothesis]:
        """Get top hypotheses by criterion"""
        hypotheses = list(space.hypotheses.values())

        if criterion == 'overall':
            key_fn = lambda h: (h.plausibility + h.novelty + h.testability - h.complexity) / 3
        elif criterion == 'plausibility':
            key_fn = lambda h: h.plausibility
        elif criterion == 'novelty':
            key_fn = lambda h: h.novelty
        elif criterion == 'testability':
            key_fn = lambda h: h.testability
        else:
            key_fn = lambda h: h.plausibility

        return sorted(hypotheses, key=key_fn, reverse=True)[:n]


# =============================================================================
# Compositional Hypothesis Builder
# =============================================================================

class CompositionalHypothesisBuilder:
    """Builds complex hypotheses from simpler ones"""

    def __init__(self, generator: HypothesisGenerator):
        self.generator = generator

    def combine_hypotheses(
        self,
        h1: Hypothesis,
        h2: Hypothesis,
        combination_type: str = 'conjunction'
    ) -> Hypothesis:
        """Combine two hypotheses"""
        if combination_type == 'conjunction':
            statement = f"({h1.statement}) AND ({h2.statement})"
            h_type = HypothesisType.CONDITIONAL
        elif combination_type == 'disjunction':
            statement = f"({h1.statement}) OR ({h2.statement})"
            h_type = HypothesisType.CONDITIONAL
        elif combination_type == 'conditional':
            statement = f"IF ({h1.statement}) THEN ({h2.statement})"
            h_type = HypothesisType.CONDITIONAL
        elif combination_type == 'causal_chain':
            statement = f"({h1.statement}) CAUSES ({h2.statement})"
            h_type = HypothesisType.CAUSAL
        else:
            statement = f"({h1.statement}) RELATED TO ({h2.statement})"
            h_type = HypothesisType.STRUCTURAL

        combined_vars = list(set(h1.variables + h2.variables))

        return self.generator._create_hypothesis(
            statement,
            h_type,
            combined_vars,
            parent_hypotheses=[h1.id, h2.id]
        )

    def specialize_hypothesis(
        self,
        hypothesis: Hypothesis,
        condition: str
    ) -> Hypothesis:
        """Make hypothesis more specific by adding condition"""
        statement = f"{hypothesis.statement} (when {condition})"

        return self.generator._create_hypothesis(
            statement,
            HypothesisType.CONDITIONAL,
            hypothesis.variables,
            conditions=hypothesis.conditions + [condition],
            parent_hypotheses=[hypothesis.id]
        )

    def generalize_hypothesis(
        self,
        hypothesis: Hypothesis
    ) -> Hypothesis:
        """Make hypothesis more general"""
        # Remove specific references
        statement = hypothesis.statement
        for var_id in hypothesis.variables:
            var = self.generator.variable_registry.variables.get(var_id)
            if var:
                statement = statement.replace(var.name, "some factor")

        return self.generator._create_hypothesis(
            f"GENERALIZED: {statement}",
            hypothesis.hypothesis_type,
            [],  # Remove specific variables
            parent_hypotheses=[hypothesis.id]
        )

    def negate_hypothesis(self, hypothesis: Hypothesis) -> Hypothesis:
        """Create negation of hypothesis"""
        return self.generator._create_hypothesis(
            f"NOT: {hypothesis.statement}",
            hypothesis.hypothesis_type,
            hypothesis.variables,
            parent_hypotheses=[hypothesis.id]
        )

    def create_competing_hypotheses(
        self,
        hypothesis: Hypothesis,
        n_alternatives: int = 3
    ) -> List[Hypothesis]:
        """Create alternative/competing hypotheses"""
        alternatives = []

        # Negation
        alternatives.append(self.negate_hypothesis(hypothesis))

        # Alternative causes (if causal)
        if hypothesis.hypothesis_type == HypothesisType.CAUSAL and len(hypothesis.variables) >= 2:
            # Reverse causation
            alternatives.append(self.generator._create_hypothesis(
                f"REVERSE: {hypothesis.variables[1]} causes {hypothesis.variables[0]}",
                HypothesisType.CAUSAL,
                list(reversed(hypothesis.variables)),
                parent_hypotheses=[hypothesis.id]
            ))

            # Common cause
            alternatives.append(self.generator._create_hypothesis(
                f"COMMON CAUSE: Both {hypothesis.variables[0]} and {hypothesis.variables[1]} are caused by a third factor",
                HypothesisType.CAUSAL,
                hypothesis.variables,
                parent_hypotheses=[hypothesis.id]
            ))

        return alternatives[:n_alternatives]


# =============================================================================
# Hypothesis Space Generator (Main Class)
# =============================================================================

class HypothesisSpaceGenerator:
    """
    Main orchestrator for hypothesis space generation.
    Integrates all components for comprehensive hypothesis management.
    """

    def __init__(self):
        self.variable_registry = VariableRegistry()
        self.generator = HypothesisGenerator(self.variable_registry)
        self.evaluator = HypothesisEvaluator()
        self.explorer = HypothesisSpaceExplorer(self.generator, self.evaluator)
        self.composer = CompositionalHypothesisBuilder(self.generator)

        logger.info("HypothesisSpaceGenerator initialized")

    def register_variables(
        self,
        variables: List[Dict[str, Any]]
    ) -> List[Variable]:
        """Register multiple variables"""
        registered = []
        for var_dict in variables:
            var = self.variable_registry.register_variable(
                name=var_dict['name'],
                var_type=var_dict.get('type', 'continuous'),
                group=var_dict.get('group'),
                domain=var_dict.get('domain'),
                categories=var_dict.get('categories'),
                values=var_dict.get('values')
            )
            registered.append(var)
        return registered

    def generate_hypothesis_space(
        self,
        name: str,
        dimensions: Optional[List[str]] = None,
        strategies: Optional[List[str]] = None,
        n_per_strategy: int = 10
    ) -> Dict[str, Any]:
        """Generate a complete hypothesis space"""
        # Create space
        if dimensions is None:
            dimensions = list(self.variable_registry.variables.keys())

        space = self.explorer.create_space(name, dimensions)

        # Populate with multiple strategies
        if strategies is None:
            strategies = ['combinatorial', 'abductive', 'interpolation']

        strategy_map = {
            'combinatorial': GenerationStrategy.COMBINATORIAL,
            'abductive': GenerationStrategy.ABDUCTIVE,
            'mutation': GenerationStrategy.MUTATION,
            'interpolation': GenerationStrategy.INTERPOLATION,
            'extrapolation': GenerationStrategy.EXTRAPOLATION
        }

        all_hypotheses = []
        for strategy_name in strategies:
            strategy = strategy_map.get(strategy_name, GenerationStrategy.COMBINATORIAL)
            hypotheses = self.explorer.populate_space(space, strategy, n_per_strategy)
            all_hypotheses.extend(hypotheses)

        # Prune and cluster
        pruned = self.explorer.prune_space(space, PruningCriterion.REDUNDANCY)
        clusters = self.explorer.cluster_hypotheses(space)
        gaps = self.explorer.find_gaps(space)

        return {
            'space_id': space.id,
            'total_hypotheses': len(space.hypotheses),
            'pruned_count': len(pruned),
            'clusters': len(clusters),
            'gaps': gaps,
            'top_hypotheses': [
                {'id': h.id, 'statement': h.statement, 'score': h.plausibility}
                for h in self.explorer.get_top_hypotheses(space, n=5)
            ]
        }

    def generate_hypotheses_for_observation(
        self,
        observation: str,
        n_hypotheses: int = 10
    ) -> List[Dict[str, Any]]:
        """Generate hypotheses explaining an observation"""
        hypotheses = self.generator.generate(
            GenerationStrategy.ABDUCTIVE,
            constraints={'observations': [observation]},
            n_hypotheses=n_hypotheses
        )

        results = []
        for h in hypotheses:
            scores = self.evaluator.evaluate(h)
            results.append({
                'id': h.id,
                'statement': h.statement,
                'type': h.hypothesis_type.name,
                'scores': scores
            })

        return sorted(results, key=lambda x: x['scores']['overall'], reverse=True)

    def add_evidence(
        self,
        description: str,
        supports: List[str],
        contradicts: List[str],
        strength: float = 1.0
    ):
        """Add evidence for/against hypotheses"""
        evidence = EvidenceItem(
            id=f"ev_{len(self.evaluator.evidence_items)}",
            description=description,
            source="user",
            supports=supports,
            contradicts=contradicts,
            strength=strength
        )
        self.evaluator.add_evidence(evidence)

    def get_hypothesis(self, hypothesis_id: str) -> Optional[Dict[str, Any]]:
        """Get hypothesis details"""
        h = self.generator.generated_hypotheses.get(hypothesis_id)
        if not h:
            return None

        return {
            'id': h.id,
            'statement': h.statement,
            'type': h.hypothesis_type.name,
            'status': h.status.name,
            'variables': h.variables,
            'conditions': h.conditions,
            'scores': {
                'plausibility': h.plausibility,
                'novelty': h.novelty,
                'testability': h.testability,
                'complexity': h.complexity,
                'evidence': h.evidence_score
            },
            'parent_hypotheses': h.parent_hypotheses
        }

    def combine_hypotheses(
        self,
        h1_id: str,
        h2_id: str,
        combination_type: str = 'conjunction'
    ) -> Optional[Dict[str, Any]]:
        """Combine two hypotheses"""
        h1 = self.generator.generated_hypotheses.get(h1_id)
        h2 = self.generator.generated_hypotheses.get(h2_id)

        if not h1 or not h2:
            return None

        combined = self.composer.combine_hypotheses(h1, h2, combination_type)
        self.generator.generated_hypotheses[combined.id] = combined
        self.evaluator.evaluate(combined)

        return self.get_hypothesis(combined.id)

    def get_competing_hypotheses(
        self,
        hypothesis_id: str,
        n_alternatives: int = 3
    ) -> List[Dict[str, Any]]:
        """Get competing/alternative hypotheses"""
        h = self.generator.generated_hypotheses.get(hypothesis_id)
        if not h:
            return []

        alternatives = self.composer.create_competing_hypotheses(h, n_alternatives)

        results = []
        for alt in alternatives:
            self.generator.generated_hypotheses[alt.id] = alt
            self.evaluator.evaluate(alt)
            results.append(self.get_hypothesis(alt.id))

        return results

    def rank_hypotheses(
        self,
        hypothesis_ids: List[str],
        criterion: str = 'overall'
    ) -> List[Dict[str, Any]]:
        """Rank hypotheses by criterion"""
        hypotheses = [
            self.generator.generated_hypotheses.get(h_id)
            for h_id in hypothesis_ids
            if h_id in self.generator.generated_hypotheses
        ]

        if criterion == 'plausibility':
            key_fn = lambda h: h.plausibility
        elif criterion == 'novelty':
            key_fn = lambda h: h.novelty
        elif criterion == 'testability':
            key_fn = lambda h: h.testability
        else:
            key_fn = lambda h: (h.plausibility + h.novelty + h.testability) / 3

        sorted_h = sorted(hypotheses, key=key_fn, reverse=True)

        return [self.get_hypothesis(h.id) for h in sorted_h if h]


# =============================================================================
# Factory Functions
# =============================================================================

def create_hypothesis_generator() -> HypothesisSpaceGenerator:
    """Create a configured hypothesis space generator"""
    return HypothesisSpaceGenerator()


def generate_hypotheses(
    variables: List[Dict[str, Any]],
    strategy: str = 'combinatorial',
    n_hypotheses: int = 10
) -> List[Dict[str, Any]]:
    """Convenience function for hypothesis generation"""
    generator = create_hypothesis_generator()
    generator.register_variables(variables)

    strategy_map = {
        'combinatorial': GenerationStrategy.COMBINATORIAL,
        'abductive': GenerationStrategy.ABDUCTIVE,
        'interpolation': GenerationStrategy.INTERPOLATION
    }

    hypotheses = generator.generator.generate(
        strategy_map.get(strategy, GenerationStrategy.COMBINATORIAL),
        n_hypotheses=n_hypotheses
    )

    results = []
    for h in hypotheses:
        generator.evaluator.evaluate(h)
        results.append(generator.get_hypothesis(h.id))

    return results


# =============================================================================
# Module Exports
# =============================================================================

__all__ = [
    # Enums
    'HypothesisType',
    'HypothesisStatus',
    'GenerationStrategy',
    'PruningCriterion',

    # Data classes
    'Variable',
    'Relation',
    'Hypothesis',
    'HypothesisSpace',
    'EvidenceItem',
    'HypothesisCluster',

    # Core classes
    'VariableRegistry',
    'HypothesisGenerator',
    'HypothesisEvaluator',
    'HypothesisSpaceExplorer',
    'CompositionalHypothesisBuilder',
    'HypothesisSpaceGenerator',

    # Factory functions
    'create_hypothesis_generator',
    'generate_hypotheses'
]
