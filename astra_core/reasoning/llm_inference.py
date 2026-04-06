"""
LLM Inference Module for STAN V40

Provides integration with Claude API for enhanced reasoning capabilities.
Supports structured prompting, chain-of-thought reasoning, and multi-turn dialogue.

Date: 2025-12-11
Version: 40.0
"""

import os
import json
import asyncio
import hashlib
import time
from typing import Dict, List, Optional, Any, Tuple, Union
from dataclasses import dataclass, field
from enum import Enum
from abc import ABC, abstractmethod

# Try to import anthropic client
try:
    import anthropic
    ANTHROPIC_AVAILABLE = True
except ImportError:
    ANTHROPIC_AVAILABLE = False
    anthropic = None


class ModelType(Enum):
    """Supported LLM models"""
    CLAUDE_3_OPUS = "claude-3-opus-20240229"
    CLAUDE_3_SONNET = "claude-3-sonnet-20240229"
    CLAUDE_3_HAIKU = "claude-3-haiku-20240307"
    CLAUDE_3_5_SONNET = "claude-3-5-sonnet-20241022"
    CLAUDE_3_5_HAIKU = "claude-3-5-haiku-20241022"


class ReasoningMode(Enum):
    """Reasoning modes for different problem types"""
    DIRECT = "direct"                    # Simple Q&A
    CHAIN_OF_THOUGHT = "chain_of_thought"  # Step-by-step reasoning
    SELF_CONSISTENCY = "self_consistency"   # Multiple reasoning paths
    TREE_OF_THOUGHT = "tree_of_thought"     # Branching exploration
    SOCRATIC = "socratic"                   # Question-driven refinement
    MATHEMATICAL = "mathematical"           # Math-specific prompting
    SCIENTIFIC = "scientific"               # Scientific reasoning


@dataclass
class LLMRequest:
    """A request to the LLM"""
    prompt: str
    system_prompt: Optional[str] = None
    reasoning_mode: ReasoningMode = ReasoningMode.DIRECT
    max_tokens: int = 4096
    temperature: float = 0.7
    model: ModelType = ModelType.CLAUDE_3_5_SONNET
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class LLMResponse:
    """Response from the LLM"""
    content: str
    reasoning_steps: List[str] = field(default_factory=list)
    confidence: float = 0.0
    model_used: str = ""
    tokens_used: int = 0
    latency_ms: float = 0.0
    cached: bool = False
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class ConversationTurn:
    """A single turn in a conversation"""
    role: str  # "user" or "assistant"
    content: str
    timestamp: float = field(default_factory=time.time)


class PromptTemplate:
    """Templates for different reasoning modes"""

    CHAIN_OF_THOUGHT = """Let's solve this step by step:

Problem: {problem}

Please think through this carefully:
1. First, identify what we're asked to find
2. List the relevant information and constraints
3. Work through the solution step by step
4. Verify your answer

Show your complete reasoning process."""

    MATHEMATICAL = """You are a mathematical reasoning expert. Solve the following problem with rigorous mathematical reasoning.

Problem: {problem}

Approach:
1. Identify the mathematical domain (algebra, calculus, number theory, etc.)
2. State any relevant theorems or formulas
3. Show all work with clear algebraic steps
4. Verify your answer by substitution or alternative method
5. State the final answer clearly

Be precise with mathematical notation and logical steps."""

    SCIENTIFIC = """You are a scientific reasoning expert. Analyze the following question using rigorous scientific methodology.

Question: {problem}

Approach:
1. Identify the scientific domain and relevant principles
2. State known facts and applicable laws/theories
3. Apply logical reasoning from first principles
4. Consider alternative explanations
5. Provide evidence-based conclusions

Use precise scientific terminology and cite relevant principles."""

    SELF_CONSISTENCY = """Solve this problem using {n_paths} different approaches, then determine the most reliable answer.

Problem: {problem}

For each approach:
- Use a distinct reasoning method
- Show complete work
- State your answer

Then compare the approaches and explain which answer is most trustworthy and why."""

    SOCRATIC = """Let's explore this question through guided inquiry.

Initial question: {problem}

Consider:
1. What do we already know that's relevant?
2. What assumptions are we making?
3. What are the key sub-questions we need to answer?
4. How do these sub-answers combine to answer the main question?
5. Are there any edge cases or exceptions to consider?

Build up your understanding systematically."""

    VERIFICATION = """Review and verify the following solution:

Problem: {problem}
Proposed solution: {solution}

Check:
1. Is the reasoning logically valid?
2. Are all calculations correct?
3. Does the answer make sense in context?
4. Are there any errors or gaps in the reasoning?

Provide your assessment and corrections if needed."""


class ResponseCache:
    """Cache for LLM responses to avoid redundant API calls"""

    def __init__(self, max_size: int = 1000):
        self.cache: Dict[str, LLMResponse] = {}
        self.max_size = max_size
        self.access_times: Dict[str, float] = {}

    def _hash_request(self, request: LLMRequest) -> str:
        """Create hash key for request"""
        key_data = f"{request.prompt}|{request.system_prompt}|{request.model.value}|{request.temperature}"
        return hashlib.sha256(key_data.encode()).hexdigest()[:16]

    def get(self, request: LLMRequest) -> Optional[LLMResponse]:
        """Get cached response if available"""
        key = self._hash_request(request)
        if key in self.cache:
            self.access_times[key] = time.time()
            response = self.cache[key]
            response.cached = True
            return response
        return None

    def put(self, request: LLMRequest, response: LLMResponse):
        """Cache a response"""
        if len(self.cache) >= self.max_size:
            # Remove least recently accessed
            oldest_key = min(self.access_times, key=self.access_times.get)
            del self.cache[oldest_key]
            del self.access_times[oldest_key]

        key = self._hash_request(request)
        self.cache[key] = response
        self.access_times[key] = time.time()


class LLMInferenceEngine:
    """
    Main LLM inference engine for STAN V40.

    Provides structured prompting, chain-of-thought reasoning,
    and integration with Claude API.
    """

    def __init__(self, api_key: Optional[str] = None,
                 default_model: ModelType = ModelType.CLAUDE_3_5_SONNET,
                 enable_cache: bool = True):
        """
        Initialize the LLM inference engine.

        Args:
            api_key: Anthropic API key (or uses ANTHROPIC_API_KEY env var)
            default_model: Default model to use
            enable_cache: Whether to cache responses
        """
        self.api_key = api_key or os.environ.get("ANTHROPIC_API_KEY")
        self.default_model = default_model
        self.cache = ResponseCache() if enable_cache else None

        # Initialize client if available
        self.client = None
        if ANTHROPIC_AVAILABLE and self.api_key:
            self.client = anthropic.Anthropic(api_key=self.api_key)

        # Conversation history for multi-turn
        self.conversations: Dict[str, List[ConversationTurn]] = {}

        # Statistics
        self.stats = {
            'total_requests': 0,
            'cache_hits': 0,
            'total_tokens': 0,
            'total_latency_ms': 0
        }

    def query(self, request: LLMRequest) -> LLMResponse:
        """
        Send a query to the LLM.

        Args:
            request: The LLM request

        Returns:
            LLMResponse with the model's answer
        """
        self.stats['total_requests'] += 1

        # Check cache first
        if self.cache:
            cached = self.cache.get(request)
            if cached:
                self.stats['cache_hits'] += 1
                return cached

        # Build prompt based on reasoning mode
        formatted_prompt = self._format_prompt(request)

        # Call API or simulate
        start_time = time.time()

        if self.client:
            response = self._call_api(formatted_prompt, request)
        else:
            response = self._simulate_response(formatted_prompt, request)

        response.latency_ms = (time.time() - start_time) * 1000
        self.stats['total_latency_ms'] += response.latency_ms
        self.stats['total_tokens'] += response.tokens_used

        # Cache response
        if self.cache:
            self.cache.put(request, response)

        return response

    def query_with_verification(self, request: LLMRequest,
                                verify: bool = True) -> LLMResponse:
        """
        Query with optional self-verification step.

        Args:
            request: The LLM request
            verify: Whether to verify the response

        Returns:
            Verified LLMResponse
        """
        # Get initial response
        response = self.query(request)

        if not verify:
            return response

        # Create verification request
        verify_prompt = PromptTemplate.VERIFICATION.format(
            problem=request.prompt,
            solution=response.content
        )

        verify_request = LLMRequest(
            prompt=verify_prompt,
            system_prompt="You are a careful reviewer. Check solutions for errors.",
            reasoning_mode=ReasoningMode.DIRECT,
            max_tokens=2048,
            temperature=0.3,
            model=request.model
        )

        verify_response = self.query(verify_request)

        # Update confidence based on verification
        if "correct" in verify_response.content.lower():
            response.confidence = min(1.0, response.confidence + 0.1)
        elif "error" in verify_response.content.lower():
            response.confidence = max(0.0, response.confidence - 0.2)

        response.metadata['verification'] = verify_response.content

        return response

    def multi_turn_query(self, conversation_id: str,
                         user_message: str,
                         system_prompt: Optional[str] = None) -> LLMResponse:
        """
        Multi-turn conversation query.

        Args:
            conversation_id: ID for this conversation
            user_message: The user's message
            system_prompt: Optional system prompt

        Returns:
            LLMResponse
        """
        # Initialize conversation if needed
        if conversation_id not in self.conversations:
            self.conversations[conversation_id] = []

        # Add user turn
        self.conversations[conversation_id].append(
            ConversationTurn(role="user", content=user_message)
        )

        # Build messages for API
        messages = [
            {"role": turn.role, "content": turn.content}
            for turn in self.conversations[conversation_id]
        ]

        # Query
        if self.client:
            response = self._call_api_messages(messages, system_prompt)
        else:
            response = self._simulate_response(user_message, LLMRequest(
                prompt=user_message,
                system_prompt=system_prompt,
                reasoning_mode=ReasoningMode.DIRECT
            ))

        # Add assistant turn
        self.conversations[conversation_id].append(
            ConversationTurn(role="assistant", content=response.content)
        )

        return response

    def chain_of_thought(self, problem: str,
                         domain: Optional[str] = None) -> LLMResponse:
        """
        Apply chain-of-thought reasoning.

        Args:
            problem: The problem to solve
            domain: Optional domain hint (math, science, etc.)

        Returns:
            LLMResponse with step-by-step reasoning
        """
        # Select appropriate template
        if domain == "math" or domain == "mathematical":
            template = PromptTemplate.MATHEMATICAL
        elif domain in ["science", "scientific", "physics", "chemistry", "biology"]:
            template = PromptTemplate.SCIENTIFIC
        else:
            template = PromptTemplate.CHAIN_OF_THOUGHT

        prompt = template.format(problem=problem)

        request = LLMRequest(
            prompt=prompt,
            system_prompt="You are an expert problem solver. Show your reasoning clearly.",
            reasoning_mode=ReasoningMode.CHAIN_OF_THOUGHT,
            temperature=0.5,
            max_tokens=4096
        )

        response = self.query(request)

        # Extract reasoning steps
        response.reasoning_steps = self._extract_steps(response.content)

        return response

    def self_consistency(self, problem: str, n_paths: int = 3) -> LLMResponse:
        """
        Apply self-consistency with multiple reasoning paths.

        Args:
            problem: The problem to solve
            n_paths: Number of reasoning paths to generate

        Returns:
            LLMResponse with consensus answer
        """
        prompt = PromptTemplate.SELF_CONSISTENCY.format(
            problem=problem,
            n_paths=n_paths
        )

        request = LLMRequest(
            prompt=prompt,
            system_prompt="You are an expert at solving problems multiple ways.",
            reasoning_mode=ReasoningMode.SELF_CONSISTENCY,
            temperature=0.7,
            max_tokens=6000
        )

        response = self.query(request)

        # Extract and compare answers
        response.metadata['n_paths'] = n_paths

        return response

    def mathematical_query(self, problem: str) -> LLMResponse:
        """
        Query specifically optimized for mathematical problems.

        Args:
            problem: The mathematical problem

        Returns:
            LLMResponse with mathematical reasoning
        """
        prompt = PromptTemplate.MATHEMATICAL.format(problem=problem)

        system = """You are a mathematical expert with deep knowledge of:
- Algebra and number theory
- Calculus and analysis
- Geometry and topology
- Probability and statistics
- Discrete mathematics

Always show rigorous proofs and verify your answers."""

        request = LLMRequest(
            prompt=prompt,
            system_prompt=system,
            reasoning_mode=ReasoningMode.MATHEMATICAL,
            temperature=0.3,  # Lower temperature for math
            max_tokens=4096
        )

        return self.query_with_verification(request)

    def scientific_query(self, question: str, domain: str = "general") -> LLMResponse:
        """
        Query optimized for scientific questions.

        Args:
            question: The scientific question
            domain: Scientific domain (physics, chemistry, biology, etc.)

        Returns:
            LLMResponse with scientific reasoning
        """
        prompt = PromptTemplate.SCIENTIFIC.format(problem=question)

        domain_expertise = {
            'physics': "classical mechanics, quantum mechanics, thermodynamics, electromagnetism, relativity",
            'chemistry': "organic chemistry, inorganic chemistry, biochemistry, physical chemistry",
            'biology': "molecular biology, genetics, ecology, evolution, physiology",
            'astronomy': "astrophysics, cosmology, planetary science, stellar evolution",
            'general': "physics, chemistry, biology, and interdisciplinary sciences"
        }

        expertise = domain_expertise.get(domain, domain_expertise['general'])

        system = f"""You are a scientific expert with deep knowledge of {expertise}.

Use first principles reasoning and cite relevant scientific laws and theories.
Be precise with units and significant figures.
Acknowledge uncertainty where appropriate."""

        request = LLMRequest(
            prompt=prompt,
            system_prompt=system,
            reasoning_mode=ReasoningMode.SCIENTIFIC,
            temperature=0.4,
            max_tokens=4096
        )

        return self.query(request)

    def _format_prompt(self, request: LLMRequest) -> str:
        """Format prompt based on reasoning mode"""
        if request.reasoning_mode == ReasoningMode.CHAIN_OF_THOUGHT:
            return PromptTemplate.CHAIN_OF_THOUGHT.format(problem=request.prompt)
        elif request.reasoning_mode == ReasoningMode.MATHEMATICAL:
            return PromptTemplate.MATHEMATICAL.format(problem=request.prompt)
        elif request.reasoning_mode == ReasoningMode.SCIENTIFIC:
            return PromptTemplate.SCIENTIFIC.format(problem=request.prompt)
        elif request.reasoning_mode == ReasoningMode.SOCRATIC:
            return PromptTemplate.SOCRATIC.format(problem=request.prompt)
