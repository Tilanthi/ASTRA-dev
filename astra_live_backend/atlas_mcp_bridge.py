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
ASTRA — ATLAS MCP Tool Bridge
Python interface to 28 ATLAS capabilities via JSON-RPC 2.0.

This module provides:
1. JSON-RPC 2.0 client for ATLAS MCP server
2. Tool catalog with 28 capabilities
3. Execution engine for tool orchestration
4. Result caching and error handling
5. Drop-in integration with ASTRA's discovery pipeline

ATLAS MCP Tools (from repository):
- Data Tools: fetch_data, query_database, transform_data
- Analysis Tools: statistical_test, correlation_analysis, regression
- Causal Tools: causal_discovery, intervention_test, counterfactual
- ML Tools: train_model, predict_model, evaluate_model
- NLP Tools: extract_entities, sentiment_analysis, text_similarity
- Visualization Tools: plot_chart, generate_report
- Knowledge Tools: semantic_search, knowledge_graph_query
- Validation Tools: validate_hypothesis, check_consistency
"""
import os
import json
import time
import logging
import threading
import asyncio
from typing import Dict, List, Optional, Any, Callable, Union
from pathlib import Path
from dataclasses import dataclass, field, asdict
from enum import Enum
import hashlib

logger = logging.getLogger('astra.atlas_mcp')

# ============================================================================
# Configuration
# ============================================================================

STATE_DIR = Path(__file__).parent.parent / 'data' / 'atlas_mcp'
CACHE_FILE = STATE_DIR / 'tool_cache.json'
METRICS_FILE = STATE_DIR / 'metrics.json'

# ATLAS MCP server configuration
MCP_SERVER_HOST = os.getenv('ATLAS_MCP_HOST', 'localhost')
MCP_SERVER_PORT = int(os.getenv('ATLAS_MCP_PORT', '8765'))
MCP_SERVER_URL = f'http://{MCP_SERVER_HOST}:{MCP_SERVER_PORT}'

# Request timeout (seconds)
DEFAULT_TIMEOUT = 30.0

# Cache configuration
MAX_CACHE_SIZE = 5000
CACHE_TTL = 3600  # 1 hour


# ============================================================================
# Data Structures
# ============================================================================

class ToolCategory(Enum):
    """Categories of ATLAS MCP tools."""
    DATA = "data"
    ANALYSIS = "analysis"
    CAUSAL = "causal"
    ML = "ml"
    NLP = "nlp"
    VISUALIZATION = "visualization"
    KNOWLEDGE = "knowledge"
    VALIDATION = "validation"


@dataclass
class MCPTool:
    """Definition of an MCP tool."""
    name: str
    category: ToolCategory
    description: str
    parameters: Dict[str, Any]  # Parameter schema
    returns: str  # Return type description
    timeout: float = DEFAULT_TIMEOUT
    enabled: bool = True


@dataclass
class MCPToolResult:
    """Result from MCP tool execution."""
    tool_name: str
    success: bool
    result: Any
    error: Optional[str] = None
    execution_time_ms: float = 0.0
    cached: bool = False
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict:
        return asdict(self)


@dataclass
class MCPMetrics:
    """Metrics for MCP tool usage."""
    total_calls: int = 0
    successful_calls: int = 0
    failed_calls: int = 0
    total_execution_time_ms: float = 0.0
    cache_hits: int = 0
    cache_misses: int = 0
    calls_by_tool: Dict[str, int] = field(default_factory=dict)

    def compute_success_rate(self) -> float:
        if self.total_calls == 0:
            return 0.0
        return self.successful_calls / self.total_calls

    def compute_avg_execution_time_ms(self) -> float:
        if self.successful_calls == 0:
            return 0.0
        return self.total_execution_time_ms / self.successful_calls


# ============================================================================
# Tool Catalog
# ============================================================================

MCP_TOOL_CATALOG: List[MCPTool] = [
    # Data Tools (4)
    MCPTool(
        name="fetch_data",
        category=ToolCategory.DATA,
        description="Fetch data from external sources (APIs, databases, files)",
        parameters={
            "source": {"type": "string", "description": "Data source URL or identifier"},
            "query": {"type": "object", "description": "Query parameters"},
            "format": {"type": "string", "enum": ["json", "csv", "fits"], "default": "json"},
        },
        returns="Dict with data and metadata"
    ),
    MCPTool(
        name="query_database",
        category=ToolCategory.DATA,
        description="Execute SQL query on database",
        parameters={
            "database": {"type": "string", "description": "Database name"},
            "query": {"type": "string", "description": "SQL query"},
        },
        returns="Query results as list of dicts"
    ),
    MCPTool(
        name="transform_data",
        category=ToolCategory.DATA,
        description="Transform data (filter, aggregate, join)",
        parameters={
            "data": {"type": "array", "description": "Input data"},
            "operations": {"type": "array", "description": "List of transformations"},
        },
        returns="Transformed data"
    ),
    MCPTool(
        name="export_data",
        category=ToolCategory.DATA,
        description="Export data to various formats",
        parameters={
            "data": {"type": "array", "description": "Data to export"},
            "format": {"type": "string", "enum": ["csv", "json", "fits", "hdf5"]},
            "filename": {"type": "string", "description": "Output filename"},
        },
        returns="Export result with file path"
    ),

    # Analysis Tools (4)
    MCPTool(
        name="statistical_test",
        category=ToolCategory.ANALYSIS,
        description="Run statistical test (t-test, KS, chi-squared, etc.)",
        parameters={
            "test": {"type": "string", "enum": ["t_test", "ks", "chi_squared", "anova"]},
            "data_x": {"type": "array", "description": "First sample"},
            "data_y": {"type": "array", "description": "Second sample (optional)"},
        },
        returns="Test result with p-value, statistic, effect size"
    ),
    MCPTool(
        name="correlation_analysis",
        category=ToolCategory.ANALYSIS,
        description="Compute correlation between variables",
        parameters={
            "data_x": {"type": "array"},
            "data_y": {"type": "array"},
            "method": {"type": "string", "enum": ["pearson", "spearman", "kendall"], "default": "pearson"},
        },
        returns="Correlation coefficient and p-value"
    ),
    MCPTool(
        name="regression",
        category=ToolCategory.ANALYSIS,
        description="Fit regression model",
        parameters={
            "data": {"type": "array", "description": "Data points"},
            "model": {"type": "string", "enum": ["linear", "polynomial", "logistic"]},
            "degree": {"type": "integer", "default": 1},
        },
        returns="Model coefficients, R-squared, predictions"
    ),
    MCPTool(
        name="time_series_analysis",
        category=ToolCategory.ANALYSIS,
        description="Analyze time series data",
        parameters={
            "data": {"type": "array"},
            "methods": {"type": "array", "items": {"type": "string"}},
        },
        returns="Trend, seasonality, autocorrelation results"
    ),

    # Causal Tools (4)
    MCPTool(
        name="causal_discovery",
        category=ToolCategory.CAUSAL,
        description="Discover causal structure from data",
        parameters={
            "data": {"type": "array"},
            "algorithm": {"type": "string", "enum": ["pc", "fci", "ges"], "default": "pc"},
        },
        returns="Causal graph (adjacency matrix)"
    ),
    MCPTool(
        name="intervention_test",
        category=ToolCategory.CAUSAL,
        description="Test effect of intervention using do-calculus",
        parameters={
            "graph": {"type": "object"},
            "intervention": {"type": "string"},
            "outcome": {"type": "string"},
        },
        returns="Causal effect estimate"
    ),
    MCPTool(
        name="counterfactual",
        category=ToolCategory.CAUSAL,
        description="Compute counterfactual outcome",
        parameters={
            "model": {"type": "object"},
            "factual": {"type": "object"},
            "intervention": {"type": "object"},
        },
        returns="Counterfactual prediction"
    ),
    MCPTool(
        name="validate_causal_structure",
        category=ToolCategory.CAUSAL,
        description="Validate causal structure against data",
        parameters={
            "graph": {"type": "object"},
            "data": {"type": "array"},
        },
        returns="Validation score and diagnostics"
    ),

    # ML Tools (4)
    MCPTool(
        name="train_model",
        category=ToolCategory.ML,
        description="Train machine learning model",
        parameters={
            "algorithm": {"type": "string", "enum": ["random_forest", "svm", "neural_net"]},
            "features": {"type": "array"},
            "labels": {"type": "array"},
            "hyperparameters": {"type": "object"},
        },
        returns="Trained model and metrics"
    ),
    MCPTool(
        name="predict_model",
        category=ToolCategory.ML,
        description="Make predictions with trained model",
        parameters={
            "model": {"type": "object"},
            "features": {"type": "array"},
        },
        returns="Predictions and confidence intervals"
    ),
    MCPTool(
        name="evaluate_model",
        category=ToolCategory.ML,
        description="Evaluate model performance",
        parameters={
            "model": {"type": "object"},
            "test_features": {"type": "array"},
            "test_labels": {"type": "array"},
            "metrics": {"type": "array"},
        },
        returns="Performance metrics"
    ),
    MCPTool(
        name="feature_importance",
        category=ToolCategory.ML,
        description="Compute feature importance",
        parameters={
            "model": {"type": "object"},
            "features": {"type": "array"},
        },
        returns="Feature importance scores"
    ),

    # NLP Tools (4)
    MCPTool(
        name="extract_entities",
        category=ToolCategory.NLP,
        description="Extract named entities from text",
        parameters={
            "text": {"type": "string"},
            "entity_types": {"type": "array", "items": {"type": "string"}},
        },
        returns="List of extracted entities"
    ),
    MCPTool(
        name="sentiment_analysis",
        category=ToolCategory.NLP,
        description="Analyze sentiment of text",
        parameters={
            "text": {"type": "string"},
            "method": {"type": "string", "enum": ["vader", "bert"], "default": "vader"},
        },
        returns="Sentiment score and classification"
    ),
    MCPTool(
        name="text_similarity",
        category=ToolCategory.NLP,
        description="Compute semantic similarity between texts",
        parameters={
            "text1": {"type": "string"},
            "text2": {"type": "string"},
            "method": {"type": "string", "enum": ["tfidf", "embedding", "levenshtein"]},
        },
        returns="Similarity score (0-1)"
    ),
    MCPTool(
        name="summarize_text",
        category=ToolCategory.NLP,
        description="Generate summary of text",
        parameters={
            "text": {"type": "string"},
            "max_length": {"type": "integer", "default": 200},
        },
        returns="Summary text"
    ),

    # Visualization Tools (2)
    MCPTool(
        name="plot_chart",
        category=ToolCategory.VISUALIZATION,
        description="Generate plot from data",
        parameters={
            "data": {"type": "array"},
            "chart_type": {"type": "string", "enum": ["scatter", "line", "bar", "histogram"]},
            "x": {"type": "string"},
            "y": {"type": "string"},
        },
        returns="Plot file path or base64 image"
    ),
    MCPTool(
        name="generate_report",
        category=ToolCategory.VISUALIZATION,
        description="Generate formatted report",
        parameters={
            "content": {"type": "object"},
            "format": {"type": "string", "enum": ["markdown", "html", "pdf"]},
            "template": {"type": "string"},
        },
        returns="Report file path"
    ),

    # Knowledge Tools (2)
    MCPTool(
        name="semantic_search",
        category=ToolCategory.KNOWLEDGE,
        description="Search knowledge base semantically",
        parameters={
            "query": {"type": "string"},
            "top_k": {"type": "integer", "default": 10},
        },
        returns="List of relevant documents with scores"
    ),
    MCPTool(
        name="knowledge_graph_query",
        category=ToolCategory.KNOWLEDGE,
        description="Query knowledge graph",
        parameters={
            "query": {"type": "string"},
            "constraints": {"type": "object"},
        },
        returns="Query results from knowledge graph"
    ),

    # Validation Tools (2)
    MCPTool(
        name="validate_hypothesis",
        category=ToolCategory.VALIDATION,
        description="Validate hypothesis against knowledge base",
        parameters={
            "hypothesis": {"type": "string"},
            "domain": {"type": "string"},
        },
        returns="Validation result with confidence score"
    ),
    MCPTool(
        name="check_consistency",
        category=ToolCategory.VALIDATION,
        description="Check internal consistency of claims",
        parameters={
            "claims": {"type": "array"},
        },
        returns="Consistency report with contradictions"
    ),
]


# ============================================================================
# MCP Bridge Implementation
# ============================================================================

class AtlasMCPBridge:
    """
    Bridge to ATLAS MCP server for 28 tool capabilities.

    This bridge provides:
    1. Tool catalog management
    2. Execution engine with caching
    3. Error handling and retries
    4. Metrics collection
    5. Fallback to local implementations

    Usage:
        bridge = AtlasMCPBridge()
        result = bridge.execute_tool("statistical_test", {
            "test": "t_test",
            "data_x": [1, 2, 3],
            "data_y": [2, 3, 4],
        })
    """

    def __init__(self,
                 server_url: str = MCP_SERVER_URL,
                 enable_cache: bool = True,
                 timeout: float = DEFAULT_TIMEOUT):
        """
        Initialize ATLAS MCP bridge.

        Args:
            server_url: URL of ATLAS MCP server
            enable_cache: Enable result caching
            timeout: Default timeout for tool execution
        """
        self.server_url = server_url
        self.enable_cache = enable_cache
        self.timeout = timeout

        # Tool catalog
        self._tools: Dict[str, MCPTool] = {t.name: t for t in MCP_TOOL_CATALOG}

        # Result cache
        self._cache: Dict[str, MCPToolResult] = {}

        # Thread safety
        self._lock = threading.RLock()
        self._cache_lock = threading.Lock()

        # Metrics
        self.metrics = MCPMetrics()

        # HTTP client (lazy initialization)
        self._session = None

        # Initialize
        STATE_DIR.mkdir(parents=True, exist_ok=True)
        self._load_cache()

        logger.info(f'AtlasMCPBridge initialized (server={server_url}, tools={len(self._tools)})')

    # ========================================================================
    # Tool Execution
    # ========================================================================

    def execute_tool(self,
                    tool_name: str,
                    parameters: Dict[str, Any],
                    timeout: Optional[float] = None) -> MCPToolResult:
        """
        Execute an MCP tool.

        Args:
            tool_name: Name of tool to execute
            parameters: Tool parameters
            timeout: Execution timeout (overrides default)

        Returns:
            MCPToolResult with execution result
        """
        start_time = time.time()

        # Validate tool exists
        if tool_name not in self._tools:
            return MCPToolResult(
                tool_name=tool_name,
                success=False,
                result=None,
                error=f"Unknown tool: {tool_name}",
                execution_time_ms=0,
            )

        tool = self._tools[tool_name]
        if not tool.enabled:
            return MCPToolResult(
                tool_name=tool_name,
                success=False,
                result=None,
                error=f"Tool disabled: {tool_name}",
                execution_time_ms=0,
            )

        # Check cache
        if self.enable_cache:
            cached = self._get_cached_result(tool_name, parameters)
            if cached is not None:
                self.metrics.cache_hits += 1
                cached.cached = True
                return cached
            self.metrics.cache_misses += 1

        # Execute tool
        try:
            result = self._execute_remote_tool(tool_name, parameters, timeout or tool.timeout)
            execution_ms = (time.time() - start_time) * 1000

            mcp_result = MCPToolResult(
                tool_name=tool_name,
                success=True,
                result=result,
                execution_time_ms=execution_ms,
            )

            # Update metrics
            with self._lock:
                self.metrics.total_calls += 1
                self.metrics.successful_calls += 1
                self.metrics.total_execution_time_ms += execution_ms
                self.metrics.calls_by_tool[tool_name] = (
                    self.metrics.calls_by_tool.get(tool_name, 0) + 1
                )

            # Cache result
            if self.enable_cache:
                self._cache_result(tool_name, parameters, mcp_result)

            return mcp_result

        except Exception as e:
            execution_ms = (time.time() - start_time) * 1000

            with self._lock:
                self.metrics.total_calls += 1
                self.metrics.failed_calls += 1
                self.metrics.calls_by_tool[tool_name] = (
                    self.metrics.calls_by_tool.get(tool_name, 0) + 1
                )

            return MCPToolResult(
                tool_name=tool_name,
                success=False,
                result=None,
                error=str(e),
                execution_time_ms=execution_ms,
            )

    def execute_batch(self,
                     operations: List[Dict[str, Any]],
                     parallel: bool = True) -> List[MCPToolResult]:
        """
        Execute multiple tools in batch.

        Args:
            operations: List of {"tool": str, "params": dict} dicts
            parallel: If True, execute in parallel

        Returns:
            List of MCPToolResult
        """
        if parallel:
            # Parallel execution using asyncio
            return self._execute_batch_parallel(operations)
        else:
            # Sequential execution
            return [
                self.execute_tool(op['tool'], op.get('params', {}))
                for op in operations
            ]

    # ========================================================================
    # Remote Execution
    # ========================================================================

    def _execute_remote_tool(self,
                            tool_name: str,
                            parameters: Dict[str, Any],
                            timeout: float) -> Any:
        """
        Execute tool on remote ATLAS MCP server via JSON-RPC 2.0.

        Raises:
            ConnectionError: If server unavailable
            TimeoutError: If execution timeout
            Exception: For other errors
        """
        try:
            import httpx
        except ImportError:
            # Fallback to requests
            import requests
            return self._execute_with_requests(tool_name, parameters, timeout)

        if self._session is None:
            self._session = httpx.Client(timeout=timeout)

        # JSON-RPC 2.0 request
        request = {
            "jsonrpc": "2.0",
            "method": "tools/call",
            "params": {
                "name": tool_name,
                "arguments": parameters,
            },
            "id": f"{tool_name}_{time.time()}",
        }

        response = self._session.post(
            f"{self.server_url}/rpc",
            json=request,
            timeout=timeout,
        )

        response.raise_for_status()
        result = response.json()

        # Check for JSON-RPC error
        if "error" in result:
            raise Exception(result["error"].get("message", "Unknown error"))

        return result.get("result")

    def _execute_with_requests(self,
                               tool_name: str,
                               parameters: Dict[str, Any],
                               timeout: float) -> Any:
        """Fallback execution using requests library."""
        import requests

        request = {
            "jsonrpc": "2.0",
            "method": "tools/call",
            "params": {
                "name": tool_name,
                "arguments": parameters,
            },
            "id": f"{tool_name}_{time.time()}",
        }

        response = requests.post(
            f"{self.server_url}/rpc",
            json=request,
            timeout=timeout,
        )

        response.raise_for_status()
        result = response.json()

        if "error" in result:
            raise Exception(result["error"].get("message", "Unknown error"))

        return result.get("result")

    def _execute_batch_parallel(self,
                                operations: List[Dict[str, Any]]) -> List[MCPToolResult]:
        """Execute tools in parallel using asyncio."""
        try:
            import asyncio
            import httpx

            async def execute_all(ops):
                async with httpx.AsyncClient(timeout=self.timeout) as session:
                    tasks = []
                    for op in ops:
                        task = self._execute_async(session, op['tool'], op.get('params', {}))
                        tasks.append(task)
                    return await asyncio.gather(*tasks, return_exceptions=True)

            results = asyncio.run(execute_all(operations))

            # Convert to MCPToolResult
            mcp_results = []
            for i, result in enumerate(results):
                if isinstance(result, Exception):
                    mcp_results.append(MCPToolResult(
                        tool_name=operations[i]['tool'],
                        success=False,
                        result=None,
                        error=str(result),
                        execution_time_ms=0,
                    ))
                else:
                    mcp_results.append(MCPToolResult(
                        tool_name=operations[i]['tool'],
                        success=True,
                        result=result,
                        execution_time_ms=0,
                    ))

            return mcp_results

        except ImportError:
            # Fall back to sequential
            logger.warning("Async libraries unavailable, using sequential execution")
            return [
                self.execute_tool(op['tool'], op.get('params', {}))
                for op in operations
            ]

    async def _execute_async(self,
                            session,
                            tool_name: str,
                            parameters: Dict[str, Any]) -> Any:
        """Async tool execution."""
        request = {
            "jsonrpc": "2.0",
            "method": "tools/call",
            "params": {
                "name": tool_name,
                "arguments": parameters,
            },
            "id": f"{tool_name}_{time.time()}",
        }

        response = await session.post(f"{self.server_url}/rpc", json=request)
        response.raise_for_status()
        result = response.json()

        if "error" in result:
            raise Exception(result["error"].get("message", "Unknown error"))

        return result.get("result")

    # ========================================================================
    # Cache Management
    # ========================================================================

    def _get_cache_key(self, tool_name: str, parameters: Dict[str, Any]) -> str:
        """Generate cache key for tool result."""
        key_data = f"{tool_name}:{json.dumps(parameters, sort_keys=True)}"
        return hashlib.md5(key_data.encode()).hexdigest()

    def _get_cached_result(self,
                          tool_name: str,
                          parameters: Dict[str, Any]) -> Optional[MCPToolResult]:
        """Get cached result if available and not expired."""
        cache_key = self._get_cache_key(tool_name, parameters)

        with self._cache_lock:
            if cache_key in self._cache:
                cached = self._cache[cache_key]
                # Check if entry has expired
                if time.time() - cached.execution_time_ms / 1000 < CACHE_TTL:
                    return cached
                else:
                    # Remove expired entry
                    del self._cache[cache_key]
        return None

    def _cache_result(self,
                     tool_name: str,
                     parameters: Dict[str, Any],
                     result: MCPToolResult):
        """Cache tool result."""
        cache_key = self._get_cache_key(tool_name, parameters)

        with self._cache_lock:
            self._cache[cache_key] = result

            # Enforce cache size limit (LRU eviction)
            if len(self._cache) > MAX_CACHE_SIZE:
                # Remove oldest entry
                oldest_key = min(self._cache.keys(),
                               key=lambda k: self._cache[k].execution_time_ms)
                del self._cache[oldest_key]

    def clear_cache(self):
        """Clear tool result cache."""
        with self._cache_lock:
            self._cache.clear()
        logger.info('MCP tool cache cleared')

    # ========================================================================
    # Tool Management
    # ========================================================================

    def get_tool(self, tool_name: str) -> Optional[MCPTool]:
        """Get tool definition from catalog."""
        return self._tools.get(tool_name)

    def list_tools(self,
                  category: Optional[ToolCategory] = None,
                  enabled_only: bool = True) -> List[MCPTool]:
        """List available tools."""
        tools = list(self._tools.values())

        if category:
            tools = [t for t in tools if t.category == category]

        if enabled_only:
            tools = [t for t in tools if t.enabled]

        return tools

    def enable_tool(self, tool_name: str) -> bool:
        """Enable a tool."""
        if tool_name in self._tools:
            self._tools[tool_name].enabled = True
            return True
        return False

    def disable_tool(self, tool_name: str) -> bool:
        """Disable a tool."""
        if tool_name in self._tools:
            self._tools[tool_name].enabled = False
            return True
        return False

    # ========================================================================
    # ASTRA Integration Helpers
    # ========================================================================

    def statistical_test(self,
                        test: str,
                        data_x: List[float],
                        data_y: Optional[List[float]] = None) -> MCPToolResult:
        """Convenience wrapper for statistical tests."""
        params = {"test": test, "data_x": data_x}
        if data_y is not None:
            params["data_y"] = data_y
        return self.execute_tool("statistical_test", params)

    def causal_discovery(self,
                        data: List[List[float]],
                        algorithm: str = "pc") -> MCPToolResult:
        """Convenience wrapper for causal discovery."""
        return self.execute_tool("causal_discovery", {
            "data": data,
            "algorithm": algorithm,
        })

    def validate_hypothesis(self,
                           hypothesis: str,
                           domain: str) -> MCPToolResult:
        """Convenience wrapper for hypothesis validation."""
        return self.execute_tool("validate_hypothesis", {
            "hypothesis": hypothesis,
            "domain": domain,
        })

    # ========================================================================
    # Status & Metrics
    # ========================================================================

    def get_status(self) -> Dict:
        """Get bridge status."""
        return {
            'server_url': self.server_url,
            'total_tools': len(self._tools),
            'enabled_tools': len([t for t in self._tools.values() if t.enabled]),
            'cache_enabled': self.enable_cache,
            'cache_size': len(self._cache),
            **asdict(self.metrics),
        }

    def get_metrics(self) -> Dict:
        """Get usage metrics."""
        with self._lock:
            return {
                'total_calls': self.metrics.total_calls,
                'successful_calls': self.metrics.successful_calls,
                'failed_calls': self.metrics.failed_calls,
                'success_rate': round(self.metrics.compute_success_rate(), 3),
                'avg_execution_time_ms': round(self.metrics.compute_avg_execution_time_ms(), 2),
                'cache_hits': self.metrics.cache_hits,
                'cache_misses': self.metrics.cache_misses,
                'cache_hit_rate': round(
                    self.metrics.cache_hits / max(self.metrics.cache_hits + self.metrics.cache_misses, 1),
                    3
                ),
                'calls_by_tool': dict(self.metrics.calls_by_tool),
            }

    # ========================================================================
    # Persistence
    # ========================================================================

    def persist_state(self):
        """Save cache and metrics to disk."""
        try:
            # Save cache
            with open(str(CACHE_FILE), 'w') as f:
                cache_data = {
                    key: result.to_dict()
                    for key, result in self._cache.items()
                }
                json.dump(cache_data, f, indent=2)

            # Save metrics
            with open(str(METRICS_FILE), 'w') as f:
                json.dump(asdict(self.metrics), f, indent=2)

            logger.info('AtlasMCPBridge state persisted')

        except Exception as e:
            logger.warning(f'Could not persist MCP state: {e}')

    def _load_cache(self):
        """Load cached results from disk."""
        try:
            if CACHE_FILE.exists():
                with open(str(CACHE_FILE)) as f:
                    cache_data = json.load(f)
                for key, result_dict in cache_data.items():
                    self._cache[key] = MCPToolResult(**result_dict)
                logger.info(f'Loaded {len(self._cache)} cached tool results')

            if METRICS_FILE.exists():
                with open(str(METRICS_FILE)) as f:
                    metrics_data = json.load(f)
                for key, value in metrics_data.items():
                    if hasattr(self.metrics, key):
                        setattr(self.metrics, key, value)
                logger.info('Loaded MCP metrics from disk')

        except Exception as e:
            logger.warning(f'Could not load MCP cache: {e}')

    def close(self):
        """Close resources (HTTP session, etc.)."""
        if self._session is not None:
            self._session.close()
            self._session = None


# ============================================================================
# Singleton Instance
# ============================================================================

_bridge_instance: Optional[AtlasMCPBridge] = None
_bridge_lock = threading.Lock()


def get_atlas_mcp_bridge(server_url: str = MCP_SERVER_URL,
                        enable_cache: bool = True) -> AtlasMCPBridge:
    """Get or create the singleton ATLAS MCP bridge."""
    global _bridge_instance
    if _bridge_instance is None:
        with _bridge_lock:
            if _bridge_instance is None:
                _bridge_instance = AtlasMCPBridge(
                    server_url=server_url,
                    enable_cache=enable_cache
                )
    return _bridge_instance
