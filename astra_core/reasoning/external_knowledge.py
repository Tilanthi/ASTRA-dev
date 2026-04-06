"""
External Knowledge Sources Integration for STAN V40

Provides integration with:
- Wolfram Alpha for mathematical computation and knowledge
- arXiv for scientific literature
- Wikipedia for general knowledge
- PubMed for biomedical literature
- NASA ADS for astronomy literature

Date: 2025-12-11
Version: 40.0
"""

import os
import re
import json
import time
import hashlib
import urllib.parse
import urllib.request
from typing import Dict, List, Optional, Any, Tuple, Union
from dataclasses import dataclass, field
from enum import Enum
from abc import ABC, abstractmethod
from datetime import datetime
import xml.etree.ElementTree as ET

# Try to import optional dependencies
try:
    import requests
    REQUESTS_AVAILABLE = True
except ImportError:
    REQUESTS_AVAILABLE = False

try:
    import wolframalpha
    WOLFRAM_AVAILABLE = True
except ImportError:
    WOLFRAM_AVAILABLE = False


class KnowledgeSourceType(Enum):
    """Types of external knowledge sources"""
    WOLFRAM_ALPHA = "wolfram_alpha"
    ARXIV = "arxiv"
    WIKIPEDIA = "wikipedia"
    PUBMED = "pubmed"
    NASA_ADS = "nasa_ads"
    SEMANTIC_SCHOLAR = "semantic_scholar"


@dataclass
class KnowledgeQuery:
    """A query to external knowledge sources"""
    query: str
    source_type: KnowledgeSourceType
    max_results: int = 5
    filters: Dict[str, Any] = field(default_factory=dict)
    timeout: float = 30.0


@dataclass
class KnowledgeResult:
    """Result from an external knowledge source"""
    source: KnowledgeSourceType
    query: str
    success: bool
    content: str
    structured_data: Dict[str, Any] = field(default_factory=dict)
    references: List[str] = field(default_factory=list)
    confidence: float = 0.0
    latency_ms: float = 0.0
    cached: bool = False
    error: Optional[str] = None


@dataclass
class WolframResult:
    """Structured result from Wolfram Alpha"""
    input_interpretation: str = ""
    result: str = ""
    step_by_step: List[str] = field(default_factory=list)
    plots: List[str] = field(default_factory=list)
    related_info: Dict[str, str] = field(default_factory=dict)
    assumptions: List[str] = field(default_factory=list)


@dataclass
class ArxivPaper:
    """An arXiv paper"""
    arxiv_id: str
    title: str
    authors: List[str]
    abstract: str
    categories: List[str]
    published: str
    updated: str
    pdf_url: str
    relevance_score: float = 0.0


@dataclass
class PubMedArticle:
    """A PubMed article"""
    pmid: str
    title: str
    authors: List[str]
    abstract: str
    journal: str
    pub_date: str
    doi: Optional[str] = None
    keywords: List[str] = field(default_factory=list)


class KnowledgeCache:
    """Cache for external knowledge queries"""

    def __init__(self, max_size: int = 500, ttl_seconds: int = 3600):
        self.cache: Dict[str, Tuple[KnowledgeResult, float]] = {}
        self.max_size = max_size
        self.ttl = ttl_seconds

    def _hash_query(self, query: KnowledgeQuery) -> str:
        key = f"{query.source_type.value}|{query.query}|{json.dumps(query.filters, sort_keys=True)}"
        return hashlib.sha256(key.encode()).hexdigest()[:16]

    def get(self, query: KnowledgeQuery) -> Optional[KnowledgeResult]:
        key = self._hash_query(query)
        if key in self.cache:
            result, timestamp = self.cache[key]
            if time.time() - timestamp < self.ttl:
                result.cached = True
                return result
            else:
                del self.cache[key]
        return None

    def put(self, query: KnowledgeQuery, result: KnowledgeResult):
        if len(self.cache) >= self.max_size:
            # Remove oldest entries
            oldest = min(self.cache.items(), key=lambda x: x[1][1])
            del self.cache[oldest[0]]
        key = self._hash_query(query)
        self.cache[key] = (result, time.time())


class WolframAlphaClient:
    """
    Client for Wolfram Alpha API.

    Handles mathematical computations, scientific queries,
    and step-by-step solutions.
    """

    def __init__(self, app_id: Optional[str] = None):
        self.app_id = app_id or os.environ.get("WOLFRAM_APP_ID")
        self.base_url = "http://api.wolframalpha.com/v2/query"

        if WOLFRAM_AVAILABLE and self.app_id:
            self.client = wolframalpha.Client(self.app_id)
        else:
            self.client = None

    def query(self, query_str: str, include_step_by_step: bool = True) -> WolframResult:
        """
        Query Wolfram Alpha.

        Args:
            query_str: The query (e.g., "solve x^2 - 4 = 0")
            include_step_by_step: Whether to include step-by-step solution

        Returns:
            WolframResult with computation results
        """
        if self.client:
            return self._query_api(query_str, include_step_by_step)
