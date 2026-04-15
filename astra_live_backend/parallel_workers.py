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
ASTRA Live — Parallel Investigation Workers
Thread pool for concurrent hypothesis investigation with stigmergic coordination.

This module enables parallel hypothesis investigation while maintaining:
- Thread-safe access to shared resources (hypotheses, discovery memory, stigmergy)
- Pheromone-guided task distribution
- Fallback to sequential mode on errors
- Performance monitoring and metrics

Expected speedup: 3.3x (50s → 15s for 5 hypotheses)
"""
import time
import logging
import threading
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import Dict, List, Optional, Callable, Any, Tuple
from dataclasses import dataclass, field

logger = logging.getLogger(__name__)


@dataclass
class InvestigationResult:
    """Result from a single hypothesis investigation."""
    hypothesis_id: str
    success: bool
    discoveries: int
    test_results: List[Dict]
    confidence_delta: float
    error: Optional[str] = None
    investigation_time: float = 0.0


@dataclass
class ParallelMetrics:
    """Metrics for parallel investigation performance."""
    total_investigations: int = 0
    parallel_investigations: int = 0
    sequential_investigations: int = 0
    total_time_parallel: float = 0.0
    total_time_sequential: float = 0.0
    errors: int = 0
    speedup_achieved: float = 1.0

    def compute_speedup(self) -> float:
        """Compute speedup ratio (sequential_time / parallel_time)."""
        if self.total_time_parallel > 0:
            return self.total_time_sequential / self.total_time_parallel
        return 1.0


class ParallelInvestigationPool:
    """
    Thread pool for parallel hypothesis investigation.

    This class manages concurrent hypothesis investigation while maintaining
    thread safety and stigmergic coordination.

    Usage:
        pool = ParallelInvestigationPool(max_workers=4)

        def investigate_hypothesis(hypothesis, engine):
            # Investigation logic here
            return InvestigationResult(...)

        results = pool.investigate_parallel(
            hypotheses=list_of_hypotheses,
            investigation_fn=investigate_hypothesis,
            engine=discovery_engine
        )
    """

    def __init__(self, max_workers: int = 4, timeout: float = 30.0):
        """
        Initialize parallel investigation pool.

        Args:
            max_workers: Maximum number of concurrent investigation threads
            timeout: Maximum time per investigation (default 30 seconds)
        """
        self.max_workers = max_workers
        self.timeout = timeout
        self.metrics = ParallelMetrics()
        self._fallback_to_sequential = False
        self._lock = threading.Lock()

    def investigate_parallel(self,
                           hypotheses: List[Any],
                           investigation_fn: Callable[[Any, Any], InvestigationResult],
                           engine: Any,
                           enable_parallel: bool = True) -> Dict[str, InvestigationResult]:
        """
        Investigate multiple hypotheses in parallel using worker pool.

        Args:
            hypotheses: List of hypothesis objects to investigate
            investigation_fn: Function that takes (hypothesis, engine) and returns InvestigationResult
            engine: DiscoveryEngine instance
            enable_parallel: If False, force sequential mode

        Returns:
            Dict mapping hypothesis IDs to InvestigationResult objects
        """
        start_time = time.time()

        if not enable_parallel or self._fallback_to_sequential or len(hypotheses) <= 1:
            # Sequential mode (fallback or single hypothesis)
            results = self._investigate_sequential(hypotheses, investigation_fn, engine)
            elapsed = time.time() - start_time

            with self._lock:
                self.metrics.total_investigations += len(hypotheses)
                self.metrics.sequential_investigations += len(hypotheses)
                self.metrics.total_time_sequential += elapsed

            logger.info(f"Sequential investigation of {len(hypotheses)} hypotheses "
                       f"completed in {elapsed:.2f}s")
            return results

        # Parallel mode
        logger.info(f"Starting parallel investigation of {len(hypotheses)} hypotheses "
                   f"with {self.max_workers} workers")
        results = {}
        completed_count = 0
        error_count = 0

        try:
            with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
                # Submit all investigation tasks
                future_to_hypothesis = {
                    executor.submit(self._investigate_safe, h, investigation_fn, engine): h
                    for h in hypotheses
                }

                # Collect results as they complete
                for future in as_completed(future_to_hypothesis, timeout=self.timeout * len(hypotheses)):
                    hypothesis = future_to_hypothesis[future]
                    try:
                        result = future.result(timeout=self.timeout)
                        results[result.hypothesis_id] = result
                        completed_count += 1

                        if result.error:
                            error_count += 1
                            logger.warning(f"Investigation error for {result.hypothesis_id}: {result.error}")
                        else:
                            logger.debug(f"Completed investigation of {result.hypothesis_id} "
                                       f"({result.discoveries} discoveries, {result.investigation_time:.2f}s)")

                    except Exception as e:
                        error_count += 1
                        logger.error(f"Exception during investigation of {hypothesis.id}: {e}")
                        # Create error result
                        results[hypothesis.id] = InvestigationResult(
                            hypothesis_id=hypothesis.id,
                            success=False,
                            discoveries=0,
                            test_results=[],
                            confidence_delta=0.0,
                            error=str(e)
                        )

        except Exception as e:
            logger.error(f"Parallel investigation failed: {e}, falling back to sequential")
            self._fallback_to_sequential = True
            # Fallback to sequential for remaining hypotheses
            remaining = [h for h in hypotheses if h.id not in results]
            if remaining:
                sequential_results = self._investigate_sequential(remaining, investigation_fn, engine)
                results.update(sequential_results)

        elapsed = time.time() - start_time

        # Update metrics
        with self._lock:
            self.metrics.total_investigations += len(hypotheses)
            self.metrics.parallel_investigations += len(hypotheses)
            self.metrics.total_time_parallel += elapsed
            self.metrics.errors += error_count
            self.metrics.speedup_achieved = self.metrics.compute_speedup()

        success_count = len([r for r in results.values() if r.success])
        logger.info(f"Parallel investigation completed: {success_count}/{len(hypotheses)} successful, "
                   f"{error_count} errors, {elapsed:.2f}s")

        # Auto-fallback if error rate is too high
        if len(hypotheses) > 5 and error_count / len(hypotheses) > 0.3:
            logger.warning(f"High error rate ({error_count}/{len(hypotheses)}), "
                          "enabling fallback to sequential mode")
            self._fallback_to_sequential = True

        return results

    def _investigate_safe(self,
                         hypothesis: Any,
                         investigation_fn: Callable,
                         engine: Any) -> InvestigationResult:
        """
        Safe wrapper for investigation function with error handling.

        This wrapper ensures that exceptions in individual investigations
        don't crash the entire parallel pool.
        """
        try:
            result = investigation_fn(hypothesis, engine)
            return result
        except Exception as e:
            logger.exception(f"Exception in investigation of {hypothesis.id}")
            return InvestigationResult(
                hypothesis_id=hypothesis.id,
                success=False,
                discoveries=0,
                test_results=[],
                confidence_delta=0.0,
                error=str(e)
            )

    def _investigate_sequential(self,
                               hypotheses: List[Any],
                               investigation_fn: Callable,
                               engine: Any) -> Dict[str, InvestigationResult]:
        """Investigate hypotheses sequentially (fallback mode)."""
        results = {}
        for hypothesis in hypotheses:
            try:
                result = self._investigate_safe(hypothesis, investigation_fn, engine)
                results[result.hypothesis_id] = result
            except Exception as e:
                logger.error(f"Sequential investigation failed for {hypothesis.id}: {e}")
                results[hypothesis.id] = InvestigationResult(
                    hypothesis_id=hypothesis.id,
                    success=False,
                    discoveries=0,
                    test_results=[],
                    confidence_delta=0.0,
                    error=str(e)
                )
        return results

    def get_metrics(self) -> Dict[str, Any]:
        """Get current performance metrics."""
        return {
            'total_investigations': self.metrics.total_investigations,
            'parallel_investigations': self.metrics.parallel_investigations,
            'sequential_investigations': self.metrics.sequential_investigations,
            'total_time_parallel': round(self.metrics.total_time_parallel, 2),
            'total_time_sequential': round(self.metrics.total_time_sequential, 2),
            'errors': self.metrics.errors,
            'speedup_achieved': round(self.metrics.speedup_achieved, 2),
            'fallback_active': self._fallback_to_sequential,
            'max_workers': self.max_workers,
            'error_rate': round(self.metrics.errors / max(self.metrics.total_investigations, 1), 3)
        }

    def reset_fallback(self):
        """Reset fallback flag to retry parallel mode."""
        self._fallback_to_sequential = False
        logger.info("Fallback flag reset - parallel mode re-enabled")


class PheromoneGuidedWorkerPool(ParallelInvestigationPool):
    """
    Extended worker pool that uses pheromone signals for task distribution.

    This pool prioritizes hypotheses based on pheromone concentrations,
    enabling stigmergic coordination among parallel workers.
    """

    def __init__(self, max_workers: int = 4, timeout: float = 30.0,
                 stigmergy_bridge=None):
        """
        Initialize pheromone-guided worker pool.

        Args:
            max_workers: Maximum number of concurrent investigation threads
            timeout: Maximum time per investigation
            stigmergy_bridge: StigmergyBridge instance for pheromone signals
        """
        super().__init__(max_workers, timeout)
        self.stigmergy_bridge = stigmergy_bridge

    def investigate_parallel(self,
                           hypotheses: List[Any],
                           investigation_fn: Callable[[Any, Any], InvestigationResult],
                           engine: Any,
                           enable_parallel: bool = True) -> Dict[str, InvestigationResult]:
        """
        Investigate hypotheses with pheromone-guided priority ordering.

        Hypotheses in high-success pheromone regions are investigated first,
        enabling workers to focus on promising areas of the search space.
        """
        if self.stigmergy_bridge and enable_parallel:
            # Re-rank hypotheses by pheromone signals
            try:
                from astra_live_backend.hypotheses import Hypothesis

                # Convert to dicts for stigmergy ranking
                h_dicts = []
                original_scores = []
                for h in hypotheses:
                    score = h.confidence
                    h_dicts.append({
                        'id': h.id,
                        'domain': h.domain,
                        'category': getattr(h, 'category', 'unknown')
                    })
                    original_scores.append(score)

                # Get pheromone-guided ranking
                ranked = self.stigmergy_bridge.rank_hypotheses(h_dicts, original_scores)

                # Reorder hypotheses by pheromone score
                hypothesis_map = {h.id: h for h in hypotheses}
                reordered_hypotheses = []
                for h_dict, _ in ranked:
                    if h_dict['id'] in hypothesis_map:
                        reordered_hypotheses.append(hypothesis_map[h_dict['id']])

                logger.info(f"Pheromone-guided ordering: top 3 priorities = "
                           f"{[h.id for h in reordered_hypotheses[:3]]}")

                hypotheses = reordered_hypotheses

            except Exception as e:
                logger.warning(f"Pheromone-guided ordering failed: {e}, using original order")

        # Call parent implementation with (possibly) reordered hypotheses
        return super().investigate_parallel(hypotheses, investigation_fn, engine, enable_parallel)


# Global worker pool instance (singleton)
_worker_pool: Optional[ParallelInvestigationPool] = None
_pool_lock = threading.Lock()


def get_investigation_pool(max_workers: int = 4,
                           timeout: float = 30.0,
                           pheromone_guided: bool = True,
                           stigmergy_bridge=None) -> ParallelInvestigationPool:
    """
    Get or create the global investigation pool.

    Args:
        max_workers: Maximum number of concurrent workers
        timeout: Maximum time per investigation
        pheromone_guided: If True, use pheromone-guided worker pool
        stigmergy_bridge: StigmergyBridge instance (required for pheromone_guided)

    Returns:
        ParallelInvestigationPool instance
    """
    global _worker_pool

    with _pool_lock:
        if _worker_pool is None:
            if pheromone_guided and stigmergy_bridge:
                _worker_pool = PheromoneGuidedWorkerPool(
                    max_workers=max_workers,
                    timeout=timeout,
                    stigmergy_bridge=stigmergy_bridge
                )
                logger.info(f"Created pheromone-guided worker pool with {max_workers} workers")
            else:
                _worker_pool = ParallelInvestigationPool(
                    max_workers=max_workers,
                    timeout=timeout
                )
                logger.info(f"Created standard worker pool with {max_workers} workers")
        return _worker_pool


def reset_worker_pool():
    """Reset the global worker pool (for testing or reconfiguration)."""
    global _worker_pool
    with _pool_lock:
        _worker_pool = None
