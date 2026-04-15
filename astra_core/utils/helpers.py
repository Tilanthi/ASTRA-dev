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
