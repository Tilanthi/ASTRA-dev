"""
Helper utilities
"""

import time
from typing import Callable, Any
from functools import wraps


def progress_bar(iterable, desc: str = ""):
    """Simple progress bar."""
    n = len(iterable)
    for i, item in enumerate(iterable):
        yield item
        if (i + 1) % max(1, n // 10) == 0 or i == n - 1:
            print(f"\r{desc} [{i+1}/{n}]", end="", flush=True)
    print()


def timing(func: Callable) -> Callable:
    """Timing decorator."""
    @wraps(func)
    def wrapper(*args, **kwargs):
        start = time.time()
        result = func(*args, **kwargs)
        end = time.time()
        print(f"{func.__name__} took {end - start:.2f}s")
        return result
    return wrapper
