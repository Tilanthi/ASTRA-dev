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
Specialized Mind Implementations for Multi-Mind Orchestration Layer (MMOL)

Each mind is a specialized cognitive subsystem optimized for a particular
domain or reasoning style.

Version: 4.0.0
Date: 2026-03-17
"""

from typing import Dict, List, Optional, Any
from dataclasses import dataclass, field
from enum import Enum
from abc import ABC, abstractmethod


class Domain(Enum):
    """Domains of specialized expertise"""
    PHYSICS = "physics"
    MATHEMATICS = "mathematics"
    EMPATHY = "empathy"
    POLITICS = "politics"
    POETRY = "poetry"
    CAUSAL = "causal"
    CREATIVE = "creative"
    ETHICS = "ethics"
    PHILOSOPHY = "philosophy"
    EPISTEMOLOGY = "epistemology"


class ReasoningStyle(Enum):
    """Styles of reasoning"""
    FORMAL = "formal"           # Rigorous, deductive logic
    INTUITIVE = "intuitive"     # Pattern-based, heuristic
    ANALYTICAL = "analytical"   # Decomposition-based
    HOLISTIC = "holistic"       # System-wide integration
    CRITICAL = "critical"       # Skeptical, questioning
    SYNTHETIC = "synthetic"     # Integration-focused
    NARRATIVE = "narrative"     # Story-based


@dataclass
class ConfidenceModel:
    """Model of how confident a mind is about its outputs"""
    base_confidence: float = 0.7
    calibration: float = 0.0  # How well-calibrated the confidence is
    uncertainty_type: str = "aleatoric"  # aleatoric or epistemic
    meta_confidence: float = 0.5  # Confidence in confidence estimate

    def adjust_confidence(self, outcome: float) -> float:
        """Adjust confidence based on outcome."""
        error = abs(outcome - self.base_confidence)
        # Simplified calibration
        self.calibration = 0.9 * self.calibration + 0.1 * error
        self.base_confidence = 0.9 * self.base_confidence + 0.1 * outcome
        return self.base_confidence


@dataclass
class MindKnowledgeBase:
    """Knowledge base specialized for a mind"""
    domain: Domain
    facts: List[str] = field(default_factory=list)
    concepts: Dict[str, Any] = field(default_factory=dict)
    principles: List[str] = field(default_factory=list)
    experts: List[str] = field(default_factory=list)
    examples: List[str] = field(default_factory=list)

    def add_knowledge(self, fact: str) -> None:
        """Add a fact to the knowledge base."""
        self.facts.append(fact)

    def get_relevant_knowledge(self, query: str) -> List[str]:
        """Get knowledge relevant to query."""
        # Simplified: return all facts
        return self.facts


@dataclass
class MindResult:
    """Result from a mind processing a query"""
    mind_id: str
    result: Any
    confidence: float
    reasoning_process: List[str]
    predicted_confidences: Dict[str, float] = field(default_factory=dict)  # Predicted other minds' confidence
    relevance_score: float = 0.0
    metadata: Dict[str, Any] = field(default_factory=dict)


class SpecializedMind(ABC):
    """
    Base class for specialized cognitive subsystems.

    Each mind is optimized for a specific domain or reasoning style.
    """

    def __init__(
        self,
        mind_id: str,
        domain: Domain,
        reasoning_style: ReasoningStyle
    ):
        self.mind_id = mind_id
        self.domain = domain
        self.reasoning_style = reasoning_style
        self.confidence_model = ConfidenceModel()
        self.knowledge_base = MindKnowledgeBase(domain=domain)
        self.relevance_tuning: Dict[str, float] = {}  # Query type -> relevance
        self.performance_history: List[float] = []

    @abstractmethod
    def process(
        self,
        query: str,
        context: Dict[str, Any]
    ) -> MindResult:
        """Process query from this mind's perspective."""
        pass

    def predict_confidence(
        self,
        query: str,
        other_minds: List['SpecializedMind']
    ) -> Dict[str, float]:
        """
        Predict other minds' confidence (for anticipatory arbitration).

        Args:
            query: Query being processed
            other_minds: Other minds to predict

        Returns:
            Dictionary mapping mind_id to predicted confidence
        """
        predictions = {}

        for other_mind in other_minds:
            # Base prediction on domain similarity
            if other_mind.domain == self.domain:
                predictions[other_mind.mind_id] = 0.8
            elif self._is_complementary_domain(other_mind.domain):
                predictions[other_mind.mind_id] = 0.6
            else:
                predictions[other_mind.mind_id] = 0.4

        return predictions

    def _is_complementary_domain(self, other_domain: Domain) -> bool:
        """Check if another domain is complementary to this one."""
        complementary_pairs = [
            (Domain.PHYSICS, Domain.MATHEMATICS),
            (Domain.EMPATHY, Domain.ETHICS),
            (Domain.POLITICS, Domain.PHILOSOPHY),
            (Domain.POETRY, Domain.CREATIVE),
        ]
        return (self.domain, other_domain) in complementary_pairs or (other_domain, self.domain) in complementary_pairs

    def update_relevance_tuning(self, query_type: str, score: float) -> None:
        """Update relevance tuning based on feedback."""
        if query_type in self.relevance_tuning:
            self.relevance_tuning[query_type] = 0.9 * self.relevance_tuning[query_type] + 0.1 * score
        else:
            self.relevance_tuning[query_type] = score

    def calculate_relevance(self, query: str) -> float:
        """Calculate how relevant this mind is to a query."""
        # Check query against domain keywords
        domain_keywords = self._get_domain_keywords()

        relevance = 0.5  # Base relevance
        query_lower = query.lower()

        for keyword in domain_keywords:
            if keyword in query_lower:
                relevance += 0.1

        return min(relevance, 1.0)

    def _get_domain_keywords(self) -> List[str]:
        """Get keywords associated with this mind's domain."""
        # Base implementation
        return [self.domain.value]

    def get_status(self) -> Dict[str, Any]:
        """Get mind status."""
        return {
            "mind_id": self.mind_id,
            "domain": self.domain.value,
            "reasoning_style": self.reasoning_style.value,
            "confidence": self.confidence_model.base_confidence,
            "performance_history": self.performance_history[-10:] if self.performance_history else []
        }


class PhysicsMind(SpecializedMind):
    """Specialized for physics reasoning and physical models."""

    def __init__(self):
        super().__init__("physics_mind", Domain.PHYSICS, ReasoningStyle.ANALYTICAL)
        self.knowledge_base.principles = [
            "Conservation of energy",
            "Newton's laws of motion",
            "Maxwell's equations",
            "Quantum superposition",
            "Relativity"
        ]
        self.knowledge_base.experts = ["Einstein", "Newton", "Feynman", "Bohr"]

    def process(self, query: str, context: Dict) -> MindResult:
        """Process query from physics perspective."""
        reasoning = [
            "Analyzing physical laws involved",
            "Checking dimensional consistency",
            "Applying conservation principles",
            "Considering quantum effects if applicable"
        ]

        result = f"Physics analysis of: {query}"

        return MindResult(
            mind_id=self.mind_id,
            result=result,
            confidence=self.confidence_model.base_confidence,
            reasoning_process=reasoning,
            relevance_score=self.calculate_relevance(query)
        )

    def _get_domain_keywords(self) -> List[str]:
        return ["force", "energy", "mass", "velocity", "acceleration", "quantum",
                "gravity", "particle", "wave", "physics", "physical", "matter"]


class EmpathyMind(SpecializedMind):
    """Specialized for emotional reasoning and human perspective."""

    def __init__(self):
        super().__init__("empathy_mind", Domain.EMPATHY, ReasoningStyle.HOLISTIC)
        self.knowledge_base.principles = [
            "Emotions provide information",
            "Subjective experience matters",
            "Human values are fundamental",
            "Relationships shape cognition"
        ]

    def process(self, query: str, context: Dict) -> MindResult:
        """Process query from empathetic perspective."""
        reasoning = [
            "Considering emotional impact",
            "Examining human perspective",
            "Evaluating value implications",
            "Understanding relationship dynamics"
        ]

        result = f"Empathetic analysis of: {query}"

        return MindResult(
            mind_id=self.mind_id,
            result=result,
            confidence=self.confidence_model.base_confidence,
            reasoning_process=reasoning,
            relevance_score=self.calculate_relevance(query)
        )

    def _get_domain_keywords(self) -> List[str]:
        return ["feel", "emotion", "human", "person", "relationship", "value",
                "empathy", "caring", "love", "suffering", "experience"]


class PoliticalMind(SpecializedMind):
    """Specialized for political and social reasoning."""

    def __init__(self):
        super().__init__("political_mind", Domain.POLITICS, ReasoningStyle.NARRATIVE)
        self.knowledge_base.principles = [
            "Power dynamics shape outcomes",
            "Institutions channel behavior",
            "Collective action problems",
            "Social choice is complex"
        ]

    def process(self, query: str, context: Dict) -> MindResult:
        """Process query from political perspective."""
        reasoning = [
            "Analyzing power structures",
            "Considering institutional constraints",
            "Evaluating collective action dynamics",
            "Examining social choice mechanisms"
        ]

        result = f"Political analysis of: {query}"

        return MindResult(
            mind_id=self.mind_id,
            result=result,
            confidence=self.confidence_model.base_confidence,
            reasoning_process=reasoning,
            relevance_score=self.calculate_relevance(query)
        )

    def _get_domain_keywords(self) -> List[str]:
        return ["power", "government", "politics", "social", "institution", "policy",
                "vote", "election", "democracy", "authority", "citizen"]


class PoeticMind(SpecializedMind):
    """Specialized for poetic and creative expression."""

    def __init__(self):
        super().__init__("poetic_mind", Domain.POETRY, ReasoningStyle.SYNTHETIC)
        self.knowledge_base.principles = [
            "Metaphor reveals truth",
            "Ambiguity creates depth",
            "Rhythm shapes meaning",
            "Beauty and truth intertwined"
        ]

    def process(self, query: str, context: Dict) -> MindResult:
        """Process query from poetic perspective."""
        reasoning = [
            "Finding metaphorical connections",
            "Exploring symbolic meanings",
            "Crafting rhythmic expression",
            "Embracing creative ambiguity"
        ]

        # Generate poetic interpretation
        result = f"Poetic reflection on: {query}"

        return MindResult(
            mind_id=self.mind_id,
            result=result,
            confidence=self.confidence_model.base_confidence * 0.8,  # Poetry is more interpretive
            reasoning_process=reasoning,
            relevance_score=self.calculate_relevance(query)
        )

    def _get_domain_keywords(self) -> List[str]:
        return ["beauty", "art", "poetry", "metaphor", "symbol", "meaning", "creative",
                "express", "aesthetic", "rhythm", "word", "language"]


class MathematicalMind(SpecializedMind):
    """Specialized for formal mathematical reasoning."""

    def __init__(self):
        super().__init__("mathematical_mind", Domain.MATHEMATICS, ReasoningStyle.FORMAL)
        self.knowledge_base.principles = [
            "Mathematical rigor requires proof",
            "Abstraction reveals structure",
            "Logic is foundational",
            "Formalization enables verification"
        ]

    def process(self, query: str, context: Dict) -> MindResult:
        """Process query from mathematical perspective."""
        reasoning = [
            "Formalizing the problem",
            "Applying mathematical theorems",
            "Checking logical consistency",
            "Deriving formal proofs"
        ]

        result = f"Mathematical analysis of: {query}"

        return MindResult(
            mind_id=self.mind_id,
            result=result,
            confidence=self.confidence_model.base_confidence,
            reasoning_process=reasoning,
            relevance_score=self.calculate_relevance(query)
        )

    def _get_domain_keywords(self) -> List[str]:
        return ["number", "equation", "proof", "theorem", "logic", "formal", "abstract",
                "mathematics", "math", "calculation", "structure", "pattern"]


class CausalMind(SpecializedMind):
    """Specialized for causal reasoning and inference."""

    def __init__(self):
        super().__init__("causal_mind", Domain.CAUSAL, ReasoningStyle.ANALYTICAL)
        self.knowledge_base.principles = [
            "Correlation does not imply causation",
            "Causal mechanisms require intervention",
            "Counterfactuals reveal structure",
            "Confounding variables obscure truth"
        ]

    def process(self, query: str, context: Dict) -> MindResult:
        """Process query from causal perspective."""
        reasoning = [
            "Identifying causal variables",
            "Analyzing causal mechanisms",
            "Considering confounders",
            "Evaluating counterfactuals"
        ]

        result = f"Causal analysis of: {query}"

        return MindResult(
            mind_id=self.mind_id,
            result=result,
            confidence=self.confidence_model.base_confidence,
            reasoning_process=reasoning,
            relevance_score=self.calculate_relevance(query)
        )

    def _get_domain_keywords(self) -> List[str]:
        return ["cause", "effect", "causal", "because", "reason", "mechanism",
                "intervention", "counterfactual", "confound", "correlation"]


class CreativeMind(SpecializedMind):
    """Specialized for creative and novel solutions."""

    def __init__(self):
        super().__init__("creative_mind", Domain.CREATIVE, ReasoningStyle.INTUITIVE)
        self.knowledge_base.principles = [
            "Novelty drives progress",
            "Combination creates innovation",
            "Constraints enable creativity",
            "Exploration yields discovery"
        ]

    def process(self, query: str, context: Dict) -> MindResult:
        """Process query from creative perspective."""
        reasoning = [
            "Exploring unconventional approaches",
            "Combining disparate ideas",
            "Challenging assumptions",
            "Generating novel alternatives"
        ]

        result = f"Creative exploration of: {query}"

        return MindResult(
            mind_id=self.mind_id,
            result=result,
            confidence=self.confidence_model.base_confidence * 0.7,  # Creative is more uncertain
            reasoning_process=reasoning,
            relevance_score=self.calculate_relevance(query)
        )

    def _get_domain_keywords(self) -> List[str]:
        return ["new", "novel", "creative", "innovate", "different", "alternative",
                "imagine", "invent", "discover", "explore", "original"]


# =============================================================================
# Factory Functions
# =============================================================================

def create_physics_mind() -> PhysicsMind:
    """Create a Physics specialized mind."""
    return PhysicsMind()

def create_empathy_mind() -> EmpathyMind:
    """Create an Empathy specialized mind."""
    return EmpathyMind()

def create_political_mind() -> PoliticalMind:
    """Create a Politics specialized mind."""
    return PoliticalMind()

def create_poetic_mind() -> PoeticMind:
    """Create a Poetry specialized mind."""
    return PoeticMind()

def create_mathematical_mind() -> MathematicalMind:
    """Create a Mathematics specialized mind."""
    return MathematicalMind()

def create_causal_mind() -> CausalMind:
    """Create a Causal specialized mind."""
    return CausalMind()

def create_creative_mind() -> CreativeMind:
    """Create a Creative specialized mind."""
    return CreativeMind()


def create_all_specialized_minds() -> Dict[str, SpecializedMind]:
    """Create all specialized minds."""
    return {
        "physics_mind": create_physics_mind(),
        "empathy_mind": create_empathy_mind(),
        "political_mind": create_political_mind(),
        "poetic_mind": create_poetic_mind(),
        "mathematical_mind": create_mathematical_mind(),
        "causal_mind": create_causal_mind(),
        "creative_mind": create_creative_mind()
    }
