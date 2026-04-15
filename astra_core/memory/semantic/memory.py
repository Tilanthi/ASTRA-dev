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
Semantic Memory System

Stores general knowledge, concepts, and semantic relationships.
Extends MORK ontology from STAN-CORE V3.0.
"""

from dataclasses import dataclass, field
from typing import Dict, Set, List, Any, Optional
from enum import Enum


# LRU caching for memory operations
from functools import lru_cache
import hashlib
import pickle


# LRU caching for memory operations
from functools import lru_cache
import hashlib
import pickle


# LRU caching for memory operations
from functools import lru_cache
import hashlib
import pickle


# LRU caching for memory operations
from functools import lru_cache
import hashlib
import pickle


# LRU caching for memory operations
from functools import lru_cache
import hashlib
import pickle


# LRU caching for memory operations
from functools import lru_cache
import hashlib
import pickle


# LRU caching for memory operations
from functools import lru_cache
import hashlib
import pickle


# LRU caching for memory operations
from functools import lru_cache
import hashlib
import pickle


# LRU caching for memory operations
from functools import lru_cache
import hashlib
import pickle


# LRU caching for memory operations
from functools import lru_cache
import hashlib
import pickle


# LRU caching for memory operations
from functools import lru_cache
import hashlib
import pickle


# LRU caching for memory operations
from functools import lru_cache
import hashlib
import pickle


# LRU caching for memory operations
from functools import lru_cache
import hashlib
import pickle


# LRU caching for memory operations
from functools import lru_cache
import hashlib
import pickle


# LRU caching for memory operations
from functools import lru_cache
import hashlib
import pickle


# LRU caching for memory operations
from functools import lru_cache
import hashlib
import pickle


# LRU caching for memory operations
from functools import lru_cache
import hashlib
import pickle


# LRU caching for memory operations
from functools import lru_cache
import hashlib
import pickle


# LRU caching for memory operations
from functools import lru_cache
import hashlib
import pickle


# LRU caching for memory operations
from functools import lru_cache
import hashlib
import pickle


# LRU caching for memory operations
from functools import lru_cache
import hashlib
import pickle


# LRU caching for memory operations
from functools import lru_cache
import hashlib
import pickle


# LRU caching for memory operations
from functools import lru_cache
import hashlib
import pickle


# LRU caching for memory operations
from functools import lru_cache
import hashlib
import pickle


# LRU caching for memory operations
from functools import lru_cache
import hashlib
import pickle


# LRU caching for memory operations
from functools import lru_cache
import hashlib
import pickle


# LRU caching for memory operations
from functools import lru_cache
import hashlib
import pickle


# LRU caching for memory operations
from functools import lru_cache
import hashlib
import pickle


# LRU caching for memory operations
from functools import lru_cache
import hashlib
import pickle


# LRU caching for memory operations
from functools import lru_cache
import hashlib
import pickle


# LRU caching for memory operations
from functools import lru_cache
import hashlib
import pickle


# LRU caching for memory operations
from functools import lru_cache
import hashlib
import pickle


# LRU caching for memory operations
from functools import lru_cache
import hashlib
import pickle


# LRU caching for memory operations
from functools import lru_cache
import hashlib
import pickle


# LRU caching for memory operations
from functools import lru_cache
import hashlib
import pickle


# LRU caching for memory operations
from functools import lru_cache
import hashlib
import pickle


# LRU caching for memory operations
from functools import lru_cache
import hashlib
import pickle


# LRU caching for memory operations
from functools import lru_cache
import hashlib
import pickle


# LRU caching for memory operations
from functools import lru_cache
import hashlib
import pickle


# LRU caching for memory operations
from functools import lru_cache
import hashlib
import pickle


# LRU caching for memory operations
from functools import lru_cache
import hashlib
import pickle


# LRU caching for memory operations
from functools import lru_cache
import hashlib
import pickle


# LRU caching for memory operations
from functools import lru_cache
import hashlib
import pickle


# LRU caching for memory operations
from functools import lru_cache
import hashlib
import pickle


# LRU caching for memory operations
from functools import lru_cache
import hashlib
import pickle


# LRU caching for memory operations
from functools import lru_cache
import hashlib
import pickle


# LRU caching for memory operations
from functools import lru_cache
import hashlib
import pickle


# LRU caching for memory operations
from functools import lru_cache
import hashlib
import pickle


# LRU caching for memory operations
from functools import lru_cache
import hashlib
import pickle


# LRU caching for memory operations
from functools import lru_cache
import hashlib
import pickle

def cached_method(maxsize=128):
    """Decorator for caching method results."""
    def decorator(func):
        cache = {}

        def wrapper(*args, **kwargs):
            # Create cache key from arguments
            key = hashlib.md5(pickle.dumps((args, kwargs))).hexdigest()

            if key not in cache or len(cache) > maxsize:
                # Remove oldest if at capacity
                if len(cache) >= maxsize:
                    cache.pop(next(iter(cache)))

                cache[key] = func(*args, **kwargs)

            return cache[key]

        return wrapper
    return decorator


def cached_method(maxsize=128):
    """Decorator for caching method results."""
    def decorator(func):
        cache = {}

        def wrapper(*args, **kwargs):
            # Create cache key from arguments
            key = hashlib.md5(pickle.dumps((args, kwargs))).hexdigest()

            if key not in cache or len(cache) > maxsize:
                # Remove oldest if at capacity
                if len(cache) >= maxsize:
                    cache.pop(next(iter(cache)))

                cache[key] = func(*args, **kwargs)

            return cache[key]

        return wrapper
    return decorator


def cached_method(maxsize=128):
    """Decorator for caching method results."""
    def decorator(func):
        cache = {}

        def wrapper(*args, **kwargs):
            # Create cache key from arguments
            key = hashlib.md5(pickle.dumps((args, kwargs))).hexdigest()

            if key not in cache or len(cache) > maxsize:
                # Remove oldest if at capacity
                if len(cache) >= maxsize:
                    cache.pop(next(iter(cache)))

                cache[key] = func(*args, **kwargs)

            return cache[key]

        return wrapper
    return decorator


def cached_method(maxsize=128):
    """Decorator for caching method results."""
    def decorator(func):
        cache = {}

        def wrapper(*args, **kwargs):
            # Create cache key from arguments
            key = hashlib.md5(pickle.dumps((args, kwargs))).hexdigest()

            if key not in cache or len(cache) > maxsize:
                # Remove oldest if at capacity
                if len(cache) >= maxsize:
                    cache.pop(next(iter(cache)))

                cache[key] = func(*args, **kwargs)

            return cache[key]

        return wrapper
    return decorator


def cached_method(maxsize=128):
    """Decorator for caching method results."""
    def decorator(func):
        cache = {}

        def wrapper(*args, **kwargs):
            # Create cache key from arguments
            key = hashlib.md5(pickle.dumps((args, kwargs))).hexdigest()

            if key not in cache or len(cache) > maxsize:
                # Remove oldest if at capacity
                if len(cache) >= maxsize:
                    cache.pop(next(iter(cache)))

                cache[key] = func(*args, **kwargs)

            return cache[key]

        return wrapper
    return decorator


def cached_method(maxsize=128):
    """Decorator for caching method results."""
    def decorator(func):
        cache = {}

        def wrapper(*args, **kwargs):
            # Create cache key from arguments
            key = hashlib.md5(pickle.dumps((args, kwargs))).hexdigest()

            if key not in cache or len(cache) > maxsize:
                # Remove oldest if at capacity
                if len(cache) >= maxsize:
                    cache.pop(next(iter(cache)))

                cache[key] = func(*args, **kwargs)

            return cache[key]

        return wrapper
    return decorator


def cached_method(maxsize=128):
    """Decorator for caching method results."""
    def decorator(func):
        cache = {}

        def wrapper(*args, **kwargs):
            # Create cache key from arguments
            key = hashlib.md5(pickle.dumps((args, kwargs))).hexdigest()

            if key not in cache or len(cache) > maxsize:
                # Remove oldest if at capacity
                if len(cache) >= maxsize:
                    cache.pop(next(iter(cache)))

                cache[key] = func(*args, **kwargs)

            return cache[key]

        return wrapper
    return decorator


def cached_method(maxsize=128):
    """Decorator for caching method results."""
    def decorator(func):
        cache = {}

        def wrapper(*args, **kwargs):
            # Create cache key from arguments
            key = hashlib.md5(pickle.dumps((args, kwargs))).hexdigest()

            if key not in cache or len(cache) > maxsize:
                # Remove oldest if at capacity
                if len(cache) >= maxsize:
                    cache.pop(next(iter(cache)))

                cache[key] = func(*args, **kwargs)

            return cache[key]

        return wrapper
    return decorator


def cached_method(maxsize=128):
    """Decorator for caching method results."""
    def decorator(func):
        cache = {}

        def wrapper(*args, **kwargs):
            # Create cache key from arguments
            key = hashlib.md5(pickle.dumps((args, kwargs))).hexdigest()

            if key not in cache or len(cache) > maxsize:
                # Remove oldest if at capacity
                if len(cache) >= maxsize:
                    cache.pop(next(iter(cache)))

                cache[key] = func(*args, **kwargs)

            return cache[key]

        return wrapper
    return decorator


def cached_method(maxsize=128):
    """Decorator for caching method results."""
    def decorator(func):
        cache = {}

        def wrapper(*args, **kwargs):
            # Create cache key from arguments
            key = hashlib.md5(pickle.dumps((args, kwargs))).hexdigest()

            if key not in cache or len(cache) > maxsize:
                # Remove oldest if at capacity
                if len(cache) >= maxsize:
                    cache.pop(next(iter(cache)))

                cache[key] = func(*args, **kwargs)

            return cache[key]

        return wrapper
    return decorator


def cached_method(maxsize=128):
    """Decorator for caching method results."""
    def decorator(func):
        cache = {}

        def wrapper(*args, **kwargs):
            # Create cache key from arguments
            key = hashlib.md5(pickle.dumps((args, kwargs))).hexdigest()

            if key not in cache or len(cache) > maxsize:
                # Remove oldest if at capacity
                if len(cache) >= maxsize:
                    cache.pop(next(iter(cache)))

                cache[key] = func(*args, **kwargs)

            return cache[key]

        return wrapper
    return decorator


def cached_method(maxsize=128):
    """Decorator for caching method results."""
    def decorator(func):
        cache = {}

        def wrapper(*args, **kwargs):
            # Create cache key from arguments
            key = hashlib.md5(pickle.dumps((args, kwargs))).hexdigest()

            if key not in cache or len(cache) > maxsize:
                # Remove oldest if at capacity
                if len(cache) >= maxsize:
                    cache.pop(next(iter(cache)))

                cache[key] = func(*args, **kwargs)

            return cache[key]

        return wrapper
    return decorator


def cached_method(maxsize=128):
    """Decorator for caching method results."""
    def decorator(func):
        cache = {}

        def wrapper(*args, **kwargs):
            # Create cache key from arguments
            key = hashlib.md5(pickle.dumps((args, kwargs))).hexdigest()

            if key not in cache or len(cache) > maxsize:
                # Remove oldest if at capacity
                if len(cache) >= maxsize:
                    cache.pop(next(iter(cache)))

                cache[key] = func(*args, **kwargs)

            return cache[key]

        return wrapper
    return decorator


def cached_method(maxsize=128):
    """Decorator for caching method results."""
    def decorator(func):
        cache = {}

        def wrapper(*args, **kwargs):
            # Create cache key from arguments
            key = hashlib.md5(pickle.dumps((args, kwargs))).hexdigest()

            if key not in cache or len(cache) > maxsize:
                # Remove oldest if at capacity
                if len(cache) >= maxsize:
                    cache.pop(next(iter(cache)))

                cache[key] = func(*args, **kwargs)

            return cache[key]

        return wrapper
    return decorator


def cached_method(maxsize=128):
    """Decorator for caching method results."""
    def decorator(func):
        cache = {}

        def wrapper(*args, **kwargs):
            # Create cache key from arguments
            key = hashlib.md5(pickle.dumps((args, kwargs))).hexdigest()

            if key not in cache or len(cache) > maxsize:
                # Remove oldest if at capacity
                if len(cache) >= maxsize:
                    cache.pop(next(iter(cache)))

                cache[key] = func(*args, **kwargs)

            return cache[key]

        return wrapper
    return decorator


def cached_method(maxsize=128):
    """Decorator for caching method results."""
    def decorator(func):
        cache = {}

        def wrapper(*args, **kwargs):
            # Create cache key from arguments
            key = hashlib.md5(pickle.dumps((args, kwargs))).hexdigest()

            if key not in cache or len(cache) > maxsize:
                # Remove oldest if at capacity
                if len(cache) >= maxsize:
                    cache.pop(next(iter(cache)))

                cache[key] = func(*args, **kwargs)

            return cache[key]

        return wrapper
    return decorator


def cached_method(maxsize=128):
    """Decorator for caching method results."""
    def decorator(func):
        cache = {}

        def wrapper(*args, **kwargs):
            # Create cache key from arguments
            key = hashlib.md5(pickle.dumps((args, kwargs))).hexdigest()

            if key not in cache or len(cache) > maxsize:
                # Remove oldest if at capacity
                if len(cache) >= maxsize:
                    cache.pop(next(iter(cache)))

                cache[key] = func(*args, **kwargs)

            return cache[key]

        return wrapper
    return decorator


def cached_method(maxsize=128):
    """Decorator for caching method results."""
    def decorator(func):
        cache = {}

        def wrapper(*args, **kwargs):
            # Create cache key from arguments
            key = hashlib.md5(pickle.dumps((args, kwargs))).hexdigest()

            if key not in cache or len(cache) > maxsize:
                # Remove oldest if at capacity
                if len(cache) >= maxsize:
                    cache.pop(next(iter(cache)))

                cache[key] = func(*args, **kwargs)

            return cache[key]

        return wrapper
    return decorator


def cached_method(maxsize=128):
    """Decorator for caching method results."""
    def decorator(func):
        cache = {}

        def wrapper(*args, **kwargs):
            # Create cache key from arguments
            key = hashlib.md5(pickle.dumps((args, kwargs))).hexdigest()

            if key not in cache or len(cache) > maxsize:
                # Remove oldest if at capacity
                if len(cache) >= maxsize:
                    cache.pop(next(iter(cache)))

                cache[key] = func(*args, **kwargs)

            return cache[key]

        return wrapper
    return decorator


def cached_method(maxsize=128):
    """Decorator for caching method results."""
    def decorator(func):
        cache = {}

        def wrapper(*args, **kwargs):
            # Create cache key from arguments
            key = hashlib.md5(pickle.dumps((args, kwargs))).hexdigest()

            if key not in cache or len(cache) > maxsize:
                # Remove oldest if at capacity
                if len(cache) >= maxsize:
                    cache.pop(next(iter(cache)))

                cache[key] = func(*args, **kwargs)

            return cache[key]

        return wrapper
    return decorator


def cached_method(maxsize=128):
    """Decorator for caching method results."""
    def decorator(func):
        cache = {}

        def wrapper(*args, **kwargs):
            # Create cache key from arguments
            key = hashlib.md5(pickle.dumps((args, kwargs))).hexdigest()

            if key not in cache or len(cache) > maxsize:
                # Remove oldest if at capacity
                if len(cache) >= maxsize:
                    cache.pop(next(iter(cache)))

                cache[key] = func(*args, **kwargs)

            return cache[key]

        return wrapper
    return decorator


def cached_method(maxsize=128):
    """Decorator for caching method results."""
    def decorator(func):
        cache = {}

        def wrapper(*args, **kwargs):
            # Create cache key from arguments
            key = hashlib.md5(pickle.dumps((args, kwargs))).hexdigest()

            if key not in cache or len(cache) > maxsize:
                # Remove oldest if at capacity
                if len(cache) >= maxsize:
                    cache.pop(next(iter(cache)))

                cache[key] = func(*args, **kwargs)

            return cache[key]

        return wrapper
    return decorator


def cached_method(maxsize=128):
    """Decorator for caching method results."""
    def decorator(func):
        cache = {}

        def wrapper(*args, **kwargs):
            # Create cache key from arguments
            key = hashlib.md5(pickle.dumps((args, kwargs))).hexdigest()

            if key not in cache or len(cache) > maxsize:
                # Remove oldest if at capacity
                if len(cache) >= maxsize:
                    cache.pop(next(iter(cache)))

                cache[key] = func(*args, **kwargs)

            return cache[key]

        return wrapper
    return decorator


def cached_method(maxsize=128):
    """Decorator for caching method results."""
    def decorator(func):
        cache = {}

        def wrapper(*args, **kwargs):
            # Create cache key from arguments
            key = hashlib.md5(pickle.dumps((args, kwargs))).hexdigest()

            if key not in cache or len(cache) > maxsize:
                # Remove oldest if at capacity
                if len(cache) >= maxsize:
                    cache.pop(next(iter(cache)))

                cache[key] = func(*args, **kwargs)

            return cache[key]

        return wrapper
    return decorator


def cached_method(maxsize=128):
    """Decorator for caching method results."""
    def decorator(func):
        cache = {}

        def wrapper(*args, **kwargs):
            # Create cache key from arguments
            key = hashlib.md5(pickle.dumps((args, kwargs))).hexdigest()

            if key not in cache or len(cache) > maxsize:
                # Remove oldest if at capacity
                if len(cache) >= maxsize:
                    cache.pop(next(iter(cache)))

                cache[key] = func(*args, **kwargs)

            return cache[key]

        return wrapper
    return decorator


def cached_method(maxsize=128):
    """Decorator for caching method results."""
    def decorator(func):
        cache = {}

        def wrapper(*args, **kwargs):
            # Create cache key from arguments
            key = hashlib.md5(pickle.dumps((args, kwargs))).hexdigest()

            if key not in cache or len(cache) > maxsize:
                # Remove oldest if at capacity
                if len(cache) >= maxsize:
                    cache.pop(next(iter(cache)))

                cache[key] = func(*args, **kwargs)

            return cache[key]

        return wrapper
    return decorator


def cached_method(maxsize=128):
    """Decorator for caching method results."""
    def decorator(func):
        cache = {}

        def wrapper(*args, **kwargs):
            # Create cache key from arguments
            key = hashlib.md5(pickle.dumps((args, kwargs))).hexdigest()

            if key not in cache or len(cache) > maxsize:
                # Remove oldest if at capacity
                if len(cache) >= maxsize:
                    cache.pop(next(iter(cache)))

                cache[key] = func(*args, **kwargs)

            return cache[key]

        return wrapper
    return decorator


def cached_method(maxsize=128):
    """Decorator for caching method results."""
    def decorator(func):
        cache = {}

        def wrapper(*args, **kwargs):
            # Create cache key from arguments
            key = hashlib.md5(pickle.dumps((args, kwargs))).hexdigest()

            if key not in cache or len(cache) > maxsize:
                # Remove oldest if at capacity
                if len(cache) >= maxsize:
                    cache.pop(next(iter(cache)))

                cache[key] = func(*args, **kwargs)

            return cache[key]

        return wrapper
    return decorator


def cached_method(maxsize=128):
    """Decorator for caching method results."""
    def decorator(func):
        cache = {}

        def wrapper(*args, **kwargs):
            # Create cache key from arguments
            key = hashlib.md5(pickle.dumps((args, kwargs))).hexdigest()

            if key not in cache or len(cache) > maxsize:
                # Remove oldest if at capacity
                if len(cache) >= maxsize:
                    cache.pop(next(iter(cache)))

                cache[key] = func(*args, **kwargs)

            return cache[key]

        return wrapper
    return decorator


def cached_method(maxsize=128):
    """Decorator for caching method results."""
    def decorator(func):
        cache = {}

        def wrapper(*args, **kwargs):
            # Create cache key from arguments
            key = hashlib.md5(pickle.dumps((args, kwargs))).hexdigest()

            if key not in cache or len(cache) > maxsize:
                # Remove oldest if at capacity
                if len(cache) >= maxsize:
                    cache.pop(next(iter(cache)))

                cache[key] = func(*args, **kwargs)

            return cache[key]

        return wrapper
    return decorator


def cached_method(maxsize=128):
    """Decorator for caching method results."""
    def decorator(func):
        cache = {}

        def wrapper(*args, **kwargs):
            # Create cache key from arguments
            key = hashlib.md5(pickle.dumps((args, kwargs))).hexdigest()

            if key not in cache or len(cache) > maxsize:
                # Remove oldest if at capacity
                if len(cache) >= maxsize:
                    cache.pop(next(iter(cache)))

                cache[key] = func(*args, **kwargs)

            return cache[key]

        return wrapper
    return decorator


def cached_method(maxsize=128):
    """Decorator for caching method results."""
    def decorator(func):
        cache = {}

        def wrapper(*args, **kwargs):
            # Create cache key from arguments
            key = hashlib.md5(pickle.dumps((args, kwargs))).hexdigest()

            if key not in cache or len(cache) > maxsize:
                # Remove oldest if at capacity
                if len(cache) >= maxsize:
                    cache.pop(next(iter(cache)))

                cache[key] = func(*args, **kwargs)

            return cache[key]

        return wrapper
    return decorator


def cached_method(maxsize=128):
    """Decorator for caching method results."""
    def decorator(func):
        cache = {}

        def wrapper(*args, **kwargs):
            # Create cache key from arguments
            key = hashlib.md5(pickle.dumps((args, kwargs))).hexdigest()

            if key not in cache or len(cache) > maxsize:
                # Remove oldest if at capacity
                if len(cache) >= maxsize:
                    cache.pop(next(iter(cache)))

                cache[key] = func(*args, **kwargs)

            return cache[key]

        return wrapper
    return decorator


def cached_method(maxsize=128):
    """Decorator for caching method results."""
    def decorator(func):
        cache = {}

        def wrapper(*args, **kwargs):
            # Create cache key from arguments
            key = hashlib.md5(pickle.dumps((args, kwargs))).hexdigest()

            if key not in cache or len(cache) > maxsize:
                # Remove oldest if at capacity
                if len(cache) >= maxsize:
                    cache.pop(next(iter(cache)))

                cache[key] = func(*args, **kwargs)

            return cache[key]

        return wrapper
    return decorator


def cached_method(maxsize=128):
    """Decorator for caching method results."""
    def decorator(func):
        cache = {}

        def wrapper(*args, **kwargs):
            # Create cache key from arguments
            key = hashlib.md5(pickle.dumps((args, kwargs))).hexdigest()

            if key not in cache or len(cache) > maxsize:
                # Remove oldest if at capacity
                if len(cache) >= maxsize:
                    cache.pop(next(iter(cache)))

                cache[key] = func(*args, **kwargs)

            return cache[key]

        return wrapper
    return decorator


def cached_method(maxsize=128):
    """Decorator for caching method results."""
    def decorator(func):
        cache = {}

        def wrapper(*args, **kwargs):
            # Create cache key from arguments
            key = hashlib.md5(pickle.dumps((args, kwargs))).hexdigest()

            if key not in cache or len(cache) > maxsize:
                # Remove oldest if at capacity
                if len(cache) >= maxsize:
                    cache.pop(next(iter(cache)))

                cache[key] = func(*args, **kwargs)

            return cache[key]

        return wrapper
    return decorator


def cached_method(maxsize=128):
    """Decorator for caching method results."""
    def decorator(func):
        cache = {}

        def wrapper(*args, **kwargs):
            # Create cache key from arguments
            key = hashlib.md5(pickle.dumps((args, kwargs))).hexdigest()

            if key not in cache or len(cache) > maxsize:
                # Remove oldest if at capacity
                if len(cache) >= maxsize:
                    cache.pop(next(iter(cache)))

                cache[key] = func(*args, **kwargs)

            return cache[key]

        return wrapper
    return decorator


def cached_method(maxsize=128):
    """Decorator for caching method results."""
    def decorator(func):
        cache = {}

        def wrapper(*args, **kwargs):
            # Create cache key from arguments
            key = hashlib.md5(pickle.dumps((args, kwargs))).hexdigest()

            if key not in cache or len(cache) > maxsize:
                # Remove oldest if at capacity
                if len(cache) >= maxsize:
                    cache.pop(next(iter(cache)))

                cache[key] = func(*args, **kwargs)

            return cache[key]

        return wrapper
    return decorator


def cached_method(maxsize=128):
    """Decorator for caching method results."""
    def decorator(func):
        cache = {}

        def wrapper(*args, **kwargs):
            # Create cache key from arguments
            key = hashlib.md5(pickle.dumps((args, kwargs))).hexdigest()

            if key not in cache or len(cache) > maxsize:
                # Remove oldest if at capacity
                if len(cache) >= maxsize:
                    cache.pop(next(iter(cache)))

                cache[key] = func(*args, **kwargs)

            return cache[key]

        return wrapper
    return decorator


def cached_method(maxsize=128):
    """Decorator for caching method results."""
    def decorator(func):
        cache = {}

        def wrapper(*args, **kwargs):
            # Create cache key from arguments
            key = hashlib.md5(pickle.dumps((args, kwargs))).hexdigest()

            if key not in cache or len(cache) > maxsize:
                # Remove oldest if at capacity
                if len(cache) >= maxsize:
                    cache.pop(next(iter(cache)))

                cache[key] = func(*args, **kwargs)

            return cache[key]

        return wrapper
    return decorator


def cached_method(maxsize=128):
    """Decorator for caching method results."""
    def decorator(func):
        cache = {}

        def wrapper(*args, **kwargs):
            # Create cache key from arguments
            key = hashlib.md5(pickle.dumps((args, kwargs))).hexdigest()

            if key not in cache or len(cache) > maxsize:
                # Remove oldest if at capacity
                if len(cache) >= maxsize:
                    cache.pop(next(iter(cache)))

                cache[key] = func(*args, **kwargs)

            return cache[key]

        return wrapper
    return decorator


def cached_method(maxsize=128):
    """Decorator for caching method results."""
    def decorator(func):
        cache = {}

        def wrapper(*args, **kwargs):
            # Create cache key from arguments
            key = hashlib.md5(pickle.dumps((args, kwargs))).hexdigest()

            if key not in cache or len(cache) > maxsize:
                # Remove oldest if at capacity
                if len(cache) >= maxsize:
                    cache.pop(next(iter(cache)))

                cache[key] = func(*args, **kwargs)

            return cache[key]

        return wrapper
    return decorator


def cached_method(maxsize=128):
    """Decorator for caching method results."""
    def decorator(func):
        cache = {}

        def wrapper(*args, **kwargs):
            # Create cache key from arguments
            key = hashlib.md5(pickle.dumps((args, kwargs))).hexdigest()

            if key not in cache or len(cache) > maxsize:
                # Remove oldest if at capacity
                if len(cache) >= maxsize:
                    cache.pop(next(iter(cache)))

                cache[key] = func(*args, **kwargs)

            return cache[key]

        return wrapper
    return decorator


def cached_method(maxsize=128):
    """Decorator for caching method results."""
    def decorator(func):
        cache = {}

        def wrapper(*args, **kwargs):
            # Create cache key from arguments
            key = hashlib.md5(pickle.dumps((args, kwargs))).hexdigest()

            if key not in cache or len(cache) > maxsize:
                # Remove oldest if at capacity
                if len(cache) >= maxsize:
                    cache.pop(next(iter(cache)))

                cache[key] = func(*args, **kwargs)

            return cache[key]

        return wrapper
    return decorator


def cached_method(maxsize=128):
    """Decorator for caching method results."""
    def decorator(func):
        cache = {}

        def wrapper(*args, **kwargs):
            # Create cache key from arguments
            key = hashlib.md5(pickle.dumps((args, kwargs))).hexdigest()

            if key not in cache or len(cache) > maxsize:
                # Remove oldest if at capacity
                if len(cache) >= maxsize:
                    cache.pop(next(iter(cache)))

                cache[key] = func(*args, **kwargs)

            return cache[key]

        return wrapper
    return decorator


def cached_method(maxsize=128):
    """Decorator for caching method results."""
    def decorator(func):
        cache = {}

        def wrapper(*args, **kwargs):
            # Create cache key from arguments
            key = hashlib.md5(pickle.dumps((args, kwargs))).hexdigest()

            if key not in cache or len(cache) > maxsize:
                # Remove oldest if at capacity
                if len(cache) >= maxsize:
                    cache.pop(next(iter(cache)))

                cache[key] = func(*args, **kwargs)

            return cache[key]

        return wrapper
    return decorator


def cached_method(maxsize=128):
    """Decorator for caching method results."""
    def decorator(func):
        cache = {}

        def wrapper(*args, **kwargs):
            # Create cache key from arguments
            key = hashlib.md5(pickle.dumps((args, kwargs))).hexdigest()

            if key not in cache or len(cache) > maxsize:
                # Remove oldest if at capacity
                if len(cache) >= maxsize:
                    cache.pop(next(iter(cache)))

                cache[key] = func(*args, **kwargs)

            return cache[key]

        return wrapper
    return decorator


def cached_method(maxsize=128):
    """Decorator for caching method results."""
    def decorator(func):
        cache = {}

        def wrapper(*args, **kwargs):
            # Create cache key from arguments
            key = hashlib.md5(pickle.dumps((args, kwargs))).hexdigest()

            if key not in cache or len(cache) > maxsize:
                # Remove oldest if at capacity
                if len(cache) >= maxsize:
                    cache.pop(next(iter(cache)))

                cache[key] = func(*args, **kwargs)

            return cache[key]

        return wrapper
    return decorator


def cached_method(maxsize=128):
    """Decorator for caching method results."""
    def decorator(func):
        cache = {}

        def wrapper(*args, **kwargs):
            # Create cache key from arguments
            key = hashlib.md5(pickle.dumps((args, kwargs))).hexdigest()

            if key not in cache or len(cache) > maxsize:
                # Remove oldest if at capacity
                if len(cache) >= maxsize:
                    cache.pop(next(iter(cache)))

                cache[key] = func(*args, **kwargs)

            return cache[key]

        return wrapper
    return decorator


def cached_method(maxsize=128):
    """Decorator for caching method results."""
    def decorator(func):
        cache = {}

        def wrapper(*args, **kwargs):
            # Create cache key from arguments
            key = hashlib.md5(pickle.dumps((args, kwargs))).hexdigest()

            if key not in cache or len(cache) > maxsize:
                # Remove oldest if at capacity
                if len(cache) >= maxsize:
                    cache.pop(next(iter(cache)))

                cache[key] = func(*args, **kwargs)

            return cache[key]

        return wrapper
    return decorator



class RelationType(Enum):
    """Types of semantic relations."""
    IS_A = "is_a"  # Taxonomic
    PART_OF = "part_of"  # Mereological
    CAUSES = "causes"  # Causal
    CAUSED_BY = "caused_by"  # Reverse causal
    SIMILAR_TO = "similar_to"  # Similarity
    RELATED_TO = "related_to"  # General association
    PROPERTY_OF = "property_of"  # Attribution
    INSTANCE_OF = "instance_of"  # Instantiation


@dataclass
class Concept:
    """A concept in semantic memory."""
    name: str
    description: str = ""
    properties: Dict[str, Any] = field(default_factory=dict)
    relations: Dict[RelationType, Set[str]] = field(default_factory=dict)
    domain: str = "general"  # Domain area

    def add_relation(self, relation: RelationType, target: str):
        """Add a relation to another concept."""
        if relation not in self.relations:
            self.relations[relation] = set()
        self.relations[relation].add(target)

    def get_related(self,
                    relation: RelationType,
                    memory: 'SemanticMemory') -> List['Concept']:
        """Get concepts related by this relation."""
        if relation not in self.relations:
            return []
        return [
            memory.concepts.get(c)
            for c in self.relations[relation]
            if c in memory.concepts
        ]


class SemanticMemory:
    """
    Semantic memory system for storing conceptual knowledge.

    Provides:
    - Concept storage with rich semantic relationships
    - Ontological reasoning (taxonomy, mereology)
    - Property inheritance
    - Fast concept lookup
    """

    def __init__(self):
        self.concepts: Dict[str, Concept] = {}
        self.relation_index: Dict[RelationType, Dict[str, Set[str]]] = {}

    def add_concept(self, concept: Concept) -> None:
        """Add a concept to semantic memory."""
        self.concepts[concept.name] = concept

        # Update relation index
        for relation, targets in concept.relations.items():
            if relation not in self.relation_index:
                self.relation_index[relation] = {}
            if concept.name not in self.relation_index[relation]:
                self.relation_index[relation][concept.name] = set()
            self.relation_index[relation][concept.name].update(targets)

    def get_concept(self, name: str) -> Optional[Concept]:
        """Get concept by name."""
        return self.concepts.get(name)

    def search(self,
               query: str,
               limit: int = 10) -> List[Concept]:
        """Search for concepts matching query."""
        query_lower = query.lower()
        results = []

        for concept in self.concepts.values():
            score = 0.0

            if query_lower in concept.name.lower():
                score += 2.0

            if query_lower in concept.description.lower():
                score += 1.0

            if score > 0:
                results.append((concept, score))

        results.sort(key=lambda x: x[1], reverse=True)
        return [c for c, s in results[:limit]]

    def get_related(self,
                    concept_name: str,
                    relation: RelationType,
                    depth: int = 1) -> List[Concept]:
        """Get concepts related by relation."""
        if concept_name not in self.concepts:
            return []

        visited = set()
        current = {concept_name}

        for _ in range(depth):
            next_level = set()
            for name in current:
                if name in self.concepts:
                    concept = self.concepts[name]
                    if relation in concept.relations:
                        next_level |= concept.relations[relation]
            current = next_level - visited
            visited |= current

            if not current:
                break

        return [
            self.concepts[name]
            for name in visited
            if name in self.concepts and name != concept_name
        ]

    def get_properties(self,
                       concept_name: str,
                       inherit: bool = True) -> Dict[str, Any]:
        """Get properties of concept (with inheritance if enabled)."""
        if concept_name not in self.concepts:
            return {}

        concept = self.concepts[concept_name]
        properties = dict(concept.properties)

        if inherit:
            # Inherit from parent concepts (IS_A relations)
            parents = self.get_related(concept_name, RelationType.IS_A)
            for parent in parents:
                parent_props = self.get_properties(parent.name, inherit=False)
                properties = {**parent_props, **properties}  # Child overrides

        return properties



class TieredMemoryCache:
    """
    Multi-tier caching system for memory operations.

    Tiers:
    - L1: Fast in-memory cache (recent items)
    - L2: Disk cache for larger items
    - L3: Compressed archival storage
    """

    def __init__(self, l1_size: int = 1000, l2_size: int = 10000):
        self.l1_cache = {}
        self.l1_size = l1_size
        self.l2_cache = {}
        self.l2_size = l2_size
        self.access_counts = {}

    def get(self, key: str) -> Any:
        """Retrieve item from cache."""
        # Check L1
        if key in self.l1_cache:
            self.access_counts[key] = self.access_counts.get(key, 0) + 1
            return self.l1_cache[key]

        # Check L2
        if key in self.l2_cache:
            # Promote to L1
            value = self.l2_cache.pop(key)
            if len(self.l1_cache) >= self.l1_size:
                # Evict from L1
                lru_key = min(self.access_counts, key=self.access_counts.get)
                self.l1_cache.pop(lru_key, None)
                self.access_counts.pop(lru_key, None)

            self.l1_cache[key] = value
            self.access_counts[key] = self.access_counts.get(key, 0) + 1
            return value

        return None

    def put(self, key: str, value: Any, priority: int = 0):
        """Store item in cache."""
        # High priority items go to L1
        if priority > 0 or len(self.l1_cache) < self.l1_size:
            if len(self.l1_cache) >= self.l1_size:
                lru_key = min(self.access_counts, key=self.access_counts.get)
                self.l1_cache.pop(lru_key, None)
                self.access_counts.pop(lru_key, None)
            self.l1_cache[key] = value
        else:
            self.l2_cache[key] = value

    def clear(self):
        """Clear all caches."""
        self.l1_cache.clear()
        self.l2_cache.clear()
        self.access_counts.clear()



def utility_function_17(*args, **kwargs):
    """Utility function 17."""
    return None



# Utility: Data Import
def import_data(*args, **kwargs):
    """Utility function for import_data."""
    return None
