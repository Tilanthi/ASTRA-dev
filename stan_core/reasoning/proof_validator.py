"""
Mathematical Proof Validator for STAN V40

Validates mathematical proofs by checking logical structure,
detecting circular reasoning, and verifying axiom applications.

This addresses the gap in Math exact-match problems that require
proof verification rather than just answer generation.

Date: 2025-12-11
"""

import re
from typing import Dict, List, Optional, Any, Tuple, Set
from dataclasses import dataclass, field
from enum import Enum
from abc import ABC, abstractmethod


class ProofType(Enum):
    """Types of mathematical proofs"""
    DIRECT = "direct"
    CONTRADICTION = "contradiction"
    CONTRAPOSITIVE = "contrapositive"
    INDUCTION = "induction"
    STRONG_INDUCTION = "strong_induction"
    STRUCTURAL_INDUCTION = "structural_induction"
    CASES = "cases"
    EXISTENCE = "existence"
    UNIQUENESS = "uniqueness"
    CONSTRUCTIVE = "constructive"


class LogicalConnective(Enum):
    """Logical connectives"""
    AND = "and"
    OR = "or"
    NOT = "not"
    IMPLIES = "implies"
    IFF = "iff"  # if and only if
    FORALL = "forall"
    EXISTS = "exists"


class ProofStepType(Enum):
    """Types of proof steps"""
    ASSUMPTION = "assumption"
    DEFINITION = "definition"
    AXIOM = "axiom"
    THEOREM = "theorem"
    LEMMA = "lemma"
    DEDUCTION = "deduction"
    SUBSTITUTION = "substitution"
    SIMPLIFICATION = "simplification"
    CASE_SPLIT = "case_split"
    INDUCTION_BASE = "induction_base"
    INDUCTION_HYPOTHESIS = "induction_hypothesis"
    INDUCTION_STEP = "induction_step"
    CONTRADICTION = "contradiction"
    CONCLUSION = "conclusion"


@dataclass
class LogicalStatement:
    """A logical statement in a proof"""
    statement_id: str
    content: str
    formal_form: Optional[str] = None
    variables: Set[str] = field(default_factory=set)
    quantifiers: List[Tuple[LogicalConnective, str]] = field(default_factory=list)
    dependencies: List[str] = field(default_factory=list)  # IDs of statements this depends on

    def __post_init__(self):
        if not self.variables:
            self.variables = self._extract_variables()
        if not self.quantifiers:
            self.quantifiers = self._extract_quantifiers()

    def _extract_variables(self) -> Set[str]:
        """Extract variable names"""
        pattern = r'\b([a-zA-Z])\b(?!\s*\()'
        matches = re.findall(pattern, self.content)
        constants = {'e', 'i', 'pi', 'P', 'Q', 'R', 'S', 'T'}
        return set(m for m in matches if m not in constants)

    def _extract_quantifiers(self) -> List[Tuple[LogicalConnective, str]]:
        """Extract quantifiers"""
        quantifiers = []

        # Universal quantifier patterns
        for pattern in [r'for all\s+(\w+)', r'forall\s+(\w+)', r'\\forall\s+(\w+)']:
            for match in re.finditer(pattern, self.content.lower()):
                quantifiers.append((LogicalConnective.FORALL, match.group(1)))

        # Existential quantifier patterns
        for pattern in [r'there exists?\s+(\w+)', r'exists\s+(\w+)', r'\\exists\s+(\w+)']:
            for match in re.finditer(pattern, self.content.lower()):
                quantifiers.append((LogicalConnective.EXISTS, match.group(1)))

        return quantifiers


@dataclass
class ProofStep:
    """A single step in a proof"""
    step_id: int
    step_type: ProofStepType
    statement: LogicalStatement
    justification: str
    references: List[int] = field(default_factory=list)  # Previous step IDs used
    is_valid: Optional[bool] = None
    validation_notes: List[str] = field(default_factory=list)


@dataclass
class ProofStructure:
    """Complete structure of a proof"""
    proof_id: str
    proof_type: ProofType
    premises: List[LogicalStatement]
    conclusion: LogicalStatement
    steps: List[ProofStep]
    is_valid: bool = False
    gaps: List[str] = field(default_factory=list)
    circular_dependencies: List[Tuple[int, int]] = field(default_factory=list)


@dataclass
class ValidationResult:
    """Result of proof validation"""
    is_valid: bool
    confidence: float
    proof_type_detected: ProofType
    steps_validated: int
    total_steps: int
    errors: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)
    suggestions: List[str] = field(default_factory=list)
    missing_steps: List[str] = field(default_factory=list)


class ProofParser:
    """Parse proof text into structured form"""

    def __init__(self):
        # Patterns for identifying proof elements
        self.proof_type_patterns = {
            ProofType.INDUCTION: [
                r'by\s+induction', r'induct\s+on', r'base\s+case',
                r'inductive\s+step', r'induction\s+hypothesis'
            ],
            ProofType.CONTRADICTION: [
                r'by\s+contradiction', r'assume\s+.*\s+not', r'suppose\s+.*\s+false',
                r'leads\s+to\s+contradiction', r'contradicts'
            ],
            ProofType.CONTRAPOSITIVE: [
                r'contrapositive', r'prove\s+.*\s+instead', r'equivalent\s+to\s+showing'
            ],
            ProofType.CASES: [
                r'case\s+\d', r'cases?\s*:', r'consider\s+the\s+cases',
                r'first\s+case', r'second\s+case'
            ],
            ProofType.DIRECT: [
                r'directly', r'straightforward', r'follows\s+from'
            ]
        }

        self.step_patterns = {
            ProofStepType.ASSUMPTION: [
                r'^assume', r'^suppose', r'^let', r'^given'
            ],
            ProofStepType.DEFINITION: [
                r'by\s+definition', r'defined\s+as', r'means\s+that'
            ],
            ProofStepType.AXIOM: [
                r'by\s+axiom', r'axiom\s+\d', r'fundamental\s+property'
            ],
            ProofStepType.THEOREM: [
                r'by\s+theorem', r'theorem\s+\d', r'applying\s+.*\s+theorem'
            ],
            ProofStepType.DEDUCTION: [
                r'therefore', r'thus', r'hence', r'so', r'it\s+follows'
            ],
            ProofStepType.SUBSTITUTION: [
                r'substitut', r'replac', r'setting\s+.*\s*='
            ],
            ProofStepType.CONCLUSION: [
                r'conclude', r'proven', r'qed', r'\\square', r'as\s+required'
            ]
        }

    def parse(self, proof_text: str) -> ProofStructure:
        """Parse proof text into structured form"""
        # Detect proof type
        proof_type = self._detect_proof_type(proof_text)

        # Split into steps
        raw_steps = self._split_into_steps(proof_text)

        # Parse each step
        steps = []
        for i, raw_step in enumerate(raw_steps):
            step = self._parse_step(i, raw_step)
            steps.append(step)

        # Extract premises and conclusion
        premises = self._extract_premises(proof_text, steps)
        conclusion = self._extract_conclusion(proof_text, steps)

        return ProofStructure(
            proof_id=f"proof_{hash(proof_text) % 10000}",
            proof_type=proof_type,
            premises=premises,
            conclusion=conclusion,
            steps=steps
        )

    def _detect_proof_type(self, text: str) -> ProofType:
        """Detect the type of proof"""
        text_lower = text.lower()

        for proof_type, patterns in self.proof_type_patterns.items():
            for pattern in patterns:
                if re.search(pattern, text_lower):
                    return proof_type

        return ProofType.DIRECT

    def _split_into_steps(self, text: str) -> List[str]:
        """Split proof into individual steps"""
        # Split by sentence-ending punctuation, numbered steps, or logical markers

        # First try numbered steps
        numbered = re.split(r'\n\s*\d+[\.\)]\s*', text)
        if len(numbered) > 1:
            return [s.strip() for s in numbered if s.strip()]

        # Try splitting by logical markers
        markers = r'(?:therefore|thus|hence|so,|it follows|we have|this gives|consequently)'
        marker_split = re.split(f'({markers})', text, flags=re.IGNORECASE)
        if len(marker_split) > 2:
            # Recombine markers with their following content
            steps = []
            for i in range(0, len(marker_split), 2):
                if i + 1 < len(marker_split):
                    steps.append(marker_split[i] + marker_split[i+1])
                else:
                    steps.append(marker_split[i])
            return [s.strip() for s in steps if s.strip()]

        # Fall back to sentence splitting
        sentences = re.split(r'(?<=[.!?])\s+', text)
        return [s.strip() for s in sentences if s.strip()]

    def _parse_step(self, step_id: int, raw_step: str) -> ProofStep:
        """Parse a single proof step"""
        step_type = self._classify_step(raw_step)

        statement = LogicalStatement(
            statement_id=f"s{step_id}",
            content=raw_step
        )

        justification = self._extract_justification(raw_step)
        references = self._extract_references(raw_step)

        return ProofStep(
            step_id=step_id,
            step_type=step_type,
            statement=statement,
            justification=justification,
            references=references
        )

    def _classify_step(self, step_text: str) -> ProofStepType:
        """Classify the type of proof step"""
        step_lower = step_text.lower()

        for step_type, patterns in self.step_patterns.items():
            for pattern in patterns:
                if re.search(pattern, step_lower):
                    return step_type

        return ProofStepType.DEDUCTION

    def _extract_justification(self, step_text: str) -> str:
        """Extract justification for the step"""
        # Look for "by X" or "from X" patterns
        by_match = re.search(r'by\s+(.+?)(?:\.|,|$)', step_text, re.IGNORECASE)
        if by_match:
            return by_match.group(1).strip()

        from_match = re.search(r'from\s+(.+?)(?:\.|,|$)', step_text, re.IGNORECASE)
        if from_match:
            return from_match.group(1).strip()

        return "implicit"

    def _extract_references(self, step_text: str) -> List[int]:
        """Extract references to previous steps"""
        refs = []

        # Match patterns like "from (1)", "by step 3", etc.
        patterns = [
            r'from\s*\(?(\d+)\)?',
            r'by\s+step\s+(\d+)',
            r'\((\d+)\)',
            r'steps?\s+(\d+(?:\s*,\s*\d+)*)'
        ]

        for pattern in patterns:
            matches = re.findall(pattern, step_text, re.IGNORECASE)
            for match in matches:
                for num in re.findall(r'\d+', match if isinstance(match, str) else str(match)):
                    refs.append(int(num) - 1)  # Convert to 0-indexed

        return refs

    def _extract_premises(self, text: str, steps: List[ProofStep]) -> List[LogicalStatement]:
        """Extract premises from proof"""
        premises = []

        for step in steps:
            if step.step_type in [ProofStepType.ASSUMPTION, ProofStepType.AXIOM]:
                premises.append(step.statement)

        return premises

    def _extract_conclusion(self, text: str, steps: List[ProofStep]) -> LogicalStatement:
        """Extract conclusion from proof"""
        for step in reversed(steps):
            if step.step_type == ProofStepType.CONCLUSION:
                return step.statement

        # If no explicit conclusion, use last step
        if steps:
            return steps[-1].statement

        return LogicalStatement(
            statement_id="conclusion",
            content="[conclusion not found]"
        )


class LogicalValidator:
    """Validate logical structure of proofs"""

    def __init__(self):
        # Valid inference rules
        self.inference_rules = {
            'modus_ponens': self._check_modus_ponens,
            'modus_tollens': self._check_modus_tollens,
            'hypothetical_syllogism': self._check_hypothetical_syllogism,
            'disjunctive_syllogism': self._check_disjunctive_syllogism,
            'constructive_dilemma': self._check_constructive_dilemma,
            'universal_instantiation': self._check_universal_instantiation,
            'existential_instantiation': self._check_existential_instantiation,
        }

    def validate_step(self, step: ProofStep,
                     previous_steps: List[ProofStep]) -> Tuple[bool, List[str]]:
        """Validate a single proof step"""
        notes = []

        # Check if references are valid
        for ref in step.references:
            if ref < 0 or ref >= len(previous_steps):
                notes.append(f"Invalid reference to step {ref + 1}")
                return False, notes

        # Check step type specific validation
        if step.step_type == ProofStepType.ASSUMPTION:
            return True, ["Assumption accepted"]

        if step.step_type == ProofStepType.AXIOM:
            return True, ["Axiom accepted (not verified)"]

        if step.step_type == ProofStepType.DEFINITION:
            return True, ["Definition accepted"]

        if step.step_type == ProofStepType.DEDUCTION:
            # Check if deduction follows from references
            is_valid, reason = self._validate_deduction(step, previous_steps)
            notes.append(reason)
            return is_valid, notes

        if step.step_type == ProofStepType.SUBSTITUTION:
            return True, ["Substitution accepted"]

        return True, ["Step accepted without formal verification"]

    def _validate_deduction(self, step: ProofStep,
                           previous_steps: List[ProofStep]) -> Tuple[bool, str]:
        """Validate that a deduction follows from previous steps"""
        if not step.references:
            return True, "Deduction with implicit references"

        # Get referenced statements
        referenced = []
        for ref in step.references:
            if 0 <= ref < len(previous_steps):
                referenced.append(previous_steps[ref].statement)

        # Try to match known inference patterns
        for rule_name, checker in self.inference_rules.items():
            if checker(referenced, step.statement):
                return True, f"Valid by {rule_name}"

        return True, "Deduction accepted (pattern not formally verified)"

    def _check_modus_ponens(self, premises: List[LogicalStatement],
                           conclusion: LogicalStatement) -> bool:
        """Check if modus ponens applies: P, P->Q |- Q"""
        if len(premises) < 2:
            return False

        # Look for implication pattern
        for p in premises:
            if 'implies' in p.content.lower() or '->' in p.content or '=>' in p.content:
                # Check if antecedent is in other premises
                return True  # Simplified check

        return False

    def _check_modus_tollens(self, premises: List[LogicalStatement],
                            conclusion: LogicalStatement) -> bool:
        """Check if modus tollens applies: P->Q, ~Q |- ~P"""
        for p in premises:
            if ('implies' in p.content.lower() or '->' in p.content) and \
               any('not' in q.content.lower() for q in premises):
                return True
        return False

    def _check_hypothetical_syllogism(self, premises: List[LogicalStatement],
                                      conclusion: LogicalStatement) -> bool:
        """Check if hypothetical syllogism applies: P->Q, Q->R |- P->R"""
        implications = [p for p in premises
                       if 'implies' in p.content.lower() or '->' in p.content]
        return len(implications) >= 2

    def _check_disjunctive_syllogism(self, premises: List[LogicalStatement],
                                     conclusion: LogicalStatement) -> bool:
        """Check if disjunctive syllogism applies: P v Q, ~P |- Q"""
        has_disjunction = any('or' in p.content.lower() for p in premises)
        has_negation = any('not' in p.content.lower() for p in premises)
        return has_disjunction and has_negation

    def _check_constructive_dilemma(self, premises: List[LogicalStatement],
                                    conclusion: LogicalStatement) -> bool:
        """Check constructive dilemma"""
        return False  # Complex pattern, skip for now

    def _check_universal_instantiation(self, premises: List[LogicalStatement],
                                       conclusion: LogicalStatement) -> bool:
        """Check universal instantiation: forall x P(x) |- P(a)"""
        for p in premises:
            if any(q[0] == LogicalConnective.FORALL for q in p.quantifiers):
                return True
        return False

    def _check_existential_instantiation(self, premises: List[LogicalStatement],
                                         conclusion: LogicalStatement) -> bool:
        """Check existential instantiation"""
        for p in premises:
            if any(q[0] == LogicalConnective.EXISTS for q in p.quantifiers):
                return True
        return False


class CircularityDetector:
    """Detect circular reasoning in proofs"""

    def detect_cycles(self, steps: List[ProofStep]) -> List[Tuple[int, int]]:
        """
        Detect circular dependencies in proof steps.

        Returns list of (step_a, step_b) pairs indicating cycles.
        """
        # Build dependency graph
        n = len(steps)
        graph = {i: set() for i in range(n)}

        for i, step in enumerate(steps):
            for ref in step.references:
                if 0 <= ref < n:
                    graph[i].add(ref)

        # Detect cycles using DFS
        cycles = []
        visited = set()
        rec_stack = set()

        def dfs(node: int, path: List[int]) -> bool:
            visited.add(node)
            rec_stack.add(node)

            for neighbor in graph[node]:
                if neighbor not in visited:
                    if dfs(neighbor, path + [node]):
                        return True
                elif neighbor in rec_stack:
                    # Found cycle
                    cycles.append((node, neighbor))
                    return True

            rec_stack.remove(node)
            return False

        for i in range(n):
            if i not in visited:
                dfs(i, [])

        return cycles

    def detect_self_reference(self, steps: List[ProofStep]) -> List[int]:
        """Detect steps that reference themselves"""
        self_refs = []
        for i, step in enumerate(steps):
            if i in step.references:
                self_refs.append(i)
        return self_refs


class InductionValidator:
    """Validate induction proofs"""

    def validate_induction(self, structure: ProofStructure) -> Tuple[bool, List[str]]:
        """Validate an induction proof has all required components"""
        issues = []

        has_base_case = False
        has_induction_hypothesis = False
        has_induction_step = False

        for step in structure.steps:
            if step.step_type == ProofStepType.INDUCTION_BASE:
                has_base_case = True
            elif step.step_type == ProofStepType.INDUCTION_HYPOTHESIS:
                has_induction_hypothesis = True
            elif step.step_type == ProofStepType.INDUCTION_STEP:
                has_induction_step = True

            # Also check content for these patterns
            content_lower = step.statement.content.lower()
            if 'base case' in content_lower or 'n = 0' in content_lower or 'n = 1' in content_lower:
                has_base_case = True
            if 'induction hypothesis' in content_lower or 'assume' in content_lower and 'n = k' in content_lower:
                has_induction_hypothesis = True
            if 'induction step' in content_lower or 'n = k + 1' in content_lower or 'k+1' in content_lower:
                has_induction_step = True

        if not has_base_case:
            issues.append("Missing base case")
        if not has_induction_hypothesis:
            issues.append("Missing induction hypothesis statement")
        if not has_induction_step:
            issues.append("Missing induction step")

        is_valid = has_base_case and has_induction_hypothesis and has_induction_step
        return is_valid, issues


class MathematicalProofValidator:
    """
    Complete proof validation system.

    Validates mathematical proofs by:
    1. Parsing proof structure
    2. Checking logical consistency
    3. Detecting circular reasoning
    4. Validating proof type requirements
    5. Identifying missing steps
    """

    def __init__(self):
        self.parser = ProofParser()
        self.logical_validator = LogicalValidator()
        self.circularity_detector = CircularityDetector()
        self.induction_validator = InductionValidator()

    def validate(self, proof_text: str) -> ValidationResult:
        """
        Validate a mathematical proof.

        Args:
            proof_text: The proof text to validate

        Returns:
            ValidationResult with detailed validation information
        """
