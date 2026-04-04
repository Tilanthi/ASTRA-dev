"""
LEAPCore Evolution: Evolutionary Meta-Theory Refinement

Learning through Evolutionary Adaptation of Parameters (LEAP) Core engine
for evolving V36's meta-theory components including laws, constraints,
symbolic templates, and observation function families.

Integration with V36:
- Evolves T_U' universal laws (L1-L8)
- Refines prohibitive constraints (N1-N3)
- Optimizes symbolic template boundaries
- Discovers new observation function families

Date: 2025-11-27
Version: 37.0
"""

import numpy as np
from typing import Dict, List, Optional, Tuple, Any, Callable
from dataclasses import dataclass, field
from enum import Enum
import json
import copy
import time
from abc import ABC, abstractmethod


class GeneType(Enum):
    """Types of evolvable genes in meta-theory"""
    LAW_CONFIDENCE = "law_confidence"
    LAW_CONDITION = "law_condition"
    CONSTRAINT_SEVERITY = "constraint_severity"
    CONSTRAINT_SCOPE = "constraint_scope"
    TEMPLATE_BOUNDARY = "template_boundary"
    OBSERVATION_FAMILY = "observation_family"
    MIXTURE_PRIOR = "mixture_prior"


@dataclass
class Gene:
    """A single evolvable gene"""
    gene_id: str
    gene_type: GeneType
    value: Any
    bounds: Tuple[Any, Any] = None
    mutation_rate: float = 0.1
    metadata: Dict[str, Any] = field(default_factory=dict)

    def mutate(self, strength: float = 1.0) -> 'Gene':
        """Create mutated copy of gene"""
        new_gene = copy.deepcopy(self)

        if isinstance(self.value, (int, float)):
            # Numeric mutation
            mutation = np.random.normal(0, self.mutation_rate * strength)
            new_val = self.value + mutation * (self.bounds[1] - self.bounds[0]) if self.bounds else self.value + mutation
            if self.bounds:
                new_val = max(self.bounds[0], min(self.bounds[1], new_val))
            new_gene.value = new_val

        elif isinstance(self.value, str):
            # Categorical mutation - swap with random option
            if self.metadata.get('options'):
                if np.random.random() < self.mutation_rate * strength:
                    new_gene.value = np.random.choice(self.metadata['options'])

        elif isinstance(self.value, list):
            # List mutation - add/remove/modify elements
            if np.random.random() < self.mutation_rate * strength:
                idx = np.random.randint(0, len(self.value)) if self.value else 0
                if np.random.random() < 0.5 and len(self.value) > 1:
                    new_gene.value = [v for i, v in enumerate(self.value) if i != idx]
                elif self.metadata.get('element_options'):
                    new_gene.value = self.value + [np.random.choice(self.metadata['element_options'])]

        elif isinstance(self.value, dict):
            # Dict mutation - modify random key
            if np.random.random() < self.mutation_rate * strength:
                keys = list(self.value.keys())
                if keys:
                    key = np.random.choice(keys)
                    if isinstance(self.value[key], (int, float)):
                        new_gene.value[key] *= (1 + np.random.normal(0, 0.1))

        return new_gene


@dataclass
class Chromosome:
    """A complete meta-theory specification as a chromosome"""
    chromosome_id: str
    genes: Dict[str, Gene]
    fitness: float = 0.0
    generation: int = 0
    parent_ids: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)

    def mutate(self, mutation_strength: float = 1.0) -> 'Chromosome':
        """Create mutated offspring"""
        new_id = f"chr_{time.time():.0f}_{np.random.randint(1000)}"
        new_genes = {gid: g.mutate(mutation_strength) for gid, g in self.genes.items()}
        return Chromosome(
            chromosome_id=new_id,
            genes=new_genes,
            generation=self.generation + 1,
            parent_ids=[self.chromosome_id]
        )

    def crossover(self, other: 'Chromosome') -> 'Chromosome':
        """Create offspring through crossover"""
        new_id = f"chr_{time.time():.0f}_{np.random.randint(1000)}"
        new_genes = {}

        for gid in self.genes:
            if gid in other.genes:
                # Randomly select from either parent
                if np.random.random() < 0.5:
                    new_genes[gid] = copy.deepcopy(self.genes[gid])
                else:
                    new_genes[gid] = copy.deepcopy(other.genes[gid])
            else:
                new_genes[gid] = copy.deepcopy(self.genes[gid])

        return Chromosome(
            chromosome_id=new_id,
            genes=new_genes,
            generation=max(self.generation, other.generation) + 1,
            parent_ids=[self.chromosome_id, other.chromosome_id]
        )


@dataclass
class EvolutionConfig:
    """Configuration for evolutionary process"""
    population_size: int = 50
    elite_count: int = 5
    tournament_size: int = 3
    crossover_rate: float = 0.7
    mutation_rate: float = 0.3
    mutation_strength: float = 1.0
    max_generations: int = 100
    stagnation_limit: int = 10
    diversity_threshold: float = 0.1


class FitnessEvaluator(ABC):
    """Abstract fitness evaluator for meta-theories"""

    @abstractmethod
    def evaluate(self, chromosome: Chromosome) -> float:
        """Evaluate fitness of a chromosome"""
        pass


class V36FitnessEvaluator(FitnessEvaluator):
    """
    Fitness evaluator for V36 meta-theory chromosomes.

    Fitness components:
    - Falsification survival rate
    - Analogy discovery rate
    - Constraint violation detection accuracy
    - Parsimony (simplicity preference)
    """

    def __init__(self, test_worlds: List[Dict] = None,
                 weights: Dict[str, float] = None):
        self.test_worlds = test_worlds or []
        self.weights = weights or {
            'falsification_survival': 0.4,
            'analogy_discovery': 0.3,
            'violation_detection': 0.2,
            'parsimony': 0.1
        }

    def evaluate(self, chromosome: Chromosome) -> float:
        """Evaluate chromosome fitness"""
        scores = {}

        # Falsification survival: How many test hypotheses survive the constraints
        scores['falsification_survival'] = self._eval_falsification_survival(chromosome)

        # Analogy discovery: Does the meta-theory enable finding analogies
        scores['analogy_discovery'] = self._eval_analogy_discovery(chromosome)

        # Violation detection: Can it detect known violations
        scores['violation_detection'] = self._eval_violation_detection(chromosome)

        # Parsimony: Simpler is better
        scores['parsimony'] = self._eval_parsimony(chromosome)

        # Weighted sum
        fitness = sum(
            self.weights[key] * scores[key]
            for key in scores
        )

        return fitness

    def _eval_falsification_survival(self, chromosome: Chromosome) -> float:
        """Evaluate falsification survival rate"""
        # Extract constraint severities from chromosome
        severities = {}
        for gid, gene in chromosome.genes.items():
            if gene.gene_type == GeneType.CONSTRAINT_SEVERITY:
                severities[gid] = gene.value

        # Simulate: stricter constraints = lower survival but higher quality
        # We want a balance
        avg_severity = np.mean(list(severities.values())) if severities else 0.5
        # Optimal around 0.6 - not too strict, not too lenient
        return 1.0 - abs(avg_severity - 0.6)

    def _eval_analogy_discovery(self, chromosome: Chromosome) -> float:
        """Evaluate analogy discovery capability"""
        # Check template boundaries - wider boundaries = more analogies found
        boundary_genes = [g for g in chromosome.genes.values()
                         if g.gene_type == GeneType.TEMPLATE_BOUNDARY]

        if not boundary_genes:
            return 0.5

        # Calculate boundary widths
        widths = []
        for gene in boundary_genes:
            if gene.bounds:
                width = (gene.value - gene.bounds[0]) / (gene.bounds[1] - gene.bounds[0])
                widths.append(width)

        # Moderate widths are best for analogies
        avg_width = np.mean(widths) if widths else 0.5
        return 1.0 - abs(avg_width - 0.5) * 2

    def _eval_violation_detection(self, chromosome: Chromosome) -> float:
        """Evaluate constraint violation detection"""
        # Scope genes - broader scope = more detections
        scope_genes = [g for g in chromosome.genes.values()
                      if g.gene_type == GeneType.CONSTRAINT_SCOPE]

        if not scope_genes:
            return 0.5

        # Count domains covered
        domains_covered = set()
        for gene in scope_genes:
            if isinstance(gene.value, list):
                domains_covered.update(gene.value)
            elif gene.value == 'ALL':
                domains_covered = {'CLD', 'D1', 'D2'}

        return len(domains_covered) / 3.0

    def _eval_parsimony(self, chromosome: Chromosome) -> float:
        """Evaluate simplicity/parsimony"""
        # Fewer genes = simpler = better (to a point)
        gene_count = len(chromosome.genes)
        # Optimal around 15-20 genes
        optimal = 17
        return max(0, 1.0 - abs(gene_count - optimal) / 20)


class LEAPCoreEvolution:
    """
    LEAPCore evolutionary engine for V36 meta-theory refinement.

    Provides:
    - Population-based evolution of meta-theory parameters
    - Genetic operators: selection, crossover, mutation
    - Fitness evaluation with V36-specific metrics
    - Elite preservation and diversity maintenance
    """

    def __init__(self, config: EvolutionConfig = None,
                 fitness_evaluator: FitnessEvaluator = None):
        self.config = config or EvolutionConfig()
        self.fitness_evaluator = fitness_evaluator or V36FitnessEvaluator()

        self.population: List[Chromosome] = []
        self.generation = 0
        self.best_fitness_history: List[float] = []
        self.diversity_history: List[float] = []

        # Statistics
        self.total_evaluations = 0
        self.stagnation_counter = 0
        self.best_ever: Optional[Chromosome] = None

    def initialize_population(self, seed_chromosome: Chromosome = None):
        """Initialize population with random or seeded chromosomes"""
        self.population = []

        # Create base chromosome from V36 defaults if not provided
        if seed_chromosome is None:
            seed_chromosome = self._create_v36_base_chromosome()

        # First chromosome is the seed
        self.population.append(seed_chromosome)

        # Create variations
        for _ in range(self.config.population_size - 1):
            mutant = seed_chromosome.mutate(mutation_strength=2.0)  # Higher initial diversity
            self.population.append(mutant)

        # Evaluate initial population
        self._evaluate_population()

    def _create_v36_base_chromosome(self) -> Chromosome:
        """Create base chromosome from V36 defaults"""
        genes = {}

        # Law confidence genes (L1-L8)
        for i in range(1, 9):
            genes[f'law_L{i}_confidence'] = Gene(
                gene_id=f'law_L{i}_confidence',
                gene_type=GeneType.LAW_CONFIDENCE,
                value=0.85,
                bounds=(0.5, 1.0),
                mutation_rate=0.1
            )

        # Constraint severity genes (N1-N3)
        severities = {'N1': 1.0, 'N2': 0.5, 'N3': 0.8}  # FATAL, MODERATE, STRONG
        for cid, sev in severities.items():
            genes[f'constraint_{cid}_severity'] = Gene(
                gene_id=f'constraint_{cid}_severity',
                gene_type=GeneType.CONSTRAINT_SEVERITY,
                value=sev,
                bounds=(0.0, 1.0),
                mutation_rate=0.15
            )

        # Constraint scope genes
        for cid in ['N1', 'N2', 'N3']:
            genes[f'constraint_{cid}_scope'] = Gene(
                gene_id=f'constraint_{cid}_scope',
                gene_type=GeneType.CONSTRAINT_SCOPE,
                value=['ALL'],
                mutation_rate=0.1,
                metadata={'element_options': ['CLD', 'D1', 'D2', 'ALL']}
            )

        # Template boundary genes
        template_bounds = {
            'stable_ar_min': (0.90, 0.95, 0.99),     # (lower, default, upper)
            'responsive_ar_min': (0.60, 0.70, 0.85),
            'responsive_ar_max': (0.85, 0.95, 0.99),
            'delayed_min_lag': (3, 5, 10)
        }
        for name, (lo, default, hi) in template_bounds.items():
            genes[f'template_{name}'] = Gene(
                gene_id=f'template_{name}',
                gene_type=GeneType.TEMPLATE_BOUNDARY,
                value=default,
                bounds=(lo, hi),
                mutation_rate=0.1
            )

        # Observation family genes
        genes['obs_families'] = Gene(
            gene_id='obs_families',
            gene_type=GeneType.OBSERVATION_FAMILY,
            value=['linear', 'polynomial', 'exponential', 'multiplicative', 'logarithmic'],
            mutation_rate=0.05,
            metadata={'element_options': ['linear', 'polynomial', 'exponential',
                                         'multiplicative', 'logarithmic', 'trigonometric',
                                         'blended', 'sigmoid', 'power_law']}
        )

        # Domain mixture prior genes
        genes['mixture_prior_cld'] = Gene(
            gene_id='mixture_prior_cld',
            gene_type=GeneType.MIXTURE_PRIOR,
            value=0.33,
            bounds=(0.1, 0.6),
            mutation_rate=0.1
        )
        genes['mixture_prior_d1'] = Gene(
            gene_id='mixture_prior_d1',
            gene_type=GeneType.MIXTURE_PRIOR,
            value=0.33,
            bounds=(0.1, 0.6),
            mutation_rate=0.1
        )

        return Chromosome(
            chromosome_id='v36_base',
            genes=genes,
            generation=0,
            metadata={'origin': 'v36_defaults'}
        )

    def _evaluate_population(self):
        """Evaluate fitness of all chromosomes"""
        for chromosome in self.population:
            if chromosome.fitness == 0.0:  # Not yet evaluated
                chromosome.fitness = self.fitness_evaluator.evaluate(chromosome)
                self.total_evaluations += 1

        # Sort by fitness (descending)
        self.population.sort(key=lambda c: c.fitness, reverse=True)

        # Update best ever
        if self.best_ever is None or self.population[0].fitness > self.best_ever.fitness:
            self.best_ever = copy.deepcopy(self.population[0])
            self.stagnation_counter = 0
        else:
            self.stagnation_counter += 1

    def _tournament_select(self) -> Chromosome:
        """Select chromosome via tournament selection"""
        tournament = np.random.choice(
            self.population,
            size=min(self.config.tournament_size, len(self.population)),
            replace=False
        )
        return max(tournament, key=lambda c: c.fitness)

    def _calculate_diversity(self) -> float:
        """Calculate population diversity"""
        if len(self.population) < 2:
            return 1.0

        # Sample genes to compare
        gene_ids = list(self.population[0].genes.keys())
        if not gene_ids:
            return 1.0

        diversities = []
        for gid in gene_ids:
            values = []
            for chrom in self.population:
                if gid in chrom.genes:
                    val = chrom.genes[gid].value
                    if isinstance(val, (int, float)):
                        values.append(val)

            if len(values) > 1:
                diversities.append(np.std(values))

        return np.mean(diversities) if diversities else 0.0

    def evolve_generation(self) -> Dict[str, Any]:
        """Evolve one generation"""
        self.generation += 1
        new_population = []

        # Elite preservation
        elites = self.population[:self.config.elite_count]
        new_population.extend(copy.deepcopy(c) for c in elites)

        # Generate offspring
        while len(new_population) < self.config.population_size:
            if np.random.random() < self.config.crossover_rate:
                # Crossover
                parent1 = self._tournament_select()
                parent2 = self._tournament_select()
                offspring = parent1.crossover(parent2)
            else:
                # Mutation only
                parent = self._tournament_select()
                offspring = parent.mutate(self.config.mutation_strength)

            # Always apply some mutation
            if np.random.random() < self.config.mutation_rate:
                offspring = offspring.mutate(self.config.mutation_strength * 0.5)

            new_population.append(offspring)

        self.population = new_population
        self._evaluate_population()

        # Record statistics
        best_fitness = self.population[0].fitness
        avg_fitness = np.mean([c.fitness for c in self.population])
        diversity = self._calculate_diversity()

        self.best_fitness_history.append(best_fitness)
        self.diversity_history.append(diversity)

        return {
            'generation': self.generation,
            'best_fitness': best_fitness,
            'avg_fitness': avg_fitness,
            'diversity': diversity,
            'stagnation': self.stagnation_counter,
            'best_chromosome_id': self.population[0].chromosome_id
        }

    def evolve(self, generations: int = None,
               callback: Callable[[Dict], bool] = None) -> Chromosome:
        """
        Run evolution for specified generations.

        Args:
            generations: Number of generations (default from config)
            callback: Optional callback(stats) -> continue_evolution

        Returns:
            Best chromosome found
        """
        generations = generations or self.config.max_generations

        for _ in range(generations):
            stats = self.evolve_generation()

            # Callback
            if callback and not callback(stats):
                break

            # Check stagnation
            if self.stagnation_counter >= self.config.stagnation_limit:
                # Inject diversity
                self._inject_diversity()

        return self.best_ever

    def _inject_diversity(self):
        """Inject diversity when evolution stagnates"""
        # Replace bottom half with random variations of elites
        mid = len(self.population) // 2
        elites = self.population[:self.config.elite_count]

        for i in range(mid, len(self.population)):
            base = np.random.choice(elites)
            self.population[i] = base.mutate(mutation_strength=3.0)

        self.stagnation_counter = 0

    # =========================================================================
    # V36 INTEGRATION
    # =========================================================================

    def chromosome_to_tu_prime(self, chromosome: Chromosome) -> Dict:
        """Convert chromosome to T_U' format"""
        tu_prime = {
            "theory_name": "T_U' (Evolved)",
            "version": f"E.{self.generation}",
            "evolved_from_generation": chromosome.generation,
            "fitness": chromosome.fitness,
            "universal_laws": {},
            "prohibitive_constraints": {},
            "template_boundaries": {},
            "observation_families": [],
            "mixture_priors": {}
        }

        for gid, gene in chromosome.genes.items():
            if gene.gene_type == GeneType.LAW_CONFIDENCE:
                law_id = gid.replace('law_', '').replace('_confidence', '')
                tu_prime["universal_laws"][law_id] = {
                    "confidence": gene.value
                }

            elif gene.gene_type == GeneType.CONSTRAINT_SEVERITY:
                cid = gid.replace('constraint_', '').replace('_severity', '')
                if cid not in tu_prime["prohibitive_constraints"]:
                    tu_prime["prohibitive_constraints"][cid] = {}
                tu_prime["prohibitive_constraints"][cid]["severity"] = gene.value

            elif gene.gene_type == GeneType.CONSTRAINT_SCOPE:
                cid = gid.replace('constraint_', '').replace('_scope', '')
                if cid not in tu_prime["prohibitive_constraints"]:
                    tu_prime["prohibitive_constraints"][cid] = {}
                tu_prime["prohibitive_constraints"][cid]["scope"] = gene.value

            elif gene.gene_type == GeneType.TEMPLATE_BOUNDARY:
                tu_prime["template_boundaries"][gid.replace('template_', '')] = gene.value

            elif gene.gene_type == GeneType.OBSERVATION_FAMILY:
                tu_prime["observation_families"] = gene.value

            elif gene.gene_type == GeneType.MIXTURE_PRIOR:
                domain = gid.replace('mixture_prior_', '')
                tu_prime["mixture_priors"][domain] = gene.value

        return tu_prime

    def propose_constraint_refinement(self) -> Dict[str, Any]:
        """
        Propose constraint refinements based on evolutionary pressure.
        Returns suggestions for adding/modifying constraints.
        """
        if not self.best_ever:
            return {"status": "no_evolution_run"}

        suggestions = []

        # Analyze constraint genes in best chromosome
        for gid, gene in self.best_ever.genes.items():
            if gene.gene_type == GeneType.CONSTRAINT_SEVERITY:
                if gene.value > 0.9:
                    suggestions.append({
                        "type": "strengthen",
                        "constraint": gid,
                        "reason": "High severity beneficial in best chromosome"
                    })
                elif gene.value < 0.3:
                    suggestions.append({
                        "type": "relax_or_remove",
                        "constraint": gid,
                        "reason": "Low severity in best chromosome suggests constraint may be too restrictive"
                    })

        return {
            "suggestions": suggestions,
            "based_on_generation": self.best_ever.generation,
            "fitness": self.best_ever.fitness
        }

    def propose_template_refinement(self) -> Dict[str, Any]:
        """
        Propose symbolic template boundary refinements.
        """
        if not self.best_ever:
            return {"status": "no_evolution_run"}

        refinements = {}

        for gid, gene in self.best_ever.genes.items():
            if gene.gene_type == GeneType.TEMPLATE_BOUNDARY:
                template_name = gid.replace('template_', '')
                refinements[template_name] = {
                    "evolved_value": gene.value,
                    "original_bounds": gene.bounds,
                    "deviation_from_default": gene.value - (gene.bounds[0] + gene.bounds[1]) / 2
                }

        return {
            "refinements": refinements,
            "based_on_generation": self.best_ever.generation
        }

    # =========================================================================
    # SERIALIZATION
    # =========================================================================

    def to_dict(self) -> Dict:
        """Serialize evolution state"""
        return {
            "config": {
                "population_size": self.config.population_size,
                "elite_count": self.config.elite_count,
                "tournament_size": self.config.tournament_size,
                "crossover_rate": self.config.crossover_rate,
                "mutation_rate": self.config.mutation_rate,
                "mutation_strength": self.config.mutation_strength
            },
            "generation": self.generation,
            "total_evaluations": self.total_evaluations,
            "best_fitness_history": self.best_fitness_history,
            "diversity_history": self.diversity_history,
            "best_ever": self._chromosome_to_dict(self.best_ever) if self.best_ever else None,
            "population": [self._chromosome_to_dict(c) for c in self.population]
        }

    def _chromosome_to_dict(self, chrom: Chromosome) -> Dict:
        """Convert chromosome to dict"""
        return {
            "chromosome_id": chrom.chromosome_id,
            "fitness": chrom.fitness,
            "generation": chrom.generation,
            "parent_ids": chrom.parent_ids,
            "genes": {
                gid: {
                    "gene_id": g.gene_id,
                    "gene_type": g.gene_type.value,
                    "value": g.value if not isinstance(g.value, np.ndarray) else g.value.tolist(),
                    "bounds": g.bounds,
                    "mutation_rate": g.mutation_rate,
                    "metadata": g.metadata
                }
                for gid, g in chrom.genes.items()
            },
            "metadata": chrom.metadata
        }

    def save(self, filepath: str):
        """Save evolution state to file"""
        with open(filepath, 'w') as f:
            json.dump(self.to_dict(), f, indent=2)

    @classmethod
    def load(cls, filepath: str) -> 'LEAPCoreEvolution':
        """Load evolution state from file"""
        with open(filepath, 'r') as f:
            data = json.load(f)

        config = EvolutionConfig(
            population_size=data["config"]["population_size"],
            elite_count=data["config"]["elite_count"],
            tournament_size=data["config"]["tournament_size"],
            crossover_rate=data["config"]["crossover_rate"],
            mutation_rate=data["config"]["mutation_rate"],
            mutation_strength=data["config"]["mutation_strength"]
        )

        engine = cls(config)
        engine.generation = data["generation"]
        engine.total_evaluations = data["total_evaluations"]
        engine.best_fitness_history = data["best_fitness_history"]
        engine.diversity_history = data["diversity_history"]

        # Restore chromosomes
        def dict_to_chromosome(d: Dict) -> Chromosome:
            genes = {}
            for gid, gdata in d["genes"].items():
                genes[gid] = Gene(
                    gene_id=gdata["gene_id"],
                    gene_type=GeneType(gdata["gene_type"]),
                    value=gdata["value"],
                    bounds=tuple(gdata["bounds"]) if gdata["bounds"] else None,
                    mutation_rate=gdata["mutation_rate"],
                    metadata=gdata["metadata"]
                )
            return Chromosome(
                chromosome_id=d["chromosome_id"],
                genes=genes,
                fitness=d["fitness"],
                generation=d["generation"],
                parent_ids=d["parent_ids"],
                metadata=d.get("metadata", {})
            )

        if data["best_ever"]:
            engine.best_ever = dict_to_chromosome(data["best_ever"])

        engine.population = [dict_to_chromosome(d) for d in data["population"]]

        return engine

    def stats(self) -> Dict[str, Any]:
        """Get evolution statistics"""
        return {
            "generation": self.generation,
            "population_size": len(self.population),
            "total_evaluations": self.total_evaluations,
            "stagnation_counter": self.stagnation_counter,
            "best_fitness": self.best_ever.fitness if self.best_ever else 0.0,
            "current_best_fitness": self.population[0].fitness if self.population else 0.0,
            "avg_fitness": np.mean([c.fitness for c in self.population]) if self.population else 0.0,
            "diversity": self._calculate_diversity()
        }


# =============================================================================
# EXPORTS
# =============================================================================

__all__ = [
    'LEAPCoreEvolution',
    'EvolutionConfig',
    'Chromosome',
    'Gene',
    'GeneType',
    'FitnessEvaluator',
    'V36FitnessEvaluator'
]
