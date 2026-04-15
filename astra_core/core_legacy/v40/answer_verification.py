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
Answer Verification System for STAN V40

Implements:
- Backward chaining verification
- Symbolic math verification (SymPy)
- Unit consistency checking
- Constraint validation

Target: +5-8% through answer validation

Date: 2025-12-11
Version: 40.0
"""

import re
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Any, Tuple, Set, Union
from enum import Enum


class VerificationStatus(Enum):
    """Status of verification"""
    VERIFIED = "verified"
    FAILED = "failed"
    PARTIAL = "partial"
    UNKNOWN = "unknown"
    ERROR = "error"


class VerificationType(Enum):
    """Types of verification"""
    BACKWARD_CHAIN = "backward_chain"
    SYMBOLIC_MATH = "symbolic_math"
    UNIT_CONSISTENCY = "unit_consistency"
    CONSTRAINT = "constraint"
    FORMAT = "format"
    RANGE = "range"


@dataclass
class VerificationResult:
    """Result of a verification check"""
    verification_type: VerificationType
    status: VerificationStatus
    confidence: float = 0.5

    # Details
    message: str = ""
    issues: List[str] = field(default_factory=list)
    suggestions: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict:
        return {
            'type': self.verification_type.value,
            'status': self.status.value,
            'confidence': self.confidence,
            'message': self.message,
            'issues': self.issues
        }


@dataclass
class Unit:
    """Physical unit representation"""
    name: str
    dimension: str  # length, time, mass, etc.
    symbol: str
    si_conversion: float = 1.0  # Conversion to SI

    # Compound unit composition
    composition: Dict[str, int] = field(default_factory=dict)  # base_unit -> power

    def to_dict(self) -> Dict:
        return {
            'name': self.name,
            'dimension': self.dimension,
            'symbol': self.symbol
        }


class BackwardChainer:
    """
    Backward chaining verification.

    Traces answer back to premises to verify derivation.
    """

    def __init__(self):
        # Inference rules
        self.rules: Dict[str, List[Tuple[List[str], str]]] = {}

        # Statistics
        self.verifications_performed = 0

    def add_rule(self, conclusion: str, premises: List[str]) -> None:
        """Add an inference rule: premises -> conclusion"""
        if conclusion not in self.rules:
            self.rules[conclusion] = []
        self.rules[conclusion].append((premises, conclusion))

    def verify(self, answer: str,
              question: str,
              reasoning_trace: List[str]) -> VerificationResult:
        """
        Verify an answer using backward chaining.

        Args:
            answer: The answer to verify
            question: Original question
            reasoning_trace: Steps taken to derive answer

        Returns:
            VerificationResult
        """
        self.verifications_performed += 1

        issues = []
        confidence = 0.5

        # Check if reasoning trace exists
        if not reasoning_trace:
            return VerificationResult(
                verification_type=VerificationType.BACKWARD_CHAIN,
                status=VerificationStatus.UNKNOWN,
                confidence=0.3,
                message="No reasoning trace provided",
                issues=["Missing derivation steps"]
            )

        # Check trace coherence
        coherence = self._check_trace_coherence(reasoning_trace)
        if coherence < 0.5:
            issues.append("Reasoning trace may have gaps")
            confidence *= 0.8

        # Check if answer follows from trace
        derivation_valid = self._check_derivation(answer, reasoning_trace)
        if not derivation_valid:
            issues.append("Answer may not follow from reasoning")
            confidence *= 0.7

        # Check consistency with question
        consistency = self._check_question_consistency(answer, question)
        if consistency < 0.5:
            issues.append("Answer may not address the question")
            confidence *= 0.8

        # Determine status
        if not issues:
            status = VerificationStatus.VERIFIED
            confidence = min(0.95, confidence * 1.2)
        elif len(issues) <= 1:
            status = VerificationStatus.PARTIAL
        else:
            status = VerificationStatus.FAILED

        return VerificationResult(
            verification_type=VerificationType.BACKWARD_CHAIN,
            status=status,
            confidence=confidence,
            message=f"Backward chain verification: {status.value}",
            issues=issues
        )

    def _check_trace_coherence(self, trace: List[str]) -> float:
        """Check if reasoning trace is coherent"""
        if len(trace) < 2:
            return 0.3

        coherence = 0.0

        for i in range(1, len(trace)):
            prev_step = trace[i-1].lower()
            curr_step = trace[i].lower()

            # Check for logical connectors
            connectors = ['therefore', 'thus', 'hence', 'so', 'because',
                        'since', 'given', 'from']
            has_connector = any(c in curr_step for c in connectors)

            # Check for word overlap
            prev_words = set(prev_step.split())
            curr_words = set(curr_step.split())
            overlap = len(prev_words & curr_words) / max(len(curr_words), 1)

            step_coherence = 0.5
            if has_connector:
                step_coherence += 0.3
            if overlap > 0.1:
                step_coherence += 0.2

            coherence += step_coherence

        return coherence / (len(trace) - 1) if len(trace) > 1 else 0.5

    def _check_derivation(self, answer: str, trace: List[str]) -> bool:
        """Check if answer is derivable from trace"""
        answer_lower = answer.lower().strip()

        # Check if answer appears in final steps
        for step in trace[-3:]:
            if answer_lower in step.lower():
                return True

        # Check for numeric match
        answer_nums = re.findall(r'-?\d+\.?\d*', answer)
        if answer_nums:
            for step in trace[-3:]:
                step_nums = re.findall(r'-?\d+\.?\d*', step)
                if any(n in step_nums for n in answer_nums):
                    return True

        return False

    def _check_question_consistency(self, answer: str, question: str) -> float:
        """Check if answer is consistent with question type"""
        q_lower = question.lower()
        a_lower = answer.lower()

        # Yes/No question
        if 'yes or no' in q_lower or q_lower.startswith(('is ', 'are ', 'does ', 'do ', 'can ', 'will ')):
            if a_lower in ['yes', 'no', 'true', 'false']:
                return 0.9
            return 0.3

        # Numeric question
        if any(w in q_lower for w in ['how many', 'how much', 'calculate', 'compute']):
            if re.search(r'\d', answer):
                return 0.8
            return 0.3

        # What/Who/Where question
        if q_lower.startswith(('what ', 'who ', 'where ', 'when ')):
            if len(answer) > 2:
                return 0.7

        return 0.5


class SymbolicMathVerifier:
    """
    Symbolic math verification using SymPy.

    Verifies:
    - Algebraic simplifications
    - Equation solutions
    - Derivative/Integral computations
    """
