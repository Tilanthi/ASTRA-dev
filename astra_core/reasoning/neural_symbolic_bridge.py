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
Neural-Symbolic Bridge: Fuse LLM Breadth with Symbolic Rigor

This module implements bidirectional translation between neural (LLM)
and symbolic (V36) representations.

Key Features:
- Neural-to-symbolic translation
- Symbolic verification of LLM outputs
- LLM-augmented symbolic reasoning
- Hybrid generation with constrained LLM proposals
- V40: Mathematical expression parsing (LaTeX, notation)

Why This Matters for AGI:
- Combines LLM creativity with symbolic rigor
- Enables verification of LLM reasoning
- Provides structured guidance for LLM exploration

Date: 2025-12-11
Version: 40.0
"""

import numpy as np
from typing import Dict, List, Optional, Any, Callable, Tuple, Set
from dataclasses import dataclass, field
from enum import Enum
from abc import ABC, abstractmethod
import json
import re
from collections import defaultdict


class SymbolicType(Enum):
    """Types of symbolic structures"""
    CONSTRAINT = "constraint"
    RELATION = "relation"
    ENTITY = "entity"
    RULE = "rule"
    TEMPLATE = "template"
    THEORY = "theory"


class VerificationStatus(Enum):
    """Status of verification"""
    VERIFIED = "verified"
    VIOLATED = "violated"
    PARTIAL = "partial"
    UNKNOWN = "unknown"


@dataclass
class SymbolicStructure:
    """A symbolic structure extracted or verified"""
    structure_id: str
    structure_type: SymbolicType
    content: Dict[str, Any]

    # Formal representation
    predicates: List[str]
    relations: List[Tuple[str, str, str]]  # (subject, relation, object)
    constraints: List[str]

    # Metadata
    source: str = "neural"  # 'neural', 'symbolic', 'hybrid'
    confidence: float = 0.5
    verification_status: VerificationStatus = VerificationStatus.UNKNOWN

    def to_dict(self) -> Dict:
        return {
            'structure_id': self.structure_id,
            'type': self.structure_type.value,
            'content': self.content,
            'predicates': self.predicates,
            'relations': self.relations,
            'constraints': self.constraints,
            'source': self.source,
            'confidence': self.confidence,
            'verification_status': self.verification_status.value
        }


@dataclass
class NeuralProposal:
    """A proposal from neural (LLM) reasoning"""
    proposal_id: str
    raw_text: str
    extracted_claims: List[str]
    extracted_entities: List[str]
    extracted_relations: List[Tuple[str, str, str]]

    # Quality metrics
    coherence_score: float = 0.5
    specificity_score: float = 0.5
    relevance_score: float = 0.5

    # Verification
    symbolic_structure: Optional[SymbolicStructure] = None
    verification_result: Optional[Dict] = None

    def to_dict(self) -> Dict:
        return {
            'proposal_id': self.proposal_id,
            'raw_text': self.raw_text,
            'claims': self.extracted_claims,
            'entities': self.extracted_entities,
            'relations': self.relations,
            'coherence': self.coherence_score,
            'specificity': self.specificity_score,
            'relevance': self.relevance_score
        }


@dataclass
class HybridResult:
    """Result of hybrid neural-symbolic reasoning"""
    query: str
    neural_proposals: List[NeuralProposal]
    verified_proposals: List[NeuralProposal]
    symbolic_refinements: List[SymbolicStructure]
    final_answer: str
    confidence: float
    reasoning_trace: List[str]

    def to_dict(self) -> Dict:
        return {
            'query': self.query,
            'n_proposals': len(self.neural_proposals),
            'n_verified': len(self.verified_proposals),
            'n_refinements': len(self.symbolic_refinements),
            'final_answer': self.final_answer,
            'confidence': self.confidence,
            'trace': self.reasoning_trace
        }


class NeuralToSymbolicTranslator:
    """Translate neural (LLM) outputs to symbolic structures"""

    def __init__(self):
        # Patterns for extraction
        self.entity_patterns = [
            r'\b([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)\b',  # Proper nouns
            r'the\s+([a-z]+(?:\s+[a-z]+)*)',  # "the X"
            r'a\s+([a-z]+)',  # "a X"
        ]

        self.relation_patterns = [
            (r'(\w+)\s+causes\s+(\w+)', 'causes'),
            (r'(\w+)\s+leads\s+to\s+(\w+)', 'leads_to'),
            (r'(\w+)\s+is\s+a\s+type\s+of\s+(\w+)', 'is_a'),
            (r'(\w+)\s+contains\s+(\w+)', 'contains'),
            (r'(\w+)\s+depends\s+on\s+(\w+)', 'depends_on'),
            (r'(\w+)\s+produces\s+(\w+)', 'produces'),
            (r'(\w+)\s+affects\s+(\w+)', 'affects'),
            (r'if\s+(\w+)\s+then\s+(\w+)', 'implies'),
        ]

        self.constraint_patterns = [
            r'must\s+not\s+(.*?)(?:\.|$)',
            r'cannot\s+(.*?)(?:\.|$)',
            r'should\s+always\s+(.*?)(?:\.|$)',
            r'requires\s+(.*?)(?:\.|$)',
        ]

    def translate(self, text: str) -> SymbolicStructure:
        """
        Translate neural text to symbolic structure.

        Args:
            text: Raw LLM output text

        Returns:
            Extracted SymbolicStructure
        """
        # Extract entities
        entities = self._extract_entities(text)

        # Extract relations
        relations = self._extract_relations(text)

        # Extract constraints
        constraints = self._extract_constraints(text)

        # Build predicates
        predicates = self._build_predicates(entities, relations)

        # Determine structure type
        if constraints:
            struct_type = SymbolicType.CONSTRAINT
        elif relations:
            struct_type = SymbolicType.RELATION
        else:
            struct_type = SymbolicType.ENTITY

        return SymbolicStructure(
            structure_id=f"neural_to_sym_{hash(text) % 10000}",
            structure_type=struct_type,
            content={'original_text': text},
            predicates=predicates,
            relations=relations,
            constraints=constraints,
            source='neural',
            confidence=self._estimate_confidence(text, entities, relations)
        )

    def _extract_entities(self, text: str) -> List[str]:
        """Extract entities from text"""
        entities = set()

        for pattern in self.entity_patterns:
            matches = re.findall(pattern, text)
            for match in matches:
                if isinstance(match, tuple):
                    entities.add(match[0].lower())
                else:
                    entities.add(match.lower())

        # Filter common words
        common_words = {'the', 'a', 'an', 'this', 'that', 'it', 'is', 'are', 'was', 'were'}
        entities = {e for e in entities if e not in common_words and len(e) > 2}

        return list(entities)

    def _extract_relations(self, text: str) -> List[Tuple[str, str, str]]:
        """Extract relations from text"""
        relations = []

        text_lower = text.lower()
        for pattern, relation_type in self.relation_patterns:
            matches = re.findall(pattern, text_lower)
            for match in matches:
                if len(match) >= 2:
                    relations.append((match[0], relation_type, match[1]))

        return relations

    def _extract_constraints(self, text: str) -> List[str]:
        """Extract constraints from text"""
        constraints = []

        text_lower = text.lower()
        for pattern in self.constraint_patterns:
            matches = re.findall(pattern, text_lower)
            constraints.extend(matches)

        return constraints

    def _build_predicates(self, entities: List[str],
                          relations: List[Tuple[str, str, str]]) -> List[str]:
        """Build predicate list from entities and relations"""
        predicates = []

        # Entity predicates
        for entity in entities:
            predicates.append(f"entity({entity})")

        # Relation predicates
        for subj, rel, obj in relations:
            predicates.append(f"{rel}({subj}, {obj})")

        return predicates

    def _estimate_confidence(self, text: str, entities: List[str],
                             relations: List[Tuple[str, str, str]]) -> float:
        """Estimate confidence in extraction"""
        confidence = 0.5

        # More structure = higher confidence
        if entities:
            confidence += 0.1 * min(len(entities) / 5, 1.0)

        if relations:
            confidence += 0.2 * min(len(relations) / 3, 1.0)

        # Length check - too short or too long reduces confidence
        words = text.split()
        if 10 < len(words) < 500:
            confidence += 0.1

        return min(0.95, confidence)


class MathematicalExpressionTranslator:
    """
    V40: Translate mathematical expressions between formats.

    Handles LaTeX, Unicode math symbols, and text notation,
    converting to symbolic form for verification and manipulation.
    """

    def __init__(self):
        # LaTeX to Python/symbolic mappings
        self.latex_to_python = {
            r'\\frac{(.+?)}{(.+?)}': r'((\1)/(\2))',
            r'\\sqrt{(.+?)}': r'sqrt(\1)',
            r'\\sin': 'sin',
            r'\\cos': 'cos',
            r'\\tan': 'tan',
            r'\\log': 'log',
            r'\\ln': 'ln',
            r'\\exp': 'exp',
            r'\\pi': 'pi',
            r'\\infty': 'inf',
            r'\\sum_{(.+?)}\\^{(.+?)}': r'sum(\1, \2)',
            r'\\int_{(.+?)}\\^{(.+?)}': r'integral(\1, \2)',
            r'\\partial': 'd',
            r'\\cdot': '*',
            r'\\times': '*',
            r'\\div': '/',
            r'\\pm': '+-',
            r'\\mp': '-+',
            r'\\leq': '<=',
            r'\\geq': '>=',
            r'\\neq': '!=',
            r'\\approx': '~=',
            r'\\equiv': '===',
            r'\\in': 'in',
            r'\\notin': 'not in',
            r'\\subset': 'subset',
            r'\\supset': 'superset',
            r'\\cup': 'union',
            r'\\cap': 'intersection',
            r'\\forall': 'forall',
            r'\\exists': 'exists',
            r'\\neg': 'not',
            r'\\land': 'and',
            r'\\lor': 'or',
            r'\\rightarrow': '->',
            r'\\Rightarrow': '=>',
            r'\\leftrightarrow': '<->',
            r'\\Leftrightarrow': '<=>',
        }

        # Unicode to Python/symbolic
        self.unicode_to_python = {
            '\u00d7': '*',      # ×
            '\u00f7': '/',      # ÷
            '\u2212': '-',      # −
            '\u00b2': '**2',    # ²
            '\u00b3': '**3',    # ³
            '\u221a': 'sqrt',   # √
            '\u03c0': 'pi',     # π
            '\u2211': 'sum',    # ∑
            '\u222b': 'integral',# ∫
            '\u2202': 'd',      # ∂
            '\u221e': 'inf',    # ∞
            '\u2264': '<=',     # ≤
            '\u2265': '>=',     # ≥
            '\u2260': '!=',     # ≠
            '\u2248': '~=',     # ≈
            '\u2261': '===',    # ≡
            '\u2208': 'in',     # ∈
            '\u2209': 'not in', # ∉
            '\u2282': 'subset', # ⊂
            '\u2283': 'superset',# ⊃
            '\u222a': 'union',  # ∪
            '\u2229': 'intersection',# ∩
            '\u2200': 'forall', # ∀
            '\u2203': 'exists', # ∃
            '\u00ac': 'not',    # ¬
            '\u2227': 'and',    # ∧
            '\u2228': 'or',     # ∨
            '\u2192': '->',     # →
            '\u21d2': '=>',     # ⇒
            '\u2194': '<->',    # ↔
            '\u21d4': '<=>',    # ⇔
        }

    def translate_latex(self, latex_expr: str) -> SymbolicStructure:
        """
        Translate LaTeX mathematical expression to symbolic form.

        Args:
            latex_expr: LaTeX expression (e.g., "\\frac{d}{dx} x^2")

        Returns:
            SymbolicStructure representing the expression
        """
        # Clean up the expression
        expr = latex_expr.strip()

        # Apply LaTeX to Python conversions
        python_expr = expr
        for pattern, replacement in self.latex_to_python.items():
            python_expr = re.sub(pattern, replacement, python_expr)

        # Handle exponents: ^{...} -> **...
        python_expr = re.sub(r'\^{(.+?)}', r'**(\1)', python_expr)
        python_expr = re.sub(r'\^(\w)', r'**\1', python_expr)

        # Handle subscripts: _{...} -> [...]
        python_expr = re.sub(r'_{(.+?)}', r'[\1]', python_expr)

        # Clean up remaining LaTeX
        python_expr = re.sub(r'\\[a-zA-Z]+', '', python_expr)
        python_expr = python_expr.replace('{', '(').replace('}', ')')

        # Extract variables
        variables = set(re.findall(r'\b([a-zA-Z])\b(?!\s*\()', python_expr))

        # Build predicates
        predicates = [f"expression({python_expr})"]

        # Identify expression type
        if 'sum' in python_expr or '\u2211' in latex_expr:
            predicates.append("is_summation")
        if 'integral' in python_expr or '\u222b' in latex_expr:
            predicates.append("is_integral")
        if 'd' in python_expr and '/' in python_expr:
            predicates.append("is_derivative")
        if '=>' in python_expr or '->' in python_expr:
            predicates.append("is_implication")
        if 'forall' in python_expr or 'exists' in python_expr:
            predicates.append("is_quantified")

        return SymbolicStructure(
            structure_id=f"math_latex_{hash(latex_expr) % 10000}",
            structure_type=SymbolicType.TEMPLATE,
            content={
                'original_latex': latex_expr,
                'python_form': python_expr,
                'variables': list(variables)
            },
            predicates=predicates,
            relations=[],
            constraints=[],
            source='latex',
            confidence=self._estimate_latex_confidence(latex_expr, python_expr)
        )

    def translate_unicode(self, unicode_expr: str) -> SymbolicStructure:
        """
        Translate Unicode mathematical expression to symbolic form.

        Args:
            unicode_expr: Expression with Unicode math symbols

        Returns:
            SymbolicStructure representing the expression
        """
        # Apply Unicode to Python conversions
        python_expr = unicode_expr
        for char, replacement in self.unicode_to_python.items():
            python_expr = python_expr.replace(char, replacement)

        # Extract variables
        variables = set(re.findall(r'\b([a-zA-Z])\b(?!\s*\()', python_expr))

        predicates = [f"expression({python_expr})"]

        return SymbolicStructure(
            structure_id=f"math_unicode_{hash(unicode_expr) % 10000}",
            structure_type=SymbolicType.TEMPLATE,
            content={
                'original_unicode': unicode_expr,
                'python_form': python_expr,
                'variables': list(variables)
            },
            predicates=predicates,
            relations=[],
            constraints=[],
            source='unicode',
            confidence=0.8
        )

    def translate_text_notation(self, text_expr: str) -> SymbolicStructure:
        """
        Translate text mathematical notation to symbolic form.

        Args:
            text_expr: Text expression (e.g., "derivative of x squared")

        Returns:
            SymbolicStructure representing the expression
        """
        text_lower = text_expr.lower()
        python_expr = text_expr

        # Text to symbolic mappings
        text_mappings = [
            (r'derivative of\s+(.+?)\s+with respect to\s+(\w+)', r'd(\1)/d\2'),
            (r'derivative of\s+(.+)', r'd(\1)/dx'),
            (r'integral of\s+(.+?)\s+from\s+(\S+)\s+to\s+(\S+)', r'integral(\1, \2, \3)'),
            (r'integral of\s+(.+)', r'integral(\1)'),
            (r'sum of\s+(.+?)\s+from\s+(\S+)\s+to\s+(\S+)', r'sum(\1, \2, \3)'),
            (r'(\w+)\s+squared', r'\1**2'),
            (r'(\w+)\s+cubed', r'\1**3'),
            (r'square root of\s+(.+)', r'sqrt(\1)'),
            (r'(\w+)\s+to the power of\s+(\S+)', r'\1**\2'),
            (r'(\w+)\s+divided by\s+(\S+)', r'\1/\2'),
            (r'(\w+)\s+times\s+(\S+)', r'\1*\2'),
            (r'(\w+)\s+plus\s+(\S+)', r'\1+\2'),
            (r'(\w+)\s+minus\s+(\S+)', r'\1-\2'),
        ]

        for pattern, replacement in text_mappings:
            python_expr = re.sub(pattern, replacement, python_expr, flags=re.IGNORECASE)

        # Extract variables
        variables = set(re.findall(r'\b([a-zA-Z])\b(?!\s*\()', python_expr))

        predicates = [f"expression({python_expr})"]

        return SymbolicStructure(
            structure_id=f"math_text_{hash(text_expr) % 10000}",
            structure_type=SymbolicType.TEMPLATE,
            content={
                'original_text': text_expr,
                'python_form': python_expr,
                'variables': list(variables)
            },
            predicates=predicates,
            relations=[],
            constraints=[],
            source='text',
            confidence=0.6
        )

    def auto_translate(self, expr: str) -> SymbolicStructure:
        """
        Automatically detect format and translate expression.

        Args:
            expr: Mathematical expression in any supported format

        Returns:
            SymbolicStructure representing the expression
        """
        # Check for LaTeX
        if '\\' in expr or '{' in expr:
            return self.translate_latex(expr)

        # Check for Unicode math symbols
        if any(ord(c) > 127 for c in expr):
            return self.translate_unicode(expr)

        # Check for text notation
        if any(kw in expr.lower() for kw in ['derivative', 'integral', 'sum of', 'squared']):
            return self.translate_text_notation(expr)

        # Default: treat as direct expression
        return SymbolicStructure(
            structure_id=f"math_direct_{hash(expr) % 10000}",
            structure_type=SymbolicType.TEMPLATE,
            content={'expression': expr},
            predicates=[f"expression({expr})"],
            relations=[],
            constraints=[],
            source='direct',
            confidence=0.7
        )

    def _estimate_latex_confidence(self, latex: str, python: str) -> float:
        """Estimate confidence in LaTeX translation"""
        confidence = 0.8

        # Penalty for remaining backslashes (untranslated LaTeX)
        remaining_latex = len(re.findall(r'\\[a-zA-Z]+', python))
        confidence -= 0.1 * remaining_latex

        # Bonus for balanced brackets
        if latex.count('{') == latex.count('}'):
            confidence += 0.05

        if latex.count('(') == latex.count(')'):
            confidence += 0.05

        return max(0.3, min(0.95, confidence))


class SymbolicToNeuralTranslator:
    """Translate symbolic structures to natural language for LLM"""

    def translate(self, structure: SymbolicStructure) -> str:
        """
        Translate symbolic structure to natural language.

        Args:
            structure: Symbolic structure to translate

        Returns:
            Natural language description
        """
        parts = []

        # Structure type header
        parts.append(f"This is a {structure.structure_type.value} structure.")

        # Translate predicates
        if structure.predicates:
            parts.append("Known facts:")
            for pred in structure.predicates[:10]:  # Limit
                natural = self._predicate_to_natural(pred)
                parts.append(f"  - {natural}")

        # Translate relations
        if structure.relations:
            parts.append("Relationships:")
            for subj, rel, obj in structure.relations[:10]:
                natural = self._relation_to_natural(subj, rel, obj)
                parts.append(f"  - {natural}")

        # Translate constraints
        if structure.constraints:
            parts.append("Constraints:")
            for constraint in structure.constraints[:5]:
                parts.append(f"  - {constraint}")

        return "\n".join(parts)

    def _predicate_to_natural(self, predicate: str) -> str:
        """Convert predicate to natural language"""
        # Parse predicate
        match = re.match(r'(\w+)\((.*)\)', predicate)
        if not match:
            return predicate

        pred_name = match.group(1)
        args = match.group(2).split(', ')

        if pred_name == 'entity':
            return f"{args[0]} is an entity"
        elif pred_name == 'causes':
            return f"{args[0]} causes {args[1]}"
        elif pred_name == 'is_a':
            return f"{args[0]} is a type of {args[1]}"
        else:
            return f"{pred_name}: {', '.join(args)}"

    def _relation_to_natural(self, subj: str, rel: str, obj: str) -> str:
        """Convert relation to natural language"""
        rel_templates = {
            'causes': f"{subj} causes {obj}",
            'leads_to': f"{subj} leads to {obj}",
            'is_a': f"{subj} is a type of {obj}",
            'contains': f"{subj} contains {obj}",
            'depends_on': f"{subj} depends on {obj}",
            'produces': f"{subj} produces {obj}",
            'affects': f"{subj} affects {obj}",
            'implies': f"if {subj} then {obj}",
        }

        return rel_templates.get(rel, f"{subj} {rel} {obj}")


class SymbolicVerifier:
    """Verify neural proposals against symbolic constraints"""

    def __init__(self, v36_system: Any = None):
        """
        Args:
            v36_system: Optional V36 system for constraint checking
        """
        self.v36_system = v36_system

    def verify(self, proposal: NeuralProposal,
               constraints: List[str] = None) -> Dict[str, Any]:
        """
        Verify neural proposal against constraints.

        Args:
            proposal: Neural proposal to verify
            constraints: List of constraint strings

        Returns:
            Verification result
        """
        results = {
            'proposal_id': proposal.proposal_id,
            'status': VerificationStatus.UNKNOWN,
            'violations': [],
            'satisfied': [],
            'score': 0.5
        }

        constraints = constraints or []

        # Check extracted relations against constraints
        for subj, rel, obj in proposal.extracted_relations:
            for constraint in constraints:
                violation = self._check_violation(subj, rel, obj, constraint)
                if violation:
                    results['violations'].append(violation)
                else:
                    results['satisfied'].append(constraint)

        # Check with V36 if available
        if self.v36_system and hasattr(self.v36_system, 'prohibitive_engine'):
            v36_violations = self._check_v36_constraints(proposal)
            results['violations'].extend(v36_violations)

        # Compute score and status
        n_constraints = len(constraints)
        if n_constraints > 0:
            satisfaction_rate = len(results['satisfied']) / n_constraints
            results['score'] = satisfaction_rate

        if results['violations']:
            if len(results['violations']) < len(constraints) / 2:
                results['status'] = VerificationStatus.PARTIAL
            else:
                results['status'] = VerificationStatus.VIOLATED
        else:
            results['status'] = VerificationStatus.VERIFIED

        return results

    def _check_violation(self, subj: str, rel: str, obj: str,
                        constraint: str) -> Optional[str]:
        """Check if relation violates constraint"""
        # Simple keyword matching
        constraint_lower = constraint.lower()

        # Check for explicit negation
        if rel in constraint_lower and 'not' in constraint_lower:
            if subj in constraint_lower or obj in constraint_lower:
                return f"Relation {subj}-{rel}-{obj} violates constraint: {constraint}"

        return None
