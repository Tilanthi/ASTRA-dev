# astra_core/core/thread_safe_timeout.py
import concurrent.futures
import logging
from typing import Any, Callable, TypeVar

logger = logging.getLogger(__name__)

T = TypeVar('T')

def call_with_timeout(func: Callable[..., T], timeout_seconds: float, *args, **kwargs) -> T:
    """
    Execute function with timeout protection - thread-safe implementation

    This replaces signal-based timeout (which only works in main thread) with
    a thread-safe implementation using concurrent.futures.

    Args:
        func: Function to execute
        timeout_seconds: Maximum time to wait for function to complete
        *args: Positional arguments for function
        **kwargs: Keyword arguments for function

    Returns:
        Function result if completed within timeout

    Raises:
        TimeoutError: If function execution exceeds timeout
        Exception: Any exception raised by the function
    """
    with concurrent.futures.ThreadPoolExecutor(max_workers=1) as executor:
        future = executor.submit(func, *args, **kwargs)
        try:
            return future.result(timeout=timeout_seconds)
        except concurrent.futures.TimeoutError:
            # Cancel the future if it's still running
            future.cancel()
            raise TimeoutError(f"Function call timed out after {timeout_seconds}s")
