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
V70 Universal Causal Substrate
==============================

A universal framework for causal reasoning that:
- Learns the meta-structure of causality itself
- Transfers causal patterns between domains
- Discovers new types of causal relationships
- Operates at multiple levels of abstraction

Key Innovation: Causality becomes a learnable, transferable substrate
rather than domain-specific rules.
"""

from dataclasses import dataclass, field
from typing import Dict, List, Optional, Any, Set, Tuple, Callable, Union
from enum import Enum
from abc import ABC, abstractmethod
import numpy as np
from collections import defaultdict
import time
import itertools


class CausalRelationType(Enum):
    """Types of causal relationships"""
    DIRECT = "direct"               # A directly causes B
    INDIRECT = "indirect"           # A causes B through intermediaries
    COMMON_CAUSE = "common_cause"   # C causes both A and B
    FEEDBACK = "feedback"           # A and B mutually cause each other
    THRESHOLD = "threshold"         # A causes B only above threshold
    DELAYED = "delayed"             # A causes B after time delay
    PROBABILISTIC = "probabilistic" # A increases probability of B
    NECESSARY = "necessary"         # A is necessary for B
    SUFFICIENT = "sufficient"       # A is sufficient for B
    INUS = "inus"                   # Insufficient but necessary part of unnecessary but sufficient condition


class CausalStrength(Enum):
    """Strength of causal relationships"""
    DETERMINISTIC = "deterministic"
    STRONG = "strong"
    MODERATE = "moderate"
    WEAK = "weak"
    UNCERTAIN = "uncertain"


class AbstractionLevel(Enum):
    """Levels of causal abstraction"""
    MECHANISM = "mechanism"         # Physical/chemical mechanism
    PROCESS = "process"             # Higher-level process
    PATTERN = "pattern"             # Abstract pattern
    PRINCIPLE = "principle"         # Universal principle
    META = "meta"                   # Meta-causal


class DomainType(Enum):
    """Domain types for causal transfer"""
    PHYSICS = "physics"
    CHEMISTRY = "chemistry"
    BIOLOGY = "biology"
    ECONOMICS = "economics"
    SOCIAL = "social"
    COGNITIVE = "cognitive"
    ABSTRACT = "abstract"
    UNIVERSAL = "universal"


@dataclass
class CausalVariable:
    """A variable in the causal system"""
    id: str
    name: str
    domain: DomainType
    abstraction_level: AbstractionLevel
    value_type: str  # continuous, discrete, binary, categorical
    value_range: Optional[Tuple[float, float]] = None
    observed: bool = True
    interventable: bool = True
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class CausalRelation:
    """A causal relationship between variables"""
    id: str
    cause: str  # Variable ID
    effect: str  # Variable ID
    relation_type: CausalRelationType
    strength: CausalStrength
    confidence: float = 0.5
    delay: float = 0.0
    threshold: Optional[float] = None
    functional_form: Optional[str] = None  # e.g., "linear", "exponential"
    parameters: Dict[str, float] = field(default_factory=dict)
    evidence: List[Dict[str, Any]] = field(default_factory=list)
    discovered_from: Optional[str] = None  # Source domain if transferred

    def compute_effect(self, cause_value: float) -> float:
        """Compute effect given cause value"""
        if self.threshold and cause_value < self.threshold:
            return 0.0

        base_effect = cause_value

        if self.functional_form == "linear":
            base_effect = self.parameters.get('slope', 1.0) * cause_value + self.parameters.get('intercept', 0.0)
        elif self.functional_form == "exponential":
            base_effect = np.exp(self.parameters.get('rate', 1.0) * cause_value)
        elif self.functional_form == "logarithmic":
            base_effect = np.log(abs(cause_value) + 1) * self.parameters.get('scale', 1.0)
        elif self.functional_form == "sigmoid":
            base_effect = 1 / (1 + np.exp(-self.parameters.get('steepness', 1.0) * cause_value))
        elif self.functional_form == "polynomial":
            degree = int(self.parameters.get('degree', 2))
            base_effect = sum(self.parameters.get(f'c{i}', 1.0) * (cause_value ** i) for i in range(degree + 1))

        # Apply strength modifier
        strength_map = {
            CausalStrength.DETERMINISTIC: 1.0,
            CausalStrength.STRONG: 0.8,
            CausalStrength.MODERATE: 0.5,
            CausalStrength.WEAK: 0.2,
            CausalStrength.UNCERTAIN: 0.1
        }
        return base_effect * strength_map.get(self.strength, 0.5)


@dataclass
class CausalStructure:
    """A causal graph structure"""
    id: str
    name: str
    variables: Dict[str, CausalVariable] = field(default_factory=dict)
    relations: Dict[str, CausalRelation] = field(default_factory=dict)
    domain: DomainType = DomainType.ABSTRACT
    abstraction_level: AbstractionLevel = AbstractionLevel.PATTERN
    confidence: float = 0.5
    source_structures: List[str] = field(default_factory=list)

    def add_variable(self, variable: CausalVariable):
        """Add a variable"""
        self.variables[variable.id] = variable

    def add_relation(self, relation: CausalRelation):
        """Add a relation"""
        self.relations[relation.id] = relation

    def get_causes(self, variable_id: str) -> List[CausalRelation]:
        """Get all relations where variable is effect"""
        return [r for r in self.relations.values() if r.effect == variable_id]

    def get_effects(self, variable_id: str) -> List[CausalRelation]:
        """Get all relations where variable is cause"""
        return [r for r in self.relations.values() if r.cause == variable_id]

    def get_ancestors(self, variable_id: str, visited: Set[str] = None) -> Set[str]:
        """Get all ancestor variables"""
        visited = visited or set()
        ancestors = set()

        for rel in self.get_causes(variable_id):
            if rel.cause not in visited:
                visited.add(rel.cause)
                ancestors.add(rel.cause)
                ancestors.update(self.get_ancestors(rel.cause, visited))

        return ancestors

    def get_descendants(self, variable_id: str, visited: Set[str] = None) -> Set[str]:
        """Get all descendant variables"""
        visited = visited or set()
        descendants = set()

        for rel in self.get_effects(variable_id):
            if rel.effect not in visited:
                visited.add(rel.effect)
                descendants.add(rel.effect)
                descendants.update(self.get_descendants(rel.effect, visited))

        return descendants


@dataclass
class CausalPattern:
    """An abstract causal pattern that can be transferred"""
    id: str
    name: str
    description: str
    structure_template: Dict[str, Any]  # Abstract structure
    variable_roles: List[str]  # e.g., ["driver", "mediator", "outcome"]
    relation_pattern: List[Tuple[str, str, CausalRelationType]]
    constraints: List[Dict[str, Any]] = field(default_factory=list)
    applicable_domains: List[DomainType] = field(default_factory=list)
    abstraction_level: AbstractionLevel = AbstractionLevel.PATTERN
    instances: List[str] = field(default_factory=list)  # Structure IDs

    def matches(self, structure: CausalStructure) -> Tuple[bool, Dict[str, str]]:
        """Check if structure matches this pattern"""
        # Try to find mapping from roles to variables
        if len(structure.variables) < len(self.variable_roles):
            return False, {}

        # Try all permutations
        for perm in itertools.permutations(structure.variables.keys(), len(self.variable_roles)):
            mapping = dict(zip(self.variable_roles, perm))

            # Check if relations match
            matches_all = True
            for role1, role2, rel_type in self.relation_pattern:
                var1 = mapping.get(role1)
                var2 = mapping.get(role2)

                # Check if relation exists
                found = False
                for rel in structure.relations.values():
                    if rel.cause == var1 and rel.effect == var2:
                        if rel.relation_type == rel_type or rel_type == CausalRelationType.DIRECT:
                            found = True
                            break

                if not found:
                    matches_all = False
                    break

            if matches_all:
                return True, mapping

        return False, {}


@dataclass
class CausalInference:
    """Result of a causal inference"""
    query: str
    result: Any
    confidence: float
    reasoning_path: List[str]
    evidence_used: List[str]
    assumptions: List[str]


class CausalPatternLibrary:
    """
    Library of universal causal patterns.
    """

    def __init__(self):
        self.patterns: Dict[str, CausalPattern] = {}
        self._initialize_universal_patterns()

    def _initialize_universal_patterns(self):
        """Initialize universal causal patterns"""
        # Chain pattern: A -> B -> C
        self.add_pattern(CausalPattern(
            id="pattern_chain",
            name="Causal Chain",
            description="Linear causal transmission",
            structure_template={'type': 'chain', 'length': 3},
            variable_roles=["source", "mediator", "target"],
            relation_pattern=[
                ("source", "mediator", CausalRelationType.DIRECT),
                ("mediator", "target", CausalRelationType.DIRECT)
            ],
            applicable_domains=list(DomainType),
            abstraction_level=AbstractionLevel.PATTERN
        ))

        # Fork pattern: A <- C -> B (common cause)
        self.add_pattern(CausalPattern(
            id="pattern_fork",
            name="Common Cause Fork",
            description="Common cause induces correlation",
            structure_template={'type': 'fork'},
            variable_roles=["cause", "effect1", "effect2"],
            relation_pattern=[
                ("cause", "effect1", CausalRelationType.DIRECT),
                ("cause", "effect2", CausalRelationType.DIRECT)
            ],
            applicable_domains=list(DomainType),
            abstraction_level=AbstractionLevel.PATTERN
        ))

        # Collider pattern: A -> C <- B
        self.add_pattern(CausalPattern(
            id="pattern_collider",
            name="Collider",
            description="Multiple causes converge",
            structure_template={'type': 'collider'},
            variable_roles=["cause1", "cause2", "effect"],
            relation_pattern=[
                ("cause1", "effect", CausalRelationType.DIRECT),
                ("cause2", "effect", CausalRelationType.DIRECT)
            ],
            applicable_domains=list(DomainType),
            abstraction_level=AbstractionLevel.PATTERN
        ))

        # Feedback loop: A <-> B
        self.add_pattern(CausalPattern(
            id="pattern_feedback",
            name="Feedback Loop",
            description="Mutual causation / feedback",
            structure_template={'type': 'feedback'},
            variable_roles=["variable1", "variable2"],
            relation_pattern=[
                ("variable1", "variable2", CausalRelationType.DIRECT),
                ("variable2", "variable1", CausalRelationType.FEEDBACK)
            ],
            applicable_domains=list(DomainType),
            abstraction_level=AbstractionLevel.PATTERN
        ))

        # Threshold trigger: A -> B only if A > threshold
        self.add_pattern(CausalPattern(
            id="pattern_threshold",
            name="Threshold Trigger",
            description="Effect only above threshold",
            structure_template={'type': 'threshold'},
            variable_roles=["trigger", "outcome"],
            relation_pattern=[
                ("trigger", "outcome", CausalRelationType.THRESHOLD)
            ],
            applicable_domains=list(DomainType),
            abstraction_level=AbstractionLevel.PATTERN
        ))

        # Delayed effect: A -> B with time delay
        self.add_pattern(CausalPattern(
            id="pattern_delayed",
            name="Delayed Effect",
            description="Effect occurs after delay",
            structure_template={'type': 'delayed'},
            variable_roles=["cause", "delayed_effect"],
            relation_pattern=[
                ("cause", "delayed_effect", CausalRelationType.DELAYED)
            ],
            applicable_domains=list(DomainType),
            abstraction_level=AbstractionLevel.PATTERN
        ))

        # Inhibition: A inhibits B -> C
        self.add_pattern(CausalPattern(
            id="pattern_inhibition",
            name="Causal Inhibition",
            description="One factor inhibits another's effect",
            structure_template={'type': 'inhibition'},
            variable_roles=["inhibitor", "cause", "effect"],
            relation_pattern=[
                ("cause", "effect", CausalRelationType.DIRECT),
                ("inhibitor", "effect", CausalRelationType.DIRECT)  # Negative
            ],
            constraints=[{'relation': 1, 'sign': 'negative'}],
            applicable_domains=list(DomainType),
            abstraction_level=AbstractionLevel.PATTERN
        ))

        # Amplification cascade
        self.add_pattern(CausalPattern(
            id="pattern_cascade",
            name="Amplification Cascade",
            description="Signal amplification through chain",
            structure_template={'type': 'cascade'},
            variable_roles=["trigger", "amplifier1", "amplifier2", "output"],
            relation_pattern=[
                ("trigger", "amplifier1", CausalRelationType.DIRECT),
                ("amplifier1", "amplifier2", CausalRelationType.DIRECT),
                ("amplifier2", "output", CausalRelationType.DIRECT)
            ],
            constraints=[{'amplification': True}],
            applicable_domains=[DomainType.BIOLOGY, DomainType.ECONOMICS, DomainType.SOCIAL],
            abstraction_level=AbstractionLevel.PROCESS
        ))

    def add_pattern(self, pattern: CausalPattern):
        """Add a pattern to the library"""
        self.patterns[pattern.id] = pattern

    def find_matching_patterns(
        self,
        structure: CausalStructure
    ) -> List[Tuple[CausalPattern, Dict[str, str]]]:
        """Find all patterns that match a structure"""
        matches = []
        for pattern in self.patterns.values():
            is_match, mapping = pattern.matches(structure)
            if is_match:
                matches.append((pattern, mapping))
        return matches

    def get_patterns_for_domain(self, domain: DomainType) -> List[CausalPattern]:
        """Get patterns applicable to a domain"""
        return [p for p in self.patterns.values()
                if domain in p.applicable_domains or DomainType.UNIVERSAL in p.applicable_domains]


class CausalDiscoveryEngine:
    """
    Discovers causal structures from data.
    """

    def __init__(self):
        self.discovered_structures: Dict[str, CausalStructure] = {}
        self.independence_cache: Dict[Tuple[str, str], float] = {}

    def discover_structure(
        self,
        data: Dict[str, np.ndarray],
        domain: DomainType = DomainType.ABSTRACT,
        method: str = "pc"
    ) -> CausalStructure:
        """Discover causal structure from data"""
        variables = list(data.keys())

        # Create structure
        structure = CausalStructure(
            id=f"structure_{time.time()}_{np.random.randint(10000)}",
            name=f"discovered_{domain.value}",
            domain=domain
        )

        # Add variables
        for var_name in variables:
            var_data = data[var_name]
            structure.add_variable(CausalVariable(
                id=f"var_{var_name}",
                name=var_name,
                domain=domain,
                abstraction_level=AbstractionLevel.MECHANISM,
                value_type="continuous" if np.issubdtype(var_data.dtype, np.floating) else "discrete",
                value_range=(float(np.min(var_data)), float(np.max(var_data)))
            ))

        # Discover relations using selected method
        if method == "pc":
            relations = self._pc_algorithm(data, variables)
        elif method == "correlation":
            relations = self._correlation_based(data, variables)
        else:
            relations = self._granger_based(data, variables)

        for rel in relations:
            structure.add_relation(rel)

        self.discovered_structures[structure.id] = structure
        return structure

    def _pc_algorithm(
        self,
        data: Dict[str, np.ndarray],
        variables: List[str]
    ) -> List[CausalRelation]:
        """PC algorithm for causal discovery"""
        n = len(variables)
        relations = []

        # Start with complete undirected graph
        adjacency = np.ones((n, n)) - np.eye(n)

        # Remove edges based on conditional independence
        for i in range(n):
            for j in range(i + 1, n):
                # Test marginal independence
                indep = self._test_independence(
                    data[variables[i]],
                    data[variables[j]]
                )
                if indep > 0.05:  # p-value threshold
                    adjacency[i, j] = 0
                    adjacency[j, i] = 0

        # Orient edges based on v-structures
        for i in range(n):
            for j in range(n):
                if adjacency[i, j] > 0:
                    # Determine direction using temporal or correlation asymmetry
                    corr = np.corrcoef(data[variables[i]], data[variables[j]])[0, 1]

                    # Use variance ratio as heuristic for direction
                    var_i = np.var(data[variables[i]])
                    var_j = np.var(data[variables[j]])

                    if var_i > var_j * 1.2:
                        # i likely causes j
                        relations.append(CausalRelation(
                            id=f"rel_{variables[i]}_{variables[j]}",
                            cause=f"var_{variables[i]}",
                            effect=f"var_{variables[j]}",
                            relation_type=CausalRelationType.DIRECT,
                            strength=self._correlation_to_strength(abs(corr)),
                            confidence=min(0.9, abs(corr) + 0.2),
                            functional_form="linear",
                            parameters={'slope': corr}
                        ))

        return relations

    def _correlation_based(
        self,
        data: Dict[str, np.ndarray],
        variables: List[str]
    ) -> List[CausalRelation]:
        """Simple correlation-based discovery"""
        relations = []

        for i, var_i in enumerate(variables):
            for j, var_j in enumerate(variables):
                if i >= j:
                    continue

                corr = np.corrcoef(data[var_i], data[var_j])[0, 1]
                if abs(corr) > 0.3:
                    relations.append(CausalRelation(
                        id=f"rel_{var_i}_{var_j}",
                        cause=f"var_{var_i}",
                        effect=f"var_{var_j}",
                        relation_type=CausalRelationType.PROBABILISTIC,
                        strength=self._correlation_to_strength(abs(corr)),
                        confidence=abs(corr),
                        functional_form="linear",
                        parameters={'slope': corr}
                    ))

        return relations

    def _granger_based(
        self,
        data: Dict[str, np.ndarray],
        variables: List[str]
    ) -> List[CausalRelation]:
        """Granger causality based discovery for time series"""
        relations = []

        for i, var_i in enumerate(variables):
            for j, var_j in enumerate(variables):
                if i == j:
                    continue

                # Simple Granger test: does lagged i predict j?
                x = data[var_i][:-1]
                y = data[var_j][1:]

                if len(x) > 10:
                    corr = np.corrcoef(x, y)[0, 1]
                    if abs(corr) > 0.2:
                        relations.append(CausalRelation(
                            id=f"rel_{var_i}_{var_j}_granger",
                            cause=f"var_{var_i}",
                            effect=f"var_{var_j}",
                            relation_type=CausalRelationType.DELAYED,
                            strength=self._correlation_to_strength(abs(corr)),
                            confidence=abs(corr),
                            delay=1.0,
                            functional_form="linear",
                            parameters={'slope': corr}
                        ))

        return relations

    def _test_independence(self, x: np.ndarray, y: np.ndarray) -> float:
        """Test independence (returns p-value)"""
        if len(x) != len(y) or len(x) < 3:
            return 1.0

        corr = np.corrcoef(x, y)[0, 1]
        if np.isnan(corr):
            return 1.0

        # Fisher z-transformation for p-value
        n = len(x)
        z = 0.5 * np.log((1 + corr) / (1 - corr + 1e-10))
        se = 1 / np.sqrt(n - 3)
        p_value = 2 * (1 - 0.5 * (1 + np.math.erf(abs(z) / (se * np.sqrt(2)))))

        return p_value

    def _correlation_to_strength(self, corr: float) -> CausalStrength:
        """Convert correlation to causal strength"""
        if corr > 0.9:
            return CausalStrength.DETERMINISTIC
        elif corr > 0.7:
            return CausalStrength.STRONG
        elif corr > 0.4:
            return CausalStrength.MODERATE
        elif corr > 0.2:
            return CausalStrength.WEAK
        else:
            return CausalStrength.UNCERTAIN


class CausalTransferEngine:
    """
    Transfers causal knowledge between domains.
    """

    def __init__(self, pattern_library: CausalPatternLibrary):
        self.pattern_library = pattern_library
        self.transfer_history: List[Dict[str, Any]] = []
        self.domain_mappings: Dict[Tuple[str, str], Dict[str, str]] = {}

    def abstract_structure(
        self,
        structure: CausalStructure
    ) -> CausalPattern:
        """Abstract a concrete structure to a pattern"""
        # Find matching patterns
        matches = self.pattern_library.find_matching_patterns(structure)

        if matches:
            # Return best match
            return matches[0][0]

        # Create new pattern from structure
        variable_roles = [f"role_{i}" for i in range(len(structure.variables))]
        var_to_role = dict(zip(structure.variables.keys(), variable_roles))

        relation_pattern = [
            (var_to_role[r.cause], var_to_role[r.effect], r.relation_type)
            for r in structure.relations.values()
        ]

        pattern = CausalPattern(
            id=f"pattern_from_{structure.id}",
            name=f"abstracted_{structure.name}",
            description=f"Pattern abstracted from {structure.domain.value}",
            structure_template={'source': structure.id},
            variable_roles=variable_roles,
            relation_pattern=relation_pattern,
            applicable_domains=[structure.domain],
            abstraction_level=AbstractionLevel.PATTERN
        )

        self.pattern_library.add_pattern(pattern)
        return pattern

    def transfer_to_domain(
        self,
        source_structure: CausalStructure,
        target_domain: DomainType,
        target_variables: Dict[str, CausalVariable]
    ) -> CausalStructure:
        """Transfer causal structure to new domain"""
        # Abstract source
        pattern = self.abstract_structure(source_structure)

        # Create mapping from roles to target variables
        if len(target_variables) < len(pattern.variable_roles):
            raise ValueError("Not enough target variables for pattern")

        role_mapping = dict(zip(pattern.variable_roles, target_variables.keys()))

        # Create new structure
        transferred = CausalStructure(
            id=f"transferred_{source_structure.id}_{target_domain.value}",
            name=f"transferred_from_{source_structure.domain.value}",
            domain=target_domain,
            abstraction_level=source_structure.abstraction_level,
            confidence=source_structure.confidence * 0.8,  # Reduce confidence for transfer
            source_structures=[source_structure.id]
        )

        # Add variables
        for var in target_variables.values():
            transferred.add_variable(var)

        # Transfer relations
        for role1, role2, rel_type in pattern.relation_pattern:
            var1_id = role_mapping.get(role1)
            var2_id = role_mapping.get(role2)

            if var1_id and var2_id:
                # Find original relation for parameters
                original_rel = None
                for rel in source_structure.relations.values():
                    if rel.relation_type == rel_type:
                        original_rel = rel
                        break

                transferred.add_relation(CausalRelation(
                    id=f"rel_{var1_id}_{var2_id}_transferred",
                    cause=var1_id,
                    effect=var2_id,
                    relation_type=rel_type,
                    strength=original_rel.strength if original_rel else CausalStrength.MODERATE,
                    confidence=0.5,  # Lower confidence for transferred relations
                    functional_form=original_rel.functional_form if original_rel else "linear",
                    parameters=original_rel.parameters.copy() if original_rel else {},
                    discovered_from=source_structure.domain.value
                ))

        self.transfer_history.append({
            'source': source_structure.id,
            'target': transferred.id,
            'pattern': pattern.id,
            'timestamp': time.time()
        })

        return transferred

    def find_analogous_structures(
        self,
        structure: CausalStructure,
        domain: DomainType
    ) -> List[Tuple[CausalStructure, float]]:
        """Find analogous structures in another domain"""
        # Get pattern
        matches = self.pattern_library.find_matching_patterns(structure)

        if not matches:
            return []

        pattern = matches[0][0]

        # Find structures with same pattern in target domain
        # (In practice, would search a database)
        return []


class CausalInterventionEngine:
    """
    Reasons about interventions and counterfactuals.
    """

    def __init__(self):
        self.intervention_history: List[Dict[str, Any]] = []

    def do_intervention(
        self,
        structure: CausalStructure,
        variable_id: str,
        value: float
    ) -> Dict[str, float]:
        """Perform do(X=x) intervention"""
        results = {}

        # Get descendants (affected by intervention)
        descendants = structure.get_descendants(variable_id)

        # Set intervened variable
        results[variable_id] = value

        # Propagate effects
        processed = {variable_id}
        queue = [(variable_id, value)]

        while queue:
            current_id, current_value = queue.pop(0)

            for rel in structure.get_effects(current_id):
                effect_id = rel.effect
                if effect_id in processed:
                    continue

                effect_value = rel.compute_effect(current_value)
                results[effect_id] = effect_value
                processed.add(effect_id)
                queue.append((effect_id, effect_value))

        return results

    def compute_counterfactual(
        self,
        structure: CausalStructure,
        factual_values: Dict[str, float],
        counterfactual_intervention: Dict[str, float]
    ) -> Dict[str, float]:
        """Compute counterfactual: given factual, what if intervention?"""
        # Step 1: Abduction - infer exogenous variables
        # (Simplified: use factual values as base)

        # Step 2: Action - apply intervention
        results = factual_values.copy()
        results.update(counterfactual_intervention)

        # Step 3: Prediction - propagate effects
        for var_id, value in counterfactual_intervention.items():
            descendants = structure.get_descendants(var_id)
            effects = self.do_intervention(structure, var_id, value)
            results.update(effects)

        return results

    def estimate_causal_effect(
        self,
        structure: CausalStructure,
        cause_id: str,
        effect_id: str,
        data: Optional[Dict[str, np.ndarray]] = None
    ) -> float:
        """Estimate average causal effect"""
        # Check if direct path exists
        path_exists = effect_id in structure.get_descendants(cause_id)
        if not path_exists:
            return 0.0

        # Find direct relations on path
        total_effect = 1.0
        current = cause_id
        visited = set()

        while current != effect_id and current not in visited:
            visited.add(current)
            for rel in structure.get_effects(current):
                if rel.effect in structure.get_descendants(cause_id) | {effect_id}:
                    # Apply effect computation
                    strength_map = {
                        CausalStrength.DETERMINISTIC: 1.0,
                        CausalStrength.STRONG: 0.8,
                        CausalStrength.MODERATE: 0.5,
                        CausalStrength.WEAK: 0.2,
                        CausalStrength.UNCERTAIN: 0.1
                    }
                    total_effect *= strength_map.get(rel.strength, 0.5)
                    current = rel.effect
                    break
            else:
                break

        return total_effect


class UniversalCausalSubstrate:
    """
    The complete universal causal reasoning system.
    """

    def __init__(self):
        self.pattern_library = CausalPatternLibrary()
        self.discovery_engine = CausalDiscoveryEngine()
        self.transfer_engine = CausalTransferEngine(self.pattern_library)
        self.intervention_engine = CausalInterventionEngine()

        self.structures: Dict[str, CausalStructure] = {}
        self.domain_structures: Dict[DomainType, List[str]] = defaultdict(list)

        self.stats = {
            'structures_discovered': 0,
            'patterns_learned': 0,
            'transfers_performed': 0,
            'interventions_computed': 0
        }

    def discover_causal_structure(
        self,
        data: Dict[str, np.ndarray],
        domain: DomainType = DomainType.ABSTRACT,
        method: str = "pc"
    ) -> CausalStructure:
        """Discover causal structure from data"""
        structure = self.discovery_engine.discover_structure(data, domain, method)
        self.structures[structure.id] = structure
        self.domain_structures[domain].append(structure.id)
        self.stats['structures_discovered'] += 1

        # Try to match to patterns
        matches = self.pattern_library.find_matching_patterns(structure)
        for pattern, _ in matches:
            pattern.instances.append(structure.id)

        return structure

    def transfer_knowledge(
        self,
        source_structure_id: str,
        target_domain: DomainType,
        target_variables: Dict[str, CausalVariable]
    ) -> CausalStructure:
        """Transfer causal knowledge to new domain"""
        source = self.structures.get(source_structure_id)
        if not source:
            raise ValueError(f"Structure {source_structure_id} not found")

        transferred = self.transfer_engine.transfer_to_domain(
            source, target_domain, target_variables
        )

        self.structures[transferred.id] = transferred
        self.domain_structures[target_domain].append(transferred.id)
        self.stats['transfers_performed'] += 1

        return transferred

    def intervene(
        self,
        structure_id: str,
        variable_id: str,
        value: float
    ) -> Dict[str, float]:
        """Perform intervention"""
        structure = self.structures.get(structure_id)
        if not structure:
            raise ValueError(f"Structure {structure_id} not found")

        result = self.intervention_engine.do_intervention(structure, variable_id, value)
        self.stats['interventions_computed'] += 1
        return result

    def counterfactual(
        self,
        structure_id: str,
        factual: Dict[str, float],
        intervention: Dict[str, float]
    ) -> Dict[str, float]:
        """Compute counterfactual"""
        structure = self.structures.get(structure_id)
        if not structure:
            raise ValueError(f"Structure {structure_id} not found")

        return self.intervention_engine.compute_counterfactual(
            structure, factual, intervention
        )

    def get_causal_effect(
        self,
        structure_id: str,
        cause: str,
        effect: str
    ) -> float:
        """Get estimated causal effect"""
        structure = self.structures.get(structure_id)
        if not structure:
            return 0.0

        return self.intervention_engine.estimate_causal_effect(
            structure, cause, effect
        )

    def find_universal_patterns(self) -> List[CausalPattern]:
        """Find patterns that appear across multiple domains"""
        pattern_domain_counts = defaultdict(set)

        for domain, structure_ids in self.domain_structures.items():
            for sid in structure_ids:
                structure = self.structures.get(sid)
                if structure:
                    matches = self.pattern_library.find_matching_patterns(structure)
                    for pattern, _ in matches:
                        pattern_domain_counts[pattern.id].add(domain)

        # Patterns appearing in 2+ domains
        universal = []
        for pattern_id, domains in pattern_domain_counts.items():
            if len(domains) >= 2:
                pattern = self.pattern_library.patterns.get(pattern_id)
                if pattern:
                    universal.append(pattern)
                    self.stats['patterns_learned'] += 1

        return universal

    def get_stats(self) -> Dict[str, Any]:
        """Get system statistics"""
        return {
            **self.stats,
            'total_structures': len(self.structures),
            'total_patterns': len(self.pattern_library.patterns),
            'domains_covered': len(self.domain_structures)
        }


# Factory functions
def create_universal_causal_substrate() -> UniversalCausalSubstrate:
    """Create the universal causal substrate"""
    return UniversalCausalSubstrate()


def create_causal_pattern_library() -> CausalPatternLibrary:
    """Create a causal pattern library"""
    return CausalPatternLibrary()


def create_causal_discovery_engine() -> CausalDiscoveryEngine:
    """Create a causal discovery engine"""
    return CausalDiscoveryEngine()


def discover_causal_structure(
    data: Dict[str, np.ndarray],
    domain: DomainType = DomainType.ABSTRACT
) -> CausalStructure:
    """Convenience function to discover causal structure"""
    engine = CausalDiscoveryEngine()
    return engine.discover_structure(data, domain)


# Exports
__all__ = [
    # Enums
    'CausalRelationType',
    'CausalStrength',
    'AbstractionLevel',
    'DomainType',

    # Data classes
    'CausalVariable',
    'CausalRelation',
    'CausalStructure',
    'CausalPattern',
    'CausalInference',

    # Core classes
    'CausalPatternLibrary',
    'CausalDiscoveryEngine',
    'CausalTransferEngine',
    'CausalInterventionEngine',
    'UniversalCausalSubstrate',

    # Factory functions
    'create_universal_causal_substrate',
    'create_causal_pattern_library',
    'create_causal_discovery_engine',
    'discover_causal_structure',
]


