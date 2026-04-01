"""
Probabilistic Program Synthesis for STAN V42

Automatically generate forward models from problem descriptions:
- Learn probabilistic programs that explain observations
- Compose existing physics modules into novel configurations
- Discover new emission mechanisms and model unexpected phenomena

Date: 2025-12-11
Version: 42.0
"""

import time
import uuid
import math
import copy
import random
from typing import Dict, List, Optional, Any, Tuple, Set, Callable, Union
from dataclasses import dataclass, field
from enum import Enum
from abc import ABC, abstractmethod
from collections import defaultdict
import re


class ProgramPrimitiveType(Enum):
    """Types of program primitives"""
    CONSTANT = "constant"
    VARIABLE = "variable"
    PARAMETER = "parameter"
    FUNCTION = "function"
    DISTRIBUTION = "distribution"
    OPERATOR = "operator"
    PHYSICS_LAW = "physics_law"
    OBSERVATION_MODEL = "observation_model"


class DistributionType(Enum):
    """Types of probability distributions"""
    NORMAL = "normal"
    LOGNORMAL = "lognormal"
    UNIFORM = "uniform"
    EXPONENTIAL = "exponential"
    GAMMA = "gamma"
    BETA = "beta"
    POISSON = "poisson"
    DIRICHLET = "dirichlet"
    CATEGORICAL = "categorical"


class PhysicsLawType(Enum):
    """Types of physics laws available"""
    GRAVITATIONAL = "gravitational"
    ELECTROMAGNETIC = "electromagnetic"
    THERMODYNAMIC = "thermodynamic"
    RELATIVISTIC = "relativistic"
    QUANTUM = "quantum"
    STATISTICAL = "statistical"
    HYDRODYNAMIC = "hydrodynamic"
    RADIATIVE = "radiative"


@dataclass
class ProgramPrimitive:
    """A primitive element in a probabilistic program"""
    primitive_id: str
    primitive_type: ProgramPrimitiveType
    name: str
    value: Any = None
    parameters: Dict[str, Any] = field(default_factory=dict)
    constraints: List[str] = field(default_factory=list)
    domain: str = ""
    units: str = ""

    def __post_init__(self):
        if not self.primitive_id:
            self.primitive_id = f"prim_{uuid.uuid4().hex[:8]}"


@dataclass
class ProgramNode:
    """A node in a probabilistic program AST"""
    node_id: str
    node_type: str  # "primitive", "application", "let", "observe", "sample"
    primitive: Optional[ProgramPrimitive] = None
    children: List['ProgramNode'] = field(default_factory=list)
    bindings: Dict[str, 'ProgramNode'] = field(default_factory=dict)
    metadata: Dict[str, Any] = field(default_factory=dict)

    def __post_init__(self):
        if not self.node_id:
            self.node_id = f"node_{uuid.uuid4().hex[:8]}"


@dataclass
class ProbabilisticProgram:
    """A complete probabilistic program"""
    program_id: str
    name: str
    description: str

    # Program structure
    root: ProgramNode
    parameters: Dict[str, ProgramPrimitive]
    latent_variables: Dict[str, ProgramPrimitive]
    observations: Dict[str, ProgramPrimitive]

    # Physics constraints
    physics_laws: List[str]
    dimensional_constraints: Dict[str, str]
    conservation_laws: List[str]

    # Metadata
    domain: str = ""
    complexity: float = 0.0
    log_likelihood: float = float('-inf')
    posterior_score: float = 0.0

    created_at: float = field(default_factory=time.time)

    def __post_init__(self):
        if not self.program_id:
            self.program_id = f"prog_{uuid.uuid4().hex[:8]}"


@dataclass
class SynthesisResult:
    """Result of program synthesis"""
    result_id: str
    programs: List[ProbabilisticProgram]
    best_program: Optional[ProbabilisticProgram]
    log_evidence: float
    synthesis_time: float
    iterations: int
    search_path: List[Dict[str, Any]]

    def __post_init__(self):
        if not self.result_id:
            self.result_id = f"synth_{uuid.uuid4().hex[:8]}"


class PhysicsLibrary:
    """
    Library of physics primitives for program synthesis.
    Contains astrophysics-relevant laws and relationships.
    """

    def __init__(self):
        self.primitives: Dict[str, ProgramPrimitive] = {}
        self.compositions: Dict[str, Callable] = {}
        self._load_astrophysics_primitives()

    def _load_astrophysics_primitives(self):
        """Load astrophysics-specific primitives"""

        # Gravitational physics
        self.primitives["newton_gravity"] = ProgramPrimitive(
            primitive_id="",
            primitive_type=ProgramPrimitiveType.PHYSICS_LAW,
            name="Newton's Gravitational Law",
            parameters={"G": 6.674e-8},  # CGS
            constraints=["mass > 0", "radius > 0"],
            domain="gravitational",
            units="dyn"
        )

        self.primitives["kepler_third"] = ProgramPrimitive(
            primitive_id="",
            primitive_type=ProgramPrimitiveType.PHYSICS_LAW,
            name="Kepler's Third Law",
            parameters={},
            constraints=["period > 0", "semi_major_axis > 0"],
            domain="orbital_mechanics",
            units=""
        )

        self.primitives["virial_theorem"] = ProgramPrimitive(
            primitive_id="",
            primitive_type=ProgramPrimitiveType.PHYSICS_LAW,
            name="Virial Theorem",
            parameters={},
            constraints=["kinetic_energy >= 0", "potential_energy <= 0"],
            domain="statistical_mechanics",
            units="erg"
        )

        # Radiative transfer
        self.primitives["planck_function"] = ProgramPrimitive(
            primitive_id="",
            primitive_type=ProgramPrimitiveType.PHYSICS_LAW,
            name="Planck Function",
            parameters={"h": 6.626e-27, "c": 2.998e10, "k": 1.381e-16},
            constraints=["temperature > 0", "frequency > 0"],
            domain="radiative",
            units="erg/s/cm^2/Hz/sr"
        )

        self.primitives["stefan_boltzmann"] = ProgramPrimitive(
            primitive_id="",
            primitive_type=ProgramPrimitiveType.PHYSICS_LAW,
            name="Stefan-Boltzmann Law",
            parameters={"sigma": 5.670e-5},  # CGS
            constraints=["temperature > 0"],
            domain="radiative",
            units="erg/s/cm^2"
        )

        self.primitives["radiative_transfer"] = ProgramPrimitive(
            primitive_id="",
            primitive_type=ProgramPrimitiveType.PHYSICS_LAW,
            name="Radiative Transfer Equation",
            parameters={},
            constraints=["optical_depth >= 0"],
            domain="radiative",
            units="erg/s/cm^2/Hz/sr"
        )

        # Gravitational lensing
        self.primitives["sie_lens"] = ProgramPrimitive(
            primitive_id="",
            primitive_type=ProgramPrimitiveType.PHYSICS_LAW,
            name="Singular Isothermal Ellipsoid",
            parameters={},
            constraints=["velocity_dispersion > 0", "0 < ellipticity < 1"],
            domain="gravitational_lensing",
            units="arcsec"
        )

        self.primitives["nfw_profile"] = ProgramPrimitive(
            primitive_id="",
            primitive_type=ProgramPrimitiveType.PHYSICS_LAW,
            name="NFW Density Profile",
            parameters={},
            constraints=["scale_radius > 0", "concentration > 0"],
            domain="dark_matter",
            units="g/cm^3"
        )

        # Stellar physics
        self.primitives["mass_luminosity"] = ProgramPrimitive(
            primitive_id="",
            primitive_type=ProgramPrimitiveType.PHYSICS_LAW,
            name="Mass-Luminosity Relation",
            parameters={"exponent": 3.5},
            constraints=["mass > 0"],
            domain="stellar",
            units="L_sun"
        )

        self.primitives["hydrostatic_equilibrium"] = ProgramPrimitive(
            primitive_id="",
            primitive_type=ProgramPrimitiveType.PHYSICS_LAW,
            name="Hydrostatic Equilibrium",
            parameters={},
            constraints=["pressure > 0", "density > 0"],
            domain="stellar",
            units="dyn/cm^2"
        )

        # Cosmology
        self.primitives["friedmann"] = ProgramPrimitive(
            primitive_id="",
            primitive_type=ProgramPrimitiveType.PHYSICS_LAW,
            name="Friedmann Equation",
            parameters={"H0": 70.0},  # km/s/Mpc
            constraints=["scale_factor > 0"],
            domain="cosmology",
            units="km/s/Mpc"
        )

        self.primitives["luminosity_distance"] = ProgramPrimitive(
            primitive_id="",
            primitive_type=ProgramPrimitiveType.PHYSICS_LAW,
            name="Luminosity Distance",
            parameters={},
            constraints=["redshift >= 0"],
            domain="cosmology",
            units="Mpc"
        )

        # Statistical distributions
        for dist in DistributionType:
            self.primitives[f"dist_{dist.value}"] = ProgramPrimitive(
                primitive_id="",
                primitive_type=ProgramPrimitiveType.DISTRIBUTION,
                name=f"{dist.value.title()} Distribution",
                parameters={},
                domain="statistical"
            )

    def get_primitive(self, name: str) -> Optional[ProgramPrimitive]:
        """Get a primitive by name"""
        return self.primitives.get(name)

    def get_primitives_by_domain(self, domain: str) -> List[ProgramPrimitive]:
        """Get all primitives for a domain"""
        return [p for p in self.primitives.values() if p.domain == domain]

    def get_compatible_primitives(self,
                                   units: str,
                                   constraints: List[str]) -> List[ProgramPrimitive]:
        """Find primitives compatible with given units and constraints"""
        compatible = []
        for prim in self.primitives.values():
            if prim.units == units or not units:
                # Check constraint compatibility
                if self._constraints_compatible(prim.constraints, constraints):
                    compatible.append(prim)
        return compatible

    def _constraints_compatible(self,
                                 prim_constraints: List[str],
                                 required: List[str]) -> bool:
        """Check if primitive constraints are compatible with requirements"""
        # Simplified check - in practice would use constraint solver
        return True


class ProgramGenerator:
    """
    Generates candidate probabilistic programs.
    Uses grammar-guided synthesis with physics constraints.
    """

    def __init__(self, physics_library: PhysicsLibrary):
        self.library = physics_library
        self.max_depth = 10
        self.max_nodes = 50

    def generate_from_sketch(self,
                             sketch: Dict[str, Any],
                             domain: str) -> ProbabilisticProgram:
        """
        Generate a program from a high-level sketch.

        Sketch format:
        {
            "inputs": ["x", "y", ...],
            "outputs": ["flux", ...],
            "physics": ["gravitational", "radiative"],
            "structure": "hierarchical" | "sequential" | "parallel"
        }
        """
        # Build program tree
        root = self._build_program_tree(sketch, domain)

        # Extract components
        parameters = self._extract_parameters(root)
        latents = self._extract_latent_variables(root)
        observations = self._extract_observations(root, sketch.get("outputs", []))

        # Determine physics laws
        physics_laws = sketch.get("physics", [])

        # Build dimensional constraints
        dim_constraints = self._infer_dimensional_constraints(root)

        # Conservation laws
        conservation = self._identify_conservation_laws(physics_laws)

        return ProbabilisticProgram(
            program_id="",
            name=f"Program for {domain}",
            description=f"Auto-generated program for {sketch}",
            root=root,
            parameters=parameters,
            latent_variables=latents,
            observations=observations,
            physics_laws=physics_laws,
            dimensional_constraints=dim_constraints,
            conservation_laws=conservation,
            domain=domain,
            complexity=self._compute_complexity(root)
        )

    def generate_random(self, domain: str, depth: int = 5) -> ProbabilisticProgram:
        """Generate a random program for exploration"""
        primitives = self.library.get_primitives_by_domain(domain)
        if not primitives:
            primitives = list(self.library.primitives.values())

        root = self._generate_random_tree(primitives, depth)

        return ProbabilisticProgram(
            program_id="",
            name=f"Random program ({domain})",
            description="Randomly generated program",
            root=root,
            parameters=self._extract_parameters(root),
            latent_variables=self._extract_latent_variables(root),
            observations={},
            physics_laws=[],
            dimensional_constraints={},
            conservation_laws=[],
            domain=domain,
            complexity=self._compute_complexity(root)
        )

    def mutate(self, program: ProbabilisticProgram) -> ProbabilisticProgram:
        """Create a mutation of an existing program"""
        new_root = copy.deepcopy(program.root)

        # Choose mutation type
        mutation_type = random.choice([
            "replace_node", "add_node", "remove_node",
            "swap_children", "change_parameter"
        ])

        if mutation_type == "replace_node":
            self._mutate_replace_node(new_root)
        elif mutation_type == "add_node":
            self._mutate_add_node(new_root)
        elif mutation_type == "remove_node":
            self._mutate_remove_node(new_root)
        elif mutation_type == "swap_children":
            self._mutate_swap_children(new_root)
        elif mutation_type == "change_parameter":
            self._mutate_change_parameter(new_root)

        return ProbabilisticProgram(
            program_id="",
            name=f"{program.name} (mutated)",
            description=f"Mutation of {program.program_id}",
            root=new_root,
            parameters=self._extract_parameters(new_root),
            latent_variables=self._extract_latent_variables(new_root),
            observations=program.observations,
            physics_laws=program.physics_laws,
            dimensional_constraints=program.dimensional_constraints,
            conservation_laws=program.conservation_laws,
            domain=program.domain,
            complexity=self._compute_complexity(new_root)
        )

    def crossover(self,
                  program1: ProbabilisticProgram,
                  program2: ProbabilisticProgram) -> ProbabilisticProgram:
        """Create a crossover of two programs"""
        # Select subtrees from each parent
        root1 = copy.deepcopy(program1.root)
        root2 = copy.deepcopy(program2.root)

        # Find compatible crossover points
        nodes1 = self._collect_nodes(root1)
        nodes2 = self._collect_nodes(root2)

        if nodes1 and nodes2:
            # Swap subtrees at random points
            swap_point1 = random.choice(nodes1)
            swap_point2 = random.choice(nodes2)

            # Perform crossover
            if swap_point1.children and swap_point2.children:
                idx1 = random.randint(0, len(swap_point1.children) - 1)
                idx2 = random.randint(0, len(swap_point2.children) - 1)
                swap_point1.children[idx1] = swap_point2.children[idx2]

        return ProbabilisticProgram(
            program_id="",
            name=f"Crossover ({program1.name}, {program2.name})",
            description="Crossover program",
            root=root1,
            parameters=self._extract_parameters(root1),
            latent_variables=self._extract_latent_variables(root1),
            observations={},
            physics_laws=list(set(program1.physics_laws + program2.physics_laws)),
            dimensional_constraints={**program1.dimensional_constraints,
                                    **program2.dimensional_constraints},
            conservation_laws=list(set(program1.conservation_laws +
                                       program2.conservation_laws)),
            domain=program1.domain,
            complexity=self._compute_complexity(root1)
        )

    def _build_program_tree(self,
                            sketch: Dict[str, Any],
                            domain: str) -> ProgramNode:
        """Build a program tree from a sketch"""
        structure = sketch.get("structure", "sequential")
        inputs = sketch.get("inputs", [])
        physics = sketch.get("physics", [])

        # Create input nodes
        input_nodes = []
        for inp in inputs:
            prim = ProgramPrimitive(
                primitive_id="",
                primitive_type=ProgramPrimitiveType.VARIABLE,
                name=inp,
                domain=domain
            )
            input_nodes.append(ProgramNode(
                node_id="",
                node_type="primitive",
                primitive=prim
            ))

        # Create physics nodes
        physics_nodes = []
        for phys in physics:
            primitives = self.library.get_primitives_by_domain(phys)
            if primitives:
                prim = random.choice(primitives)
                physics_nodes.append(ProgramNode(
                    node_id="",
                    node_type="application",
                    primitive=prim,
                    children=input_nodes[:2] if len(input_nodes) >= 2 else input_nodes
                ))

        # Compose based on structure
        if structure == "sequential":
            root = self._compose_sequential(physics_nodes)
        elif structure == "parallel":
            root = self._compose_parallel(physics_nodes)
        else:  # hierarchical
            root = self._compose_hierarchical(physics_nodes)

        return root

    def _compose_sequential(self, nodes: List[ProgramNode]) -> ProgramNode:
        """Compose nodes sequentially (output of one feeds next)"""
        if not nodes:
            return ProgramNode(node_id="", node_type="primitive")

        current = nodes[0]
        for i in range(1, len(nodes)):
            nodes[i].children = [current]
            current = nodes[i]
        return current

    def _compose_parallel(self, nodes: List[ProgramNode]) -> ProgramNode:
        """Compose nodes in parallel (all feed into combiner)"""
        combiner = ProgramNode(
            node_id="",
            node_type="application",
            primitive=ProgramPrimitive(
                primitive_id="",
                primitive_type=ProgramPrimitiveType.OPERATOR,
                name="combine"
            ),
            children=nodes
        )
        return combiner

    def _compose_hierarchical(self, nodes: List[ProgramNode]) -> ProgramNode:
        """Compose nodes hierarchically (tree structure)"""
        if len(nodes) <= 1:
            return nodes[0] if nodes else ProgramNode(node_id="", node_type="primitive")

        # Build binary tree
        while len(nodes) > 1:
            new_level = []
            for i in range(0, len(nodes), 2):
                if i + 1 < len(nodes):
                    parent = ProgramNode(
                        node_id="",
                        node_type="application",
                        primitive=ProgramPrimitive(
                            primitive_id="",
                            primitive_type=ProgramPrimitiveType.OPERATOR,
                            name="compose"
                        ),
                        children=[nodes[i], nodes[i + 1]]
                    )
                    new_level.append(parent)
                else:
                    new_level.append(nodes[i])
            nodes = new_level

        return nodes[0]

    def _generate_random_tree(self,
                              primitives: List[ProgramPrimitive],
                              depth: int) -> ProgramNode:
        """Generate a random program tree"""
        if depth <= 0 or not primitives:
            prim = random.choice(primitives) if primitives else None
            return ProgramNode(
                node_id="",
                node_type="primitive",
                primitive=prim
            )

        # Randomly choose node type
        node_type = random.choice(["primitive", "application", "sample"])

        if node_type == "primitive":
            prim = random.choice(primitives)
            return ProgramNode(
                node_id="",
                node_type="primitive",
                primitive=prim
            )
        elif node_type == "sample":
            dist_prims = [p for p in primitives
                        if p.primitive_type == ProgramPrimitiveType.DISTRIBUTION]
            if dist_prims:
                prim = random.choice(dist_prims)
            else:
                prim = random.choice(primitives)
            return ProgramNode(
                node_id="",
                node_type="sample",
                primitive=prim
            )
        else:  # application
            prim = random.choice(primitives)
            num_children = random.randint(1, 3)
            children = [
                self._generate_random_tree(primitives, depth - 1)
                for _ in range(num_children)
            ]
            return ProgramNode(
                node_id="",
                node_type="application",
                primitive=prim,
                children=children
            )

    def _extract_parameters(self, root: ProgramNode) -> Dict[str, ProgramPrimitive]:
        """Extract all parameters from program tree"""
        params = {}

        def visit(node: ProgramNode):
            if node.primitive and node.primitive.primitive_type == ProgramPrimitiveType.PARAMETER:
                params[node.primitive.name] = node.primitive
            for child in node.children:
                visit(child)

        visit(root)
        return params

    def _extract_latent_variables(self, root: ProgramNode) -> Dict[str, ProgramPrimitive]:
        """Extract latent variables (sampled values)"""
        latents = {}

        def visit(node: ProgramNode):
            if node.node_type == "sample" and node.primitive:
                latents[node.primitive.name] = node.primitive
            for child in node.children:
                visit(child)

        visit(root)
        return latents

    def _extract_observations(self,
                              root: ProgramNode,
                              output_names: List[str]) -> Dict[str, ProgramPrimitive]:
        """Extract observation variables"""
        observations = {}
        for name in output_names:
            observations[name] = ProgramPrimitive(
                primitive_id="",
                primitive_type=ProgramPrimitiveType.OBSERVATION_MODEL,
                name=name
            )
        return observations

    def _infer_dimensional_constraints(self, root: ProgramNode) -> Dict[str, str]:
        """Infer dimensional constraints from program structure"""
        constraints = {}

        def visit(node: ProgramNode):
            if node.primitive and node.primitive.units:
                constraints[node.primitive.name] = node.primitive.units
            for child in node.children:
                visit(child)

        visit(root)
        return constraints

    def _identify_conservation_laws(self, physics: List[str]) -> List[str]:
        """Identify applicable conservation laws"""
        laws = []

        if "gravitational" in physics or "stellar" in physics:
            laws.append("energy_conservation")
            laws.append("momentum_conservation")

        if "electromagnetic" in physics or "radiative" in physics:
            laws.append("energy_conservation")
            laws.append("photon_number_conservation")

        if "hydrodynamic" in physics:
            laws.append("mass_conservation")
            laws.append("momentum_conservation")
            laws.append("energy_conservation")

        return list(set(laws))

    def _compute_complexity(self, root: ProgramNode) -> float:
        """Compute program complexity (for regularization)"""
        node_count = 0
        depth = 0

        def visit(node: ProgramNode, d: int):
            nonlocal node_count, depth
            node_count += 1
            depth = max(depth, d)
            for child in node.children:
                visit(child, d + 1)

        visit(root, 0)
        return node_count + 0.5 * depth

    def _collect_nodes(self, root: ProgramNode) -> List[ProgramNode]:
        """Collect all nodes in a tree"""
        nodes = []

        def visit(node: ProgramNode):
            nodes.append(node)
            for child in node.children:
                visit(child)

        visit(root)
        return nodes

    def _mutate_replace_node(self, root: ProgramNode):
        """Replace a random node with a new one"""
        nodes = self._collect_nodes(root)
        if nodes:
            node = random.choice(nodes)
            primitives = list(self.library.primitives.values())
            if primitives:
                node.primitive = random.choice(primitives)

    def _mutate_add_node(self, root: ProgramNode):
        """Add a new child to a random node"""
        nodes = self._collect_nodes(root)
        if nodes:
            node = random.choice(nodes)
            primitives = list(self.library.primitives.values())
            if primitives:
                new_child = ProgramNode(
                    node_id="",
                    node_type="primitive",
                    primitive=random.choice(primitives)
                )
                node.children.append(new_child)

    def _mutate_remove_node(self, root: ProgramNode):
        """Remove a random child from a node"""
        nodes = self._collect_nodes(root)
        for node in nodes:
            if node.children:
                node.children.pop(random.randint(0, len(node.children) - 1))
                break

    def _mutate_swap_children(self, root: ProgramNode):
        """Swap children of a random node"""
        nodes = self._collect_nodes(root)
        for node in nodes:
            if len(node.children) >= 2:
                i, j = random.sample(range(len(node.children)), 2)
                node.children[i], node.children[j] = node.children[j], node.children[i]
                break

    def _mutate_change_parameter(self, root: ProgramNode):
        """Change a parameter value"""
        nodes = self._collect_nodes(root)
        for node in nodes:
            if node.primitive and node.primitive.parameters:
                key = random.choice(list(node.primitive.parameters.keys()))
                old_val = node.primitive.parameters[key]
                if isinstance(old_val, (int, float)):
                    # Perturb by up to 20%
                    node.primitive.parameters[key] = old_val * (1 + random.uniform(-0.2, 0.2))
                break


class ProgramEvaluator:
    """
    Evaluates probabilistic programs against data.
    Computes likelihoods and posterior scores.
    """

    def __init__(self):
        self.execution_cache: Dict[str, Any] = {}

    def evaluate(self,
                 program: ProbabilisticProgram,
                 data: Dict[str, Any],
                 num_samples: int = 100) -> Tuple[float, Dict[str, Any]]:
        """
        Evaluate a program's likelihood given data.

        Returns:
            (log_likelihood, execution_trace)
        """
        # Execute program to generate predictions
        predictions, trace = self._execute_program(program, data, num_samples)

        # Compare predictions to observations
        log_lik = self._compute_log_likelihood(predictions, data, program.observations)

        # Add complexity penalty (Occam's razor)
        complexity_penalty = -0.1 * program.complexity

        # Check physics constraints
        constraint_penalty = self._check_constraints(trace, program)

        total_score = log_lik + complexity_penalty + constraint_penalty

        return total_score, trace

    def _execute_program(self,
                         program: ProbabilisticProgram,
                         data: Dict[str, Any],
                         num_samples: int) -> Tuple[Dict[str, Any], Dict[str, Any]]:
        """Execute a probabilistic program"""
        trace = {"samples": [], "intermediate": {}}
        predictions = {}

        for _ in range(num_samples):
            sample_trace = {}
            result = self._execute_node(program.root, data, sample_trace)
            trace["samples"].append(sample_trace)

            # Collect predictions
            for obs_name in program.observations:
                if obs_name not in predictions:
                    predictions[obs_name] = []
                predictions[obs_name].append(result)

        # Aggregate predictions
        for key in predictions:
            values = predictions[key]
            if all(isinstance(v, (int, float)) for v in values):
                predictions[key] = {
                    "mean": sum(values) / len(values),
                    "std": (sum((v - sum(values)/len(values))**2 for v in values) / len(values))**0.5,
                    "samples": values
                }

        return predictions, trace

    def _execute_node(self,
                      node: ProgramNode,
                      data: Dict[str, Any],
                      trace: Dict[str, Any]) -> Any:
        """Execute a single program node"""
        if node.node_type == "primitive":
            if node.primitive:
                if node.primitive.primitive_type == ProgramPrimitiveType.VARIABLE:
                    return data.get(node.primitive.name, 0)
                elif node.primitive.primitive_type == ProgramPrimitiveType.CONSTANT:
                    return node.primitive.value
                elif node.primitive.primitive_type == ProgramPrimitiveType.PARAMETER:
                    return node.primitive.parameters.get("value", 1.0)
            return 0

        elif node.node_type == "sample":
            return self._sample_distribution(node.primitive, trace)

        elif node.node_type == "application":
            # Execute children first
            child_values = [self._execute_node(c, data, trace) for c in node.children]

            # Apply function
            return self._apply_primitive(node.primitive, child_values, trace)

        return 0

    def _sample_distribution(self,
                             primitive: Optional[ProgramPrimitive],
                             trace: Dict[str, Any]) -> float:
        """Sample from a distribution primitive"""
        if not primitive:
            return random.gauss(0, 1)

        name = primitive.name.lower()
        params = primitive.parameters

        if "normal" in name:
            mu = params.get("mean", 0)
            sigma = params.get("std", 1)
            return random.gauss(mu, sigma)
        elif "uniform" in name:
            low = params.get("low", 0)
            high = params.get("high", 1)
            return random.uniform(low, high)
        elif "exponential" in name:
            rate = params.get("rate", 1)
            return random.expovariate(rate)
        elif "lognormal" in name:
            mu = params.get("mean", 0)
            sigma = params.get("std", 1)
            return random.lognormvariate(mu, sigma)
        else:
            return random.gauss(0, 1)

    def _apply_primitive(self,
                         primitive: Optional[ProgramPrimitive],
                         args: List[Any],
                         trace: Dict[str, Any]) -> Any:
        """Apply a primitive function to arguments"""
        if not primitive or not args:
            return sum(args) if args else 0

        name = primitive.name.lower()

        # Physics primitives
        if "planck" in name:
            # B_nu(T) approximation
            T = args[0] if args else 5000
            return 2.0 * 6.626e-27 * (3e10)**2 / (1e14**3) * 1 / (math.exp(6.626e-27 * 1e14 / (1.381e-16 * T)) - 1)

        elif "stefan" in name:
            T = args[0] if args else 5000
            return 5.67e-5 * T**4

        elif "newton" in name or "gravity" in name:
            if len(args) >= 2:
                M, r = args[0], args[1]
                G = 6.674e-8
                return G * M / (r**2 + 1e-10)
            return 0

        elif "kepler" in name:
            if len(args) >= 2:
                a, M = args[0], args[1]
                G = 6.674e-8
                return 2 * math.pi * math.sqrt(a**3 / (G * M + 1e-10))
            return 0

        elif "nfw" in name:
            if len(args) >= 2:
                r, rs = args[0], args[1]
                x = r / (rs + 1e-10)
                return 1 / (x * (1 + x)**2 + 1e-10)
            return 0

        elif "combine" in name:
            return sum(args)

        elif "compose" in name:
            result = args[0] if args else 0
            for a in args[1:]:
                result = result * a
            return result

        # Default: sum
        return sum(args) if args else 0

    def _compute_log_likelihood(self,
                                predictions: Dict[str, Any],
                                data: Dict[str, Any],
                                observations: Dict[str, ProgramPrimitive]) -> float:
        """Compute log likelihood of data given predictions"""
        log_lik = 0.0

        for obs_name, obs_prim in observations.items():
            if obs_name in data and obs_name in predictions:
                observed = data[obs_name]
                pred = predictions[obs_name]

                if isinstance(pred, dict) and "mean" in pred and "std" in pred:
                    # Gaussian likelihood
                    mu = pred["mean"]
                    sigma = max(pred["std"], 1e-10)

                    if isinstance(observed, (list, tuple)):
                        for obs in observed:
                            log_lik += -0.5 * ((obs - mu) / sigma)**2 - math.log(sigma)
                    else:
                        log_lik += -0.5 * ((observed - mu) / sigma)**2 - math.log(sigma)

        return log_lik

    def _check_constraints(self,
                           trace: Dict[str, Any],
                           program: ProbabilisticProgram) -> float:
        """Check physics constraints and return penalty"""
        penalty = 0.0

        # Check dimensional constraints
        for var, units in program.dimensional_constraints.items():
            # In a full implementation, would check unit consistency
            pass

        # Check conservation laws
        for law in program.conservation_laws:
            # In a full implementation, would verify conservation
            pass

        return penalty


class ProbabilisticProgramSynthesizer:
    """
    Main interface for probabilistic program synthesis.

    Uses evolutionary search with physics-guided mutations
    to discover programs that explain observations.
    """

    def __init__(self,
                 physics_library: Optional[PhysicsLibrary] = None):
        self.library = physics_library or PhysicsLibrary()
        self.generator = ProgramGenerator(self.library)
        self.evaluator = ProgramEvaluator()

        # Search parameters
        self.population_size = 50
        self.generations = 100
        self.mutation_rate = 0.3
        self.crossover_rate = 0.5
        self.elite_fraction = 0.1

        # Event callbacks
        self._callbacks: Dict[str, List[Callable]] = defaultdict(list)

    def synthesize(self,
                   problem_description: str,
                   data: Dict[str, Any],
                   domain: str,
                   constraints: Optional[List[str]] = None,
                   max_time: float = 60.0) -> SynthesisResult:
        """
        Synthesize a probabilistic program to explain data.

        Args:
            problem_description: Natural language problem description
            data: Dictionary of observations
            domain: Physics domain (e.g., "gravitational_lensing")
            constraints: Additional constraints
            max_time: Maximum synthesis time in seconds

        Returns:
            SynthesisResult with candidate programs
        """
        start_time = time.time()
        search_path = []

        # Parse problem description to create sketch
        sketch = self._parse_description(problem_description, data, domain)

        # Initialize population
        population = self._initialize_population(sketch, domain)

        # Evaluate initial population
        for prog in population:
            score, _ = self.evaluator.evaluate(prog, data)
            prog.posterior_score = score
            prog.log_likelihood = score

        # Sort by score
        population.sort(key=lambda p: p.posterior_score, reverse=True)

        # Evolutionary search
        generation = 0
        best_score = population[0].posterior_score if population else float('-inf')

        while time.time() - start_time < max_time and generation < self.generations:
            generation += 1

            # Record search state
            search_path.append({
                "generation": generation,
                "best_score": best_score,
                "population_size": len(population),
                "diversity": self._compute_diversity(population)
            })

            # Selection
            parents = self._select_parents(population)

            # Create next generation
            next_gen = []

            # Elitism
            elite_count = int(self.elite_fraction * self.population_size)
            next_gen.extend(population[:elite_count])

            # Crossover and mutation
            while len(next_gen) < self.population_size:
                if random.random() < self.crossover_rate and len(parents) >= 2:
                    p1, p2 = random.sample(parents, 2)
                    child = self.generator.crossover(p1, p2)
                else:
                    parent = random.choice(parents)
                    child = copy.deepcopy(parent)

                if random.random() < self.mutation_rate:
                    child = self.generator.mutate(child)

                # Evaluate child
                score, _ = self.evaluator.evaluate(child, data)
                child.posterior_score = score
                child.log_likelihood = score

                next_gen.append(child)

            # Sort and update
            population = sorted(next_gen, key=lambda p: p.posterior_score, reverse=True)

            # Update best
            if population[0].posterior_score > best_score:
                best_score = population[0].posterior_score
                self._emit("improvement", {
                    "generation": generation,
                    "score": best_score,
                    "program": population[0]
                })

        synthesis_time = time.time() - start_time

        # Compute evidence estimate
        log_evidence = self._estimate_evidence(population, data)

        return SynthesisResult(
            result_id="",
            programs=population[:10],  # Top 10 programs
            best_program=population[0] if population else None,
            log_evidence=log_evidence,
            synthesis_time=synthesis_time,
            iterations=generation,
            search_path=search_path
        )

    def synthesize_from_sketch(self,
                               sketch: Dict[str, Any],
                               data: Dict[str, Any],
                               domain: str) -> ProbabilisticProgram:
        """
        Synthesize a program from a given sketch structure.

        Useful when you know the general form of the model.
        """
        program = self.generator.generate_from_sketch(sketch, domain)
        score, trace = self.evaluator.evaluate(program, data)
        program.posterior_score = score
        program.log_likelihood = score
        return program

    def explain_program(self, program: ProbabilisticProgram) -> str:
        """Generate a natural language explanation of a program"""
        lines = [f"Program: {program.name}", ""]

        # Describe structure
        lines.append("Structure:")
        lines.append(f"  - Domain: {program.domain}")
        lines.append(f"  - Complexity: {program.complexity:.2f}")
        lines.append(f"  - Parameters: {len(program.parameters)}")
        lines.append(f"  - Latent variables: {len(program.latent_variables)}")
        lines.append("")

        # Physics laws
        if program.physics_laws:
            lines.append("Physics:")
            for law in program.physics_laws:
                lines.append(f"  - {law}")
            lines.append("")

        # Conservation laws
        if program.conservation_laws:
            lines.append("Conservation laws:")
            for law in program.conservation_laws:
                lines.append(f"  - {law}")
            lines.append("")

        # Score
        lines.append(f"Log-likelihood: {program.log_likelihood:.2f}")
        lines.append(f"Posterior score: {program.posterior_score:.2f}")

        return "\n".join(lines)

    def on(self, event: str, callback: Callable):
        """Register event callback"""
