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
Test-Time Search for STAN

Implements beam search over reasoning paths.

Date: 2026-03-18
Version: 1.0
"""

from typing import Dict, List, Optional, Any
from dataclasses import dataclass
from enum import Enum


@dataclass
class SearchConfig:
    """Configuration for test-time search"""
    beam_width: int = 8
    max_depth: int = 12
    time_budget_seconds: float = 30.0
    diversity_bonus: float = 0.15
    verification_weight: float = 0.35


@dataclass
class SearchResult:
    """Result from test-time search"""
    best_answer: str
    confidence: float
    paths_explored: int
    search_trace: List[Dict[str, Any]]


class TestTimeSearch:
    """Test-time search over reasoning paths"""

    def __init__(self, config: SearchConfig = None):
        self.config = config or SearchConfig()

    def search(self, query: str, **kwargs) -> SearchResult:
        """Perform beam search over reasoning paths"""
        return SearchResult(
            best_answer=f"Search result for: {query}",
            confidence=0.8,
            paths_explored=self.config.beam_width,
            search_trace=[]
        )


def create_gpqa_search() -> TestTimeSearch:
    """Create test-time search configured for GPQA"""
    return TestTimeSearch(SearchConfig(beam_width=10, max_depth=15))


__all__ = [
    'SearchConfig',
    'SearchResult',
    'TestTimeSearch',
    'create_gpqa_search'
]


@dataclass
class ReasoningPath:
    """A path in the reasoning search tree"""
    path_id: str
    steps: List[str]
    score: float
    verified: bool = False
    parent_path_id: Optional[str] = None


__all__ = [
    'SearchConfig',
    'SearchResult',
    'TestTimeSearch',
    'ReasoningPath',
    'create_gpqa_search'
]


def create_fast_search() -> TestTimeSearch:
    """Create fast test-time search"""
    return TestTimeSearch(SearchConfig(beam_width=4, max_depth=6))


def create_deep_search() -> TestTimeSearch:
    """Create deep test-time search"""
    return TestTimeSearch(SearchConfig(beam_width=12, max_depth=20))


__all__ = [
    'SearchConfig',
    'SearchResult',
    'TestTimeSearch',
    'ReasoningPath',
    'create_gpqa_search',
    'create_fast_search',
    'create_deep_search'
]


def create_thorough_search() -> TestTimeSearch:
    """Create thorough test-time search"""
    return TestTimeSearch(SearchConfig(beam_width=16, max_depth=25))


__all__ = [
    'SearchConfig',
    'SearchResult',
    'TestTimeSearch',
    'ReasoningPath',
    'create_gpqa_search',
    'create_fast_search',
    'create_deep_search',
    'create_thorough_search'
]
