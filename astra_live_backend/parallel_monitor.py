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
ASTRA Live — Parallel Performance Monitor
Monitoring and automatic fallback for parallel discovery architecture.

This module provides:
1. Performance monitoring for parallel vs sequential operations
2. Automatic fallback triggers based on error rates and performance
3. Health checks for thread safety and resource utilization
4. Metrics collection and reporting
"""
import time
import threading
import logging
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, field
from enum import Enum

logger = logging.getLogger(__name__)


class ParallelMode(Enum):
    """Parallel operation modes."""
    AUTO = "auto"  # Automatically choose between parallel and sequential
    PARALLEL = "parallel"  # Force parallel mode
    SEQUENTIAL = "sequential"  # Force sequential mode (fallback)


@dataclass
class PerformanceMetrics:
    """Performance metrics for parallel operations."""
    total_cycles: int = 0
    parallel_cycles: int = 0
    sequential_cycles: int = 0

    # Data fetching metrics
    total_data_fetch_time: float = 0.0
    parallel_fetch_time: float = 0.0
    sequential_fetch_time: float = 0.0

    # Investigation metrics
    total_investigation_time: float = 0.0
    parallel_investigation_time: float = 0.0
    sequential_investigation_time: float = 0.0

    # Error tracking
    parallel_errors: int = 0
    sequential_errors: int = 0
    total_parallel_operations: int = 0

    # Thread safety monitoring
    lock_contentions: int = 0
    lock_wait_time: float = 0.0

    def compute_fetch_speedup(self) -> float:
        """Compute data fetching speedup (sequential_time / parallel_time)."""
        if self.parallel_fetch_time > 0:
            return self.sequential_fetch_time / self.parallel_fetch_time
        return 1.0

    def compute_investigation_speedup(self) -> float:
        """Compute investigation speedup."""
        if self.parallel_investigation_time > 0:
            return self.sequential_investigation_time / self.parallel_investigation_time
        return 1.0

    def compute_parallel_error_rate(self) -> float:
        """Compute error rate for parallel operations."""
        if self.total_parallel_operations > 0:
            return self.parallel_errors / self.total_parallel_operations
        return 0.0


class ParallelMonitor:
    """
    Monitor parallel performance and trigger fallback when needed.

    Fallback triggers:
    - Parallel error rate > 30%
    - Parallel speedup < 1.2x (not worth the overhead)
    - Lock contention > 50%
    - Resource exhaustion (memory, threads)
    """

    def __init__(self):
        self.metrics = PerformanceMetrics()
        self.mode = ParallelMode.AUTO
        self.fallback_active = False
        self.fallback_reason = ""
        self._lock = threading.Lock()

        # Fallback thresholds
        self.max_error_rate = 0.3  # 30% error rate triggers fallback
        self.min_speedup = 1.2  # Minimum speedup to justify parallel mode
        self.max_lock_contention = 0.5  # 50% lock contention triggers warning

        # Health check intervals
        self.last_health_check = 0.0
        self.health_check_interval = 60.0  # Check every 60 seconds

    def record_fetch_performance(self, parallel_time: float,
                                 sequential_time: float,
                                 source_count: int,
                                 errors: int = 0):
        """Record data fetching performance metrics."""
        with self._lock:
            self.metrics.total_data_fetch_time += (parallel_time + sequential_time) / 2
            self.metrics.parallel_fetch_time += parallel_time
            self.metrics.sequential_fetch_time += sequential_time
            if errors > 0:
                self.metrics.parallel_errors += errors
                self.metrics.total_parallel_operations += 1

    def record_investigation_performance(self, parallel_time: float,
                                        hypothesis_count: int,
                                        errors: int = 0):
        """Record hypothesis investigation performance metrics."""
        with self._lock:
            self.metrics.total_investigation_time += parallel_time
            self.metrics.parallel_investigation_time += parallel_time
            self.metrics.parallel_cycles += 1
            self.metrics.total_cycles += 1
            if errors > 0:
                self.metrics.parallel_errors += errors
                self.metrics.total_parallel_operations += hypothesis_count

    def record_lock_contention(self, wait_time: float):
        """Record lock contention for thread safety monitoring."""
        with self._lock:
            self.metrics.lock_contentions += 1
            self.metrics.lock_wait_time += wait_time

    def should_use_parallel(self) -> bool:
        """
        Decide whether to use parallel mode based on current metrics.

        Returns:
            True if parallel mode is recommended, False if sequential is better
        """
        if self.mode == ParallelMode.SEQUENTIAL:
            return False
        if self.mode == ParallelMode.PARALLEL:
            return True

        # Auto mode: check performance and error rate
        if self.fallback_active:
            return False

        # Check if we have enough data to make a decision
        if self.metrics.total_parallel_operations < 10:
            return True  # Not enough data, default to parallel

        error_rate = self.metrics.compute_parallel_error_rate()
        if error_rate > self.max_error_rate:
            self._trigger_fallback(f"High error rate: {error_rate:.2%}")
            return False

        fetch_speedup = self.metrics.compute_fetch_speedup()
        if fetch_speedup < self.min_speedup and self.metrics.parallel_cycles > 5:
            logger.warning(f"Low fetch speedup ({fetch_speedup:.2f}x), considering fallback")
            # Don't trigger fallback yet, just log warning

        return True

    def _trigger_fallback(self, reason: str):
        """Trigger fallback to sequential mode."""
        self.fallback_active = True
        self.fallback_reason = reason
        logger.warning(f"Parallel monitor: TRIGGERING FALLBACK to sequential mode - {reason}")

    def reset_fallback(self):
        """Reset fallback flag and return to auto mode."""
        self.fallback_active = False
        self.fallback_reason = ""
        logger.info("Parallel monitor: Fallback reset - returning to auto mode")

    def health_check(self) -> Dict[str, Any]:
        """
        Perform health check on parallel subsystem.

        Returns:
            Dict with health status and recommendations
        """
        now = time.time()
        if now - self.last_health_check < self.health_check_interval:
            return {}  # Skip if checked recently

        self.last_health_check = now

        health = {
            'status': 'healthy',
            'timestamp': now,
            'metrics': {},
            'recommendations': [],
        }

        # Check error rate
        error_rate = self.metrics.compute_parallel_error_rate()
        health['metrics']['error_rate'] = error_rate
        if error_rate > self.max_error_rate:
            health['status'] = 'degraded'
            health['recommendations'].append(f"High error rate ({error_rate:.2%}) - reduce parallelism")

        # Check speedup
        fetch_speedup = self.metrics.compute_fetch_speedup()
        inv_speedup = self.metrics.compute_investigation_speedup()
        health['metrics']['fetch_speedup'] = fetch_speedup
        health['metrics']['investigation_speedup'] = inv_speedup

        if fetch_speedup < self.min_speedup and self.metrics.parallel_cycles > 5:
            health['status'] = 'degraded'
            health['recommendations'].append(f"Low fetch speedup ({fetch_speedup:.2f}x) - may not be worth overhead")

        # Check lock contention
        if self.metrics.lock_contentions > 0:
            avg_wait = self.metrics.lock_wait_time / self.metrics.lock_contentions
            health['metrics']['avg_lock_wait'] = avg_wait
            if avg_wait > 0.1:  # 100ms average lock wait
                health['status'] = 'degraded'
                health['recommendations'].append(f"High lock contention ({avg_wait:.3f}s avg wait)")

        # Overall system health
        if health['status'] == 'healthy':
            health['recommendations'].append("Parallel subsystem operating normally")

        return health

    def get_metrics(self) -> Dict[str, Any]:
        """Get current performance metrics."""
        with self._lock:
            return {
                'mode': self.mode.value,
                'fallback_active': self.fallback_active,
                'fallback_reason': self.fallback_reason,
                'total_cycles': self.metrics.total_cycles,
                'parallel_cycles': self.metrics.parallel_cycles,
                'sequential_cycles': self.metrics.sequential_cycles,
                'fetch_speedup': self.metrics.compute_fetch_speedup(),
                'investigation_speedup': self.metrics.compute_investigation_speedup(),
                'parallel_error_rate': self.metrics.compute_parallel_error_rate(),
                'lock_contentions': self.metrics.lock_contentions,
                'avg_lock_wait': (self.metrics.lock_wait_time / max(self.metrics.lock_contentions, 1)),
            }

    def set_mode(self, mode: ParallelMode):
        """Set parallel operation mode."""
        self.mode = mode
        logger.info(f"Parallel mode set to: {mode.value}")


class FallbackController:
    """
    Controller for automatic fallback between parallel and sequential modes.

    This controller monitors system health and performance, automatically
    switching to sequential mode when parallel mode underperforms.
    """

    def __init__(self, monitor: ParallelMonitor):
        self.monitor = monitor
        self._fallback_history: List[Dict] = []

    def check_fallback_conditions(self) -> bool:
        """
        Check if fallback to sequential mode is needed.

        Returns:
            True if fallback should be triggered
        """
        # Check if already in fallback mode
        if self.monitor.fallback_active:
            # Check if conditions have improved
            if self._should_return_to_parallel():
                self.monitor.reset_fallback()
                self._record_fallback_action("returned_to_parallel")
            return False

        # Check if fallback should be triggered
        should_fallback = not self.monitor.should_use_parallel()
        if should_fallback:
            self._record_fallback_action("triggered", reason=self.monitor.fallback_reason)

        return should_fallback

    def _should_return_to_parallel(self) -> bool:
        """Check if conditions have improved enough to return to parallel mode."""
        # Check if error rate has decreased
        error_rate = self.monitor.metrics.compute_parallel_error_rate()
        if error_rate > self.monitor.max_error_rate * 0.5:  # Still high
            return False

        # Check if we've been in fallback long enough
        if not self._fallback_history:
            return True

        last_fallback = self._fallback_history[-1]
        if time.time() - last_fallback.get('timestamp', 0) < 300:  # 5 minutes
            return False

        return True

    def _record_fallback_action(self, action: str, reason: str = ""):
        """Record fallback action in history."""
        self._fallback_history.append({
            'action': action,
            'reason': reason,
            'timestamp': time.time(),
        })
        # Keep only last 100 entries
        if len(self._fallback_history) > 100:
            self._fallback_history = self._fallback_history[-100:]

    def get_fallback_history(self) -> List[Dict]:
        """Get fallback action history."""
        return self._fallback_history.copy()


# Global monitor instance (singleton)
_monitor: Optional[ParallelMonitor] = None
_monitor_lock = threading.Lock()


def get_parallel_monitor() -> ParallelMonitor:
    """Get or create the global parallel monitor."""
    global _monitor
    with _monitor_lock:
        if _monitor is None:
            _monitor = ParallelMonitor()
            logger.info("Created global parallel performance monitor")
        return _monitor


def get_fallback_controller() -> FallbackController:
    """Get or create the global fallback controller."""
    monitor = get_parallel_monitor()
    return FallbackController(monitor)
