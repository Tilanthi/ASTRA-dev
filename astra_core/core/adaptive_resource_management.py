"""
Adaptive Resource Management for Computational Efficiency
==========================================================

This module addresses the challenge of computational overhead in sophisticated
autonomous systems by implementing intelligent resource management.

Based on challenges identified in ASTRA v4.5 vs robotics optimization:
- Sophisticated methods (correlated noise, Riemannian optimization) cost more
- Need for adaptive precision based on problem complexity
- Require caching and memoization for efficiency
- Need hierarchical optimization (coarse-to-fine approach)

Solutions implemented:
1. Adaptive precision based on problem requirements
2. Intelligent caching and memoization
3. Hierarchical optimization strategy
4. Resource monitoring and allocation
5. Early stopping with resource awareness
"""

import numpy as np
from typing import Dict, Any, List, Optional, Callable, Tuple
import time
import hashlib
import json
from functools import wraps


class AdaptivePrecisionManager:
    """
    Adaptive precision manager that adjusts computational methods based on
    problem requirements and available resources.

    Unlike robotics where consistent precision is needed, scientific discovery
    can benefit from adaptive precision strategies.
    """

    def __init__(self):
        """Initialize adaptive precision manager."""
        self.precision_history = []
        self.resource_monitor = ResourceMonitor()
        self.current_precision_level = 'medium'

    def assess_required_precision(self,
                                 problem_type: str,
                                 data_complexity: float,
                                 time_constraint: Optional[float] = None) -> str:
        """
        Assess required precision level for problem.

        Args:
            problem_type: Type of problem
            data_complexity: Complexity of input data (0-1)
            time_constraint: Optional time constraint in seconds

        Returns:
            Precision level: 'low', 'medium', 'high'
        """
        # Base precision from problem type
        precision_requirements = {
            'exploratory': 0.3,  # Low precision for exploration
            'parameter_estimation': 0.7,  # Medium precision
            'model_selection': 0.8,  # High precision
            'final_validation': 0.9,  # Highest precision
            'discovery': 0.6  # Medium-high for discovery
        }

        base_precision = precision_requirements.get(problem_type, 0.5)

        # Adjust based on data complexity
        adjusted_precision = base_precision + (data_complexity * 0.2)

        # Adjust based on time constraint
        if time_constraint is not None:
            available_resources = self.resource_monitor.get_available_resources()
            if available_resources['cpu_time'] < time_constraint * 0.5:
                # Limited time, reduce precision
                adjusted_precision *= 0.7

        # Convert to precision level
        if adjusted_precision < 0.4:
            precision_level = 'low'
        elif adjusted_precision < 0.7:
            precision_level = 'medium'
        else:
            precision_level = 'high'

        self.current_precision_level = precision_level
        return precision_level

    def get_optimization_method_for_precision(self,
                                            precision_level: str) -> Dict[str, Any]:
        """
        Get appropriate optimization method for precision level.

        Args:
            precision_level: Required precision level

        Returns:
            Method configuration
        """
        methods = {
            'low': {
                'method': 'gradient_descent',
                'max_iterations': 50,
                'tolerance': 1e-4,
                'use_correlated_noise': False,
                'use_manifold_optimization': False,
                'use_advanced_features': False
            },
            'medium': {
                'method': 'lbfgs',
                'max_iterations': 200,
                'tolerance': 1e-6,
                'use_correlated_noise': True,
                'use_manifold_optimization': False,
                'use_advanced_features': True
            },
            'high': {
                'method': 'riemannian_optimization',
                'max_iterations': 500,
                'tolerance': 1e-8,
                'use_correlated_noise': True,
                'use_manifold_optimization': True,
                'use_advanced_features': True
            }
        }

        return methods.get(precision_level, methods['medium'])

    def adapt_during_optimization(self,
                                 current_iteration: int,
                                 objective_history: List[float],
                                 resource_usage: Dict[str, float]) -> Dict[str, Any]:
        """
        Adapt precision during optimization based on performance.

        Args:
            current_iteration: Current iteration number
            objective_history: History of objective values
            resource_usage: Current resource usage

        Returns:
            Adaptation recommendations
        """
        recommendations = {}

        # Check if converging quickly
        if len(objective_history) > 10:
            recent_improvement = objective_history[-10] - objective_history[-1]
            total_improvement = objective_history[0] - objective_history[-1]

            # If converging quickly, can reduce precision
            if recent_improvement < total_improvement * 0.01:
                recommendations['precision'] = 'reduce'
                recommendations['reason'] = 'fast_convergence'
            # If not converging, increase precision
            elif recent_improvement > total_improvement * 0.1:
                recommendations['precision'] = 'increase'
                recommendations['reason'] = 'slow_convergence'

        # Check resource usage
        if resource_usage.get('memory_usage', 0) > 0.8:
            recommendations['memory_action'] = 'reduce_cache'
            recommendations['reason'] = 'high_memory_usage'

        if resource_usage.get('time_remaining', 1.0) < 0.2:
            recommendations['time_action'] = 'early_stop'
            recommendations['reason'] = 'low_time_remaining'

        return recommendations


class ResourceMonitor:
    """
    Monitor and manage computational resources.
    """

    def __init__(self):
        """Initialize resource monitor."""
        self.resource_history = []
        self.start_time = time.time()
        self.memory_baseline = None

    def get_available_resources(self) -> Dict[str, float]:
        """
        Get currently available resources.

        Returns:
            Resource availability metrics
        """
        try:
            import psutil
            cpu_percent = psutil.cpu_percent(interval=0.1)
            memory = psutil.virtual_memory()
            memory_available = memory.available / memory.total
        except ImportError:
            # Fallback if psutil not available
            cpu_percent = 50.0  # Assume moderate usage
            memory_available = 0.5  # Assume 50% available

        elapsed_time = time.time() - self.start_time

        return {
            'cpu_usage': cpu_percent / 100.0,
            'memory_usage': 1.0 - memory_available,
            'cpu_time': elapsed_time,
            'time_remaining': max(0, 1.0 - elapsed_time / 3600)  # Assume 1 hour budget
        }

    def estimate_computational_cost(self,
                                   problem_size: int,
                                   method_complexity: str) -> float:
        """
        Estimate computational cost for problem.

        Args:
            problem_size: Size of problem (e.g., number of parameters)
            method_complexity: Complexity level of method

        Returns:
            Estimated cost (0-1 scale)
        """
        complexity_factors = {
            'low': 1.0,
            'medium': 4.0,
            'high': 16.0
        }

        base_cost = (problem_size / 1000)  # Normalize to typical problem sizes
        complexity_multiplier = complexity_factors.get(method_complexity, 4.0)

        estimated_cost = min(base_cost * complexity_multiplier / 100, 1.0)

        return estimated_cost

    def should_use_advanced_method(self,
                                   problem_size: int,
                                   available_time: float) -> bool:
        """
        Determine if advanced methods are feasible.

        Args:
            problem_size: Size of problem
            available_time: Available time in seconds

        Returns:
            Whether to use advanced methods
        """
        # Estimate time for basic vs advanced methods
        basic_time = problem_size * 0.001  # Rough estimate
        advanced_time = basic_time * 4  # Advanced methods take ~4x longer

        return advanced_time < available_time * 0.8  # Use only if enough time


class IntelligentCache:
    """
    Intelligent caching system for computational results.

    Dramatically reduces computational overhead by storing and reusing results.
    """

    def __init__(self, max_cache_size: int = 1000):
        """
        Initialize intelligent cache.

        Args:
            max_cache_size: Maximum number of cached items
        """
        self.cache = {}
        self.cache_stats = {
            'hits': 0,
            'misses': 0,
            'evictions': 0
        }
        self.max_cache_size = max_cache_size
        self.access_times = {}

    def generate_cache_key(self, func_name: str,
                          args: Tuple,
                          kwargs: Dict[str, Any]) -> str:
        """
        Generate cache key from function arguments.

        Args:
            func_name: Name of function
            args: Positional arguments
            kwargs: Keyword arguments

        Returns:
            Cache key
        """
        # Create deterministic string representation
        key_parts = [func_name]

        # Add args
        for arg in args:
            if isinstance(arg, np.ndarray):
                key_parts.append(f"array_{arg.shape}_{arg.mean():.4f}_{arg.std():.4f}")
            elif isinstance(arg, (int, float, str, bool)):
                key_parts.append(str(arg))
            else:
                key_parts.append(f"{type(arg).__name__}_{hash(str(arg)) % 10000}")

        # Add kwargs (sorted for consistency)
        for k in sorted(kwargs.keys()):
            v = kwargs[k]
            if isinstance(v, np.ndarray):
                key_parts.append(f"{k}_array_{v.shape}_{v.mean():.4f}_{v.std():.4f}")
            elif isinstance(v, (int, float, str, bool)):
                key_parts.append(f"{k}_{v}")
            else:
                key_parts.append(f"{k}_{type(v).__name__}_{hash(str(v)) % 10000}")

        key_string = "_".join(key_parts)
        return hashlib.md5(key_string.encode()).hexdigest()

    def get(self, func_name: str,
           args: Tuple = (),
           kwargs: Dict[str, Any] = None) -> Optional[Any]:
        """
        Get cached result if available.

        Args:
            func_name: Name of function
            args: Positional arguments
            kwargs: Keyword arguments

        Returns:
            Cached result or None
        """
        if kwargs is None:
            kwargs = {}

        cache_key = self.generate_cache_key(func_name, args, kwargs)

        if cache_key in self.cache:
            self.cache_stats['hits'] += 1
            self.access_times[cache_key] = time.time()
            return self.cache[cache_key]
        else:
            self.cache_stats['misses'] += 1
            return None

    def set(self, func_name: str,
           result: Any,
           args: Tuple = (),
           kwargs: Dict[str, Any] = None):
        """
        Cache a result.

        Args:
            func_name: Name of function
            result: Result to cache
            args: Positional arguments
            kwargs: Keyword arguments
        """
        if kwargs is None:
            kwargs = {}

        cache_key = self.generate_cache_key(func_name, args, kwargs)

        # Check cache size and evict if necessary
        if len(self.cache) >= self.max_cache_size:
            self._evict_oldest()

        self.cache[cache_key] = result
        self.access_times[cache_key] = time.time()

    def _evict_oldest(self):
        """Evict oldest cached item."""
        if not self.access_times:
            return

        # Find oldest key
        oldest_key = min(self.access_times.items(), key=lambda x: x[1])[0]

        # Remove from cache
        del self.cache[oldest_key]
        del self.access_times[oldest_key]
        self.cache_stats['evictions'] += 1

    def get_cache_stats(self) -> Dict[str, Any]:
        """Get cache statistics."""
        hit_rate = (self.cache_stats['hits'] /
                   (self.cache_stats['hits'] + self.cache_stats['misses'])
                   if (self.cache_stats['hits'] + self.cache_stats['misses']) > 0 else 0)

        return {
            'size': len(self.cache),
            'max_size': self.max_cache_size,
            'hits': self.cache_stats['hits'],
            'misses': self.cache_stats['misses'],
            'evictions': self.cache_stats['evictions'],
            'hit_rate': hit_rate
        }


def cached_function(func):
    """
    Decorator for caching function results.

    Usage:
        @cached_function
        def expensive_function(x, y=1):
            return x * y
    """
    cache = IntelligentCache()

    @wraps(func)
    def wrapper(*args, **kwargs):
        # Try to get from cache
        cached_result = cache.get(func.__name__, args, kwargs)
        if cached_result is not None:
            return cached_result

        # Compute result
        result = func(*args, **kwargs)

        # Cache result
        cache.set(func.__name__, result, args, kwargs)

        return result

    # Add cache access
    wrapper._cache = cache
    return wrapper


class HierarchicalOptimizer:
    """
    Hierarchical optimization that uses coarse-to-fine approach.

    Dramatically reduces computational cost by starting with simple methods
    and only using sophisticated methods when necessary.
    """

    def __init__(self):
        """Initialize hierarchical optimizer."""
        self.optimization_stages = [
            'coarse',
            'medium',
            'fine'
        ]

    def optimize_hierarchical(self,
                             objective: Callable,
                             initial_point: np.ndarray,
                             problem_importance: str = 'medium') -> Dict[str, Any]:
        """
        Perform hierarchical optimization.

        Args:
            objective: Objective function to minimize
            initial_point: Starting point
            problem_importance: Importance level ('low', 'medium', 'high')

        Returns:
            Optimization results
        """
        results = {
            'stages_completed': [],
            'total_time': 0,
            'final_result': None,
            'converged_early': False
        }

        # Determine which stages to run
        if problem_importance == 'low':
            stages_to_run = ['coarse']
        elif problem_importance == 'medium':
            stages_to_run = ['coarse', 'medium']
        else:  # high
            stages_to_run = self.optimization_stages

        current_point = initial_point.copy()
        start_time = time.time()

        for stage in stages_to_run:
            stage_result = self._run_optimization_stage(
                objective, current_point, stage
            )

            results['stages_completed'].append(stage)
            current_point = stage_result['solution']
            results['total_time'] = time.time() - start_time

            # Check if converged well enough
            if stage_result['converged'] and stage != 'fine':
                # Check if solution is good enough
                if stage_result['value'] < 1e-4:  # Good convergence
                    results['converged_early'] = True
                    break

        results['final_result'] = current_point
        results['final_value'] = objective(current_point)
        results['optimization_stages'] = stages_to_run

        return results

    def _run_optimization_stage(self,
                               objective: Callable,
                               initial_point: np.ndarray,
                               stage: str) -> Dict[str, Any]:
        """Run single optimization stage."""
        from scipy.optimize import minimize

        stage_configs = {
            'coarse': {
                'method': 'Nelder-Mead',
                'options': {'maxiter': 50, 'xatol': 1e-2}
            },
            'medium': {
                'method': 'BFGS',
                'options': {'maxiter': 200, 'gtol': 1e-4}
            },
            'fine': {
                'method': 'L-BFGS-B',
                'options': {'maxiter': 500, 'gtol': 1e-8}
            }
        }

        config = stage_configs.get(stage, stage_configs['medium'])

        start_time = time.time()
        result = minimize(
            objective,
            initial_point,
            method=config['method'],
            options=config['options']
        )
        elapsed_time = time.time() - start_time

        return {
            'solution': result.x,
            'value': result.fun,
            'converged': result.success,
            'iterations': result.nit,
            'stage': stage,
            'time': elapsed_time
        }


class AdaptiveResourceManager:
    """
    Main coordinator for adaptive resource management.

    Combines all resource management strategies into unified system.
    """

    def __init__(self):
        """Initialize adaptive resource manager."""
        self.precision_manager = AdaptivePrecisionManager()
        self.resource_monitor = ResourceMonitor()
        self.cache = IntelligentCache()
        self.hierarchical_optimizer = HierarchicalOptimizer()
        self.performance_history = []

    def optimize_with_resources(self,
                               objective: Callable,
                               initial_point: np.ndarray,
                               problem_type: str = 'discovery',
                               time_constraint: Optional[float] = None) -> Dict[str, Any]:
        """
        Perform optimization with intelligent resource management.

        Args:
            objective: Objective function
            initial_point: Starting point
            problem_type: Type of problem
            time_constraint: Optional time constraint

        Returns:
            Optimization results with resource efficiency metrics
        """
        start_time = time.time()
        results = {}

        # Assess problem requirements
        data_complexity = self._assess_data_complexity(initial_point)
        precision_level = self.precision_manager.assess_required_precision(
            problem_type, data_complexity, time_constraint
        )

        # Get appropriate optimization method
        method_config = self.precision_manager.get_optimization_method_for_precision(
            precision_level
        )

        # Check if hierarchical approach is beneficial
        available_resources = self.resource_monitor.get_available_resources()
        use_hierarchical = self.resource_monitor.should_use_advanced_method(
            len(initial_point), time_constraint or 3600
        )

        # Run optimization
        if use_hierarchical and precision_level == 'high':
            # Use hierarchical approach for high-precision problems
            optimization_result = self.hierarchical_optimizer.optimize_hierarchical(
                objective, initial_point, problem_type
            )
            results['optimization_method'] = 'hierarchical'
        else:
            # Use single-stage optimization
            optimization_result = self._run_single_stage_optimization(
                objective, initial_point, method_config
            )
            results['optimization_method'] = 'single_stage'

        elapsed_time = time.time() - start_time

        results.update({
            'precision_level': precision_level,
            'elapsed_time': elapsed_time,
            'resource_usage': available_resources,
            'optimization_result': optimization_result,
            'cache_stats': self.cache.get_cache_stats()
        })

        self.performance_history.append(results)
        return results

    def _assess_data_complexity(self, data: np.ndarray) -> float:
        """Assess complexity of data (0-1 scale)."""
        # Simple complexity metrics
        variance = np.var(data)
        n_dimensions = len(data) if data.ndim == 1 else data.shape[1]

        # Normalize complexity score
        complexity = min((variance * n_dimensions) / 100, 1.0)
        return complexity

    def _run_single_stage_optimization(self,
                                       objective: Callable,
                                       initial_point: np.ndarray,
                                       method_config: Dict[str, Any]) -> Dict[str, Any]:
        """Run single-stage optimization."""
        from scipy.optimize import minimize

        start_time = time.time()
        result = minimize(
            objective,
            initial_point,
            method=method_config['method'],
            tol=method_config['tolerance'],
            options={'maxiter': method_config['max_iterations']}
        )
        elapsed_time = time.time() - start_time

        return {
            'solution': result.x,
            'value': result.fun,
            'converged': result.success,
            'iterations': result.nit,
            'time': elapsed_time,
            'method': method_config['method']
        }

    def get_performance_summary(self) -> Dict[str, Any]:
        """Get summary of performance with resource management."""
        if not self.performance_history:
            return {'message': 'No performance history available'}

        total_time = sum(r['elapsed_time'] for r in self.performance_history)
        cache_hits = self.cache.get_cache_stats()['hits']
        avg_precision_level = np.mean([1 if r.get('precision_level') == 'high' else
                                     0.5 if r.get('precision_level') == 'medium' else
                                     0.25 for r in self.performance_history])

        return {
            'total_optimizations': len(self.performance_history),
            'total_time': total_time,
            'average_time': total_time / len(self.performance_history),
            'cache_hits': cache_hits,
            'average_precision_level': avg_precision_level,
            'resource_efficiency': 'high' if avg_precision_level < 0.7 else 'medium'
        }


# Universal interface for adaptive resource management
def optimize_with_resource_management(objective: Callable,
                                     initial_point: np.ndarray,
                                     problem_type: str = 'discovery',
                                     **kwargs) -> Dict[str, Any]:
    """
    Universal interface for resource-aware optimization.

    Args:
        objective: Objective function to minimize
        initial_point: Starting point
        problem_type: Type of problem
        **kwargs: Additional parameters

    Returns:
        Optimization results with resource efficiency
    """
    manager = AdaptiveResourceManager()
    return manager.optimize_with_resources(
        objective, initial_point, problem_type, **kwargs
    )


if __name__ == "__main__":
    print("Testing Adaptive Resource Management...")

    # Test with sample optimization
    def test_objective(x):
        return np.sum(x**2)

    initial_point = np.random.randn(10)

    result = optimize_with_resource_management(
        test_objective, initial_point, 'discovery'
    )

    print(f"Optimization Method: {result['optimization_method']}")
    print(f"Precision Level: {result['precision_level']}")
    print(f"Elapsed Time: {result['elapsed_time']:.3f}s")
    print(f"Converged: {result['optimization_result']['converged']}")

    print("\n✅ Adaptive resource management system ready!")