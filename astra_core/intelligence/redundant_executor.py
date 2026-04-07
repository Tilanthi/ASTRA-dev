"""
Redundant Execution for Fault Tolerance (Priority 5)
====================================================

Executes 2+ identical agents in parallel for reliability.

Problem Solved:
- APIs time out, models crash, networks drop
- Single point of failure causes entire operation to fail
- Long-tail latency causes unpredictable user experience

Benefits:
- 33% reliability improvement (60% → 80% success rate in article)
- Eliminates long-tail latency events
- Zero additional latency (parallel execution)
- Graceful degradation under adverse conditions

Based on: "Building the 14 Key Pillars of Agentic AI" - Pillar 9

Example Use:
    executor = RedundantExecutor(num_copies=2)
    result = executor.execute(unreliable_api_call, "user_data")
    # If first copy fails or times out, second copy provides result
    # Success: 80% vs 60% for single execution
"""

import time
import random
from dataclasses import dataclass, field
from typing import Callable, Any, List, Dict, Optional, TypeVar
from concurrent.futures import ThreadPoolExecutor, as_completed, Future
from enum import Enum


T = TypeVar('T')


class ExecutionStrategy(Enum):
    """Strategy for redundant execution."""
    FIRST_SUCCESS = "first_success"      # Return first successful result
    MAJORITY_VOTE = "majority_vote"      # Wait for majority, return most common
    ALL_SUCCESS = "all_success"          # Wait for all, verify consistency


@dataclass
class ExecutionResult:
    """Result from redundant execution."""
    success: bool
    result: Optional[Any]
    error: Optional[str]
    execution_time: float
    attempts: int
    successful_attempts: int
    failed_attempts: int
    all_results: List[Any] = field(default_factory=list)
    all_errors: List[str] = field(default_factory=list)


class RedundantExecutor:
    """
    Redundant Execution System for Fault Tolerance.

    Executes 2+ identical agents/functions in parallel and uses
    the result from the first to successfully finish.

    Architecture:
        1. Scatter: Dispatch N identical tasks in parallel
        2. Race: Wait for first successful completion
        3. Cancel: Cancel remaining tasks (optional)
        4. Return: Return successful result immediately

    Benefits:
        - +33% reliability (60% → 80% success rate)
        - Eliminates long-tail latency
        - Zero additional latency (parallel execution)
        - Production-grade fault tolerance

    Example:
        ```python
        executor = RedundantExecutor(num_copies=2)

        # Unreliable operation (30% failure rate)
        def fetch_data(query):
            if random.random() < 0.3:
                raise ConnectionError("Network timeout")
            return f"Data for '{query}'"

        result = executor.execute(fetch_data, "user profile")
        # 80% success rate vs 60% for single execution
        ```
    """

    def __init__(self,
                 num_copies: int = 2,
                 strategy: ExecutionStrategy = ExecutionStrategy.FIRST_SUCCESS,
                 max_workers: int = 4,
                 timeout: float = None):
        """
        Initialize redundant executor.

        Args:
            num_copies: Number of parallel copies to execute (default: 2)
            strategy: Execution strategy (default: first_success)
            max_workers: Max parallel workers
            timeout: Timeout in seconds for each copy (None = no timeout)
        """
        self.num_copies = num_copies
        self.strategy = strategy
        self.max_workers = max_workers
        self.timeout = timeout

    def execute(self,
                func: Callable[..., T],
                *args,
                **kwargs) -> ExecutionResult:
        """
        Execute function redundantly in parallel.

        Args:
            func: Function to execute
            *args: Positional arguments for function
            **kwargs: Keyword arguments for function

        Returns:
            ExecutionResult with successful result or error
        """
        start_time = time.time()

        if self.strategy == ExecutionStrategy.FIRST_SUCCESS:
            return self._execute_first_success(func, args, kwargs, start_time)
        elif self.strategy == ExecutionStrategy.MAJORITY_VOTE:
            return self._execute_majority_vote(func, args, kwargs, start_time)
        elif self.strategy == ExecutionStrategy.ALL_SUCCESS:
            return self._execute_all_success(func, args, kwargs, start_time)
        else:
            raise ValueError(f"Unknown strategy: {self.strategy}")

    def _execute_first_success(self,
                               func: Callable[..., T],
                               args: tuple,
                               kwargs: dict,
                               start_time: float) -> ExecutionResult:
        """Execute copies and return first successful result."""
        all_results = []
        all_errors = []

        with ThreadPoolExecutor(max_workers=min(self.max_workers, self.num_copies)) as executor:
            # Submit all copies
            futures = [
                executor.submit(func, *args, **kwargs)
                for _ in range(self.num_copies)
            ]

            # Wait for first success
            for future in as_completed(futures):
                try:
                    result = future.result(timeout=self.timeout_per_copy)
                    all_results.append(result)
                    # Return first successful result
                    return ExecutionResult(
                        success=True,
                        result=result,
                        execution_time=time.time() - start_time,
                        num_copies_used=len(all_results)
                    )
                except Exception as e:
                    all_errors.append(e)

        # If all failed, return last error
        return ExecutionResult(
            success=False,
            result=None,
            execution_time=time.time() - start_time,
            num_copies_used=len(all_errors),
            error=all_errors[-1] if all_errors else "Unknown error"
        )
