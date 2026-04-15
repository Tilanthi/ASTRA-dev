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
V70 Algorithmic Discovery Engine
================================

Discovers new computational primitives and algorithms through:
- Genetic programming over algorithm space
- Program synthesis with learned primitives
- Algorithm performance prediction
- Computational primitive invention

This enables STAN to discover methods humans haven't conceived,
rather than just applying known algorithms.

Key Innovation: The system doesn't just SELECT algorithms, it INVENTS them.
"""

from dataclasses import dataclass, field
from typing import Dict, List, Optional, Any, Set, Tuple, Callable, Union, TypeVar
from enum import Enum
from abc import ABC, abstractmethod
import numpy as np
from collections import defaultdict
import copy
import time
import hashlib
import random


T = TypeVar('T')


class PrimitiveType(Enum):
    """Types of computational primitives"""
    ARITHMETIC = "arithmetic"
    LOGICAL = "logical"
    STATISTICAL = "statistical"
    STRUCTURAL = "structural"
    TEMPORAL = "temporal"
    RELATIONAL = "relational"
    TRANSFORMATIONAL = "transformational"
    COMPOSITIONAL = "compositional"


class AlgorithmClass(Enum):
    """Classes of algorithms"""
    OPTIMIZATION = "optimization"
    SEARCH = "search"
    INFERENCE = "inference"
    PREDICTION = "prediction"
    CLUSTERING = "clustering"
    TRANSFORMATION = "transformation"
    GENERATION = "generation"
    COMPRESSION = "compression"


class EvolutionStrategy(Enum):
    """Strategies for evolving algorithms"""
    MUTATION = "mutation"
    CROSSOVER = "crossover"
    RECOMBINATION = "recombination"
    SIMPLIFICATION = "simplification"
    ELABORATION = "elaboration"
    HYBRIDIZATION = "hybridization"


@dataclass
class ComputationalPrimitive:
    """A fundamental computational building block"""
    id: str
    name: str
    primitive_type: PrimitiveType
    arity: int  # Number of inputs
    operation: Callable
    inverse: Optional[Callable] = None
    complexity: float = 1.0
    discovered: bool = False  # True if invented by the system
    performance_profile: Dict[str, float] = field(default_factory=dict)

    def execute(self, *args) -> Any:
        """Execute the primitive operation"""
        if len(args) != self.arity:
            raise ValueError(f"Expected {self.arity} args, got {len(args)}")
        return self.operation(*args)

    def __hash__(self):
        return hash(self.id)


@dataclass
class AlgorithmNode:
    """A node in an algorithm tree"""
    primitive: ComputationalPrimitive
    children: List['AlgorithmNode'] = field(default_factory=list)
    parameters: Dict[str, Any] = field(default_factory=dict)
    node_id: str = ""

    def __post_init__(self):
        if not self.node_id:
            self.node_id = f"node_{time.time()}_{random.randint(0, 10000)}"

    def execute(self, inputs: Dict[str, Any]) -> Any:
        """Execute this node and its subtree"""
        child_results = [child.execute(inputs) for child in self.children]

        if self.primitive.arity == 0:
            # Leaf node - get from inputs
            return inputs.get(self.parameters.get('input_key', 'x'), 0)

        return self.primitive.execute(*child_results[:self.primitive.arity])

    def depth(self) -> int:
        """Get depth of subtree"""
        if not self.children:
            return 1
        return 1 + max(child.depth() for child in self.children)

    def size(self) -> int:
        """Get number of nodes in subtree"""
        return 1 + sum(child.size() for child in self.children)


@dataclass
class DiscoveredAlgorithm:
    """A discovered or evolved algorithm"""
    id: str
    name: str
    algorithm_class: AlgorithmClass
    root: AlgorithmNode
    fitness: float = 0.0
    complexity: float = 0.0
    generalization_score: float = 0.0
    novelty_score: float = 0.0
    generation: int = 0
    parent_ids: List[str] = field(default_factory=list)
    performance_history: List[Dict[str, float]] = field(default_factory=list)
    discovered_at: float = field(default_factory=time.time)

    def execute(self, inputs: Dict[str, Any]) -> Any:
        """Execute the algorithm"""
        return self.root.execute(inputs)

    def get_complexity(self) -> float:
        """Calculate algorithm complexity"""
        return self._node_complexity(self.root)

    def _node_complexity(self, node: AlgorithmNode) -> float:
        """Recursively calculate complexity"""
        base = node.primitive.complexity
        child_complexity = sum(self._node_complexity(c) for c in node.children)
        return base + child_complexity


@dataclass
class ProblemInstance:
    """A problem instance for testing algorithms"""
    id: str
    inputs: Dict[str, Any]
    expected_output: Any
    difficulty: float = 0.5
    problem_class: str = "general"
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class AlgorithmEvaluation:
    """Evaluation results for an algorithm"""
    algorithm_id: str
    accuracy: float
    efficiency: float
    generalization: float
    novelty: float
    composite_fitness: float
    test_cases_passed: int
    test_cases_total: int
    execution_time: float


class PrimitiveLibrary:
    """
    Library of computational primitives that can be discovered and expanded.
    """

    def __init__(self):
        self.primitives: Dict[str, ComputationalPrimitive] = {}
        self.discovered_primitives: Dict[str, ComputationalPrimitive] = {}
        self._initialize_core_primitives()

    def _initialize_core_primitives(self):
        """Initialize core computational primitives"""
        # Arithmetic primitives
        self._add_primitive("add", PrimitiveType.ARITHMETIC, 2, lambda a, b: a + b)
        self._add_primitive("sub", PrimitiveType.ARITHMETIC, 2, lambda a, b: a - b)
        self._add_primitive("mul", PrimitiveType.ARITHMETIC, 2, lambda a, b: a * b)
        self._add_primitive("div", PrimitiveType.ARITHMETIC, 2,
                           lambda a, b: a / b if b != 0 else 0)
        self._add_primitive("pow", PrimitiveType.ARITHMETIC, 2,
                           lambda a, b: np.power(a, b) if abs(b) < 10 else a)
        self._add_primitive("sqrt", PrimitiveType.ARITHMETIC, 1,
                           lambda a: np.sqrt(abs(a)))
        self._add_primitive("log", PrimitiveType.ARITHMETIC, 1,
                           lambda a: np.log(abs(a) + 1e-10))
        self._add_primitive("exp", PrimitiveType.ARITHMETIC, 1,
                           lambda a: np.exp(np.clip(a, -20, 20)))
        self._add_primitive("abs", PrimitiveType.ARITHMETIC, 1, lambda a: abs(a))
        self._add_primitive("neg", PrimitiveType.ARITHMETIC, 1, lambda a: -a)

        # Statistical primitives
        self._add_primitive("mean", PrimitiveType.STATISTICAL, 1,
                           lambda a: np.mean(a) if hasattr(a, '__iter__') else a)
        self._add_primitive("std", PrimitiveType.STATISTICAL, 1,
                           lambda a: np.std(a) if hasattr(a, '__iter__') else 0)
        self._add_primitive("max", PrimitiveType.STATISTICAL, 2, lambda a, b: max(a, b))
        self._add_primitive("min", PrimitiveType.STATISTICAL, 2, lambda a, b: min(a, b))
        self._add_primitive("sum", PrimitiveType.STATISTICAL, 1,
                           lambda a: np.sum(a) if hasattr(a, '__iter__') else a)

        # Logical primitives
        self._add_primitive("and", PrimitiveType.LOGICAL, 2, lambda a, b: a and b)
        self._add_primitive("or", PrimitiveType.LOGICAL, 2, lambda a, b: a or b)
        self._add_primitive("not", PrimitiveType.LOGICAL, 1, lambda a: not a)
        self._add_primitive("gt", PrimitiveType.LOGICAL, 2, lambda a, b: a > b)
        self._add_primitive("lt", PrimitiveType.LOGICAL, 2, lambda a, b: a < b)
        self._add_primitive("eq", PrimitiveType.LOGICAL, 2, lambda a, b: abs(a - b) < 1e-10)

        # Conditional primitive
        self._add_primitive("if", PrimitiveType.LOGICAL, 3,
                           lambda c, t, f: t if c else f, complexity=2.0)

        # Structural primitives
        self._add_primitive("first", PrimitiveType.STRUCTURAL, 1,
                           lambda a: a[0] if hasattr(a, '__getitem__') and len(a) > 0 else a)
        self._add_primitive("last", PrimitiveType.STRUCTURAL, 1,
                           lambda a: a[-1] if hasattr(a, '__getitem__') and len(a) > 0 else a)
        self._add_primitive("len", PrimitiveType.STRUCTURAL, 1,
                           lambda a: len(a) if hasattr(a, '__len__') else 1)

        # Temporal primitives
        self._add_primitive("diff", PrimitiveType.TEMPORAL, 1,
                           lambda a: np.diff(a) if hasattr(a, '__iter__') and len(a) > 1 else 0)
        self._add_primitive("cumsum", PrimitiveType.TEMPORAL, 1,
                           lambda a: np.cumsum(a) if hasattr(a, '__iter__') else a)
        self._add_primitive("lag", PrimitiveType.TEMPORAL, 2,
                           lambda a, n: a[:-int(n)] if hasattr(a, '__getitem__') and len(a) > n else a)

        # Transformational primitives
        self._add_primitive("normalize", PrimitiveType.TRANSFORMATIONAL, 1,
                           lambda a: (a - np.mean(a)) / (np.std(a) + 1e-10) if hasattr(a, '__iter__') else 0)
        self._add_primitive("scale", PrimitiveType.TRANSFORMATIONAL, 2,
                           lambda a, s: a * s)
        self._add_primitive("clip", PrimitiveType.TRANSFORMATIONAL, 3,
                           lambda a, lo, hi: np.clip(a, lo, hi))

        # Relational primitives
        self._add_primitive("corr", PrimitiveType.RELATIONAL, 2,
                           lambda a, b: np.corrcoef(a, b)[0, 1] if hasattr(a, '__iter__') and hasattr(b, '__iter__') and len(a) == len(b) > 1 else 0)
        self._add_primitive("dist", PrimitiveType.RELATIONAL, 2,
                           lambda a, b: np.sqrt(np.sum((np.array(a) - np.array(b))**2)) if hasattr(a, '__iter__') else abs(a - b))

        # Input primitive (leaf)
        self._add_primitive("input", PrimitiveType.STRUCTURAL, 0, lambda: None, complexity=0.0)
        self._add_primitive("const", PrimitiveType.STRUCTURAL, 0, lambda: 1.0, complexity=0.0)

    def _add_primitive(
        self,
        name: str,
        ptype: PrimitiveType,
        arity: int,
        operation: Callable,
        complexity: float = 1.0
    ):
        """Add a primitive to the library"""
        primitive = ComputationalPrimitive(
            id=f"prim_{name}",
            name=name,
            primitive_type=ptype,
            arity=arity,
            operation=operation,
            complexity=complexity,
            discovered=False
        )
        self.primitives[name] = primitive

    def discover_primitive(
        self,
        name: str,
        ptype: PrimitiveType,
        arity: int,
        operation: Callable,
        complexity: float = 1.5
    ) -> ComputationalPrimitive:
        """Discover a new primitive"""
        primitive = ComputationalPrimitive(
            id=f"discovered_{name}_{time.time()}",
            name=name,
            primitive_type=ptype,
            arity=arity,
            operation=operation,
            complexity=complexity,
            discovered=True
        )
        self.discovered_primitives[name] = primitive
        self.primitives[name] = primitive
        return primitive

    def get_primitive(self, name: str) -> Optional[ComputationalPrimitive]:
        """Get primitive by name"""
        return self.primitives.get(name)

    def get_primitives_by_type(self, ptype: PrimitiveType) -> List[ComputationalPrimitive]:
        """Get all primitives of a type"""
        return [p for p in self.primitives.values() if p.primitive_type == ptype]

    def get_all_primitives(self) -> List[ComputationalPrimitive]:
        """Get all primitives"""
        return list(self.primitives.values())


class AlgorithmGenerator:
    """
    Generates new algorithms through various synthesis methods.
    """

    def __init__(self, library: PrimitiveLibrary):
        self.library = library
        self.max_depth = 6
        self.max_size = 50

    def generate_random(
        self,
        algorithm_class: AlgorithmClass,
        depth: int = 3,
        input_keys: List[str] = None
    ) -> DiscoveredAlgorithm:
        """Generate a random algorithm tree"""
        input_keys = input_keys or ['x']
        root = self._generate_random_node(depth, input_keys)

        return DiscoveredAlgorithm(
            id=f"algo_{time.time()}_{random.randint(0, 10000)}",
            name=f"generated_{algorithm_class.value}",
            algorithm_class=algorithm_class,
            root=root,
            generation=0
        )

    def _generate_random_node(
        self,
        depth: int,
        input_keys: List[str]
    ) -> AlgorithmNode:
        """Generate a random node"""
        if depth <= 1:
            # Leaf node
            prim = self.library.get_primitive("input")
            return AlgorithmNode(
                primitive=prim,
                parameters={'input_key': random.choice(input_keys)}
            )

        # Choose random primitive
        primitives = [p for p in self.library.get_all_primitives() if p.arity > 0]
        prim = random.choice(primitives)

        # Generate children
        children = []
        for _ in range(prim.arity):
            child_depth = depth - 1 if random.random() < 0.7 else 1
            children.append(self._generate_random_node(child_depth, input_keys))

        return AlgorithmNode(primitive=prim, children=children)

    def generate_from_template(
        self,
        template: str,
        algorithm_class: AlgorithmClass
    ) -> DiscoveredAlgorithm:
        """Generate algorithm from a template pattern"""
        templates = {
            'moving_average': self._template_moving_average,
            'gradient': self._template_gradient,
            'normalize_transform': self._template_normalize,
            'ratio': self._template_ratio,
            'threshold': self._template_threshold
        }

        if template in templates:
            root = templates[template]()
        else:
            root = self._generate_random_node(3, ['x'])

        return DiscoveredAlgorithm(
            id=f"algo_template_{template}_{time.time()}",
            name=f"{template}_{algorithm_class.value}",
            algorithm_class=algorithm_class,
            root=root,
            generation=0
        )

    def _template_moving_average(self) -> AlgorithmNode:
        """Moving average template"""
        mean_prim = self.library.get_primitive("mean")
        input_prim = self.library.get_primitive("input")

        return AlgorithmNode(
            primitive=mean_prim,
            children=[AlgorithmNode(primitive=input_prim, parameters={'input_key': 'x'})]
        )

    def _template_gradient(self) -> AlgorithmNode:
        """Gradient/difference template"""
        diff_prim = self.library.get_primitive("diff")
        input_prim = self.library.get_primitive("input")

        return AlgorithmNode(
            primitive=diff_prim,
            children=[AlgorithmNode(primitive=input_prim, parameters={'input_key': 'x'})]
        )

    def _template_normalize(self) -> AlgorithmNode:
        """Normalization template"""
        norm_prim = self.library.get_primitive("normalize")
        input_prim = self.library.get_primitive("input")

        return AlgorithmNode(
            primitive=norm_prim,
            children=[AlgorithmNode(primitive=input_prim, parameters={'input_key': 'x'})]
        )

    def _template_ratio(self) -> AlgorithmNode:
        """Ratio template"""
        div_prim = self.library.get_primitive("div")
        input_prim = self.library.get_primitive("input")

        return AlgorithmNode(
            primitive=div_prim,
            children=[
                AlgorithmNode(primitive=input_prim, parameters={'input_key': 'x'}),
                AlgorithmNode(primitive=input_prim, parameters={'input_key': 'y'})
            ]
        )

    def _template_threshold(self) -> AlgorithmNode:
        """Threshold template"""
        gt_prim = self.library.get_primitive("gt")
        input_prim = self.library.get_primitive("input")
        const_prim = self.library.get_primitive("const")

        return AlgorithmNode(
            primitive=gt_prim,
            children=[
                AlgorithmNode(primitive=input_prim, parameters={'input_key': 'x'}),
                AlgorithmNode(primitive=const_prim, parameters={'value': 0.5})
            ]
        )


class GeneticAlgorithmEvolver:
    """
    Evolves algorithms using genetic programming.
    """

    def __init__(
        self,
        library: PrimitiveLibrary,
        generator: AlgorithmGenerator,
        population_size: int = 100
    ):
        self.library = library
        self.generator = generator
        self.population_size = population_size
        self.mutation_rate = 0.3
        self.crossover_rate = 0.5
        self.elite_fraction = 0.1
        self.tournament_size = 5

    def evolve(
        self,
        initial_population: List[DiscoveredAlgorithm],
        fitness_function: Callable[[DiscoveredAlgorithm], float],
        generations: int = 50,
        target_fitness: float = 0.95
    ) -> Tuple[List[DiscoveredAlgorithm], List[Dict[str, Any]]]:
        """Evolve population over generations"""
        population = initial_population.copy()
        history = []

        for gen in range(generations):
            # Evaluate fitness
            for algo in population:
                algo.fitness = fitness_function(algo)

            # Sort by fitness
            population.sort(key=lambda a: a.fitness, reverse=True)

            # Record history
            best = population[0]
            avg_fitness = np.mean([a.fitness for a in population])
            history.append({
                'generation': gen,
                'best_fitness': best.fitness,
                'avg_fitness': avg_fitness,
                'best_id': best.id
            })

            # Check termination
            if best.fitness >= target_fitness:
                break

            # Create next generation
            next_gen = []

            # Elite selection
            elite_count = int(self.population_size * self.elite_fraction)
            next_gen.extend(population[:elite_count])

            # Generate offspring
            while len(next_gen) < self.population_size:
                if random.random() < self.crossover_rate:
                    # Crossover
                    parent1 = self._tournament_select(population)
                    parent2 = self._tournament_select(population)
                    child = self._crossover(parent1, parent2)
                else:
                    # Clone and mutate
                    parent = self._tournament_select(population)
                    child = self._clone_algorithm(parent)

                if random.random() < self.mutation_rate:
                    child = self._mutate(child)

                child.generation = gen + 1
                next_gen.append(child)

            population = next_gen

        return population, history

    def _tournament_select(
        self,
        population: List[DiscoveredAlgorithm]
    ) -> DiscoveredAlgorithm:
        """Tournament selection"""
        tournament = random.sample(population, min(self.tournament_size, len(population)))
        return max(tournament, key=lambda a: a.fitness)

    def _crossover(
        self,
        parent1: DiscoveredAlgorithm,
        parent2: DiscoveredAlgorithm
    ) -> DiscoveredAlgorithm:
        """Crossover two algorithms"""
        # Clone parent1
        child = self._clone_algorithm(parent1)
        child.parent_ids = [parent1.id, parent2.id]

        # Find crossover points
        nodes1 = self._get_all_nodes(child.root)
        nodes2 = self._get_all_nodes(parent2.root)

        if len(nodes1) > 1 and len(nodes2) > 0:
            # Select random subtree from parent2
            donor_node = random.choice(nodes2)
            donor_copy = self._clone_node(donor_node)

            # Replace random node in child
            target_idx = random.randint(1, len(nodes1) - 1)
            self._replace_node(child.root, nodes1[target_idx].node_id, donor_copy)

        return child

    def _mutate(self, algorithm: DiscoveredAlgorithm) -> DiscoveredAlgorithm:
        """Mutate an algorithm"""
        mutation_type = random.choice([
            'replace_primitive',
            'add_node',
            'remove_node',
            'swap_children'
        ])

        nodes = self._get_all_nodes(algorithm.root)

        if mutation_type == 'replace_primitive' and len(nodes) > 0:
            node = random.choice(nodes)
            # Find compatible primitive
            compatible = [p for p in self.library.get_all_primitives()
                         if p.arity == node.primitive.arity]
            if compatible:
                node.primitive = random.choice(compatible)

        elif mutation_type == 'add_node' and len(nodes) < 30:
            node = random.choice(nodes)
            if len(node.children) < 3:
                new_child = self.generator._generate_random_node(2, ['x', 'y'])
                node.children.append(new_child)

        elif mutation_type == 'remove_node' and len(nodes) > 3:
            # Find non-root node to remove
            for node in nodes:
                if node.children:
                    if random.random() < 0.5:
                        node.children.pop()
                        break

        elif mutation_type == 'swap_children':
            for node in nodes:
                if len(node.children) >= 2:
                    i, j = random.sample(range(len(node.children)), 2)
                    node.children[i], node.children[j] = node.children[j], node.children[i]
                    break

        return algorithm

    def _clone_algorithm(self, algo: DiscoveredAlgorithm) -> DiscoveredAlgorithm:
        """Deep clone an algorithm"""
        return DiscoveredAlgorithm(
            id=f"algo_{time.time()}_{random.randint(0, 10000)}",
            name=algo.name,
            algorithm_class=algo.algorithm_class,
            root=self._clone_node(algo.root),
            fitness=0.0,
            complexity=algo.complexity,
            generation=algo.generation,
            parent_ids=[algo.id]
        )

    def _clone_node(self, node: AlgorithmNode) -> AlgorithmNode:
        """Deep clone a node"""
        return AlgorithmNode(
            primitive=node.primitive,
            children=[self._clone_node(c) for c in node.children],
            parameters=node.parameters.copy(),
            node_id=f"node_{time.time()}_{random.randint(0, 10000)}"
        )

    def _get_all_nodes(self, root: AlgorithmNode) -> List[AlgorithmNode]:
        """Get all nodes in tree"""
        nodes = [root]
        for child in root.children:
            nodes.extend(self._get_all_nodes(child))
        return nodes

    def _replace_node(
        self,
        root: AlgorithmNode,
        target_id: str,
        replacement: AlgorithmNode
    ) -> bool:
        """Replace node by ID"""
        for i, child in enumerate(root.children):
            if child.node_id == target_id:
                root.children[i] = replacement
                return True
            if self._replace_node(child, target_id, replacement):
                return True
        return False


class AlgorithmEvaluator:
    """
    Evaluates discovered algorithms on problem instances.
    """

    def __init__(self):
        self.evaluation_cache: Dict[str, AlgorithmEvaluation] = {}
        self.novelty_archive: List[DiscoveredAlgorithm] = []

    def evaluate(
        self,
        algorithm: DiscoveredAlgorithm,
        problems: List[ProblemInstance],
        timeout: float = 1.0
    ) -> AlgorithmEvaluation:
        """Evaluate algorithm on problem instances"""
        passed = 0
