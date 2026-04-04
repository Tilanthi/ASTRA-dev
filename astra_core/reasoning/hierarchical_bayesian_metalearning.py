"""
Hierarchical Bayesian Meta-Learning for STAN V42

Learn prior distributions from solved problems within each domain:
- Transfer learned priors to new problems
- Adaptive regularization based on problem similarity
- Better parameter initialization, faster convergence on sparse data

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
import json


class PriorType(Enum):
    """Types of learned priors"""
    GAUSSIAN = "gaussian"
    MIXTURE_GAUSSIAN = "mixture_gaussian"
    LOG_NORMAL = "log_normal"
    UNIFORM = "uniform"
    HIERARCHICAL = "hierarchical"
    EMPIRICAL = "empirical"
    INFORMATIVE = "informative"
    WEAKLY_INFORMATIVE = "weakly_informative"


class TaskSimilarityMetric(Enum):
    """Metrics for measuring task similarity"""
    PARAMETER_SPACE = "parameter_space"
    FEATURE_BASED = "feature_based"
    STRUCTURAL = "structural"
    DOMAIN_HIERARCHY = "domain_hierarchy"
    EMBEDDING = "embedding"


@dataclass
class LearnedPrior:
    """A learned prior distribution for a parameter"""
    prior_id: str
    parameter_name: str
    prior_type: PriorType

    # Distribution parameters
    location: float = 0.0  # Mean/mode
    scale: float = 1.0     # Std/precision
    shape: float = 1.0     # Shape parameter (for gamma, etc.)
    bounds: Tuple[float, float] = field(default_factory=lambda: (-float('inf'), float('inf')))

    # Mixture components (for mixture priors)
    mixture_weights: List[float] = field(default_factory=list)
    mixture_components: List[Dict[str, float]] = field(default_factory=list)

    # Meta-information
    domain: str = ""
    num_tasks_learned: int = 0
    confidence: float = 0.5
    last_updated: float = field(default_factory=time.time)

    # Source tasks
    source_task_ids: List[str] = field(default_factory=list)

    def __post_init__(self):
        if not self.prior_id:
            self.prior_id = f"prior_{uuid.uuid4().hex[:8]}"

    def sample(self, n: int = 1) -> List[float]:
        """Sample from this prior"""
        samples = []
        for _ in range(n):
            if self.prior_type == PriorType.GAUSSIAN:
                s = random.gauss(self.location, self.scale)
            elif self.prior_type == PriorType.LOG_NORMAL:
                s = random.lognormvariate(self.location, self.scale)
            elif self.prior_type == PriorType.UNIFORM:
                s = random.uniform(self.bounds[0], self.bounds[1])
            elif self.prior_type == PriorType.MIXTURE_GAUSSIAN:
                # Sample from mixture
                if self.mixture_weights and self.mixture_components:
                    idx = random.choices(range(len(self.mixture_weights)),
                                        weights=self.mixture_weights)[0]
                    comp = self.mixture_components[idx]
                    s = random.gauss(comp.get("mean", 0), comp.get("std", 1))
                else:
                    s = random.gauss(self.location, self.scale)
            else:
                s = random.gauss(self.location, self.scale)

            # Apply bounds
            s = max(self.bounds[0], min(self.bounds[1], s))
            samples.append(s)

        return samples if n > 1 else samples[0]

    def log_prob(self, x: float) -> float:
        """Compute log probability of x under this prior"""
        # Check bounds
        if x < self.bounds[0] or x > self.bounds[1]:
            return float('-inf')

        if self.prior_type == PriorType.GAUSSIAN:
            return -0.5 * ((x - self.location) / self.scale)**2 - math.log(self.scale) - 0.5 * math.log(2 * math.pi)

        elif self.prior_type == PriorType.LOG_NORMAL:
            if x <= 0:
                return float('-inf')
            return -0.5 * ((math.log(x) - self.location) / self.scale)**2 - math.log(x * self.scale) - 0.5 * math.log(2 * math.pi)

        elif self.prior_type == PriorType.UNIFORM:
            width = self.bounds[1] - self.bounds[0]
            if width > 0:
                return -math.log(width)
            return 0

        elif self.prior_type == PriorType.MIXTURE_GAUSSIAN:
            if not self.mixture_weights or not self.mixture_components:
                return -0.5 * ((x - self.location) / self.scale)**2

            # Log-sum-exp for mixture
            log_probs = []
            for w, comp in zip(self.mixture_weights, self.mixture_components):
                mu = comp.get("mean", 0)
                sigma = comp.get("std", 1)
                lp = math.log(w) - 0.5 * ((x - mu) / sigma)**2 - math.log(sigma)
                log_probs.append(lp)

            max_lp = max(log_probs)
            return max_lp + math.log(sum(math.exp(lp - max_lp) for lp in log_probs))

        return 0.0


@dataclass
class TaskSignature:
    """Signature describing a task for similarity computation"""
    task_id: str
    domain: str
    subdomain: str = ""

    # Feature vector
    features: Dict[str, float] = field(default_factory=dict)

    # Parameter space description
    parameter_names: List[str] = field(default_factory=list)
    parameter_bounds: Dict[str, Tuple[float, float]] = field(default_factory=dict)

    # Problem characteristics
    data_size: int = 0
    dimensionality: int = 0
    noise_level: float = 0.0

    # Structural information
    model_type: str = ""
    physics_constraints: List[str] = field(default_factory=list)

    # Embedding (if computed)
    embedding: List[float] = field(default_factory=list)

    def __post_init__(self):
        if not self.task_id:
            self.task_id = f"task_{uuid.uuid4().hex[:8]}"


@dataclass
class SolvedTask:
    """A solved task with learned parameters"""
    task_id: str
    signature: TaskSignature

    # Solution
    optimal_parameters: Dict[str, float]
    parameter_uncertainties: Dict[str, float]

    # Fit quality
    log_likelihood: float = 0.0
    chi_squared: float = 0.0
    degrees_of_freedom: int = 0

    # Meta-data
    solve_time: float = 0.0
    iterations: int = 0
    converged: bool = True

    created_at: float = field(default_factory=time.time)

    def __post_init__(self):
        if not self.task_id:
            self.task_id = f"solved_{uuid.uuid4().hex[:8]}"


@dataclass
class TransferResult:
    """Result of prior transfer to a new task"""
    transfer_id: str
    source_tasks: List[str]
    target_task: str

    # Transferred priors
    priors: Dict[str, LearnedPrior]

    # Transfer quality metrics
    similarity_scores: Dict[str, float]
    expected_improvement: float = 0.0

    # Regularization
    regularization_strength: float = 1.0

    created_at: float = field(default_factory=time.time)

    def __post_init__(self):
        if not self.transfer_id:
            self.transfer_id = f"transfer_{uuid.uuid4().hex[:8]}"


class TaskSimilarityComputer:
    """
    Computes similarity between tasks for prior transfer.
    """

    def __init__(self):
        self.domain_hierarchy = self._build_domain_hierarchy()

    def compute_similarity(self,
                          task1: TaskSignature,
                          task2: TaskSignature,
                          metric: TaskSimilarityMetric = TaskSimilarityMetric.FEATURE_BASED) -> float:
        """Compute similarity between two tasks"""
        if metric == TaskSimilarityMetric.PARAMETER_SPACE:
            return self._parameter_space_similarity(task1, task2)
        elif metric == TaskSimilarityMetric.FEATURE_BASED:
            return self._feature_similarity(task1, task2)
        elif metric == TaskSimilarityMetric.STRUCTURAL:
            return self._structural_similarity(task1, task2)
        elif metric == TaskSimilarityMetric.DOMAIN_HIERARCHY:
            return self._domain_hierarchy_similarity(task1, task2)
        elif metric == TaskSimilarityMetric.EMBEDDING:
            return self._embedding_similarity(task1, task2)
        else:
            return self._feature_similarity(task1, task2)

    def _parameter_space_similarity(self, task1: TaskSignature, task2: TaskSignature) -> float:
        """Similarity based on shared parameters"""
        params1 = set(task1.parameter_names)
        params2 = set(task2.parameter_names)

        if not params1 or not params2:
            return 0.0

        intersection = params1 & params2
        union = params1 | params2

        jaccard = len(intersection) / len(union) if union else 0.0

        # Also consider bounds overlap
        bound_similarity = 0.0
        for param in intersection:
            if param in task1.parameter_bounds and param in task2.parameter_bounds:
                b1 = task1.parameter_bounds[param]
                b2 = task2.parameter_bounds[param]
                overlap = max(0, min(b1[1], b2[1]) - max(b1[0], b2[0]))
                span = max(b1[1], b2[1]) - min(b1[0], b2[0])
                if span > 0:
                    bound_similarity += overlap / span

        if intersection:
            bound_similarity /= len(intersection)

        return 0.5 * jaccard + 0.5 * bound_similarity

    def _feature_similarity(self, task1: TaskSignature, task2: TaskSignature) -> float:
        """Similarity based on feature vectors"""
        f1 = task1.features
        f2 = task2.features

        if not f1 or not f2:
            # Fall back to basic attributes
            sim = 0.0
            if task1.domain == task2.domain:
                sim += 0.5
            if task1.subdomain == task2.subdomain:
                sim += 0.3
            if task1.model_type == task2.model_type:
                sim += 0.2
            return sim

        # Cosine similarity on shared features
        shared = set(f1.keys()) & set(f2.keys())
        if not shared:
            return 0.0

        dot = sum(f1[k] * f2[k] for k in shared)
        norm1 = math.sqrt(sum(f1[k]**2 for k in shared))
        norm2 = math.sqrt(sum(f2[k]**2 for k in shared))

        if norm1 > 0 and norm2 > 0:
            return (dot / (norm1 * norm2) + 1) / 2  # Normalize to [0, 1]
        return 0.0

    def _structural_similarity(self, task1: TaskSignature, task2: TaskSignature) -> float:
        """Similarity based on problem structure"""
        sim = 0.0

        # Model type
        if task1.model_type == task2.model_type:
            sim += 0.4

        # Physics constraints overlap
        c1 = set(task1.physics_constraints)
        c2 = set(task2.physics_constraints)
        if c1 and c2:
            sim += 0.3 * len(c1 & c2) / len(c1 | c2)

        # Dimensionality similarity
        if task1.dimensionality > 0 and task2.dimensionality > 0:
            ratio = min(task1.dimensionality, task2.dimensionality) / max(task1.dimensionality, task2.dimensionality)
            sim += 0.3 * ratio

        return sim

    def _domain_hierarchy_similarity(self, task1: TaskSignature, task2: TaskSignature) -> float:
        """Similarity based on domain hierarchy"""
        # Find common ancestor in hierarchy
        path1 = self._get_domain_path(task1.domain)
        path2 = self._get_domain_path(task2.domain)

        # Count shared ancestors
        shared = 0
        for i, (a, b) in enumerate(zip(path1, path2)):
            if a == b:
                shared = i + 1
            else:
                break

        max_depth = max(len(path1), len(path2))
        if max_depth > 0:
            return shared / max_depth
        return 0.0

    def _embedding_similarity(self, task1: TaskSignature, task2: TaskSignature) -> float:
        """Similarity based on learned embeddings"""
        e1 = task1.embedding
        e2 = task2.embedding

        if not e1 or not e2 or len(e1) != len(e2):
            return self._feature_similarity(task1, task2)

        # Cosine similarity
        dot = sum(a * b for a, b in zip(e1, e2))
        norm1 = math.sqrt(sum(a**2 for a in e1))
        norm2 = math.sqrt(sum(b**2 for b in e2))

        if norm1 > 0 and norm2 > 0:
            return (dot / (norm1 * norm2) + 1) / 2
        return 0.0

    def _build_domain_hierarchy(self) -> Dict[str, List[str]]:
        """Build domain hierarchy for astrophysics"""
        return {
            "astrophysics": ["astrophysics"],
            "gravitational_lensing": ["astrophysics", "gravitational_lensing"],
            "strong_lensing": ["astrophysics", "gravitational_lensing", "strong_lensing"],
            "weak_lensing": ["astrophysics", "gravitational_lensing", "weak_lensing"],
            "stellar": ["astrophysics", "stellar"],
            "stellar_evolution": ["astrophysics", "stellar", "stellar_evolution"],
            "stellar_atmospheres": ["astrophysics", "stellar", "stellar_atmospheres"],
            "galactic": ["astrophysics", "galactic"],
            "galaxy_dynamics": ["astrophysics", "galactic", "galaxy_dynamics"],
            "galaxy_morphology": ["astrophysics", "galactic", "galaxy_morphology"],
            "cosmology": ["astrophysics", "cosmology"],
            "dark_matter": ["astrophysics", "cosmology", "dark_matter"],
            "dark_energy": ["astrophysics", "cosmology", "dark_energy"],
            "molecular_clouds": ["astrophysics", "interstellar_medium", "molecular_clouds"],
            "radiative_transfer": ["astrophysics", "radiative_transfer"],
            "spectroscopy": ["astrophysics", "spectroscopy"],
        }

    def _get_domain_path(self, domain: str) -> List[str]:
        """Get path from root to domain in hierarchy"""
        return self.domain_hierarchy.get(domain, [domain])


class PriorLearner:
    """
    Learns prior distributions from solved tasks.
    """

    def __init__(self):
        self.min_tasks_for_learning = 3
        self.prior_update_rate = 0.1

    def learn_prior(self,
                   parameter_name: str,
                   solved_tasks: List[SolvedTask],
                   domain: str = "") -> LearnedPrior:
        """
        Learn a prior for a parameter from solved tasks.
        """
        # Extract parameter values
        values = []
        uncertainties = []

        for task in solved_tasks:
            if parameter_name in task.optimal_parameters:
                values.append(task.optimal_parameters[parameter_name])
                if parameter_name in task.parameter_uncertainties:
                    uncertainties.append(task.parameter_uncertainties[parameter_name])
                else:
                    uncertainties.append(1.0)

        if len(values) < self.min_tasks_for_learning:
            # Not enough data - return weakly informative prior
            return self._create_weakly_informative_prior(parameter_name, domain)

        # Decide on prior type based on data
        prior_type = self._select_prior_type(values)

        # Fit prior parameters
        if prior_type == PriorType.GAUSSIAN:
            return self._fit_gaussian_prior(parameter_name, values, uncertainties, domain, solved_tasks)
        elif prior_type == PriorType.LOG_NORMAL:
            return self._fit_lognormal_prior(parameter_name, values, uncertainties, domain, solved_tasks)
        elif prior_type == PriorType.MIXTURE_GAUSSIAN:
            return self._fit_mixture_prior(parameter_name, values, uncertainties, domain, solved_tasks)
        else:
            return self._fit_gaussian_prior(parameter_name, values, uncertainties, domain, solved_tasks)

    def update_prior(self,
                    existing_prior: LearnedPrior,
                    new_task: SolvedTask) -> LearnedPrior:
        """
        Update an existing prior with a new solved task.
        """
        param_name = existing_prior.parameter_name

        if param_name not in new_task.optimal_parameters:
            return existing_prior

        new_value = new_task.optimal_parameters[param_name]
        new_uncertainty = new_task.parameter_uncertainties.get(param_name, 1.0)

        # Bayesian update (simplified)
        if existing_prior.prior_type == PriorType.GAUSSIAN:
            # Precision-weighted update
            old_prec = 1 / (existing_prior.scale**2)
            new_prec = 1 / (new_uncertainty**2)

            total_prec = old_prec + self.prior_update_rate * new_prec
            new_location = (old_prec * existing_prior.location +
                          self.prior_update_rate * new_prec * new_value) / total_prec
            new_scale = 1 / math.sqrt(total_prec)

            existing_prior.location = new_location
            existing_prior.scale = new_scale

        existing_prior.num_tasks_learned += 1
        existing_prior.source_task_ids.append(new_task.task_id)
        existing_prior.last_updated = time.time()

        # Update confidence
        existing_prior.confidence = min(0.95,
            existing_prior.confidence + 0.05 * (1 - existing_prior.confidence))

        return existing_prior

    def _select_prior_type(self, values: List[float]) -> PriorType:
        """Select appropriate prior type based on data"""
        if not values:
            return PriorType.GAUSSIAN

        # Check if all positive (might be log-normal)
        if all(v > 0 for v in values):
            log_values = [math.log(v) for v in values]

            # Check normality of log values vs original
            log_skew = self._compute_skewness(log_values)
            orig_skew = self._compute_skewness(values)

            if abs(log_skew) < abs(orig_skew):
                return PriorType.LOG_NORMAL

        # Check for multimodality
        if len(values) >= 10:
            if self._is_multimodal(values):
                return PriorType.MIXTURE_GAUSSIAN

        return PriorType.GAUSSIAN

    def _compute_skewness(self, values: List[float]) -> float:
        """Compute skewness of values"""
        if len(values) < 3:
            return 0.0

        mean = sum(values) / len(values)
        variance = sum((v - mean)**2 for v in values) / len(values)
        if variance == 0:
            return 0.0

        std = math.sqrt(variance)
        skew = sum(((v - mean) / std)**3 for v in values) / len(values)
        return skew

    def _is_multimodal(self, values: List[float]) -> bool:
        """Simple test for multimodality using dip test approximation"""
        if len(values) < 10:
            return False

        sorted_vals = sorted(values)
        n = len(sorted_vals)

        # Look for significant gaps
        gaps = [sorted_vals[i+1] - sorted_vals[i] for i in range(n-1)]
        mean_gap = sum(gaps) / len(gaps)
        max_gap = max(gaps)

        # If max gap is much larger than mean, might be multimodal
        return max_gap > 3 * mean_gap

    def _create_weakly_informative_prior(self,
                                         parameter_name: str,
                                         domain: str) -> LearnedPrior:
        """Create a weakly informative prior"""
        # Domain-specific defaults
        defaults = {
            "einstein_radius": (1.0, 2.0, (0.1, 10.0)),
            "velocity_dispersion": (200.0, 100.0, (50.0, 500.0)),
            "redshift": (1.0, 0.5, (0.0, 10.0)),
            "mass": (1e12, 1e12, (1e8, 1e16)),
            "temperature": (5000.0, 2000.0, (100.0, 50000.0)),
            "metallicity": (0.0, 0.5, (-3.0, 1.0)),
        }

        # Check for known parameter
        for key, (loc, scale, bounds) in defaults.items():
            if key in parameter_name.lower():
                return LearnedPrior(
                    prior_id="",
                    parameter_name=parameter_name,
                    prior_type=PriorType.WEAKLY_INFORMATIVE,
                    location=loc,
                    scale=scale,
                    bounds=bounds,
                    domain=domain,
                    confidence=0.3
                )

        # Generic weakly informative
        return LearnedPrior(
            prior_id="",
            parameter_name=parameter_name,
            prior_type=PriorType.WEAKLY_INFORMATIVE,
            location=0.0,
            scale=10.0,
            domain=domain,
            confidence=0.1
        )

    def _fit_gaussian_prior(self,
                           parameter_name: str,
                           values: List[float],
                           uncertainties: List[float],
                           domain: str,
                           tasks: List[SolvedTask]) -> LearnedPrior:
        """Fit a Gaussian prior"""
        # Weighted mean and variance
        weights = [1/u**2 for u in uncertainties]
        total_weight = sum(weights)

        mean = sum(w * v for w, v in zip(weights, values)) / total_weight
        variance = sum(w * (v - mean)**2 for w, v in zip(weights, values)) / total_weight

        # Add uncertainty in the mean
        mean_uncertainty = 1 / math.sqrt(total_weight)
        scale = math.sqrt(variance + mean_uncertainty**2)

        # Compute bounds from data
        min_val = min(values)
        max_val = max(values)
        range_val = max_val - min_val
        bounds = (min_val - 0.5 * range_val, max_val + 0.5 * range_val)

        return LearnedPrior(
            prior_id="",
            parameter_name=parameter_name,
            prior_type=PriorType.GAUSSIAN,
            location=mean,
            scale=scale,
            bounds=bounds,
            domain=domain,
            num_tasks_learned=len(tasks),
            confidence=min(0.9, 0.3 + 0.1 * len(tasks)),
            source_task_ids=[t.task_id for t in tasks]
        )

    def _fit_lognormal_prior(self,
                            parameter_name: str,
                            values: List[float],
                            uncertainties: List[float],
                            domain: str,
                            tasks: List[SolvedTask]) -> LearnedPrior:
        """Fit a log-normal prior"""
        log_values = [math.log(v) for v in values if v > 0]

        if not log_values:
            return self._fit_gaussian_prior(parameter_name, values, uncertainties, domain, tasks)

        mean = sum(log_values) / len(log_values)
        variance = sum((v - mean)**2 for v in log_values) / len(log_values)
        scale = math.sqrt(variance)

        return LearnedPrior(
            prior_id="",
            parameter_name=parameter_name,
            prior_type=PriorType.LOG_NORMAL,
            location=mean,
            scale=scale,
            bounds=(0, float('inf')),
            domain=domain,
            num_tasks_learned=len(tasks),
            confidence=min(0.9, 0.3 + 0.1 * len(tasks)),
            source_task_ids=[t.task_id for t in tasks]
        )

    def _fit_mixture_prior(self,
                          parameter_name: str,
                          values: List[float],
                          uncertainties: List[float],
                          domain: str,
                          tasks: List[SolvedTask]) -> LearnedPrior:
        """Fit a Gaussian mixture prior using simple k-means"""
        # Simple 2-component mixture
        k = 2

        # Initialize with min/max
        sorted_vals = sorted(values)
        centers = [sorted_vals[len(sorted_vals)//4], sorted_vals[3*len(sorted_vals)//4]]

        # K-means iterations
        for _ in range(10):
            # Assign to clusters
            clusters = [[] for _ in range(k)]
            for v in values:
                dists = [abs(v - c) for c in centers]
                clusters[dists.index(min(dists))].append(v)

            # Update centers
            for i in range(k):
                if clusters[i]:
                    centers[i] = sum(clusters[i]) / len(clusters[i])

        # Compute mixture parameters
        weights = []
        components = []

        for i in range(k):
            if clusters[i]:
                w = len(clusters[i]) / len(values)
                m = sum(clusters[i]) / len(clusters[i])
                s = math.sqrt(sum((v - m)**2 for v in clusters[i]) / len(clusters[i])) if len(clusters[i]) > 1 else 1.0

                weights.append(w)
                components.append({"mean": m, "std": max(s, 0.1)})

        return LearnedPrior(
            prior_id="",
            parameter_name=parameter_name,
            prior_type=PriorType.MIXTURE_GAUSSIAN,
            location=sum(c["mean"] * w for c, w in zip(components, weights)),
            scale=1.0,
            mixture_weights=weights,
            mixture_components=components,
            domain=domain,
            num_tasks_learned=len(tasks),
            confidence=min(0.85, 0.25 + 0.1 * len(tasks)),
            source_task_ids=[t.task_id for t in tasks]
        )


class HierarchicalBayesianMetaLearner:
    """
    Main interface for hierarchical Bayesian meta-learning.

    Learns from solved problems to provide better priors for new problems,
    enabling faster convergence and better regularization.
    """

    def __init__(self):
        self.similarity_computer = TaskSimilarityComputer()
        self.prior_learner = PriorLearner()

        # Storage
        self.solved_tasks: Dict[str, SolvedTask] = {}
        self.learned_priors: Dict[str, Dict[str, LearnedPrior]] = defaultdict(dict)  # domain -> param -> prior
        self.task_signatures: Dict[str, TaskSignature] = {}

        # Configuration
        self.similarity_threshold = 0.3
        self.max_source_tasks = 20
        self.regularization_decay = 0.5

        # Event callbacks
        self._callbacks: Dict[str, List[Callable]] = defaultdict(list)

    def register_solved_task(self, task: SolvedTask):
        """
        Register a solved task for learning.
        """
        self.solved_tasks[task.task_id] = task
        self.task_signatures[task.task_id] = task.signature

        # Update priors for this domain
        self._update_domain_priors(task)

        self._emit("task_registered", {
            "task_id": task.task_id,
            "domain": task.signature.domain,
            "parameters": list(task.optimal_parameters.keys())
        })

    def get_priors_for_task(self,
                           new_task: TaskSignature,
                           parameters: List[str]) -> TransferResult:
        """
        Get transferred priors for a new task.

        Args:
            new_task: Signature of the new task
            parameters: Parameters needing priors

        Returns:
            TransferResult with priors and metadata
        """
        # Find similar solved tasks
        similar_tasks = self._find_similar_tasks(new_task)

        # Transfer priors
        priors = {}
        similarity_scores = {}

        for param in parameters:
            prior, score = self._transfer_prior(param, new_task, similar_tasks)
            priors[param] = prior
            similarity_scores[param] = score

        # Compute regularization strength
        avg_similarity = sum(similarity_scores.values()) / len(similarity_scores) if similarity_scores else 0
        regularization = self._compute_regularization(avg_similarity, len(similar_tasks))

        # Expected improvement
        expected_improvement = self._estimate_improvement(priors, new_task)

        result = TransferResult(
            transfer_id="",
            source_tasks=[t.task_id for t in similar_tasks],
            target_task=new_task.task_id,
            priors=priors,
            similarity_scores=similarity_scores,
            expected_improvement=expected_improvement,
            regularization_strength=regularization
        )

        self._emit("priors_transferred", {
            "target_task": new_task.task_id,
            "num_source_tasks": len(similar_tasks),
            "parameters": parameters,
            "avg_similarity": avg_similarity
        })

        return result

    def get_initialization(self,
                          new_task: TaskSignature,
                          parameters: List[str]) -> Dict[str, float]:
        """
        Get good initial parameter values for optimization.
        """
        transfer_result = self.get_priors_for_task(new_task, parameters)

        initialization = {}
        for param, prior in transfer_result.priors.items():
            initialization[param] = prior.location

        return initialization

    def compute_regularization_term(self,
                                   parameters: Dict[str, float],
                                   priors: Dict[str, LearnedPrior],
                                   strength: float = 1.0) -> float:
        """
        Compute regularization term for optimization.

        This is the negative log prior, to be added to the objective.
        """
        reg = 0.0

        for param, value in parameters.items():
            if param in priors:
                prior = priors[param]
                log_prob = prior.log_prob(value)
                reg -= strength * log_prob

        return reg

    def get_domain_summary(self, domain: str) -> Dict[str, Any]:
        """Get summary of learned knowledge for a domain"""
        domain_tasks = [t for t in self.solved_tasks.values()
                       if t.signature.domain == domain]
        domain_priors = self.learned_priors.get(domain, {})

        return {
            "domain": domain,
            "num_tasks": len(domain_tasks),
            "num_parameters": len(domain_priors),
            "parameters": {
                name: {
                    "type": prior.prior_type.value,
                    "location": prior.location,
                    "scale": prior.scale,
                    "confidence": prior.confidence,
                    "num_tasks": prior.num_tasks_learned
                }
                for name, prior in domain_priors.items()
            },
            "avg_chi_squared": sum(t.chi_squared for t in domain_tasks) / len(domain_tasks) if domain_tasks else 0
        }

    def get_all_domains(self) -> List[str]:
        """Get list of all domains with learned priors"""
        return list(self.learned_priors.keys())

    def export_priors(self, domain: Optional[str] = None) -> Dict[str, Any]:
        """Export learned priors for persistence"""
        if domain:
            priors = self.learned_priors.get(domain, {})
        else:
            priors = dict(self.learned_priors)

        export = {}
        for d, param_priors in (priors.items() if isinstance(priors, dict) and not domain else [(domain, priors)]):
            export[d] = {}
            for name, prior in param_priors.items():
                export[d][name] = {
                    "prior_id": prior.prior_id,
                    "prior_type": prior.prior_type.value,
                    "location": prior.location,
                    "scale": prior.scale,
                    "bounds": prior.bounds,
                    "mixture_weights": prior.mixture_weights,
                    "mixture_components": prior.mixture_components,
                    "confidence": prior.confidence,
                    "num_tasks": prior.num_tasks_learned
                }

        return export

    def import_priors(self, data: Dict[str, Any]):
        """Import previously learned priors"""
        for domain, param_priors in data.items():
            for name, prior_data in param_priors.items():
                prior = LearnedPrior(
                    prior_id=prior_data.get("prior_id", ""),
                    parameter_name=name,
                    prior_type=PriorType(prior_data["prior_type"]),
                    location=prior_data["location"],
                    scale=prior_data["scale"],
                    bounds=tuple(prior_data.get("bounds", (-float('inf'), float('inf')))),
                    mixture_weights=prior_data.get("mixture_weights", []),
                    mixture_components=prior_data.get("mixture_components", []),
                    domain=domain,
                    confidence=prior_data.get("confidence", 0.5),
                    num_tasks_learned=prior_data.get("num_tasks", 0)
                )
                self.learned_priors[domain][name] = prior

    def on(self, event: str, callback: Callable):
        """Register event callback"""
