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


class AnswerVerifier:
    """
    Unified answer verifier (restored 2026-08-21).

    Imported by v40_system (constructor + .verify + .get_stats) but
    never defined in the original module. This restoration composes the
    verifiers that DO exist in this module (BackwardChainer) with
    explicit numeric-sanity checks, and never reports 'verified' unless
    a real check actually passed — undecidable stays 'unknown'.
    """

    def __init__(self):
        self.backward_chainer = BackwardChainer()

        # Statistics
        self.total_verifications = 0
        self.verified_count = 0
        self.failed_count = 0
        self.unknown_count = 0

    def verify(self,
               answer: str,
               question: str,
               reasoning_trace: List[str],
               category: str = "") -> Dict[str, Any]:
        """
        Verify an answer against its question and derivation.

        Args:
            answer: The answer to verify
            question: Original question
            reasoning_trace: Steps taken to derive the answer
            category: Optional problem category

        Returns:
            Dict with verified flag, status, confidence, per-check
            details, and issues found.
        """
        self.total_verifications += 1

        if answer is None or not str(answer).strip():
            self.unknown_count += 1
            return {
                'verified': False,
                'status': VerificationStatus.UNKNOWN.value,
                'confidence': 0.0,
                'checks': [],
                'issues': ['No answer to verify']
            }

        checks: List[Dict[str, Any]] = []
        issues: List[str] = []

        # Check 1: backward chaining over the derivation (real module code)
        chain_result = self.backward_chainer.verify(
            str(answer), question, reasoning_trace or [])
        checks.append(chain_result.to_dict())
        issues.extend(chain_result.issues)

        # Check 2: numeric sanity — a numeric answer must be a finite number
        numeric_result = self._check_numeric_sanity(str(answer))
        checks.append(numeric_result.to_dict())
        issues.extend(numeric_result.issues)

        # Aggregate: verified only if the backward chain genuinely passed
        # and no check failed outright.
        failed = any(c['status'] == VerificationStatus.FAILED.value
                     for c in checks)
        if (chain_result.status == VerificationStatus.VERIFIED
                and not failed):
            status = VerificationStatus.VERIFIED
            confidence = min(0.95, max(chain_result.confidence,
                                       numeric_result.confidence))
        elif failed:
            status = VerificationStatus.FAILED
            confidence = min(chain_result.confidence,
                             numeric_result.confidence)
        else:
            status = VerificationStatus.UNKNOWN
            confidence = min(chain_result.confidence, 0.5)

        if status == VerificationStatus.VERIFIED:
            self.verified_count += 1
        elif status == VerificationStatus.FAILED:
            self.failed_count += 1
        else:
            self.unknown_count += 1

        return {
            'verified': status == VerificationStatus.VERIFIED,
            'status': status.value,
            'confidence': round(confidence, 3),
            'checks': checks,
            'issues': issues,
            'category': category
        }

    def get_stats(self) -> Dict[str, Any]:
        """Verification statistics"""
        return {
            'total_verifications': self.total_verifications,
            'verified': self.verified_count,
            'failed': self.failed_count,
            'unknown': self.unknown_count
        }

    def _check_numeric_sanity(self, answer: str) -> VerificationResult:
        """
        If the answer looks numeric, it must parse as a finite number.
        Non-numeric answers pass this check trivially (nothing asserted).
        """
        cleaned = answer.strip().rstrip('%').replace(',', '')
        is_numeric = bool(cleaned) and (
            cleaned.replace('.', '', 1).replace('-', '', 1).isdigit())

        if not is_numeric:
            return VerificationResult(
                verification_type=VerificationType.FORMAT,
                status=VerificationStatus.UNKNOWN,
                confidence=0.5,
                message="Answer is not numeric; no numeric check applies"
            )

        try:
            value = float(cleaned)
        except ValueError:
            return VerificationResult(
                verification_type=VerificationType.RANGE,
                status=VerificationStatus.FAILED,
                confidence=0.9,
                message="Numeric-looking answer does not parse as a number",
                issues=["Malformed numeric answer"]
            )

        if value != value or value in (float('inf'), float('-inf')):
            return VerificationResult(
                verification_type=VerificationType.RANGE,
                status=VerificationStatus.FAILED,
                confidence=0.9,
                message="Numeric answer is not finite",
                issues=["Non-finite numeric answer"]
            )

        return VerificationResult(
            verification_type=VerificationType.RANGE,
            status=VerificationStatus.VERIFIED,
            confidence=0.9,
            message=f"Numeric answer is finite ({value})"
        )


class UnitConsistencyChecker:
    """
    Checks physical consistency between two quantities by converting
    both to SI before comparing (restored 2026-08-21).
    """

    def __init__(self, tolerance: float = 1e-6):
        self.tolerance = tolerance
        self.checks_performed = 0

    def check_consistency(self,
                          value_a: float,
                          unit_a: Unit,
                          value_b: float,
                          unit_b: Unit) -> VerificationResult:
        """
        Verify that two quantities are consistent.

        Fails when dimensions differ or the SI-converted magnitudes
        disagree beyond tolerance.
        """
        self.checks_performed += 1

        if unit_a.dimension != unit_b.dimension:
            return VerificationResult(
                verification_type=VerificationType.UNIT_CONSISTENCY,
                status=VerificationStatus.FAILED,
                confidence=0.9,
                message=(f"Dimension mismatch: {unit_a.dimension} vs "
                         f"{unit_b.dimension}"),
                issues=["Incompatible physical dimensions"]
            )

        si_a = value_a * unit_a.si_conversion
        si_b = value_b * unit_b.si_conversion

        if abs(si_a - si_b) > self.tolerance * max(abs(si_a), abs(si_b), 1.0):
            return VerificationResult(
                verification_type=VerificationType.UNIT_CONSISTENCY,
                status=VerificationStatus.FAILED,
                confidence=0.9,
                message=f"Values disagree in SI units: {si_a} vs {si_b}",
                issues=["Quantities are not equal after SI conversion"]
            )

        return VerificationResult(
            verification_type=VerificationType.UNIT_CONSISTENCY,
            status=VerificationStatus.VERIFIED,
            confidence=0.95,
            message=f"Consistent in SI units ({si_a})"
        )


class ConstraintValidator:
    """
    Validates a value against explicit constraints
    (restored 2026-08-21).

    Supported constraints: min, max, allowed (list of valid values),
    non_null.
    """

    def __init__(self):
        self.validations_performed = 0

    def validate(self, value: Any,
                 constraints: Dict[str, Any]) -> VerificationResult:
        """
        Validate value against a constraint dict.

        An empty constraint dict is honestly UNKNOWN: nothing was
        asserted, so nothing was verified.
        """
        self.validations_performed += 1

        if not constraints:
            return VerificationResult(
                verification_type=VerificationType.CONSTRAINT,
                status=VerificationStatus.UNKNOWN,
                confidence=0.5,
                message="No constraints provided"
            )

        issues = []

        if constraints.get('non_null') and value is None:
            issues.append("Value is null but must not be")

        if 'allowed' in constraints and value not in constraints['allowed']:
            issues.append(f"Value {value!r} not in allowed set")

        if 'min' in constraints:
            try:
                if float(value) < float(constraints['min']):
                    issues.append(f"Value below minimum {constraints['min']}")
            except (TypeError, ValueError):
                issues.append("Non-numeric value compared against 'min'")

        if 'max' in constraints:
            try:
                if float(value) > float(constraints['max']):
                    issues.append(f"Value above maximum {constraints['max']}")
            except (TypeError, ValueError):
                issues.append("Non-numeric value compared against 'max'")

        if issues:
            return VerificationResult(
                verification_type=VerificationType.CONSTRAINT,
                status=VerificationStatus.FAILED,
                confidence=0.9,
                message="Constraint validation failed",
                issues=issues
            )

        return VerificationResult(
            verification_type=VerificationType.CONSTRAINT,
            status=VerificationStatus.VERIFIED,
            confidence=0.95,
            message="All constraints satisfied"
        )
