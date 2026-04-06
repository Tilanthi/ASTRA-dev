"""
Feasibility Checker for Autonomous Scientific Discovery
=======================================================

Assesses the feasibility of proposed experiments, simulations, and analyses.
Ensures the autonomous discovery system operates within safety limits and
resource constraints.

Key Components:
- FeasibilityAssessor: Evaluate experiment feasibility
- ResourceEstimator: Estimate compute, data, and time requirements
- SafetyValidator: Enforce safety limits and constraints

Safety Limits:
- Max compute time: 24 hours
- Max data size: 100 GB
- Min confidence threshold: 0.3
- Max hypothesis depth: 5 iterations

Version: 1.0.0
Date: 2025-12-27
"""

import time
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Any, Tuple
from enum import Enum
import logging

logger = logging.getLogger(__name__)


# =============================================================================
# Safety Limits and Configuration
# =============================================================================

@dataclass
class SafetyLimits:
    """Safety limits for autonomous discovery"""
    max_compute_time_hours: float = 24.0
    max_data_size_gb: float = 100.0
    max_simultaneous_queries: int = 5
    min_confidence_threshold: float = 0.3
    max_hypothesis_depth: int = 5
    max_papers_per_review: int = 50
    max_download_rate_mbps: float = 100.0  # Max download rate
    max_memory_gb: float = 32.0  # Max memory usage

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            'max_compute_time_hours': self.max_compute_time_hours,
            'max_data_size_gb': self.max_data_size_gb,
            'max_simultaneous_queries': self.max_simultaneous_queries,
            'min_confidence_threshold': self.min_confidence_threshold,
            'max_hypothesis_depth': self.max_hypothesis_depth,
            'max_papers_per_review': self.max_papers_per_review,
            'max_download_rate_mbps': self.max_download_rate_mbps,
            'max_memory_gb': self.max_memory_gb,
        }


DEFAULT_SAFETY_LIMITS = SafetyLimits()


# =============================================================================
# Feasibility Assessment
# =============================================================================

class FeasibilityLevel(Enum):
    """Feasibility levels"""
    INFEASIBLE = 0         # Cannot be done
    LOW = 1                # Possible but risky
    MEDIUM = 2             # Feasible with constraints
    HIGH = 3               # Highly feasible
    GUARANTEED = 4         # Definitely feasible


@dataclass
class ResourceEstimate:
    """Estimated resource requirements"""
    compute_time_hours: float = 0.0
    data_size_gb: float = 0.0
    memory_gb: float = 0.0
    network_gb: float = 0.0
    storage_gb: float = 0.0

    # Detailed breakdown
    cpu_hours: float = 0.0
    gpu_hours: float = 0.0
    disk_io_gb: float = 0.0

    # Confidence in estimate
    confidence: float = 0.5

    def total_cost_score(self) -> float:
        """
        Calculate total cost score (0-1, higher is more expensive)
        """
        # Normalize each component
        compute_cost = min(1.0, self.compute_time_hours / 24.0)
        data_cost = min(1.0, self.data_size_gb / 100.0)
        memory_cost = min(1.0, self.memory_gb / 32.0)

        # Weighted combination
        total = 0.5 * compute_cost + 0.3 * data_cost + 0.2 * memory_cost
        return total


@dataclass
class FeasibilityResult:
    """Result of feasibility assessment"""
    feasible: bool
    level: FeasibilityLevel
    confidence: float

    # Resource estimates
    estimated_resources: ResourceEstimate

    # Constraint checks
    data_available: bool = True
    compute_feasible: bool = True
    time_reasonable: bool = True
    memory_sufficient: bool = True

    # Detailed assessment
    limiting_factors: List[str] = field(default_factory=list)
    recommendations: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)

    # Risk assessment
    risk_score: float = 0.0  # 0-1, higher is riskier

    # Metadata
    assessment_time: float = field(default_factory=time.time)

    def summary(self) -> str:
        """Generate summary string"""
        status = "FEASIBLE" if self.feasible else "INFEASIBLE"
        return (
            f"Feasibility: {status} ({self.level.name})\n"
            f"Confidence: {self.confidence:.2f}\n"
            f"Risk Score: {self.risk_score:.2f}\n"
            f"Estimated Resources:\n"
            f"  - Compute: {self.estimated_resources.compute_time_hours:.2f} hours\n"
            f"  - Data: {self.estimated_resources.data_size_gb:.2f} GB\n"
            f"  - Memory: {self.estimated_resources.memory_gb:.2f} GB\n"
            + (f"Limiting Factors: {', '.join(self.limiting_factors)}\n" if self.limiting_factors else "")
            + (f"Warnings: {', '.join(self.warnings)}\n" if self.warnings else "")
        )


# =============================================================================
# Resource Estimator
# =============================================================================

class ResourceEstimator:
    """
    Estimate resource requirements for different task types.

    Uses heuristics and historical data to predict compute time,
    data requirements, and memory usage.
    """

    def __init__(self):
        # Historical performance data (can be learned over time)
        self.performance_db = {
            'pdf_processing': {'time_per_page': 0.5, 'memory_per_page': 0.01},
            'database_query': {'time_per_query': 2.0, 'data_per_result': 0.001},
            'bayesian_inference': {'time_per_iteration': 0.1, 'memory_per_param': 0.05},
            'simulation_mhd': {'time_per_cell_step': 1e-6, 'memory_per_cell': 0.0001},
            'ml_classification': {'time_per_sample': 0.01, 'memory_per_model': 1.0},
        }

    def estimate_pdf_processing(self, num_papers: int, avg_pages: int = 10) -> ResourceEstimate:
        """Estimate resources for PDF processing"""
        total_pages = num_papers * avg_pages
        perf = self.performance_db['pdf_processing']

        return ResourceEstimate(
            compute_time_hours=(total_pages * perf['time_per_page']) / 3600.0,
            memory_gb=total_pages * perf['memory_per_page'],
            data_size_gb=num_papers * 0.5,  # ~0.5 GB per paper
            storage_gb=num_papers * 0.1,  # Extracted text
            confidence=0.8
        )

    def estimate_database_query(self, num_queries: int,
                               expected_results_per_query: int = 100) -> ResourceEstimate:
        """Estimate resources for database queries"""
        perf = self.performance_db['database_query']
        total_results = num_queries * expected_results_per_query

        return ResourceEstimate(
            compute_time_hours=(num_queries * perf['time_per_query']) / 3600.0,
            network_gb=total_results * perf['data_per_result'],
            data_size_gb=total_results * perf['data_per_result'],
            memory_gb=min(1.0, total_results * 0.0001),  # Catalog data
            confidence=0.7
        )

    def estimate_bayesian_inference(self, num_parameters: int,
                                    num_iterations: int = 10000) -> ResourceEstimate:
        """Estimate resources for Bayesian inference"""
        perf = self.performance_db['bayesian_inference']

        return ResourceEstimate(
            compute_time_hours=(num_iterations * perf['time_per_iteration']) / 3600.0,
            cpu_hours=(num_iterations * perf['time_per_iteration']) / 3600.0,
            memory_gb=num_parameters * perf['memory_per_param'],
            confidence=0.75
        )

    def estimate_simulation(self, simulation_type: str,
                           grid_cells: int, timesteps: int) -> ResourceEstimate:
        """Estimate resources for physical simulations"""
        if simulation_type == 'mhd':
            perf = self.performance_db['simulation_mhd']
            total_operations = grid_cells * timesteps

            return ResourceEstimate(
                compute_time_hours=(total_operations * perf['time_per_cell_step']) / 3600.0,
                cpu_hours=(total_operations * perf['time_per_cell_step']) / 3600.0,
                memory_gb=grid_cells * perf['memory_per_cell'],
                storage_gb=grid_cells * timesteps * 1e-6,  # Output data
                confidence=0.6
            )
        else:
            # Generic estimate
            return ResourceEstimate(
                compute_time_hours=1.0,
                memory_gb=4.0,
                confidence=0.3
            )

    def estimate_ml_analysis(self, num_samples: int,
                            model_complexity: str = 'medium') -> ResourceEstimate:
        """Estimate resources for ML analysis"""
        perf = self.performance_db['ml_classification']

        complexity_factors = {'simple': 0.5, 'medium': 1.0, 'complex': 2.0}
        factor = complexity_factors.get(model_complexity, 1.0)

        return ResourceEstimate(
            compute_time_hours=(num_samples * perf['time_per_sample'] * factor) / 3600.0,
            memory_gb=perf['memory_per_model'] * factor,
            confidence=0.7
        )

    def combine_estimates(self, estimates: List[ResourceEstimate]) -> ResourceEstimate:
        """Combine multiple resource estimates"""
        if not estimates:
            return ResourceEstimate()

        combined = ResourceEstimate(
            compute_time_hours=sum(e.compute_time_hours for e in estimates),
            data_size_gb=sum(e.data_size_gb for e in estimates),
            memory_gb=max(e.memory_gb for e in estimates),  # Peak memory
            network_gb=sum(e.network_gb for e in estimates),
            storage_gb=sum(e.storage_gb for e in estimates),
            cpu_hours=sum(e.cpu_hours for e in estimates),
            gpu_hours=sum(e.gpu_hours for e in estimates),
            disk_io_gb=sum(e.disk_io_gb for e in estimates),
            confidence=min(e.confidence for e in estimates)  # Conservative
        )

        return combined


# =============================================================================
# Safety Validator
# =============================================================================

class SafetyValidator:
    """
    Validate that proposed tasks satisfy safety constraints.

    Enforces resource limits and prevents unsafe operations.
    """

    def __init__(self, limits: Optional[SafetyLimits] = None):
        self.limits = limits or DEFAULT_SAFETY_LIMITS
        logger.info(f"SafetyValidator initialized with limits: {self.limits}")

    def validate(self, estimated: ResourceEstimate) -> Tuple[bool, List[str]]:
        """
        Validate resource estimate against safety limits.

        Returns:
            (is_safe, violations)
        """
        violations = []

        # Check compute time
        if estimated.compute_time_hours > self.limits.max_compute_time_hours:
            violations.append(
                f"Compute time {estimated.compute_time_hours:.1f}h exceeds "
                f"limit of {self.limits.max_compute_time_hours:.1f}h"
            )

        # Check data size
        if estimated.data_size_gb > self.limits.max_data_size_gb:
            violations.append(
                f"Data size {estimated.data_size_gb:.1f}GB exceeds "
                f"limit of {self.limits.max_data_size_gb:.1f}GB"
            )

        # Check memory
        if estimated.memory_gb > self.limits.max_memory_gb:
            violations.append(
                f"Memory {estimated.memory_gb:.1f}GB exceeds "
                f"limit of {self.limits.max_memory_gb:.1f}GB"
            )

        is_safe = len(violations) == 0
        return is_safe, violations

    def validate_confidence(self, confidence: float) -> bool:
        """Check if confidence meets minimum threshold"""
        return confidence >= self.limits.min_confidence_threshold

    def validate_hypothesis_depth(self, depth: int) -> bool:
        """Check if hypothesis refinement depth is within limits"""
        return depth <= self.limits.max_hypothesis_depth


# =============================================================================
# Feasibility Assessor (Main Interface)
# =============================================================================

class FeasibilityAssessor:
    """
    Main interface for assessing experiment and analysis feasibility.

    Combines resource estimation with safety validation to determine
    if a proposed task can be executed within constraints.
    """

    def __init__(self, limits: Optional[SafetyLimits] = None):
        self.estimator = ResourceEstimator()
        self.validator = SafetyValidator(limits)
        self.limits = limits or DEFAULT_SAFETY_LIMITS

        logger.info("FeasibilityAssessor initialized")

    def assess_experiment(self, task_description: Dict[str, Any]) -> FeasibilityResult:
        """
        Assess feasibility of a proposed experiment.

        Args:
            task_description: Dictionary with task details
                - 'type': Task type ('literature', 'database', 'inference', 'simulation', 'ml')
                - 'parameters': Task-specific parameters

        Returns:
            FeasibilityResult with detailed assessment
        """
        task_type = task_description.get('type', 'unknown')
        params = task_description.get('parameters', {})

        # Estimate resources based on task type
        if task_type == 'literature':
            num_papers = params.get('num_papers', 10)
            estimated = self.estimator.estimate_pdf_processing(num_papers)

        elif task_type == 'database':
            num_queries = params.get('num_queries', 5)
            estimated = self.estimator.estimate_database_query(num_queries)

        elif task_type == 'inference':
            num_params = params.get('num_parameters', 5)
            num_iter = params.get('num_iterations', 10000)
            estimated = self.estimator.estimate_bayesian_inference(num_params, num_iter)

        elif task_type == 'simulation':
            sim_type = params.get('simulation_type', 'generic')
            grid_cells = params.get('grid_cells', 100**3)
            timesteps = params.get('timesteps', 1000)
            estimated = self.estimator.estimate_simulation(sim_type, grid_cells, timesteps)

        elif task_type == 'ml':
            num_samples = params.get('num_samples', 1000)
            complexity = params.get('complexity', 'medium')
            estimated = self.estimator.estimate_ml_analysis(num_samples, complexity)

        else:
            # Unknown task - conservative estimate
            estimated = ResourceEstimate(
                compute_time_hours=1.0,
                memory_gb=2.0,
                confidence=0.3
            )

        # Validate against safety limits
        is_safe, violations = self.validator.validate(estimated)

        # Determine feasibility level
        cost_score = estimated.total_cost_score()

        if not is_safe:
            level = FeasibilityLevel.INFEASIBLE
            feasible = False
        elif cost_score < 0.3:
            level = FeasibilityLevel.HIGH
            feasible = True
        elif cost_score < 0.6:
            level = FeasibilityLevel.MEDIUM
            feasible = True
        elif cost_score < 0.9:
            level = FeasibilityLevel.LOW
            feasible = True
        else:
            level = FeasibilityLevel.LOW
            feasible = True

        # Calculate risk score
        risk_score = max(cost_score, 1.0 - estimated.confidence)

        # Generate recommendations
        recommendations = []
        if cost_score > 0.7:
            recommendations.append("Consider reducing scope or using approximations")
        if estimated.confidence < 0.5:
            recommendations.append("Low confidence - consider pilot study first")
        if estimated.memory_gb > self.limits.max_memory_gb * 0.8:
            recommendations.append("High memory usage - monitor for out-of-memory errors")

        # Create result
        result = FeasibilityResult(
            feasible=feasible,
            level=level,
            confidence=estimated.confidence,
            estimated_resources=estimated,
            data_available=True,  # Would check actual data availability
            compute_feasible=is_safe,
            time_reasonable=estimated.compute_time_hours < self.limits.max_compute_time_hours,
            memory_sufficient=estimated.memory_gb < self.limits.max_memory_gb,
            limiting_factors=violations,
            recommendations=recommendations,
            risk_score=risk_score
        )

        logger.info(f"Feasibility assessment for {task_type}: {level.name}")
        return result

    def assess_pipeline(self, tasks: List[Dict[str, Any]]) -> FeasibilityResult:
        """
        Assess feasibility of a pipeline of tasks.

        Combines estimates for multiple sequential tasks.
        """
        estimates = [self.assess_experiment(task).estimated_resources for task in tasks]
        combined = self.estimator.combine_estimates(estimates)

        # Create combined task description
        combined_task = {
            'type': 'pipeline',
            'parameters': {'num_tasks': len(tasks)}
        }

        # Assess with combined estimate
        is_safe, violations = self.validator.validate(combined)
        cost_score = combined.total_cost_score()

        if not is_safe:
            level = FeasibilityLevel.INFEASIBLE
            feasible = False
        elif cost_score < 0.4:
            level = FeasibilityLevel.HIGH
            feasible = True
        else:
            level = FeasibilityLevel.MEDIUM
            feasible = True

        return FeasibilityResult(
            feasible=feasible,
            level=level,
            confidence=combined.confidence,
            estimated_resources=combined,
            limiting_factors=violations,
            risk_score=cost_score
        )


# =============================================================================
# Factory Function
# =============================================================================

def create_feasibility_assessor(
    max_compute_hours: Optional[float] = None,
    max_data_gb: Optional[float] = None,
    custom_limits: Optional[SafetyLimits] = None
) -> FeasibilityAssessor:
    """
    Create a feasibility assessor with custom limits.

    Args:
        max_compute_hours: Override default compute time limit
        max_data_gb: Override default data size limit
        custom_limits: Complete custom SafetyLimits object

    Returns:
        Configured FeasibilityAssessor
    """
    if custom_limits:
        limits = custom_limits
    else:
        limits = SafetyLimits()
        if max_compute_hours is not None:
            limits.max_compute_time_hours = max_compute_hours
        if max_data_gb is not None:
            limits.max_data_size_gb = max_data_gb

    return FeasibilityAssessor(limits)


# =============================================================================
# Example Usage
# =============================================================================

if __name__ == "__main__":
    # Configure logging
    logging.basicConfig(level=logging.INFO)

    # Create assessor
    assessor = create_feasibility_assessor()

    # Assess literature review task
    lit_task = {
        'type': 'literature',
        'parameters': {'num_papers': 20}
    }
    result = assessor.assess_experiment(lit_task)
    print("\n" + "="*60)
    print("LITERATURE REVIEW FEASIBILITY")
    print("="*60)
    print(result.summary())

    # Assess Bayesian inference task
    inf_task = {
        'type': 'inference',
        'parameters': {'num_parameters': 10, 'num_iterations': 50000}
    }
    result = assessor.assess_experiment(inf_task)
    print("\n" + "="*60)
    print("BAYESIAN INFERENCE FEASIBILITY")
    print("="*60)
    print(result.summary())

    # Assess full pipeline
    pipeline = [lit_task, inf_task]
    result = assessor.assess_pipeline(pipeline)
    print("\n" + "="*60)
    print("PIPELINE FEASIBILITY")
    print("="*60)
    print(result.summary())



def utility_function_7(*args, **kwargs):
    """Utility function 7."""
    return None


