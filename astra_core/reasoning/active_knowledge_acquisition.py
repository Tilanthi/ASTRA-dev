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
Active Knowledge Acquisition Module for STAN V41

Implements intelligent, goal-directed knowledge seeking. Instead of passive
information gathering, this module actively identifies knowledge gaps and
formulates optimal queries to fill them.

Key capabilities:
- Knowledge gap identification: Find critical unknowns
- Query optimization: Formulate maximally informative questions
- Source selection: Choose best sources for different knowledge types
- Information value estimation: Prioritize high-value acquisitions
- Curriculum learning: Structured knowledge building
"""

from dataclasses import dataclass, field
from typing import Dict, List, Set, Optional, Any, Callable, Tuple
from enum import Enum, auto
from datetime import datetime
import uuid
from collections import defaultdict
import math
import heapq


class KnowledgeType(Enum):
    """Types of knowledge"""
    FACTUAL = auto()           # Facts and data
    PROCEDURAL = auto()        # How to do things
    CONCEPTUAL = auto()        # Understanding concepts
    CAUSAL = auto()            # Cause-effect relationships
    STRUCTURAL = auto()        # Organization and relationships
    CONDITIONAL = auto()       # Context-dependent knowledge
    TACIT = auto()             # Implicit, hard-to-articulate


class SourceType(Enum):
    """Types of knowledge sources"""
    INTERNAL_MEMORY = auto()   # Already known
    EXTERNAL_DATABASE = auto() # Structured data
    SCIENTIFIC_LITERATURE = auto()  # Papers, journals
    EXPERT_SYSTEM = auto()     # Domain expert
    COMPUTATION = auto()       # Derived through calculation
    OBSERVATION = auto()       # Empirical observation
    EXPERIMENT = auto()        # Active experimentation
    SIMULATION = auto()        # Model-based inference


class AcquisitionPriority(Enum):
    """Priority levels for knowledge acquisition"""
    CRITICAL = auto()          # Blocking current task
    HIGH = auto()              # Significantly impacts quality
    MEDIUM = auto()            # Would improve results
    LOW = auto()               # Nice to have
    BACKGROUND = auto()        # Long-term learning


@dataclass
class KnowledgeGap:
    """A identified gap in current knowledge"""
    gap_id: str
    description: str
    knowledge_type: KnowledgeType

    # Context
    domain: str
    related_task: Optional[str] = None
    blocking_inference: bool = False

    # Impact assessment
    priority: AcquisitionPriority = AcquisitionPriority.MEDIUM
    information_value: float = 0.5      # How valuable is this knowledge
    urgency: float = 0.5                # How soon is it needed

    # Acquisition planning
    suggested_sources: List[SourceType] = field(default_factory=list)
    estimated_effort: float = 0.5       # 0 = trivial, 1 = very difficult
    prerequisites: List[str] = field(default_factory=list)  # Other knowledge needed first

    # Status
    is_resolved: bool = False
    resolution_source: Optional[SourceType] = None

    discovered_at: datetime = field(default_factory=datetime.now)
    resolved_at: Optional[datetime] = None

    def __post_init__(self):
        if not self.gap_id:
            self.gap_id = f"GAP-{uuid.uuid4().hex[:8]}"

    @property
    def acquisition_score(self) -> float:
        """Score for prioritizing acquisition"""
        priority_weights = {
            AcquisitionPriority.CRITICAL: 1.0,
            AcquisitionPriority.HIGH: 0.8,
            AcquisitionPriority.MEDIUM: 0.5,
            AcquisitionPriority.LOW: 0.3,
            AcquisitionPriority.BACKGROUND: 0.1
        }

        base = priority_weights[self.priority]
        value_factor = self.information_value
        urgency_factor = self.urgency
        effort_penalty = (1 - self.estimated_effort) * 0.3

        return base * 0.4 + value_factor * 0.3 + urgency_factor * 0.2 + effort_penalty


@dataclass
class Query:
    """A formulated query to acquire knowledge"""
    query_id: str
    question: str
    target_gap: str                     # Gap ID being addressed

    # Query specification
    knowledge_type: KnowledgeType
    expected_answer_format: str         # "factual", "explanation", "procedure", etc.
    constraints: List[str]              # Requirements on the answer

    # Source targeting
    preferred_sources: List[SourceType]
    source_requirements: Dict[str, Any] = field(default_factory=dict)

    # Information theory
    expected_information_gain: float = 0.5
    uncertainty_reduction: float = 0.5

    # Status
    is_answered: bool = False
    answer: Optional[str] = None
    answer_confidence: float = 0.0
    answer_source: Optional[SourceType] = None

    created_at: datetime = field(default_factory=datetime.now)
    answered_at: Optional[datetime] = None

    def __post_init__(self):
        if not self.query_id:
            self.query_id = f"QRY-{uuid.uuid4().hex[:8]}"


@dataclass
class AcquiredKnowledge:
    """Knowledge that has been acquired"""
    knowledge_id: str
    content: str
    knowledge_type: KnowledgeType

    # Source
    source: SourceType
    source_details: str
    acquisition_query: Optional[str] = None  # Query ID

    # Quality
    confidence: float = 0.5
    reliability: float = 0.5            # Trust in source
    completeness: float = 0.5           # How complete is this knowledge

    # Integration
    gaps_resolved: List[str] = field(default_factory=list)  # Gap IDs
    related_knowledge: List[str] = field(default_factory=list)

    # Metadata
    acquired_at: datetime = field(default_factory=datetime.now)
    last_validated: Optional[datetime] = None

    def __post_init__(self):
        if not self.knowledge_id:
            self.knowledge_id = f"KNW-{uuid.uuid4().hex[:8]}"


@dataclass
class LearningCurriculum:
    """A structured plan for knowledge acquisition"""
    curriculum_id: str
    goal: str
    domain: str

    # Structure
    learning_stages: List[Dict[str, Any]]  # Ordered stages

    # Prerequisites graph (must come before fields with defaults)
    knowledge_dependencies: Dict[str, List[str]] = field(default_factory=dict)  # knowledge -> prerequisites

    current_stage: int = 0

    # Progress
    completed_topics: List[str] = field(default_factory=list)
    pending_topics: List[str] = field(default_factory=list)

    # Metrics
    progress: float = 0.0
    estimated_completion: float = 1.0   # Effort remaining

    created_at: datetime = field(default_factory=datetime.now)

    def __post_init__(self):
        if not self.curriculum_id:
            self.curriculum_id = f"CUR-{uuid.uuid4().hex[:8]}"


class KnowledgeGapIdentifier:
    """Identifies gaps in current knowledge"""

    def __init__(self):
        self.gap_patterns = {
            "undefined_term": self._check_undefined_terms,
            "missing_mechanism": self._check_missing_mechanisms,
            "unknown_boundary": self._check_unknown_boundaries,
            "incomplete_chain": self._check_incomplete_chains,
        }

    def identify_gaps(
        self,
        current_knowledge: Dict[str, Any],
        task_requirements: List[str],
        domain: str
    ) -> List[KnowledgeGap]:
        """Identify knowledge gaps for a task"""
        gaps = []

        for pattern_name, checker in self.gap_patterns.items():
            pattern_gaps = checker(current_knowledge, task_requirements, domain)
            gaps.extend(pattern_gaps)

        # Deduplicate and prioritize
        unique_gaps = self._deduplicate_gaps(gaps)
        return sorted(unique_gaps, key=lambda g: g.acquisition_score, reverse=True)

    def _check_undefined_terms(
        self,
        knowledge: Dict[str, Any],
        requirements: List[str],
        domain: str
    ) -> List[KnowledgeGap]:
        """Find undefined terms in requirements"""
        gaps = []
        defined_terms = set(knowledge.keys())

        for req in requirements:
            # Extract terms (simplified - would use NLP in production)
            words = req.lower().split()
            for word in words:
                if len(word) > 3 and word not in defined_terms:
                    # Check if it looks like a domain term
                    if self._is_domain_term(word, domain):
                        gaps.append(KnowledgeGap(
                            gap_id="",
                            description=f"Undefined term: {word}",
                            knowledge_type=KnowledgeType.CONCEPTUAL,
                            domain=domain,
                            related_task=req[:50],
                            priority=AcquisitionPriority.HIGH,
                            information_value=0.7,
                            suggested_sources=[SourceType.EXTERNAL_DATABASE, SourceType.SCIENTIFIC_LITERATURE]
                        ))

        return gaps

    def _check_missing_mechanisms(
        self,
        knowledge: Dict[str, Any],
        requirements: List[str],
        domain: str
    ) -> List[KnowledgeGap]:
        """Find missing causal mechanisms"""
        gaps = []

        mechanism_keywords = ["causes", "leads to", "results in", "produces", "generates"]

        for req in requirements:
            req_lower = req.lower()
            for keyword in mechanism_keywords:
                if keyword in req_lower:
                    # Check if mechanism is known
                    if "mechanisms" not in knowledge or not knowledge.get("mechanisms"):
                        gaps.append(KnowledgeGap(
                            gap_id="",
                            description=f"Missing mechanism for: {req[:50]}",
                            knowledge_type=KnowledgeType.CAUSAL,
                            domain=domain,
                            related_task=req[:50],
                            blocking_inference=True,
                            priority=AcquisitionPriority.CRITICAL,
                            information_value=0.9,
                            suggested_sources=[SourceType.SCIENTIFIC_LITERATURE, SourceType.EXPERT_SYSTEM]
                        ))

        return gaps

    def _check_unknown_boundaries(
        self,
        knowledge: Dict[str, Any],
        requirements: List[str],
        domain: str
    ) -> List[KnowledgeGap]:
        """Find unknown boundary conditions"""
        gaps = []

        boundary_keywords = ["range", "limit", "boundary", "valid when", "applies to"]

        for req in requirements:
            req_lower = req.lower()
            if any(kw in req_lower for kw in boundary_keywords):
                if "boundaries" not in knowledge:
                    gaps.append(KnowledgeGap(
                        gap_id="",
                        description=f"Unknown boundary conditions for: {req[:50]}",
                        knowledge_type=KnowledgeType.CONDITIONAL,
                        domain=domain,
                        priority=AcquisitionPriority.MEDIUM,
                        information_value=0.6,
                        suggested_sources=[SourceType.COMPUTATION, SourceType.EXPERIMENT]
                    ))

        return gaps

    def _check_incomplete_chains(
        self,
        knowledge: Dict[str, Any],
        requirements: List[str],
        domain: str
    ) -> List[KnowledgeGap]:
        """Find incomplete reasoning chains"""
        gaps = []

        # Check for prerequisites that aren't satisfied
        if "reasoning_chains" in knowledge:
            for chain in knowledge["reasoning_chains"]:
                if isinstance(chain, dict) and "prerequisites" in chain:
                    for prereq in chain["prerequisites"]:
                        if prereq not in knowledge:
                            gaps.append(KnowledgeGap(
                                gap_id="",
                                description=f"Missing prerequisite: {prereq}",
                                knowledge_type=KnowledgeType.CONCEPTUAL,
                                domain=domain,
                                blocking_inference=True,
                                priority=AcquisitionPriority.HIGH,
                                prerequisites=[],
                                suggested_sources=[SourceType.INTERNAL_MEMORY, SourceType.EXTERNAL_DATABASE]
                            ))

        return gaps

    def _is_domain_term(self, word: str, domain: str) -> bool:
        """Check if word is likely a domain-specific term"""
        # Heuristic: longer words, technical suffixes
        technical_suffixes = ["tion", "ment", "ity", "ics", "ism", "phy", "logy"]
        return (
            len(word) > 5 or
            any(word.endswith(suffix) for suffix in technical_suffixes)
        )

    def _deduplicate_gaps(self, gaps: List[KnowledgeGap]) -> List[KnowledgeGap]:
        """Remove duplicate gaps"""
        seen = set()
        unique = []
        for gap in gaps:
            key = (gap.description.lower(), gap.knowledge_type)
            if key not in seen:
                seen.add(key)
                unique.append(gap)
        return unique


class QueryOptimizer:
    """Optimizes queries for maximum information gain"""

    def __init__(self):
        self.query_templates = {
            KnowledgeType.FACTUAL: [
                "What is {concept}?",
                "What are the key properties of {concept}?",
                "How is {concept} defined in {domain}?"
            ],
            KnowledgeType.PROCEDURAL: [
                "How do you {action}?",
                "What are the steps to {action}?",
                "What is the procedure for {action}?"
            ],
            KnowledgeType.CAUSAL: [
                "What causes {effect}?",
                "How does {cause} lead to {effect}?",
                "What is the mechanism by which {cause} produces {effect}?"
            ],
            KnowledgeType.CONCEPTUAL: [
                "What are the key concepts in {domain}?",
                "How is {concept} related to {other_concept}?",
                "What distinguishes {concept} from {other_concept}?"
            ],
            KnowledgeType.CONDITIONAL: [
                "Under what conditions does {phenomenon} occur?",
                "What are the boundary conditions for {law}?",
                "When is {method} applicable?"
            ],
            KnowledgeType.STRUCTURAL: [
                "What are the components of {system}?",
                "How is {system} organized?",
                "What are the relationships between {entities}?"
            ]
        }

    def optimize_query(
        self,
        gap: KnowledgeGap,
        context: Dict[str, Any] = None
    ) -> Query:
        """Generate an optimized query for a knowledge gap"""
        # Select template based on knowledge type
        templates = self.query_templates.get(gap.knowledge_type, ["Tell me about {concept}?"])
        template = templates[0]  # Use best template

        # Fill template
        question = self._fill_template(template, gap, context or {})

        # Estimate information gain
        info_gain = self._estimate_information_gain(gap)

        return Query(
            query_id="",
            question=question,
            target_gap=gap.gap_id,
            knowledge_type=gap.knowledge_type,
            expected_answer_format=self._expected_format(gap.knowledge_type),
            constraints=self._derive_constraints(gap),
            preferred_sources=gap.suggested_sources,
            expected_information_gain=info_gain,
            uncertainty_reduction=gap.information_value
        )

    def refine_query(
        self,
        query: Query,
        previous_answer: str,
        answer_quality: float
    ) -> Query:
        """Refine a query based on previous answer"""
        if answer_quality >= 0.8:
            # Good enough, no refinement needed
            return query

        # Add specificity
        refined_question = query.question

        if answer_quality < 0.5:
            # Too vague, make more specific
            refined_question = f"Specifically, {query.question.lower()} Please provide concrete details."
        elif answer_quality < 0.8:
            # Partially answered, ask for more
            refined_question = f"Building on '{previous_answer[:50]}...', {query.question.lower()}"

        return Query(
            query_id="",
            question=refined_question,
            target_gap=query.target_gap,
            knowledge_type=query.knowledge_type,
            expected_answer_format=query.expected_answer_format,
            constraints=query.constraints + ["More specific than previous answer"],
            preferred_sources=query.preferred_sources,
            expected_information_gain=query.expected_information_gain * 0.8,
            uncertainty_reduction=query.uncertainty_reduction * 0.9
        )

    def _fill_template(
        self,
        template: str,
        gap: KnowledgeGap,
        context: Dict[str, Any]
    ) -> str:
        """Fill a query template with gap information"""
        # Extract key terms from gap description
        terms = gap.description.split()

        substitutions = {
            "concept": terms[-1] if terms else "this",
            "domain": gap.domain,
            "action": gap.description,
            "effect": terms[-1] if terms else "this",
            "cause": terms[0] if terms else "this",
            "phenomenon": gap.description,
            "law": gap.description,
            "method": gap.description,
            "system": gap.description,
            "entities": gap.description,
            "other_concept": context.get("related_concept", "related concepts")
        }

        result = template
        for key, value in substitutions.items():
            result = result.replace("{" + key + "}", str(value))

        return result

    def _estimate_information_gain(self, gap: KnowledgeGap) -> float:
        """Estimate information gain from answering the gap"""
        # Higher for blocking inferences, critical priority
        base = 0.5

        if gap.blocking_inference:
            base += 0.3

        priority_bonus = {
            AcquisitionPriority.CRITICAL: 0.2,
            AcquisitionPriority.HIGH: 0.15,
            AcquisitionPriority.MEDIUM: 0.1,
            AcquisitionPriority.LOW: 0.05,
            AcquisitionPriority.BACKGROUND: 0.0
        }
        base += priority_bonus.get(gap.priority, 0)

        return min(1.0, base)

    def _expected_format(self, knowledge_type: KnowledgeType) -> str:
        """Get expected answer format for knowledge type"""
        formats = {
            KnowledgeType.FACTUAL: "factual_statement",
            KnowledgeType.PROCEDURAL: "step_by_step",
            KnowledgeType.CAUSAL: "causal_explanation",
            KnowledgeType.CONCEPTUAL: "definition_and_relations",
            KnowledgeType.CONDITIONAL: "conditions_list",
            KnowledgeType.STRUCTURAL: "hierarchical_structure",
            KnowledgeType.TACIT: "examples_and_analogies"
        }
        return formats.get(knowledge_type, "general")

    def _derive_constraints(self, gap: KnowledgeGap) -> List[str]:
        """Derive answer constraints from gap"""
        constraints = []

        if gap.domain:
            constraints.append(f"Answer should be specific to {gap.domain}")

        if gap.blocking_inference:
            constraints.append("Answer must be complete enough to proceed")

        if gap.estimated_effort > 0.7:
            constraints.append("Complex topic - may need multiple parts")

        return constraints


class SourceSelector:
    """Selects optimal sources for different knowledge types"""

    def __init__(self):
        self.source_capabilities = {
            SourceType.INTERNAL_MEMORY: {
                "strengths": [KnowledgeType.FACTUAL, KnowledgeType.PROCEDURAL],
                "speed": 1.0,
                "reliability": 0.8,
                "cost": 0.0
            },
            SourceType.EXTERNAL_DATABASE: {
                "strengths": [KnowledgeType.FACTUAL, KnowledgeType.STRUCTURAL],
                "speed": 0.8,
                "reliability": 0.9,
                "cost": 0.1
            },
            SourceType.SCIENTIFIC_LITERATURE: {
                "strengths": [KnowledgeType.CAUSAL, KnowledgeType.CONCEPTUAL],
                "speed": 0.4,
                "reliability": 0.95,
                "cost": 0.3
            },
            SourceType.EXPERT_SYSTEM: {
                "strengths": [KnowledgeType.PROCEDURAL, KnowledgeType.TACIT],
                "speed": 0.6,
                "reliability": 0.85,
                "cost": 0.5
            },
            SourceType.COMPUTATION: {
                "strengths": [KnowledgeType.FACTUAL, KnowledgeType.CONDITIONAL],
                "speed": 0.7,
                "reliability": 0.99,
                "cost": 0.2
            },
            SourceType.OBSERVATION: {
                "strengths": [KnowledgeType.FACTUAL, KnowledgeType.STRUCTURAL],
                "speed": 0.3,
                "reliability": 0.9,
                "cost": 0.4
            },
            SourceType.EXPERIMENT: {
                "strengths": [KnowledgeType.CAUSAL, KnowledgeType.CONDITIONAL],
                "speed": 0.1,
                "reliability": 0.95,
                "cost": 0.8
            },
            SourceType.SIMULATION: {
                "strengths": [KnowledgeType.CAUSAL, KnowledgeType.CONDITIONAL],
                "speed": 0.5,
                "reliability": 0.7,
                "cost": 0.4
            }
        }

        # Source availability
        self.available_sources: Set[SourceType] = set(SourceType)

    def select_sources(
        self,
        query: Query,
        time_budget: float = 0.5,
        reliability_threshold: float = 0.7
    ) -> List[Tuple[SourceType, float]]:
        """Select and rank sources for a query"""
        candidates = []

        for source, capabilities in self.source_capabilities.items():
            if source not in self.available_sources:
                continue

            if capabilities["reliability"] < reliability_threshold:
                continue

            if capabilities["speed"] < (1 - time_budget):
                continue

            # Score based on match
            score = 0.0

            # Knowledge type match
            if query.knowledge_type in capabilities["strengths"]:
                score += 0.4

            # Speed/reliability/cost trade-off
            score += capabilities["speed"] * time_budget * 0.2
            score += capabilities["reliability"] * 0.3
            score += (1 - capabilities["cost"]) * 0.1

            candidates.append((source, score))

        return sorted(candidates, key=lambda x: x[1], reverse=True)

    def set_source_availability(self, source: SourceType, available: bool):
        """Set source availability"""
        if available:
            self.available_sources.add(source)
        else:
            self.available_sources.discard(source)


class InformationValueEstimator:
    """Estimates the value of acquiring specific information"""

    def __init__(self):
        self.value_factors = {
            "task_relevance": 0.3,
            "uncertainty_reduction": 0.25,
            "reusability": 0.2,
            "chain_enabling": 0.25
        }

    def estimate_value(
        self,
        gap: KnowledgeGap,
        current_task: Optional[str] = None,
        future_tasks: List[str] = None
    ) -> float:
        """Estimate the value of filling a knowledge gap"""
        value = 0.0

        # Task relevance
        if current_task and gap.related_task:
            overlap = self._compute_overlap(current_task, gap.related_task)
            value += self.value_factors["task_relevance"] * overlap

        # Uncertainty reduction
        value += self.value_factors["uncertainty_reduction"] * gap.information_value

        # Reusability across future tasks
        if future_tasks:
            reuse_score = sum(
                1 for task in future_tasks
                if self._could_be_relevant(gap, task)
            ) / len(future_tasks)
            value += self.value_factors["reusability"] * reuse_score

        # Chain enabling (does this unlock other knowledge?)
        if gap.blocking_inference:
            value += self.value_factors["chain_enabling"]

        return min(1.0, value)

    def _compute_overlap(self, text1: str, text2: str) -> float:
        """Compute word overlap between texts"""
        words1 = set(text1.lower().split())
        words2 = set(text2.lower().split())
        if not words1 or not words2:
            return 0.0
        return len(words1 & words2) / len(words1 | words2)

    def _could_be_relevant(self, gap: KnowledgeGap, task: str) -> bool:
        """Check if gap could be relevant to task"""
        return (
            gap.domain.lower() in task.lower() or
            any(word in task.lower() for word in gap.description.lower().split()[:3])
        )


class CurriculumBuilder:
    """Builds structured learning curricula"""

    def __init__(self):
        self.domain_structures: Dict[str, Dict[str, List[str]]] = {}

    def build_curriculum(
        self,
        goal: str,
        domain: str,
        gaps: List[KnowledgeGap],
        max_stages: int = 5
    ) -> LearningCurriculum:
        """Build a curriculum to address knowledge gaps"""
        # Sort gaps by prerequisites and priority
        sorted_gaps = self._topological_sort(gaps)

        # Group into stages
        stages = []
        current_stage = []

        for gap in sorted_gaps:
            if len(current_stage) >= len(gaps) // max_stages + 1:
                stages.append({
                    "stage_num": len(stages) + 1,
                    "topics": current_stage,
                    "focus": self._determine_focus(current_stage)
                })
                current_stage = []
            current_stage.append(gap.description)

        if current_stage:
            stages.append({
                "stage_num": len(stages) + 1,
                "topics": current_stage,
                "focus": self._determine_focus(current_stage)
            })

        # Build dependency graph
        dependencies = {}
        for gap in gaps:
            dependencies[gap.description] = gap.prerequisites

        return LearningCurriculum(
            curriculum_id="",
            goal=goal,
            domain=domain,
            learning_stages=stages,
            knowledge_dependencies=dependencies,
            pending_topics=[g.description for g in sorted_gaps],
            estimated_completion=sum(g.estimated_effort for g in gaps)
        )

    def _topological_sort(self, gaps: List[KnowledgeGap]) -> List[KnowledgeGap]:
        """Sort gaps respecting prerequisites"""
        # Build dependency graph
        gap_dict = {g.description: g for g in gaps}
        in_degree = {g.description: 0 for g in gaps}

        for gap in gaps:
            for prereq in gap.prerequisites:
                if prereq in gap_dict:
                    in_degree[gap.description] += 1

        # Kahn's algorithm
        queue = [g for g in gaps if in_degree[g.description] == 0]
        result = []

        while queue:
            # Sort by priority within same level
            queue.sort(key=lambda g: g.acquisition_score, reverse=True)
            current = queue.pop(0)
            result.append(current)

            for gap in gaps:
                if current.description in gap.prerequisites:
                    in_degree[gap.description] -= 1
                    if in_degree[gap.description] == 0:
                        queue.append(gap)

        return result

    def _determine_focus(self, topics: List[str]) -> str:
        """Determine the focus of a curriculum stage"""
        if not topics:
            return "general"

        # Simple heuristic based on common words
        all_words = " ".join(topics).lower().split()
        word_freq = defaultdict(int)
        for word in all_words:
            if len(word) > 4:
                word_freq[word] += 1

        if word_freq:
            return max(word_freq.items(), key=lambda x: x[1])[0]
        return "foundations"


class ActiveKnowledgeAcquirer:
    """
    Main active knowledge acquisition engine.
    Coordinates gap identification, query optimization, source selection,
    and curriculum building.
    """

    def __init__(self):
        self.gap_identifier = KnowledgeGapIdentifier()
        self.query_optimizer = QueryOptimizer()
        self.source_selector = SourceSelector()
        self.value_estimator = InformationValueEstimator()
        self.curriculum_builder = CurriculumBuilder()

        # Storage
        self.gaps: Dict[str, KnowledgeGap] = {}
        self.queries: Dict[str, Query] = {}
        self.acquired: Dict[str, AcquiredKnowledge] = {}
        self.curricula: Dict[str, LearningCurriculum] = {}

        # Priority queue for acquisitions
        self._acquisition_queue: List[Tuple[float, str]] = []  # (neg_score, gap_id)

        # Event callbacks
        self._callbacks: Dict[str, List[Callable]] = defaultdict(list)

    def on(self, event: str, callback: Callable):
        """Register event callback"""
        self._callbacks[event].append(callback)

    def _emit(self, event: str, data: Any):
        """Emit event"""
        for callback in self._callbacks[event]:
            callback(data)

    def identify_gaps(
        self,
        current_knowledge: Dict[str, Any],
        task_requirements: List[str],
        domain: str
    ) -> List[KnowledgeGap]:
        """Identify knowledge gaps for a task"""
        gaps = self.gap_identifier.identify_gaps(
            current_knowledge, task_requirements, domain
        )

        for gap in gaps:
            self.gaps[gap.gap_id] = gap
            # Add to priority queue
            heapq.heappush(self._acquisition_queue, (-gap.acquisition_score, gap.gap_id))

        self._emit("gaps_identified", gaps)
        return gaps

    def get_next_acquisition(self) -> Optional[KnowledgeGap]:
        """Get the highest priority gap to acquire"""
        while self._acquisition_queue:
            _, gap_id = heapq.heappop(self._acquisition_queue)
            gap = self.gaps.get(gap_id)
            if gap and not gap.is_resolved:
                return gap
        return None

    def formulate_query(
        self,
        gap: KnowledgeGap,
        context: Dict[str, Any] = None
    ) -> Query:
        """Formulate an optimized query for a gap"""
        query = self.query_optimizer.optimize_query(gap, context)
        self.queries[query.query_id] = query
        self._emit("query_formulated", query)
        return query

    def select_sources(
        self,
        query: Query,
        time_budget: float = 0.5
    ) -> List[Tuple[SourceType, float]]:
        """Select sources for a query"""
        return self.source_selector.select_sources(query, time_budget)

    def record_acquisition(
        self,
        query_id: str,
        answer: str,
        source: SourceType,
        confidence: float
    ) -> AcquiredKnowledge:
        """Record acquired knowledge"""
        query = self.queries.get(query_id)
        if not query:
            return None

        query.is_answered = True
        query.answer = answer
        query.answer_confidence = confidence
        query.answer_source = source
        query.answered_at = datetime.now()

        # Create knowledge record
        knowledge = AcquiredKnowledge(
            knowledge_id="",
            content=answer,
            knowledge_type=query.knowledge_type,
            source=source,
            source_details=f"Query: {query.question[:50]}",
            acquisition_query=query_id,
            confidence=confidence,
            gaps_resolved=[query.target_gap]
        )

        self.acquired[knowledge.knowledge_id] = knowledge

        # Mark gap as resolved
        gap = self.gaps.get(query.target_gap)
        if gap:
            gap.is_resolved = True
            gap.resolution_source = source
            gap.resolved_at = datetime.now()

        self._emit("knowledge_acquired", knowledge)
        return knowledge

    def refine_query(
        self,
        query_id: str,
        previous_answer: str,
        answer_quality: float
    ) -> Optional[Query]:
        """Refine a query if previous answer was insufficient"""
        query = self.queries.get(query_id)
        if not query:
            return None

        refined = self.query_optimizer.refine_query(query, previous_answer, answer_quality)
        self.queries[refined.query_id] = refined
        self._emit("query_refined", refined)
        return refined

    def build_curriculum(
        self,
        goal: str,
        domain: str,
        max_stages: int = 5
    ) -> LearningCurriculum:
        """Build a learning curriculum for unresolved gaps"""
        unresolved = [g for g in self.gaps.values() if not g.is_resolved]

        if not unresolved:
            return None

        curriculum = self.curriculum_builder.build_curriculum(
            goal, domain, unresolved, max_stages
        )

        self.curricula[curriculum.curriculum_id] = curriculum
        self._emit("curriculum_built", curriculum)
        return curriculum

    def get_acquisition_summary(self) -> Dict[str, Any]:
        """Get summary of knowledge acquisition state"""
        total_gaps = len(self.gaps)
        resolved = sum(1 for g in self.gaps.values() if g.is_resolved)

        return {
            "gaps": {
                "total": total_gaps,
                "resolved": resolved,
                "pending": total_gaps - resolved,
                "by_priority": self._count_by_priority()
            },
            "queries": {
                "total": len(self.queries),
                "answered": sum(1 for q in self.queries.values() if q.is_answered)
            },
            "acquired_knowledge": {
                "total": len(self.acquired),
                "by_type": self._count_by_knowledge_type()
            },
            "curricula": {
                "active": len([c for c in self.curricula.values() if c.progress < 1.0])
            }
        }

    def _count_by_priority(self) -> Dict[str, int]:
        counts = defaultdict(int)
        for gap in self.gaps.values():
            if not gap.is_resolved:
                counts[gap.priority.name] += 1
        return dict(counts)

    def _count_by_knowledge_type(self) -> Dict[str, int]:
        counts = defaultdict(int)
        for k in self.acquired.values():
            counts[k.knowledge_type.name] += 1
        return dict(counts)


# Singleton instance
_knowledge_acquirer: Optional[ActiveKnowledgeAcquirer] = None


def get_knowledge_acquirer() -> ActiveKnowledgeAcquirer:
    """Get or create the global knowledge acquirer"""
    global _knowledge_acquirer
    if _knowledge_acquirer is None:
        _knowledge_acquirer = ActiveKnowledgeAcquirer()
    return _knowledge_acquirer
