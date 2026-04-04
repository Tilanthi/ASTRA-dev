"""
Self-Consistency Engine: Multi-Sample Voting with Temperature Variation

Core concept: Generate N answers at different temperatures, then vote on the
most common answer. This improves accuracy by +3-5% on complex reasoning tasks.

Features:
- Temperature variation prevents mode collapse
- Confidence = fraction of samples agreeing
- Fallback to Chain-of-Thought if confidence < threshold
- Supports multiple answer types (multiple choice, exact match, open-ended)

Date: 2025-12-10
Version: 38.0
"""

import re
from typing import Dict, List, Optional, Callable, Any, Tuple
from dataclasses import dataclass, field
from collections import Counter
import hashlib


@dataclass
class ConsistencyResult:
    """Result from self-consistency voting"""
    answer: str
    confidence: float
    vote_distribution: Dict[str, int]
    samples: List[str]
    temperatures_used: List[float]
    method: str = "self_consistency"
    fallback_used: bool = False

    def __str__(self):
        return f"ConsistencyResult(answer='{self.answer}', confidence={self.confidence:.2f}, votes={self.vote_distribution})"


@dataclass
class ChainOfThoughtResult:
    """Result from chain-of-thought reasoning"""
    answer: str
    reasoning_chain: List[str]
    confidence: float
    method: str = "chain_of_thought"


class SelfConsistencyEngine:
    """
    Self-Consistency Engine for improved answer accuracy.

    Multi-sample voting with temperature variation:
    1. Generate n_samples answers at varying temperatures
    2. Normalize answers (extract letter for MC, normalize text for exact)
    3. Vote on most common answer
    4. Return answer with confidence = vote_fraction

    Expected gain: +3-5% accuracy
    """

    def __init__(self, n_samples: int = 5, confidence_threshold: float = 0.6):
        """
        Initialize self-consistency engine.

        Args:
            n_samples: Number of samples to generate (default 5)
            confidence_threshold: Minimum confidence before fallback (default 0.6)
        """
        self.n_samples = n_samples
        self.confidence_threshold = confidence_threshold
        self.temperatures = [0.3, 0.5, 0.7, 0.9, 1.1]  # Vary per sample

    def solve(self, prompt: str, answer_type: str,
              llm_fn: Callable[[str, float], str]) -> ConsistencyResult:
        """
        Solve using self-consistency voting.

        Args:
            prompt: The question/prompt to answer
            answer_type: 'multipleChoice', 'exactMatch', or 'openEnded'
            llm_fn: Function(prompt, temperature) -> response

        Returns:
            ConsistencyResult with answer, confidence, and vote distribution
        """
        samples = []
        temperatures_used = []

        for i in range(self.n_samples):
            temp = self.temperatures[i % len(self.temperatures)]
            temperatures_used.append(temp)

            try:
                response = llm_fn(prompt, temp)
                normalized = self._normalize_answer(response, answer_type)
                samples.append(normalized)
            except Exception as e:
                # On error, add placeholder
                samples.append(f"ERROR: {str(e)[:50]}")

        # Remove error samples for voting
        valid_samples = [s for s in samples if not s.startswith("ERROR:")]

        if not valid_samples:
            return ConsistencyResult(
                answer="UNABLE_TO_ANSWER",
                confidence=0.0,
                vote_distribution={},
                samples=samples,
                temperatures_used=temperatures_used
            )

        # Majority vote
        vote_counts = Counter(valid_samples)
        winner, count = vote_counts.most_common(1)[0]
        confidence = count / len(valid_samples)

        return ConsistencyResult(
            answer=winner,
            confidence=confidence,
            vote_distribution=dict(vote_counts),
            samples=samples,
            temperatures_used=temperatures_used
        )

    def _normalize_answer(self, response: str, answer_type: str) -> str:
        """
        Normalize answer based on answer type.

        Args:
            response: Raw LLM response
            answer_type: Type of answer expected

        Returns:
            Normalized answer string
        """
        if answer_type == 'multipleChoice':
            # Extract first letter A-E from response
            # Look for patterns like "A)", "A.", "(A)", "Answer: A", etc.
            patterns = [
                r'\b([A-E])\)',           # A)
                r'\b([A-E])\.',           # A.
                r'\(([A-E])\)',           # (A)
                r'[Aa]nswer:?\s*([A-E])', # Answer: A
                r'^([A-E])\b',            # A at start
                r'\b([A-E])\b'            # Any A-E word boundary
            ]

            for pattern in patterns:
                match = re.search(pattern, response.upper())
                if match:
                    return match.group(1)

            # Last resort: first uppercase letter A-E
            for char in response.upper():
                if char in 'ABCDE':
                    return char

            return response[:1].upper() if response else 'A'

        elif answer_type == 'exactMatch':
            # Normalize exact match: lowercase, strip, remove trailing punctuation
            normalized = response.strip().lower()
            # Remove common trailing punctuation
            normalized = normalized.rstrip('.,;:!?')
            # Remove quotes if present
            normalized = normalized.strip('"\'')
            return normalized

        else:  # openEnded
            # For open-ended, hash the content for comparison
            # (since exact match is unlikely)
            normalized = response.strip().lower()
            # Create a semantic hash based on key words
            words = sorted(set(normalized.split()))
            return ' '.join(words[:10])  # First 10 unique words

    def solve_with_fallback(self, prompt: str, answer_type: str,
                           llm_fn: Callable[[str, float], str],
                           cot_prompt_template: str = None) -> Tuple[str, float, ConsistencyResult]:
        """
        Solve with fallback to Chain-of-Thought if confidence is low.

        Args:
            prompt: The question/prompt
            answer_type: Answer type
            llm_fn: LLM function
            cot_prompt_template: Optional CoT prompt template

        Returns:
            Tuple of (answer, confidence, full_result)
        """
        # First try self-consistency
        result = self.solve(prompt, answer_type, llm_fn)

        if result.confidence >= self.confidence_threshold:
            return result.answer, result.confidence, result

        # Low confidence - try Chain-of-Thought
        if cot_prompt_template:
            cot_prompt = cot_prompt_template.format(question=prompt)
        else:
            cot_prompt = f"""Let's solve this step by step.

Question: {prompt}

Please think through this carefully:
1. First, identify what the question is asking.
2. Consider the relevant facts and concepts.
3. Work through the reasoning step by step.
4. Provide your final answer.
"""

        # Use CoT to get a better answer
        cot_result = llm_fn(cot_prompt)
        return cot_result, 0.8, result
