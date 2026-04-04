"""
Tool Integration: External APIs and Computation Tools

Provides access to external knowledge sources and computation capabilities:
- Wikipedia API for factual context (free, unlimited)
- arXiv API for research/academic questions (free, unlimited)
- MathTool for symbolic computation (SymPy-based)
- Python executor for safe numerical computation

Expected gain: +5-8% accuracy

Date: 2025-12-10
Version: 38.0
"""

import re
import json
import urllib.request
import urllib.parse
import urllib.error
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, field
import xml.etree.ElementTree as ET
import math


@dataclass
class ToolResult:
    """Result from a tool query"""
    tool: str
    query: str
    success: bool
    result: Any
    confidence: float
    source_url: Optional[str] = None
    error_message: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)

    def __str__(self):
        if self.success:
            result_preview = str(self.result)[:100] + "..." if len(str(self.result)) > 100 else str(self.result)
            return f"ToolResult({self.tool}: {result_preview}, confidence={self.confidence:.2f})"
        return f"ToolResult({self.tool}: FAILED - {self.error_message})"


class WikipediaAPI:
    """
    Wikipedia API for factual context.

    Free, unlimited - always query for factual context.
    Uses the Wikipedia REST API v1.
    """

    BASE_URL = "https://en.wikipedia.org/api/rest_v1"
    SEARCH_URL = "https://en.wikipedia.org/w/api.php"

    def __init__(self, timeout: int = 10):
        self.timeout = timeout

    def query(self, question: str) -> ToolResult:
        """
        Query Wikipedia for relevant content.

        Args:
            question: The question or search query

        Returns:
            ToolResult with summary and source URL
        """
        try:
            # Extract key terms from question
            search_terms = self._extract_search_terms(question)

            # Search Wikipedia
            search_results = self._search(search_terms)

            if not search_results:
                return ToolResult(
                    tool="wikipedia",
                    query=question,
                    success=False,
                    result=None,
                    confidence=0.0,
                    error_message="No relevant Wikipedia articles found"
                )

            # Get summary of top result
            top_title = search_results[0]
            summary = self._get_summary(top_title)

            if summary:
                return ToolResult(
                    tool="wikipedia",
                    query=question,
                    success=True,
                    result=summary['extract'],
                    confidence=0.8,
                    source_url=f"https://en.wikipedia.org/wiki/{urllib.parse.quote(top_title)}",
                    metadata={
                        'title': summary.get('title', top_title),
                        'pageid': summary.get('pageid'),
                        'search_results': search_results[:5]
                    }
                )
            else:
                return ToolResult(
                    tool="wikipedia",
                    query=question,
                    success=False,
                    result=None,
                    confidence=0.0,
                    error_message="Failed to retrieve article summary"
                )

        except Exception as e:
            return ToolResult(
                tool="wikipedia",
                query=question,
                success=False,
                result=None,
                confidence=0.0,
                error_message=str(e)
            )

    def _extract_search_terms(self, question: str) -> str:
        """Extract key search terms from question"""
        # Remove common question words
        stop_words = {'what', 'is', 'are', 'how', 'why', 'when', 'where', 'who',
                     'the', 'a', 'an', 'of', 'in', 'to', 'for', 'does', 'do',
                     'can', 'could', 'would', 'should', 'explain', 'describe'}

        words = question.lower().split()
        key_words = [w for w in words if w not in stop_words and len(w) > 2]

        return ' '.join(key_words[:5])

    def _search(self, query: str) -> List[str]:
        """Search Wikipedia for articles"""
        params = {
            'action': 'opensearch',
            'search': query,
            'limit': 5,
            'namespace': 0,
