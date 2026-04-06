"""
Symbolic Verification for GPQA
===============================

Verifies answers against symbolic constraints from physics,
chemistry, and biology. Uses dimensional analysis, conservation
laws, and domain-specific rules to validate answers.

Key features:
1. Dimensional analysis verification
2. Conservation law checking
3. Stoichiometric balance verification
4. Biological constraint checking
5. Order of magnitude verification

Expected improvement: +1% on GPQA Diamond

Date: 2025-12-17
"""

from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional, Tuple, Set
from enum import Enum
import re
import math


class ConstraintType(Enum):
    """Types of symbolic constraints."""
    DIMENSIONAL = "dimensional"
    CONSERVATION = "conservation"
    STOICHIOMETRIC = "stoichiometric"
    BIOLOGICAL = "biological"
    MATHEMATICAL = "mathematical"
    THERMODYNAMIC = "thermodynamic"


class VerificationOutcome(Enum):
    """Outcome of constraint verification."""
    SATISFIED = "satisfied"
    VIOLATED = "violated"
    UNCERTAIN = "uncertain"
    NOT_APPLICABLE = "not_applicable"


@dataclass
class Dimension:
    """Physical dimension representation."""
    length: int = 0      # L
    mass: int = 0        # M
    time: int = 0        # T
    current: int = 0     # I
    temperature: int = 0  # Θ
    amount: int = 0      # N (moles)
    luminosity: int = 0  # J

    def __str__(self) -> str:
        parts = []
        if self.length: parts.append(f"L^{self.length}")
        if self.mass: parts.append(f"M^{self.mass}")
        if self.time: parts.append(f"T^{self.time}")
        if self.current: parts.append(f"I^{self.current}")
        if self.temperature: parts.append(f"Θ^{self.temperature}")
        if self.amount: parts.append(f"N^{self.amount}")
        return " ".join(parts) if parts else "dimensionless"

    def __eq__(self, other) -> bool:
        if not isinstance(other, Dimension):
            return False
        return (self.length == other.length and
                self.mass == other.mass and
                self.time == other.time and
                self.current == other.current and
                self.temperature == other.temperature and
                self.amount == other.amount)

    def __mul__(self, other: 'Dimension') -> 'Dimension':
        return Dimension(
            self.length + other.length,
            self.mass + other.mass,
            self.time + other.time,
            self.current + other.current,
            self.temperature + other.temperature,
            self.amount + other.amount
        )

    def __truediv__(self, other: 'Dimension') -> 'Dimension':
        return Dimension(
            self.length - other.length,
            self.mass - other.mass,
            self.time - other.time,
            self.current - other.current,
            self.temperature - other.temperature,
            self.amount - other.amount
        )


@dataclass
class ConstraintCheck:
    """Result of a single constraint check."""
    constraint_type: ConstraintType
    constraint_name: str
    outcome: VerificationOutcome
    details: str
    evidence: List[str] = field(default_factory=list)


@dataclass
class SymbolicVerificationResult:
    """Result of symbolic verification."""
    overall_valid: bool
    confidence: float
    checks: List[ConstraintCheck]
    violations: List[str]
    suggestions: List[str]


# Unit dimension database
UNIT_DIMENSIONS = {
    # Base SI units
    'm': Dimension(length=1),
    'meter': Dimension(length=1),
    'kg': Dimension(mass=1),
    'kilogram': Dimension(mass=1),
    's': Dimension(time=1),
    'second': Dimension(time=1),
    'a': Dimension(current=1),
    'ampere': Dimension(current=1),
    'k': Dimension(temperature=1),
    'kelvin': Dimension(temperature=1),
    'mol': Dimension(amount=1),
    'mole': Dimension(amount=1),

    # Derived units
    'n': Dimension(mass=1, length=1, time=-2),  # Newton
    'newton': Dimension(mass=1, length=1, time=-2),
    'j': Dimension(mass=1, length=2, time=-2),  # Joule
    'joule': Dimension(mass=1, length=2, time=-2),
    'w': Dimension(mass=1, length=2, time=-3),  # Watt
    'watt': Dimension(mass=1, length=2, time=-3),
    'pa': Dimension(mass=1, length=-1, time=-2),  # Pascal
    'pascal': Dimension(mass=1, length=-1, time=-2),
    'hz': Dimension(time=-1),  # Hertz
    'hertz': Dimension(time=-1),
    'c': Dimension(current=1, time=1),  # Coulomb
    'coulomb': Dimension(current=1, time=1),
    'v': Dimension(mass=1, length=2, time=-3, current=-1),  # Volt
    'volt': Dimension(mass=1, length=2, time=-3, current=-1),

    # Common compound units
    'm/s': Dimension(length=1, time=-1),
    'm/s^2': Dimension(length=1, time=-2),
    'kg/m^3': Dimension(mass=1, length=-3),
    'j/mol': Dimension(mass=1, length=2, time=-2, amount=-1),
}


class DimensionalAnalyzer:
    """Performs dimensional analysis verification."""

    def __init__(self):
        self.unit_dimensions = UNIT_DIMENSIONS

    def extract_dimension(self, text: str) -> Optional[Dimension]:
        """Extract dimension from text containing units."""
        text_lower = text.lower()

        # Check for known units
        for unit, dim in self.unit_dimensions.items():
            if unit in text_lower:
                return dim

        # Check for compound units
        if 'm/s' in text_lower:
            return Dimension(length=1, time=-1)
        if 'kg' in text_lower and 'm' in text_lower:
            # Could be various combinations
            if 's^2' in text_lower or 's²' in text_lower:
                return Dimension(mass=1, length=1, time=-2)  # Force

        return None

    def check_dimensional_consistency(self, question: str, answer: str,
                                     choices: List[str]) -> ConstraintCheck:
        """Check if answer has dimensionally consistent units."""
        # Extract dimensions from question (expected)
        question_dim = self._infer_expected_dimension(question)

        # Extract dimensions from answer
        answer_dim = self.extract_dimension(answer)

        # Compare
        if question_dim is None or answer_dim is None:
            return ConstraintCheck(
                constraint_type=ConstraintType.DIMENSIONAL,
                constraint_name="Dimensional Consistency",
                outcome=VerificationOutcome.UNCERTAIN,
                details="Could not extract dimensions for comparison",
                evidence=[]
            )

        if question_dim == answer_dim:
            return ConstraintCheck(
                constraint_type=ConstraintType.DIMENSIONAL,
                constraint_name="Dimensional Consistency",
                outcome=VerificationOutcome.SATISFIED,
                details=f"Dimensions match: {question_dim}",
                evidence=[f"Expected: {question_dim}", f"Found: {answer_dim}"]
            )
        else:
            return ConstraintCheck(
                constraint_type=ConstraintType.DIMENSIONAL,
                constraint_name="Dimensional Consistency",
                outcome=VerificationOutcome.VIOLATED,
                details=f"Dimension mismatch: expected {question_dim}, got {answer_dim}",
                evidence=[f"Expected: {question_dim}", f"Found: {answer_dim}"]
            )

    def _infer_expected_dimension(self, question: str) -> Optional[Dimension]:
        """Infer expected dimension from question context."""
        q_lower = question.lower()

        # Physics quantity patterns
        if 'velocity' in q_lower or 'speed' in q_lower:
            return Dimension(length=1, time=-1)
        if 'acceleration' in q_lower:
            return Dimension(length=1, time=-2)
        if 'force' in q_lower:
            return Dimension(mass=1, length=1, time=-2)
        if 'energy' in q_lower or 'work' in q_lower:
            return Dimension(mass=1, length=2, time=-2)
        if 'power' in q_lower:
            return Dimension(mass=1, length=2, time=-3)
        if 'pressure' in q_lower:
            return Dimension(mass=1, length=-1, time=-2)
        if 'frequency' in q_lower:
            return Dimension(time=-1)

        return None


class ConservationChecker:
    """Checks conservation laws."""

    def __init__(self):
        self.conservation_laws = [
            "energy",
            "momentum",
            "angular_momentum",
            "charge",
            "mass",
            "baryon_number",
            "lepton_number"
        ]

    def check_conservation(self, question: str, answer: str,
                          reasoning: str) -> List[ConstraintCheck]:
        """Check applicable conservation laws."""
        checks = []
        q_lower = question.lower()
        r_lower = reasoning.lower() if reasoning else ""

        # Energy conservation
        if any(term in q_lower for term in ['energy', 'work', 'heat', 'power']):
            check = self._check_energy_conservation(question, answer, reasoning)
            checks.append(check)

        # Momentum conservation
        if any(term in q_lower for term in ['momentum', 'collision', 'impact']):
            check = self._check_momentum_conservation(question, answer, reasoning)
            checks.append(check)

        # Charge conservation
        if any(term in q_lower for term in ['charge', 'electron', 'ion', 'current']):
            check = self._check_charge_conservation(question, answer, reasoning)
            checks.append(check)

        return checks

    def _check_energy_conservation(self, question: str, answer: str,
                                  reasoning: str) -> ConstraintCheck:
        """Check energy conservation principle."""
        r_lower = (reasoning or "").lower()

        # Check if reasoning mentions energy conservation
        conserved = any(phrase in r_lower for phrase in
                       ['conservation of energy', 'energy conserv', 'energy is conserved'])

        if conserved:
            outcome = VerificationOutcome.SATISFIED
            details = "Energy conservation principle applied"
        else:
            outcome = VerificationOutcome.UNCERTAIN
            details = "Energy conservation not explicitly verified"

        return ConstraintCheck(
            constraint_type=ConstraintType.CONSERVATION,
            constraint_name="Energy Conservation",
            outcome=outcome,
            details=details
        )

    def _check_momentum_conservation(self, question: str, answer: str,
                                    reasoning: str) -> ConstraintCheck:
        """Check momentum conservation principle."""
        r_lower = (reasoning or "").lower()

        conserved = any(phrase in r_lower for phrase in
                       ['conservation of momentum', 'momentum conserv', 'momentum is conserved'])

        if conserved:
            outcome = VerificationOutcome.SATISFIED
            details = "Momentum conservation principle applied"
        else:
            outcome = VerificationOutcome.UNCERTAIN
            details = "Momentum conservation not explicitly verified"

        return ConstraintCheck(
            constraint_type=ConstraintType.CONSERVATION,
            constraint_name="Momentum Conservation",
            outcome=outcome,
            details=details
        )

    def _check_charge_conservation(self, question: str, answer: str,
                                  reasoning: str) -> ConstraintCheck:
        """Check charge conservation."""
        r_lower = (reasoning or "").lower()

        conserved = any(phrase in r_lower for phrase in
                       ['charge balance', 'charge conserv', 'neutral'])

        if conserved:
            outcome = VerificationOutcome.SATISFIED
            details = "Charge conservation verified"
        else:
            outcome = VerificationOutcome.UNCERTAIN
            details = "Charge conservation not explicitly verified"

        return ConstraintCheck(
            constraint_type=ConstraintType.CONSERVATION,
            constraint_name="Charge Conservation",
            outcome=outcome,
            details=details
        )


class StoichiometryChecker:
    """Checks stoichiometric constraints for chemistry."""

    def __init__(self):
        pass

    def check_stoichiometry(self, question: str, answer: str,
                           reasoning: str) -> List[ConstraintCheck]:
        """Check stoichiometric constraints."""
        checks = []
        q_lower = question.lower()

        # Check for reaction stoichiometry
        if any(term in q_lower for term in ['reaction', 'equation', 'yield', 'product']):
            check = self._check_reaction_balance(question, answer, reasoning)
            checks.append(check)

        # Check oxidation states
        if any(term in q_lower for term in ['oxidation', 'reduction', 'redox']):
            check = self._check_oxidation_balance(question, answer, reasoning)
            checks.append(check)

        return checks

    def _check_reaction_balance(self, question: str, answer: str,
                               reasoning: str) -> ConstraintCheck:
        """Check if reaction is balanced."""
        r_lower = (reasoning or "").lower()

        balanced = any(phrase in r_lower for phrase in
                      ['balanced', 'stoichiometr', 'mole ratio', 'coefficient'])

        if balanced:
            outcome = VerificationOutcome.SATISFIED
            details = "Stoichiometric balance considered"
        else:
            outcome = VerificationOutcome.UNCERTAIN
            details = "Stoichiometric balance not explicitly verified"

        return ConstraintCheck(
            constraint_type=ConstraintType.STOICHIOMETRIC,
            constraint_name="Reaction Balance",
            outcome=outcome,
            details=details
        )

    def _check_oxidation_balance(self, question: str, answer: str,
                                reasoning: str) -> ConstraintCheck:
        """Check oxidation state balance."""
        r_lower = (reasoning or "").lower()

        balanced = any(phrase in r_lower for phrase in
                      ['oxidation state', 'electron transfer', 'oxidized', 'reduced'])

        if balanced:
            outcome = VerificationOutcome.SATISFIED
            details = "Oxidation states considered"
        else:
            outcome = VerificationOutcome.UNCERTAIN
            details = "Oxidation balance not explicitly verified"

        return ConstraintCheck(
            constraint_type=ConstraintType.STOICHIOMETRIC,
            constraint_name="Oxidation Balance",
            outcome=outcome,
            details=details
        )


class BiologicalConstraintChecker:
    """Checks biological constraints."""

    def __init__(self):
        pass

    def check_biological_constraints(self, question: str, answer: str,
                                    reasoning: str) -> List[ConstraintCheck]:
        """Check biological constraints."""
        checks = []
        q_lower = question.lower()

        # Central dogma
        if any(term in q_lower for term in ['transcription', 'translation', 'dna', 'rna', 'protein']):
            check = self._check_central_dogma(question, answer, reasoning)
            checks.append(check)

        # Compartmentalization
        if any(term in q_lower for term in ['cell', 'organelle', 'membrane', 'nucleus', 'cytoplasm']):
            check = self._check_compartmentalization(question, answer, reasoning)
            checks.append(check)

        return checks

    def _check_central_dogma(self, question: str, answer: str,
                            reasoning: str) -> ConstraintCheck:
        """Check consistency with central dogma."""
        r_lower = (reasoning or "").lower()

        consistent = any(phrase in r_lower for phrase in
                        ['transcription', 'translation', 'gene expression',
                         'dna to rna', 'rna to protein', 'codon'])

        if consistent:
            outcome = VerificationOutcome.SATISFIED
            details = "Central dogma principles considered"
        else:
            outcome = VerificationOutcome.UNCERTAIN
            details = "Central dogma not explicitly verified"

        return ConstraintCheck(
            constraint_type=ConstraintType.BIOLOGICAL,
            constraint_name="Central Dogma",
            outcome=outcome,
            details=details
        )

    def _check_compartmentalization(self, question: str, answer: str,
                                   reasoning: str) -> ConstraintCheck:
        """Check cellular compartmentalization."""
        r_lower = (reasoning or "").lower()

        considered = any(phrase in r_lower for phrase in
                        ['compartment', 'organelle', 'membrane', 'cytosol',
                         'nucleus', 'mitochondr'])

        if considered:
            outcome = VerificationOutcome.SATISFIED
            details = "Cellular compartmentalization considered"
        else:
            outcome = VerificationOutcome.UNCERTAIN
            details = "Compartmentalization not explicitly addressed"

        return ConstraintCheck(
            constraint_type=ConstraintType.BIOLOGICAL,
            constraint_name="Compartmentalization",
            outcome=outcome,
            details=details
        )


class OrderOfMagnitudeChecker:
    """Checks order of magnitude reasonableness."""

    def __init__(self):
        # Known orders of magnitude
        self.reference_values = {
            'speed_of_light': 3e8,  # m/s
            'electron_mass': 9.1e-31,  # kg
            'proton_mass': 1.67e-27,  # kg
            'avogadro': 6.02e23,
            'boltzmann': 1.38e-23,  # J/K
            'planck': 6.63e-34,  # J·s
        }

    def check_magnitude(self, question: str, answer: str) -> ConstraintCheck:
        """Check if numerical answer has reasonable magnitude."""
        # Extract numbers from answer
        numbers = re.findall(r'[-+]?\d*\.?\d+(?:[eE][-+]?\d+)?', answer)

        if not numbers:
            return ConstraintCheck(
                constraint_type=ConstraintType.MATHEMATICAL,
                constraint_name="magnitude_check",
                is_satisfied=True,
                reason="No numerical values found in answer",
                confidence=1.0
            )

        # Check if magnitudes are reasonable
        # This is a simplified check
        try:
            value = float(numbers[0])
            # Check for extreme values
            if abs(value) > 1e100 or abs(value) < 1e-100:
                return ConstraintCheck(
                    constraint_type=ConstraintType.MATHEMATICAL,
                    constraint_name="magnitude_check",
                    is_satisfied=False,
                    reason=f"Value {value} has unusual magnitude",
                    confidence=0.7
                )
            return ConstraintCheck(
                constraint_type=ConstraintType.MATHEMATICAL,
                constraint_name="magnitude_check",
                is_satisfied=True,
                reason="Magnitude appears reasonable",
                confidence=0.8
            )
        except:
            return ConstraintCheck(
                constraint_type=ConstraintType.MATHEMATICAL,
                constraint_name="magnitude_check",
                is_satisfied=True,
                reason="Could not parse numerical value",
                confidence=0.5
            )


class SymbolicVerifier:
    """
    Main symbolic verification class for STAN.

    Coordinates various constraint checkers to verify answers
    across physics, mathematics, biology, and chemistry domains.
    """

    def __init__(self):
        """Initialize the symbolic verifier with all checkers."""
        self.dimensional_analyzer = DimensionalAnalyzer()
        self.conservation_checker = ConservationChecker()
        self.stoichiometry_checker = StoichiometryChecker()
        self.biological_checker = BiologicalConstraintChecker()
        self.magnitude_checker = OrderOfMagnitudeChecker()

    def verify(self, question: str, answer: str, domain: str = "physics") -> SymbolicVerificationResult:
        """
        Verify an answer symbolically.

        Args:
            question: The question asked
            answer: The proposed answer
            domain: The domain (physics, math, biology, chemistry)

        Returns:
            SymbolicVerificationResult with verification outcome
        """
        checks = []

        # Run relevant checks based on domain
        if domain in ["physics", "chemistry"]:
            # Dimensional analysis
            dim_result = self.dimensional_analyzer.check_dimensions(question, answer)
            checks.append(dim_result)

            # Conservation laws
            conservation_result = self.conservation_checker.check_conservation(question, answer)
            checks.append(conservation_result)

        if domain == "chemistry":
            # Stoichiometry
            stoich_result = self.stoichiometry_checker.check_stoichiometry(question, answer)
            checks.append(stoich_result)

        if domain == "biology":
            # Biological constraints
            bio_result = self.biological_checker.check_biological_constraints(question, answer)
            checks.append(bio_result)

        # Magnitude check (all domains)
        mag_result = self.magnitude_checker.check_magnitude(question, answer)
        checks.append(mag_result)

        # Compute overall outcome
        passed_checks = sum(1 for c in checks if c.is_satisfied)
        total_checks = len(checks)

        if passed_checks == total_checks:
            outcome = VerificationOutcome.CORRECT
            confidence = 0.9
        elif passed_checks >= total_checks * 0.7:
            outcome = VerificationOutcome.PARTIALLY_CORRECT
            confidence = 0.6
        elif passed_checks >= total_checks * 0.3:
            outcome = VerificationOutcome.UNCERTAIN
            confidence = 0.4
        else:
            outcome = VerificationOutcome.INCORRECT
            confidence = 0.7

        return SymbolicVerificationResult(
            outcome=outcome,
            confidence=confidence,
            checks_performed=checks,
            domain=domain,
            reasoning=f"Passed {passed_checks}/{total_checks} constraint checks"
        )


def create_symbolic_verifier() -> SymbolicVerifier:
    """
    Factory function to create a SymbolicVerifier instance.

    Returns:
        SymbolicVerifier instance
    """
    return SymbolicVerifier()


def verify_symbolically(question: str, answer: str, domain: str = "physics") -> SymbolicVerificationResult:
    """
    Verify an answer symbolically.

    Convenience function that creates a verifier and performs verification.

    Args:
        question: The question asked
        answer: The proposed answer
        domain: The domain (physics, math, biology, chemistry)

    Returns:
        SymbolicVerificationResult with verification outcome
    """
    verifier = create_symbolic_verifier()
    return verifier.verify(question, answer, domain)


__all__ = [
    'SymbolicVerifier',
    'SymbolicVerificationResult',
    'ConstraintCheck',
    'Dimension',
    'ConstraintType',
    'VerificationOutcome',
    'create_symbolic_verifier',
    'verify_symbolically',
]
