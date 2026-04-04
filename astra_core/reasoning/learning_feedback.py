"""
Learning Feedback Loop for STAN V40

Analyzes wrong answers, learns from failures, adjusts parameters,
and propagates learnings across capability modules.

This addresses the gap where the system doesn't learn from
success/failure after answering questions.

Date: 2025-12-11
"""

import json
import time
from typing import Dict, List, Optional, Any, Tuple, Set
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from collections import defaultdict
import re


class FailureType(Enum):
    """Types of reasoning failures"""
    WRONG_ANSWER = "wrong_answer"
    INCOMPLETE_REASONING = "incomplete_reasoning"
    WRONG_METHOD = "wrong_method"
    CALCULATION_ERROR = "calculation_error"
    MISSING_CONSTRAINT = "missing_constraint"
    OVER_GENERALIZATION = "over_generalization"
    UNDER_GENERALIZATION = "under_generalization"
    TIMEOUT = "timeout"
    CONFIDENCE_MISCALIBRATION = "confidence_miscalibration"
    UNKNOWN = "unknown"


class LearningType(Enum):
    """Types of learnings"""
    PARAMETER_ADJUSTMENT = "parameter_adjustment"
    STRATEGY_SWITCH = "strategy_switch"
    CAPABILITY_PRIORITIZATION = "capability_prioritization"
    PATTERN_ADDITION = "pattern_addition"
    CONSTRAINT_ADDITION = "constraint_addition"
    DOMAIN_SPECIFIC = "domain_specific"


@dataclass
class FailureAnalysis:
    """Analysis of a failure"""
    failure_id: str
    failure_type: FailureType
    question_id: str
    question_category: str
    expected_answer: str
    predicted_answer: str
    confidence: float
    reasoning_trace: List[str]
    root_cause: str
    contributing_factors: List[str]
    capabilities_used: List[str]
    capability_that_failed: Optional[str] = None


@dataclass
class Learning:
    """A learning derived from failure analysis"""
    learning_id: str
    learning_type: LearningType
    source_failure: str  # failure_id
    description: str
    category: str
    domain: Optional[str] = None
    parameter_adjustments: Dict[str, Any] = field(default_factory=dict)
    new_patterns: List[str] = field(default_factory=list)
    confidence: float = 0.5
    times_validated: int = 0


@dataclass
class ParameterState:
    """Current state of capability parameters"""
    capability: str
    parameters: Dict[str, float]
    last_updated: float
    update_history: List[Dict] = field(default_factory=list)


@dataclass
class FeedbackRecord:
    """Record of a feedback event"""
    record_id: str
    timestamp: float
    question_id: str
    was_correct: bool
    confidence: float
    actual_answer: str
    predicted_answer: str
    capabilities_used: List[str]
    time_taken: float
    learning_applied: Optional[str] = None


class FailureAnalyzer:
    """Analyze failures to determine root causes"""

    def __init__(self):
        # Patterns for identifying failure types
        self.failure_patterns = {
            FailureType.CALCULATION_ERROR: [
                r'arithmetic', r'compute', r'calculate', r'numerical',
                r'order of magnitude', r'decimal'
            ],
            FailureType.WRONG_METHOD: [
                r'approach', r'method', r'technique', r'formula',
                r'theorem', r'principle'
            ],
            FailureType.MISSING_CONSTRAINT: [
                r'constraint', r'condition', r'assuming', r'given',
                r'boundary', r'limit'
            ],
            FailureType.INCOMPLETE_REASONING: [
                r'step', r'therefore', r'because', r'since',
                r'follows', r'implies'
            ]
        }

    def analyze(self, question: str, expected: str, predicted: str,
                confidence: float, reasoning_trace: List[str],
                capabilities_used: List[str]) -> FailureAnalysis:
        """
        Analyze a failure to determine root cause.

        Args:
            question: The question text
            expected: Expected correct answer
            predicted: Predicted (wrong) answer
            confidence: Confidence in the prediction
            reasoning_trace: Steps taken during reasoning
            capabilities_used: Which capabilities were invoked

        Returns:
            FailureAnalysis with root cause and factors
        """
        failure_id = f"fail_{hash(question) % 10000}_{int(time.time())}"

        # Determine failure type
        failure_type = self._classify_failure(
            question, expected, predicted, reasoning_trace
        )

        # Find root cause
        root_cause = self._find_root_cause(
            failure_type, expected, predicted, reasoning_trace
        )

        # Find contributing factors
        contributing_factors = self._find_contributing_factors(
            question, reasoning_trace, confidence
        )

        # Identify which capability likely failed
        failed_capability = self._identify_failed_capability(
            failure_type, capabilities_used, reasoning_trace
        )

        # Extract category from question
        category = self._infer_category(question)

        return FailureAnalysis(
            failure_id=failure_id,
            failure_type=failure_type,
            question_id=f"q_{hash(question) % 10000}",
            question_category=category,
            expected_answer=expected,
            predicted_answer=predicted,
            confidence=confidence,
            reasoning_trace=reasoning_trace,
            root_cause=root_cause,
            contributing_factors=contributing_factors,
            capabilities_used=capabilities_used,
            capability_that_failed=failed_capability
        )

    def _classify_failure(self, question: str, expected: str,
                         predicted: str, trace: List[str]) -> FailureType:
        """Classify the type of failure"""
        # Simple classification based on keywords and patterns
        question_lower = question.lower()

        if "calculate" in question_lower or "compute" in question_lower:
            if not any(c.isdigit() for c in predicted):
                return FailureType.CALCULATION_ERROR

        if "why" in question_lower or "explain" in question_lower:
            if len(predicted) < 50:
                return FailureType.INSUFFICIENT_DEPTH

        if "not" in expected.lower() and "not" not in predicted.lower():
            return FailureType.LOGICAL_ERROR

        return FailureType.KNOWLEDGE_GAP
